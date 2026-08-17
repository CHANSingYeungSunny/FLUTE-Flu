#!/usr/bin/env python
"""
make_miflu_evaluation_figure.py — Publication-layout EVALUATION figures + verdict
for MIFlu NATIONAL ILITOTAL (paper protocol, N=7).

This script is part of the MIFlu paper-protocol evaluation line
(`train_miflu.py` + `compute_miflu_indicators.py`). It:
  * Reads the paper-protocol per-horizon prediction CSV (has a `split` column)
    and plots the TEST split only.
  * Emits exactly the artifacts requested:
      results/ili/figures/fig_miflu_eval_continuous_L{L}.png
      results/ili/figures/fig_miflu_eval_diagnostics_L{L}.png
  * The 4 supplementary diagnostic indicators (Peak Hit / Timing / Peak
    Intensity / Direction) are computed by `compute_miflu_indicators.py`
    (this project's own script). They are supplementary only — the MIFlu
    National paper protocol reports MSE/MAE. Full caveat in FIGURE_CAPTION.
  * Thresholds: Peak Hit >= 0.75, Timing <= 2.0, Peak Intensity <= 20.0,
    Direction >= 0.60.

Pure CPU (matplotlib/pandas/numpy). 300 DPI.

Usage:
  python scripts/make_miflu_evaluation_figure.py --pred_csv data/predictions_miflu_L24_paper_protocol.csv --L 24
"""
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)  # allow `from compute_miflu_indicators import ...`
# Default input is the PAPER-PROTOCOL per-horizon prediction CSV (has `split`).
DEFAULT_PRED = os.path.join(PROJECT_ROOT, "data",
                            "predictions_miflu_L24_paper_protocol.csv")
# Retained only for the (deprecated) ChatTime walk-forward comparison.
DEFAULT_WF = os.path.join(PROJECT_ROOT, "results", "ili",
                          "miflu_fulltest_walkforward.csv")
DEFAULT_IND = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                           "miflu_ili_peak_indicators.csv")
DEFAULT_SUM = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                           "miflu_ili_peak_trend_summary.json")
FIG_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "figures")
MET_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "metrics")

PHASE_COLORS = {"Baseline": "#e8e8e8", "Ramp-up": "#fde0dd",
                "Peak": "#f9c0bb", "Decay": "#d9d2e9"}

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 100,
})


# --------------------------------------------------------------------------- #
def parse_dates(series: pd.Series) -> pd.Series:
    """Parse MIFlu epiweek codes (YYYYWW) into Timestamps (ISO-week start)."""
    from datetime import datetime

    def _one(s):
        s = str(s)
        if len(s) == 6 and s.isdigit():
            y, w = int(s[:4]), int(s[4:])
            try:
                return pd.Timestamp(datetime.fromisocalendar(y, w, 1))
            except Exception:
                return pd.NaT
        return pd.NaT
    ts = series.map(_one)
    if ts.notna().all():
        return ts
    return pd.to_datetime(series.astype(str), format="%Y-%m-%d", errors="coerce")


def season_label(date: pd.Timestamp) -> str:
    y, m = date.year, date.month
    return f"{y-1}-{y}" if m < 7 else f"{y}-{y+1}"


def _week_to_epiweek(abs_week: int) -> str:
    """Map an absolute week index (0-based, 2002w01 = index 0) to an epiweek
    code YYYYWW for date parsing. The national data starts at 200201."""
    base_year, base_week = 2002, 1
    # ISO week arithmetic via pandas Timestamp.
    from datetime import datetime
    d = datetime.fromisocalendar(base_year, base_week, 1)
    ts = pd.Timestamp(d) + pd.Timedelta(weeks=int(abs_week))
    # Convert back to epiweek code YYYYWW (ISO week number, zero-padded).
    iso = ts.isocalendar()
    return f"{iso[0]}{iso[1]:02d}"


