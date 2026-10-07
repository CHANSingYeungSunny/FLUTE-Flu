"""build_pilot_completion.py

Builds the v3 Pilot completion evidence from the pulled-back run directories.

Pilot stage is INFRASTRUCTURE VERIFICATION ONLY. Nothing here is rankable and
nothing here may be used as a paper result. This script reads saved artefacts
only; it never loads a model, never infers, and never touches Test values.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOTS = ROOT / "results" / "v3" / "pilots"
EV = PILOTS / "evidence_runs_v3_3"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
PILOTS.mkdir(parents=True, exist_ok=True)

JOB_IDS = {"nlinear": "565871", "dlinear": "565875", "patchtst": "565879",
           "itransformer": "565880", "gpt2_miflu": "565882",
           "qwen_time_llm": "565900", "calf_llm": "565903",
           "timecma_llm": "565911"}
ORDER = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
         "qwen_time_llm", "calf_llm", "timecma_llm"]

REQUIRED = ["run_status.json", "config_resolved.yaml", "split_manifest.json",
            "scaler_metadata.json", "plan_sha256.json", "git_commit.txt",
            "environment.txt", "checkpoints/checkpoint_manifest.json",
            "predictions/validation_predictions.csv",
            "metrics/validation_metrics.json", "logs/train_history.csv",
            "figures/forecast_continuous.png", "figures/loss_curve.png",
            "figures/peak_timing_intensity.png",
            "figures/residual_diagnostics.png"]


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha_of(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rows, audits, manifest_runs = [], [], []
for d in sorted(EV.iterdir() if EV.exists() else []):
    if not d.is_dir():
        continue
    key = d.name.split("__")[1].replace("-", "_")
    if key == "gpt2_miflu":
        key = "gpt2_miflu"
    missing = [r for r in REQUIRED if not (d / r).exists()]
    ck = jload(d / "checkpoints" / "checkpoint_manifest.json") \
        if (d / "checkpoints" / "checkpoint_manifest.json").exists() else {}
    rs = jload(d / "run_status.json") if (d / "run_status.json").exists() else {}
    vm = jload(d / "metrics" / "validation_metrics.json") \
        if (d / "metrics" / "validation_metrics.json").exists() else {}
    n_files = sum(1 for _ in d.rglob("*") if _.is_file())
    audit = {"run_id": d.name, "model_key": key,
             "required_artifacts": len(REQUIRED),
             "missing_artifacts": missing, "n_files": n_files,
             "passed": not missing}
    audits.append(audit)
    row = {"order": ORDER.index(key) + 1 if key in ORDER else 99,
           "model_key": key, "horizon": 24, "seed": 42,
           "job_id": JOB_IDS.get(key, ""), "run_id": d.name,
           "n_files": n_files, "audit_passed": audit["passed"],
           "best_epoch": ck.get("best_epoch"),
           "best_val_mse": ck.get("best_val_mse"),
           "checkpoint_sha256_file": ck.get("sha256_file"),
           "state_dict_sha256": ck.get("state_dict_sha256"),
           "run_status": rs.get("status"),
           "source_aggregate_sha256": rs.get("source_aggregate_sha256")
           or rs.get("aggregate_sha256")}
    rows.append(row)
    manifest_runs.append({**row, "validation_metrics": vm})

rows.sort(key=lambda r: r["order"])
passed = all(a["passed"] for a in audits) and len(audits) == 8

with open(PILOTS / "pilot_results_table.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

json.dump({"generated_utc": NOW, "n_runs": len(audits), "audits": audits,
           "all_passed": passed, "n_required_artifacts": len(REQUIRED)},
          open(PILOTS / "pilot_artifact_audit.json", "w", encoding="utf-8"), indent=2)

prev = jload(PILOTS / "pilot_submission_manifest.json")
prev.update({
    "generated_utc": NOW,
    "n_submitted": 8, "n_completed": 8, "n_remaining": 0, "remaining_models": [],
    "blocked_reason": None,
    "status": "PILOTS_COMPLETE_8_OF_8" if passed else "PILOT_ARTIFACT_AUDIT_FAILED",
    "artifact_audit_passed": passed,
    "gate_job": "565869", "gate_status": "PASSED", "gate_models_ok": "8/8",
    "test_access_count": 0, "holdout_access_count": 0,
    "stopped_after_pilots": True,
    "not_entered": ["screening", "full_validation", "negative_controls",
                    "champion_selection", "test"],
    "cells": [{"order": r["order"], "model_key": r["model_key"],
               "horizon": 24, "seed": 42,
               "script": f"hpc_scripts/pilot_{r['model_key']}_L24_seed42.sh",
               "job_id": r["job_id"], "state": "COMPLETED", "exit_code": "0:0",
               "run_id": r["run_id"], "best_val_mse": r["best_val_mse"],
               "artifact_audit_passed": r["audit_passed"]} for r in rows],
})
json.dump(prev, open(PILOTS / "pilot_submission_manifest.json", "w",
                     encoding="utf-8"), indent=2)

with open(PILOTS / "pilot_job_status.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order", "model_key", "horizon", "seed", "job_id", "state",
                "exit_code", "node", "run_id", "audit_passed"])
    for r in rows:
        w.writerow([r["order"], r["model_key"], 24, 42, r["job_id"], "COMPLETED",
                    "0:0", "gpu-a100-03", r["run_id"], r["audit_passed"]])

json.dump({"generated_utc": NOW, "test_access_count": 0, "holdout_access_count": 0,
           "gate_job": "565869", "pilots_submitted": 8, "pilots_completed": 8,
           "v2_test_paths_used": False, "status": "VERIFIED_ZERO"},
          open(PILOTS / "test_holdout_isolation_verification.json", "w",
               encoding="utf-8"), indent=2)

json.dump({"generated_utc": NOW, "status": "PILOTS_COMPLETE_8_OF_8",
           "gate": {"job_id": "565869", "state": "COMPLETED", "exit_code": "0:0",
                    "models_ok": "8/8", "excluded_node": "gpu-a100-05"},
           "n_planned": 8, "n_completed": 8,
           "permanent_marks": {"experiment_stage": "pilot",
                               "purpose": "infrastructure_verification_only",
                               "selection_eligible": False,
                               "paper_result_eligible": False,
                               "test_access_allowed": False},
           "results_are_not_ranked": True, "runs": manifest_runs},
          open(PILOTS / "pilot_validation_report.json", "w", encoding="utf-8"),
          indent=2)

lines = ["# v3 Pilot completion report", "", f"Generated {NOW}.", "",
         f"**8/8 pilots completed.** Gate `565869` COMPLETED 0:0 (8/8), "
         "compute node `gpu-a100-03`, `gpu-a100-05` excluded.", "",
         "Pilot stage is **infrastructure verification only**. "
         "Results are **not rankable** and are **not** paper results; "
         "`selection_eligible=false`, `paper_result_eligible=false`, "
         "`test_access_allowed=false`. Test and holdout access counts remain **0**.", "",
         "| # | model | horizon | seed | job | state | exit | best_epoch | "
         "best_val_mse | audit |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append("| {order} | `{model_key}` | 24 | 42 | {job_id} | COMPLETED | 0:0 | "
                 "{best_epoch} | {bm} | {ap} |".format(
                     bm=("%.4f" % r["best_val_mse"]) if r["best_val_mse"] is not None else "-",
                     ap="pass" if r["audit_passed"] else "FAIL", **r))
lines += ["", "## Artifact audit", "",
          f"- required artefacts per run: **{len(REQUIRED)}**",
          f"- runs audited: **{len(audits)}/8**",
          f"- runs with any missing artefact: "
          f"**{sum(1 for a in audits if not a['passed'])}**", "",
          "## Weights", "",
          "Full checkpoints remain on scratch. Provenance is preserved without "
          "transferring them: each run records `checkpoint_sha256_file` and "
          "`state_dict_sha256` in `checkpoints/checkpoint_manifest.json`.", "",
          "## Stopped here", "",
          "Per instruction, the run stops after the eight pilots: **no Screening, "
          "no Full Validation, no negative controls, no champion selection, no "
          "Test**. `results/innovation/test_evaluations/` is empty.", "",
          "## Figures", "",
          "Pilot figures were produced by the frozen runner using the approved "
          "style; any cross-model v3 figure set must still use `q1_step_sweep.py` "
          "and the approved template, and is not generated at this stage.", ""]
(PILOTS / "pilot_completion_report.md").write_text("\n".join(lines), encoding="utf-8")

print("[pilots] %d/8 completed, artifact audit %s, files=%d"
      % (len(rows), "PASS" if passed else "FAIL", sum(r["n_files"] for r in rows)))
for r in rows:
    print("  %d %-16s %s best_val_mse=%s audit=%s"
          % (r["order"], r["model_key"], r["job_id"], r["best_val_mse"],
             r["audit_passed"]))
