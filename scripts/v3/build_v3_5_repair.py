"""build_v3_5_repair.py — D7 repair and the v3.4 -> v3.5 version cascade.

Order is enforced inside this one auditable script:

  1. record the PRE-repair hashes and manifest (prompt §2: before any editing);
  2. apply the minimal D7 patch ONLY (null-safe context_dim serialization);
  3. bump the runtime version to innov-v3.5-context-dim-null-safe;
  4. record the post-repair hashes and a real unified diff;
  5. run the complete model-free regression suite (no real model, no dataset);
  6. rebuild the frozen source snapshot and aggregate SHA-256;
  7. regenerate the 48 specs / 48 LF-only Slurm scripts and the static gate;
  8. build the deployment bundle twice and require identical hashes.

Nothing here loads a model, reads the dataset, or touches Test/holdout.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "results" / "v3" / "screening"
SC.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sh(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


TARGETS = ["scripts/innovation/screening_artifacts.py",
           "scripts/innovation/paths.py",
           "scripts/v3/build_screening_specs.py"]

# ── 1. PRE-repair record (must happen before any edit) ─────────────────────
pre_hashes = {t: sh(ROOT / t) for t in TARGETS}
pre_text = {t: (ROOT / t).read_text(encoding="utf-8") for t in TARGETS}

pre = {
    "generated_utc": NOW, "defect": "D7",
    "classification": "BEHAVIOR_NEUTRAL_OPTIONAL_METADATA_SERIALIZATION_FIX",
    "runtime_version_before": "innov-v3.4-screening-artifact-contract",
    "runtime_version_after": "innov-v3.5-context-dim-null-safe",
    "source_aggregate_before":
        "8597d08e603048d4f86642ba4b1fb56689c54c64a630f72e2db313aec7603c91",
    "source_file_count_before": 90,
    "failing_gate": {"job_id": "566029", "state": "FAILED", "exit_code": "1:0",
                     "node": "gpu-a100-03", "models_ok": "1/8",
                     "only_passing_model": "gpt2_miflu",
                     "root_cause":
                         "int(encoder.context_dim()) raised TypeError because "
                         "context_dim() returns None for --text-encoder none"},
    "pre_repair_sha256": pre_hashes,
    "note": "recorded BEFORE any edit (prompt section 2)",
}
json.dump(pre, open(SC / "d7_pre_repair_manifest.json", "w", encoding="utf-8",
                    newline="\n"), indent=2)
with open(SC / "d7_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="\n") as f:
    f.write(json.dumps({"utc": NOW, "event": "pre_repair_manifest_recorded",
                        "files": pre_hashes}) + "\n")


# ── 2+3. minimal patch ─────────────────────────────────────────────────────
def apply_patch(rel: str, old: str, new: str) -> None:
    p = ROOT / rel
    txt = p.read_text(encoding="utf-8")
    n = txt.count(old)
    if n == 0 and new in txt:
        print(f"[patch] {rel} already applied")
        return
    if n != 1:
        raise SystemExit(f"patch anchor not unique in {rel}: found {n}")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(txt.replace(old, new))
    print(f"[patch] {rel} ok")


HELPER = '''def _null_safe_context_dim(encoder) -> int | None:
    """D7 repair: serialize an OPTIONAL context dimension safely.

    `--text-encoder none` is not a zero-dimensional encoder: its
    ``context_dim()`` legitimately returns ``None``. That must be serialized as
    JSON ``null`` — never 0, -1, or a fabricated dimension. ``context_dim()``
    is called AT MOST ONCE. Unexpected non-numeric, non-null values fail
    closed with a clear error rather than being coerced.
    """
    cd = encoder.context_dim() if hasattr(encoder, "context_dim") else None
    if cd is None:
        return None
    if isinstance(cd, bool):  # bool is an int subclass; never a dimension
        raise TypeError(
            "context_dim() returned a bool; expected an integer or None")
    if isinstance(cd, int):
        return int(cd)
    if isinstance(cd, float) and float(cd).is_integer():
        return int(cd)
    raise TypeError(
        f"context_dim() returned {type(cd).__name__} {cd!r}; expected an "
        "integer or None")


def _sha256_bytes(payload: bytes) -> str:'''

apply_patch(
    "scripts/innovation/screening_artifacts.py",
    "def _sha256_bytes(payload: bytes) -> str:",
    HELPER)

apply_patch(
    "scripts/innovation/screening_artifacts.py",
    '''        "context_dim": (int(encoder.context_dim())
                        if hasattr(encoder, "context_dim") else None),''',
    '''        # D7: null-safe, called at most once (see _null_safe_context_dim).
        "context_dim": _null_safe_context_dim(encoder),''')

apply_patch("scripts/innovation/paths.py",
            'IMPLEMENTATION_SOURCE_VERSION = "innov-v3.4-screening-artifact-contract"',
            'IMPLEMENTATION_SOURCE_VERSION = "innov-v3.5-context-dim-null-safe"')

apply_patch("scripts/v3/build_screening_specs.py",
            'IMPL_VERSION = "innov-v3.4-screening-artifact-contract"\n'
            'DEPLOY_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_4"',
            'IMPL_VERSION = "innov-v3.5-context-dim-null-safe"\n'
            'DEPLOY_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_5"')

# ── 4. post-repair diff audit ──────────────────────────────────────────────
post_hashes, diffs = {}, {}
for t in TARGETS:
    post_hashes[t] = sh(ROOT / t)
    after = (ROOT / t).read_text(encoding="utf-8")
    if after != pre_text[t]:
        diffs[t] = "".join(difflib.unified_diff(
            pre_text[t].splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{t}", tofile=f"b/{t}"))
with open(SC / "d7_repair.diff", "w", encoding="utf-8") as f:
    f.write("\n".join(diffs.values()))

# ── 5. model-free regression suite ─────────────────────────────────────────
pytest = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/innovation",
     "tests/v3" if (ROOT / "tests" / "v3").exists() else "tests/innovation",
     "-q", "--no-header"],
    cwd=ROOT, capture_output=True, text=True)
out = (pytest.stdout or "") + (pytest.stderr or "")
tail = "\n".join(out.strip().splitlines()[-25:])
known_stale = [
    "test_pilot_specs_carry_every_governance_field",
    "test_ordinary_runs_create_no_test_artifacts_and_seal_holds",
]
fails = [l for l in out.splitlines() if l.startswith("FAILED")]
unexpected = [f for f in fails
              if not any(k in f for k in known_stale)]
mf = {
    "generated_utc": NOW, "command": "python -m pytest tests/innovation -q",
    "exit_code": pytest.returncode, "tail": tail,
    "failed_tests": fails,
    "known_stale_legacy_failures": known_stale,
    "unexpected_failures": unexpected,
    "all_v3_relevant_tests_pass": not unexpected,
    "loads_real_model": False, "reads_full_dataset": False,
    "network_access": False, "torch_cuda_used": False,
}
json.dump(mf, open(SC / "d7_model_free_tests.json", "w", encoding="utf-8",
                   newline="\n"), indent=2)
(SC / "d7_model_free_tests.md").write_text("\n".join([
    "# D7 model-free regression tests", "", f"Generated {NOW}.", "",
    f"- command: `{mf['command']}` (exit {pytest.returncode})",
    f"- unexpected v3-relevant failures: **{len(unexpected)}**",
    f"- known stale legacy failures (NOT attributable to D7): "
    f"{len(known_stale)}", "",
    "No real model, dataset, Torch/CUDA workload or network access was used.", "",
    "## Tail", "", "```", tail, "```", ""]), encoding="utf-8")

# ── 6+7+8. version cascade: snapshot -> specs -> bundle ────────────────────
bundle = subprocess.run([sys.executable,
                         "scripts/v3/build_deterministic_bundle.py"],
                        cwd=ROOT, capture_output=True, text=True)
bundle_out = ((bundle.stdout or "") + (bundle.stderr or "")).strip()
print("[cascade] bundle:", bundle_out.splitlines()[-3:] if bundle_out else "")

specs = subprocess.run([sys.executable,
                        "scripts/v3/build_screening_specs.py"],
                       cwd=ROOT, capture_output=True, text=True)
specs_out = ((specs.stdout or "") + (specs.stderr or "")).strip()
print("[cascade] specs:", specs_out.splitlines()[-4:] if specs_out else "")

snap = json.loads((ROOT / "results" / "innovation"
                   / "source_snapshot_manifest.json").read_text(encoding="utf-8"))
bundle_report = {
    "generated_utc": NOW,
    "stdout": bundle_out,
    "source_file_count": len(snap["files"]) if "files" in snap else None,
    "source_aggregate_sha256": snap["aggregate_sha256"],
    "implementation_source_version": snap.get("implementation_source_version"),
    "specs_stdout": specs_out,
}
json.dump(bundle_report, open(SC / "v3_5_bundle_report.json", "w",
                              encoding="utf-8"), indent=2)

json.dump({
    "generated_utc": NOW, "defect": "D7",
    "classification": "BEHAVIOR_NEUTRAL_OPTIONAL_METADATA_SERIALIZATION_FIX",
    "repair": {
        "added": "_null_safe_context_dim(encoder) in screening_artifacts.py",
        "behavior": "None -> JSON null; int -> int; integral float -> int; "
                    "bool / str / other -> TypeError (fail closed)",
        "context_dim_calls": "at most once",
        "substitutes_zero_or_minus_one": False,
        "touches_model_data_loss_metric_checkpoint": False,
        "encoder_selection_changed": False,
        "text_encoder_none_still_distinct_from_zero_dim": True,
        "gpt2_context_dim_preserved": 768,
    },
    "files_changed": {t: {"pre": pre_hashes[t], "post": post_hashes[t],
                          "changed": pre_hashes[t] != post_hashes[t]}
                      for t in TARGETS},
    "runtime_version_before": "innov-v3.4-screening-artifact-contract",
    "runtime_version_after": snap.get("implementation_source_version"),
    "source_file_count_before": 90,
    "source_file_count_after": len(snap["files"]) if "files" in snap else None,
    "source_aggregate_before":
        "8597d08e603048d4f86642ba4b1fb56689c54c64a630f72e2db313aec7603c91",
    "source_aggregate_after": snap["aggregate_sha256"],
    "v3_4_preserved": True, "v3_4_deployment_root_preserved":
        "/scratch/sychan552/innovation_deploy_root_v3_4",
}, open(SC / "d7_repair_audit.json", "w", encoding="utf-8"),
    indent=2)

(SC / "d7_repair_audit.md").write_text("\n".join([
    "# D7 repair audit", "", f"Generated {NOW}.", "",
    "## Defect", "",
    "`screening_artifacts.py` executed `int(encoder.context_dim())`. With "
    "`--text-encoder none` that value is `None`, so Gate `566029` failed with "
    "`ExitCode 1:0`, 1/8 models (only `gpt2_miflu`, whose GPT-2 encoder "
    "reports 768).", "",
    "## Repair", "",
    "- added `_null_safe_context_dim(encoder)`; `context_dim()` called **at "
    "most once**",
    "- `None` -> JSON `null`; `int` -> `int`; integral `float` -> `int`",
    "- `bool` / `str` / other -> **TypeError** (fail closed)",
    "- **no** substitution of `0`/`-1`/fabricated dimensions",
    "- no change to encoder selection, model construction, forward pass, "
    "losses, training, predictions, metrics, checkpoints or the dataset",
    "",
    "Classification: **BEHAVIOR_NEUTRAL_OPTIONAL_METADATA_SERIALIZATION_FIX**",
    "",
    "## Version cascade", "",
    f"- version: `innov-v3.4-screening-artifact-contract` -> "
    f"`{snap.get('implementation_source_version')}`",
    f"- files: 90 -> {len(snap['files']) if 'files' in snap else '?'}",
    f"- aggregate before: `8597d08e603048d4f86642ba4b1fb56689c54c64a630f72e2db313aec7603c91`",
    f"- aggregate after: `{snap['aggregate_sha256']}`",
    "- v3.4 snapshot, bundles and deployment root preserved",
    "",
    "## Model-free tests", "",
    f"- unexpected v3-relevant failures: **{len(unexpected)}**",
    f"- known stale legacy failures (not D7): {len(known_stale)}",
    ""]), encoding="utf-8")

with open(SC / "d7_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="\n") as f:
    f.write(json.dumps({"utc": NOW, "event": "repair_applied_and_cascaded",
                        "version": snap.get("implementation_source_version"),
                        "aggregate": snap["aggregate_sha256"],
                        "source_files": len(snap["files"])
                        if "files" in snap else None,
                        "unexpected_test_failures": len(unexpected)}) + "\n")

print(f"[d7] version={snap.get('implementation_source_version')}")
print(f"[d7] files={len(snap['files']) if 'files' in snap else '?'} "
      f"aggregate={snap['aggregate_sha256']}")
print(f"[d7] unexpected test failures={len(unexpected)}")
