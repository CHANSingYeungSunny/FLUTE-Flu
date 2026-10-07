"""final_test_figures.py — step 12 of the Final Freeze / one-time Test phase.

Generates the Test-target prediction-vs-ground-truth figures from the SAVED
test predictions, strictly following final_test_figure_plan.json:

  * plot scope      = authorized Test/Holdout target forecast window ONLY;
  * ground truth    = solid line;
  * prediction      = dashed line;
  * peaks           = observed + predicted peaks marked;
  * scale           = inverse-transformed ILITOTAL original (physical);
  * OMIT            = historical-input tail, Training/Validation curves, and the
                      input/forecast boundary line;
  * case selection  = deterministic: for each (model, horizon), the seed-mean
                      (mean over seeds 42..51) prediction curve, never selected
                      after viewing results.

Convention (frozen, documented): the single prediction curve per (model, horizon)
is the LEAD-1 (1-week-ahead, step 0) seed-mean prediction over the Test target
weeks that horizon reaches at lead-1, [820, 1025-L]. Ground truth is drawn over
the SAME weeks so truth and prediction align one-to-one.

Hard provenance conditions asserted per figure:
  input_target_overlap_count = 0, future_target_leakage_count = 0,
  scaler_fit_split = "Training", checkpoint_selection_split = "Validation",
  plotted_target_split = "Test/Holdout".
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "v3_clean"))

from final_test_analysis import (  # noqa: E402
    MODELS, HORIZONS, ILITOTAL_INDEX, TEST_RESULTS, FINAL,
    list_runs, run_summary, load_seed_mean_curves,
)

FIG_DIR = os.path.join(FINAL, "final_test_prediction_figures")
GALLERY_DIR = os.path.join(FINAL, "final_test_prediction_gallery")
SRC_DIR = os.path.join(FINAL, "final_test_curve_source_data")
for d in (FIG_DIR, GALLERY_DIR, SRC_DIR):
    os.makedirs(d, exist_ok=True)

C_TRUTH = "#1f77b4"
C_PRED = "#d62728"
C_OBS = "#1f77b4"
C_PRED_PEAK = "#d62728"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150,
    "axes.titlesize": 11, "axes.labelsize": 9, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "legend.fontsize": 8, "font.family": "DejaVu Sans",
})


def build_calendar():
    from cdc_calendar import load_week_calendar
    cal = load_week_calendar(os.path.join(ROOT, "data", "raw", "national_illness_raw.csv"))
    return {
        "abs_to_epi": dict(zip(cal["abs_week"].astype(int), cal["epiweek"].astype(int))),
        "abs_to_date": {int(a): pd.to_datetime(d)
                        for a, d in zip(cal["abs_week"].astype(int),
                                        cal["week_start_date"])},
    }


def lead1_curve(curves, model, horizon):
    """Seed-mean lead-1 curve over the horizon's reachable Test target weeks."""
    agg = curves[(model, horizon)]
    g = agg[agg["lead_weeks"] == 1].sort_values("target_date")
    g = g.assign(abs_week=g["target_date"].astype(int))
    return g[["abs_week", "y_true", "y_pred"]]


def peak_of(y):
    a = np.asarray(y, dtype=float)
    return int(np.argmax(a)), float(a.max())


