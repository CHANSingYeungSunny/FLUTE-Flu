"""
figures.py — the four mandatory per-run figures.
================================================

Every run produces, inside its own `figures/` directory:
  * loss_curve.png            train/val loss per epoch (from train_history.csv)
  * forecast_continuous.png   gt vs pred over the scored calendar window
  * peak_timing_intensity.png predicted vs true peak week / intensity per season
  * residual_diagnostics.png  residual vs time + residual histogram

All figures use the non-interactive Agg backend (headless-safe).
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def loss_curve(history: pd.DataFrame, path: str) -> str:
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(history["epoch"], history["train_loss"], marker="o", label="train")
    if "val_mse" in history.columns:
        ax.plot(history["epoch"], history["val_mse"], marker="s", label="val MSE")
    if "best_epoch" in history.columns and history["best_epoch"].notna().any():
        be = int(history["best_epoch"].dropna().iloc[-1])
        ax.axvline(be, color="green", ls="--", lw=1, label=f"best ep {be}")
    ax.set_xlabel("epoch")
    ax.set_ylabel("MSE (z-space)")
    ax.set_title("Loss curve")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    return _save(fig, path)


def forecast_continuous(series: pd.DataFrame, path: str,
                        split_label: str = "validation") -> str:
    if "week_start_date" not in series.columns:
        raise KeyError("forecast_continuous needs `week_start_date`")
    x = pd.to_datetime(series["week_start_date"])
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.plot(x, series["gt"], color="black", lw=1.6, label="ground truth")
    ax.plot(x, series["pred"], color="tab:red", lw=1.3, ls="--", label="prediction")
    ax.set_xlabel("date")
    ax.set_ylabel("ILITOTAL (patients)")
    ax.set_title(f"Continuous forecast ({split_label}, fixed step=0)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    return _save(fig, path)


def peak_timing_intensity(by_season: pd.DataFrame, path: str) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    d = by_season[by_season["status"] == "evaluable"] if len(by_season) else by_season
    if len(d):
        ax = axes[0]
        ax.plot(d["season"], d["gt_peak_week"], "o-", label="true peak week")
        ax.plot(d["season"], d["pred_peak_week"], "s--", label="pred peak week")
        ax.set_xlabel("season")
        ax.set_ylabel("abs_week of peak")
        ax.set_title("Peak timing")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)

        ax = axes[1]
        ax.plot(d["season"], d["gt_peak_value"], "o-", label="true peak")
        ax.plot(d["season"], d["pred_peak_value"], "s--", label="pred peak")
        ax.set_xlabel("season")
        ax.set_ylabel("peak ILITOTAL")
        ax.set_title("Peak intensity")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    else:
        for ax in axes:
            ax.text(0.5, 0.5, "no evaluable season", ha="center", va="center")
            ax.axis("off")
    return _save(fig, path)


def residual_diagnostics(series: pd.DataFrame, path: str) -> str:
    resid = series["gt"].to_numpy(float) - series["pred"].to_numpy(float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    x = pd.to_datetime(series["week_start_date"]) if "week_start_date" in series.columns \
        else np.arange(len(resid))
    axes[0].plot(x, resid, color="tab:blue", lw=1.2)
    axes[0].axhline(0.0, color="black", lw=0.8, ls="--")
    axes[0].set_title("Residual vs time")
    axes[0].set_ylabel("gt - pred (patients)")
    axes[0].grid(alpha=0.25)
    axes[1].hist(resid, bins=20, color="tab:blue", alpha=0.8)
    axes[1].axvline(0.0, color="black", lw=0.8, ls="--")
    axes[1].set_title("Residual distribution")
    axes[1].set_xlabel("gt - pred (patients)")
    axes[1].grid(alpha=0.25)
    return _save(fig, path)


if __name__ == "__main__":  # pragma: no cover
    print("[figures] module OK (Agg backend)")
