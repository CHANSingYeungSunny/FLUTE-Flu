#!/usr/bin/env python3
"""make_wave1_figures.py — generate Wave-1 analysis figures (PNG).

Reads the CSV outputs of analyze_wave1.py / analyze_wave1_secondary.py and
writes publication-style PNGs under results/v3_clean/analysis/figures/.
English labels (to avoid CJK font issues); report prose carries the Chinese.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
FIG = ANALYSIS / "figures"
FIG.mkdir(parents=True, exist_ok=True)

NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
C_NON = "#2c7fb8"
C_LLM = "#e67e22"
C_BASE = "#7f8c8d"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150,
    "axes.titlesize": 12, "axes.labelsize": 10, "xtick.labelsize": 9,
    "ytick.labelsize": 9, "font.family": "DejaVu Sans",
})


def color_of(model: str) -> str:
    return C_LLM if model in LLM else C_NON


def fig1_ranking() -> None:
    r = pd.read_csv(ANALYSIS / "model_ranking.csv")
    r = r.sort_values("average_MSE_4L", ascending=False)  # horizontal bar bottom->top
    colors = [color_of(m) for m in r["model"]]
    yerr = np.array([
        r["average_MSE_4L"] - r["MSE_4L_ci95_lo"],
        r["MSE_4L_ci95_hi"] - r["average_MSE_4L"],
    ])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(r["model"], r["average_MSE_4L"], xerr=yerr, color=colors,
            capsize=3, alpha=0.9)
    ax.set_xlabel("average MSE (7-var, full-horizon, z-space; lower is better)")
    ax.set_title("Wave-1 primary ranking by average_MSE_4L (95% CI over 10 seeds)")
    ax.axvline(0.7709, color="grey", linestyle="--", linewidth=0.7, alpha=0.6)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C_NON),
               plt.Rectangle((0, 0), 1, 1, color=C_LLM)]
    ax.legend(handles, ["Non-LLM", "LLM"], loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig1_model_ranking.png")
    plt.close(fig)


def fig2_per_horizon() -> None:
    s = pd.read_csv(ANALYSIS / "primary_summary_statistics.csv")
    models = NON_LLM + LLM
    horizons = [24, 36, 48, 60]
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(horizons))
    w = 0.1
    for i, m in enumerate(models):
        vals = [s[(s["model"] == m) & (s["horizon"] == h)]["mse_mean"].iloc[0]
                for h in horizons]
        ax.bar(x + (i - len(models) / 2 + 0.5) * w, vals, w,
               label=m, color=color_of(m), alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"L{h}" for h in horizons])
    ax.set_ylabel("MSE (7-var full-horizon z-space)")
    ax.set_title("Per-horizon MSE by model")
    ax.legend(ncol=2, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_per_horizon.png")
    plt.close(fig)


def fig3_ablation() -> None:
    a = pd.read_csv(ANALYSIS / "ablation_effects.csv").sort_values("delta_vs_parent")
    labels = [x.replace("without_", "no ").replace("_", " ") for x in a["ablation"]]
    colors = ["#c0392b" if p < 0.05 else "#95a5a6" for p in a["p_value_vs_parent"]]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(labels, a["delta_vs_parent"], color=colors, alpha=0.9)
    for b, p, d in zip(bars, a["p_value_vs_parent"], a["delta_vs_parent"]):
        ax.text(d + 0.001, b.get_y() + b.get_height() / 2,
                f"p={p:.3f}", va="center", fontsize=8)
    ax.set_xlabel("delta average_MSE_4L vs parent gpt2_miflu (positive = worse)")
    ax.set_title("Ablation effects (parent = gpt2_miflu)")
    ax.axvline(0, color="black", linewidth=0.8)
    handles = [plt.Rectangle((0, 0), 1, 1, color="#c0392b"),
               plt.Rectangle((0, 0), 1, 1, color="#95a5a6")]
    ax.legend(handles, ["significant (p<0.05)", "not significant"], loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_ablation_effects.png")
    plt.close(fig)


def fig4_seasonal_vs_llm() -> None:
    b = pd.read_csv(ANALYSIS / "baseline_comparison.csv")
    s = pd.read_csv(ANALYSIS / "primary_summary_statistics.csv")
    horizons = [24, 36, 48, 60]
    def line(model, col="mse_z", df=b):
        return [df[(df["model"] == model) & (df["horizon"] == h)][col].iloc[0]
                for h in horizons]
    def prim_line(model):
        return [s[(s["model"] == model) & (s["horizon"] == h)]["mse_mean"].iloc[0]
                for h in horizons]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(horizons, line("seasonal_naive"), "o-", color=C_BASE,
            label="seasonal_naive (deterministic)")
    ax.plot(horizons, line("last_value_naive"), "s--", color="#bdc3c7",
            label="last_value_naive")
    ax.plot(horizons, prim_line("gpt2_miflu"), "o-", color=C_LLM,
            label="gpt2_miflu (LLM winner)")
    ax.plot(horizons, prim_line("nlinear"), "o-", color=C_NON,
            label="nlinear (Non-LLM winner)")
    ax.set_xlabel("horizon (weeks)")
    ax.set_ylabel("MSE (7-var full-horizon z-space)")
    ax.set_title("Deterministic baselines vs top models")
    ax.legend(fontsize=8)
    ax.set_xticks(horizons)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_seasonal_vs_llm.png")
    plt.close(fig)


def fig5_resource_tradeoff() -> None:
    res = pd.read_csv(ANALYSIS / "resource_storage.csv")
    r = pd.read_csv(ANALYSIS / "model_ranking.csv")
    res = res.merge(r[["model", "average_MSE_4L"]], on="model", how="left")
    res = res[res["model"].isin(NON_LLM + LLM)].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    for _, row in res.iterrows():
        ax.scatter(row["trainable_parameters"], row["average_MSE_4L"],
                   color=color_of(row["model"]), s=60, alpha=0.9)
        ax.annotate(row["model"], (row["trainable_parameters"], row["average_MSE_4L"]),
                    fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("trainable parameters (log scale)")
    ax.set_ylabel("average_MSE_4L (lower is better)")
    ax.set_title("Accuracy vs parameter count")
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=C_NON,
                          label="Non-LLM"),
               plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=C_LLM,
                          label="LLM")]
    ax.legend(handles=handles, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig5_resource_tradeoff.png")
    plt.close(fig)


def main() -> None:
    fig1_ranking()
    fig2_per_horizon()
    fig3_ablation()
    fig4_seasonal_vs_llm()
    fig5_resource_tradeoff()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