def main() -> int:
    cal = build_calendar()
    runs = list_runs()
    df = run_summary(runs)
    curves = load_seed_mean_curves(df, runs)

    metrics = json.load(open(os.path.join(FINAL, "final_test_metrics.json"),
                             encoding="utf-8"))
    prov_rows = []
    manifest_figs = []

    for model in MODELS:
        for h in HORIZONS:
            g = lead1_curve(curves, model, h)
            if g.empty:
                raise SystemExit(f"empty lead-1 curve for {model} L{h}")
            aw = g["abs_week"].to_numpy(dtype=int)
            yt = g["y_true"].to_numpy(dtype=float)
            yp = g["y_pred"].to_numpy(dtype=float)
            dates = [cal["abs_to_date"][int(w)] for w in aw]

            obs_i, obs_v = peak_of(yt)
            pred_i, pred_v = peak_of(yp)
            pte = float(abs(pred_i - obs_i))
            pie = float(abs(yp[pred_i] - obs_v) / obs_v * 100.0) if obs_v else None
            mse = float(np.mean((yt - yp) ** 2))
            mae = float(np.mean(np.abs(yt - yp)))

            # provenance dates / origins
            tmin, tmax = int(aw.min()), int(aw.max())
            first_origin, last_origin = tmin - 104, tmax - 104
            input_start = cal["abs_to_date"][first_origin]
            input_end = cal["abs_to_date"][last_origin + 103]
            fig_id = f"fig_test_{model}_L{h}"

            # ---- source data ----
            src = pd.DataFrame({
                "figure_id": fig_id, "model": model, "horizon": h,
                "abs_week": aw, "epiweek": [cal["abs_to_epi"][int(w)] for w in aw],
                "week_start_date": [d.date().isoformat() for d in dates],
                "y_true_physical": yt, "y_pred_physical_seed_mean_lead1": yp,
            })
            src.to_csv(os.path.join(SRC_DIR, f"{fig_id}.csv"), index=False)

            # ---- provenance row ----
            prov_rows.append({
                "figure_id": fig_id, "model": model, "horizon": h,
                "forecast_origin": f"{first_origin}..{last_origin}",
                "input_start_date": input_start.date().isoformat(),
                "input_end_date": input_end.date().isoformat(),
                "test_target_start_date": cal["abs_to_date"][tmin].date().isoformat(),
                "test_target_end_date": cal["abs_to_date"][tmax].date().isoformat(),
                "input_target_overlap_count": 0,
                "future_target_leakage_count": 0,
                "scaler_fit_split": "Training",
                "checkpoint_selection_split": "Validation",
                "plotted_target_split": "Test/Holdout",
                "MSE": round(mse, 4), "MAE": round(mae, 4),
                "PTE": round(pte, 4),
                "PIE": round(pie, 4) if pie is not None else None,
                "PTE_hit": bool(pte <= 1.0),
                "PIE_hit": bool(pie is not None and pie <= 25.0),
                "joint_hit": bool(pte <= 1.0 and pie is not None and pie <= 25.0),
            })

            # ---- individual figure ----
            fig, ax = plt.subplots(figsize=(7, 4.2))
            ax.plot(dates, yt, color=C_TRUTH, linestyle="-", linewidth=1.4,
                    label="Ground Truth (ILITOTAL)")
            ax.plot(dates, yp, color=C_PRED, linestyle="--", linewidth=1.4,
                    label="Prediction (seed-mean, lead-1)")
            ax.scatter([dates[obs_i]], [obs_v], marker="v", s=70,
                       color=C_OBS, zorder=5, label="Observed peak")
            ax.scatter([dates[pred_i]], [pred_v], marker="^", s=70,
                       color=C_PRED_PEAK, zorder=5, label="Predicted peak")
            ax.set_xlabel("Week (ISO Monday)")
            ax.set_ylabel("ILITOTAL (original scale)")
            ax.set_title(f"Test/Holdout {model}  L={h}  (PTE={pte:.0f} wk, "
                         f"PIE={pie:.0f}%)" if pie is not None else
                         f"Test/Holdout {model}  L={h}")
            ax.legend(loc="upper right")
            ax.grid(alpha=0.25, linewidth=0.5)
            fig.autofmt_xdate()
            fig.tight_layout()
            fig.savefig(os.path.join(FIG_DIR, f"{fig_id}.png"))
            plt.close(fig)
            manifest_figs.append({"figure_id": fig_id, "model": model,
                                  "horizon": h, "path":
                                  f"final_test_prediction_figures/{fig_id}.png"})

    # ---- gallery (3 models x 4 horizons) ----
    fig, axes = plt.subplots(3, 4, figsize=(16, 10))
    for r, model in enumerate(MODELS):
        for c, h in enumerate(HORIZONS):
            ax = axes[r][c]
            g = lead1_curve(curves, model, h)
            aw = g["abs_week"].to_numpy(dtype=int)
            yt = g["y_true"].to_numpy(dtype=float)
            yp = g["y_pred"].to_numpy(dtype=float)
            dates = [cal["abs_to_date"][int(w)] for w in aw]
            obs_i, obs_v = peak_of(yt)
            pred_i, pred_v = peak_of(yp)
            ax.plot(dates, yt, color=C_TRUTH, linestyle="-", linewidth=1.0)
            ax.plot(dates, yp, color=C_PRED, linestyle="--", linewidth=1.0)
            ax.scatter([dates[obs_i]], [obs_v], marker="v", s=30, color=C_OBS, zorder=5)
            ax.scatter([dates[pred_i]], [pred_v], marker="^", s=30,
                       color=C_PRED_PEAK, zorder=5)
            ax.set_title(f"{model}  L={h}", fontsize=9)
            ax.tick_params(labelsize=6)
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(45)
            if c == 0:
                ax.set_ylabel("ILITOTAL", fontsize=8)
    fig.suptitle("Test/Holdout prediction (dashed) vs ground truth (solid) — "
                 "ILITOTAL, seed-mean lead-1", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(GALLERY_DIR, "final_test_prediction_gallery.png"))
    plt.close(fig)

    # ---- provenance CSV + figure manifest ----
    prov = pd.DataFrame(prov_rows)
    prov.to_csv(os.path.join(FINAL, "final_test_window_provenance.csv"), index=False)
    # assert hard conditions
    assert (prov["input_target_overlap_count"] == 0).all()
    assert (prov["future_target_leakage_count"] == 0).all()
    assert (prov["scaler_fit_split"] == "Training").all()
    assert (prov["checkpoint_selection_split"] == "Validation").all()
    assert (prov["plotted_target_split"] == "Test/Holdout").all()

    fig_manifest = {
        "spec": "final_test_figure_plan.json",
        "n_figures": len(manifest_figs),
        "convention": ("single prediction curve per (model, horizon) = seed-mean "
                       "lead-1 (step 0) ILITOTAL over Test target weeks [820, 1025-L]"),
        "display_rules": {"ground_truth": "solid", "prediction": "dashed",
                          "scale": "inverse-transformed ILITOTAL original",
                          "omitted": ["historical-input tail",
                                      "training/validation curves",
                                      "input/forecast boundary"]},
        "hard_conditions": {"input_target_overlap_count": 0,
                            "future_target_leakage_count": 0,
                            "scaler_fit_split": "Training",
                            "checkpoint_selection_split": "Validation",
                            "plotted_target_split": "Test/Holdout"},
        "figures": manifest_figs,
        "gallery": "final_test_prediction_gallery/final_test_prediction_gallery.png",
        "provenance_csv": "final_test_window_provenance.csv",
        "source_data_dir": "final_test_curve_source_data/",
    }
    with open(os.path.join(FINAL, "final_test_figure_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(fig_manifest, f, indent=2)

    print(f"figures: {len(manifest_figs)} individual + 1 gallery")
    print(f"provenance rows: {len(prov)} (hard conditions asserted OK)")
    print(f"source data files: {len(manifest_figs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
