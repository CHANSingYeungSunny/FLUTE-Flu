"""test_eval.py — one-time Test/Holdout inference for frozen v3_clean rows.

This is the ONLY entry point that may read the Test split and write
`test_predictions.csv`. It is inference-only and runs on a compute node.

For ONE frozen run_key it:
  * resolves the immutable 598-row spec (accepted rows ARE eligible here —
    this deliberately does NOT reuse clean_runner.resolve_spec, which refuses
    already-accepted rows);
  * loads the raw data + train-only scaler + normalizes + builds windows (T=104,
    stride 1, split by target start week — identical to data_pipeline);
  * builds the model architecture EXACTLY as clean_runner does
    (make_backbone + make_encoder, encoder fit on train rows only, seed 42);
  * for stochastic arms: restores the compact checkpoint (base_sd | compact,
    strict load, missing=0 unexpected=0) — the full checkpoint no longer exists;
  * for baseline arms: deterministic reconstruction (no checkpoint);
  * infers on X_test ONLY; writes test_predictions.csv with REAL target_date;
  * computes the four frozen metric families on the TEST split;
  * writes test_manifest.json (provenance + restoration evidence).

Hard rules (fail-stop on violation):
  * scaler fit = train rows only; encoder fit = train rows only; prompt stats =
    train rows only. NO Test target value ever enters model input, prompt,
    scaler, statistics, adaptation, or model selection.
  * no training, no model/checkpoint/seed/prompt/scaler/horizon/endpoint change.
  * writes a single isolated test-eval directory; refuses to overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))     # <root>/scripts/innovation
_SCRIPTS_ROOT = os.path.dirname(_HERE)                 # <root>/scripts
_ROOT = os.path.dirname(_SCRIPTS_ROOT)                 # <root>
for _p in (_SCRIPTS_ROOT, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                  # noqa: E402
import pandas as pd                 # noqa: E402
import torch                        # noqa: E402

from innovation import clean_metrics as CM            # noqa: E402
from innovation import compact_checkpoint as CC       # noqa: E402
from innovation import clean_runner as CR             # noqa: E402

N_VARIABLES = 7
T_WINDOW = 104
SPLIT = {"train": 717, "validation": 102, "test": 206}
ILITOTAL_INDEX = CM.ILITOTAL_INDEX


def _sha256_file(p: str) -> str:
    if not os.path.exists(p):
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _atomic_write_json(path: str, obj) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def resolve_spec_for_test(reg: dict, run_key: str) -> dict:
    """Resolve the frozen spec for a run_key WITHOUT the 'already accepted'
    refusal (accepted rows are exactly what the one-time Test phase runs)."""
    specs = [s for s in reg.get("specs", []) if s.get("run_key") == run_key]
    if len(specs) == 0:
        raise SystemExit(f"unknown run_key: {run_key}")
    if len(specs) > 1:
        raise SystemExit(f"duplicate run_key in registry: {run_key}")
    s = specs[0]
    for field in ("model", "horizon", "seed", "arm", "parent_model", "wave"):
        if field not in s:
            raise SystemExit(f"malformed spec {run_key}: missing {field}")
    return s


def build_test_prediction_frame(y_pred: np.ndarray, y_true: np.ndarray,
                                idx_test, horizon: int, var_names,
                                mean_v, std_v, model_key, seed):
    """Mirror clean_runner.build_full_prediction_frame but for the TEST split,
    with a REAL target_date = forecast_origin + T + step (abs_week)."""
    rows = []
    n, N, L = y_true.shape
    for i in range(n):
        origin = int(np.asarray(idx_test)[i])
        for vi in range(N):
            for k in range(L):
                tz = float(y_true[i, vi, k])
                pz = float(y_pred[i, vi, k])
                rows.append({
                    "model_key": model_key, "horizon": int(horizon),
                    "seed_or_rep": seed, "split": "test",
                    "forecast_origin": origin,
                    "target_date": int(origin + T_WINDOW + k),
                    "step": k, "lead_weeks": k + 1,
                    "variable": var_names[vi], "variable_index": vi,
                    "y_true_z": tz, "y_pred_z": pz,
                    "y_true_physical": float(tz * std_v[vi] + mean_v[vi]),
                    "y_pred_physical": float(pz * std_v[vi] + mean_v[vi]),
                })
    return pd.DataFrame(rows, columns=CM.PREDICTION_COLUMNS)


def baseline_predictions(name: str, X_test: np.ndarray, horizon: int):
    """Deterministic baseline prediction from the input window alone (no model).
    Mirrors clean_metrics.naive_prediction_frame's math exactly."""
    n, N, T = X_test.shape
    out = np.zeros((n, N, horizon), dtype=np.float32)
    lag = 52
    for i in range(n):
        for vi in range(N):
            for k in range(horizon):
                if name == "last_value_naive":
                    out[i, vi, k] = float(X_test[i, vi, -1])
                elif name == "seasonal_naive":
                    src = (T - 1) + (k + 1) - lag
                    src = min(max(src, 0), T - 1)
                    out[i, vi, k] = float(X_test[i, vi, src])
                else:
                    raise ValueError(f"unknown baseline {name}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="one-time Test/Holdout inference")
    ap.add_argument("--run-key", required=True)
    ap.add_argument("--out-root", default=None,
                    help="output root for test-eval directories")
    ap.add_argument("--durable-root", required=True,
                    help="path to the durable screening root (compact.safetensors)")
    a = ap.parse_args(argv)

    deployment_root = os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if not deployment_root:
        raise SystemExit("INNOVATION_DEPLOYMENT_ROOT must be set")
    out_root = a.out_root or os.path.join(deployment_root, "results",
                                          "v3_clean", "test_eval")

    reg = CR.load_registry(deployment_root)
    spec = resolve_spec_for_test(reg, a.run_key)
    run_key = a.run_key

    # --- isolated output dir (create-only) ---------------------------------
    os.makedirs(out_root, exist_ok=True)
    run_dir = os.path.join(out_root, run_key)
    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise SystemExit(f"test-eval dir already exists and is non-empty: {run_dir}")
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "metrics"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "predictions"), exist_ok=True)

    status_path = os.path.join(run_dir, "test_status.json")
    started = time.time()

    def status(state, **extra):
        _atomic_write_json(status_path, {
            "run_key": run_key, "state": state,
            "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "split": SPLIT, **extra})

    status("CREATED")
    try:
        from innovation.data_pipeline import (build_windows, load_raw_df,
                                              load_scaler, normalize, to_array)
        from innovation.backbones.registry import make_backbone
        from innovation.encoders.registry import make_encoder

        raw = load_raw_df()
        scaler = load_scaler()
        data = normalize(to_array(raw), scaler)
        horizon = int(spec["horizon"])
        windows = build_windows(data, horizon)

        var_names = list(raw.columns[:N_VARIABLES])
        mean_v = np.asarray(scaler.mean_, dtype=float).reshape(-1)
        std_v = np.asarray(scaler.scale_, dtype=float).reshape(-1)

        arm = spec["arm"]
        name = spec["model"]
        seed = spec["seed"]

        X_test = np.asarray(windows["X_test"])
        Y_test = np.asarray(windows["Y_test"])
        idx_test = np.asarray(windows["idx_test"])

        manifest = {
            "run_key": run_key,
            "model": name,
            "arm": arm,
            "horizon": horizon,
            "seed": seed,
            "wave": spec["wave"],
            "split": SPLIT,
            "n_test_windows": int(X_test.shape[0]),
            "test_target_abs_week_min": int(idx_test.min() + T_WINDOW),
            "test_target_abs_week_max": int(idx_test.max() + T_WINDOW + horizon - 1),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if arm == "baseline":
            # deterministic no-checkpoint reconstruction
            y_pred = baseline_predictions(name, X_test, horizon)
            pred_df = build_test_prediction_frame(
                y_pred, Y_test, idx_test, horizon, var_names,
                mean_v, std_v, name, seed="n/a")
            manifest.update({
                "checkpoint_applicable": False,
                "stochastic_seed_applicable": False,
                "reason": "deterministic_baseline_no_checkpoint",
                "compact_sha256": "not_applicable",
                "canonical_tensor_sha256": "not_applicable",
            })
        else:
            # stochastic: restore the frozen compact checkpoint
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if name in CR.VARIANTS:
                base_model, enc_name, bkw, ekw = CR.VARIANTS[name]
            else:
                base_model, enc_name, bkw, ekw = name, CR.PRIMARY_MODELS[name], {}, {}
            if base_model in ("qwen_time_llm",):
                bkw = dict(bkw, model_id="Qwen/Qwen2.5-1.5B", load_backbone=True)
            elif base_model in ("calf_llm", "timecma_llm"):
                bkw = dict(bkw, model_id="gpt2", load_backbone=True)

            encoder = make_encoder(enc_name, **(ekw or {}))
            encoder.fit_on_train_only(raw.iloc[:SPLIT["train"]], horizon=horizon,
                                      seed=42)
            ctx_fn = (lambda bsz: encoder.encode(bsz, device=device,
                                                 horizon=horizon))

            model = make_backbone(base_model, T=T_WINDOW, N=N_VARIABLES,
                                  L=horizon, **bkw)
            if hasattr(model, "set_train_statistics"):
                model.set_train_statistics({"target_name": "ILITOTAL",
                                            "horizon": horizon,
                                            "channel_count": N_VARIABLES})
            model = model.to(device)

            # --- restore compact (base_sd | compact), strict -----------------
            compact_path = os.path.join(a.durable_root, run_key,
                                        "compact.safetensors")
            if not os.path.isfile(compact_path):
                raise SystemExit(f"compact checkpoint missing: {compact_path}")
            compact_sd = CC._load_compact(compact_path)
            base_sd = {k: v.detach().cpu()
                       for k, v in model.state_dict().items()}
            rebuilt = dict(base_sd)
            rebuilt.update({k: v for k, v in compact_sd.items()})
            res = model.load_state_dict(rebuilt, strict=True)
            if res.missing_keys or res.unexpected_keys:
                raise SystemExit(
                    f"strict restore failed: missing={res.missing_keys} "
                    f"unexpected={res.unexpected_keys}")
            model.eval()

            manifest.update({
                "checkpoint_applicable": True,
                "stochastic_seed_applicable": True,
                "compact_sha256": _sha256_file(compact_path),
                "canonical_tensor_sha256": CC.canonical_tensor_sha256(compact_sd),
                "canonical_hash_schema": CC.CANONICAL_HASH_SCHEMA,
                "base_model": base_model,
                "text_encoder": enc_name,
                "restoration": {
                    "strict_load_ok": True,
                    "missing_keys": list(res.missing_keys),
                    "unexpected_keys": list(res.unexpected_keys),
                },
                "device": device,
            })

            with torch.no_grad():
                out = model(torch.as_tensor(X_test, device=device),
                            ctx=ctx_fn(X_test.shape[0]))
            y_pred = out.detach().cpu().numpy().reshape(-1, N_VARIABLES, horizon)
            pred_df = build_test_prediction_frame(
                y_pred, Y_test, idx_test, horizon, var_names,
                mean_v, std_v, name, seed)

        pred_df.to_csv(os.path.join(run_dir, "predictions",
                                    "test_predictions.csv"), index=False)

        metrics = CM.compute_all(pred_df)
        for fname, payload in (("paper_aligned_full_output_metrics",
                                "paper_aligned_full_output_metrics"),
                               ("ilitotal_fixed_step_metrics",
                                "ilitotal_fixed_step_metrics"),
                               ("ilitotal_full_horizon_metrics",
                                "ilitotal_full_horizon_metrics"),
                               ("pte_pie_metrics", "pte_pie_metrics")):
            _atomic_write_json(os.path.join(run_dir, "metrics", f"{fname}.json"),
                               metrics[payload])

        manifest.update({
            "elapsed_seconds": round(time.time() - started, 3),
            "metrics_written": sorted(os.listdir(os.path.join(run_dir, "metrics"))),
        })
        _atomic_write_json(os.path.join(run_dir, "test_manifest.json"), manifest)
        status("COMPLETED", elapsed_seconds=round(time.time() - started, 3),
               n_test_windows=int(X_test.shape[0]))
        return 0

    except SystemExit:
        raise
    except Exception as e:                                        # noqa: BLE001
        try:
            status("FAILED", error=f"{type(e).__name__}: {e}")
        except Exception:
            pass
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
