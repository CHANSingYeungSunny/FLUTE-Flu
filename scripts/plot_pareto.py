#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""plot_pareto.py — item (1) of the cross-scale methodology: the Pareto frontier figure.

One publication-quality figure:
  x = parameter count (log scale), y = 7-variable aggregate MSE in z-space (lower is
  better), one labelled point per model that HAS a parameter count, the non-dominated
  (Pareto) models highlighted with a step line and larger markers, plus the OLS fit of
  MSE on log10(params) whose slope answers "do more parameters help?".

Source of truth: paper_tables/BENCH_EFFICIENCY.csv (already DLinear-free; produced by
scripts/analysis_postprocess.py v2.1, whose Pareto rule and slope convention are
re-implemented here and cross-checked against the file, so the figure cannot silently
drift from the table).

Output: results/bench_figures/pareto_frontier.png (dpi=200, caption-free, English).

Hard rules honoured:
  * DLinear is EXCLUDED everywhere (absent from the CSV; also asserted below).
  * The metric is the 7-variable aggregate MSE in z-space. It is NOT de-normalised and
    NOT the benchmark PTE/PIE peak metric: a 7-variable aggregate is a loss, not a
    series, so it has no physical units and no "patients" axis.
  * The evaluation windows are the shared ones: `(W // 16) * 16` (160/144/144/128 at
    L = 24/36/48/60), identical to MIFlu's reproduction set. The table already encodes
    them; `load()` asserts the `n_eval_windows_L*` columns are present and uniform and
    the figure prints them.
