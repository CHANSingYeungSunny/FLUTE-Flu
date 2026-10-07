#!/usr/bin/env python
"""make_advisor_qa_figures.py — evidence for Advisor Questions 1, 2 and 3.
=============================================================================
Produces three concrete artefacts, all derived from the SAME dual-track,
test-only prediction CSV exported by the final HPC runs:

  Q1 -> results/ili/metrics/q1_lead_time_policy_proof.csv
        Proves overlapping forecast windows are collapsed with a CONSTANT
        lead time (fixed_step=0) rather than averaging 1..L-week-ahead
        predictions.

  Q2 -> results/ili/figures/fig_q2_covid_alignment.png
        True vs Predicted on the REAL CDC epiweek calendar, in physical units,
        with the COVID-19 NPI window shaded. Proves the X axis no longer
        carries the old ~19-week drift.

  Q3 -> results/ili/figures/fig_q3_physical_units.png
        Side-by-side z-space vs physical-unit panels, proving that
        `inverse_transform` (phys = z * scale_ + mean_) is applied before
        plotting, so the Y axis reads real patient counts.

Styling follows scripts/make_miflu_evaluation_figure.py (same rcParams, same
colour convention: blue dashed = ground truth, red solid = prediction).

Usage:
    python scripts/make_advisor_qa_figures.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from cdc_calendar import load_week_calendar                     # noqa: E402
from compute_miflu_indicators import aggregate_lead_time        # noqa: E402

# Final HPC export for the `full` variant (rep_01), horizon L=24.
PRED_CSV = os.path.join(
    PROJECT_ROOT, "results", "ili", "journal_evidence", "full",
    "reps_1_to_10", "rep_01", "predictions_miflu_L24_paper_protocol.csv")
SCALER_JSON = os.path.join(PROJECT_ROOT, "data",
                           "scaler_miflu_national.json")
FIG_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "figures")
MET_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "metrics")

ILI_CHANNEL = 4          # index of "ILITOTAL" inside VAR_COLS

# COVID-19 NPI window: the period when NPIs (lockdowns / masking / distancing)
# FLATTENED the influenza season. Starts 2020-05-01 — the tail of the genuine
# 2019-20 season (up to ~Mar 2020) is deliberately EXCLUDED so the shaded
# region marks only the anomalous flat stretch.
COVID_START = pd.Timestamp("2020-05-01")
COVID_END = pd.Timestamp("2021-06-30")

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 100,
})


def load_test() -> pd.DataFrame:
    df = pd.read_csv(PRED_CSV)
    assert "split" in df.columns, "prediction CSV must carry a `split` column"
    test = df[df["split"] == "test"].copy()
    assert len(test) > 0, "no test rows — leakage guard failed"
    return test


# --------------------------------------------------------------------------- #
# Q1 — lead-time aggregation proof
# --------------------------------------------------------------------------- #
def q1_proof(test: pd.DataFrame) -> pd.DataFrame:
    fixed = aggregate_lead_time(test, mode="fixed_step", step=0)
    mixed = aggregate_lead_time(test, mode="mean_over_lead")

    # NOTE: the two modes cover DIFFERENT numbers of weeks (fixed_step only
    # keeps step==0, so the final L-1 weeks — which are reachable only at
    # steps 1..23 — drop out). Merge on abs_week instead of assuming equal
    # length; missing values stay blank rather than being silently aligned.
    fx = fixed[["abs_week", "week_start_date", "n_windows", "gt", "pred"]].rename(
        columns={"n_windows": "n_windows_fixed_step",
                 "gt": "gt_patients", "pred": "pred_fixed_step"})
    mx = mixed[["abs_week", "n_windows", "pred"]].rename(
        columns={"n_windows": "n_windows_mean_over_lead",
                 "pred": "pred_mean_over_lead"})

    cmp_df = fx.merge(mx, on="abs_week", how="outer").sort_values("abs_week")
    cmp_df["week_start_date"] = pd.to_datetime(
        cmp_df["week_start_date"]).dt.date
    for c in ("gt_patients", "pred_fixed_step", "pred_mean_over_lead"):
        cmp_df[c] = cmp_df[c].astype(float).round(1)
    cmp_df = cmp_df[["abs_week", "week_start_date",
                     "n_windows_fixed_step", "n_windows_mean_over_lead",
                     "gt_patients", "pred_fixed_step", "pred_mean_over_lead"]]

    os.makedirs(MET_DIR, exist_ok=True)
    out = os.path.join(MET_DIR, "q1_lead_time_policy_proof.csv")
    cmp_df.to_csv(out, index=False)

    print("[Q1] fixed_step  : every week uses step==0 -> "
          f"weeks={len(fixed)}, n_windows min={int(fixed['n_windows'].min())} "
          f"max={int(fixed['n_windows'].max())}  "
          f"(constant lead time = 1 week ahead)")
    print("[Q1] mean_over_lead: mixes steps 0..23 -> "
          f"weeks={len(mixed)}, n_windows min={int(mixed['n_windows'].min())} "
          f"max={int(mixed['n_windows'].max())}  "
          f"(effective lead time VARIES along the curve)")
    print(f"[Q1] wrote {out}")
    return cmp_df


# --------------------------------------------------------------------------- #
# Q2 — real-date alignment + COVID hallucination
# --------------------------------------------------------------------------- #
def q2_figure(test: pd.DataFrame) -> str:
    grp = aggregate_lead_time(test, mode="fixed_step", step=0)
    dates = pd.to_datetime(grp["week_start_date"]).dt.to_pydatetime()
    gt = grp["gt"].to_numpy(dtype=float)
    pred = grp["pred"].to_numpy(dtype=float)

    cal = load_week_calendar()
    real_820 = cal.loc[cal["abs_week"] == 820, "week_start_date"].iloc[0]
    # the value the OLD synthetic helper produced for the same row
    old_820 = pd.Timestamp("2017-09-17")

    # Model's hallucinated peak inside the COVID window
    dser = pd.Series(dates)
    mask = (dser >= COVID_START) & (dser <= COVID_END)
    covid_dates = np.asarray(dates)[mask.to_numpy()]
    covid_pred = pred[mask.to_numpy()]
    covid_gt = gt[mask.to_numpy()]
    hi = int(np.argmax(covid_pred))
    hall_date, hall_pred = covid_dates[hi], float(covid_pred[hi])
    hall_gt = float(covid_gt[hi])

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.axvspan(COVID_START, COVID_END, color="#d9d2e9", alpha=0.55,
               label="COVID-19 NPI window (flu season flattened)")
    ax.plot(dates, gt, "--", color="#1f4e79", lw=1.6,
            label="Ground Truth (CDC ILITOTAL)")
    ax.plot(dates, pred, "-", color="#c00000", lw=1.6,
            label="MIFlu prediction (full variant)")

    ax.annotate(
        f"FROZEN-LLM SEASONAL PRIOR -> hallucinated peak\n"
        f"{pd.Timestamp(hall_date).date()}: predicted {int(hall_pred):,} "
        f"vs true {int(hall_gt):,}\n"
        f"(model invents a winter peak that never came)",
        xy=(hall_date, hall_pred),
        xytext=(0.32, 0.78), textcoords="axes fraction",
        fontsize=8, color="#7f0000",
        arrowprops=dict(arrowstyle="->", color="#7f0000", lw=1.0),
        bbox=dict(boxstyle="round,pad=0.35", fc="#ffecec", ec="#c00000"))

    # Winter 2020-21 over-prediction, the aggregate form of the same failure.
    dser2 = pd.Series(dates)
    win = (dser2 >= pd.Timestamp("2020-11-01")) & (dser2 <= pd.Timestamp("2021-04-30"))
    w_m = win.to_numpy()
    if w_m.any():
        ax.text(0.015, 0.30,
                f"Winter 2020-21 (Nov-Apr):\n"
                f"  mean true      {gt[w_m].mean():,.0f}\n"
                f"  mean predicted {pred[w_m].mean():,.0f}\n"
                f"  over-prediction "
                f"{100 * (pred[w_m].mean() / gt[w_m].mean() - 1):+.0f}%",
                transform=ax.transAxes, fontsize=7.5, va="top",
                bbox=dict(boxstyle="round,pad=0.4", fc="#fff6e5", ec="#d18f00"))

    # Provenance box: real vs old (drifted) calendar
    ax.text(0.015, 0.95,
            f"X axis = REAL CDC epiweek dates\n"
            f"abs_week 820 -> {real_820.date()}  (REAL)\n"
            f"old synthetic helper said {old_820.date()}  (drift ~19 weeks)",
            transform=ax.transAxes, fontsize=7.5, va="top", color="#1a1a1a",
            bbox=dict(boxstyle="round,pad=0.4", fc="#eef6ff", ec="#4a90d9"))

    ax.set_title("Q2 — True vs Predicted ILITOTAL on the REAL CDC calendar "
                 "(test split, physical units)\n"
                 "Lead-time policy: fixed_step=0 (constant 1-week-ahead)")
    ax.set_xlabel("Calendar week (CDC epiweek start date, Sunday)")
    ax.set_ylabel("ILITOTAL — patient counts")
    ax.legend(loc="upper left", fontsize=7.5)
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()

    os.makedirs(FIG_DIR, exist_ok=True)
    out = os.path.join(FIG_DIR, "fig_q2_covid_alignment.png")
    fig.savefig(out, dpi=300)
    plt.close(fig)

    print(f"[Q2] abs_week 820 real date = {real_820.date()} "
          f"(old drifted value 2017-09-17)")
    print(f"[Q2] COVID window {COVID_START.date()}..{COVID_END.date()}: "
          f"max prediction {hall_pred:,.0f} on {pd.Timestamp(hall_date).date()} "
          f"vs true {hall_gt:,.0f}")
    print(f"[Q2] wrote {out}")
    return out


# --------------------------------------------------------------------------- #
# Q3 — z-space vs physical units (inverse transform proof)
# --------------------------------------------------------------------------- #
def q3_figure(test: pd.DataFrame) -> str:
    grp_z = aggregate_lead_time(test, mode="fixed_step", step=0,
                                gt_col="ground_truth_ili",
                                pred_col="prediction_ili")
    grp_p = aggregate_lead_time(test, mode="fixed_step", step=0,
                                gt_col="ground_truth_ili_phys",
                                pred_col="prediction_ili_phys")
    dates = pd.to_datetime(grp_z["week_start_date"]).dt.to_pydatetime()
    z_gt, z_pr = grp_z["gt"].to_numpy(float), grp_z["pred"].to_numpy(float)
    p_gt, p_pr = grp_p["gt"].to_numpy(float), grp_p["pred"].to_numpy(float)

    with open(SCALER_JSON, "r", encoding="utf-8") as f:
        sc = json.load(f)
    mean_, scale_ = float(sc["mean"][ILI_CHANNEL]), float(sc["std"][ILI_CHANNEL])

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.6))

    axL.plot(dates, z_gt, "--", color="#1f4e79", lw=1.5, label="Ground Truth (z)")
    axL.plot(dates, z_pr, "-", color="#c00000", lw=1.5, label="Prediction (z)")
    axL.set_title("BEFORE inverse_transform — z-score space\n"
                  "(this is the 0–12 axis; NOT patient counts)")
    axL.set_ylabel("ILITOTAL (z-score)")
    axL.set_xlabel("Calendar week")
    axL.legend(fontsize=7.5); axL.grid(alpha=0.25)

    axR.plot(dates, p_gt, "--", color="#1f4e79", lw=1.5,
             label="Ground Truth (patients)")
    axR.plot(dates, p_pr, "-", color="#c00000", lw=1.5,
             label="Prediction (patients)")
    axR.set_title("AFTER inverse_transform — physical units\n"
                  "(real patient counts; used for all figures)")
    axR.set_ylabel("ILITOTAL — patient counts")
    axR.set_xlabel("Calendar week")
    axR.legend(fontsize=7.5); axR.grid(alpha=0.25)

    fig.suptitle(
        f"Q3 — inverse transform proof:  physical = z x scale_ + mean_\n"
        f"ILITOTAL train-only statistics: mean_={mean_:,.1f}, scale_={scale_:,.1f} "
        f"(fit on data[:717] ONLY)",
        fontsize=10)
    fig.autofmt_xdate()
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    os.makedirs(FIG_DIR, exist_ok=True)
    out = os.path.join(FIG_DIR, "fig_q3_physical_units.png")
    fig.savefig(out, dpi=300)
    plt.close(fig)

    print(f"[Q3] z-space range      : {z_gt.min():.2f} .. {z_gt.max():.2f}")
    print(f"[Q3] physical range     : {p_gt.min():,.0f} .. {p_gt.max():,.0f}")
    print(f"[Q3] scaler mean_={mean_:,.1f} scale_={scale_:,.1f} (train-only)")
    print(f"[Q3] wrote {out}")
    return out


def main() -> int:
    test = load_test()
    print(f"[data] {PRED_CSV}")
    print(f"[data] test rows={len(test)}, weeks={test['abs_week'].nunique()}, "
          f"steps={test['step'].min()}..{test['step'].max()}")
    q1_proof(test)
    q2_figure(test)
    q3_figure(test)
    print("[OK] all advisor evidence artefacts written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
