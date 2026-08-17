#!/usr/bin/env python
"""
compute_miflu_indicators.py — APPENDIX / SUPPLEMENTARY diagnostic indicators for
MIFlu NATIONAL ILITOTAL.

================================================================================
  ⚠️  SUPPLEMENTARY — NOT PART OF THE MIFLU PAPER-PROTOCOL METRICS
--------------------------------------------------------------------------------
  The MIFlu paper (MIFlu_paper.md, Section V-B) reports National ILI forecasting
  using ONLY **MSE** and **MAE**. The four indicators computed here
  (Peak Hit / Timing / Peak Intensity / Direction) are NOT part of the MIFlu
  paper's evaluation protocol — they are this project's own supplementary
  diagnostics, computed by this script for additional insight only. They MUST
  be presented in an APPENDIX or supplementary section, clearly labeled as
  "supplementary, non-MIFlu-paper-protocol", and MUST NOT be mixed into the
  primary MIFlu results table (which is MSE/MAE only).
================================================================================

Reads the paper-protocol per-horizon prediction CSV written by
`scripts/train_miflu.py`:
    data/predictions_miflu_L{L}_paper_protocol.csv
with columns: split, abs_week, step, ground_truth_ili, prediction_ili.

Only the `test` split is used (asserted). The continuous test series is rebuilt
by collapsing overlapping test windows onto the absolute-week axis (mean where
they overlap).

Four SUPPLEMENTARY indicators (this project's own definitions + thresholds):
  1. Peak Hit       : ratio of true peaks matched within +/-2 weeks.
  2. Timing          : mean absolute delta-t (weeks) over MATCHED peaks ONLY.
  3. Peak Intensity  : mean absolute relative error (%) at MATCHED peaks ONLY.
  4. Direction       : week-over-week directional accuracy.

CRITICAL (Fix Brief #3): Timing and Peak Intensity are computed ONLY over peaks
that pass the Peak Hit criterion. The Peak Hit numerator/denominator are ALWAYS
reported alongside Timing/Intensity (e.g. "peak_hit_count": "1/4"). Unmatched
true peaks are recorded as "Missed" (a miss), NEVER as Timing = 0. If zero peaks
are matched, Timing/Intensity are reported as null ("unmatched"), never 0.0.

Thresholds: Peak Hit >= 0.75, Timing <= 2.0, Peak Intensity <= 20.0, Direction >= 0.60.

Pure CPU (pandas/numpy/scipy/statsmodels). NO model, NO HPC.

Usage:
  python scripts/compute_miflu_indicators.py --pred_csv data/predictions_miflu_L24_paper_protocol.csv
"""
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from statsmodels.tsa.seasonal import STL

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_PRED = os.path.join(PROJECT_ROOT, "data",
                            "predictions_miflu_L24_paper_protocol.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "metrics")


# --------------------------------------------------------------------------- #
# helpers (operate purely on ground_truth/prediction series)
# --------------------------------------------------------------------------- #
def detect_peaks(values: np.ndarray, prominence_frac: float = 0.08,
                 distance: int = 8):
    """Return indices of local maxima via scipy find_peaks on the raw series.

    The SAME prominence/distance are applied to BOTH ground-truth and prediction
    series (no per-series tuning) so the Peak Hit / Timing comparison is fair.
    """
    if len(values) == 0:
        return np.array([], dtype=int)
    prom = prominence_frac * (values.max() - values.min())
    if prom <= 0:
        return np.array([], dtype=int)
    idx, _ = find_peaks(values, prominence=prom, distance=distance)
    return idx


def stl_strengths(values: np.ndarray, period: int = 52):
    """(beta_trend, zeta_seasonal) per Rethinking Tables 9 & 8."""
    s = pd.Series(values.astype(float))
    if len(s) < 2 * period:
        period = max(2, len(s) // 2)
    try:
        stl = STL(s, period=period, robust=True).fit()
        R = stl.resid.to_numpy()
        T = stl.trend.to_numpy()
        S = stl.seasonal.to_numpy()
        varR = np.var(R)
        beta = max(0.0, 1.0 - varR / np.var(T + R)) if np.var(T + R) > 0 else 0.0
        zeta = max(0.0, 1.0 - varR / np.var(S + R)) if np.var(S + R) > 0 else 0.0
    except Exception as e:
        print(f"[warn] STL failed ({e}); using beta=zeta=0.0")
        beta, zeta = 0.0, 0.0
    return beta, zeta


# --------------------------------------------------------------------------- #
# A. PEAK indicators
# --------------------------------------------------------------------------- #
def compute_peak_indicators(gt: np.ndarray, pred: np.ndarray, match_tol: int = 2):
    """Compute peak-hit, timing, and intensity on the (already test-only) series.

    Returns (peak_df, agg). `agg` ALWAYS includes `peak_hit_count` as a
    "hit/true" string so Timing/Intensity are never shown without context.
    Unmatched true peaks are "Missed" (a miss, NOT Timing=0). If no peaks match,
    Timing/Intensity are null.
    """
    true_pk = detect_peaks(gt)
    pred_pk = detect_peaks(pred)

    rows = []
    matched_pred = set()
    for ti in true_pk:
        best, best_d = None, None
        for pj in pred_pk:
            d = abs(pj - ti)
            if d <= match_tol and (best_d is None or d < best_d):
                best, best_d = pj, d
        if best is not None:
            matched_pred.add(int(best))
            status = "Hit"
            delta_t = int(best - ti)
        else:
            status = "Missed"          # unmatched → recorded as a MISS, never Timing=0
            delta_t = None
        rows.append({
            "true_peak_idx": int(ti),
            "pred_peak_idx": (int(best) if best is not None else ""),
            "delta_t_weeks": delta_t if delta_t is not None else "",
            "true_peak_value": float(gt[ti]),
            "pred_peak_value": (float(pred[best]) if best is not None else ""),
            "peak_magnitude_rel_err_pct": (abs(float(pred[best]) - float(gt[ti]))
                                           / float(gt[ti]) * 100.0
                                           if best is not None else ""),
            "status": status,
        })
    for pj in pred_pk:
        if int(pj) not in matched_pred:
            rows.append({
                "true_peak_idx": "",
                "pred_peak_idx": int(pj),
                "delta_t_weeks": "",
                "true_peak_value": "",
                "pred_peak_value": float(pred[pj]),
                "peak_magnitude_rel_err_pct": "",
                "status": "False",
            })
    peak_df = pd.DataFrame(rows)

    n_true = len(true_pk)
    n_hit = int((peak_df["status"] == "Hit").sum())
    hit_rate = (n_hit / n_true) if n_true else 0.0
    hit_rows = peak_df[peak_df["status"] == "Hit"]
    mean_abs_dt = (hit_rows["delta_t_weeks"].abs().mean()
                   if len(hit_rows) else float("nan"))
    mean_mag_rel = (hit_rows["peak_magnitude_rel_err_pct"].mean()
                    if len(hit_rows) else float("nan"))
    false_count = int((peak_df["status"] == "False").sum())

    agg = {
        # Peak Hit numerator/denominator — ALWAYS co-reported with Timing.
        "peak_hit_count": f"{n_hit}/{n_true}",
        "n_true_peaks": int(n_true),
        "n_hit": n_hit,
        "n_missed": int((peak_df["status"] == "Missed").sum()),
        "peak_hit_rate": float(hit_rate),
        # Timing / Intensity only meaningful for matched peaks; null if none.
        "mean_abs_delta_t": (float(mean_abs_dt)
                             if not np.isnan(mean_abs_dt) else None),
        "mean_peak_magnitude_rel_err_pct": (float(mean_mag_rel)
                                            if not np.isnan(mean_mag_rel) else None),
        "false_peak_count": false_count,
    }
    return peak_df, agg


# --------------------------------------------------------------------------- #
# B. TREND indicators
# --------------------------------------------------------------------------- #
def compute_trend_indicators(gt: np.ndarray, pred: np.ndarray):
    dgt = np.diff(gt)
    dpred = np.diff(pred)
    same = np.sign(dgt) == np.sign(dpred)
    nonzero = ~((dgt == 0) & (dpred == 0))
    directional_accuracy = float(same[nonzero].mean()) if nonzero.any() else float("nan")
    beta_gt, zeta_gt = stl_strengths(gt)
    beta_pred, zeta_pred = stl_strengths(pred)
    trend = {
        "directional_accuracy": directional_accuracy,
        "beta_gt": float(beta_gt), "beta_pred": float(beta_pred),
        "beta_abs_diff": float(abs(beta_pred - beta_gt)),
        "zeta_gt": float(zeta_gt), "zeta_pred": float(zeta_pred),
        "zeta_abs_diff": float(abs(zeta_pred - zeta_gt)),
    }
    return trend


# --------------------------------------------------------------------------- #
# C. VERDICT rules
# --------------------------------------------------------------------------- #
def verdicts(peak_agg, trend, thr):
    v = {}
    hr = peak_agg["peak_hit_rate"]
    v["peak_hit_rate"] = {
        "value": hr, "threshold": thr["peak_hit_rate"],
        "verdict": "accurate" if hr >= thr["peak_hit_rate"] else "not accurate"}
    madt = peak_agg["mean_abs_delta_t"]
    v["mean_abs_delta_t"] = {
        "value": madt, "threshold": thr["mean_abs_delta_t"],
        "verdict": ("accurate" if (madt is not None
                                   and madt <= thr["mean_abs_delta_t"])
                    else "not accurate")}
    mmr = peak_agg["mean_peak_magnitude_rel_err_pct"]
    v["mean_peak_magnitude_rel_err"] = {
        "value": mmr, "threshold": thr["mean_peak_mag_rel_err"],
        "verdict": ("accurate" if (mmr is not None
                                   and mmr <= thr["mean_peak_mag_rel_err"])
                    else "not accurate")}
    da = trend["directional_accuracy"]
    v["directional_accuracy"] = {
        "value": da, "threshold": thr["directional_accuracy"],
        "verdict": ("accurate" if (da is not None
                                   and da >= thr["directional_accuracy"])
                    else "not accurate")}
    return v


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred_csv", default=DEFAULT_PRED,
                    help="Paper-protocol prediction CSV with a `split` column.")
    ap.add_argument("--out_dir", default=OUT_DIR)
    ap.add_argument("--match_tol", type=int, default=2)
    ap.add_argument("--thr_peak_hit_rate", type=float, default=0.75)
    ap.add_argument("--thr_mean_abs_delta_t", type=float, default=2.0)
    ap.add_argument("--thr_peak_mag_rel_err", type=float, default=20.0)
    ap.add_argument("--thr_directional_accuracy", type=float, default=0.60)
    ap.add_argument("--prefix", default="miflu_",
                    help="Output prefix, e.g. miflu_L24_")
    args = ap.parse_args()

    if not os.path.exists(args.pred_csv):
        print(f"[BLOCKER] prediction CSV not found: {args.pred_csv}")
        sys.exit(3)

    df = pd.read_csv(args.pred_csv)
    assert "split" in df.columns, "prediction CSV must carry a `split` column"
    test_df = df[df["split"] == "test"].copy()
    assert len(test_df) > 0, "no `test` rows in prediction CSV — leakage guard failed"
    # Collapse overlapping test windows onto the absolute-week axis (mean).
    grp = test_df.groupby("abs_week").agg(
        ground_truth_ili=("ground_truth_ili", "mean"),
        prediction_ili=("prediction_ili", "mean")).sort_index()
    gt = grp["ground_truth_ili"].to_numpy(dtype=float)
    pred = grp["prediction_ili"].to_numpy(dtype=float)

    thr = {
        "peak_hit_rate": args.thr_peak_hit_rate,
        "mean_abs_delta_t": args.thr_mean_abs_delta_t,
        "mean_peak_mag_rel_err": args.thr_peak_mag_rel_err,
        "directional_accuracy": args.thr_directional_accuracy,
    }

    peak_df, peak_agg = compute_peak_indicators(gt, pred, args.match_tol)
    trend = compute_trend_indicators(gt, pred)
    v = verdicts(peak_agg, trend, thr)

    os.makedirs(args.out_dir, exist_ok=True)
    peak_csv = os.path.join(args.out_dir, f"{args.prefix}ili_peak_indicators.csv")
    summary_json = os.path.join(args.out_dir, f"{args.prefix}ili_peak_trend_summary.json")
    peak_df.to_csv(peak_csv, index=False)

    summary = {
        "source": args.pred_csv,
        "peak_aggregate": peak_agg,
        "trend_indicators": trend,
        "verdicts": v,
        "thresholds": thr,
    }
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== PEAK INDICATORS (per peak) ===")
    print(peak_df.to_string(index=False))
    print("\n=== PEAK AGGREGATE ===")
    for k, val in peak_agg.items():
        print(f"  {k:38s} = {val}")
    print("\n=== TREND INDICATORS ===")
    for k, val in trend.items():
        print(f"  {k:18s} = {val}")
    print("\n=== VERDICTS (SUPPLEMENTARY — non-MIFlu-paper-protocol; this project's own diagnostics) ===")
    for name, d in v.items():
        print(f"  {name:32s} value={d['value']}  thr={d['threshold']}  "
              f"-> {d['verdict'].upper()}")
    # Force-co-display Peak Hit count with Timing/Intensity.
    print(f"\n[CONTEXT] Peak Hit = {peak_agg['peak_hit_count']} "
          f"(Timing/Intensity above are computed over the {peak_agg['n_hit']} "
          f"matched peak(s) only; {peak_agg['n_missed']} true peak(s) MISSED).")
    print(f"[out] peak indicators CSV -> {peak_csv}")
    print(f"[out] summary JSON        -> {summary_json}")


if __name__ == "__main__":
    main()
