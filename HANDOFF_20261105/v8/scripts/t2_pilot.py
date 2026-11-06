#!/usr/bin/env python3
"""TASK 2 pilot: 1 model x L24 x seed 2021 on an A100 compute node.

FAITHFUL ADAPTER (documented, with limits):
  Chronos / TimesFM checkpoints named in the handoff are UNIVARIATE. The benchmark
  has 7 standardized channels, so each channel is forecast INDEPENDENTLY (the
  model's 2-D input is a BATCH of series, not a variate axis). This discards all
  cross-channel dependence and is therefore NOT an information-set-matched control
  against the multivariate arms. Each model also applies its own internal scaling,
  so the benchmark z-space is passed through and the output is used as-is; the
  mismatch is recorded, not silently corrected.

  Frozen zero-shot models have NO training seed, so `seed=2021` only fixes
  torch/numpy RNG state for reproducibility; it does not create a new model fit.
  Reported honestly, never used to manufacture 10 distinct "seed" cells.

Runs ONLY inside sbatch on a GPU compute node (AGENTS.md RULE 1).
"""
import json
import os
import time

import numpy as np
import pandas as pd
import torch

from chronos import ChronosBoltPipeline

ROOT = "/gpfs1/scratch/sychan552/stage5_a2_durable"
OUT = f"{ROOT}/code/queue/t2_fm/pilot_out"
MODEL_DIR = f"{ROOT}/code/queue/t2_fm/extracted/chronos_bolt_tiny/chronos_bolt_tiny"
DATA = f"{ROOT}/data/raw/national_illness_author_repo_966.csv"
SCALER = f"{ROOT}/data/scaler_miflu_author966.json"
T, L, SEED = 104, 24, 2021
MODEL_ID = "amazon/chronos-bolt-tiny"
REVISION = "a0e552de83495b5c28c14c71c374f3e33280b340"  # tree id in extracted .cache metadata
os.makedirs(OUT, exist_ok=True)

torch.manual_seed(SEED)
np.random.seed(SEED)
res = {"model": MODEL_ID, "revision": REVISION, "L": L, "T": T, "seed": SEED,
       "adapter": "per-channel independent univariate forecasting (2-D input = batch)",
       "adapter_limits": ["discards cross-channel dependence",
                          "model applies its own internal scaling; benchmark z-space passed through",
                          "frozen zero-shot model has no training seed dimension"],
       "device": None, "status": "NOT_EXECUTED"}

# ---- benchmark data: 966 weekly rows x 7 channels, train-only z-scaler ----
df = pd.read_csv(DATA)
cols = [c for c in df.columns if c != "date"]
assert len(cols) == 7, cols
X = df[cols].to_numpy(dtype=np.float64)
sc = json.load(open(SCALER))
mean = np.asarray(sc["mean"], dtype=np.float64)
std = np.asarray(sc["std"], dtype=np.float64)
Z = (X - mean) / std
test_start = int(sc["val_end"])            # 773
assert Z.shape[0] >= test_start + L
context = Z[test_start - T:test_start]      # (104, 7)
target = Z[test_start:test_start + L]       # (24, 7)
res["data"] = {"file": DATA, "rows": int(Z.shape[0]), "channels": list(cols),
               "test_start_row": test_start, "scaler": SCALER,
               "context_shape": list(context.shape), "target_shape": list(target.shape)}

# ---- load pinned UNIVARIATE checkpoint OFFLINE on the allocated GPU ----
dev = "cuda" if torch.cuda.is_available() else "cpu"
res["device"] = dev
res["torch"] = torch.__version__
res["gpu_name"] = torch.cuda.get_device_name(0) if dev == "cuda" else "NONE"
t0 = time.perf_counter()
pipe = ChronosBoltPipeline.from_pretrained(MODEL_DIR, local_files_only=True,
                                           device_map=dev)
res["load_wall_s"] = round(time.perf_counter() - t0, 4)
print("MODEL_LOADED", MODEL_ID, "device", dev, "load_wall_s", res["load_wall_s"], flush=True)

# batch of 7 independent 1-D series -> (7, 9, L) quantiles
ctx = torch.tensor(context.T, dtype=torch.float32)   # (7,104)

# warm-up + repeated latency (measured on the SAME single cell)
pipe.predict(ctx[:1], prediction_length=L)           # warm-up
lat = []
for _ in range(5):
    t1 = time.perf_counter()
    q = pipe.predict(ctx, prediction_length=L)
    if dev == "cuda":
        torch.cuda.synchronize()
    lat.append((time.perf_counter() - t1) * 1000.0)
res["inference_latency_ms"] = {"warmup_runs": 1, "repeat_runs": 5,
                               "mean": round(float(np.mean(lat)), 3),
                               "std": round(float(np.std(lat)), 3),
                               "all_runs": [round(x, 3) for x in lat]}
pred = q[:, q.shape[1] // 2, :].detach().float().cpu().numpy()   # median quantile (7,L)
pred7 = pred.T                                                    # (L,7) to match target
finite = bool(np.isfinite(pred7).all())
mse = float(np.mean((pred7 - target) ** 2)) if finite else None
mae = float(np.mean(np.abs(pred7 - target))) if finite else None
res["predictions"] = {"quantile_shape": list(q.shape), "point_shape": list(pred7.shape),
                      "all_finite": finite, "mse_7var_z": mse, "mae_7var_z": mae,
                      "point_estimator": "median quantile (index q.shape[1]//2)"}
res["status"] = "COMPLETED" if finite else "FAILED_NONFINITE"

np.savez(f"{OUT}/pred_foundation_chronos_bolt_tiny_L24_s2021.npz",
         pred=pred7.astype(np.float32), target=target.astype(np.float32),
         model=np.array(MODEL_ID), L=np.array(L), seed=np.array(SEED),
         fold=np.array("national_common_panel"),
         space=np.array("standardized_train_fit_z"),
         adapter=np.array("per_channel_independent_univariate"),
         var_cols=np.array(cols))
with open(f"{OUT}/pilot_result.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2)
print("PILOT_RESULT", json.dumps(res, indent=2), flush=True)
print("PILOT_STATUS", res["status"], flush=True)
