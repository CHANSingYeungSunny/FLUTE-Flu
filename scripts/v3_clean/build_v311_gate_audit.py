"""build_v311_gate_audit.py — prompt section 1: preserve Gate 570452 / v3.11.

Creates (create-only):
  results/v3_clean/implementation/gates/gate_570452_preservation_manifest.json
  results/v3_clean/implementation/v311_gate_validator_failure_audit.json
  results/v3_clean/implementation/v311_gate_validator_failure_audit.md
and records v3.11 as SUPERSEDED_FOR_EXECUTION_GATE_VALIDATOR_SCHEMA_MISMATCH.

Gate 570452 stays classified FAILED, and is recorded as a VALIDATOR-ONLY false
failure — never a model-performance result.
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
SC = ROOT / "results" / "v3_clean" / "preregistration"
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


candidates = [
    IMPL / "source_manifest.json", IMPL / "deployment_manifest.json",
    IMPL / "bundle_a.zip", IMPL / "bundle_b.zip",
    IMPL / "deterministic_bundle_report.json",
    IMPL / "v311_SUPERSEDED.json",
    RUNS / "gate_570452_report.json",
    RUNS / "gate_570452_failure_signature_matrix.json",
    RUNS / "gate_570452_failure_signature_matrix.md",
    RUNS / "v3_clean_reconciliation_ledger.jsonl",
    RUNS / "gate_569016_report.json",
    SC / "d11_pre_repair_manifest.json", SC / "d11_repair.diff",
    SC / "d12_pre_repair_manifest.json", SC / "d12_repair.diff",
    SC / "d12_repair_record.json",
]
preserved = [rec(p) for p in candidates if p.exists()]
missing = [str(p.relative_to(ROOT)) for p in candidates if not p.exists()]

(GATES / "gate_570452_preservation_manifest.json").write_text(json.dumps({
    "generated_utc": NOW,
    "gate_job_id": "570452",
    "gate_state": "FAILED", "gate_exit_code": "1:0", "gate_passed": "1/19",
    "runners_rc0": "18/18",
    "classification": "VALIDATOR_ONLY_FALSE_FAILURE",
    "not_a_model_performance_result": True,
    "preserved": preserved, "n_preserved": len(preserved), "missing": missing,
    "remote_evidence": {
        "root": "/scratch/sychan552/innovation_deploy_root_v3_clean5",
        "gate_dir": "/scratch/sychan552/innovation_deploy_root_v3_clean5/"
                    "results/v3_clean/implementation/gate_570452",
        "slurm_out": "/scratch/sychan552/innovation_deploy_root_v3_clean5/"
                     "hpc_results/innovation/logs/slurm_570452_clean_gate.out",
        "note": "left untouched; never rerun, never overwritten"},
    "rerun_forbidden": True,
}, indent=2), encoding="utf-8")

audit = {
    "generated_utc": NOW,
    "runtime_version": "innov-v3.11-artifact-directory-initialization",
    "executable_status":
        "SUPERSEDED_FOR_EXECUTION_GATE_VALIDATOR_SCHEMA_MISMATCH",
    "superseded_by": "innov-v3.12-gate-validator-schema-alignment",
    "gate_570452": {"state": "FAILED", "exit_code": "1:0", "elapsed": "00:26:38",
                    "node": "gpu-a100-03", "passed": "1/19",
                    "runners_rc0": "18/18"},
    "validator_only": True,
    "runner_defect": False,
    "scientific_protocol_changed": False,
    "scientific_checks_passed_on_all_18_paths": True,
    "failing_validator_assertions": {
        "checkpoint_file_present": {"n_paths": 16,
                                    "wrong": "checkpoints/best_validation.pt",
                                    "actual": "checkpoints/best_val_mse.pt"},
        "baseline_no_checkpoint": {"n_paths": 2,
                                   "wrong": "checkpoints/ dir must be absent",
                                   "actual": "uniform tree; empty dir valid"},
        "artifact_completeness": {"n_paths": 2,
                                  "wrong": "shared list with train history",
                                  "actual": "baselines never train"},
    },
    "isolation": {"test_access": 0, "holdout_access": 0,
                  "formal_rows_submitted": "0/598",
                  "archive_isolated": True},
}
(IMPL / "v311_gate_validator_failure_audit.json").write_text(
    json.dumps(audit, indent=2), encoding="utf-8")
(IMPL / "v311_gate_validator_failure_audit.md").write_text(
    f"""# v3.11 Gate-validator failure audit (Gate 570452)

**Executable status: `SUPERSEDED_FOR_EXECUTION_GATE_VALIDATOR_SCHEMA_MISMATCH`**
(superseded by `{audit['superseded_by']}`)

Gate 570452 is classified **FAILED** and is a **validator-only false failure**
— never a model-performance result.

| field | value |
|---|---|
| state | FAILED |
| exit code | 1:0 |
| elapsed | 00:26:38 |
| node | gpu-a100-03 |
| gate passed | 1/19 |
| **runtime paths rc=0** | **18/18** |

## Only three validator assertions failed

1. `checkpoint_file_present` (16 paths) — looked for a hard-coded
   `best_validation.pt`; the runner writes `best_val_mse.pt`, declared by the
   manifest as `checkpoint_file` with a matching `sha256_file`.
2. `baseline_no_checkpoint` (2 paths) — required the `checkpoints/` DIRECTORY
   to be absent; the D11 uniform tree legitimately creates an empty one.
3. `artifact_completeness` (2 paths) — one shared required list containing
   `logs/train_history.csv`, which deterministic baselines never produce.

## Not affected

Runner behaviour, D11 fix, stochastic checkpoint restoration, and every
scientific check all passed. Test/holdout access = 0/0; formal submissions
remain 0/598.
""", encoding="utf-8")

print(f"[audit] preserved={len(preserved)} missing={len(missing)}")
if missing:
    for m in missing:
        print(f"[audit]   MISSING {m}")
print("[audit] wrote v311_gate_validator_failure_audit.json/.md and "
      "gates/gate_570452_preservation_manifest.json")
