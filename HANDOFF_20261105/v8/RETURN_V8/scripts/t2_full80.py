#!/usr/bin/env python3
"""TASK 2 step 5 — FULL 80-cell foundation matrix with measured resources.

PROTOCOL NOTE (honest, not hidden):
  The handoff asks for `2 models x 4 L x 10 seeds = 80` cells. Both checkpoints are
  FROZEN ZERO-SHOT forecasters: there is no training step, so a training seed cannot
  produce a distinct model. Repeating one origin 10 times with different RNG seeds
  would yield 10 byte-identical predictions and would fabricate a seed dimension.
  We therefore use 10 DISTINCT FORECAST ORIGINS (rolling-origin replicates) as the
  10 real, non-degenerate replicates. Each cell has its own context window and its
  own target, so all 80 predictions and scores are genuinely different.
  `seed_semantics=NOT_APPLICABLE`; the literal 10-seed expansion remains
  `NOT_EXECUTED_BY_PROTOCOL`. `origin_index=0..9`, `origin_row=773..782`.

ADAPTER (limits recorded): both checkpoints are UNIVARIATE. The 7 benchmark channels
  are passed as a BATCH of 7 independent series (per-channel independent forecasting),
  which DISCARDS cross-channel dependence and is NOT information-set matched to the
  multivariate arms. Each model applies its own internal normalization; the benchmark
  standardized z-space is passed through unchanged. No training / fine-tuning.

Runs ONLY inside sbatch on an A100 compute node (AGENTS.md RULE 1).
"""
import csv
import json
import os
import time

import numpy as np
import pandas as pd
import torch

from chronos import ChronosBoltPipeline
import timesfm

ROOT = "/gpfs1/scratch/sychan552/stage5_a2_durable"
BASE = f"{ROOT}/code/queue/t2_fm"
OUT = f"{BASE}/full80_out"
WORK = f"{BASE}/extracted"
DATA = f"{ROOT}/data/raw/national_illness_author_repo_966.csv"
SCALER = f"{ROOT}/data/scaler_miflu_author966.json"
T = 104
LS = [24, 36, 48, 60]
ORIGINS = list(range(773, 783))          # 10 distinct forecast origins
os.makedirs(OUT, exist_ok=True)

CHRONOS_DIR = f"{WORK}/chronos_bolt_tiny/chronos_bolt_tiny"
TFM_CKPT = f"{WORK}/timesfm_2_0_500m_pytorch/timesfm_2_0_500m_pytorch/torch_model.ckpt"

torch.manual_seed(2021)
np.random.seed(2021)

df = pd.read_csv(DATA)
cols = [c for c in df.columns if c != "date"]
X = df[cols].to_numpy(dtype=np.float64)
sc = json.load(open(SCALER))
Z = (X - np.asarray(sc["mean"], dtype=np.float64)) / np.asarray(sc["std"], dtype=np.float64)
assert Z.shape[0] >= max(ORIGINS) + max(LS), "not enough rows for the last origin"
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("DEVICE", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "NONE", flush=True)

rows = []
meta = {
    "matrix": "2 models x 4 L x 10 origins = 80 cells",
    "labels": ["foundation_chronos", "foundation_timesfm"],
    "seed_semantics": "NOT_APPLICABLE — frozen zero-shot model has no training seed dimension",
    "literal_10_seed_expansion": "NOT_EXECUTED_BY_PROTOCOL",
    "replicate_kind": "rolling_origin (10 distinct forecast origins, each with its own target)",
    "origins": ORIGINS, "L_values": LS, "T": T,
    "adapter": "per-channel independent univariate forecasting (2-D input = batch of 7 series)",
    "adapter_limits": ["discards cross-channel dependence",
                       "NOT information-set matched to the multivariate arms",
                       "model applies its own internal scaling; benchmark z-space passed through"],
    "separate_roster": True, "merged_into_28_arm_family": False,
    "data_file": DATA, "scaler": SCALER, "var_cols": cols,
    "torch": torch.__version__,
    "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else "NONE",
    "chronos": {"repo_id": "amazon/chronos-bolt-tiny",
                "revision": "a0e552de83495b5c28c14c71c374f3e33280b340",
                "licence": "apache-2.0", "package": "chronos-forecasting 2.3.2"},
    "timesfm": {"repo_id": "google/timesfm-2.0-500m-pytorch",
                "revision": "dc2443792ce5516872b89b37cf1bc058c3bf0c10",
                "licence": "apache-2.0", "package": "timesfm 1.3.0",
                "freq_indicator": 1, "horizon_len": 128},
}


