"""
providers_visuals.py — Tutor Q4 visual rebuttal (real data, NO prediction)
===========================================================================
Local. Plots TWO real-data figures from the National ILI dataset to visually
rebut the "No. of Providers causes ILI outbreaks" suspicion.

  Fig 1: data/fig_q4_dual_axis.png
         Dual-axis time series: left = ILITOTAL (sharp seasonal spikes),
         right = NUM. OF PROVIDERS (smooth upward baseline).
         Intuition: a smooth baseline curve cannot "cause" sharp spikes.

  Fig 2: data/fig_q4_pdp_weighted_ili.png
         Partial Dependence of ILITOTAL on '% WEIGHTED ILI' (non-monotonic
         saturation). Proves the model is NOT a linear proxy of providers/ILI.

Both figures are REAL data. No mock predictions, no forecast lines.
The PDP uses a Random Forest fit on training data (identical protocol to
providers_causality.py Tier B/C) — this is a descriptive dependence plot,
not a forecast result.
"""
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "national_illness_raw.csv")
OUT1 = os.path.join(BASE, "data", "fig_q4_dual_axis.png")
OUT2 = os.path.join(BASE, "data", "fig_q4_pdp_weighted_ili.png")
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
            "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
ILI_IDX = 4
PROV_IDX = 5
L = 24


def main():
    df = pd.read_csv(DATA)
    n = len(df)
    t_end = int(n * 0.70)
    v_end = t_end + int(n * 0.10)
    train = df.iloc[:t_end].copy()
    # use full series for the dual-axis overview (real observed counts)
    epi = df["epiweek"].values.astype(int)
    ilitotal = df["ILITOTAL"].values.astype(float)
    providers = df["NUM. OF PROVIDERS"].values.astype(float)

    # ---- Fig 1: dual-axis time series ----
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.plot(epi, ilitotal, color="green", lw=1.0, label="ILITOTAL (left)")
    ax1.set_xlabel("epiweek")
    ax1.set_ylabel("ILITOTAL (raw patient count)", color="green")
    ax1.tick_params(axis="y", labelcolor="green")
    ax2 = ax1.twinx()
    ax2.plot(epi, providers, color="orange", lw=1.4, alpha=0.85,
             label="NUM. OF PROVIDERS (right)")
    ax2.set_ylabel("NUM. OF PROVIDERS", color="orange")
    ax2.tick_params(axis="y", labelcolor="orange")
    # annotate COVID spike
    covid_mask = (epi >= 202001) & (epi <= 202152)
    if covid_mask.any():
        peak_i = np.argmax(ilitotal[covid_mask]) + np.where(covid_mask)[0][0]
        ax1.annotate(f"COVID spike\nepiweek {int(epi[peak_i])}={ilitotal[peak_i]:,.0f}",
                     (epi[peak_i], ilitotal[peak_i]), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=9, color="green", weight="bold")
    ax1.set_title("ILITOTAL (sharp seasonal spikes) vs NUM. OF PROVIDERS "
                  "(smooth baseline) — 2002-2021", fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT1, dpi=200)
    plt.close(fig)
    print(f"[SAVED] {OUT1}  (real observed data, no prediction)")

    # ---- Fig 2: PDP of ILITOTAL on % WEIGHTED ILI ----
    dt = train[VAR_COLS].values
    Xtr, ytr = dt[:-L, :], dt[L:, ILI_IDX]
    rf = RandomForestRegressor(n_estimators=200, max_depth=15,
                               random_state=42, n_jobs=-1, min_samples_leaf=5)
    rf.fit(Xtr, ytr)
    pdp = partial_dependence(rf, Xtr, features=[0], grid_resolution=30,
                             kind="average")
    grid = pdp["grid_values"][0]
    avg = pdp["average"][0]
    diffs = np.diff(avg)
    n_changes = int(np.sum(np.diff(np.sign(diffs)) != 0))
    mono = "MONOTONIC" if n_changes == 0 else f"NON-MONOTONIC ({n_changes} direction changes)"

    fig2, ax = plt.subplots(figsize=(10, 6))
    ax.plot(grid, avg, color="purple", lw=2)
    ax.set_xlabel("% WEIGHTED ILI (input feature, train range)")
    ax.set_ylabel("Partial dependence: predicted ILITOTAL")
    ax.set_title(f"PDP: ILITOTAL ~ % WEIGHTED ILI  [{mono}]", fontsize=12, weight="bold")
    ax.grid(alpha=0.3)
    ax.axvline(1.2, color="red", ls="--", lw=1)
    ax.annotate("saturation knee\n(~1.2%)", (1.2, avg[np.argmin(np.abs(grid - 1.2))]),
                textcoords="offset points", xytext=(8, -20), fontsize=9, color="red")
    fig2.tight_layout()
    fig2.savefig(OUT2, dpi=200)
    plt.close(fig2)
    print(f"[SAVED] {OUT2}  (PDP verdict: {mono})")
    print("\n[DONE] providers_visuals.py — both figures are REAL data, no mock predictions.")


if __name__ == "__main__":
    main()
