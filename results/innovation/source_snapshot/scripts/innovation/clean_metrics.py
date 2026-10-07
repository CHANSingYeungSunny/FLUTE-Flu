"""clean_metrics.py — the clean-v3 frozen metric contracts.

Four formal artifact families, all computed from SAVED predictions only:

  1. paper_aligned_full_output_metrics.json
       mse_all_7vars_full_horizon_z / mae_all_7vars_full_horizon_z
       MSE & MAE over EVERY valid element of the complete seven-variable,
       complete-L output in paper-aligned StandardScaler (z) space.
       -> this is the PRIMARY champion selector (average_MSE_4L).

  2. ilitotal_fixed_step_metrics.json
       ILITOTAL fixed steps 0/1/2/3, each reported INDEPENDENTLY.
       step 0 = 1-week-ahead ... step 3 = 4-week-ahead.
       Never averaged across steps; never pooled into a champion score.

  3. ilitotal_full_horizon_metrics.json
       ILITOTAL MSE/MAE over the complete horizon (z and physical space).

  4. pte_pie_metrics.json
       PTE = |predicted peak week - observed peak week|          (weeks)
       PIE = |predicted peak intensity - observed peak intensity| /
             observed peak intensity                            (%)
       Literature thresholds ONLY: PTE <= 1 week, PIE <= 25%.

FORBIDDEN here by the final protocol, and therefore absent:
  Peak Hit Rate (0.70/0.75), PTE <= 2 weeks, PIE <= 20%,
  +/-2-week matching window, peak-aware early stopping / checkpoint gate,
  peak_hit_ratio gate or tie-breaker, weighted PTE/PIE champion score.

No model is loaded and no inference is run anywhere in this module.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ── frozen literature thresholds (final protocol) ───────────────────────────
PTE_THRESHOLD_WEEKS = 1
PIE_THRESHOLD_PCT = 25.0
FIXED_STEPS = (0, 1, 2, 3)
STEP_LEAD_WEEKS = {0: 1, 1: 2, 2: 3, 3: 4}
ILITOTAL_INDEX = 4          # canonical National-Illness variable order
N_VARIABLES = 7

PREDICTION_COLUMNS = ["model_key", "horizon", "seed_or_rep", "split",
                      "forecast_origin", "target_date", "step", "lead_weeks",
                      "variable", "variable_index", "y_true_z", "y_pred_z",
                      "y_true_physical", "y_pred_physical"]


def _mse(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.mean((a - b) ** 2))


def _mae(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.mean(np.abs(a - b)))


def _finite(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    return df[[a, b]].replace([np.inf, -np.inf], np.nan).dropna()


def paper_aligned_full_output_metrics(pred_df: pd.DataFrame,
                                      n_variables: int = N_VARIABLES) -> dict:
    """Family 1 — the paper-aligned primary selector metrics."""
    # Keep `variable_index` alongside the two metric columns: dropping it would
    # make the per-variable breakdown impossible.
    keep = [c for c in ("variable_index",) if c in pred_df.columns]
    d_all = (pred_df[["y_true_z", "y_pred_z"] + keep]
             .replace([np.inf, -np.inf], np.nan)
             .dropna(subset=["y_true_z", "y_pred_z"]))
    d = d_all[["y_true_z", "y_pred_z"]]
    per_var = {}
    for vi, g in d_all.groupby("variable_index"):
        gg = _finite(g, "y_true_z", "y_pred_z")
        per_var[str(int(vi))] = {"mse_z": _mse(gg["y_true_z"], gg["y_pred_z"]),
                                 "mae_z": _mae(gg["y_true_z"], gg["y_pred_z"]),
                                 "n": int(len(gg))}
    seen = sorted(int(v) for v in d_all["variable_index"].unique())
    return {
        "contract": "paper_aligned_full_output",
        "space": "StandardScaler z",
        "n_variables": int(n_variables),
        "variables_observed": seen,
        "complete_seven_variable_output": sorted(seen) == list(range(n_variables)),
        "mse_all_7vars_full_horizon_z": _mse(d["y_true_z"], d["y_pred_z"]),
        "mae_all_7vars_full_horizon_z": _mae(d["y_true_z"], d["y_pred_z"]),
        "n_elements": int(len(d)),
        "horizon": (int(pred_df["horizon"].iloc[0])
                    if "horizon" in pred_df.columns and len(pred_df) else None),
        "per_variable_z": per_var,
        "primary_selector_role": "average_MSE_4L is the arithmetic mean of the "
                                 "four per-L values of mse_all_7vars_full_horizon_z",
    }


def _ilitotal(df: pd.DataFrame) -> pd.DataFrame:
    if "variable_index" in df.columns:
        return df[df["variable_index"] == ILITOTAL_INDEX]
    return df[df["variable"] == "ILITOTAL"]


def ilitotal_fixed_step_metrics(pred_df: pd.DataFrame,
                                steps=FIXED_STEPS) -> dict:
    """Family 2 — ILITOTAL fixed steps 0/1/2/3, reported independently."""
    d = _ilitotal(pred_df)
    out = {
        "contract": "ilitotal_fixed_step",
        "channel": "ILITOTAL", "channel_index": ILITOTAL_INDEX,
        "steps_never_averaged": True,
        "never_pooled_into_champion_score": True,
        "step_lead_weeks": {str(k): v for k, v in STEP_LEAD_WEEKS.items()},
        "steps": {},
    }
    for s in steps:
        s = int(s)
        g = d[d["step"] == s]
        gz = _finite(g, "y_true_z", "y_pred_z")
        gp = _finite(g, "y_true_physical", "y_pred_physical")
        out["steps"][str(s)] = {
            "step": s,
            "lead_weeks": STEP_LEAD_WEEKS[s],
            "available": bool(len(gz)),
            "n": int(len(gz)),
            "mse_z": _mse(gz["y_true_z"], gz["y_pred_z"]) if len(gz) else None,
            "mae_z": _mae(gz["y_true_z"], gz["y_pred_z"]) if len(gz) else None,
            "mse_physical": (_mse(gp["y_true_physical"], gp["y_pred_physical"])
                             if len(gp) else None),
            "mae_physical": (_mae(gp["y_true_physical"], gp["y_pred_physical"])
                             if len(gp) else None),
        }
    return out


def ilitotal_full_horizon_metrics(pred_df: pd.DataFrame) -> dict:
    """Family 3 — ILITOTAL over the complete horizon."""
    d = _ilitotal(pred_df)
    gz = _finite(d, "y_true_z", "y_pred_z")
    gp = _finite(d, "y_true_physical", "y_pred_physical")
    return {
        "contract": "ilitotal_full_horizon",
        "channel": "ILITOTAL", "channel_index": ILITOTAL_INDEX,
        "horizon": (int(pred_df["horizon"].iloc[0])
                    if "horizon" in pred_df.columns and len(pred_df) else None),
        "mse_z": _mse(gz["y_true_z"], gz["y_pred_z"]) if len(gz) else None,
        "mae_z": _mae(gz["y_true_z"], gz["y_pred_z"]) if len(gz) else None,
        "mse_physical": (_mse(gp["y_true_physical"], gp["y_pred_physical"])
                         if len(gp) else None),
        "mae_physical": (_mae(gp["y_true_physical"], gp["y_pred_physical"])
                         if len(gp) else None),
        "n": int(len(gz)),
        "note": "disease-specific secondary; never replaces the seven-variable "
                "paper-aligned selector",
    }


def _seasonal_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one row per target week: group by target_date, mean."""
    if df.empty:
        return df
    return (df.groupby("target_date", as_index=False)
              .agg(y_true_z=("y_true_z", "mean"), y_pred_z=("y_pred_z", "mean"),
                   y_true_physical=("y_true_physical", "mean"),
                   y_pred_physical=("y_pred_physical", "mean"))
              .sort_values("target_date"))


