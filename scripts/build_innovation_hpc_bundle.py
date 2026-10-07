"""
build_innovation_hpc_bundle.py — deterministic HPC deployment archive (Phase A).
===============================================================================

Deliberately OUTSIDE the frozen source scope (`scripts/innovation/**`) so that
building the bundle does NOT change the frozen runtime file-set hash.

Produces, under `results/innovation/hpc_deployment/`:
  * innovation_hpc_bundle.tar.gz            byte-deterministic archive
  * innovation_hpc_bundle.tar.gz.sha256     sidecar (archive SHA-256)
  * DEPLOY_AND_VERIFY.md                    exact deployment + verification commands
  * hpc_deployment_prep.json               machine-readable prep record
and, additionally, `hpc_scripts/hpc_env_check.sh` (separate SHA-256 recorded;
it is NOT part of the frozen runtime hash).

Hard rules implemented
----------------------
  * UNIQUE archive member names; identical (name, bytes) duplicates are
    deduplicated; the SAME name for DIFFERENT sources is a hard failure.
  * audit attachments come from an EXPLICIT REVIEWED ALLOWLIST (no recursive
    glob) and pass a SAFETY SCAN (secrets / credentials / personal absolute
    paths / model weights / test artifacts). Severe hits are excluded; other
    hits are redacted in the bundled copy.
  * the archive is built TWICE and must be byte-identical (same SHA-256).
  * the archive is extracted to an explicit temporary deployment root and
    re-verified with `verify_source_snapshot.verify(deployment_root=tmp)`.

It NEVER invokes ssh or sbatch.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)                      # scripts/
if _os.path.dirname(_HERE) not in _sys.path:
    _sys.path.insert(0, _os.path.dirname(_HERE))    # repo root

import gzip
import hashlib
import io
import json
import os
import re
import shutil
import tarfile
import tempfile

from innovation.paths import (IMPLEMENTATION_SOURCE_VERSION, PLAN_MD,
                              PROTOCOL_VERSION, PROJECT_ROOT,
                              SOURCE_SNAPSHOT_MANIFEST)
from innovation.verify_source_snapshot import verify as verify_deployment

OUT_DIR = os.path.join(PROJECT_ROOT, "results", "innovation", "hpc_deployment")
ARCHIVE_NAME = "innovation_hpc_bundle.tar.gz"
ENV_CHECK_REPO_PATH = "hpc_scripts/hpc_env_check.sh"

# ── explicit, reviewed audit attachment allowlist (no recursive glob) ───────
AUDIT_ALLOWLIST = (
    "audit/audit.md",
    "audit/plan_compliance_matrix.md",
    "audit/early_stopping_audit.md",
    "audit/peak_criteria_spec.md",
    "audit/eligibility_policy.md",
    "audit/failed_runs_resolution.md",
    "audit/environment_report.md",
    "audit/environment_report.json",
    "audit/aggregation_regression_report.json",
    "audit/pipeline_regression_report.json",
    "audit/gpt2_control_repro_report.json",
    "audit/architecture_equivalence.md",
    "audit/architecture_equivalence.json",
    "audit/slurm_validation_report.json",
    "audit/fix_fingerprint.json",
    "audit/plan_sha256.json",
    "audit/dependency_probe.json",
    "audit/prompt_variation_report.json",
    "pre_hpc_gate.json",
    "pre_hpc_gate.md",
    "human_review_checklist.md",
    "remaining_plan_execution_matrix.md",
)

# ── safety scan ─────────────────────────────────────────────────────────────
SEVERE_PATTERNS = (
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{20,}")),
    ("password_assignment",
     re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*\S+")),
)
SOFT_PATTERNS = (
    ("personal_windows_path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"']+")),
    ("model_weight_file", re.compile(r"\.(pt|pth|ckpt|safetensors|bin|h5|onnx)\b")),
    ("test_artifact",
     re.compile(r"(test_predictions\.json|test_predictions\.csv|test_metrics\.json|"
                r"test_evaluations/)")),
)


class ArchiveNameCollision(RuntimeError):
    pass


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _scan(text: str) -> dict:
    severe, soft = [], []
    for name, rx in SEVERE_PATTERNS:
        for m in rx.finditer(text):
            severe.append({"pattern": name, "match": m.group(0)[:80]})
    for name, rx in SOFT_PATTERNS:
        for m in rx.finditer(text):
            soft.append({"pattern": name, "match": m.group(0)[:120]})
    return {"severe": severe, "soft": soft}


def _redact(text: str) -> tuple[str, int]:
    n = 0
    for name, rx in SOFT_PATTERNS:
        text, k = rx.subn(f"<REDACTED:{name}>", text)
        n += k
    return text, n


def env_check_script() -> str:
    return """#!/bin/bash
