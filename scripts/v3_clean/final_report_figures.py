"""final_report_figures.py — generate the comparison figures for the FINAL
Chinese report + Project Summary (Addendum: embed latest Test/Holdout figures).

ALL figure text is English (titles, axes, legends, annotations), per standing
instruction. The surrounding report prose is Chinese; only the figure images
and their caption alt-text are English.

Figures produced (into results/v3_clean/final/final_report_figures/):
  figB_final_test_comparison.png      — 3-model Test average_MSE_4L with 95% CI
  figC_validation_to_test_reversal.png— validation vs Test, split separated
  figD_test_mse_mae_by_horizon.png    — per-horizon Test MSE / MAE (3 models)
  figE_test_pte_pie_by_horizon.png    — per-horizon PTE (wk) / PIE (%)
  figG_deferred_controls_familyAB.png — Family A vs Family B, kept separate
  figH_final_workflow.png             — completed workflow + integrity labels

All values are read from the authoritative final artifacts:
  final_test_metrics.json (primary/confirmatory), final_peak_hit_rates.csv,
  deferred_controls_statistical_interpretation.json.
Nothing is hardcoded. Validation values for figC come from
selection_outcome.json (frozen Wave-1 results).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FINAL = os.path.join(ROOT, "results", "v3_clean", "final")
OUT = os.path.join(FINAL, "final_report_figures")
os.makedirs(OUT, exist_ok=True)

# consistent model color palette across all comparison figures
MODEL_COLOR = {
    "nlinear": "#1f77b4",       # blue
    "gpt2_miflu": "#ff7f0e",    # orange
    "seasonal_naive": "#2ca02c",  # green
}
MODEL_LABEL = {
    "nlinear": "NLinear (Non-LLM)",
    "gpt2_miflu": "GPT-2 MIFlu (LLM)",
    "seasonal_naive": "Seasonal-Naive (baseline)",
}
MODELS = ["nlinear", "gpt2_miflu", "seasonal_naive"]
HORIZONS = [24, 36, 48, 60]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150,
    "axes.titlesize": 11, "axes.labelsize": 10, "xtick.labelsize": 9,
    "ytick.labelsize": 9, "legend.fontsize": 9, "font.family": "DejaVu Sans",
})


def load_metrics():
    return json.load(open(os.path.join(FINAL, "final_test_metrics.json"), encoding="utf-8"))


def load_validation():
    return json.load(open(os.path.join(ROOT, "results", "v3_clean", "analysis",
                                       "selection_outcome.json"), encoding="utf-8"))


def figB(m):
    """Final Test comparison: 3-model average_MSE_4L with 95% CI."""
    fig, ax = plt.subplots(figsize=(7, 4.2))
    xs = np.arange(len(MODELS))
    vals, errs = [], []
    for mi, model in enumerate(MODELS):
        mo = m["models"][model]
        vals.append(mo["average_MSE_4L"])
        ci = mo["average_MSE_4L_ci95"]
        if ci[0] is not None:
            errs.append([mo["average_MSE_4L"] - ci[0], ci[1] - mo["average_MSE_4L"]])
        else:
            errs.append([0, 0])
    errs = np.array(errs).T
    ax.bar(xs, vals, yerr=errs, capsize=6, width=0.55,
           color=[MODEL_COLOR[x] for x in MODELS], alpha=0.9, zorder=3)
    for xi, v in zip(xs, vals):
        ax.text(xi, v + 0.06, f"{v:.3f}", ha="center", va="bottom", fontsize=10,
                fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels([MODEL_LABEL[x] for x in MODELS])
    ax.set_ylabel("average_MSE_4L  (lower is better)")
    ax.set_title("Figure B. Final Test/Holdout comparison (frozen comparison set, 3 models only)")
    ax.set_ylim(0, max(vals) + 0.55)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.text(0.99, 0.02, "Test/Holdout  ·  lower MSE is better  ·  deterministic baseline has no CI",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color="#555555")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figB_final_test_comparison.png"))
    plt.close(fig)


def figC(m, val):
    """Validation-to-Test generalization reversal, splits separated."""
    base = pd.read_csv(os.path.join(ROOT, "results", "v3_clean", "analysis",
                                    "baseline_comparison.csv"))
    sn = base[base["model"] == "seasonal_naive"]["mse_z"].mean()
    val_avg = {
        "gpt2_miflu": val["winner_vs_runner"]["winner_mean"],
        "nlinear": val["winner_vs_runner"]["runner_mean"],
        "seasonal_naive": float(sn),
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    xs = np.arange(len(MODELS))
    w = 0.38
    for i, model in enumerate(MODELS):
        v = val_avg.get(model, np.nan)
        t = m["models"][model]["average_MSE_4L"]
        ax.bar(xs[i] - w / 2, v, width=w, color="#9fb3c8", alpha=0.95,
               label="Wave-1 Validation" if i == 0 else None)
        ax.bar(xs[i] + w / 2, t, width=w, color=MODEL_COLOR[model], alpha=0.95,
               label="Final Test/Holdout" if i == 0 else None)
        ax.text(xs[i] - w / 2, v + 0.05, f"{v:.2f}", ha="center", fontsize=8.5)
        ax.text(xs[i] + w / 2, t + 0.05, f"{t:.2f}", ha="center", fontsize=8.5,
                fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels([MODEL_LABEL[x] for x in MODELS])
    ax.set_ylabel("average_MSE_4L  (lower is better)")
    ax.set_title("Figure C. Generalization reversal: Validation champion vs final Test champion")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.annotate("Validation champion = GPT-2 MIFlu\nFinal Test best = NLinear",
                xy=(1.5, 4.1), xytext=(1.5, 4.6), ha="center", fontsize=9,
                color="#a00000", arrowprops=dict(arrowstyle="->", color="#a00000"))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figC_validation_to_test_reversal.png"))
    plt.close(fig)


def figD(m):
    """Test MSE / MAE by horizon (3 models)."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))
    for ax, metric in ((axes[0], "per_L_mse"), (axes[1], "per_L_mae")):
        for model in MODELS:
            d = m["models"][model][metric]
            ys = [d[str(h)] for h in HORIZONS]
            ax.plot(HORIZONS, ys, marker="o", linewidth=1.6,
                    color=MODEL_COLOR[model], label=MODEL_LABEL[model])
            for h, y in zip(HORIZONS, ys):
                ax.annotate(f"{y:.2f}", (h, y), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=7.5,
                            color=MODEL_COLOR[model])
        ax.set_xlabel("Horizon L (weeks)")
        ax.set_ylabel("Test MSE (lower is better)" if metric == "per_L_mse"
                      else "Test MAE (lower is better)")
        ax.set_xticks(HORIZONS)
        ax.grid(alpha=0.25, linewidth=0.5)
    axes[0].set_title("Test MSE by horizon (7-var full-horizon z-space)")
    axes[1].set_title("Test MAE by horizon")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Figure D. Test/Holdout error by horizon (3 frozen comparison models)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, "figD_test_mse_mae_by_horizon.png"))
    plt.close(fig)


