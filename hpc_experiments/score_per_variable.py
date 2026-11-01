#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""score_per_variable.py — Per-variable MSE for MIFlu (authoritative strict966 CSVs).

Purpose: determine WHICH variable (or aggregate) the paper's Table V value 1.4355
actually measures. The national_illness dataset has 7 variables:

  idx 0  % WEIGHTED ILI
  idx 1  % UNWEIGHTED ILI
  idx 2  AGE 0-4
  idx 3  AGE 5-24
  idx 4  ILITOTAL
  idx 5  NUM. OF PROVIDERS
  idx 6  OT

If a single variable's MSE lands near 1.4355, the paper's number is that variable,
and our 7-variable aggregate (1.8652) was never directly comparable.
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

VARS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
        "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
BASE = "/home/sychan552/scratch/MLFLU/miflu_csv"

files = sorted(glob.glob(os.path.join(BASE, "miflu_strict966__*", "test_predictions_*.csv")))
print(f"[scan] {len(files)} MIFlu cells\n")

per_var = {i: [] for i in range(7)}
per_var_L = {}
all7 = []

for path in files:
    df = pd.read_csv(path)
    if df.empty:
        continue
    m = None
    import re
    m = re.search(r"miflu_strict966__L(\d+)__seed(\d+)", path)
    L = int(m.group(1)) if m else 0
    df["err2"] = (df["y_pred_z"].astype(float) - df["y_true_z"].astype(float)) ** 2
    all7.append(float(df["err2"].mean()))
    for i in range(7):
        sub = df[df["feature_index"].astype(int) == i]
        if sub.empty:
            continue
        per_var[i].append(float(sub["err2"].mean()))
        per_var_L.setdefault(i, {}).setdefault(L, []).append(float(sub["err2"].mean()))

print("=== MIFlu per-variable MSE (z-space, 4L mean) ===")
print(f"{'idx':<5}{'variable':<22}{'MSE_z':>10}{'vs paper 1.4355':>18}")
print("-" * 58)
for i in range(7):
    if not per_var[i]:
        continue
    mz = float(np.mean(per_var[i]))
    delta = (mz - 1.4355) / 1.4355 * 100
    flag = "  <== CLOSE!" if abs(delta) < 10 else ""
    print(f"{i:<5}{VARS[i]:<22}{mz:>10.4f}{delta:>17.1f}%{flag}")

print(f"\n{'ALL7':<5}{'7-variable aggregate':<22}{np.mean(all7):>10.4f}"
      f"{(np.mean(all7)-1.4355)/1.4355*100:>17.1f}%")

print("\n=== per-variable by horizon (which step is best?) ===")
print(f"{'variable':<22}" + "".join(f"{'L'+str(L):>10}" for L in [24, 36, 48, 60]))
for i in range(7):
    if i not in per_var_L:
        continue
    line = f"{VARS[i]:<22}"
    for L in [24, 36, 48, 60]:
        v = per_var_L[i].get(L, [])
        line += f"{np.mean(v):>10.4f}" if v else f"{'NA':>10}"
    print(line)