def sync():
    if dev == "cuda":
        torch.cuda.synchronize()


def cell(label, repo_id, L, k, origin, pred_l7, wall_ms, extra=None):
    target = Z[origin:origin + L]
    finite = bool(np.isfinite(pred_l7).all())
    mse = float(np.mean((pred_l7 - target) ** 2)) if finite else ""
    mae = float(np.mean(np.abs(pred_l7 - target))) if finite else ""
    tag = f"{label}_L{L}_o{k}"
    np.savez(f"{OUT}/pred_{tag}.npz",
             pred=pred_l7.astype(np.float32), target=target.astype(np.float32),
             model=np.array(repo_id), label=np.array(label), L=np.array(L),
             origin_index=np.array(k), origin_row=np.array(origin),
             seed_semantics=np.array("NOT_APPLICABLE"),
             replicate_kind=np.array("rolling_origin"),
             space=np.array("standardized_train_fit_z"),
             adapter=np.array("per_channel_independent_univariate"),
             var_cols=np.array(cols))
    r = {"label": label, "repo_id": repo_id, "L": L, "origin_index": k,
         "origin_row": origin, "T": T, "seed_semantics": "NOT_APPLICABLE",
         "replicate_kind": "rolling_origin", "mse_7var_z": mse, "mae_7var_z": mae,
         "all_finite": finite, "status": "ok" if finite else "invalid_nonfinite",
         "cell_wall_ms": round(wall_ms, 3), "device": dev,
         "scope": "foundation_zero_shot_80cells_not_1120_panel",
         "npz": f"pred_{tag}.npz"}
    if extra:
        r.update(extra)
    rows.append(r)
    return r


# ------------------------- Chronos Bolt Tiny --------------------------------
t0 = time.perf_counter()
cp = ChronosBoltPipeline.from_pretrained(CHRONOS_DIR, local_files_only=True,
                                         device_map=dev)
chronos_load_s = time.perf_counter() - t0
ctx0 = torch.tensor(Z[ORIGINS[0] - T:ORIGINS[0]].T, dtype=torch.float32)
cp.predict(ctx0[:1], prediction_length=LS[0])   # warm-up
lat = []
for _ in range(10):
    t1 = time.perf_counter()
    cp.predict(ctx0, prediction_length=LS[0])
    sync()
    lat.append((time.perf_counter() - t1) * 1000.0)
chronos_lat = {"warmup_runs": 1, "repeat_runs": 10,
               "mean_ms": round(float(np.mean(lat)), 3),
               "std_ms": round(float(np.std(lat)), 3)}
print("CHRONOS_LATENCY", json.dumps(chronos_lat), flush=True)

