"""Wave-1 revision figures: prediction curves (inverse-transformed ILITOTAL),
peak timing/intensity (PTE/PIE), and IPO evaluation workflow.

Reads authoritative CSVs + extracted ILITOTAL predictions. Outputs to
results/v3_clean/analysis/figures/.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
FIG = ANALYSIS / "figures"
DATA = FIG / "data"
FIG.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "scripts"))
from cdc_calendar import load_week_calendar  # noqa: E402

MODEL_COLOR = {
    "nlinear": "#08519c", "dlinear": "#2c7fb8", "patchtst": "#6baed6",
    "itransformer": "#a6bddb", "gpt2_miflu": "#a50f15", "qwen_time_llm": "#d95f0e",
    "calf_llm": "#f16913", "timecma_llm": "#fdae6b",
    "seasonal_naive": "#252525", "last_value_naive": "#969696",
}
NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]

T = 104
REPR_ORIGIN = 715

RAW = pd.read_csv(ROOT / "data/raw/national_illness_raw.csv")
ILI = RAW["ILITOTAL"].to_numpy(np.float64)

_cal = load_week_calendar(str(ROOT / "data/raw/national_illness_raw.csv"))
CAL = {int(r.abs_week): (int(r.epiweek), str(r.week_start_date)[:10])
       for r in _cal.itertuples()}

EXTRACT = pd.read_csv(ROOT / "_tmp_audit/ili_ilitotal_extract.csv.gz",
                      compression="gzip")
EXTRACT["abs_week"] = EXTRACT.forecast_origin + T + EXTRACT.step

METRICS = pd.read_csv(ANALYSIS / "analysis_dataset.csv")


def run_parts(rk):
    p = rk.split("__")
    return p[0], "__".join(p[1:-2]), int(p[-2][1:]), p[-1][4:]


def curve_data(run_key, origin=REPR_ORIGIN):
    """Return (pred_aw, pred_y, gt_y, L) for one origin's forecast window."""
    e = EXTRACT[EXTRACT.run_key == run_key]
    e = e[e.forecast_origin == origin].sort_values("step")
    L = int(e.step.max()) + 1
    pred_aw = origin + T + e.step.to_numpy()  # abs_week of forecast window
    pred_y = e.y_pred_physical.to_numpy(np.float64)
    gt_y = ILI[pred_aw]  # raw observed (== y_true_physical)
    return pred_aw, pred_y, gt_y, L


def mse_mae(gt, pred):
    mse = float(np.mean((gt - pred) ** 2))
    mae = float(np.mean(np.abs(gt - pred)))
    return mse, mae


def plot_one_curve(ax, run_key, origin=REPR_ORIGIN):
    pred_aw, pred_y, gt_y, L = curve_data(run_key, origin)
    mse, mae = mse_mae(gt_y, pred_y)
    arm, model, horizon, seed = run_parts(run_key)
    color = MODEL_COLOR.get(model, "#444444")

    ax.plot(pred_aw, gt_y, "-", color="#111111", lw=1.8, label="ground truth")
    ax.plot(pred_aw, pred_y, "--", color=color, lw=1.8, label="prediction")

    # peaks
    obs_peak_aw = pred_aw[int(np.argmax(gt_y))]
    pred_peak_aw = pred_aw[int(np.argmax(pred_y))]
    ax.scatter([obs_peak_aw], [gt_y.max()], marker="*", s=130, color="#111111",
               zorder=5, label="true peak")
    ax.scatter([pred_peak_aw], [pred_y.max()], marker="v", s=70, color=color,
               zorder=5, label="pred peak")

    # x ticks: a few dates across the forecast window only
    tick_aw = np.linspace(pred_aw.min(), pred_aw.max(), 7).astype(int)
    ax.set_xticks(tick_aw)
    ax.set_xticklabels([CAL.get(int(a), ("", ""))[1][5:] for a in tick_aw],
                       rotation=30, ha="right", fontsize=7)
    ax.set_ylabel("ILITOTAL", fontsize=8)
    ax.set_title(f"{model}  L{horizon}  seed={seed}\n"
                 f"MSE={mse:.0f}  MAE={mae:.0f}  (physical ILITOTAL)",
                 fontsize=8.5)
    ax.grid(True, linestyle="--", alpha=0.25)
    return dict(model=model, horizon=horizon, seed=seed, mse=mse, mae=mae,
                obs_peak_aw=int(obs_peak_aw), pred_peak_aw=int(pred_peak_aw))


