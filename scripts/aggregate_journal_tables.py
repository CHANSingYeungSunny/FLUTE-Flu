#!/usr/bin/env python
"""
aggregate_journal_tables.py — Build the journal Table VIII + Supplementary table
================================================================================
Consumes the per-experiment `metrics.csv` / `summary.csv` files written by
`train_ablation.py` under `hpc_results/journal_evidence/<exp>/reps_1_to_10/`
and produces:

  * journal_table_viii.csv / .md  — mean±std over the 10 reps for every
    experiment (Primary track, z-space per MIFlu §V-B).
  * journal_table_physical.csv/.md — SUPPLEMENTARY de-normalised (patient-count)
    metrics, clearly labelled as not the paper's primary numbers.

Experiment labels follow the naming used by run_journal_experiments.py:
  full, no_multi, no_lora, no_lora_multi                (Table VIII variants)
  full__adamw_cosine, full__huber_clip                  (recipe sweep, Q4)
  full__earlystop                                       (peak-aware ES, Q5)

Usage:
  python scripts/aggregate_journal_tables.py
  python scripts/aggregate_journal_tables.py --root hpc_results/journal_evidence
"""
from __future__ import annotations

import argparse
import os
import glob
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_ROOT = os.path.join(PROJECT_ROOT, "hpc_results", "journal_evidence")

# Table VIII uses 10 repetitions per experiment. Any variant with fewer valid
# reps is INCOMPLETE and must be EXCLUDED so partial/legacy reps cannot skew
# the reported mean/std (defence-in-depth for data purity).
REQUIRED_REPS = 10


def _read_metrics(exp_dir: str) -> pd.DataFrame | None:
    cand = glob.glob(os.path.join(exp_dir, "metrics.csv"))
    if not cand:
        return None
    df = pd.read_csv(cand[0])
    return df


