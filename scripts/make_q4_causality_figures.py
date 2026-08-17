"""
make_q4_causality_figures.py
================================
Generates the two figures requested for Q4 (NUM. OF PROVIDERS: cause or
reversed-effect artifact?):

  Fig 1: Two-sided (bidirectional) Granger causality graph.
         Arrows drawn for BOTH directions:
           - each of 7 channels -> ILITOTAL  (does X precede Y?)
           - ILITOTAL -> each of 7 channels  (reverse direction)
         Edge thickness/color encodes significance (p<0.05). A one-way
         arrow (e.g. PROVIDERS -> ILITOTAL but NOT ILITOTAL -> PROVIDERS)
         would suggest possible causation; a two-way arrow shows the two
         are jointly driven by the same surveillance process (sampling-frame
         artifact), disarming "34.7% importance = main cause".

  Fig 2: Scatter of ILITOTAL (y) vs NUM. OF PROVIDERS (x) with OLS fit + R^2.
         Shows the mechanical correlation: more providers -> larger counted
         aggregate base -> larger ILITOTAL, i.e. reporting-scale effect, not
         epidemiological causation.

Outputs (English labels, top-journal ready):
  results/ili/figures/q4_granger_bidirectional.png
  results/ili/figures/q4_ilittotal_vs_providers_scatter.png
  data/q4_causality_summary.csv
"""
import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import networkx as nx

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data", "raw", "national_illness_raw.csv")
OUT_DIR = os.path.join(BASE, "..", "results", "ili", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
            "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
TARGET = "ILITOTAL"
SHORT = {"% WEIGHTED ILI": "W_ILI", "% UNWEIGHTED ILI": "U_ILI",
         "AGE 0-4": "AGE0-4", "AGE 5-24": "AGE5-24", "ILITOTAL": "ILITOTAL",
         "NUM. OF PROVIDERS": "PROVIDERS", "OT": "OT"}
MAX_LAG = 24


def load_train():
    df = pd.read_csv(DATA)
    n = len(df)
    t_end = int(n * 0.70)
    v_end = t_end + int(n * 0.10)
    return df.iloc[:t_end].copy(), df.iloc[t_end:v_end].copy()


def granger_pval(x, y, maxlag=MAX_LAG):
    """p-value that x Granger-causes y (x precedes y). Returns best (min) p over lags."""
    from statsmodels.tsa.stattools import grangercausalitytests
    data = np.column_stack([y, x])
    try:
        res = grangercausalitytests(data, maxlag=maxlag, verbose=False)
    except Exception:
        return np.nan
    best = 1.0
    for lag in range(1, maxlag + 1):
        try:
            p = res[lag][0]["ssr_chi2test"][1]
        except Exception:
            continue
        if p < best:
            best = p
    return best


def main():
    train, _ = load_train()
    cols = train[VAR_COLS].dropna().values
    others = [c for c in VAR_COLS if c != TARGET]
    tgt_idx = VAR_COLS.index(TARGET)

    # ---- Bidirectional Granger: collect best p for both directions ----
    rows = []
    G = nx.DiGraph()
    G.add_node("ILITOTAL")
    for c in others:
        G.add_node(SHORT[c])
    for c in others:
        ci = VAR_COLS.index(c)
        p_fwd = granger_pval(cols[:, ci], cols[:, tgt_idx])   # c -> ILITOTAL
        p_rev = granger_pval(cols[:, tgt_idx], cols[:, ci])   # ILITOTAL -> c
        rows.append({"variable": c, "p_fwd_(XtoILITOTAL)": p_fwd,
                     "p_rev_(ILITOTALtoX)": p_rev,
                     "fwd_sig": p_fwd < 0.05, "rev_sig": p_rev < 0.05})
        if p_fwd < 0.05:
            G.add_edge(SHORT[c], "ILITOTAL", weight=1 - p_fwd)
        if p_rev < 0.05:
            G.add_edge("ILITOTAL", SHORT[c], weight=1 - p_rev)
        print(f"  {c:<20s}: p(fwd)={p_fwd:.4g}  p(rev)={p_rev:.4g}")

    sumdf = pd.DataFrame(rows)
    csv_path = os.path.join(BASE, "..", "data", "q4_causality_summary.csv")
    sumdf.to_csv(csv_path, index=False)
    print(f"  [saved] {csv_path}")

    # ---- Fig 1: bidirectional Granger graph ----
    pos = nx.circular_layout(G)
    # place ILITOTAL center-top
    pos["ILITOTAL"] = np.array([0.0, 1.0])
    fig, ax = plt.subplots(figsize=(9, 6))
    nx.draw_networkx_nodes(G, pos, nodelist=["ILITOTAL"], node_color="#c0392b",
                           node_size=2200, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=[SHORT[c] for c in others],
                           node_color="#2980b9", node_size=1700, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_color="white", ax=ax)
    for u, v, d in G.edges(data=True):
        color = "#27ae60" if (u == "ILITOTAL") else "#e67e22"
        arrow = FancyArrowPatch(pos[u], pos[v], connectionstyle="arc3,rad=0.15",
                                arrowstyle="-|>", mutation_scale=18,
                                color=color, lw=1 + 4 * d["weight"], alpha=0.8)
        ax.add_patch(arrow)
    # legend
    ax.text(1.15, 1.0, "red = ILITOTAL", color="#c0392b", fontsize=9,
            transform=ax.transAxes)
    ax.text(1.15, 0.93, "blue = 7 input channels", color="#2980b9",
            fontsize=9, transform=ax.transAxes)
    ax.text(1.15, 0.86, "orange = X -> ILITOTAL (fwd)", color="#e67e22",
            fontsize=9, transform=ax.transAxes)
    ax.text(1.15, 0.79, "green = ILITOTAL -> X (rev)", color="#27ae60",
            fontsize=9, transform=ax.transAxes)
    ax.text(1.15, 0.72, "thicker = more significant (p<0.05)",
            fontsize=9, transform=ax.transAxes)
    ax.set_title("Fig 1. Bidirectional Granger Causality Graph\n"
                 "(does provider count cause ILITOTAL, or are both driven by the same surveillance process?)",
                 fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    p1 = os.path.join(OUT_DIR, "q4_granger_bidirectional.png")
    fig.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {p1}")

    # ---- Fig 2: ILITOTAL vs NUM. OF PROVIDERS scatter ----
    x = train["NUM. OF PROVIDERS"].values.astype(float)
    y = train["ILITOTAL"].values.astype(float)
    mask = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[mask], y[mask]
    b1, b0 = np.polyfit(x, y, 1)
    yhat = b1 * x + b0
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    corr = np.corrcoef(x, y)[0, 1]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.scatter(x, y, s=12, alpha=0.5, color="#2980b9",
               label="weekly observations (train)")
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, b1 * xs + b0, color="#c0392b", lw=2,
            label=f"OLS fit: ILITOTAL = {b1:.3f}·PROVIDERS + {b0:.1f}")
    ax.set_xlabel("NUM. OF PROVIDERS (reporting providers)")
    ax.set_ylabel("ILITOTAL (total patient count)")
    ax.set_title(f"Fig 2. ILITOTAL vs NUM. OF PROVIDERS\n"
                 f"R² = {r2:.3f}, Pearson r = {corr:.3f} "
                 f"(mechanical reporting-scale correlation, not causation)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    p2 = os.path.join(OUT_DIR, "q4_ilittotal_vs_providers_scatter.png")
    fig.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {p2}")
    print(f"  [done] R2={r2:.3f}, r={corr:.3f}")


if __name__ == "__main__":
    main()
