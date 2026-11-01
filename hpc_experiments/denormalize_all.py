#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""denormalize_all.py — User requirement #1: denormalize MSE to physical units.

The 7-variable aggregate MSE CANNOT be denormalized with a single scaler (the 7
variables have different scales). The valid denormalization is PER-VARIABLE:

    MSE_physical_j = MSE_z_j * std_j^2
    MAE_physical_j = MAE_z_j * std_j

This reports "actual performance" in real units for every variable of every model.

Sources:
  * MIFlu   : miflu_strict966__* CSVs  (verified: all-7 aggregate == 1.8652)
  * 7 bases : stage6 pred_<model>_L<L>_s<seed>.npz (verified == Track C)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re

import numpy as np
import pandas as pd

SCALER = "/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/inputs/handoff/03_data/scaler_miflu_author966.json"
OUT_DIR = "/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/paper_tables"

with open(SCALER, encoding="utf-8") as f:
    S = json.load(f)
VARS = S["var_cols"]
STD = S["std"]

BASE_MODELS = ["nlinear", "dlinear", "timecma_llm", "patchtst",
               "itransformer", "qwen_time_llm", "calf_llm"]
STAGE6 = "/home/sychan552/stage5_a2_durable/stage6/predictions"
MIFLU_CSV = "/home/sychan552/scratch/MLFLU/miflu_csv"

# cell -> {var_idx: [mse_z, mae_z]}
data = {}


def add(model, L, seed, mse_by_var, mae_by_var):
    data[(model, L, seed)] = (mse_by_var, mae_by_var)


# ---- MIFlu ----
for path in sorted(glob.glob(os.path.join(MIFLU_CSV, "miflu_strict966__*", "test_predictions_*.csv"))):
    df = pd.read_csv(path)
    if df.empty:
        continue
    m = re.search(r"miflu_strict966__L(\d+)__seed(\d+)", path)
    L, seed = int(m.group(1)), int(m.group(2))
    df["e2"] = (df["y_pred_z"].astype(float) - df["y_true_z"].astype(float)) ** 2
    df["ae"] = (df["y_pred_z"].astype(float) - df["y_true_z"].astype(float)).abs()
    mse_v, mae_v = {}, {}
    for i in range(7):
        sub = df[df["feature_index"].astype(int) == i]
        if sub.empty:
            continue
        mse_v[i] = float(sub["e2"].mean())
        mae_v[i] = float(sub["ae"].mean())
    add("miflu", L, seed, mse_v, mae_v)

# ---- baselines (stage6 npz) ----
for path in sorted(glob.glob(os.path.join(STAGE6, "pred_*.npz"))):
    m = re.match(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(path))
    if not m:
        continue
    model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
    if model not in BASE_MODELS:
        continue
    d = np.load(path)
    pred = gt = None
    for k in ("pred", "preds", "prediction", "predictions", "y_pred"):
        if k in d.files:
            pred = np.asarray(d[k]); break
    for k in ("gt", "true", "truth", "y_true", "target", "targets", "label"):
        if k in d.files:
            gt = np.asarray(d[k]); break
    if pred is None or gt is None:
        continue
    if pred.ndim == 3:
        mse_v = {i: float(np.mean((pred[..., i] - gt[..., i]) ** 2)) for i in range(min(7, pred.shape[-1]))}
        mae_v = {i: float(np.mean(np.abs(pred[..., i] - gt[..., i]))) for i in range(min(7, pred.shape[-1]))}
        add(model, L, seed, mse_v, mae_v)

# ---- aggregate to per-model per-variable (mean over L, seed) ----
models = ["miflu"] + BASE_MODELS
rows = []
for model in models:
    cells = [v for k, v in data.items() if k[0] == model]
    if not cells:
        continue
    for i in range(7):
        mses = [c[0][i] for c in cells if i in c[0]]
        maes = [c[1][i] for c in cells if i in c[1]]
        if not mses:
            continue
        mz = float(np.mean(mses)); az = float(np.mean(maes))
        rows.append({
            "model": model, "feature_index": i, "variable": VARS[i],
            "std": round(STD[i], 4),
            "mse_z": round(mz, 4), "mae_z": round(az, 4),
            "mse_physical": round(mz * STD[i] ** 2, 2),
            "mae_physical": round(az * STD[i], 2),
        })

os.makedirs(OUT_DIR, exist_ok=True)
dst = os.path.join(OUT_DIR, "DENORMALIZED_MSE_MAE_BY_VARIABLE.csv")
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"[write] {dst} ({len(rows)} rows)\n")

# ---- print: physical-unit MSE per variable, all models ----
print("=== Denormalized MSE by variable (physical units) ===")
print(f"{'variable':<20}" + "".join(f"{m[:9]:>11}" for m in models))
print("-" * (20 + 11 * len(models)))
for i in range(7):
    line = f"{VARS[i][:19]:<20}"
    for m in models:
        r = [x for x in rows if x["model"] == m and x["feature_index"] == i]
        line += f"{r[0]['mse_physical']:>11,.0f}" if r else f"{'NA':>11}"
    print(line)

print("\n=== Denormalized MAE by variable (physical units) ===")
print(f"{'variable':<20}" + "".join(f"{m[:9]:>11}" for m in models))
print("-" * (20 + 11 * len(models)))
for i in range(7):
    line = f"{VARS[i][:19]:<20}"
    for m in models:
        r = [x for x in rows if x["model"] == m and x["feature_index"] == i]
        line += f"{r[0]['mae_physical']:>11,.1f}" if r else f"{'NA':>11}"
    print(line)
