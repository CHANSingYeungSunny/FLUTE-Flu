#!/usr/bin/env python3
"""Regenerate all 8 Wave-1 figures with one consistent colour scheme.

Reads ONLY authoritative CSVs/JSONs under results/v3_clean/analysis/ (no
hard-coded results). Exports each figure's source data to figures/data/.
Colour: Non-LLM=blue family, LLM=orange/red family, baseline=grey family;
each model keeps a fixed colour across all figures.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
FIG = ANALYSIS / "figures"
DATA = FIG / "data"
FIG.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

FAMILY_COLOR = {"non_llm": "#2c7fb8", "llm": "#d95f0e", "baseline": "#636363"}
FAMILY_LABEL = {"non_llm": "Non-LLM", "llm": "LLM", "baseline": "Baseline"}
MODEL_COLOR = {
    "nlinear": "#08519c", "dlinear": "#2c7fb8", "patchtst": "#6baed6",
    "itransformer": "#a6bddb", "gpt2_miflu": "#a50f15", "qwen_time_llm": "#d95f0e",
    "calf_llm": "#f16913", "timecma_llm": "#fdae6b",
    "seasonal_naive": "#252525", "last_value_naive": "#969696",
}
NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
HORIZONS = [24, 36, 48, 60]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 160, "axes.titlesize": 11,
    "axes.labelsize": 9.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.fontsize": 8, "font.family": "DejaVu Sans",
})


def family_of(model):
    return "llm" if model in LLM else ("non_llm" if model in NON_LLM else "baseline")


def stamp(ax, y=0.015):
    ax.text(0.995, y, "validation-only (test/holdout sealed)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
            style="italic", color="#666666")


def save(df, name):
    df.to_csv(DATA / name, index=False)


def fam_handles():
    return [plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR[k]) for k in FAMILY_COLOR]


def mod_handles(models):
    return [plt.Rectangle((0, 0), 1, 1, color=MODEL_COLOR[m]) for m in models]


# ---------------------------------------------------------------- fig 1
def fig1():
    r = pd.read_csv(ANALYSIS / "model_ranking.csv").sort_values(
        "average_MSE_4L", ascending=False)
    models = r["model"].tolist()
    yerr = np.vstack([r["average_MSE_4L"] - r["MSE_4L_ci95_lo"],
                      r["MSE_4L_ci95_hi"] - r["average_MSE_4L"]])
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.barh(models, r["average_MSE_4L"], xerr=yerr,
            color=[MODEL_COLOR[m] for m in models], capsize=3, alpha=0.9,
            edgecolor="black", linewidth=0.4,
            error_kw={"elinewidth": 1, "ecolor": "black"})
    for m, v in zip(models, r["average_MSE_4L"]):
        ax.text(v + 0.012, m, f"{v:.3f}", va="center", fontsize=8)
    ax.set_xlabel("average_MSE_4L  (7-var full-horizon z-space; lower is better)")
    ax.set_title("Figure 1. Primary architecture ranking with 95% CI "
                 f"(N={len(models)} models, 10 frozen seeds 42\u201351 each)")
    ax.set_xlim(left=0)
    ax.legend(fam_handles(), [FAMILY_LABEL[k] for k in FAMILY_COLOR], loc="lower right")
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig1_model_ranking_ci.png"); plt.close(fig)
    save(r[["model", "family", "average_MSE_4L", "MSE_4L_sd", "MSE_4L_ci95_lo",
            "MSE_4L_ci95_hi", "average_MAE_4L", "n_seeds"]], "fig1_model_ranking_ci.csv")


# ---------------------------------------------------------------- fig 2
def fig2():
    s = pd.read_csv(ANALYSIS / "primary_summary_statistics.csv")
    rank = pd.read_csv(ANALYSIS / "model_ranking.csv").sort_values("average_MSE_4L")
    models = rank["model"].tolist()
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    x = np.arange(len(HORIZONS))
    for i, m in enumerate(models):
        sub = s[s["model"] == m].sort_values("horizon")
        y = sub["mse_mean"].values
        ci_lo = y - sub["mse_ci95_lo"].values
        ci_hi = sub["mse_ci95_hi"].values - y
        ax.errorbar(x, y, yerr=[ci_lo, ci_hi], marker="o", ms=4, lw=1.4,
                    color=MODEL_COLOR[m], label=m, capsize=2.5, elinewidth=1)
    ax.set_xticks(x); ax.set_xticklabels([f"L{h}" for h in HORIZONS])
    ax.set_xlabel("horizon (weeks)")
    ax.set_ylabel("MSE  (7-var full-horizon z-space; lower is better)")
    ax.set_title("Figure 2. Per-horizon MSE for all 8 architectures "
                 "(markers = mean over 10 seeds, bars = 95% CI)")
    ax.legend(ncol=2, loc="upper left")
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig2_per_horizon.png"); plt.close(fig)
    save(s[["model", "family", "horizon", "n", "mse_mean", "mse_sd",
            "mse_ci95_lo", "mse_ci95_hi", "mae_mean", "mae_ci95_lo", "mae_ci95_hi"]],
         "fig2_per_horizon.csv")


# ---------------------------------------------------------------- fig 3
def fig3():
    seed = pd.read_csv(ANALYSIS / "primary_seed_level.csv")
    sel = json.loads((ANALYSIS / "selection_outcome.json").read_text())
    rows = []
    for h in HORIZONS:
        for fam in ["non_llm", "llm"]:
            mods = NON_LLM if fam == "non_llm" else LLM
            per_seed = (seed[(seed["horizon"] == h) & (seed["model"].isin(mods))]
                        .groupby("seed")["mse_all_7vars_full_horizon_z"].mean())
            m = per_seed.mean(); sd = per_seed.std(ddof=1); n = len(per_seed)
            ci = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
            rows.append({"horizon": h, "family": fam, "mean": m, "ci95_lo": m - ci,
                         "ci95_hi": m + ci, "n_seed_pairs": n})
    df = pd.DataFrame(rows)
    pvals = {str(h): sel["per_horizon_group_compare"][str(h)]["p_value"]
             for h in HORIZONS}
    overall = sel["non_llm_vs_llm_group"]

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    x = np.arange(len(HORIZONS)); w = 0.38
    for fam, dx in [("non_llm", -w / 2), ("llm", w / 2)]:
        sub = df[df["family"] == fam]
        y = sub["mean"].values
        yerr = np.vstack([y - sub["ci95_lo"].values, sub["ci95_hi"].values - y])
        ax.bar(x + dx, y, w, yerr=yerr, color=FAMILY_COLOR[fam],
               label=FAMILY_LABEL[fam], capsize=3, alpha=0.9,
               edgecolor="black", linewidth=0.4,
               error_kw={"elinewidth": 1, "ecolor": "black"})
        for xi, v in zip(x, y):
            ax.text(xi + dx, v + 0.01, f"{v:.3f}", ha="center", fontsize=7.5)
    for xi, h in enumerate(HORIZONS):
        ax.text(xi, 1.335, f"p={pvals[str(h)]:.2g}", ha="center", fontsize=7.5,
                color="#333333")
    ax.set_xticks(x); ax.set_xticklabels([f"L{h}" for h in HORIZONS])
    ax.set_ylabel("family mean MSE  (lower is better)")
    ax.set_title(f"Figure 3. Non-LLM vs LLM family (matched-seed, per horizon)  "
                 f"overall p={overall['p_value']:.2g}")
    ax.set_ylim(top=1.42)
    ax.legend(loc="upper right")
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig3_family_comparison.png"); plt.close(fig)
    save(df, "fig3_family_comparison.csv")


# ---------------------------------------------------------------- fig 4
def fig4():
    b = pd.read_csv(ANALYSIS / "baseline_comparison.csv")
    s = pd.read_csv(ANALYSIS / "primary_summary_statistics.csv")
    def prim(m):
        return s[(s["model"] == m)].sort_values("horizon")["mse_mean"].values
    def base(m):
        return b[(b["model"] == m)].sort_values("horizon")["mse_z"].values
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.plot(HORIZONS, base("seasonal_naive"), "o-", color=MODEL_COLOR["seasonal_naive"],
            lw=2, label="seasonal_naive (baseline)")
    ax.plot(HORIZONS, base("last_value_naive"), "s--", color=MODEL_COLOR["last_value_naive"],
            lw=1.2, label="last_value_naive (baseline)")
    ax.plot(HORIZONS, prim("gpt2_miflu"), "o-", color=MODEL_COLOR["gpt2_miflu"],
            lw=2, label="gpt2_miflu (LLM winner)")
    ax.plot(HORIZONS, prim("nlinear"), "o-", color=MODEL_COLOR["nlinear"],
            lw=2, label="nlinear (Non-LLM winner)")
    ax.set_xticks(HORIZONS)
    ax.set_xlabel("horizon (weeks)")
    ax.set_ylabel("MSE  (7-var full-horizon z-space; lower is better)")
    ax.set_title("Figure 4. seasonal_naive vs gpt2_miflu / nlinear "
                 "(deterministic baseline vs top models)")
    ax.legend(fontsize=8)
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig4_seasonal_vs_top.png"); plt.close(fig)
    combo = pd.concat([
        b[["model", "horizon", "mse_z"]].rename(columns={"mse_z": "mse"}),
        s[s["model"].isin(["gpt2_miflu", "nlinear"])][["model", "horizon", "mse_mean"]]
        .rename(columns={"mse_mean": "mse"})])
    combo["source"] = combo["model"].apply(lambda m: "baseline" if m in
        ("seasonal_naive", "last_value_naive") else "primary")
    save(combo, "fig4_seasonal_vs_top.csv")


# ---------------------------------------------------------------- fig 5
def fig5():
    a = pd.read_csv(ANALYSIS / "ablation_effects.csv").sort_values("delta_vs_parent")
    labels = [x.replace("without_", "no ").replace("_", " ") for x in a["ablation"]]
    colors = ["#c0392b" if p < 0.05 else "#95a5a6" for p in a["p_value_vs_parent"]]
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    bars = ax.barh(labels, a["delta_vs_parent"], color=colors, alpha=0.9,
                   edgecolor="black", linewidth=0.4)
    for bar, p, d, rel in zip(bars, a["p_value_vs_parent"], a["delta_vs_parent"],
                              a["rel_delta_pct"]):
        ax.text(d + 0.002, bar.get_y() + bar.get_height() / 2,
                f"p={p:.3f}  (+{rel:.2f}%)", va="center", fontsize=7.5)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("delta average_MSE_4L vs parent gpt2_miflu  (positive = worse)")
    ax.set_title("Figure 5. Ablation paired effect vs parent (gpt2_miflu), "
                 "N=10 matched seeds")
    handles = [plt.Rectangle((0, 0), 1, 1, color="#c0392b"),
               plt.Rectangle((0, 0), 1, 1, color="#95a5a6")]
    ax.legend(handles, ["significant (p<0.05)", "not significant"], loc="lower right")
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig5_ablation_paired.png"); plt.close(fig)
    save(a, "fig5_ablation_paired.csv")


# ---------------------------------------------------------------- fig 6
def fig6():
    seed = pd.read_csv(ANALYSIS / "primary_seed_level.csv")
    g = (seed.groupby(["model", "seed"])["mse_all_7vars_full_horizon_z"]
         .mean().reset_index().rename(columns={"mse_all_7vars_full_horizon_z": "avg_MSE_4L"}))
    order = g.groupby("model")["avg_MSE_4L"].median().sort_values().index.tolist()
    data = [g.loc[g["model"] == m, "avg_MSE_4L"].values for m in order]
    fams = [family_of(m) for m in order]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bp = ax.boxplot(data, tick_labels=order, patch_artist=True, showfliers=False)
    for patch, m in zip(bp["boxes"], order):
        patch.set_facecolor(MODEL_COLOR[m]); patch.set_alpha(0.55)
        patch.set_edgecolor("black")
    rng = np.random.default_rng(0)
    for i, (m, vals) in enumerate(zip(order, data)):
        jx = rng.normal(0, 0.06, size=len(vals))
        ax.scatter(i + 1 + jx, vals, s=20, color=MODEL_COLOR[m], alpha=0.9,
                   edgecolor="black", linewidth=0.4, zorder=3)
    ax.set_ylabel("average_MSE_4L per seed  (10 seeds; lower is better)")
    ax.set_title("Figure 6. Seed-level stability of average_MSE_4L "
                 "(box = 10 frozen seeds, dots = individual seeds)")
    ax.set_xticklabels(order, rotation=30, ha="right")
    ax.legend(mod_handles(order), order, loc="upper left", ncol=2)
    stamp(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig6_seed_stability.png"); plt.close(fig)
    save(g, "fig6_seed_stability.csv")


# ---------------------------------------------------------------- fig 7
def fig7():
    res = pd.read_csv(ANALYSIS / "resource_storage.csv")
    rank = pd.read_csv(ANALYSIS / "model_ranking.csv")[["model", "average_MSE_4L"]]
    d = res.merge(rank, on="model", how="left")
    d = d[d["model"].isin(NON_LLM + LLM)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.0))
    for ax, col, xlab, t in [
        (axes[0], "train_seconds_mean", "training time (s, log scale)", "runtime"),
        (axes[1], "compact_bytes", "compact storage (bytes, log scale)", "storage")]:
        for _, row in d.iterrows():
            ax.scatter(row[col], row["average_MSE_4L"], color=MODEL_COLOR[row["model"]],
                       s=70, alpha=0.9, edgecolor="black", linewidth=0.4)
            ax.annotate(row["model"], (row[col], row["average_MSE_4L"]),
                        fontsize=7.5, xytext=(5, 4), textcoords="offset points")
        ax.set_xscale("log")
        ax.set_xlabel(xlab)
        ax.set_ylabel("average_MSE_4L  (lower is better)" if ax is axes[0] else "")
        ax.set_title(f"(a) accuracy vs {t}" if ax is axes[0] else f"(b) accuracy vs {t}")
        ax.grid(True, linestyle="--", alpha=0.35)
    fig.suptitle("Figure 7. Accuracy vs runtime / storage (8 architectures)",
                 fontsize=11)
    handles = fam_handles()
    fig.legend(handles, [FAMILY_LABEL[k] for k in FAMILY_COLOR], loc="lower center",
               ncol=3, bbox_to_anchor=(0.5, -0.02))
    stamp(axes[1])
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(FIG / "fig7_accuracy_vs_resource.png"); plt.close(fig)
    save(d[["model", "family", "train_seconds_mean", "trainable_parameters",
            "compact_bytes", "average_MSE_4L"]], "fig7_accuracy_vs_resource.csv")


# ---------------------------------------------------------------- fig 8
def fig8():
    proto = json.loads((ANALYSIS / "frozen_analysis_protocol.json").read_text())
    cs = proto["wave1_completion_status"]
    br = cs["breakdown"]
    # Taller canvas + generous vertical spacing so no box overlaps another and
    # arrows never cross text. ledger FAIL box sits in its own row below the
    # primary ranking (not on top of it).
    fig, ax = plt.subplots(figsize=(10.2, 7.8))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    def box(x, y, w, h, txt, fc="#eaf2f8", fs=8.5, tc="#111111", bold=False):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                           fc=fc, ec="#444444", lw=1)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#444444", lw=1.2))

    # Row 1: accepted rows
    box(28, 90, 44, 8, f"Wave-1 accepted rows: {cs['accepted']}",
        fc="#fef3d9", fs=10, bold=True)
    # Row 2: four arms
    box(2, 72, 21, 10, f"primary\n8 x 4 horizons\nx 10 seeds = {br['primary_8x4x10']}")
    box(26, 72, 21, 10, f"baselines\n2 x 4 horizons\n= {br['baselines_2x4']}")
    box(50, 72, 21, 10, f"ablations\n6 x 4 x 10\n= {br['ablations_6x4x10']}")
    box(74, 72, 24, 10, f"negative controls\nzero/shuffled text\n= {br['negative_control_fixed_parent']}")
    for x in (12.5, 36.5, 60.5, 86):
        arrow(50, 90, x, 82)
    # Row 3: frozen selection rule
    box(18, 52, 64, 12,
        "Frozen selection rule\nrank by average_MSE_4L (7-var, full-horizon, z-space; lower is better)",
        fc="#e8f5e9")
    arrow(50, 72, 50, 64)
    # Row 4: primary ranking
    box(18, 34, 64, 12,
        "Primary ranking (320 rows only)\nbest: gpt2_miflu   |   best non-LLM: nlinear",
        fc="#e8f5e9")
    arrow(50, 52, 50, 46)
    # Row 5: ledger integrity check (own row, no overlap)
    box(34, 18, 32, 9, "ledger FAIL = 0", fc="#ffffff", fs=8.5)
    arrow(50, 34, 50, 27)
    # Row 6: deferred controls + test/holdout access (bottom, no overlap)
    box(2, 2, 30, 11, f"Deferred controls\npending Wave-2: {cs['deferred_controls_pending']}",
        fc="#fdecea")
    box(66, 2, 32, 11,
        f"Test access: {cs['test_access']}  /\nHoldout access: {cs['holdout_access']}  (sealed)",
        fc="#fdecea")
    arrow(36, 8, 66, 8)
    ax.set_title("Figure 8. Wave-1 workflow and evidence-integrity (validation-only)",
                 fontsize=11)
    stamp(ax, y=0.975)
    fig.tight_layout(); fig.savefig(FIG / "fig8_workflow_evidence.png"); plt.close(fig)
    wf = pd.DataFrame([{"accepted": cs["accepted"],
                        "primary": br["primary_8x4x10"], "baselines": br["baselines_2x4"],
                        "ablations": br["ablations_6x4x10"],
                        "negative_control": br["negative_control_fixed_parent"],
                        "deferred_controls_pending": cs["deferred_controls_pending"],
                        "ledger_fail_events": cs["ledger_fail_events"],
                        "test_access": cs["test_access"],
                        "holdout_access": cs["holdout_access"]}])
    save(wf, "fig8_workflow_evidence.csv")


def main():
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8()
    print("wrote 8 figures + source CSVs to", FIG)


if __name__ == "__main__":
    main()
