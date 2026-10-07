"""repair_v310_make_backbone_kwargs.py — D9: backbone constructor kwarg mismatch.

EVIDENCE (from the runner's own atomic run_status.json, not a guess):
Gate 568988, path `primary__nlinear__L24__seed42__w1`:

    File ".../scripts/innovation/clean_runner.py", line 307, in main
        model = make_backbone(base_model, T=T_WINDOW, N=N_VARIABLES,
                              L=horizon, device=device, **bkw)
    File ".../scripts/innovation/backbones/registry.py", line 28, in make_backbone
        return get_backbone(name)(**kwargs)
    TypeError: __init__() got an unexpected keyword argument 'device'

`make_backbone` forwards EVERY keyword straight to the backbone constructor,
and those constructors accept only T/N/L plus their own kwargs. `device` is not
part of that signature — the model is already moved with `.to(device)` later.

This is squarely inside the authorised repair scope "API signature adaptation".
No model architecture, loss, optimizer, early stopping, horizon, seed, metric,
matrix row, ablation/control semantic or endpoint is touched.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "results" / "v3_clean" / "preregistration"
RUNNER = ROOT / "scripts" / "innovation" / "clean_runner.py"
SC.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

VERSION_AFTER = "innov-v3.10-backbone-kwarg-fix"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


before_text = RUNNER.read_text(encoding="utf-8")

OLD = """        model = make_backbone(base_model, T=T_WINDOW, N=N_VARIABLES,
                              L=horizon, device=device, **bkw)"""
NEW = """        # `make_backbone` forwards every keyword to the backbone constructor,
        # which accepts only T/N/L plus its own kwargs. `device` is NOT part of
        # that signature (Gate 568988 D9); the model is moved with `.to(device)`
        # immediately below.
        model = make_backbone(base_model, T=T_WINDOW, N=N_VARIABLES,
                              L=horizon, **bkw)"""

pre_path = SC / "d9_pre_repair_manifest.json"
if not pre_path.exists():
    pre_path.write_text(json.dumps({
        "generated_utc": NOW, "defect": "D9",
        "classification": "BEHAVIOR_NEUTRAL_API_SIGNATURE_ADAPTATION_FIX",
        "runtime_version_before": "innov-v3.9-runner-import-path-fix",
        "runtime_version_after": VERSION_AFTER,
        "failing_gate": {"job_id": "568988", "state": "FAILED",
                         "n_failing_paths": 18,
                         "first_observed": "primary__nlinear__L24__seed42__w1"},
        "failure_signature": {
            "exception": "TypeError",
            "message": "__init__() got an unexpected keyword argument 'device'",
            "failing_file": "scripts/innovation/backbones/registry.py",
            "failing_line": 28,
            "raised_from": "scripts/innovation/clean_runner.py line 307",
            "stage": "model construction (data loaded, training not started)",
            "shared_by_all_model_paths": True},
        "predecessor_defect": {
            "id": "D8",
            "status": "FIXED_AND_VERIFIED_IN_v3.9",
            "evidence": "after the v3.9 import-path fix the runner imports "
                        "successfully and reaches spec resolution and model "
                        "construction (baseline paths now report "
                        "'unknown run_key' from the GATE's key builder, and "
                        "primary paths reach make_backbone)"},
        "pre_repair_sha256": {"scripts/innovation/clean_runner.py": sha(RUNNER)},
        "note": "Recorded BEFORE any edit to this defect's target.",
    }, indent=2), encoding="utf-8")

after_text = before_text
if OLD in after_text:
    after_text = after_text.replace(OLD, NEW)
    applied = True
elif NEW in after_text:
    applied = False
else:
    raise SystemExit("D9 anchor not found in clean_runner.py")

if applied:
    with open(RUNNER, "w", encoding="utf-8", newline="") as f:
        f.write(after_text)

diff = "".join(difflib.unified_diff(
    before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
    fromfile="a/scripts/innovation/clean_runner.py",
    tofile="b/scripts/innovation/clean_runner.py"))
dp = SC / "d9_repair.diff"
if diff.strip():
    dp.write_text(diff, encoding="utf-8")
elif dp.exists():
    diff = dp.read_text(encoding="utf-8")

pre = json.loads(pre_path.read_text(encoding="utf-8"))
rec = {
    "generated_utc": NOW, "defect": "D9", "applied_now": applied,
    "classification": "BEHAVIOR_NEUTRAL_API_SIGNATURE_ADAPTATION_FIX",
    "file": "scripts/innovation/clean_runner.py",
    "pre_repair_sha256": pre["pre_repair_sha256"][
        "scripts/innovation/clean_runner.py"],
    "post_repair_sha256": sha(RUNNER),
    "diff_bytes": len(diff.encode("utf-8")),
    "diff_sha256": sha_b(diff.encode("utf-8")),
    "repair_scope": "API signature adaptation (authorised, item 8)",
    "untouched": ["model architecture", "loss", "optimizer",
                  "early stopping", "horizons", "seeds", "metrics",
                  "598-row matrix", "ablation/control semantics",
                  "endpoint hierarchy"],
    "scientific_parameters_changed": 0,
}
(SC / "d9_repair_record.json").write_text(json.dumps(rec, indent=2),
                                          encoding="utf-8")
with open(SC / "d9_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="") as f:
    f.write(json.dumps({"utc": NOW, "event": "d9_repair_applied",
                        "applied": applied,
                        "pre": rec["pre_repair_sha256"],
                        "post": rec["post_repair_sha256"]}) + "\n")
print(f"[d9] applied={applied} pre={rec['pre_repair_sha256'][:16]} "
      f"post={rec['post_repair_sha256'][:16]} "
      f"diff_bytes={rec['diff_bytes']}")
