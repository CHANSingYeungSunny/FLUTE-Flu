#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_final_ilitotal.py — Consolidated ILITOTAL-only MSE/MAE for all 8 TRACK_C models.

Sources (both verified against authoritative Track C):
  * MIFlu   : miflu_strict966__* CSVs  (all-7 aggregate cross-check = 1.8652 -> MATCH)
  * 7 bases : stage6 pred_<model>_L<L>_s<seed>.npz
              (all-7 aggregate matches Track C exactly for all 7 -> MATCH)

Outputs:
  TRACK_C_ILITOTAL_CONSOLIDATED.csv   (per model x L x seed)
  TRACK_C_ILITOTAL_4L_MEAN.csv        (per model 4L mean, z-space + physical)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re

import numpy as np
import pandas as pd

ILITOTAL_IDX = 4
STD = 9003.15234375
MEAN = 9439.841796875

BASE_MODELS = ["nlinear", "dlinear", "timecma_llm", "patchtst",
               "itransformer", "qwen_time_llm", "calf_llm"]
STAGE6 = "/home/sychan552/stage5_a2_durable/stage6/predictions"
MIFLU_CSV = "/home/sychan552/scratch/MLFLU/miflu_csv"
OUT_DIR = "/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/paper_tables"


def parse_cell(fname):
    m = re.match(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(fname))
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


rows = []

# ---- MIFlu from authoritative strict966 CSVs ----
for path in sorted(glob.glob(os.path.join(MIFLU_CSV, "miflu_strict966__*", "test_predictions_*.csv"))):
    df = pd.read_csv(path)
    if df.empty:
        continue
    m = re.search(r"miflu_strict966__L(\d+)__seed(\d+)", path)
    L, seed = int(m.group(1)), int(m.group(2))
    sub = df[df["feature_index"].astype(int) == ILITOTAL_IDX]
    if sub.empty:
        continue
    err = sub["y_pred_z"].astype(float) - sub["y_true_z"].astype(float)
    rows.append({
        "model": "miflu", "L": L, "seed": seed,
        "mse_z_ILITOTAL": round(float(np.mean(err ** 2)), 6),
        "mae_z_ILITOTAL": round(float(np.mean(np.abs(err))), 6),
        "source": "miflu_strict966_csv",
    })

# ---- 7 baselines from stage6 npz (verified == Track C) ----
for path in sorted(glob.glob(os.path.join(STAGE6, "pred_*.npz"))):
    cell = parse_cell(path)
    if not cell:
        continue
    model, L, seed = cell
    if model not in BASE_MODELS:
        continue
    d = np.load(path)
    pred = gt = None
    for pk in ("pred", "preds", "prediction", "predictions", "y_pred"):
        if pk in d.files:
            pred = np.asarray(d[pk])
            break
    for gk in ("gt", "true", "truth", "y_true", "target", "targets", "label"):
        if gk in d.files:
            gt = np.asarray(d[gk])
            break
    if pred is None or gt is None:
        continue
    if pred.ndim == 3 and pred.shape[-1] > ILITOTAL_IDX:
        p_i, g_i = pred[..., ILITOTAL_IDX], gt[..., ILITOTAL_IDX]
    else:
        p_i, g_i = pred, gt
    err = p_i - g_i
    rows.append({
        "model": model, "L": L, "seed": seed,
        "mse_z_ILITOTAL": round(float(np.mean(err ** 2)), 6),
        "mae_z_ILITOTAL": round(float(np.mean(np.abs(err))), 6),
        "source": "stage6_npz",
    })

# add physical units
for r in rows:
    r["mse_physical_ILITOTAL"] = round(r["mse_z_ILITOTAL"] * STD ** 2, 4)
    r["mae_physical_ILITOTAL"] = round(r["mae_z_ILITOTAL"] * STD, 4)

os.makedirs(OUT_DIR, exist_ok=True)
fields = ["model", "L", "seed", "mse_z_ILITOTAL", "mae_z_ILITOTAL",
          "mse_physical_ILITOTAL", "mae_physical_ILITOTAL", "source"]
with open(os.path.join(OUT_DIR, "TRACK_C_ILITOTAL_CONSOLIDATED.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# 4L mean
summary = {}
for r in rows:
    summary.setdefault(r["model"], []).append(r)
sum_rows = []
for model in ["miflu"] + BASE_MODELS:
    rs = summary.get(model, [])
    if not rs:
        continue
    sum_rows.append({
        "model": model,
        "n_cells": len(rs),
        "mse_z_ILITOTAL_4L": round(float(np.mean([r["mse_z_ILITOTAL"] for r in rs])), 4),
        "mae_z_ILITOTAL_4L": round(float(np.mean([r["mae_z_ILITOTAL"] for r in rs])), 4),
        "mse_physical_ILITOTAL_4L": round(float(np.mean([r["mse_physical_ILITOTAL"] for r in rs])), 2),
        "mae_physical_ILITOTAL_4L": round(float(np.mean([r["mae_physical_ILITOTAL"] for r in rs])), 2),
    })
with open(os.path.join(OUT_DIR, "TRACK_C_ILITOTAL_4L_MEAN.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(sum_rows[0].keys()))
    w.writeheader()
    w.writerows(sum_rows)

print(f"[write] TRACK_C_ILITOTAL_CONSOLIDATED.csv ({len(rows)} rows)")
print(f"[write] TRACK_C_ILITOTAL_4L_MEAN.csv ({len(sum_rows)} models)")
print("\n=== ILITOTAL-only 4L mean (authoritative) ===")
print(f"{'model':<16}{'MSE_z':>10}{'MSE_phys(pat-cnt^2)':>24}")
for r in sum_rows:
    print(f"{r['model']:<16}{r['mse_z_ILITOTAL_4L']:>10.4f}{r['mse_physical_ILITOTAL_4L']:>24,.0f}")
