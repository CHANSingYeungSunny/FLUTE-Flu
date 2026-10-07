"""Generate two supplementary Wave-1 figures:
  fig6_family_comparison.png  — model avg_MSE_4L with 95% CI, colored by family
  fig7_seed_stability.png      — per-seed avg_MSE_4L distribution (box + strip)

Reads from results/v3_clean/analysis (model_ranking.csv, primary_seed_level.csv).
Pure matplotlib/pandas; no HPC compute.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANALYSIS = os.path.join(os.path.dirname(__file__), "..", "..", "results", "v3_clean", "analysis")
ANALYSIS = os.path.abspath(ANALYSIS)
FIG = os.path.join(ANALYSIS, "figures")
os.makedirs(FIG, exist_ok=True)

FAMILY_COLOR = {"non_llm": "#2c7fb8", "llm": "#d95f0e"}
FAMILY_LABEL = {"non_llm": "Non-LLM", "llm": "LLM-based"}

# --- Fig 6: model avg_MSE_4L with 95% CI, family-colored ---
rank = pd.read_csv(os.path.join(ANALYSIS, "model_ranking.csv"))
rank = rank.sort_values("average_MSE_4L", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
colors = [FAMILY_COLOR[f] for f in rank["family"]]
x = np.arange(len(rank))
yerr = np.vstack([
    rank["average_MSE_4L"] - rank["MSE_4L_ci95_lo"],
    rank["MSE_4L_ci95_hi"] - rank["average_MSE_4L"],
])
ax.bar(x, rank["average_MSE_4L"], yerr=yerr, capsize=4,
       color=colors, alpha=0.85, edgecolor="black", linewidth=0.6)
ax.set_xticks(x)
ax.set_xticklabels(rank["model"], rotation=30, ha="right")
ax.set_ylabel("average MSE 4L (z-space, lower is better)")
ax.set_title("Figure 6. Primary architecture ranking with 95% CI (seeds 42–51)")
# legend
handles = [plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR[k], alpha=0.85)
           for k in FAMILY_COLOR]
ax.legend(handles, [FAMILY_LABEL[k] for k in FAMILY_COLOR], loc="upper left")
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig6_family_comparison.png"), dpi=160)
plt.close(fig)

# --- Fig 7: seed-level avg_MSE_4L distribution per model ---
seed = pd.read_csv(os.path.join(ANALYSIS, "primary_seed_level.csv"))
# per (model, seed) mean across 4 horizons
g = seed.groupby(["model", "seed"])["mse_all_7vars_full_horizon_z"].mean().reset_index()
g = g.rename(columns={"mse_all_7vars_full_horizon_z": "avg_MSE_4L"})
# order models by median
order = g.groupby("model")["avg_MSE_4L"].median().sort_values().index.tolist()

fig, ax = plt.subplots(figsize=(9, 5))
data = [g.loc[g["model"] == m, "avg_MSE_4L"].values for m in order]
box_colors = []
for m in order:
    fam = seed.loc[seed["model"] == m, "family"].iloc[0]
    box_colors.append(FAMILY_COLOR[fam])
bp = ax.boxplot(data, labels=order, patch_artist=True, showfliers=False)
for patch, c in zip(bp["boxes"], box_colors):
    patch.set_facecolor(c)
    patch.set_alpha(0.55)
    patch.set_edgecolor("black")
# jittered strip points
rng = np.random.default_rng(0)
for i, m in enumerate(order):
    vals = g.loc[g["model"] == m, "avg_MSE_4L"].values
    jx = rng.normal(0, 0.06, size=len(vals))
    fam = seed.loc[seed["model"] == m, "family"].iloc[0]
    ax.scatter(i + 1 + jx, vals, s=22, color=FAMILY_COLOR[fam],
               alpha=0.85, edgecolor="black", linewidth=0.4, zorder=3)
ax.set_ylabel("average MSE 4L per seed (10 seeds)")
ax.set_title("Figure 7. Seed-level stability of avg MSE 4L (10 frozen seeds)")
handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=FAMILY_COLOR[k],
                      markersize=8, label=FAMILY_LABEL[k]) for k in FAMILY_COLOR]
ax.legend(handles=handles, loc="upper left")
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig7_seed_stability.png"), dpi=160)
plt.close(fig)

print("wrote fig6_family_comparison.png and fig7_seed_stability.png")