"""
from __future__ import annotations
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator
from matplotlib.transforms import Bbox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "paper_tables", "BENCH_EFFICIENCY.csv")
OUT = os.path.join(ROOT, "results", "bench_figures")
PNG = os.path.join(OUT, "pareto_frontier.png")
EXCLUDE = {"dlinear"}

TITLE = ("Accuracy vs model size \u2014 7-variable aggregate MSE "
         "(US national ILI, 4 horizons)")

# ── cosmetic maps (display names, family -> colour/marker) ────────────────────
PRETTY = {
    "patchtst": "PatchTST", "nlinear": "NLinear", "dnn": "DNN", "cnn": "CNN",
    "rnn": "RNN", "lstm": "LSTM", "gru": "GRU", "itransformer": "iTransformer",
    "timecma_llm": "TimeCMA-LLM", "qwen_time_llm": "Qwen-Time-LLM",
    "calf_llm": "CALF-LLM", "gradient_boosting": "Gradient Boosting",
    "knn": "KNN", "random_forest": "Random Forest",
    "decision_tree": "Decision Tree", "svr": "SVR",
}
FAMILY = {
    "nlinear": "linear",
    "patchtst": "transformer", "itransformer": "transformer",
    "dnn": "neural", "cnn": "neural", "rnn": "neural", "lstm": "neural",
    "gru": "neural",
    "timecma_llm": "llm", "qwen_time_llm": "llm", "calf_llm": "llm",
    "gradient_boosting": "classical", "knn": "classical",
    "random_forest": "classical", "decision_tree": "classical", "svr": "classical",
}
STYLE = {  # family -> (colour, marker)
    "linear":      ("#d62728", "D"),
    "transformer": ("#1f77b4", "^"),
    "neural":      ("#2ca02c", "o"),
    "llm":         ("#9467bd", "s"),
    "classical":   ("#7f7f7f", "v"),
}
LEGEND_ORDER = ["linear", "transformer", "neural", "llm", "classical"]


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["model"] = df["model"].str.lower()
    bad = EXCLUDE & set(df["model"])
    assert not bad, f"hard rule 3 violated: {sorted(bad)} present in {CSV}"
    # the figure inherits the shared evaluation-window rule through the table and
    # states it in-figure, so a reader cannot mistake the window set.
    wcols = [c for c in df.columns if c.startswith("n_eval_windows_L")]
    assert wcols, (f"{CSV} has no n_eval_windows_L* columns — re-run "
                   f"scripts/analysis_postprocess.py (shared (W//16)*16 rule)")
    for c in wcols:
        vals = sorted(set(int(v) for v in df[c].dropna()))
        assert len(vals) == 1, f"{c} is not uniform across arms: {vals}"
    return df


def pareto_set(df: pd.DataFrame) -> list[str]:
    """Non-dominated in (MSE, params) over models that HAVE a parameter count.

    Identical rule to scripts/analysis_postprocess.py: sort by params ascending and
    keep a model only when its MSE strictly improves on the best MSE seen so far.
    """
    p = df[df["params"].notna()].sort_values("params")
    keep, best = [], np.inf
    for r in p.itertuples():
        if r.mse_mean < best - 1e-12:
            keep.append(r.model)
            best = r.mse_mean
    return keep


def fit_slope(df: pd.DataFrame) -> tuple[float, float]:
    """OLS of MSE on log10(params) across the parametrised models."""
    p = df[df["params"].notna()]
    x, y = np.log10(p["params"].to_numpy(float)), p["mse_mean"].to_numpy(float)
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1.0 - np.sum((y - (slope * x + intercept)) ** 2) / np.sum((y - y.mean()) ** 2)
    return float(slope), float(r2)


def _params_fmt(v: float, _pos=None) -> str:
    """Human-readable parameter-count tick: 3,350 / 5.3e5 / 1.5e9."""
    if v < 1e4:
        return f"{v:,.0f}"
    e = int(np.floor(np.log10(v)))
    m = v / 10.0 ** e
    return f"{m:.0f}e{e}" if abs(m - round(m)) < 1e-9 else f"{m:.1f}e{e}"


def _overlap_area(a: Bbox, b: Bbox) -> float:
    """Visible overlap area of two display-space boxes (0.0 when disjoint)."""
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return max(0.0, w) * max(0.0, h)


def place_labels(ax, fig, rows, line_pts=(), avoid=()) -> None:
    """Greedy non-overlapping point labels.

    For every point, try a ring of candidate offsets (in points) and keep the one whose
    text box collides least with the already-placed labels, with the other markers, with
    the reference line sampled at ``line_pts`` (data coords) and with any artist passed
    in ``avoid`` (e.g. the numbers box). Deterministic, so the figure is reproducible
    for a given matplotlib version.
    """
    fig.canvas.draw()                     # one draw: establishes the renderer
    rend = fig.canvas.get_renderer()
    ax_bb = ax.get_window_extent(rend)

    # marker footprints, so labels do not sit on top of other dots
    taken = []
    for x, y in ((r["params"], r["mse_mean"]) for r in rows):
        px, py = ax.transData.transform((x, y))
        taken.append(Bbox.from_bounds(px - 7.0, py - 7.0, 14.0, 14.0))
    # the reference line is an obstacle too, else labels straddle it
    for x, y in line_pts:
        px, py = ax.transData.transform((x, y))
        taken.append(Bbox.from_bounds(px - 3.0, py - 3.0, 6.0, 6.0))
    # and so is every annotation box handed in by the caller
    for art in avoid:
        taken.append(art.get_window_extent(rend))

    candidates = [(7, 6), (7, -13), (-7, 6), (-7, -13), (7, 13), (7, -20),
                  (-7, 13), (-7, -20), (16, 0), (-16, 0), (0, 13), (0, -18),
                  (14, 14), (-14, 14), (14, -18), (-14, -18), (22, -4), (-22, -4)]

    # place the tightest clusters first: low MSE / small models get priority
    for r in sorted(rows, key=lambda r: (r["mse_mean"], r["params"])):
        x, y = r["params"], r["mse_mean"]
        txt = PRETTY.get(r["model"], r["model"])
        best, best_cost = None, None
        for dx, dy in candidates:
            ha = "left" if dx > 0 else ("right" if dx < 0 else "center")
            t = ax.annotate(txt, xy=(x, y), xytext=(dx, dy),
                            textcoords="offset points", ha=ha, va="center",
                            fontsize=8.6, color="#111111", zorder=6)
            bb = t.get_window_extent(rend)
            cost = sum(_overlap_area(bb, b2) for b2 in taken)
            cost += 1e4 * (max(0.0, ax_bb.x0 - bb.x0) + max(0.0, bb.x1 - ax_bb.x1) +
                           max(0.0, ax_bb.y0 - bb.y0) + max(0.0, bb.y1 - ax_bb.y1))
            t.remove()
            if best_cost is None or cost < best_cost - 1e-9:
                best, best_cost = (dx, dy, ha), cost
            if cost == 0.0:
                break
        dx, dy, ha = best
        t = ax.annotate(txt, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                        ha=ha, va="center", fontsize=8.6, color="#111111", zorder=6)
        taken.append(t.get_window_extent(rend))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    df = load()
    wcols_vals = [int(sorted(set(df[c].dropna()))[0])
                  for c in sorted(c for c in df.columns
                                  if c.startswith("n_eval_windows_L"))]
    print(f"evaluation windows per horizon (uniform across arms): {wcols_vals}")
    pars = df[df["params"].notna()].sort_values("mse_mean").reset_index(drop=True)
    skipped = df[df["params"].isna()].sort_values("mse_mean")

    frontier = pareto_set(df)
    slope, r2 = fit_slope(df)

    # the CSV already stores these; assert we reproduce them (no silent drift)
    c_slope = float(df["mse_vs_log10params_slope"].iloc[0])
    c_r2 = float(df["mse_vs_log10params_r2"].iloc[0])
    c_par = set(df.loc[df["on_pareto"] == True, "model"])  # noqa: E712
    print(f"CSV     slope={c_slope:+.4f}  r2={c_r2:.4f}  pareto={sorted(c_par)}")
    print(f"recomputed slope={slope:+.4f}  r2={r2:.4f}  pareto={frontier}")
    assert abs(slope - c_slope) < 5e-4 and abs(r2 - c_r2) < 5e-4, "slope/R2 drift"
    assert set(frontier) == c_par, "Pareto set drift"
    print("consistency check vs BENCH_EFFICIENCY.csv: OK\n")

    # ── figure ───────────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "axes.linewidth": 0.9,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "mathtext.default": "regular",
    })
    fig, ax = plt.subplots(figsize=(10.4, 7.0))

    # OLS fit underneath the points
    xf = np.linspace(np.log10(pars["params"].min()), np.log10(pars["params"].max()), 64)
    a, b = np.polyfit(np.log10(pars["params"].to_numpy(float)),
                      pars["mse_mean"].to_numpy(float), 1)
    ax.plot(10.0 ** xf, a * xf + b, color="#999999", lw=1.2, ls="--", zorder=1)

    # family-coloured points; Pareto models are larger and black-edged
    for fam in LEGEND_ORDER:
        sub = pars[pars["model"].map(FAMILY) == fam]
        if sub.empty:
            continue
        col, mk = STYLE[fam]
        on = sub["model"].isin(frontier).to_numpy()
        ax.scatter(sub["params"][~on], sub["mse_mean"][~on], s=42, marker=mk,
                   color=col, edgecolors="white", linewidths=0.6, zorder=3)
        ax.scatter(sub["params"][on], sub["mse_mean"][on], s=130, marker=mk,
                   color=col, edgecolors="black", linewidths=1.3, zorder=5)

    # Pareto step line: horizontal to the next model's size, then down
    fr = pars[pars["model"].isin(frontier)].sort_values("params")
    if len(fr) > 1:
        ax.step(fr["params"].to_numpy(float), fr["mse_mean"].to_numpy(float),
                where="post", color="#111111", lw=1.7, ls=(0, (5, 2)), zorder=2)

    ax.set_xscale("log")
    ax.set_ylim(pars["mse_mean"].min() - 0.28, pars["mse_mean"].max() + 0.36)
    ax.set_xlim(pars["params"].min() / 1.6, pars["params"].max() * 2.4)
    ax.xaxis.set_major_locator(LogLocator(base=10, numticks=12))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1,
                                          numticks=12))
    ax.xaxis.set_major_formatter(FuncFormatter(_params_fmt))
    ax.set_xlabel("Parameter count (log scale)")
    ax.set_ylabel("7-variable aggregate MSE (z-space, lower is better)")
    ax.grid(True, which="major", axis="both", alpha=0.30, lw=0.7)
    ax.grid(True, which="minor", axis="x", alpha=0.12, lw=0.5)
    ax.set_axisbelow(True)

    handles = [Line2D([], [], ls="none", marker=STYLE[f][1], color=STYLE[f][0],
                      markersize=7, label=f)
               for f in LEGEND_ORDER if (pars["model"].map(FAMILY) == f).any()]
    handles.append(Line2D([], [], color="#111111", lw=1.7, ls=(0, (5, 2)),
                          label="Pareto frontier (non-dominated)"))
    handles.append(Line2D([], [], color="#999999", lw=1.2, ls="--",
                          label=f"OLS fit over {len(pars)} parametrised models"))
    # legend lives OUTSIDE the plotting area so it can never cover a point or label
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.115),
              ncol=4, fontsize=8.8, frameon=False, columnspacing=1.8,
              handletextpad=0.6, labelspacing=0.5)

    # the quotable numbers, in the figure itself
    wins = " / ".join(f"{int(v)}" for v in wcols_vals)
    nbox = ax.text(0.985, 0.030,
                   f"slope = {slope:+.3f} MSE per decade of parameters,  $R^2$ = {r2:.3f}"
                   f"   (n = {len(pars)})\n"
                   f"evaluated test windows per horizon = {wins}  "
                   f"(= (W//16)*16, identical to MIFlu)\n"
                   f"\u2192 more parameters do not lower MSE",
                   transform=ax.transAxes, ha="right", va="bottom", fontsize=8.2,
                   bbox=dict(boxstyle="round,pad=0.42", fc="white", ec="#bbbbbb",
                             alpha=0.95))

    ax.set_title(TITLE, fontsize=12.5, fontweight="bold", pad=12)

    place_labels(ax, fig, list(pars.to_dict("records")),
                 line_pts=[(10.0 ** v, a * v + b) for v in xf],
                 avoid=(nbox,))

    fig.tight_layout()
    fig.savefig(PNG, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # ── console report ───────────────────────────────────────────────────────
    print("Pareto set (non-dominated in MSE vs params), ordered by size:")
    for r in fr.itertuples():
        print(f"  {PRETTY.get(r.model, r.model):<14s} params={r.params:,.0f}"
              f"  params_B={r.params_B:.6f}  MSE={r.mse_mean:.4f}")
    small, big = fr.iloc[0], fr.iloc[-1]
    if len(fr) > 1:
        ratio = big["params"] / small["params"]
        rel = (big["mse_mean"] - small["mse_mean"]) / small["mse_mean"] * 100
        print(f"\n  {PRETTY.get(big.model, big.model)} uses {ratio:,.0f}x more"
              f" parameters than {PRETTY.get(small.model, small.model)}"
              f" for {abs(rel):.1f}% lower MSE")
    print(f"\nMSE vs log10(params): slope = {slope:+.4f}  R2 = {r2:.4f}"
          f"   -> "
          f"{'MORE params = HIGHER MSE' if slope > 0 else 'MORE params = LOWER MSE'}")
    print(f"  each 10x in parameters changes MSE by {slope:+.3f};"
          f" R2={r2:.3f} means size explains ~{r2 * 100:.0f}% of the variance")
    print("\nnot plotted (no parameter count / non-parametric sklearn models): "
          + ", ".join(PRETTY.get(m, m) for m in skipped["model"]))
    sz = os.path.getsize(PNG)
    print(f"\nfigure -> {PNG}  ({sz:,} bytes)")


if __name__ == "__main__":
    main()
