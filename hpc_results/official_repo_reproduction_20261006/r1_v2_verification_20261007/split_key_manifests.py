#!/usr/bin/env python3
"""Generate the split-specific strict-966 key manifests and verify Test counts."""
from __future__ import annotations

import os

import pandas as pd

BASE = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007"
K = f"{BASE}/canonical_keys"
EXPECT = {24: (170, 24), 36: (158, 36), 48: (146, 48), 60: (134, 60)}
SEEDS = (42, 43, 44)

for split in ("train", "validation", "test"):
    frames = []
    for L in (24, 36, 48, 60):
        for s in SEEDS:
            d = pd.read_csv(f"{K}/canonical_keys_L{L}_seed{s}.csv")
            frames.append(d[d.split == split])
    all_ = pd.concat(frames)
    name = f"STRICT_966_{split.upper()}_KEYS.csv"
    all_.to_csv(f"{BASE}/{name}", index=False)
    print(f"{name:34s} rows={len(all_):>9,}")

print()
print("TEST keys per horizon x seed (origins x leads x 7):")
ok = True
for L, (o, ld) in EXPECT.items():
    for s in SEEDS:
        d = pd.read_csv(f"{K}/canonical_keys_L{L}_seed{s}.csv")
        t = d[d.split == "test"]
        exp = o * ld * 7
        good = len(t) == exp
        ok = ok and good
        verdict = "OK" if good else "MISMATCH"
        print(f"  L{L} seed{s}: {len(t):>6,} expected {exp:>6,} {verdict}")

print()
print("ALL TEST KEY COUNTS MATCH:", ok)
print("duplicate test keys:",
      sum(pd.read_csv(f"{K}/canonical_keys_L{L}_seed{s}.csv")
          .query("split=='test'")
          .duplicated(subset=["forecast_origin", "forecast_lead", "feature_index"]).sum()
          for L in EXPECT for s in SEEDS))