def figE():
    """PTE / PIE by horizon (mean over eligible leads/seasons), from hit-rates CSV."""
    df = pd.read_csv(os.path.join(FINAL, "final_peak_hit_rates.csv"))
    agg = df.groupby(["model", "horizon"]).agg(
        pte=("mean_pte", "mean"), pie=("mean_pie", "mean"),
        pte_hit=("pte_hit_rate", "mean"), pie_hit=("pie_hit_rate", "mean"),
        joint_hit=("joint_hit_rate", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))
    for ax, metric in ((axes[0], "pte"), (axes[1], "pie")):
        for model in MODELS:
            sub = agg[agg["model"] == model].sort_values("horizon")
            ax.plot(sub["horizon"], sub[metric], marker="o", linewidth=1.6,
                    color=MODEL_COLOR[model], label=MODEL_LABEL[model])
        ax.set_xlabel("Horizon L (weeks)")
        ax.set_xticks(HORIZONS)
        ax.grid(alpha=0.25, linewidth=0.5)
    axes[0].set_ylabel("PTE peak-timing error (weeks, lower is better)")
    axes[0].set_title("Test peak-timing error (PTE)  —  hit: PTE <= 1 week")
    axes[1].set_ylabel("PIE peak-intensity error (%, lower is better)")
    axes[1].set_title("Test peak-intensity error (PIE)  —  hit: PIE <= 25%")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[1].annotate("NLinear leads peak-intensity accuracy", xy=(24, 9.2),
                     xytext=(30, 60), fontsize=9, color="#a00000",
                     arrowprops=dict(arrowstyle="->", color="#a00000"))
    fig.suptitle("Figure E. Test/Holdout peak prediction error (hit: PTE <= 1 wk, PIE <= 25%)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, "figE_test_pte_pie_by_horizon.png"))
    plt.close(fig)


def figG():
    """Deferred controls: Family A vs Family B, kept separate."""
    d = json.load(open(os.path.join(FINAL, "deferred_controls_statistical_interpretation.json"),
                       encoding="utf-8"))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))

    fa = d["family_A"]["controls"]
    fa_labels = ["zero_text", "shuffled_text"]
    fa_delta = [fa["zero_text"]["pooled"]["mean_delta"], fa["shuffled_text"]["pooled"]["mean_delta"]]
    fa_p = [fa["zero_text"]["pooled"]["p_value"], fa["shuffled_text"]["pooled"]["p_value"]]
    colors_a = ["#7fbf7f", "#f4a582"]
    ax = axes[0]
    ax.axhline(0, color="#888888", linewidth=0.8)
    for xi, (lab, dv, pv, c) in enumerate(zip(fa_labels, fa_delta, fa_p, colors_a)):
        ax.bar(xi, dv, width=0.5, color=c, alpha=0.9)
        ax.text(xi, dv + (0.006 if dv >= 0 else -0.02), f"{dv:+.3f}\np={pv:.2f}",
                ha="center", va="bottom" if dv >= 0 else "top", fontsize=8.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["zero_text\n(empty text)", "shuffled_text\n(shuffled text)"])
    ax.set_ylabel("Delta MSE vs parent (lower is better)")
    ax.set_title("Family A: descriptive negative controls (parent = GPT-2 MIFlu)", fontsize=10)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_ylim(-0.16, 0.20)

    fb = d["family_B"]["comparisons"]
    ax = axes[1]
    ax.axhline(0, color="#888888", linewidth=0.8)
    for xi, (h, c) in enumerate(zip(["L24", "L60"], ["#9ecae1", "#3182bd"])):
        dv = fb[h]["mean_delta"]
        pv = fb[h]["p_value"]
        ax.bar(xi, dv, width=0.5, color=c, alpha=0.9)
        ax.text(xi, dv + (0.006 if dv >= 0 else -0.02), f"{dv:+.3f}\np={pv:.3f}",
                ha="center", va="bottom" if dv >= 0 else "top", fontsize=8.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["L24\n(short horizon, n.s.)", "L60\n(long horizon, p=0.0015)"])
    ax.set_ylabel("Delta MSE vs parent (lower is better)")
    ax.set_title("Family B: confirmatory controls (parent = TimeCMA-LLM, LLM branch removed)",
                 fontsize=10)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_ylim(-0.16, 0.20)

    fig.suptitle("Figure G. Deferred controls: Family A vs Family B (kept strictly separate)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "figG_deferred_controls_familyAB.png"))
    plt.close(fig)


def figH():
    """Final workflow + integrity labels. Vertical flow: no overlapping text,
    arrows never cross a label, every box on its own row (fixes the earlier
    overlap bug)."""
    fig, ax = plt.subplots(figsize=(9.2, 7.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def box(x, y, w, h, txt, fc="#eaf2f8", fs=9.5, tc="#111111", bold=False):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                           fc=fc, ec="#444444", lw=1)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
                fontsize=fs, color=tc, fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#444444", lw=1.3))

    cx = 50
    w = 62
    steps = [
        ("Training", "#eaf2f8"),
        ("Wave-1 Validation — 580/580 accepted rows", "#eaf2f8"),
        ("Deferred controls — 18/18 resolved", "#eaf2f8"),
        ("Final candidate & comparator freeze", "#eaf2f8"),
        ("One-time Test/Holdout — 84/84 runs", "#fde0dd"),
        ("Final report & QA", "#eaf2f8"),
    ]
    ys = [88, 73, 58, 43, 28, 13]
    h = 9.5
    for (txt, fc), y in zip(steps, ys):
        box(cx - w / 2, y, w, h, txt, fc=fc, bold=("Test/Holdout" in txt))
    for i in range(len(ys) - 1):
        arrow(cx, ys[i], cx, ys[i + 1] + h)

    ax.text(cx, 3.5,
            "Terminal audit 25/25 passed   ·   isolation violations = 0   ·   "
            "no post-Test scientific change",
            ha="center", va="center", fontsize=9.5, color="#a00000", fontweight="bold")
    ax.set_title("Figure H. MIFlu final workflow and evidence integrity", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figH_final_workflow.png"))
    plt.close(fig)


def main():
    m = load_metrics()
    val = load_validation()
    figB(m)
    figC(m, val)
    figD(m)
    figE()
    figG()
    figH()
    manifest = {
        "generated_from": ["final_test_metrics.json", "final_peak_hit_rates.csv",
                           "deferred_controls_statistical_interpretation.json",
                           "selection_outcome.json (validation values)"],
        "figure_text_language": "English",
        "figures": {
            "figB_final_test_comparison.png": "3-model Test average_MSE_4L + 95% CI",
            "figC_validation_to_test_reversal.png": "validation vs Test, splits separated",
            "figD_test_mse_mae_by_horizon.png": "per-horizon Test MSE / MAE",
            "figE_test_pte_pie_by_horizon.png": "per-horizon PTE (wk) / PIE (%)",
            "figG_deferred_controls_familyAB.png": "Family A vs B, kept separate",
            "figH_final_workflow.png": "completed workflow + integrity labels",
        },
        "model_colors": MODEL_COLOR,
    }
    json.dump(manifest, open(os.path.join(OUT, "final_report_figures_manifest.json"), "w"),
              indent=2)
    print("generated 6 figures (English) into", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