# ============================================================================
# hpc_env_check.sh — HPC environment FACTS for the innovation pilot.
# Prints facts ONLY. It does NOT verify the source, does NOT unlock pilot
# submission, and never submits anything.
# Run from the deployment root:   bash hpc_scripts/hpc_env_check.sh
# ============================================================================
set -u
ROOT="${INNOVATION_DEPLOYMENT_ROOT:-$(pwd)}"
echo "== host =="; hostname; date -u '+%Y-%m-%dT%H:%M:%SZ'; echo "pwd=$(pwd)"; echo "deployment_root=${ROOT}"
echo "== slurm =="; echo "SLURM_JOB_ID=${SLURM_JOB_ID:-none}"; sinfo -V 2>/dev/null || echo "sinfo: unavailable"
echo "== python/lib stack =="
python - <<'PY'
import platform
print("python", platform.python_version())
for m in ("torch", "transformers", "numpy", "pandas", "scipy", "sklearn", "statsmodels", "matplotlib"):
    try:
        mod = __import__(m); print(m, getattr(mod, "__version__", "?"))
    except Exception as e:
        print(m, "UNAVAILABLE", type(e).__name__)
try:
    import torch
    print("cuda_available", torch.cuda.is_available())
    print("cuda_device_count", torch.cuda.device_count())
    if torch.cuda.is_available():
        print("cuda_device_name", torch.cuda.get_device_name(0))
        print("cudnn_version", torch.backends.cudnn.version())
        print("cudnn_deterministic", torch.backends.cudnn.deterministic)
except Exception as e:
    print("torch probe failed", type(e).__name__, e)
PY
echo "== gpu =="; nvidia-smi 2>/dev/null || echo "nvidia-smi: unavailable"
echo "== offline GPT-2 load probe (must NOT download) =="
python - <<'PY'
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
try:
    from transformers import GPT2Model, GPT2Tokenizer
    GPT2Tokenizer.from_pretrained("gpt2"); GPT2Model.from_pretrained("gpt2")
    print("gpt2_offline_load=OK")
except Exception as e:
    print("gpt2_offline_load=FAILED", type(e).__name__, e)
PY
echo "== pilot script syntax (bash -n) =="
for f in hpc_scripts/pilot_*.sh hpc_scripts/innovation_worker.sh; do
  [ -f "$f" ] && { bash -n "$f" && echo "ok $f" || echo "FAIL $f"; }
done
echo "== deployment-root verification (informational; authoritative check is the pilot startup step) =="
python scripts/innovation/verify_source_snapshot.py \\
  --deployment-root "${ROOT}" \\
  --manifest results/innovation/source_snapshot_manifest.json || echo "DEPLOYMENT_ROOT_VERIFY=FAILED"