def aggregate_experiment(name: str, exp_dir: str) -> dict | None:
    df = _read_metrics(exp_dir)
    if df is None or len(df) == 0:
        print(f"  [INCOMPLETE] {name}: no metrics.csv - EXCLUDED")
        return None
    discarded = df.get("discarded", pd.Series(False, index=df.index))
    if "mse_all" in df.columns:
        finite = df["mse_all"].apply(
            lambda v: isinstance(v, (int, float)) and np.isfinite(v))
    else:
        finite = pd.Series(False, index=df.index)
    ok = df[~discarded & finite]
    n_valid = int(len(ok))
    if n_valid < REQUIRED_REPS:
        print(f"  [INCOMPLETE] {name}: only {n_valid}/{REQUIRED_REPS} valid reps "
              f"- EXCLUDED from journal table (partial/legacy reps would skew mean/std)")
        return None
    preds = glob.glob(os.path.join(exp_dir, "predictions_miflu_L*_paper_protocol.csv"))
    if not preds:
        print(f"  [INCOMPLETE] {name}: missing prediction_*.csv - EXCLUDED")
        return None

    # ── PHASE 4 strict artifact tree ──
    # Each rep_N/ must carry the FULL artifact set: the epoch-by-epoch
    # metrics.csv, the dual-track prediction CSV, and checkpoints/best_model.pt.
    # A rep missing any of the three is not publishable evidence.
    rep_dirs = sorted(glob.glob(os.path.join(exp_dir, "rep_*")))
    complete_reps = 0
    for rd in rep_dirs:
        has_metrics = os.path.exists(os.path.join(rd, "metrics.csv"))
        has_pred = bool(glob.glob(
            os.path.join(rd, "predictions_miflu_L*_paper_protocol.csv")))
        has_ckpt = bool(glob.glob(
            os.path.join(rd, "checkpoints", "best_model_L*.pt")))
        if has_metrics and has_pred and has_ckpt:
            complete_reps += 1
        else:
            missing = [lbl for lbl, ok in
                       (("metrics.csv", has_metrics),
                        ("predictions", has_pred),
                        ("checkpoints/best_model_L*.pt", has_ckpt)) if not ok]
            print(f"    [rep-incomplete] {name}/{os.path.basename(rd)}: "
                  f"missing {', '.join(missing)}")
    if rep_dirs and complete_reps < REQUIRED_REPS:
        print(f"  [INCOMPLETE] {name}: only {complete_reps}/{REQUIRED_REPS} reps "
              f"carry the full artifact set - EXCLUDED")
        return None

    row = {
        "experiment": name,
        "n_reps": n_valid,
        "n_complete_reps": complete_reps,
        "MSE_AllVars_mean": ok["mse_all"].mean(),
        "MSE_AllVars_std": ok["mse_all"].std(),
        "MAE_AllVars_mean": ok["mae_all"].mean(),
        "MAE_AllVars_std": ok["mae_all"].std(),
        "MSE_ILITotal_mean": ok["mse_ili"].mean(),
        "MSE_ILITotal_std": ok["mse_ili"].std(),
        "MAE_ILITotal_mean": ok["mae_ili"].mean(),
        "MAE_ILITotal_std": ok["mae_ili"].std(),
        # SUPPLEMENTARY physical track (patient counts) — not the paper's primary.
        "MSE_ILITotal_phys_mean": ok["mse_ili_phys"].mean(),
        "MAE_ILITotal_phys_mean": ok["mae_ili_phys"].mean(),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out", default=None, help="Output dir (default: <root>)")
    args = ap.parse_args()
    root = args.root
    out_dir = args.out or root
    os.makedirs(out_dir, exist_ok=True)

    # Each experiment is a directory containing reps_1_to_10/metrics.csv
    exp_dirs = []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d):
            continue
        if os.path.exists(os.path.join(d, "reps_1_to_10", "metrics.csv")):
            exp_dirs.append((os.path.basename(d), os.path.join(d, "reps_1_to_10")))
        elif os.path.exists(os.path.join(d, "metrics.csv")):
            exp_dirs.append((os.path.basename(d), d))

    if not exp_dirs:
        print(f"[ERROR] no experiment metrics found under {root}")
        print("Run: python scripts/run_journal_experiments.py  first.")
        return 2

    rows = []
    for name, d in exp_dirs:
        r = aggregate_experiment(name, d)
        if r:
            rows.append(r)
    if not rows:
        print("[ERROR] all experiments skipped (no valid metrics).")
        return 2

    table = pd.DataFrame(rows)

    # ---- Table VIII (PRIMARY, z-space) ----
    viii_cols = ["experiment", "n_reps",
                 "MSE_AllVars_mean", "MSE_AllVars_std",
                 "MAE_AllVars_mean", "MAE_AllVars_std",
                 "MSE_ILITotal_mean", "MSE_ILITotal_std",
                 "MAE_ILITotal_mean", "MAE_ILITotal_std"]
    viii = table[viii_cols]
    viii.to_csv(os.path.join(out_dir, "journal_table_viii.csv"), index=False)

    # ---- Supplementary PHYSICAL table ----
    phys_cols = ["experiment", "n_reps",
                 "MSE_ILITotal_phys_mean", "MAE_ILITotal_phys_mean"]
    phys = table[phys_cols]
    phys.to_csv(os.path.join(out_dir, "journal_table_physical.csv"), index=False)

    # ---- Markdown render ----
    def _md(df: pd.DataFrame, title: str) -> str:
        s = f"# {title}\n\n"
        s += "| " + " | ".join(df.columns) + " |\n"
        s += "|" + "|".join(["---"] * len(df.columns)) + "|\n"
        for _, r in df.iterrows():
            cells = []
            for c in df.columns:
                v = r[c]
                cells.append(f"{v:.6f}" if isinstance(v, float) else str(v))
            s += "| " + " | ".join(cells) + " |\n"
        return s

    with open(os.path.join(out_dir, "journal_table_viii.md"), "w") as f:
        f.write(_md(viii, "Table VIII — Ablation (PRIMARY, z-space, per MIFlu §V-B)"))
    with open(os.path.join(out_dir, "journal_table_physical.md"), "w") as f:
        f.write(_md(phys, "Supplementary — de-normalised ILITOTAL (patient counts)"))

    print(f"[OK] wrote journal_table_viii.* and journal_table_physical.* to {out_dir}")
    print(viii.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