def smooth(series: np.ndarray, window: int = 4) -> np.ndarray:
    if len(series) < window:
        return series
    return np.convolve(series, np.ones(window) / window, mode="same")


def phase_label(values: np.ndarray) -> np.ndarray:
    sm = smooth(values, 4)
    slope = np.gradient(sm)
    p75 = np.percentile(values, 75)
    p40 = np.percentile(values, 40)
    labels = np.array(["Baseline"] * len(values), dtype=object)
    labels[values >= p40] = "Ramp-up"
    labels[values >= p75] = "Peak"
    dec = (values >= p40) & (slope < 0)
    labels[dec] = "Decay"
    return labels


def shade_phases(ax, dates, labels):
    for ph, col in PHASE_COLORS.items():
        m = labels == ph
        if not m.any():
            continue
        idx = np.where(m)[0]
        start = prev = idx[0]
        for i in idx[1:]:
            if i == prev + 1:
                prev = i
                continue
            ax.axvspan(dates.iloc[start], dates.iloc[prev], color=col,
                       alpha=0.45, zorder=0)
            start = prev = i
        ax.axvspan(dates.iloc[start], dates.iloc[prev], color=col,
                   alpha=0.45, zorder=0)


def add_annotation_box(ax, summary, L, split_label="test"):
    """Annotation box with the 4 SUPPLEMENTARY indicators.

    The 4 indicators are supplementary diagnostics for our own MIFlu pipeline
    (computed by compute_miflu_indicators.py). The full caveat — "not part of
    the MIFlu paper-reported metrics (National paper protocol reports MSE/MAE
    only)" — lives in FIGURE_CAPTION_L24.md. On the figure itself we keep only a
    short "Supplementary" tag. Timing / Peak Intensity MUST be shown together
    with the Peak-Hit hit count, never as a bare number (Fix Brief #3).
    """
    v = summary.get("verdicts", {})
    peak = summary.get("peak_aggregate", {})
    hit_count = peak.get("peak_hit_count", "NA")
    n_missed = peak.get("n_missed", "NA")

    def _fmt(x, nd=2, na="NA"):
        return na if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"

    # Timing / Peak Intensity shown WITH hit count (Fix Brief #3).
    madt = peak.get("mean_abs_delta_t", None)
    mmr = peak.get("mean_peak_magnitude_rel_err_pct", None)
    timing_s = (f"{_fmt(madt,1)} wk (based on {hit_count} matched peaks)"
                if madt is not None else f"unmatched (hit {hit_count})")
    intensity_s = (f"{_fmt(mmr,1)}% (based on {hit_count} matched peaks)"
                   if mmr is not None else f"unmatched (hit {hit_count})")

    box = (
        "Supplementary indicators:\n"
        f"  Peak Hit   = {_fmt(peak.get('peak_hit_rate'),2)} ({hit_count}; {n_missed} missed)\n"
        f"  Timing     = {timing_s}\n"
        f"  Peak Int.  = {intensity_s}\n"
        f"  Direction  = {_fmt(v.get('directional_accuracy', {}).get('value'),2)}"
    )
    ax.text(0.985, 0.95, box, transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.5", fc="#fff8e1", ec="#caa"))


def build_continuous_panel(ax, dates, gt, pred, labels, summary, L,
                            split_boundaries=None):
    """Plot the TEST-ONLY series.

    `split_boundaries` (optional) is a list of (abs_week_index, label) pairs
    marking the train→val and val→test cut points, drawn as vertical dashed
    lines so the viewer can SEE the split is test-only (Task A.1).
    """
    shade_phases(ax, dates, labels)
    ax.plot(dates, gt, color="#1f77b4", lw=2.0, ls="--",
            label="Ground Truth (ILITOTAL)", zorder=3)
    ax.plot(dates, pred, color="#d62728", lw=1.8,
            label="MIFlu Prediction (ILITOTAL)", zorder=2)
    tpk = find_peaks(gt, prominence=0.08 * (gt.max() - gt.min()),
                     distance=8)[0]
    ppk = find_peaks(pred, prominence=0.08 * (pred.max() - pred.min()),
                     distance=8)[0]
    ax.scatter(dates.iloc[tpk], gt[tpk], marker="v", color="#1f77b4",
               s=70, zorder=5, label="True Peak")
    ax.scatter(dates.iloc[ppk], pred[ppk], marker="^", color="#d62728",
               s=70, zorder=5, label="Pred Peak")
    # (Task A.1) Explicit split boundaries — prove the plotted curve is test-only.
    if split_boundaries:
        for bw, blab in split_boundaries:
            bdate = parse_dates(pd.Series([_week_to_epiweek(bw)]))
            ax.axvline(bdate.iloc[0], color="#888", ls=":", lw=1.2, zorder=1)
            # Place the split-boundary label at the BOTTOM of the axis (lower right
            # area) so it never collides with the upper-left legend.
            ax.text(bdate.iloc[0], ax.get_ylim()[0], f"{blab} ",
                    fontsize=7, color="#555", va="bottom", ha="left",
                    rotation=90)
    ax.set_ylabel("ILITOTAL (patient count)")
    ax.set_title(f"MIFlu Forecast vs Ground Truth — Test Set Only, L={L}",
                 fontsize=10.5, weight="bold")
    # COVID-19 distribution-shift annotation (test period 2020-2021) — lower LEFT.
    ax.annotate("COVID-19 NPIs → atypical flat 2020-21 season\n"
                "(distribution shift: not seen in 2002-2019 training)",
                xy=(0.015, 0.04), xycoords="axes fraction",
                fontsize=7.5, color="#555",
                bbox=dict(boxstyle="round,pad=0.4", fc="#f3f3f3", ec="#bbb"))
    # Legend upper-LEFT, nudged down slightly so it never overlaps the title or
    # the (now bottom-placed) split label.
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0.0, 0.98))
    ax.grid(alpha=0.25)
    add_annotation_box(ax, summary, L)