def pte_pie_metrics(pred_df: pd.DataFrame, steps=FIXED_STEPS) -> dict:
    """Family 4 — literature PTE/PIE with the 1-week / 25% thresholds only."""
    d = _ilitotal(pred_df)
    out = {
        "contract": "pte_pie_literature",
        "channel": "ILITOTAL", "channel_index": ILITOTAL_INDEX,
        "definitions": {
            "PTE": "abs(predicted peak week - observed peak week), in weeks",
            "PIE": "abs(predicted peak intensity - observed peak intensity) / "
                   "observed peak intensity, in percent",
        },
        "thresholds": {"PTE_weeks": PTE_THRESHOLD_WEEKS,
                       "PIE_percent": PIE_THRESHOLD_PCT},
        "forbidden_and_absent": ["Peak Hit Rate (0.70/0.75)", "PTE <= 2 weeks",
                                 "PIE <= 20 percent",
                                 "plus/minus 2-week matching window",
                                 "peak-aware early stopping / checkpoint gate",
                                 "peak_hit_ratio gate or tie-breaker",
                                 "weighted PTE/PIE champion score"],
        "steps": {},
    }
    for s in steps:
        s = int(s)
        g = d[d["step"] == s]
        ser = _seasonal_frame(g)
        entry = {"step": s, "lead_weeks": STEP_LEAD_WEEKS[s],
                 "available": bool(len(ser)), "n_points": int(len(ser))}
        if len(ser) >= 2:
            yt = ser["y_true_physical"].to_numpy(dtype=float)
            yp = ser["y_pred_physical"].to_numpy(dtype=float)
            obs_i = int(np.argmax(yt))
            pred_i = int(np.argmax(yp))
            pte = float(abs(pred_i - obs_i))
            obs_peak = float(yt[obs_i])
            pie = (float(abs(yp[pred_i] - obs_peak) / obs_peak * 100.0)
                   if obs_peak else None)
            entry.update({
                "observed_peak_index": obs_i,
                "predicted_peak_index": pred_i,
                "observed_peak_value": obs_peak,
                "predicted_peak_value": float(yp[pred_i]),
                "PTE_weeks": pte,
                "PIE_percent": pie,
                "accurate_peak_timing": bool(pte <= PTE_THRESHOLD_WEEKS),
                "accurate_peak_intensity": bool(pie is not None
                                                and pie <= PIE_THRESHOLD_PCT),
            })
            entry["literature_criterion_met"] = bool(
                entry["accurate_peak_timing"]
                and entry["accurate_peak_intensity"])
        else:
            entry.update({"PTE_weeks": None, "PIE_percent": None,
                          "accurate_peak_timing": False,
                          "accurate_peak_intensity": False,
                          "literature_criterion_met": False,
                          "reason": "insufficient target weeks for peak detection"})
        out["steps"][str(s)] = entry
    return out


