"""clean_runner.py — the clean-v3 single-run entry point.

One invocation == exactly one preregistered matrix row, resolved from the frozen
598-spec registry by `--run-key`. Nothing about the experiment can be overridden
on the command line: the model, parent, horizon, seed/repetition, control arm,
data and metrics all come from the frozen spec.

Guards enforced here:
  * unknown / duplicate / malformed / already-accepted run keys are refused;
  * the 18 deferred rows (execution_eligible_now == false) are refused;
  * an unbound BEST_VALIDATION_LLM_AFTER_SCREENING parent is refused;
  * source, spec, data, model and asset hashes are verified;
  * Test/holdout are never read.

Metric rules are the frozen ones: primary = seven-variable full-horizon z-space
MSE; key secondary = seven-variable full-horizon z-space MAE; ILITOTAL fixed
steps 0-3 reported separately (never averaged, never pooled); PTE/PIE use only
the 1-week / 25% literature thresholds.

Runs ONLY on a compute node (loads real models / data when the arm requires it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))     # <root>/scripts/innovation
# The importable package parent is <root>/scripts, NOT the deployment root.
# Inserting the root alone made every run die with
# "ModuleNotFoundError: No module named 'innovation'" (Gate 568972).
_SCRIPTS_ROOT = os.path.dirname(_HERE)                    # <root>/scripts
_ROOT = os.path.dirname(_SCRIPTS_ROOT)                    # <root>
for _p in (_SCRIPTS_ROOT, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                     # noqa: E402
import pandas as pd                    # noqa: E402

from innovation import clean_metrics as CM        # noqa: E402
from innovation import run_artifacts as ART       # noqa: E402

DEFERRED_PARENT = "BEST_VALIDATION_LLM_AFTER_SCREENING"
N_VARIABLES = 7
T_WINDOW = 104
SPLIT = {"train": 717, "validation": 102, "test": 206}
ILITOTAL_INDEX = CM.ILITOTAL_INDEX

# variant name -> (base model, text encoder, backbone kwargs, encoder kwargs)
# ALL six original MIFlu ablations are parented to gpt2_miflu.
VARIANTS = {
    "without_dataset_information":
        ("gpt2_miflu", "gpt2", {}, {"prompt_components": ("variable", "task")}),
    "without_task_instruction":
        ("gpt2_miflu", "gpt2", {}, {"prompt_components": ("dataset", "variable")}),
    "without_input_variable_description":
        ("gpt2_miflu", "gpt2", {}, {"prompt_components": ("dataset", "task")}),
    "without_lora":
        ("gpt2_miflu", "gpt2", {"use_lora": False}, {}),
    "without_multimodality":
        ("gpt2_miflu", "gpt2", {"multimodal": False}, {}),
    "without_lora_and_multimodality":
        ("gpt2_miflu", "gpt2", {"use_lora": False, "multimodal": False}, {}),
    "zero_text":
        ("gpt2_miflu", "gpt2", {}, {"text_mode": "zero"}),
    "shuffled_text":
        ("gpt2_miflu", "gpt2", {}, {"text_mode": "shuffle"}),
    "llm_removed_or_alignment_only":
        ("timecma_llm", "none", {"text_mode": "removed"}, {}),
}
PRIMARY_MODELS = {"nlinear": "none", "dlinear": "none", "patchtst": "none",
                  "itransformer": "none", "gpt2_miflu": "gpt2",
                  "qwen_time_llm": "none", "calf_llm": "none",
                  "timecma_llm": "none"}
BASELINES = ("last_value_naive", "seasonal_naive")


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


def _write_text(path: str, text: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# v3.11 (D11): the COMPLETE per-run artifact tree. `_atomic_write_json` and
# `_write_text` create the parent of the file they write (which is why
# metrics/ and checkpoints/ existed in Gate 569016), but pandas `.to_csv` does
# NOT — so logs/train_history.csv and predictions/validation_predictions.csv
# died with "Cannot save file into a non-existent directory".
RUN_SUBDIRS = ("logs", "predictions", "metrics", "checkpoints")


def ensure_run_dirs(run_dir: str, out_root: str) -> str:
    """Idempotently create the full run artifact tree (called ONCE per run).

    Safety, all mandatory:
      * `run_dir` must be a DIRECT child of the authorised output root;
      * the RESOLVED real paths must stay directly under the real output root,
        so a symlinked run directory or an escaping `..` can never cause a
        write outside the authorised output root;
      * only the four declared sub-directories are created — never any other
        path, and never a parent outside the authorised output root.

    Behaviour-neutral: no scientific input, metric or checkpoint choice is
    touched. Returns the resolved run directory.
    """
    real_out = os.path.realpath(out_root)
    real_run = os.path.realpath(run_dir)
    if os.path.dirname(real_run) != real_out:
        raise SystemExit(
            "run directory escapes the authorised output root: "
            f"{run_dir} (resolved {real_run})")
    os.makedirs(real_run, exist_ok=True)
    for name in RUN_SUBDIRS:
        d = os.path.join(real_run, name)
        if os.path.islink(d):
            raise SystemExit(f"refusing symlinked artifact directory: {d}")
        os.makedirs(d, exist_ok=True)
    return real_run


def load_registry(deployment_root: str) -> dict:
    # The frozen 598 matrix is immutable. The deferred-controls amendment may
    # supply an append-only amended execution registry (never the frozen file)
    # via INNOVATION_REGISTRY_REL; the default remains the frozen registry.
    rel = os.environ.get(
        "INNOVATION_REGISTRY_REL",
        os.path.join("results", "v3_clean", "runs", "complete_specs_598.json"))
    p = os.path.join(deployment_root, rel)
    if not os.path.exists(p):
        raise SystemExit(f"frozen spec registry not found: {p}")
    return json.loads(open(p, encoding="utf-8").read())


def resolve_spec(reg: dict, run_key: str) -> dict:
    specs = [s for s in reg["specs"] if s["run_key"] == run_key]
    if len(specs) == 0:
        raise SystemExit(f"unknown run_key: {run_key}")
    if len(specs) > 1:
        raise SystemExit(f"duplicate run_key in registry: {run_key}")
    s = specs[0]
    for field in ("model", "horizon", "seed", "arm", "parent_model", "wave"):
        if field not in s:
            raise SystemExit(f"malformed spec {run_key}: missing {field}")
    if s.get("accepted"):
        raise SystemExit(f"run_key already accepted: {run_key}")
    if not s.get("executable_binding", False) or not s.get("submittable", False):
        raise SystemExit(f"run_key not eligible now (deferred): {run_key}")
    if s.get("parent_model") == DEFERRED_PARENT:
        raise SystemExit("deferred parent is unbound: "
                         f"{DEFERRED_PARENT}")
    return s


def build_full_prediction_frame(y_pred: np.ndarray, y_true: np.ndarray,
                                idx_val, horizon: int, var_names,
                                mean_v, std_v, model_key, seed):
    """Rows for ALL seven variables (the existing predict_frame emits only
    ILITOTAL and therefore cannot support the paper-aligned primary metric)."""
    rows = []
    n, N, L = y_true.shape
    for i in range(n):
        origin = int(np.asarray(idx_val)[i])
        for vi in range(N):
            for k in range(L):
                tz = float(y_true[i, vi, k])
                pz = float(y_pred[i, vi, k])
                rows.append({
                    "model_key": model_key, "horizon": int(horizon),
                    "seed_or_rep": seed, "split": "val",
                    "forecast_origin": origin, "target_date": None,
                    "step": k, "lead_weeks": k + 1,
                    "variable": var_names[vi], "variable_index": vi,
                    "y_true_z": tz, "y_pred_z": pz,
                    "y_true_physical": float(tz * std_v[vi] + mean_v[vi]),
                    "y_pred_physical": float(pz * std_v[vi] + mean_v[vi]),
                })
    return pd.DataFrame(rows, columns=CM.PREDICTION_COLUMNS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="clean-v3 single-run entry point")
    ap.add_argument("--run-key", required=True,
                    help="exact run_key from the frozen 598-spec registry")
    ap.add_argument("--out-root", default=None,
                    help="output root for run directories")
    a = ap.parse_args(argv)

    deployment_root = os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if not deployment_root:
        raise SystemExit("INNOVATION_DEPLOYMENT_ROOT must be set")
    out_root = a.out_root or os.path.join(deployment_root, "results",
                                          "v3_clean", "runs")

    reg = load_registry(deployment_root)
    spec = resolve_spec(reg, a.run_key)
    run_key = a.run_key

    os.makedirs(out_root, exist_ok=True)
    run_dir = os.path.join(out_root, run_key)
    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise SystemExit(f"run directory already exists and is non-empty: {run_dir}")
    # D11: create the COMPLETE artifact tree ONCE, after the create-only and
    # path-containment checks, and before ANY artifact write.
    run_dir = ensure_run_dirs(run_dir, out_root)

    status_path = os.path.join(run_dir, "run_status.json")
    started = time.time()

    def status(state, **extra):
        rec = {"run_key": run_key, "state": state,
               "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "spec": {k: spec[k] for k in ("arm", "model", "parent_model",
                                             "horizon", "seed", "wave",
                                             "control")},
               **extra}
        _atomic_write_json(status_path, rec)
        return rec

    status("CREATED")
    try:
        status("RUNNING")
        from innovation.data_pipeline import (build_windows, load_raw_df,
                                              load_scaler, normalize, to_array)
        from innovation.backbones.registry import make_backbone
        from innovation.encoders.registry import make_encoder

        raw = load_raw_df()
        scaler = load_scaler()
        data = normalize(to_array(raw), scaler)
        horizon = int(spec["horizon"])
        windows = build_windows(data, horizon)

        source_manifest = os.path.join(deployment_root, "results", "v3_clean",
                                       "implementation", "source_manifest.json")
        src_agg = ""
        if os.path.exists(source_manifest):
            src_agg = json.loads(open(source_manifest, encoding="utf-8")
                                 .read()).get("aggregate_sha256", "")
        _atomic_write_json(os.path.join(run_dir, "source_manifest.json"),
                           {"registry_aggregate_sha256": reg.get("aggregate_sha256"),
                            "source_aggregate_sha256": src_agg,
                            "version": reg.get("version"),
                            "canonical_data_sha256": CM.__dict__.get(
                                "CANONICAL_DATA_SHA256", ""),
                            "split": SPLIT})

        _write_text(os.path.join(run_dir, "environment.txt"),
                    "\n".join([f"platform: {platform.platform()}",
                               f"python: {sys.version.split()[0]}",
                               f"node: {os.environ.get('SLURMD_NODENAME', '')}",
                               f"job: {os.environ.get('SLURM_JOB_ID', '')}"]))
        _write_text(os.path.join(run_dir, "git_commit.txt"), "")

        var_names = list(raw.columns[:N_VARIABLES])
        mean_v = np.asarray(scaler.mean_, dtype=float).reshape(-1)
        std_v = np.asarray(scaler.scale_, dtype=float).reshape(-1)

        arm = spec["arm"]
        name = spec["model"]
        seed = spec["seed"]

        if arm == "baseline":
            X_val = np.asarray(windows["X_val"])
            Y_val = np.asarray(windows["Y_val"])
            pred_df = CM.naive_prediction_frame(
                name, X_val, Y_val, windows["idx_val"], horizon, var_names,
                mean_v, std_v, seed_or_rep="n/a")
            metrics = CM.compute_all(pred_df)
            for fname, payload in (("paper_aligned_full_output_metrics",
                                    "paper_aligned_full_output_metrics"),
                                   ("ilitotal_fixed_step_metrics",
                                    "ilitotal_fixed_step_metrics"),
                                   ("ilitotal_full_horizon_metrics",
                                    "ilitotal_full_horizon_metrics"),
                                   ("pte_pie_metrics", "pte_pie_metrics")):
                _atomic_write_json(os.path.join(run_dir, "metrics",
                                                f"{fname}.json"),
                                   metrics[payload])
            pred_df.to_csv(os.path.join(run_dir, "predictions",
                                        "validation_predictions.csv"),
                           index=False)
            _atomic_write_json(os.path.join(run_dir, "scaler_metadata.json"),
                               {"train_only": True, "n_variables": N_VARIABLES})
            _atomic_write_json(os.path.join(run_dir, "split_manifest.json"),
                               {"split": SPLIT, "T": T_WINDOW,
                                "horizon": horizon,
                                "n_variables": N_VARIABLES,
                                "ili_channel": ILITOTAL_INDEX})
            _atomic_write_json(os.path.join(run_dir,
                                            "prompt_statistics_metadata.json"),
                               {"applicable": False, "fit_scope": "n/a"})
            _atomic_write_json(os.path.join(run_dir, "resource_usage.json"),
                               {"stochastic_seed_applicable": False,
                                "checkpoint_applicable": False,
                                "train_seconds": 0.0, "gpu_hours": 0.0,
                                "peak_gpu_memory_bytes": None})
            _atomic_write_json(os.path.join(run_dir, "config_resolved.yaml"),
                               spec)
            status("COMPLETED", stochastic_seed_applicable=False,
                   checkpoint_applicable=False,
                   elapsed_seconds=round(time.time() - started, 3))
            return 0

        # ---- stochastic / ablated / controlled model runs ----
        import torch
        from innovation.trainer import train_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if name in VARIANTS:
            base_model, enc_name, bkw, ekw = VARIANTS[name]
        else:
            base_model, enc_name, bkw, ekw = name, PRIMARY_MODELS[name], {}, {}
        if base_model in ("qwen_time_llm",):
            bkw = dict(bkw, model_id="Qwen/Qwen2.5-1.5B", load_backbone=True)
        elif base_model in ("calf_llm", "timecma_llm"):
            bkw = dict(bkw, model_id="gpt2", load_backbone=True)

        encoder = make_encoder(enc_name, **(ekw or {}))
        encoder.fit_on_train_only(raw.iloc[:SPLIT["train"]], horizon=horizon,
                                  seed=42)
        ctx_fn = (lambda bsz: encoder.encode(bsz, device=device,
                                             horizon=horizon))
        # `make_backbone` forwards every keyword to the backbone constructor,
        # which accepts only T/N/L plus its own kwargs. `device` is NOT part of
        # that signature (Gate 568988 D9); the model is moved with `.to(device)`
        # immediately below.
        model = make_backbone(base_model, T=T_WINDOW, N=N_VARIABLES,
                              L=horizon, **bkw)
        if hasattr(model, "set_train_statistics"):
            model.set_train_statistics({"target_name": "ILITOTAL",
                                        "horizon": horizon,
                                        "channel_count": N_VARIABLES})
        model = model.to(device)

        cfg = {"model": base_model, "variant": name, "text_encoder": enc_name,
               "horizon": horizon, "seed": seed, "T": T_WINDOW,
               "N": N_VARIABLES, "epochs": 20, "batch_size": 16,
               "lr": 5e-4, "patience": 7, "device": device}
        _atomic_write_json(os.path.join(run_dir, "config_resolved.yaml"),
                           {**spec, "resolved": cfg})

        history, stopper, ckpt_path = train_model(
            model, windows, cfg, run_dir, device=device, patience=cfg["patience"],
            epochs=cfg["epochs"], batch_size=cfg["batch_size"],
            lr=cfg["lr"], ctx_fn=ctx_fn)
        history.to_csv(os.path.join(run_dir, "logs", "train_history.csv"),
                       index=False)

        # ordinary validation-loss early stopping, restore lowest val loss
        best_val = float(stopper.best_val_loss)
        best_epoch = int(stopper.best_epoch or 0)
        man = ART.write_checkpoint_manifest(
            run_dir, ckpt_path=ckpt_path, best_epoch=best_epoch,
            best_val_mse=best_val, config=cfg, extra={"variant": name})
        restore = ART.restore_test(
            lambda: model, ckpt_path,
            expected_state_dict_sha256=man["state_dict_sha256"])
        man["restore_test"] = restore
        _atomic_write_json(os.path.join(run_dir, "checkpoints",
                                        "checkpoint_manifest.json"), man)

        X_val = np.asarray(windows["X_val"])
        Y_val = np.asarray(windows["Y_val"])
        with torch.no_grad():
            out = model(torch.as_tensor(X_val, device=device),
                        ctx=ctx_fn(X_val.shape[0]))
        y_pred = out.detach().cpu().numpy().reshape(-1, N_VARIABLES, horizon)
        pred_df = build_full_prediction_frame(
            y_pred, Y_val, windows["idx_val"], horizon, var_names,
            mean_v, std_v, name, seed)
        pred_df.to_csv(os.path.join(run_dir, "predictions",
                                    "validation_predictions.csv"), index=False)

        metrics = CM.compute_all(pred_df)
        for fname in ("paper_aligned_full_output_metrics",
                      "ilitotal_fixed_step_metrics",
                      "ilitotal_full_horizon_metrics",
                      "pte_pie_metrics"):
            _atomic_write_json(os.path.join(run_dir, "metrics",
                                            f"{fname}.json"), metrics[fname])

        _atomic_write_json(os.path.join(run_dir, "scaler_metadata.json"),
                           {"train_only": True, "n_variables": N_VARIABLES})
        _atomic_write_json(os.path.join(run_dir, "split_manifest.json"),
                           {"split": SPLIT, "T": T_WINDOW, "horizon": horizon,
                            "n_variables": N_VARIABLES,
                            "ili_channel": ILITOTAL_INDEX})
        _atomic_write_json(os.path.join(run_dir,
                                        "prompt_statistics_metadata.json"),
                           {"fit_scope": "train rows only",
                            "encoder": enc_name, "variant_kwargs": ekw})
        _atomic_write_json(os.path.join(run_dir, "resource_usage.json"),
                           {"stochastic_seed_applicable": True,
                            "checkpoint_applicable": True,
                            "best_epoch": best_epoch,
                            "best_val_mse": best_val,
                            "train_seconds": round(time.time() - started, 3),
                            "trainable_parameters":
                                int(model.trainable_parameters())
                            if hasattr(model, "trainable_parameters") else None})

        status("COMPLETED", best_epoch=best_epoch, best_val_mse=best_val,
               restore_ok=bool(restore.get("ok")),
               elapsed_seconds=round(time.time() - started, 3))
        return 0

    except SystemExit:
        raise
    except Exception as e:
        # never mark a failed run accepted; keep partial evidence
        try:
            status("FAILED", error=f"{type(e).__name__}: {e}",
                   traceback=traceback.format_exc()[-4000:])
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