def build_directional_panel(ax, dates, gt, pred):
    dgt = np.diff(gt)
    dpred = np.diff(pred)
    same = (np.sign(dgt) == np.sign(dpred)).astype(float)
    win = 13
    if len(same) >= win:
        roll = np.convolve(same, np.ones(win) / win, mode="valid")
        rdates = dates.iloc[win // 2: win // 2 + len(roll)]
        ax.plot(rdates, roll, color="#2ca02c", lw=1.8)
        ax.axhline(0.5, color="gray", ls="--", lw=1.0, label="chance (0.5)")
        overall = float(np.nanmean(same[(~((dgt == 0) & (dpred == 0)))]))
        ax.axhline(overall, color="#d62728", ls=":", lw=1.2,
                   label=f"overall={overall:.2f}")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("P(sign slope matches)")
    ax.set_title("Rolling Directional Accuracy (13-wk)",
                 fontsize=10, weight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)


def build_peakbars_panel(ax, peak_df):
    hit = peak_df[peak_df["status"].isin(["Hit", "Missed"])].copy()
    # The indicator module returns `true_peak_idx`/`pred_peak_idx`, not a `season`
    # label. Fall back gracefully if `season` is absent.
    if "season" in hit.columns:
        seasons = hit["season"].tolist()
    else:
        seasons = [f"pk{i+1}" for i in range(len(hit))]
    dt = [abs(x) if isinstance(x, (int, float)) and not pd.isna(x)
          else 0 for x in hit["delta_t_weeks"]]
    mag = [x if isinstance(x, (int, float)) and not pd.isna(x)
           else 0 for x in hit["peak_magnitude_rel_err_pct"]]
    x = np.arange(len(seasons))
    w = 0.38
    ax.bar(x - w / 2, dt, w, color="#1f77b4", label="|\u0394t| weeks (timing)")
    ax.bar(x + w / 2, mag, w, color="#ff7f0e", label="mag rel-err %")
    ax.set_xticks(x)
    ax.set_xticklabels(seasons, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("weeks / percent")
    ax.set_title("Per-Season Peak Timing & Magnitude Error",
                 fontsize=10, weight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="y")


def write_verdict_table(summary, md_path):
    order = ["peak_hit_rate", "mean_abs_delta_t",
             "mean_peak_magnitude_rel_err", "directional_accuracy"]
    pretty = {
        "peak_hit_rate": "Peak Hit",
        "mean_abs_delta_t": "Timing",
        "mean_peak_magnitude_rel_err": "Peak Intensity",
        "directional_accuracy": "Direction",
    }
    rows = []
    for name in order:
        d = summary["verdicts"][name]
        val = d["value"]
        val_s = (f"{val:.3f}" if isinstance(val, float) else str(val))
        thr_s = (f"{d['threshold']:.2f}" if isinstance(d["threshold"], float)
                 else str(d["threshold"]))
        verdict = "accurate" if d["verdict"] == "accurate" else "NOT accurate"
        rows.append((pretty[name], val_s, thr_s, verdict))

    with open(md_path, "w") as f:
        f.write("| Indicator | Value | Threshold | Verdict |\n")
        f.write("|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n")
    return rows


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred_csv", default=DEFAULT_PRED,
                    help="Paper-protocol per-horizon prediction CSV with a `split` "
                         "column (e.g. data/predictions_miflu_L24_paper_protocol.csv). "
                         "MUST contain a `split` column; only `test` rows are plotted.")
    ap.add_argument("--L", type=int, default=None,
                    help="Horizon L (for title/annotation). If None, inferred from filename.")
    ap.add_argument("--walkforward_csv", default=None,
                    help="[DEPRECATED] ChatTime L=52 walk-forward CSV. Use --pred_csv instead.")
    ap.add_argument("--indicators_csv", default=DEFAULT_IND)
    ap.add_argument("--summary_json", default=DEFAULT_SUM)
    ap.add_argument("--fig_dir", default=FIG_DIR)
    ap.add_argument("--met_dir", default=MET_DIR)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    os.makedirs(args.fig_dir, exist_ok=True)
    os.makedirs(args.met_dir, exist_ok=True)

    L = args.L
    if L is None:
        import re
        m = re.search(r"L(\d+)", os.path.basename(args.pred_csv))
        if m:
            L = int(m.group(1))

    # ── PAPER-PROTOCOL PATH (default) ──
    if args.walkforward_csv is None:
        if not os.path.exists(args.pred_csv):
            print(f"[BLOCKER] prediction CSV not found: {args.pred_csv}")
            print("Generate it via: python scripts/train_miflu.py  (writes "
                  "data/predictions_miflu_L{L}_paper_protocol.csv)")
            sys.exit(3)
        df = pd.read_csv(args.pred_csv)
        # CRITICAL: the plotted curve MUST come from the test split only.
        assert "split" in df.columns, "prediction CSV must carry a `split` column"
        test_df = df[df["split"] == "test"].copy()
        assert len(test_df) > 0, "no `test` rows in prediction CSV — leakage guard failed"
        # Collapse overlapping test windows onto a common absolute-week axis;
        # where windows overlap, take the MEAN (deterministic, leakage-free).
        grp = test_df.groupby("abs_week").agg(
            ground_truth_ili=("ground_truth_ili", "mean"),
            prediction_ili=("prediction_ili", "mean")).sort_index()
        dates = parse_dates(pd.Series([_week_to_epiweek(w) for w in grp.index]))
        gt = grp["ground_truth_ili"].to_numpy(dtype=float)
        pred = grp["prediction_ili"].to_numpy(dtype=float)
        # Build the REAL supplementary summary from the test-only series via the
        # indicator module (Fix Brief #3 math: Timing/Intensity over matched peaks
        # only; Peak-Hit count always co-reported).
        from compute_miflu_indicators import (
            compute_peak_indicators, compute_trend_indicators, verdicts)
        peak_df, peak_agg = compute_peak_indicators(gt, pred)
        trend = compute_trend_indicators(gt, pred)
        thr = {"peak_hit_rate": 0.75, "mean_abs_delta_t": 2.0,
               "mean_peak_mag_rel_err": 20.0, "directional_accuracy": 0.60}
        v = verdicts(peak_agg, trend, thr)
        summary = {"peak_aggregate": peak_agg, "verdicts": v,
                   "trend_indicators": trend, "thresholds": thr}
        labels = phase_label(gt)
        suffix = f"_L{L}" if L else ""
        # (Task A.1) Split boundaries from the leakage audit: train[0,717),
        # val[717,819), test[819,1025). The plotted curve is test-only (abs_week
        # >= 820). Draw the val/test boundary so the viewer can SEE it.
        split_boundaries = [(819, "val|test (test starts wk820)")]
        # ---- 1. Continuous forecast figure (TEST ONLY) ----
        fig1, ax = plt.subplots(figsize=(7, 4.2))
        build_continuous_panel(ax, dates, gt, pred, labels, summary, L or 0,
                               split_boundaries=split_boundaries)
        fig1.tight_layout()
        p1 = os.path.join(args.fig_dir, f"fig_miflu_eval_continuous{suffix}.png")
        fig1.savefig(p1, dpi=args.dpi)
        plt.close(fig1)
        # ---- 2. Diagnostics (rolling direction + peak bars) ----
        fig2, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.2))
        build_directional_panel(axL, dates, gt, pred)
        build_peakbars_panel(axR, peak_df)
        fig2.tight_layout()
        p2 = os.path.join(args.fig_dir, f"fig_miflu_eval_diagnostics{suffix}.png")
        fig2.savefig(p2, dpi=args.dpi)
        plt.close(fig2)
        print(f"[fig] -> {p1}")
        print(f"[fig] -> {p2}")
        print(f"[OK ] plotted TEST split only ({len(gt)} weeks) for L={L}")
        return

    # ── DEPRECATED walk-forward path (kept for the ChatTime variant only) ──
    print("[WARN] Using DEPRECATED ChatTime L=52 walk-forward path. "
          "Prefer --pred_csv (paper protocol).")
    for p in (args.walkforward_csv, args.indicators_csv, args.summary_json):
        if not os.path.exists(p):
            print(f"[BLOCKER] missing input: {p}")
            sys.exit(3)
    df = pd.read_csv(args.walkforward_csv)
    dates = parse_dates(df["date"].astype(str))
    gt = df["ground_truth"].to_numpy(dtype=float)
    pred = df["prediction"].to_numpy(dtype=float)
    peak_df = pd.read_csv(args.indicators_csv)
    with open(args.summary_json) as f:
        summary = json.load(f)
    labels = phase_label(gt)
    fig1, ax = plt.subplots(figsize=(7, 4.2))
    build_continuous_panel(ax, dates, gt, pred, labels, summary, L or 52)
    fig1.tight_layout()
    p1 = os.path.join(args.fig_dir, "fig_miflu_eval_continuous_DEPRECATED.png")
    fig1.savefig(p1, dpi=args.dpi)
    plt.close(fig1)
    fig2, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.2))
    build_directional_panel(axL, dates, gt, pred)
    build_peakbars_panel(axR, peak_df)
    fig2.tight_layout()
    p2 = os.path.join(args.fig_dir, "fig_miflu_eval_diagnostics_DEPRECATED.png")
    fig2.savefig(p2, dpi=args.dpi)
    plt.close(fig2)
    md_p = os.path.join(args.met_dir, "miflu_verdict_table_DEPRECATED.md")
    write_verdict_table(summary, md_p)
    print(f"[fig] -> {p1}")
    print(f"[fig] -> {p2}")
    print(f"[md ] -> {md_p}")


if __name__ == "__main__":
    main()
