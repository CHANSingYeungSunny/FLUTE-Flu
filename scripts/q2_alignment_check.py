#!/usr/bin/env python
"""
q2_alignment_check.py — Advisor Question 2: date-range printout + alignment cross-check
=======================================================================================

The advisor report (Q2) asks for TWO independent, code-level checks that do NOT
depend on literature:

  (b) "建议在代码中直接 print 测试集起止日期加以确认" — confirm the test split
      really covers the COVID 2020–2021 window.

  (a) "交叉验证法：单独挑选若干个非异常年份（如 2015–2019 正常流感季）画出同款
      连续预测图。若这些年份中红蓝两线吻合良好（无论幅度还是峰值周），说明整体
      index 对齐、绘图逻辑没有问题，只有 COVID 年份出现异常，从而支持'分布漂移'
      而非'索引错位'的解释。"

This script implements both. It is a PURE RE-AGGREGATION of exported prediction
CSVs — no training, no inference, NO GPU REQUIRED.

Output:
    results/ili/metrics/q2_alignment_check.csv
    results/ili/figures/fig_q2_alignment_precovid_vs_covid.png
    stdout: the test-split start/end dates (the direct verification)
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
                       "q2_alignment_check.csv")
FIG_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "figures")
OUT_FIG = os.path.join(FIG_DIR, "fig_q2_alignment_precovid_vs_covid.png")

HORIZONS = (24, 36, 48, 60)

# COVID-era boundary. Pre-COVID = the NORMAL influenza seasons present in the
# test split (2018–2019). Using 2020-01-01 because NPI-driven ILI collapse in
# the US began during the 2019–20 season's second half.
COVID_BOUNDARY = pd.Timestamp("2020-01-01")

PHYS_GT = "ground_truth_ili_phys"
PHYS_PR = "prediction_ili_phys"


def load_test(L: int) -> pd.DataFrame:
    path = os.path.join(DATA, f"predictions_miflu_L{L}_paper_protocol.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    test = df[df["split"] == "test"].copy()
    if test.empty:
        raise ValueError(f"{path}: no test rows")
    return test


def segment_metrics(dates: pd.Series, gt: np.ndarray, pr: np.ndarray) -> dict:
    """Alignment diagnostics for one contiguous segment."""
    gt = np.asarray(gt, dtype=float)
    pr = np.asarray(pr, dtype=float)
    n = len(gt)
    out = {"n_weeks": int(n)}
    if n < 3:
        out.update(pearson_r=np.nan, mse=np.nan, mae=np.nan,
                   peak_timing_diff_weeks=np.nan, gt_peak=np.nan,
                   pred_peak=np.nan)
        return out
    # Pearson correlation: the single best "are the two curves in register?"
    # statistic. High r => indices are aligned, even if amplitudes differ.
    if np.std(gt) > 0 and np.std(pr) > 0:
        out["pearson_r"] = float(np.corrcoef(gt, pr)[0, 1])
    else:
        out["pearson_r"] = float("nan")
    out["mse"] = float(np.mean((gt - pr) ** 2))
    out["mae"] = float(np.mean(np.abs(gt - pr)))
    # Peak placement: |argmax(gt) - argmax(pred)| in weeks.
    ig, ip = int(np.argmax(gt)), int(np.argmax(pr))
    out["peak_timing_diff_weeks"] = float(abs(ig - ip))
    out["gt_peak"] = float(gt[ig])
    out["pred_peak"] = float(pr[ip])
    return out


def main() -> None:
    rows = []
    curves = {}                    # L -> (dates, gt, pred) aggregated physical

    print("=" * 78)
    print("Q2 VERIFICATION — test-split date coverage (advisor request: print it)")
    print("=" * 78)

    for L in HORIZONS:
        test = load_test(L)
        raw_dates = pd.to_datetime(test["week_start_date"])
        print(f"\n[L={L}] RAW TEST SPLIT  : "
              f"{raw_dates.min().date()} -> {raw_dates.max().date()}  "
              f"(rows={len(test)})")

        agg = aggregate_lead_time(test, mode="fixed_step", step=0,
                                  gt_col=PHYS_GT, pred_col=PHYS_PR)
        dates = pd.to_datetime(agg["week_start_date"])
        gt = agg["gt"].to_numpy(float)
        pr = agg["pred"].to_numpy(float)
        curves[L] = (dates, gt, pr)
        print(f"[L={L}] step=0 AGGREGATED : "
              f"{dates.min().date()} -> {dates.max().date()}  "
              f"(weeks={len(agg)})")

        pre_m = dates < COVID_BOUNDARY
        cov_m = ~pre_m

        for label, mask in (("precovid_2018_2019", pre_m),
                            ("covid_2020_2021", cov_m)):
            m = segment_metrics(dates[mask], gt[mask.to_numpy()],
                                pr[mask.to_numpy()])
            rows.append({"L": L, "segment": label,
                         "date_start": str(dates[mask].min().date())
                         if mask.any() else "",
                         "date_end": str(dates[mask].max().date())
                         if mask.any() else "", **m})
            print(f"    {label:20s} n={m['n_weeks']:3d}  "
                  f"r={m['pearson_r']:+.3f}  MAE={m['mae']:9.0f}  "
                  f"peakΔ={m['peak_timing_diff_weeks']:.0f}wk  "
                  f"gt_peak={m['gt_peak']:.0f} pred_peak={m['pred_peak']:.0f}")

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n[q2] wrote {OUT_CSV}")

    # ------------------------------------------------------------------ #
    # Figure: row 1 = PRE-COVID normal seasons, row 2 = COVID era.
    # Reading: if row 1 tracks well and row 2 does not, that supports
    # "distribution shift", NOT "index misalignment".
    # ------------------------------------------------------------------ #
    os.makedirs(FIG_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, len(HORIZONS), figsize=(17, 7.2), sharex="col")
    meta = df.set_index(["L", "segment"])

    for j, L in enumerate(HORIZONS):
        dates, gt, pr = curves[L]
        pre_m = (dates < COVID_BOUNDARY).to_numpy()
        for i, (label, mask) in enumerate(
                (("precovid_2018_2019", pre_m), ("covid_2020_2021", ~pre_m))):
            ax = axes[i, j]
            d = dates[mask]
            g = gt[mask]
            p = pr[mask]
            ax.plot(d, g, "-", color="#1f4e79", lw=1.9, label="Ground truth")
            ax.plot(d, p, "--", color="#d62728", lw=1.6, label="MIFlu prediction")
            m = meta.loc[(L, label)]
            ax.set_title(f"L={L} — {label}\n"
                         f"r={m['pearson_r']:+.3f}  MAE={m['mae']:.0f}  "
                         f"peakΔ={m['peak_timing_diff_weeks']:.0f} wk",
                         fontsize=8.5)
            ax.grid(alpha=0.25)
            ax.tick_params(labelsize=7)
            if j == 0:
                ax.set_ylabel("ILITOTAL (patients)", fontsize=9)
            if i == 0 and j == 0:
                ax.legend(fontsize=7, loc="upper left")

    fig.suptitle(
        "Advisor Q2 — alignment cross-check: NORMAL seasons (top) vs COVID era (bottom)\n"
        "Top rows tracking well => index/plot logic is correct; the bottom-row "
        "breakdown is distribution shift, not an off-by-one",
        fontsize=10.5, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(OUT_FIG, dpi=190)
    plt.close(fig)
    print(f"[q2] wrote {OUT_FIG}")


if __name__ == "__main__":
    main()
