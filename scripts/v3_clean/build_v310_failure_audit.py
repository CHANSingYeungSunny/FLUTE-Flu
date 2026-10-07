"""build_v310_failure_audit.py — prompt section 2 preservation + reconciliation.

Creates (create-only):
  results/v3_clean/implementation/gates/gate_569016_preservation_manifest.json
  results/v3_clean/implementation/v310_artifact_directory_failure_audit.json
  results/v3_clean/implementation/v310_artifact_directory_failure_audit.md
and marks v3.10 executable status SUPERSEDED_FOR_EXECUTION_
ARTIFACT_DIRECTORY_INITIALIZATION_FAILURE.

Gate outputs are NEVER characterized as scientific results.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3_clean" / "implementation"
GATES = IMPL / "gates"
RUNS = ROOT / "results" / "v3_clean" / "runs"
GATES.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rec(p: Path) -> dict:
    return {"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "bytes": p.stat().st_size, "sha256": sha(p)}


# ── what must be preserved ─────────────────────────────────────────────────
to_preserve = [
    IMPL / "source_manifest.json", IMPL / "deployment_manifest.json",
    IMPL / "bundle_a.zip", IMPL / "bundle_b.zip",
    IMPL / "deterministic_bundle_report.json",
    IMPL / "v310_SUPERSEDED.json" if (IMPL / "v310_SUPERSEDED.json").exists()
    else None,
    RUNS / "gate_569016_report.json",
    RUNS / "gate_569016_failure_signature_matrix.json",
    RUNS / "gate_569016_failure_signature_matrix.md",
    RUNS / "v3_clean_reconciliation_ledger.jsonl",
    ROOT / "results" / "v3_clean" / "preregistration"
    / "d11_pre_repair_manifest.json",
    ROOT / "results" / "v3_clean" / "preregistration" / "d11_repair.diff",
    ROOT / "results" / "v3_clean" / "preregistration" / "d11_repair_record.json",
]
preserved = [rec(p) for p in to_preserve if p is not None and p.exists()]
missing = [str(p) for p in to_preserve if p is not None and not p.exists()]

run_status_files = sorted((RUNS / "gate_569016_evidence" / "runs")
                          .glob("*/run_status.json"))
pres_manifest = {
    "generated_utc": NOW,
    "gate_job_id": "569016",
    "gate_state": "FAILED", "gate_exit_code": "1:0", "gate_passed": "1/19",
    "preserved": preserved,
    "n_preserved": len(preserved),
    "missing": missing,
    "run_status_files_preserved": len(run_status_files),
    "remote_evidence": {
        "gate_dir": "/scratch/sychan552/innovation_deploy_root_v3_clean4/"
                    "results/v3_clean/implementation/gate_569016",
        "slurm_out": "/scratch/sychan552/innovation_deploy_root_v3_clean4/"
                     "hpc_results/innovation/logs/slurm_569016_clean_gate.out",
        "note": "left untouched on the cluster; never rerun, never overwritten"},
    "rerun_forbidden": True,
    "v3_clean4_deployment_identity": {
        "root": "/scratch/sychan552/innovation_deploy_root_v3_clean4",
        "runtime_version": "innov-v3.10-backbone-kwarg-fix",
        "remote_bundle_sha256":
            "7944d7396fc59e427cb977933fdaecadf16417e32f2a569fec2b27e81ad030f0"},
}
(GATES / "gate_569016_preservation_manifest.json").write_text(
    json.dumps(pres_manifest, indent=2), encoding="utf-8")

matrix = json.loads((RUNS / "gate_569016_failure_signature_matrix.json")
                    .read_text(encoding="utf-8"))
audit = {
    "generated_utc": NOW,
    "runtime_version": "innov-v3.10-backbone-kwarg-fix",
    "executable_status":
        "SUPERSEDED_FOR_EXECUTION_ARTIFACT_DIRECTORY_INITIALIZATION_FAILURE",
    "superseded_by": "innov-v3.11-artifact-directory-initialization",
    "gate_569016": {"state": "FAILED", "exit_code": "1:0",
                    "elapsed": "00:24:33", "node": "gpu-a100-06",
                    "passed": "1/19", "n_runtime_paths_failed": 18},
    "observed": {
        "stochastic_paths_failed_at": "logs/train_history.csv",
        "n_stochastic_paths": 16,
        "baseline_paths_failed_at": "predictions/validation_predictions.csv",
        "n_baseline_paths": 2,
        "training_completed_for_stochastic_paths": True,
        "best_checkpoint_existed_for_stochastic_paths": True,
        "four_metric_artifacts_existed_for_baseline_paths": True,
        "formal_rows_submitted": "0/598",
        "test_access": 0, "holdout_access": 0,
        "scientific_protocol_changed": False,
    },
    "confirmed_working_after_previous_repairs": {
        "D8_import_path": True, "D9_backbone_kwarg": True,
        "D10_gate_run_key": True,
    },
    "root_cause": matrix["root_cause"],
    "missing_directories": matrix["missing_directories"],
    "signature_count": {"paths": matrix["n_paths"],
                        "distinct_signatures":
                            matrix["n_distinct_traceback_signatures"],
                        "call_sites": matrix["root_cause_call_sites"]},
    "not_scientific_results": True,
    "gate_outputs_are_infrastructure_only": True,
}
(IMPL / "v310_artifact_directory_failure_audit.json").write_text(
    json.dumps(audit, indent=2), encoding="utf-8")

md = f"""# v3.10 artifact-directory failure audit (Gate 569016)

**Executable status: `SUPERSEDED_FOR_EXECUTION_ARTIFACT_DIRECTORY_INITIALIZATION_FAILURE`**
(superseded by `{audit['superseded_by']}`)

## Gate 569016

| field | value |
|---|---|
| state | FAILED |
| exit code | 1:0 |
| elapsed | 00:24:33 |
| node | gpu-a100-06 |
| passed | 1/19 |
| runtime paths failed | 18 |

## Observed

- **16 stochastic paths** failed at `logs/train_history.csv`
- **2 baseline paths** failed at `predictions/validation_predictions.csv`
- training **completed** for the stochastic paths
- the **best checkpoint existed** for the stochastic paths
- the **four metric artifacts existed** for the baseline paths
- formal rows submitted = **0/598**, Test access = **0**, holdout access = **0**
- **scientific protocol changed = false**

## Confirmed working (earlier repairs)

D8 import path, D9 backbone kwarg, D10 Gate run-key — all **verified** in this run.

## Root cause

`clean_runner.py` never created the per-run artifact sub-directories. The
training arms hit `logs/` first (line 330); the checkpoint-free baselines hit
`predictions/` first (line 263). `metrics/` and `checkpoints/` existed only
because `_atomic_write_json` creates the parent of the file it writes.

> Gate outputs are **infrastructure diagnostics only** — they are **never**
> scientific results and never enter any ranking.
"""
(IMPL / "v310_artifact_directory_failure_audit.md").write_text(md,
                                                              encoding="utf-8")

print(f"[audit] preserved={len(preserved)} missing={len(missing)} "
      f"run_status_files={len(run_status_files)}")
print(f"[audit] wrote v310_artifact_directory_failure_audit.json/.md and "
      f"gates/gate_569016_preservation_manifest.json")
