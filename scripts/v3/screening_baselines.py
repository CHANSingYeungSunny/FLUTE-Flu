"""screening_baselines.py — the two preregistered deterministic baselines.

Runs ON A COMPUTE NODE inside the v3.5 deployment root. Uses the SAME dataset,
split, scaler, window construction, horizons, variable order, fixed-step
definitions and metric code as the formal Screening runs, so the baselines are
directly comparable and can serve as the frozen `last_value_naive` denominator.

  last_value_naive  : persistence — repeat the last observed input value over
                      the whole horizon (per variable).
  seasonal_naive    : the value 52 weeks (one season) before each target week.

These are DETERMINISTIC. They are computed ONCE per unique horizon and mapped
transparently to the matching seed cells with `stochastic_seed_applicable=false`.
They are NOT part of the eight primary architectures and never enter the 4-vs-4
count. Validation only — the test split is never read.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.environ.get("INNOVATION_DEPLOYMENT_ROOT", "."))
if os.path.join(_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from innovation import metrics as MET          # noqa: E402
from innovation import screening_artifacts as SCR  # noqa: E402
from innovation.data_pipeline import (build_windows, load_raw_df,  # noqa: E402
                                      load_scaler, normalize, to_array)
from innovation.paths import ILI_CHANNEL, SCALER_JSON  # noqa: E402

OUT_DIR = os.environ.get("BASELINE_OUT",
                         "/home/sychan552/innovation_durable/screening/baselines")
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
SEASONAL_LAG = 52
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def build_predictions(name: str, horizon: int):
    """Return a long-format prediction frame in the frozen Screening schema."""
    raw = load_raw_df()
    scaler = load_scaler()
    data = normalize(to_array(raw), scaler)
    w = build_windows(data, horizon)
    X = np.asarray(w["X_val"])          # (n_val, T, N)
    Y = np.asarray(w["Y_val"])          # (n_val, L, N)
    idx = list(w["idx_val"])            # absolute end-of-input week index
    # Window arrays are CHANNELS-FIRST in this codebase: (n_val, N, T) / (n_val, N, L).
    n_val, N, T = X.shape
    L = Y.shape[2]
    _sc = scaler.to_dict() if hasattr(scaler, "to_dict") else {}
    mean_v = np.asarray(_sc.get("mean", [0.0] * N), dtype=float)
    std_v = np.asarray(_sc.get("std", [1.0] * N), dtype=float)

    pred = np.empty_like(Y)
    for i in range(n_val):
        if name == "last_value_naive":
            pred[i] = np.repeat(X[i, :, -1:], L, axis=1)
        elif name == "seasonal_naive":
            for k in range(L):
                # lag-52 reference week for target lead (k+1)
                src = (T - 1) + (k + 1) - SEASONAL_LAG
                # Leads beyond the 104-week input window have no in-window
                # seasonal reference; clamp to the window edge and record it
                # (provenance: seasonal_reference_clamped). Steps 0-3, the
                # reported fixed-step endpoints, are always unclamped.
                src = min(max(src, 0), T - 1)
                pred[i, :, k] = X[i, :, src]
        else:
            raise SystemExit(f"unknown baseline {name}")

    rows = []
    for i in range(n_val):
        end_abs = int(idx[i])
        for k in range(L):
            target_abs = end_abs + k + 1
            epi = int(raw["epiweek"].iloc[target_abs]) \
                if "epiweek" in raw.columns and target_abs < len(raw) else None
            tdate = None
            if "week_start_date" in raw.columns and target_abs < len(raw):
                tdate = str(pd.to_datetime(
                    raw["week_start_date"].iloc[target_abs]).date())
            for j in range(N):
                rows.append({
                    "model_key": name, "horizon": horizon, "seed": SEEDS[0],
                    "split": "val", "step": k, "abs_week": target_abs,
                    "epiweek": epi, "week_start_date": tdate,
                    "variable": f"var{j}",
                    "y_true": float(Y[i, j, k]), "y_pred": float(pred[i, j, k]),
                    "y_true_phys": float(Y[i, j, k] * std_v[j] + mean_v[j]),
                    "y_pred_phys": float(pred[i, j, k] * std_v[j] + mean_v[j]),
                    "var_index": j,
                })
    df = pd.DataFrame(rows)

    # ILITOTAL-only long frame in the exact Screening prediction contract
    ili = df[df["var_index"] == ILI_CHANNEL].copy()
    ili = ili.rename(columns={"y_true": "ground_truth_ili",
                              "y_pred": "prediction_ili",
                              "y_true_phys": "ground_truth_ili_phys",
                              "y_pred_phys": "prediction_ili_phys"})
    ili["lead_weeks"] = ili["step"].astype(int) + 1
    ili["target_date"] = ili["week_start_date"]
    ili["variable"] = "ILITOTAL"
    ili = SCR.add_prediction_keys(ili, model_key=name, horizon=horizon,
                                 seed=SEEDS[0])
    keep = ["model_key", "horizon", "seed", "split", "step", "lead_weeks",
            "target_date", "variable", "abs_week", "epiweek",
            "ground_truth_ili", "prediction_ili", "ground_truth_ili_phys",
            "prediction_ili_phys"]
    return df, ili[keep]


def metrics_for(name: str, horizon: int, full_df: pd.DataFrame,
                ili_df: pd.DataFrame) -> dict:
    """Full-horizon (7-variable) metrics + ILITOTAL fixed-step metrics."""
    # full-horizon paper-style metrics over the complete 7-variable output
    all_z_true = full_df["y_true"].to_numpy()
    all_z_pred = full_df["y_pred"].to_numpy()
    all_p_true = full_df["y_true_phys"].to_numpy()
    all_p_pred = full_df["y_pred_phys"].to_numpy()
    m = {
        "mse_all_z": MET.mse(all_z_true, all_z_pred),
        "mae_all_z": MET.mae(all_z_true, all_z_pred),
        "mse_all_phys": MET.mse(all_p_true, all_p_pred),
        "mae_all_phys": MET.mae(all_p_true, all_p_pred),
        "n_rows_z": int(len(all_z_true)),
        "n_variables": int(full_df["var_index"].nunique()),
        "horizon": horizon,
    }
    fixed = SCR.fixed_step_metrics(ili_df)
    return {"full_horizon": m, "fixed_step": fixed}


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest, prov = {}, {}
    all_preds, all_metrics = [], {}
    for name in ("last_value_naive", "seasonal_naive"):
        all_metrics[name] = {}
        for h in HORIZONS:
            full_df, ili_df = build_predictions(name, h)
            all_preds.append(ili_df)
            all_metrics[name][str(h)] = metrics_for(name, h, full_df, ili_df)
            print(f"[baseline] {name} L{h} rows={len(ili_df)} "
                  f"mse_all_z={all_metrics[name][str(h)]['full_horizon']['mse_all_z']:.6f}")
        manifest[name] = {
            "deterministic": True, "stochastic_seed_applicable": False,
            "mapped_seed_cells": SEEDS, "horizons": HORIZONS,
            "role": "reference_baseline_outside_4v4",
            "is_frozen_reference": name == "last_value_naive",
            "primary_channel": "ILITOTAL", "variables": 7,
            "seasonal_lag_weeks": SEASONAL_LAG if name == "seasonal_naive" else None,
        }
        prov[name] = {
            "dataset": "canonical National-Illness",
            "canonical_data_sha256": SCR.CANONICAL_DATA_SHA256,
            "scaler_file": SCALER_JSON,
            "scaler_fit": "train rows only",
            "window_T": 104, "split": "train 717 / validation 102 / test 206",
            "validation_use": "validation windows only; test split NEVER read",
            "metric_code": "innovation.metrics + innovation.screening_artifacts",
            "construction": ("persistence: repeat last input value"
                             if name == "last_value_naive"
                             else "lag-52 seasonal value from the input window"),
        }

    pd.concat(all_preds, ignore_index=True).to_csv(
        os.path.join(OUT_DIR, "baseline_predictions.csv"), index=False)
    with open(os.path.join(OUT_DIR, "baseline_metrics.json"), "w",
              encoding="utf-8") as f:
        json.dump({"generated_utc": NOW, "metrics": all_metrics,
                   "test_access_count": 0, "holdout_access_count": 0}, f, indent=2)
    with open(os.path.join(OUT_DIR, "baseline_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"generated_utc": NOW, "baselines": manifest,
                   "frozen_reference": "last_value_naive",
                   "enters_4v4_count": False}, f, indent=2)
    with open(os.path.join(OUT_DIR, "baseline_provenance.json"), "w",
              encoding="utf-8") as f:
        json.dump({"generated_utc": NOW, "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                   "node": os.environ.get("SLURMD_NODENAME"),
                   "deployment_root": _ROOT, "provenance": prov,
                   "test_access_count": 0, "holdout_access_count": 0}, f, indent=2)
    print(f"[baseline] wrote 4 artifacts -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
