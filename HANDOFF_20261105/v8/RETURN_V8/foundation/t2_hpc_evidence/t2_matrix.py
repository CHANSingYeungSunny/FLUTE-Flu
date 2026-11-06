#!/usr/bin/env python3
"""TASK 2 step 5 — smallest FAITHFUL subset of the 80-cell foundation matrix.

WHY NOT 80 CELLS (documented, not hidden):
  The handoff asks for `2 models x 4 L x 10 seeds = 80` cells. Both named
  checkpoints are FROZEN ZERO-SHOT forecasters: there is no training step and no
  model fit, so a "seed" cannot produce a distinct model. Repeating each cell with
  10 different RNG seeds would yield 10 byte-identical predictions and would
  fabricate a seed dimension that does not exist. We therefore run the smallest
  faithful subset the models actually support: 2 models x 4 horizons = 8 distinct
  deterministic zero-shot cells, each with real predictions + measured resources.
  The 10-seed expansion is recorded as NOT_EXECUTED_BY_PROTOCOL with this reason.

ADAPTER (documented limits, see FOUNDATION_MODEL_PROVENANCE.md):
  Both checkpoints are UNIVARIATE. The 7 benchmark channels are passed as a BATCH
  of 7 independent series (per-channel independent forecasting). This discards all
  cross-channel dependence, so these controls are NOT information-set matched to
  the multivariate arms. Each model applies its own internal normalization; the
  benchmark standardized z-space is passed through and used as-is.

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
OUT = f"{BASE}/matrix_out"
WORK = f"{BASE}/extracted"
DATA = f"{ROOT}/data/raw/national_illness_author_repo_966.csv"
SCALER = f"{ROOT}/data/scaler_miflu_author966.json"
T, SEED = 104, 2021
LS = [24, 36, 48, 60]
os.makedirs(OUT, exist_ok=True)

CHRONOS_DIR = f"{WORK}/chronos_bolt_tiny/chronos_bolt_tiny"
TFM_CKPT = f"{WORK}/timesfm_2_0_500m_pytorch/timesfm_2_0_500m_pytorch/torch_model.ckpt"

torch.manual_seed(SEED)
np.random.seed(SEED)

df = pd.read_csv(DATA)
cols = [c for c in df.columns if c != "date"]
X = df[cols].to_numpy(dtype=np.float64)
sc = json.load(open(SCALER))
Z = (X - np.asarray(sc["mean"], dtype=np.float64)) / np.asarray(sc["std"], dtype=np.float64)
test_start = int(sc["val_end"])
context = Z[test_start - T:test_start]                 # (104,7)
ctx_t = torch.tensor(context.T, dtype=torch.float32)  # (7,104)
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("DEVICE", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "NONE", flush=True)

rows = []
meta = {
    "protocol": "frozen zero-shot; smallest faithful subset = 2 models x 4 L = 8 cells",
    "requested_80_cells": "NOT_EXECUTED_BY_PROTOCOL",
    "reason": "no training seed dimension in a frozen zero-shot model; 10 seeds would produce 10 identical predictions",
    "adapter": "per-channel independent univariate forecasting (2-D input = batch)",
    "adapter_limits": ["discards cross-channel dependence",
                       "model applies its own internal scaling; benchmark z-space passed through"],
    "T": T, "seed": SEED, "test_start_row": test_start,
    "data_file": DATA, "scaler": SCALER, "var_cols": cols,
    "torch": torch.__version__,
    "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else "NONE",
    "chronos": {"repo_id": "amazon/chronos-bolt-tiny",
                "revision": "a0e552de83495b5c28c14c71c374f3e33280b340",
                "licence": "apache-2.0", "package": "chronos-forecasting 2.3.2"},
    "timesfm": {"repo_id": "google/timesfm-2.0-500m-pytorch",
                "revision": "dc2443792ce5516872b89b37cf1bc058c3bf0c10",
                "licence": "apache-2.0", "package": "timesfm 1.3.0"},
}


def record(label, repo_id, L, pred_l7, wall_s, load_s, latency_ms, extra=None):
    """pred_l7: (L,7) point forecast; returns one validated cell row."""
    target = Z[test_start:test_start + L]              # (L,7)
    finite = bool(np.isfinite(pred_l7).all())
    mse = float(np.mean((pred_l7 - target) ** 2)) if finite else ""
    mae = float(np.mean(np.abs(pred_l7 - target))) if finite else ""
    status = "ok" if finite else "invalid_nonfinite"
    tag = f"{label}_L{L}_s{SEED}"
    np.savez(f"{OUT}/pred_{tag}.npz",
             pred=pred_l7.astype(np.float32), target=target.astype(np.float32),
             model=np.array(repo_id), L=np.array(L), seed=np.array(SEED),
             space=np.array("standardized_train_fit_z"),
             adapter=np.array("per_channel_independent_univariate"),
             label=np.array(label), var_cols=np.array(cols))
    r = {"label": label, "repo_id": repo_id, "L": L, "seed": SEED, "T": T,
         "mse_7var_z": mse, "mae_7var_z": mae, "all_finite": finite,
         "status": status, "wall_s": round(wall_s, 4), "load_s": round(load_s, 4),
         "inference_latency_ms": round(latency_ms, 3), "device": dev,
         "scope": "foundation_zero_shot_subset_not_1120_panel",
         "npz": f"pred_{tag}.npz"}
    if extra:
        r.update(extra)
    rows.append(r)
    print("CELL", json.dumps(r), flush=True)
    return r


# ---------------- Chronos Bolt Tiny (univariate, max prediction 64) ----------
t0 = time.perf_counter()
cp = ChronosBoltPipeline.from_pretrained(CHRONOS_DIR, local_files_only=True,
                                         device_map=dev)
chronos_load = time.perf_counter() - t0
for L in LS:
    t1 = time.perf_counter()
    q = cp.predict(ctx_t, prediction_length=L)
    if dev == "cuda":
        torch.cuda.synchronize()
    wall = time.perf_counter() - t1
    point = q[:, q.shape[1] // 2, :].detach().float().cpu().numpy().T  # (L,7)
    record("foundation_chronos", "amazon/chronos-bolt-tiny", L, point,
           wall, chronos_load, wall * 1000.0,
           {"quantile_shape": list(q.shape), "point_estimator": "median quantile"})
del cp
if dev == "cuda":
    torch.cuda.empty_cache()

# ---------------- TimesFM 2.0-500m PyTorch (univariate, any horizon) ---------
if not os.path.isfile(TFM_CKPT):
    print("TIMESFM_CHECKPOINT_MISSING", TFM_CKPT, flush=True)
    for L in LS:
        rows.append({"label": "foundation_timesfm",
                     "repo_id": "google/timesfm-2.0-500m-pytorch", "L": L,
                     "seed": SEED, "status": "BLOCKED_missing_ckpt",
                     "scope": "foundation_zero_shot_subset_not_1120_panel"})
else:
    t0 = time.perf_counter()
    hp = timesfm.TimesFmHparams(
        backend="gpu" if dev == "cuda" else "cpu", per_core_batch_size=32,
        horizon_len=128, context_len=512, input_patch_len=32,
        output_patch_len=128, num_layers=50, model_dims=1280,
        use_positional_embedding=False)
    ck = timesfm.TimesFmCheckpoint(version="torch", path=TFM_CKPT)
    tfm = timesfm.TimesFm(hparams=hp, checkpoint=ck)
    timesfm_load = time.perf_counter() - t0
    inputs = [context[:, c] for c in range(7)]          # 7 independent series
    freqs = [1] * 7                                     # 1 = weekly/medium
    try:
        mean_fc, full_fc = tfm.forecast(inputs, freq=freqs)
        mean_fc = np.asarray(mean_fc)
        print("TIMESFM_FORECAST_OK", mean_fc.shape, np.asarray(full_fc).shape, flush=True)
        t_all = time.perf_counter()
        for L in LS:
            t1 = time.perf_counter()
            point_l7 = mean_fc[:, :L].T                  # (L,7)
            wall = time.perf_counter() - t1
            record("foundation_timesfm", "google/timesfm-2.0-500m-pytorch", L,
                   point_l7, wall, timesfm_load, (time.perf_counter() - t_all) * 1000.0,
                   {"forecast_shape": list(mean_fc.shape),
                    "freq_indicator": 1,
                    "point_estimator": "TimesFM mean forecast (horizon_len=128, sliced to L)"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        for L in LS:
            rows.append({"label": "foundation_timesfm",
                         "repo_id": "google/timesfm-2.0-500m-pytorch", "L": L,
                         "seed": SEED, "status": "BLOCKED_forecast_error",
                         "error": type(e).__name__ + ": " + str(e)[:200],
                         "scope": "foundation_zero_shot_subset_not_1120_panel"})

with open(f"{OUT}/FOUNDATION_CELLS.csv", "w", newline="", encoding="utf-8") as fh:
    fields = sorted({k for r in rows for k in r})
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
meta["cells"] = len(rows)
meta["ok_cells"] = sum(1 for r in rows if r.get("status") == "ok")
with open(f"{OUT}/FOUNDATION_MATRIX_REPORT.json", "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
print("MATRIX_SUMMARY", json.dumps({"cells": meta["cells"], "ok": meta["ok_cells"]}), flush=True)
