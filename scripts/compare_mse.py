#!/usr/bin/env python
"""compare_mse.py — read journal_table_viii.csv and emit per-variant MSE mean/std
as evidence for the ablation comparison."""
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SRC = os.path.join(PROJECT_ROOT, "results", "ili", "core4_table",
                   "journal_table_viii.csv")
OUT = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                   "mse_comparison_evidence.csv")


def main():
    rows = []
    with open(SRC, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "experiment": r["experiment"],
                "n_reps": r["n_reps"],
                "MSE_AllVars_mean": r["MSE_AllVars_mean"],
                "MSE_AllVars_std": r["MSE_AllVars_std"],
                "MAE_AllVars_mean": r["MAE_AllVars_mean"],
                "MAE_AllVars_std": r["MAE_AllVars_std"],
            })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fields = ["experiment", "n_reps", "MSE_AllVars_mean", "MSE_AllVars_std",
              "MAE_AllVars_mean", "MAE_AllVars_std"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[mse] wrote {OUT}")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
