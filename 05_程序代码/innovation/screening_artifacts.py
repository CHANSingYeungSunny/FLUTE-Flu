"""screening_artifacts.py — v3.4 formal-Screening artifact contract.

Adds the three artefacts that formal Screening requires on top of the Pilot
schema, plus the full prediction key set:

  * ``predictions/validation_predictions.csv`` gains ``model_key``, ``horizon``,
    ``seed``, ``variable`` and ``lead_weeks`` so every fixed step can be
    reconstructed independently   (screening metric contract, §7);
  * ``metrics/fixed_step_metrics.json`` — ILITOTAL per fixed step 0/1/2/3:
    z-space and physical-space MSE/MAE, PTE, PIE, and the literature peak
    criterion (PTE <= 1 week AND PIE <= 25%)   (§7 family B);
  * ``prompt_statistics_metadata.json`` — provenance of the train-only prompt
    statistics   (§8);
  * ``resource_usage.json`` — parameters, GPU-hours, peak GPU memory, inference
    latency and storage   (§8).

This module is PURE bookkeeping over already-computed arrays and files. It never
loads a model, never infers, and never reads the test split. Steps are NEVER
averaged or merged: each step is reported on its own.
"""
from __future__ import annotations

import hashlib
import os

import numpy as np
import pandas as pd

from innovation import metrics as MET

# Frozen canonical National-Illness dataset identity (prompt §4). Recorded in
# every artifact chain; never recomputed from a different file.
CANONICAL_DATA_SHA256 = \
    "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d"

# Frozen by the screening metric contract BEFORE the first submission.
FIXED_STEPS = (0, 1, 2, 3)
STEP_LEAD_WEEKS = {0: 1, 1: 2, 2: 3, 3: 4}
PRIMARY_STEP = 0
SUPPLEMENTARY_STEPS = (1, 2, 3)
FIXED_CHANNEL = "ILITOTAL"
Z_TRUE, Z_PRED = "ground_truth_ili", "prediction_ili"
P_TRUE, P_PRED = "ground_truth_ili_phys", "prediction_ili_phys"
PEAK_PTE_MAX_WEEKS = 1
PEAK_PIE_MAX_PCT = 25.0


def add_prediction_keys(df: pd.DataFrame, *, model_key: str, horizon: int,
                        seed: int, variable: str = FIXED_CHANNEL) -> pd.DataFrame:
    """Attach the full key set required by the Screening metric contract §7."""
    out = df.copy()
    out["model_key"] = str(model_key)
    out["horizon"] = int(horizon)
    out["seed"] = int(seed)
    out["variable"] = str(variable)
    out["lead_weeks"] = out["step"].astype(int) + 1
    # `target_date` is the pre-existing `week_start_date` under its contract name.
    if "week_start_date" in out.columns and "target_date" not in out.columns:
        out["target_date"] = pd.to_datetime(out["week_start_date"]) \
            .dt.strftime("%Y-%m-%d")
    return out


def _series(frame: pd.DataFrame, step: int, gt: str, pred: str) -> pd.DataFrame:
    return MET.aggregate_fixed_step(frame, step=int(step), gt_col=gt,
                                    pred_col=pred)


