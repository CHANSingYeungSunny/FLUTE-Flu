#!/usr/bin/env python
"""
q1_step_sweep.py — Advisor Question 1: parallel step=0..3 aggregation evidence
==============================================================================

WHY THIS SCRIPT EXISTS
----------------------
The advisor report (Q1) notes that `fixed_step, step=0` fixes the old
`mean_over_lead` bug (mixing different lead times), but that the CDC FluSight
convention keeps horizons 0/1/2/3 weeks as SEPARATE, independently-scored tasks
rather than selecting one representative horizon.

The report's suggestion (verbatim intent):

    "可补充生成 step=1, 2, 3（对应 2/3/4 周 ahead）的平行版本，作为附加证据
     展示在同一组图或附录表格中，而不是用来替换 step=0——这是'完善'而非
     '修正错误'，不属于必须项。"

So this script does NOT replace step=0. It ADDS step=1,2,3 as supplementary
evidence, and reports all four side by side.

PROVENANCE / REPRODUCIBILITY
----------------------------
This is a PURE RE-AGGREGATION of already-exported prediction CSVs. It performs
NO model training and NO inference — the exported CSVs already carry every
forecast step (column `step`, 0..L-1), so changing the aggregation policy is a
pandas groupby, not a re-run. Therefore this needs NO GPU.

Input CSVs (pulled from HPC Burgundy, per-horizon runs):
    data/predictions_miflu_L{24,36,48,60}_paper_protocol.csv
  Source on HPC:
    /scratch/sychan552/CHATTIME/Chattime/hpc_results/journal_evidence/
        full_H{L}/reps_1_to_10/predictions_miflu_L{L}_paper_protocol.csv

Outputs:
    results/ili/metrics/q1_step_sweep.csv
    results/ili/figures/fig_q1_step_sweep_L24_L60_step{0,1,2,3}.png  (per-step; combined 2x3 removed)
"""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from compute_miflu_indicators import aggregate_lead_time  # noqa: E402

DATA = os.path.join(PROJECT_ROOT, "data")
OUT_CSV = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                       "q1_step_sweep.csv")
FIG_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "figures")
# (combined 2x3 figure removed 2026-09; see make_per_step_figures)

HORIZONS = (24, 36, 48, 60)
STEPS = (0, 1, 2, 3)

PHYS_GT = "ground_truth_ili_phys"
PHYS_PR = "prediction_ili_phys"
Z_GT = "ground_truth_ili"
Z_PR = "prediction_ili"


def load_test(L: int) -> pd.DataFrame:
    path = os.path.join(DATA, f"predictions_miflu_L{L}_paper_protocol.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    if "split" not in df.columns:
        raise KeyError(f"{path} has no `split` column")
    test = df[df["split"] == "test"].copy()
    if test.empty:
        raise ValueError(f"{path}: no test rows (leakage guard)")
    return test


def metrics(gt: np.ndarray, pr: np.ndarray) -> tuple:
    gt = np.asarray(gt, dtype=float)
    pr = np.asarray(pr, dtype=float)
    return float(np.mean((gt - pr) ** 2)), float(np.mean(np.abs(gt - pr)))


def sweep() -> pd.DataFrame:
    rows = []
    curves = {}                       # (L, step) -> (dates, gt, pred)
    for L in HORIZONS:
        test = load_test(L)
        for step in STEPS:
            # ---- physical units (patient counts) ----
            phys = aggregate_lead_time(test, mode="fixed_step", step=step,
                                       gt_col=PHYS_GT, pred_col=PHYS_PR)
            mse_p, mae_p = metrics(phys["gt"], phys["pred"])
            # ---- z-space (paper metric space, Table V convention) ----
            zsp = aggregate_lead_time(test, mode="fixed_step", step=step,
                                      gt_col=Z_GT, pred_col=Z_PR)
            mse_z, mae_z = metrics(zsp["gt"], zsp["pred"])

            dates = pd.to_datetime(zsp["week_start_date"])
            curves[(L, step)] = (dates, phys["gt"].to_numpy(float),
                                 phys["pred"].to_numpy(float))
            rows.append({
                "L": L,
                "step": step,
                "lead_weeks": step + 1,          # step h == (h+1)-week ahead
                "n_weeks": int(len(zsp)),
                # Coverage matters: a longer L shrinks the evaluable window and
                # can EXCLUDE the COVID-era period entirely (see README note).
                "date_start": str(dates.min().date()),
                "date_end": str(dates.max().date()),
                "MSE_z": mse_z,
                "MAE_z": mae_z,
                "MSE_phys": mse_p,
                "MAE_phys": mae_p,
            })
            print(f"  L={L:2d} step={step} (lead={step+1}wk)  "
                  f"weeks={len(zsp):3d}  MSE_z={mse_z:.4f}  MAE_z={mae_z:.4f}")
    return pd.DataFrame(rows), curves


# NOTE: the old 2x3 combined figure (fig_q1_step_sweep_L24_L60.png) was removed
# on 2026-09; make_per_step_figures is now the only Q1 figure output.


def make_per_step_figures(curves: dict) -> list:
    """One PNG PER STEP (step=0..3), each containing the 4 horizons for that
    step. This is the 'split by step size' view: instead of one panel per
    horizon overlaying all 4 steps, each photo isolates a single lead time and
    shows how the four horizons behave at that lead time.

    NOTE (Advisor Q1 thesis): the four horizons are still kept SEPARATE inside
    each photo — we never re-merge lead times. We only reorganise the *layout*
    so each step gets its own file.
    """
    os.makedirs(FIG_DIR, exist_ok=True)
    out = []
    for step in STEPS:
        fig, axes = plt.subplots(2, 2, figsize=(13, 7))
        for ax, L in zip(axes.flat, HORIZONS):
            d0, gt0, _ = curves[(L, 0)]           # GT is step-independent
            d, _, pr = curves[(L, step)]
            ax.plot(d0, gt0, color="black", lw=1.9, label="Ground truth")
            ax.plot(d, pr, lw=1.3, ls="--", color="tab:red",
                    label=f"step={step} ({step + 1}-wk ahead)")
            ax.set_title(f"L={L}", fontsize=11, weight="bold")
            ax.set_ylabel("ILITOTAL (patients)")
            ax.grid(alpha=0.25)
            ax.legend(fontsize=7, loc="upper left")
            ax.tick_params(labelsize=7)
        fig.suptitle(
            f"Advisor Q1 — step={step} ({step + 1}-week ahead) aggregation\n"
            "Pure re-aggregation of exported prediction CSVs; no retraining",
            fontsize=11, weight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        path = os.path.join(FIG_DIR,
                            f"fig_q1_step_sweep_L24_L60_step{step}.png")
        fig.savefig(path, dpi=190)
        plt.close(fig)
        out.append(path)
    return out


def main() -> None:
    print("[q1_step_sweep] sweeping step=0..3 over L=24/36/48/60 "
          "(pure re-aggregation, no GPU)")
    df, curves = sweep()
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"[q1_step_sweep] wrote {OUT_CSV}")
    step_figs = make_per_step_figures(curves)
    for sf in step_figs:
        print(f"[q1_step_sweep] wrote {sf}")

    print("\n=== step sweep summary (MSE in z-space) ===")
    piv = df.pivot(index="L", columns="step", values="MSE_z")
    piv.columns = [f"step{c}" for c in piv.columns]
    print(piv.to_string(float_format=lambda v: f"{v:.4f}"))


if __name__ == "__main__":
    main()
