"""verify_deployment_clean.py — remote deployment audit for v3.10 (v3_clean4).

Runs ON THE COMPUTE-ADJACENT FILESYSTEM against an already-extracted root.
It performs NO model, Torch/CUDA, training, inference or evaluation work — only
hashing, file listing and `bash -n` syntax checks. Small-file only.

Usage:
  python3 verify_deployment_clean.py --root <deployment_root> \
      --deploy-manifest <path to deployment_manifest.json> \
      --out <json path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--deploy-manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-version",
                    default="innov-v3.11-artifact-directory-initialization")
    ap.add_argument("--expect-source-files", type=int, default=128)
    ap.add_argument("--expect-source-prefix", default="67a3d80666941bba")
    ap.add_argument("--expect-deployment-prefix", default="4eed21a1e1fdfe32")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    checks: list[dict] = []

    def chk(cid, ok, detail):
        checks.append({"id": cid, "passed": bool(ok), "detail": str(detail)})

    # ── source manifest: every frozen file byte-identical ────────────────────
    sm_path = root / "results/v3_clean/implementation/source_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    src_lines, src_bad = [], []
    for rec in sm["files"]:
        p = root / rec["path"]
        if not p.exists():
            src_bad.append({"path": rec["path"], "why": "MISSING"})
            continue
        got = sha256(p)
        if got != rec["sha256"]:
            src_bad.append({"path": rec["path"], "why": "HASH",
                            "expected": rec["sha256"], "got": got})
        else:
            src_lines.append(f"{rec['path']}:{rec['sha256']}")

    # EXACTLY as build_v38_closure.py computes it: "path:sha256" joined by LF,
    # NO trailing newline.
    recomputed = hashlib.sha256(
        "\n".join(sorted(src_lines)).encode("utf-8")).hexdigest()
    chk("source_version_matches_expected",
        sm["version"] == a.expect_version, sm["version"])
    chk("source_files_count",
        sm["n_files"] == len(sm["files"]) == a.expect_source_files,
        f"{sm['n_files']} (expected {a.expect_source_files})")
    chk("source_files_all_present_and_hashed", not src_bad, src_bad[:3])
    chk("source_aggregate_matches_manifest",
        recomputed == sm["aggregate_sha256"],
        f"recomputed={recomputed[:16]} manifest={sm['aggregate_sha256'][:16]}")
    chk("source_aggregate_matches_authorised_prefix",
        sm["aggregate_sha256"].startswith(a.expect_source_prefix),
        sm["aggregate_sha256"])

    # ── deployment manifest: every closure member present ────────────────────
    dm = json.loads(Path(a.deploy_manifest).read_text(encoding="utf-8"))
    dep_bad = []
    for rec in dm["members"]:
        p = root / rec["path"]
        if not p.exists():
            dep_bad.append({"path": rec["path"], "why": "MISSING"})
            continue
        if rec.get("sha256") and sha256(p) != rec["sha256"]:
            dep_bad.append({"path": rec["path"], "why": "HASH"})
    # The member COUNT grows whenever governance evidence is added; the
    # authoritative check is the independently recomputed aggregate below.
    chk("deployment_member_count_consistent",
        dm["n_members"] == len(dm["members"]), dm["n_members"])
    chk("deployment_members_all_valid", not dep_bad, dep_bad[:3])
    chk("deployment_aggregate_authorised_prefix",
        dm["deployment_aggregate_sha256"].startswith(
            a.expect_deployment_prefix),
        dm["deployment_aggregate_sha256"])
    dep_agg = hashlib.sha256("\n".join(
        f"{m['path']}:{m['sha256']}" for m in dm["members"]
    ).encode("utf-8")).hexdigest()
    chk("deployment_aggregate_recomputed",
        dep_agg == dm["deployment_aggregate_sha256"],
        f"{dep_agg[:16]} vs {dm['deployment_aggregate_sha256'][:16]}")
    slurm_all = sorted((root / "hpc_scripts").rglob("*.sh"))
    n_exec = sum(1 for p in slurm_all if os.access(p, os.X_OK))
    chk("slurm_scripts_executable_bits", n_exec == len(slurm_all),
        f"{n_exec}/{len(slurm_all)}")

    # ── matrix counts ───────────────────────────────────────────────────────
    sp = root / "results/v3_clean/runs/complete_specs_598.json"
    specs = json.loads(sp.read_text(encoding="utf-8"))
    rows = specs["specs"]
    w1 = [r for r in rows if r.get("wave") == 1]
    w2 = [r for r in rows if r.get("wave") == 2]
    keys = [r["run_key"] for r in rows]
    chk("specs_total_598", len(rows) == 598, len(rows))
    chk("specs_wave1_580", len(w1) == 580, len(w1))
    chk("specs_wave2_18", len(w2) == 18, len(w2))
    chk("specs_no_duplicate_keys", len(set(keys)) == len(keys),
        f"{len(keys) - len(set(keys))} dups")
    chk("specs_csv_present",
        (root / "results/v3_clean/runs/complete_specs_598.csv").exists(), "ok")

    # ── shell scripts: LF-only + bash -n ────────────────────────────────────
    scripts = sorted((root / "hpc_scripts").rglob("*.sh"))
    crlf = [str(p.relative_to(root)) for p in scripts
            if b"\r" in p.read_bytes()]
    syntax_fail = []
    for p in scripts:
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True)
        if r.returncode != 0:
            syntax_fail.append(str(p.relative_to(root)))
    chk("shell_scripts_581", len(scripts) == 581, len(scripts))
    chk("shell_scripts_lf_only", not crlf, crlf[:3])
    chk("shell_scripts_pass_bash_n", not syntax_fail, syntax_fail[:3])

    # ── runner / gate / registry lookup path ────────────────────────────────
    chk("clean_runner_present",
        (root / "scripts/innovation/clean_runner.py").exists(), "ok")
    chk("clean_gate_py_present",
        (root / "scripts/innovation/clean_gate.py").exists(), "ok")
    chk("clean_gate_sh_present",
        (root / "hpc_scripts/v3_clean/clean_gate.sh").exists(), "ok")
    chk("package_parent_layout_ok",
        (root / "scripts/innovation/__init__.py").exists()
        and (root / "scripts/textual_embedder.py").exists(), "ok")

    # ── canonical data + scaler ─────────────────────────────────────────────
    raw = root / "data/raw/national_illness_raw.csv"
    scal = root / "data/scaler_miflu_national.json"
    chk("canonical_raw_data_present", raw.exists(),
        sha256(raw)[:16] if raw.exists() else "MISSING")
    chk("scaler_present", scal.exists(),
        sha256(scal)[:16] if scal.exists() else "MISSING")

    # ── isolation: archive / Test / holdout / stray weights ─────────────────
    stray = [str(p.relative_to(root)) for p in root.rglob("*")
             if p.suffix in (".pt", ".pth", ".safetensors")]
    chk("no_stray_model_weights", not stray, stray[:3])
    chk("archive_absent", not (root / "results/v3").exists(), "ok")
    hits = [str(p.relative_to(root)) for p in root.rglob("*")
            if "test_evaluations" in str(p) or "holdout" in str(p).lower()]
    chk("test_and_holdout_absent", not hits, hits[:3])

    # ── durable destination writable ────────────────────────────────────────
    dur = Path("/home/sychan552/innovation_durable")
    chk("durable_root_exists", dur.exists(), str(dur))
    chk("durable_root_writable", os.access(dur, os.W_OK) if dur.exists()
        else False, str(dur))

    rep = {
        "root": str(root),
        "n_checks": len(checks),
        "n_passed": sum(1 for c in checks if c["passed"]),
        "all_passed": all(c["passed"] for c in checks),
        "checks": checks,
    }
    Path(a.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['id']}: {c['detail']}")
    print(f"RESULT {rep['n_passed']}/{rep['n_checks']} "
          f"all_passed={rep['all_passed']}")
    return 0 if rep["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