def compute_all(pred_df: pd.DataFrame) -> dict:
    """Produce all four families from one saved prediction frame."""
    return {
        "paper_aligned_full_output_metrics":
            paper_aligned_full_output_metrics(pred_df),
        "ilitotal_fixed_step_metrics": ilitotal_fixed_step_metrics(pred_df),
        "ilitotal_full_horizon_metrics": ilitotal_full_horizon_metrics(pred_df),
        "pte_pie_metrics": pte_pie_metrics(pred_df),
    }


# ── seven-variable deterministic baselines ─────────────────────────────────
def naive_prediction_frame(name: str, X_val: np.ndarray, Y_val: np.ndarray,
                           idx_val, horizon: int, var_names, mean_v, std_v,
                           dates=None, seed_or_rep="n/a") -> pd.DataFrame:
    """Build the frozen long prediction schema for a 7-variable naive baseline.

    X_val: (n, N, T) normalized;  Y_val: (n, N, L) normalized
    (channel-first, matching this codebase's window layout).
    """
    n, N, T = X_val.shape
    L = Y_val.shape[2]
    rows = []
    lag = 52
    for i in range(n):
        origin = idx_val[i] if hasattr(idx_val, "__getitem__") else None
        for vi in range(N):
            for k in range(L):
                if name == "last_value_naive":
                    pred_z = float(X_val[i, vi, -1])
                elif name == "seasonal_naive":
                    src = (T - 1) + (k + 1) - lag
                    src = min(max(src, 0), T - 1)
                    pred_z = float(X_val[i, vi, src])
                else:
                    raise ValueError(f"unknown baseline {name}")
                true_z = float(Y_val[i, vi, k])
                rows.append({
                    "model_key": name,
                    "horizon": int(horizon),
                    "seed_or_rep": seed_or_rep,
                    "split": "val",
                    "forecast_origin": int(origin) if origin is not None else None,
                    "target_date": (dates[i + k + 1]
                                    if dates is not None and (i + k + 1) < len(dates)
                                    else None),
                    "step": k,
                    "lead_weeks": k + 1,
                    "variable": var_names[vi] if var_names else f"var{vi}",
                    "variable_index": vi,
                    "y_true_z": true_z,
                    "y_pred_z": pred_z,
                    "y_true_physical": float(true_z * std_v[vi] + mean_v[vi]),
                    "y_pred_physical": float(pred_z * std_v[vi] + mean_v[vi]),
                })
    return pd.DataFrame(rows, columns=PREDICTION_COLUMNS)


__all__ = ["PTE_THRESHOLD_WEEKS", "PIE_THRESHOLD_PCT", "FIXED_STEPS",
           "STEP_LEAD_WEEKS", "ILITOTAL_INDEX", "N_VARIABLES",
           "PREDICTION_COLUMNS", "paper_aligned_full_output_metrics",
           "ilitotal_fixed_step_metrics", "ilitotal_full_horizon_metrics",
           "pte_pie_metrics", "compute_all", "naive_prediction_frame"]