echo "== done =="
"""


def _gather_members() -> tuple[list[tuple[str, bytes]], dict]:
    with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
        man = json.load(f)

    members: dict[str, bytes] = {}
    origins: dict[str, str] = {}

    def add(name: str, data: bytes, origin: str):
        name = name.replace(os.sep, "/")
        if name in members:
            if members[name] != data:
                raise ArchiveNameCollision(
                    f"archive-name collision for {name!r}: different sources "
                    f"({origins[name]} vs {origin})")
            return                      # identical duplicate -> deduplicated
        members[name] = data
        origins[name] = origin

    # (A) the frozen runtime file set at repo-relative paths
    for rec in man["files"]:
        p = os.path.join(PROJECT_ROOT, rec["path"])
        add(rec["path"], open(p, "rb").read(), f"frozen:{rec['path']}")

    # (B) the manifest itself
    add("results/innovation/source_snapshot_manifest.json",
        open(SOURCE_SNAPSHOT_MANIFEST, "rb").read(), "manifest")

    # (C) pilot specs
    ps = os.path.join(PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")
    if os.path.exists(ps):
        add("hpc_scripts/pilot_specs.json", open(ps, "rb").read(), "pilot_specs")

    # (D) env check script (separate hash recorded; NOT in the frozen hash set)
    ec = env_check_script().encode("utf-8")
    os.makedirs(os.path.join(PROJECT_ROOT, "hpc_scripts"), exist_ok=True)
    with open(os.path.join(PROJECT_ROOT, ENV_CHECK_REPO_PATH), "wb") as f:
        f.write(ec)
    add(ENV_CHECK_REPO_PATH, ec, "env_check")

    # (E) audit attachments — EXPLICIT allowlist + safety scan
    audit_report = {"included": [], "redacted": [], "excluded": []}
    for rel in AUDIT_ALLOWLIST:
        src = os.path.join(PROJECT_ROOT, "results", "innovation", rel)
        member = f"results/innovation/{rel}"
        if not os.path.exists(src):
            audit_report["excluded"].append(
                {"member": member, "reason": "not present in workspace"})
            continue
        raw = open(src, "rb").read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            audit_report["excluded"].append(
                {"member": member, "reason": "binary content"})
            continue
        scan = _scan(text)
        if scan["severe"]:
            audit_report["excluded"].append(
                {"member": member, "reason": "safety_scan_severe",
                 "findings": scan["severe"]})
            continue
        if scan["soft"]:
            red, n = _redact(text)
            audit_report["redacted"].append(
                {"member": member, "redactions": n,
                 "findings": [f["pattern"] for f in scan["soft"]]})
            add(member, red.encode("utf-8"), f"audit_redacted:{rel}")
        else:
            audit_report["included"].append(member)
            add(member, raw, f"audit:{rel}")

    return sorted(members.items()), audit_report


def _tar_bytes(members: list[tuple[str, bytes]]) -> bytes:
    """Byte-deterministic gzip+tar: fixed order, mtime/uid/gid/mode, gzip mtime=0."""
    buf = io.BytesIO()
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0,
                       compresslevel=9)
    tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT)
    for name, data in sorted(members, key=lambda x: x[0]):
        ti = tarfile.TarInfo(name)
        ti.size = len(data)
        ti.mtime = 0
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = ""
        ti.mode = 0o755 if name.endswith(".sh") else 0o644
        ti.type = tarfile.REGTYPE
        tar.addfile(ti, io.BytesIO(data))
    tar.close()
    gz.close()
    return buf.getvalue()


def deploy_doc(archive_sha: str, runtime_sha: str, env_sha: str,
               plan_sha: str) -> str:
    # The frozen innovation source must NOT be extracted into the original
    # reproduction repo: every deployment gets its own content-addressed ISOLATED
    # root (exactly what the v2.1 deployment used). The earlier text pointed at
    # `.../CHATTIME/Chattime`, which is how an extraction ended up overwriting the
    # reproduction tree; that is fixed here.
    deploy_root = ("/home/sychan552/scratch/CHATTIME/"
                   "MIFlu_innovation_deployments/"
                   f"{IMPLEMENTATION_SOURCE_VERSION}_{runtime_sha[:8]}")
    return f"""# Deploy & verify the innovation HPC bundle (Phase A)

Scientific protocol: `{PROTOCOL_VERSION}` · implementation source:
`{IMPLEMENTATION_SOURCE_VERSION}`

| artefact | SHA-256 |
|---|---|
| archive `{ARCHIVE_NAME}` | `{archive_sha}` |
| runtime file-set aggregate | `{runtime_sha}` |
| `hpc_scripts/hpc_env_check.sh` | `{env_sha}` |
| authoritative plan | `{plan_sha}` |

## 1. Upload (from the local repo root; adjust the remote path if needed)

```bash
scp results/innovation/hpc_deployment/{ARCHIVE_NAME} \\
    results/innovation/hpc_deployment/{ARCHIVE_NAME}.sha256 \\
    sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/
```

## 2. Extract into the ISOLATED deployment root on HPC

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk
cd /home/sychan552/scratch/CHATTIME
sha256sum -c {ARCHIVE_NAME}.sha256
mkdir -p {deploy_root}
tar -xzf {ARCHIVE_NAME} -C {deploy_root}
```

> **Never extract into the original reproduction repo** (`.../CHATTIME/Chattime`).
> The frozen innovation source lives in its own content-addressed isolated root, so
> the reproduction tree stays untouched and every deployment is independently
> verifiable. `{deploy_root}`

## 3. Authoritative deployment-root source verification (explicit root)

```bash
cd {deploy_root}
export INNOVATION_DEPLOYMENT_ROOT="$PWD"
python scripts/innovation/verify_source_snapshot.py \\
  --deployment-root "$INNOVATION_DEPLOYMENT_ROOT" \\
  --manifest results/innovation/source_snapshot_manifest.json \\
  --expect {runtime_sha}
