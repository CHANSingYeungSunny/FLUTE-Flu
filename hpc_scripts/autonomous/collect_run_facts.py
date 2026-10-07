"""collect_run_facts.py — read-only per-run facts dump for audit.

Lives OUTSIDE the frozen innovation source hash (`hpc_scripts/autonomous/`), so it
never changes the runtime aggregate. It walks `results/innovation/runs/*/` and emits
one compact JSON record per run (governance + resource fields + artifact presence).

Usage:  python hpc_scripts/autonomous/collect_run_facts.py <deployment_root> [out.json]
"""
from __future__ import annotations

import glob
import json
import os
import sys

_FIELDS = (
    "status", "experiment_stage", "model_key", "horizon", "seed",
    "train_seconds", "trainable_parameters", "total_parameters", "device_name",
    "test_artifacts_written", "test_access_allowed", "source_snapshot_sha256",
    "checkpoint_sha256", "restore_ok", "best_val_mse", "val_mae_all_z",
    "peak_hit_ratio", "implementation_source_version", "protocol_version",
)


def collect(root: str) -> list:
    runs = os.path.join(root, "results", "innovation", "runs")
    out = []
    for d in sorted(glob.glob(os.path.join(runs, "*"))):
        if not os.path.isdir(d):
            continue
        rec = {"run_id": os.path.basename(d)}
        try:
            with open(os.path.join(d, "run_status.json"), "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            st = {}
        for k in _FIELDS:
            rec[k] = st.get(k)
        rec["has_checkpoint_manifest"] = os.path.exists(
            os.path.join(d, "checkpoints", "checkpoint_manifest.json"))
        rec["has_checkpoint_pt"] = bool(glob.glob(os.path.join(d, "checkpoints", "*.pt")))
        rec["has_val_pred"] = os.path.exists(
            os.path.join(d, "predictions", "validation_predictions.csv"))
        rec["has_val_metrics"] = os.path.exists(
            os.path.join(d, "metrics", "validation_metrics.json"))
        rec["has_peak_by_season"] = os.path.exists(
            os.path.join(d, "metrics", "peak_metrics_by_season.csv"))
        rec["has_test_pred"] = os.path.exists(
            os.path.join(d, "predictions", "test_predictions.csv"))
        rec["has_test_metrics"] = os.path.exists(
            os.path.join(d, "metrics", "test_metrics.json"))
        rec["n_figures"] = len(glob.glob(os.path.join(d, "figures", "*")))
        out.append(rec)
    return out


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    root = argv[0] if argv else "."
    out = argv[1] if len(argv) > 1 else os.path.join(root, "runs_facts.json")
    facts = collect(root)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=1)
    print("[collect_run_facts] wrote %s (%d runs)" % (out, len(facts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