def median_seed(model, horizon):
    sub = METRICS[(METRICS.model == model) & (METRICS.horizon == horizon)]
    sub = sub.sort_values("ilitotal_full_mse_phys")
    seeds = sub.seed.tolist()
    return seeds[len(seeds) // 2]


def best_worst_seed(model, horizon):
    sub = METRICS[(METRICS.model == model) & (METRICS.horizon == horizon)]
    sub = sub.sort_values("ilitotal_full_mse_phys")
    return sub.seed.iloc[0], sub.seed.iloc[-1]


def make_curve_panels():
    """fig9 = L24 panel, fig10 = L60 panel, fig11 = seed effect."""
    panels = {
        "fig9_prediction_curves_L24": (24, [
            ("gpt2_miflu", "llm"), ("nlinear", "non_llm"),
            ("seasonal_naive", "baseline"), ("calf_llm", "llm"),
        ]),
        "fig10_prediction_curves_L60": (60, [
            ("gpt2_miflu", "llm"), ("nlinear", "non_llm"),
            ("seasonal_naive", "baseline"), ("calf_llm", "llm"),
        ]),
    }
    for name, (horizon, models) in panels.items():
        fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.5))
        for ax, (model, fam) in zip(axes.ravel(), models):
            if model == "seasonal_naive":
                seed = "na"
            else:
                seed = median_seed(model, horizon)
            rk = f"primary__{model}__L{horizon}__seed{seed}" if model not in (
                "seasonal_naive", "last_value_naive") else \
                f"baseline__{model}__L{horizon}__seedna"
            plot_one_curve(ax, rk)
        axes[0, 0].legend(fontsize=7, loc="upper left")
        fig.suptitle(f"{name.replace('_', ' ')}  (median seed, "
                     f"validation forecast origin={REPR_ORIGIN}, ILITOTAL physical scale)",
                     fontsize=11)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(FIG / f"{name}.png"); plt.close(fig)
        print("wrote", name)

    # fig11: seed effect for gpt2_miflu L24
    fig, ax = plt.subplots(figsize=(9, 5.2))
    b, w = best_worst_seed("gpt2_miflu", 24)
    m = median_seed("gpt2_miflu", 24)
    for seed, style, lab in [(b, "-", f"best seed={b}"), (m, "--", f"median seed={m}"),
                             (w, ":", f"worst seed={w}")]:
        rk = f"primary__gpt2_miflu__L24__seed{seed}"
        pred_aw, pred_y, gt_y, L = curve_data(rk)
        ax.plot(pred_aw, pred_y, style, color="#a50f15", lw=1.6,
                label=lab + " (pred)")
    ax.plot(pred_aw, gt_y, "-", color="#111111", lw=2, label="ground truth")
    tick_aw = np.linspace(pred_aw.min(), pred_aw.max(), 7).astype(int)
    ax.set_xticks(tick_aw)
    ax.set_xticklabels([CAL.get(int(a), ("", ""))[1][5:] for a in tick_aw],
                       rotation=30, ha="right")
    ax.set_ylabel("ILITOTAL"); ax.set_title(
        "Figure 11. Seed sensitivity of gpt2_miflu L24 forecasts (best/median/worst seed)")
    ax.legend(fontsize=8); ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig11_seed_sensitivity.png"); plt.close(fig)
    print("wrote fig11_seed_sensitivity")