def fixed_step_metrics(val_df: pd.DataFrame,
                       steps=FIXED_STEPS) -> dict:
    """Per fixed step: z MSE/MAE, physical MSE/MAE, PTE, PIE, peak criterion."""
    frame = MET.split_frame(val_df, "val")
    out = {
        "contract_version": "v3.4-fixed-step-metrics",
        "channel": FIXED_CHANNEL,
        "primary_step": PRIMARY_STEP,
        "supplementary_steps": list(SUPPLEMENTARY_STEPS),
        "steps_never_averaged": True,
        "peak_criterion": {"PTE_max_weeks": PEAK_PTE_MAX_WEEKS,
                           "PIE_max_pct": PEAK_PIE_MAX_PCT,
                           "expression": "PTE <= 1 week AND PIE <= 25%"},
        "step_lead_weeks": {str(k): int(v) for k, v in STEP_LEAD_WEEKS.items()},
        "steps": {},
    }
    for s in steps:
        s = int(s)
        entry = {"step": s, "lead_weeks": STEP_LEAD_WEEKS.get(s)}
        try:
            zs = _series(frame, s, Z_TRUE, Z_PRED)
            ps = _series(frame, s, P_TRUE, P_PRED)
        except Exception as e:  # a step absent for this horizon
            entry.update({"available": False, "reason": f"{type(e).__name__}: {e}"})
            out["steps"][str(s)] = entry
            continue
        entry["available"] = True
        entry["n_points"] = int(len(zs))
        entry["mse_z"] = MET.mse(zs["gt"], zs["pred"])
        entry["mae_z"] = MET.mae(zs["gt"], zs["pred"])
        entry["mse_phys"] = MET.mse(ps["gt"], ps["pred"])
        entry["mae_phys"] = MET.mae(ps["gt"], ps["pred"])
        try:
            _by_season, agg = MET.seasonal_peak_metrics(ps)
            n_eval = int(agg.get("n_seasons_evaluable") or 0)
            n_hit = int(agg.get("n_hits") or 0)
            entry["pte_weeks"] = agg.get("mean_pte_weeks")
            entry["pie_pct"] = agg.get("mean_pie_pct")
            entry["n_seasons_evaluable"] = n_eval
            entry["n_hits"] = n_hit
            entry["peak_hit_ratio"] = agg.get("peak_hit_ratio")
            entry["peak_criterion_pass_all"] = bool(
                n_eval > 0 and n_hit == n_eval
                and entry["pte_weeks"] is not None
                and entry["pte_weeks"] <= PEAK_PTE_MAX_WEEKS
                and entry["pie_pct"] is not None
                and entry["pie_pct"] <= PEAK_PIE_MAX_PCT)
        except Exception as e:
            entry["pte_weeks"] = None
            entry["pie_pct"] = None
            entry["peak_metric_error"] = f"{type(e).__name__}: {e}"
            entry["peak_criterion_pass_all"] = False
        out["steps"][str(s)] = entry
    return out


def _null_safe_context_dim(encoder) -> int | None:
    """D7 repair: serialize an OPTIONAL context dimension safely.

    `--text-encoder none` is not a zero-dimensional encoder: its
    ``context_dim()`` legitimately returns ``None``. That must be serialized as
    JSON ``null`` — never 0, -1, or a fabricated dimension. ``context_dim()``
    is called AT MOST ONCE. Unexpected non-numeric, non-null values fail
    closed with a clear error rather than being coerced.
    """
    cd = encoder.context_dim() if hasattr(encoder, "context_dim") else None
    if cd is None:
        return None
    if isinstance(cd, bool):  # bool is an int subclass; never a dimension
        raise TypeError(
            "context_dim() returned a bool; expected an integer or None")
    if isinstance(cd, int):
        return int(cd)
    if isinstance(cd, float) and float(cd).is_integer():
        return int(cd)
    raise TypeError(
        f"context_dim() returned {type(cd).__name__} {cd!r}; expected an "
        "integer or None")


def _null_safe_context_dim(encoder) -> int | None:
    """D7 repair: serialize an OPTIONAL context dimension safely.

    `--text-encoder none` is not a zero-dimensional encoder: its
    ``context_dim()`` legitimately returns ``None``. That must be serialized as
    JSON ``null`` — never 0, -1, or a fabricated dimension. ``context_dim()``
    is called AT MOST ONCE. Unexpected non-numeric, non-null values fail
    closed with a clear error rather than being coerced.
    """
    cd = encoder.context_dim() if hasattr(encoder, "context_dim") else None
    if cd is None:
        return None
    if isinstance(cd, bool):  # bool is an int subclass; never a dimension
        raise TypeError(
            "context_dim() returned a bool; expected an integer or None")
    if isinstance(cd, int):
        return int(cd)
    if isinstance(cd, float) and float(cd).is_integer():
        return int(cd)
    raise TypeError(
        f"context_dim() returned {type(cd).__name__} {cd!r}; expected an "
        "integer or None")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def prompt_statistics_metadata(*, encoder, horizon: int, seed: int,
                               channel_count: int,
                               target_name: str = FIXED_CHANNEL) -> dict:
    """Provenance of the prompt statistics. Train-only by construction."""
    stats_sha = None
    stats_kind = None
    for attr in ("statistics_sha256", "stats_sha256"):
        v = getattr(encoder, attr, None)
        if isinstance(v, str) and v:
            stats_sha, stats_kind = v, attr
            break
    if stats_sha is None:
        for attr in ("state_dict", "statistics", "stats"):
            obj = getattr(encoder, attr, None)
            if callable(obj):
                try:
                    obj = obj()
                except Exception:
                    obj = None
            if obj is not None:
                try:
                    import json as _json
                    blob = _json.dumps(obj, sort_keys=True,
                                       default=str).encode("utf-8")
                    stats_sha, stats_kind = _sha256_bytes(blob), attr
                except Exception:
                    stats_sha, stats_kind = None, None
                if stats_sha:
                    break
    return {
        "contract_version": "v3.4-prompt-statistics",
        "fit_scope": "train rows only",
        "source_of_truth": "split_manifest.json: prompt_stats_fit = train rows only",
        "target_name": target_name,
        "horizon": int(horizon),
        "seed": int(seed),
        "channel_count": int(channel_count),
        "encoder_name": getattr(encoder, "name", None)
        or encoder.__class__.__name__,
        "encoder_available": bool(getattr(encoder, "is_available", lambda: True)()),
        # D7: null-safe, called at most once (see _null_safe_context_dim).
        "context_dim": _null_safe_context_dim(encoder),
        "statistics_sha256": stats_sha,
        "statistics_source_attribute": stats_kind,
        "train_only_enforced": True,
    }


