#!/usr/bin/env python
"""
compute_miflu_indicators.py — APPENDIX / SUPPLEMENTARY diagnostic indicators for
MIFlu NATIONAL ILITOTAL.

================================================================================
  ⚠️  SUPPLEMENTARY — NOT PART OF THE MIFLU PAPER-PROTOCOL METRICS
--------------------------------------------------------------------------------
  The MIFlu paper (MIFlu_paper.md, Section V-B) reports National ILI forecasting
  using ONLY **MSE** and **MAE**. The TWO indicators computed here
  (Peak Timing Error / Peak Intensity Error) are NOT part of the MIFlu
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

TWO SUPPLEMENTARY indicators (PTE and PIE). The metric DEFINITIONS come from the
published literature; the numeric THRESHOLDS are this project's own choices and
are NOT literature values. See the PROVENANCE block below — do not blur the two.
  1. Peak Timing Error (PTE) : mean |Δt| IN WEEKS between a true peak and its
                         matched predicted peak, over MATCHED peaks ONLY.
                         *** THIS IS AN ERROR, NOT A LEAD TIME ***
                         (Advisor Q1c: a reported value of "0.5" was misread as
                         "0.5 weeks lead time". It means the matched peaks were
                         on average half a week off. Forecast lead time is
                         instead given by the `step` column: step h = (h+1)-week
                         ahead. Renamed from `mean_abs_delta_t` accordingly.)
  2. Peak Intensity Error (PIE) : mean absolute relative error (%) at MATCHED
                         peaks ONLY.

REMOVED (2026-09) — no longer computed or reported anywhere:
  * "Peak Hit Rate" (`peak_hit_rate`) — a project-specific ratio with a custom
    0.75 threshold. Removed by decision to report PTE/PIE only.
  * "Direction" (`directional_accuracy`) — week-over-week directional accuracy.
  The matched-peak COUNT (`peak_hit_count`, e.g. "3/5") is still produced, but
  ONLY as the sample-size qualifier for PTE/PIE — it is not an indicator.

CRITICAL: PTE and PIE are computed ONLY over MATCHED peaks. They MUST therefore
always be reported together with the matched-peak count (e.g. "3/5"), never as
a bare number — otherwise a reader cannot tell whether the mean was taken over
5 peaks or 1. Unmatched true peaks are recorded as "Missed" (a miss), NEVER as
Timing = 0. If zero peaks are matched, PTE/PIE are reported as null
("unmatched"), never 0.0.

# --------------------------------------------------------------------------- #
# PROVENANCE OF INDICATORS AND THRESHOLDS  (Advisor Q5 — DO NOT BLUR THESE)
# --------------------------------------------------------------------------- #
# (a) FROM THE LITERATURE — the metric DEFINITIONS:
#       Peak Timing Error (PTE) = |predicted peak week - true peak week| (weeks)
#       Peak Intensity Error (PIE) = |pred peak intensity - true peak intensity|
#                                    / true peak intensity   (percent)
#     Both definitions, and the acceptance convention "a peak counts as hit when
#     PTE <= 1 week AND PIE <= 25%", are taken from:
#         Kramer SC, Shaman J. "Development and validation of influenza
#         forecasting for 64 temperate and tropical countries."
#         PLOS Computational Biology, 2019. DOI: 10.1371/journal.pcbi.1006742
#         https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006742
#     (the same convention used by the CDC "Predict the Influenza Season
#     Challenge").
#
# (b) THIS PROJECT'S OWN — the numeric thresholds actually applied below.
#       NON-LITERATURE, CUSTOM ENGINEERING CHOICES (do NOT attribute to a paper):
#         Timing        PTE <= 2.0 wk  (RELAXED vs the literature's 1 week)
#         Peak Intensity PIE <= 20.0 % (TIGHTENED vs the literature's 25 %)
#     The +/-2 week peak matching window (`match_tol`) is likewise a project
#     choice, which is why our PTE is judged against 2.0 weeks rather than
#     the literature's 1 week. If you want to report against the literature
#     convention instead, pass --thr_mean_abs_delta_t 1.0 and
#     --thr_peak_mag_rel_err 25 and label the change explicitly.
#
# (c) REMOVED (2026-09) — no longer computed, judged, or reported:
#     * "Peak Hit Rate" (peak_hit_rate) with its custom 0.75 threshold.
#     * "Direction" (directional_accuracy) with its custom 0.60 threshold.
#     * The "dual gate" early-stopping mechanism (persist a checkpoint only when
#       val_loss improves AND peak_hit_rate clears a threshold) — it depended on
#       peak_hit_rate and was removed with it. Early stopping is now plain
#       val_loss + patience (see early_stopping.py). That mechanism had been a
#       project-specific design with no published precedent.
# --------------------------------------------------------------------------- #
Thresholds: PTE <= 2.0 weeks, PIE <= 20.0 %.

Pure CPU (pandas/numpy/scipy/statsmodels). NO model, NO HPC.

Usage:
  python scripts/compute_miflu_indicators.py --pred_csv data/predictions_miflu_L24_paper_protocol.csv
"""
from __future__ import annotations   # Python 3.9: enables `int | None` annotations

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
    series (no per-series tuning) so the PTE / PIE comparison is fair.
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
    """Compute PTE (timing error) and PIE (intensity error) on the test series.

    Returns (peak_df, agg). PTE and PIE are computed over MATCHED peaks only, so
    `agg` ALWAYS includes `peak_hit_count` as a "hit/true" string (e.g. "3/5")
    carrying the sample size — they must never be shown without it.
    Unmatched true peaks are "Missed" (a miss, NOT Timing=0). If no peaks match,
    PTE/PIE are null.
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
    # EDGE CASE: when neither series has a detectable peak, `rows` is empty and
    # `pd.DataFrame([])` has NO columns, so `peak_df["status"]` raises KeyError.
    # This happens routinely on short validation windows, and it is exactly the
    # case the early stopper must survive. Declare the schema explicitly.
    PEAK_DF_COLUMNS = ["true_peak_idx", "pred_peak_idx", "delta_t_weeks",
                       "true_peak_value", "pred_peak_value",
                       "peak_magnitude_rel_err_pct", "status"]
    peak_df = pd.DataFrame(rows, columns=PEAK_DF_COLUMNS)

    n_true = len(true_pk)
    n_hit = int((peak_df["status"] == "Hit").sum())
    hit_rows = peak_df[peak_df["status"] == "Hit"]
    mean_abs_dt = (hit_rows["delta_t_weeks"].abs().mean()
                   if len(hit_rows) else float("nan"))
    mean_mag_rel = (hit_rows["peak_magnitude_rel_err_pct"].mean()
                    if len(hit_rows) else float("nan"))
    false_count = int((peak_df["status"] == "False").sum())

    agg = {
        # Matched-peak count — the SAMPLE SIZE for PTE/PIE. ALWAYS co-reported
        # with them; it is a qualifier, NOT a reported indicator.
        "peak_hit_count": f"{n_hit}/{n_true}",
        "n_true_peaks": int(n_true),
        "n_hit": n_hit,
        "n_missed": int((peak_df["status"] == "Missed").sum()),
        # ── NAMING (Advisor Q1c) ──────────────────────────────────────────
        # `mean_abs_delta_t` was the original key. The advisor read a reported
        # value of 0.5 as "lead time = 0.5 weeks". It is NOT a lead time: it is
        # the mean |Δt| between a TRUE peak and its matched PREDICTED peak, in
        # WEEKS — i.e. a peak-TIMING ERROR. Renamed to make that unambiguous.
        # `mean_abs_delta_t` is retained as a deprecated alias so existing
        # JSON/CSV consumers keep working.
        "peak_timing_error_weeks": (float(mean_abs_dt)
                                    if not np.isnan(mean_abs_dt) else None),
        "mean_abs_delta_t": (float(mean_abs_dt)
                             if not np.isnan(mean_abs_dt) else None),
        "mean_peak_magnitude_rel_err_pct": (float(mean_mag_rel)
                                            if not np.isnan(mean_mag_rel) else None),
        "false_peak_count": false_count,
    }
    return peak_df, agg


# --------------------------------------------------------------------------- #
# A'. LEAD-TIME AGGREGATION  (Advisor Question 1) -- shared by figures & here
# --------------------------------------------------------------------------- #
def aggregate_lead_time(df: pd.DataFrame, mode: str = "fixed_step",
                        step: int = 0, stride: int | None = None,
                        gt_col: str = "ground_truth_ili_phys",
                        pred_col: str = "prediction_ili_phys") -> pd.DataFrame:
    """Collapse overlapping forecast windows onto one row per calendar week.

    WHY THIS EXISTS
    ---------------
    `train_miflu.build_windows` uses **stride = 1**, so windows overlap almost
    completely: week W is predicted by up to L different windows, at forecast
    steps 0..L-1. A naive `groupby("abs_week").mean()` therefore averages a
    1-week-ahead prediction together with a 24-week-ahead one, AND the number
    of contributing windows varies along the curve (1 at the start of the test
    split, L in the interior, 1 again at the end). That makes the *effective
    lead time* non-stationary — the exact thing that makes a plotted curve
    impossible to interpret.

    MODES
    -----
    mean_over_lead : average every available forecast step (legacy behaviour).
                     Retained for backward comparison ONLY. The returned
                     `n_windows` column documents the varying lead-time mix.
    fixed_step     : keep ONLY forecast step == `step`. Every point then has a
                     CONSTANT lead time of (step + 1) weeks, so the curve is
                     scientifically interpretable. RECOMMENDED for the journal.
    origin_stride  : keep only windows whose target start is a multiple of
                     `stride`. With stride == L the windows are NON-OVERLAPPING
                     and NO aggregation is needed at all (each week is covered
                     exactly once).

    Returns columns: abs_week, epiweek, week_start_date, gt, pred, n_windows.
    """
    if gt_col not in df.columns or pred_col not in df.columns:
        raise KeyError(
            f"aggregate_lead_time needs '{gt_col}' / '{pred_col}'. "
            "The CSV predates the dual-track export — re-run train_miflu.py.")

    d = df.copy()

    # The CSV round-trips `week_start_date` as a STRING; coerce it back to a
    # real datetime so downstream plotting/conversion works.
    if "week_start_date" in d.columns:
        d["week_start_date"] = pd.to_datetime(d["week_start_date"])

    if mode == "fixed_step":
        d = d[d["step"] == int(step)]
        if d.empty:
            raise ValueError(f"no rows with step == {step}")
    elif mode == "origin_stride":
        if not stride:
            raise ValueError("origin_stride requires `stride`")
        # target start of the window that produced this row:
        d = d[(d["abs_week"] - d["step"]) % int(stride) == 0]
        if d.empty:
            raise ValueError(f"no rows align to stride={stride}")
    elif mode != "mean_over_lead":
        raise ValueError(f"unknown lead mode: {mode!r}")

    grp = d.groupby("abs_week").agg(
        gt=(gt_col, "mean"),
        pred=(pred_col, "mean"),
        n_windows=(pred_col, "size"),
    ).sort_index()

    # Carry the calendar through if it is present.
    for col in ("epiweek", "week_start_date"):
        if col in d.columns:
            grp[col] = d.groupby("abs_week")[col].first()

    grp = grp.reset_index()
    ordered = ["abs_week"] + [c for c in ("epiweek", "week_start_date")
                              if c in grp.columns] + ["gt", "pred", "n_windows"]
    grp.attrs["lead_mode"] = mode
    grp.attrs["lead_step"] = int(step) if mode == "fixed_step" else None
    grp.attrs["stride"] = int(stride) if stride else None
    return grp[ordered]


# --------------------------------------------------------------------------- #
# B. TREND indicators
# --------------------------------------------------------------------------- #
def compute_trend_indicators(gt: np.ndarray, pred: np.ndarray):
    """STL trend/seasonal strengths only.

    NOTE: `directional_accuracy` (week-over-week direction) was REMOVED (2026-09)
    together with the Peak Hit Rate indicator — only PTE and PIE are reported.
    The STL strengths below are trend/seasonal diagnostics, a different concept
    from direction accuracy, and are intentionally kept.
    """
    beta_gt, zeta_gt = stl_strengths(gt)
    beta_pred, zeta_pred = stl_strengths(pred)
    trend = {
        "beta_gt": float(beta_gt), "beta_pred": float(beta_pred),
        "beta_abs_diff": float(abs(beta_pred - beta_gt)),
        "zeta_gt": float(zeta_gt), "zeta_pred": float(zeta_pred),
        "zeta_abs_diff": float(abs(zeta_pred - zeta_gt)),
    }
    return trend


# --------------------------------------------------------------------------- #
# C. VERDICT rules
# --------------------------------------------------------------------------- #
def verdicts(peak_agg, thr):
    """Verdicts for the two RETAINED indicators: PTE and PIE.

    The `trend` argument was dropped from this signature because
    `directional_accuracy` — the only trend key that ever fed a verdict — was
    removed together with the Peak Hit Rate indicator (2026-09).
    """
    v = {}
    # Renamed key with backward-compatible fallback (see Advisor Q1c).
    madt = peak_agg.get("peak_timing_error_weeks",
                        peak_agg.get("mean_abs_delta_t"))
    v["peak_timing_error_weeks"] = {
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
    ap.add_argument("--thr_mean_abs_delta_t", type=float, default=2.0,
                    help="Threshold for Peak Timing Error (weeks). Kept under "
                         "its historical name for CLI compatibility.")
    ap.add_argument("--lead_mode", default="fixed_step",
                    choices=["mean_over_lead", "fixed_step", "origin_stride"],
                    help="How overlapping windows are collapsed (Advisor Q1).")
    ap.add_argument("--lead_step", type=int, default=0,
                    help="Forecast step kept when --lead_mode=fixed_step. "
                         "step h == (h+1)-week-ahead; 0 = 1-week-ahead.")
    ap.add_argument("--stride", type=int, default=None,
                    help="Window stride for --lead_mode=origin_stride. "
                         "stride == L means non-overlapping (no aggregation).")
    ap.add_argument("--thr_peak_mag_rel_err", type=float, default=20.0)
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
    # ADVISOR Q1/Q3: collapse overlapping windows with an EXPLICIT, declared
    # lead-time policy, and evaluate in PHYSICAL units (patient counts) so the
    # peak magnitude threshold (20 %) is meaningful.
    grp = aggregate_lead_time(test_df, mode=args.lead_mode,
                              step=args.lead_step, stride=args.stride)
    gt = grp["gt"].to_numpy(dtype=float)
    pred = grp["pred"].to_numpy(dtype=float)
    lead_note = {
        "fixed_step": f"constant lead time = {args.lead_step + 1} week(s) ahead",
        "mean_over_lead": ("MIXED lead times 1..L averaged per week "
                           "(effective lead time varies along the curve)"),
        "origin_stride": f"window stride = {args.stride}",
    }[args.lead_mode]
    print(f"[lead-time policy] mode={args.lead_mode} — {lead_note}")
    print(f"                   weeks={len(gt)}, contributing windows per week: "
          f"min={int(grp['n_windows'].min())}, max={int(grp['n_windows'].max())}")

    thr = {
        "mean_abs_delta_t": args.thr_mean_abs_delta_t,
        "mean_peak_mag_rel_err": args.thr_peak_mag_rel_err,
    }

    peak_df, peak_agg = compute_peak_indicators(gt, pred, args.match_tol)
    trend = compute_trend_indicators(gt, pred)
    v = verdicts(peak_agg, thr)

    os.makedirs(args.out_dir, exist_ok=True)
    peak_csv = os.path.join(args.out_dir, f"{args.prefix}ili_peak_indicators.csv")
    summary_json = os.path.join(args.out_dir, f"{args.prefix}ili_peak_trend_summary.json")
    peak_df.to_csv(peak_csv, index=False)

    summary = {
        "source": args.pred_csv,
        "lead_time_policy": {
            "mode": args.lead_mode,
            "step": args.lead_step if args.lead_mode == "fixed_step" else None,
            "stride": args.stride,
            "lead_note": lead_note,
            "n_weeks": int(len(gt)),
            "windows_per_week_min": int(grp["n_windows"].min()),
            "windows_per_week_max": int(grp["n_windows"].max()),
        },
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
    # Force-co-display the matched-peak count: PTE/PIE are computed over matched
    # peaks ONLY, so they are uninterpretable without the sample size.
    print(f"\n[CONTEXT] {peak_agg['peak_hit_count']} true peak(s) matched — "
          f"PTE/PIE above are computed over the {peak_agg['n_hit']} "
          f"matched peak(s) only; {peak_agg['n_missed']} true peak(s) MISSED.")
    print(f"[out] peak indicators CSV -> {peak_csv}")
    print(f"[out] summary JSON        -> {summary_json}")


if __name__ == "__main__":
    main()