def make_peak_figure():
    """fig12: PTE/PIE peak timing & intensity scatter."""
    long = pd.read_csv(ANALYSIS / "pte_pie_long.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    # timing: predicted peak week vs observed peak week
    ax = axes[0]
    for model in NON_LLM + LLM:
        sub = long[long.model == model]
        ax.scatter(sub.obs_peak_abs_week, sub.pred_peak_abs_week, s=16,
                   color=MODEL_COLOR[model], alpha=0.55, label=model)
    lo = min(long.obs_peak_abs_week.min(), long.pred_peak_abs_week.min())
    hi = max(long.obs_peak_abs_week.max(), long.pred_peak_abs_week.max())
    ax.plot([lo, hi], [lo, hi], "k--", lw=1)
    ax.set_xlabel("observed peak (abs week)"); ax.set_ylabel("predicted peak (abs week)")
    ax.set_title("(a) peak timing")
    # intensity
    ax = axes[1]
    for model in NON_LLM + LLM:
        sub = long[long.model == model]
        ax.scatter(sub.obs_peak_intensity, sub.pred_peak_intensity, s=16,
                   color=MODEL_COLOR[model], alpha=0.55, label=model)
    lo = min(long.obs_peak_intensity.min(), long.pred_peak_intensity.min())
    hi = max(long.obs_peak_intensity.max(), long.pred_peak_intensity.max())
    ax.plot([lo, hi], [lo, hi], "k--", lw=1)
    ax.set_xlabel("observed peak intensity"); ax.set_ylabel("predicted peak intensity")
    ax.set_title("(b) peak intensity (ILITOTAL)")
    fig.suptitle("Figure 12. Peak timing / intensity (secondary application metric, "
                 "580 runs x 4 leads x 2 seasons 2016-17 & 2017-18, physical ILITOTAL)",
                 fontsize=11)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=8,
               bbox_to_anchor=(0.5, -0.06), fontsize=7)
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(FIG / "fig12_peak_timing_intensity.png"); plt.close(fig)
    print("wrote fig12_peak_timing_intensity")


def make_ipo_figure():
    """fig13: IPO evaluation workflow (zero-baseline explainer)."""
    fig, ax = plt.subplots(figsize=(11, 7.0))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    def box(x, y, w, h, txt, fc="#eaf2f8", fs=8.5, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5",
                                    fc=fc, ec="#444444", lw=1))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#444444", lw=1.3))

    # Input
    box(2, 74, 30, 20,
        "INPUT\n7 historical variables\n(L=104-week window)\n\n% WEIGHTED ILI\n"
        "% UNWEIGHTED ILI\nAGE 0-4 / AGE 5-24\nILITOTAL\nNUM. PROVIDERS / OT",
        fc="#e3f2fd")
    # Process
    box(38, 74, 26, 20,
        "PROCESS\n1) standardise with\ntrain-only scaler\n2) model inference\n"
        "3) inverse-transform\nback to physical scale", fc="#fff3e0")
    # Output
    box(70, 74, 28, 20,
        "OUTPUT\nfuture horizon x 7 vars\nL = 24 / 36 / 48 / 60 weeks\n"
        "(e.g. L24 -> 24 weeks\nx 7 variables)", fc="#e8f5e9")
    arrow(32, 84, 38, 84)
    arrow(64, 84, 70, 84)

    # Ground truth / error
    box(38, 42, 26, 20,
        "GROUND TRUTH\nobserved ILITOTAL (raw)\nfor the same weeks\n(never seen in training)",
        fc="#f3e5f5")
    arrow(84, 74, 84, 62); arrow(84, 62, 64, 52)  # output -> truth comparison

    box(2, 42, 30, 20,
        "PER-PREDICTION ERROR\n|y_pred - y_true|\nMSE = mean((y_pred-y_true)^2)\n"
        "MAE = mean(|y_pred-y_true|)\n(lower is better)", fc="#fdecea")
    arrow(32, 52, 38, 52)

    box(70, 42, 28, 20,
        "AGGREGATE\noverall metric = all 7 vars\nILITOTAL metric = ILITOTAL only\n"
        "10 frozen seeds -> mean\n4 horizons -> average_MSE_4L", fc="#e8f5e9")
    arrow(51, 52, 70, 52)

    box(20, 8, 60, 20,
        "MSE is NOT an accuracy percentage.\nIt is a squared-error cost in z-space "
        "(or physical units); smaller = better,\nbut it has no %-accuracy meaning.",
        fc="#fef9e7", fs=9, bold=True)
    arrow(50, 42, 50, 28)

    ax.set_title("Figure 13. How model performance is evaluated (Input -> Process -> Output)",
                 fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "fig13_evaluation_workflow.png"); plt.close(fig)
    print("wrote fig13_evaluation_workflow")


def main():
    make_curve_panels()
    make_peak_figure()
    make_ipo_figure()
    print("done")


if __name__ == "__main__":
    main()
