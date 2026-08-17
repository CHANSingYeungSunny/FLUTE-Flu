"""
make_q4_overlay_figure.py
==========================
Generates the PRIMARY evidence figure for Q4 (NUM. OF PROVIDERS: cause or
reversed-effect artifact?).

  Fig: Overlay time-series of GROUND-TRUTH ILITOTAL (blue, left axis) and
       GROUND-TRUTH NUM. OF PROVIDERS (orange, right axis) on the SAME weekly
       time axis, across the full 2002-2021 span (1025 weeks).

Why this figure (top-journal framing):
  ILITOTAL is *defined* as the aggregate count of ILI cases reported by the
  participating providers. So ILITOTAL and NUM. OF PROVIDERS MUST co-move every
  flu season -- this is a denominator / sampling-frame effect, not epidemiological
  causation. The overlay makes the annual winter co-movement visually obvious;
  the bidirectional Granger graph + scatter (make_q4_causality_figures.py) then
  separate "real lead information" (PROVIDERS -> ILITOTAL, p=1.2e-6) from the
  mechanical co-movement (r=0.704).

Output (English labels, top-journal ready):
  results/ili/figures/q4_overlay_ilitotal_vs_providers.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data", "raw", "national_illness_raw.csv")
OUT_DIR = os.path.join(BASE, "..", "results", "ili", "figures")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    df = pd.read_csv(DATA).dropna(subset=["ILITOTAL", "NUM. OF PROVIDERS"]).reset_index(drop=True)
    n = len(df)

    # x axis: epiweek (YYYYWW) -> fractional year for readable ticks
    epiweek = df["epiweek"].astype(int).values
    year = epiweek // 100
    week = epiweek % 100
    x = year + (week - 1) / 52.0  # fractional year, monotonic

    ilitotal = df["ILITOTAL"].astype(float).values
    providers = df["NUM. OF PROVIDERS"].astype(float).values

    # flu-season shading: weeks ~40..53 (prev year-end) and 1..20 (early year)
    # i.e. roughly Oct -> mid-May. Build contiguous shaded spans.
    in_season = ((week >= 40) | (week <= 20)).astype(int)
    # We shade by detecting runs of in_season==1 (handles year wrap since sorted)
    season_spans = []
    start = None
    for i, flag in enumerate(in_season):
        if flag == 1 and start is None:
            start = i
        elif flag == 0 and start is not None:
            season_spans.append((start, i - 1))
            start = None
    if start is not None:
        season_spans.append((start, n - 1))

    fig, ax1 = plt.subplots(figsize=(12, 5.5))

    # flu-season shading (behind)
    for s, e in season_spans:
        ax1.axvspan(x[s], x[e], color="#f2c14e", alpha=0.18, zorder=0)

    color_ili = "#1f77b4"
    color_prov = "#ff7f0e"

    ax1.plot(x, ilitotal, color=color_ili, lw=1.1, label="ILITOTAL (total patient count)", zorder=3)
    ax1.set_xlabel("Year")
    ax1.set_ylabel("ILITOTAL (total patient count)", color=color_ili)
    ax1.tick_params(axis="y", labelcolor=color_ili)

    ax2 = ax1.twinx()
    ax2.plot(x, providers, color=color_prov, lw=1.1, label="NUM. OF PROVIDERS (reporting providers)", zorder=2)
    ax2.set_ylabel("NUM. OF PROVIDERS (reporting providers)", color=color_prov)
    ax2.tick_params(axis="y", labelcolor=color_prov)

    # year ticks every 2 years
    ymin, ymax = int(x.min()), int(x.max()) + 1
    ax1.set_xticks(range(ymin, ymax, 2))
    ax1.set_xlim(x.min(), x.max())

    # combined legend (only the two real curves; flu-season shading kept visual-only)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9, framealpha=0.9)

    ax1.set_title("Fig (main). Ground-truth ILITOTAL vs NUM. OF PROVIDERS, 2002–2021\n"
                  "Both peak every flu season — a sampling-frame (denominator) effect, not causation",
                  fontsize=11)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "q4_overlay_ilitotal_vs_providers.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {out}")
    print(f"  span: {int(epiweek.min())} .. {int(epiweek.max())}, n={n} weeks")


if __name__ == "__main__":
    main()
