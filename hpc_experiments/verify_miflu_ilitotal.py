#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_miflu_ilitotal.py — Recompute MIFlu ILITOTAL-only MSE from authoritative strict966 CSVs.

Expected (ChatGPT claim): 3.7020 z^2  ->  300,071,219.88 patient-count^2
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

ILITOTAL_IDX = 4
STD = 9003.15234375

base = "/home/sychan552/scratch/MLFLU/miflu_csv"
files = sorted(glob.glob(os.path.join(base, "miflu_strict966__*", "test_predictions_*.csv")))
print(f"[scan] {len(files)} MIFlu cells")

per_cell = []
all7 = []
for path in files:
    df = pd.read_csv(path)
    name = os.path.basename(path)
    if df.empty:
        continue
    # feature_index identifies the variable; ILITOTAL == 4
    fi = df["feature_index"].astype(int) if "feature_index" in df.columns else None
    sub = df[fi == ILITOTAL_IDX] if fi is not None else df
    if sub.empty:
        print(f"  [warn] no ILITOTAL rows in {name}")
        continue
    err = sub["y_pred_z"].astype(float) - sub["y_true_z"].astype(float)
    mse_i = float(np.mean(err ** 2))
    mae_i = float(np.mean(np.abs(err)))
    # all-7 aggregate for cross-check
    err_all = df["y_pred_z"].astype(float) - df["y_true_z"].astype(float)
    all7.append(float(np.mean(err_all ** 2)))
    per_cell.append((name, mse_i, mae_i))

print("\n=== per-cell ILITOTAL-only ===")
for n, m, a in per_cell:
    print(f"  {n}: MSE_z={m:.4f}  MAE_z={a:.4f}")

if per_cell:
    mm = float(np.mean([m for _, m, _ in per_cell]))
    ma = float(np.mean([a for _, _, a in per_cell]))
    print(f"\n=== MIFlu 4L mean ILITOTAL-only ===")
    print(f"  MSE_z = {mm:.4f}")
    print(f"  MSE_physical = {mm * STD**2:,.4f} patient-count^2")
    print(f"  MAE_z = {ma:.4f}")
    print(f"  MAE_physical = {ma * STD:,.4f} patient counts")
if all7:
    print(f"\n  [cross-check] all-7 aggregate MSE = {np.mean(all7):.4f} (Track C = 1.8652)")