def _dir_bytes(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def resource_usage(*, run_dir: str, ckpt_path: str, train_seconds: float,
                   inference_seconds: float, trainable_parameters: int,
                   total_parameters: int, n_train_windows: int,
                   n_val_windows: int, batch_size: int, epochs: int,
                   device: str, device_name: str, lr: float, patience: int,
                   horizon: int, seed: int, model_key: str) -> dict:
    """Parameters, GPU-hours, peak GPU memory, latency and storage."""
    peak_mem = None
    try:
        import torch
        if torch.cuda.is_available():
            peak_mem = int(torch.cuda.max_memory_allocated())
    except Exception:
        peak_mem = None
    ckpt_bytes = None
    try:
        ckpt_bytes = int(os.path.getsize(ckpt_path))
    except OSError:
        pass
    n_val_steps = int(n_val_windows) * int(horizon)
    return {
        "contract_version": "v3.4-resource-usage",
        "model_key": str(model_key),
        "horizon": int(horizon), "seed": int(seed),
        "device_actual": str(device), "device_name": str(device_name),
        "trainable_parameters": int(trainable_parameters),
        "total_parameters": int(total_parameters),
        "train_seconds": round(float(train_seconds), 6),
        "inference_seconds": round(float(inference_seconds), 6),
        "gpu_hours_train": round(float(train_seconds) / 3600.0, 8),
        "peak_gpu_memory_bytes": peak_mem,
        "peak_gpu_memory_gib": (round(peak_mem / (1024 ** 3), 4)
                                if peak_mem else None),
        "inference_latency_seconds_per_window": (
            round(float(inference_seconds) / int(n_val_windows), 8)
            if n_val_windows else None),
        "inference_latency_ms_per_forecast_step": (
            round(float(inference_seconds) * 1000.0 / n_val_steps, 6)
            if n_val_steps else None),
        "checkpoint_bytes": ckpt_bytes,
        "checkpoint_gib": (round(ckpt_bytes / (1024 ** 3), 6)
                           if ckpt_bytes else None),
        "run_dir_bytes": _dir_bytes(run_dir),
        "run_dir_gib": round(_dir_bytes(run_dir) / (1024 ** 3), 6),
        "n_train_windows": int(n_train_windows),
        "n_val_windows": int(n_val_windows),
        "batch_size": int(batch_size), "epochs": int(epochs),
        "learning_rate": float(lr), "patience": int(patience),
    }


def screening_marks() -> dict:
    """The exact eligibility block every formal Screening run must carry (§6)."""
    return {
        "experiment_stage": "screening",
        "purpose": "formal_validation_screening",
        "selection_eligible": True,
        "paper_result_eligible": "screening_only",
        "test_access_allowed": False,
        "holdout_access_allowed": False,
    }


def access_counters() -> dict:
    return {"test_access_count": 0, "holdout_access_count": 0}


def numeric_tolerance() -> dict:
    """Preregistered restoration tolerance (durable-storage policy §9)."""
    return {"metric": "max_abs_diff", "z_space_predictions": 1e-5,
            "mse_all_z_relative": 1e-6}


__all__ = ["FIXED_STEPS", "STEP_LEAD_WEEKS", "PRIMARY_STEP",
           "SUPPLEMENTARY_STEPS", "add_prediction_keys", "fixed_step_metrics",
           "prompt_statistics_metadata", "resource_usage", "screening_marks",
           "access_counters", "numeric_tolerance"]