```
Exit code 0 and `actual_aggregate_sha256 == {runtime_sha}` are REQUIRED.
A nested `results/innovation/source_snapshot` root is rejected with
`INVALID_NESTED_SNAPSHOT_ROOT`.

## 4. Environment facts (does NOT unlock pilot submission)

```bash
cd {deploy_root}
INNOVATION_DEPLOYMENT_ROOT="$PWD" bash hpc_scripts/hpc_env_check.sh
```

## 5. Stop

Do **not** submit any pilot until the user explicitly authorizes it. The pilot
scripts additionally refuse to run unless `CONFIRM_INNOVATION_SUBMIT=YES`.
"""


def main(argv=None) -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    members, audit_report = _gather_members()

    b1 = _tar_bytes(members)
    b2 = _tar_bytes(members)
    sha1, sha2 = _sha256_bytes(b1), _sha256_bytes(b2)
    if sha1 != sha2:
        raise RuntimeError(f"NON_DETERMINISTIC_BUILD: {sha1} != {sha2}")

    archive = os.path.join(OUT_DIR, ARCHIVE_NAME)
    with open(archive, "wb") as f:
        f.write(b1)
    with open(archive + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{sha1}  {ARCHIVE_NAME}\n")

    with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
        man = json.load(f)
    runtime_sha = man["aggregate_sha256"]
    plan_sha = man["authoritative_plan"]["sha256"]
    env_sha = _sha256_bytes(next(d for n, d in members
                                 if n == ENV_CHECK_REPO_PATH))

    # ── local extraction + explicit-root verification ──
    tmp = tempfile.mkdtemp(prefix="innov_extract_")
    with tarfile.open(archive, "r:gz") as t:
        t.extractall(tmp)
    ver = verify_deployment(
        os.path.join(tmp, "results", "innovation",
                     "source_snapshot_manifest.json"),
        deployment_root=tmp)

    with open(os.path.join(OUT_DIR, "DEPLOY_AND_VERIFY.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(deploy_doc(sha1, runtime_sha, env_sha, plan_sha))

    prep = {
        "created_utc": __import__("datetime").datetime.utcnow()
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
        "archive": {"path": os.path.relpath(archive, PROJECT_ROOT).replace(os.sep, "/"),
                    "sha256": sha1, "size_bytes": len(b1),
                    "deterministic_double_build": True,
                    "member_count": len(members)},
        "runtime_file_set_aggregate_sha256": runtime_sha,
        "hpc_env_check_sha256": env_sha,
        "authoritative_plan_sha256": plan_sha,
        "frozen_source_snapshot_dir": man["snapshot_dir"],
        "nested_snapshot_included_in_bundle": False,
        "audit_attachments": audit_report,
        "local_extraction_verification": {
            "deployment_root": tmp,
            "ok": bool(ver["ok"]),
            "verified_file_count": ver["verified_file_count"],
            "expected_file_count": ver["expected_file_count"],
            "actual_aggregate_sha256": ver["actual_aggregate_sha256"],
            "verification_mode": ver["verification_mode"],
        },
        "hpc_deployment_verified": False,
        "pilot_submission_ready": False,
        "full_sweep_submission_ready": False,
        "blocker": "UNVERIFIED_HPC_SOURCE_DEPLOYMENT",
        "submission_attempted": False,
        "sbatch_invoked": False,
        "note": ("local deterministic bundle + local explicit-root extraction "
                 "verification only; real HPC deployment is NOT verified"),
    }
    with open(os.path.join(OUT_DIR, "hpc_deployment_prep.json"), "w",
              encoding="utf-8") as f:
        json.dump(prep, f, indent=2)

    shutil.rmtree(tmp, ignore_errors=True)

    print(f"[bundle] archive={archive}")
    print(f"[bundle] archive_sha256={sha1} (deterministic: {sha1 == sha2})")
    print(f"[bundle] runtime_file_set_aggregate_sha256={runtime_sha}")
    print(f"[bundle] hpc_env_check_sha256={env_sha}")
    print(f"[bundle] members={len(members)} attachments: "
          f"{len(audit_report['included'])} clean / "
          f"{len(audit_report['redacted'])} redacted / "
          f"{len(audit_report['excluded'])} excluded")
    print(f"[bundle] local extraction verify ok={ver['ok']} "
          f"({ver['verified_file_count']}/{ver['expected_file_count']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