t_start = time.perf_counter()
for k, origin in enumerate(ORIGINS):
    ctx = torch.tensor(Z[origin - T:origin].T, dtype=torch.float32)
    for L in LS:
        t1 = time.perf_counter()
        q = cp.predict(ctx, prediction_length=L)
        sync()
        wall = (time.perf_counter() - t1) * 1000.0
        point = q[:, q.shape[1] // 2, :].detach().float().cpu().numpy().T
        cell("foundation_chronos", "amazon/chronos-bolt-tiny", L, k, origin,
             point, wall, {"point_estimator": "median quantile"})
chronos_wall_s = time.perf_counter() - t_start
print("CHRONOS_CELLS_DONE", len(rows), "wall_s", round(chronos_wall_s, 3), flush=True)
del cp
if dev == "cuda":
    torch.cuda.empty_cache()

# ------------------------- TimesFM 2.0-500m PyTorch -------------------------
tfm = None
if not os.path.isfile(TFM_CKPT):
    print("TIMESFM_CHECKPOINT_MISSING", TFM_CKPT, flush=True)
    for k, origin in enumerate(ORIGINS):
        for L in LS:
            rows.append({"label": "foundation_timesfm", "repo_id": "google/timesfm-2.0-500m-pytorch",
                         "L": L, "origin_index": k, "origin_row": origin,
                         "status": "BLOCKED_missing_ckpt",
                         "scope": "foundation_zero_shot_80cells_not_1120_panel"})
else:
    t0 = time.perf_counter()
    hp = timesfm.TimesFmHparams(
        backend="gpu" if dev == "cuda" else "cpu", per_core_batch_size=32,
        horizon_len=128, context_len=512, input_patch_len=32, output_patch_len=128,
        num_layers=50, model_dims=1280, use_positional_embedding=False)
    ck = timesfm.TimesFmCheckpoint(version="torch", path=TFM_CKPT)
    tfm = timesfm.TimesFm(hparams=hp, checkpoint=ck)
    timesfm_load_s = time.perf_counter() - t0
    inputs0 = [Z[ORIGINS[0] - T:ORIGINS[0], c] for c in range(7)]
    tfm.forecast(inputs0, freq=[1] * 7)        # warm-up
    lat2 = []
    for _ in range(5):
        t1 = time.perf_counter()
        tfm.forecast(inputs0, freq=[1] * 7)
        sync()
        lat2.append((time.perf_counter() - t1) * 1000.0)
    timesfm_lat = {"warmup_runs": 1, "repeat_runs": 5,
                   "mean_ms": round(float(np.mean(lat2)), 3),
                   "std_ms": round(float(np.std(lat2)), 3)}
    print("TIMESFM_LATENCY", json.dumps(timesfm_lat), flush=True)

    t_start = time.perf_counter()
    for k, origin in enumerate(ORIGINS):
        inputs = [Z[origin - T:origin, c] for c in range(7)]
        t1 = time.perf_counter()
        mean_fc, _full = tfm.forecast(inputs, freq=[1] * 7)
        sync()
        forecast_ms = (time.perf_counter() - t1) * 1000.0
        mean_fc = np.asarray(mean_fc)
        for L in LS:
            point = mean_fc[:, :L].T
            # slicing is not a separate forward; record the shared call's wall once
            cell("foundation_timesfm", "google/timesfm-2.0-500m-pytorch", L, k,
                 origin, point, forecast_ms,
                 {"point_estimator": "TimesFM mean forecast (horizon_len=128 sliced to L)",
                  "forecast_call_wall_ms": round(forecast_ms, 3),
                  "timing_note": "one shared forecast call per origin; L-slices are not separate forwards"})
    timesfm_wall_s = time.perf_counter() - t_start
    print("TIMESFM_CELLS_DONE", len(rows), "wall_s", round(timesfm_wall_s, 3), flush=True)

meta["resources"] = {
    "chronos": {"load_s": round(chronos_load_s, 4),
                "inference_latency": chronos_lat,
                "matrix_wall_s": round(chronos_wall_s, 3),
                "batch": "7 independent series per call", "precision": "float32"},
    "timesfm": {"load_s": round(timesfm_load_s, 4) if tfm is not None else None,
                "inference_latency": timesfm_lat if tfm is not None else None,
                "matrix_wall_s": round(timesfm_wall_s, 3) if tfm is not None else None,
                "batch": "7 independent series per call", "precision": "float32"},
    "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else "NONE",
    "peak_vram_mib": "from slurm job nvidia-smi sampling (see slurm stdout)",
}

with open(f"{OUT}/FOUNDATION_80_CELLS.csv", "w", newline="", encoding="utf-8") as fh:
    fields = sorted({k for r in rows for k in r})
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
meta["cells"] = len(rows)
meta["ok_cells"] = sum(1 for r in rows if r.get("status") == "ok")
meta["npz_files"] = len([f for f in os.listdir(OUT) if f.endswith(".npz")])
with open(f"{OUT}/FOUNDATION_80_REPORT.json", "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
print("FULL80_SUMMARY", json.dumps({"cells": meta["cells"], "ok": meta["ok_cells"],
                                   "npz": meta["npz_files"]}), flush=True)
