"""verify_restoration.py — compute-node restoration verification.

For the default cell of EVERY model family (L24 / seed42) this:
  1. rebuilds the model exactly as the runner does;
  2. restores the ACCEPTED durable checkpoint;
  3. re-runs validation prediction;
  4. compares against the SAVED durable predictions.

Acceptance (preregistered):
    max_abs_prediction_diff (z-space)      <= 1e-5
    relative full-horizon MSE difference   <= 1e-6

Runs ONLY on a compute node (loads a real model). Never reads Test/holdout.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

ROOT = os.path.abspath(os.environ.get("INNOVATION_DEPLOYMENT_ROOT", "."))
if os.path.join(ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "scripts"))

import innovation.runner as R                      # noqa: E402
from innovation import metrics as MET               # noqa: E402
from innovation.data_pipeline import (N, T, build_windows, load_raw_df,  # noqa: E402
                                      load_scaler, normalize, to_array)
from innovation.trainer import predict_frame        # noqa: E402

DURABLE = os.environ.get("SCREENING_DURABLE",
                         "/home/sychan552/innovation_durable/screening")
OUT = os.path.join(DURABLE, "restoration_verification.json")
TOL_ABS = 1e-5
TOL_MSE_REL = 1e-6

MODELS = [
    ("nlinear", "none", "identity", None),
    ("dlinear", "none", "identity", None),
    ("patchtst", "none", "identity", None),
    ("itransformer", "none", "identity", None),
    ("gpt2_miflu", "gpt2", "concat-projection", None),
    ("qwen_time_llm", "none", "identity", "Qwen/Qwen2.5-1.5B"),
    ("calf_llm", "none", "identity", "gpt2"),
    ("timecma_llm", "none", "identity", "gpt2"),
]
HORIZON, SEED = 24, 42


def main() -> int:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    raw = load_raw_df()
    scaler = load_scaler()
    data = normalize(to_array(raw), scaler)
    w = build_windows(data, HORIZON)
    results = []
    for model, te, fusion, mid in MODELS:
        key = f"screening_{model}_L{HORIZON}_seed{SEED}"
        d = os.path.join(DURABLE, key)
        ckpt_path = os.path.join(d, "checkpoints", "best_val_mse.pt")
        saved_path = os.path.join(d, "predictions", "validation_predictions.csv")
        rec = {"run_key": key, "model": model, "checkpoint": ckpt_path}
        if not (os.path.exists(ckpt_path) and os.path.exists(saved_path)):
            rec.update({"passed": False, "error": "missing durable checkpoint or "
                                                  "saved predictions"})
            results.append(rec)
            print(f"[restore] {key}: MISSING")
            continue
        try:
            bk = ({"model_id": mid, "load_backbone": True} if mid else None)
            m, enc, ctx_fn = R.build_components(
                model, te, fusion, HORIZON, device,
                raw.iloc[:scaler.train_end], d_model=64, backbone_kwargs=bk)
            m = m.to(device)
            # The runner sets the train-only Prompt-as-Prefix statistics before
            # the first forward pass (qwen_time_llm requires them). The
            # verification harness must reproduce that exactly, otherwise the
            # forward raises "train-only Prompt-as-Prefix statistics were not
            # set". This is a harness gap, not a model/data/defect of the run.
            if hasattr(m, "set_train_statistics"):
                m.set_train_statistics({"target_name": "ILITOTAL",
                                        "horizon": HORIZON,
                                        "channel_count": int(N)})
            obj = torch.load(ckpt_path, map_location=device)
            sd = None
            if isinstance(obj, dict):
                for k in ("model_state_dict", "state_dict", "model"):
                    if isinstance(obj.get(k), dict):
                        sd = obj[k]
                        break
            if sd is None and isinstance(obj, dict) and obj and all(
                    isinstance(v, torch.Tensor) for v in obj.values()):
                sd = obj
            if sd is None:
                raise RuntimeError("unrecognised checkpoint payload; keys="
                                   f"{list(obj)[:8] if isinstance(obj, dict) else type(obj)}")
            missing, unexpected = m.load_state_dict(sd, strict=False)

            df = predict_frame(m, w["X_val"], w["Y_val"], w["idx_val"], T,
                               HORIZON, scaler, "val", device,
                               batch_size=16, ctx_fn=ctx_fn)
            z_new = df["prediction_ili"].to_numpy(dtype=float)
            saved = pd.read_csv(saved_path)
            z_old = saved["prediction_ili"].to_numpy(dtype=float)
            if len(z_new) != len(z_old):
                raise RuntimeError(f"row count mismatch new={len(z_new)} "
                                   f"saved={len(z_old)}")
            max_abs = float(np.max(np.abs(z_new - z_old)))
            mse_new = MET.mse(df["ground_truth_ili"].to_numpy(dtype=float), z_new)
            mse_old = MET.mse(saved["ground_truth_ili"].to_numpy(dtype=float), z_old)
            rel = abs(mse_new - mse_old) / mse_old if mse_old else float("inf")
            rec.update({
                "rows_compared": int(len(z_new)),
                "max_abs_prediction_diff": max_abs,
                "mse_restored": mse_new, "mse_saved": mse_old,
                "relative_full_horizon_mse_diff": rel,
                "tolerance": {"max_abs_prediction_diff": TOL_ABS,
                              "relative_full_horizon_mse_diff": TOL_MSE_REL},
                "missing_keys": list(missing)[:5], "unexpected_keys": list(unexpected)[:5],
                "passed": bool(max_abs <= TOL_ABS and rel <= TOL_MSE_REL),
            })
            print(f"[restore] {key}: max_abs={max_abs:.3e} rel_mse={rel:.3e} "
                  f"passed={rec['passed']}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            rec.update({"passed": False, "error": f"{type(e).__name__}: {e}"})
            print(f"[restore] {key}: ERROR {e}")
        results.append(rec)

    n_ok = sum(1 for r in results if r.get("passed"))
    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "node": os.environ.get("SLURMD_NODENAME"),
        "deployment_root": ROOT,
        "cells": f"default cell L{HORIZON}/seed{SEED} for every architecture family",
        "n_families": len(results), "n_passed": n_ok,
        "all_passed": n_ok == len(results),
        "tolerance": {"max_abs_prediction_diff": TOL_ABS,
                      "relative_full_horizon_mse_diff": TOL_MSE_REL},
        "device": device,
        "test_access_count": 0, "holdout_access_count": 0,
        "results": results,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    md = ["# Restoration verification (compute node)", "",
          f"Generated {payload['generated_utc']} · job {payload['slurm_job_id']} · "
          f"node {payload['node']} · device {device}", "",
          f"**{n_ok}/{len(results)} families passed** "
          f"(`max_abs <= {TOL_ABS}`, `rel_mse <= {TOL_MSE_REL}`).", "",
          "| run_key | rows | max_abs_diff | rel MSE diff | passed |",
          "|---|---|---|---|---|"]
    for r in results:
        md.append("| `{}` | {} | {} | {} | {} |".format(
            r["run_key"], r.get("rows_compared", "-"),
            ("%.3e" % r["max_abs_prediction_diff"]) if "max_abs_prediction_diff" in r else "-",
            ("%.3e" % r["relative_full_horizon_mse_diff"]) if "relative_full_horizon_mse_diff" in r else "-",
            r.get("passed")))
    md += ["", "Only ACCEPTED durable checkpoints were restored; no Screening cell "
           "was re-run. Test/holdout access counts remain 0/0.", ""]
    with open(os.path.join(DURABLE, "restoration_verification.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"[restore] families_passed={n_ok}/{len(results)} -> {OUT}")
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
