#!/usr/bin/env python3
"""Audit reuse compatibility of existing author-966 artifacts against the
canonical strict-966 key contract (execution step 4/§5)."""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

DUR = "/gpfs1/home/sychan552/stage5_a2_durable"
KEYS = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/canonical_keys"

print("=== durable tree (depth 2) ===")
for d in sorted(os.listdir(DUR)):
    p = os.path.join(DUR, d)
    if os.path.isdir(p):
        n = len(os.listdir(p))
        print(f"  {d}/  ({n} entries)")

print()
print("=== prediction npz files under durable ===")
npzs = sorted(glob.glob(DUR + "/**/*.npz", recursive=True))
by_dir = {}
for f in npzs:
    by_dir.setdefault(os.path.dirname(f), []).append(os.path.basename(f))
for d, fs in sorted(by_dir.items()):
    models = sorted({f.split("_")[1] for f in fs if f.startswith("pred_")})
    print(f"  {d}: {len(fs)} files, models={models}")

print()
print("=== schema of one npz ===")
for f in npzs:
    if "nlinear" in f and "L24" in f and "s42" in f:
        z = np.load(f, allow_pickle=True)
        print("  file:", f)
        for k in z.files:
            a = z[k]
            info = "shape=" + str(getattr(a, "shape", None))
            if a.dtype.kind in "US" or a.ndim == 0:
                info += "  value=" + str(a)
            print(f"    {k}: {info}")
        break

print()
print("=== canonical strict-966 test keys (L24 seed42) ===")
k = pd.read_csv(f"{KEYS}/canonical_keys_L24_seed42.csv")
kt = k[k.split == "test"]
print("  test origins:", kt.forecast_origin.nunique(),
      "range", kt.forecast_origin.min(), "-", kt.forecast_origin.max())
print("  target_start range:", kt.target_start_row.min(), "-", kt.target_start_row.max())
print("  leads:", kt.forecast_lead.nunique(), "features:", kt.feature_index.nunique())
print("  rows:", len(kt))