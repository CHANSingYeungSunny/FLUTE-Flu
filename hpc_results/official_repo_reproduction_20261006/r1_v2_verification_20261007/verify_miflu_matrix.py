#!/usr/bin/env python3
"""Verify every completed Track C MIFlu cell against the frozen contract."""
from __future__ import annotations

import json
import os

B = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/runs"
EXPECT = {24: (549, 74, 170, 28560), 36: (537, 62, 158, 39816),
          48: (525, 50, 146, 49056), 60: (513, 38, 134, 56280)}

hdr = f"{'cell':34s} {'windows':>18s} {'n_test':>7s} {'exp':>7s} {'mse_z':>9s} {'mae_z':>9s} ep testacc"
print(hdr)
print("-" * len(hdr))
bad, rows = [], []
if not os.path.isdir(B):
    raise SystemExit(f"missing {B}")
for d in sorted(os.listdir(B)):
    m = os.path.join(B, d, f"manifest_{d}.json")
    if not os.path.exists(m):
        print(f"{d:34s} NO MANIFEST")
        bad.append(d)
        continue
    j = json.load(open(m))
    L = j["horizon"]
    w = j["window_counts"]
    got = (w["train"], w["validation"], w["test"])
    exp = EXPECT[L]
    ok = (got == exp[:3] and j["n_test"] == exp[3]
          and str(j.get("test_access_during_fit")) == "False"
          and j.get("lora_tensors") == 12
          and j.get("trainable_fraction", 1) < 0.05)
    if not ok:
        bad.append(d)
    rows.append((d, got, j["n_test"], exp[3], j["test_mse_z"], j["test_mae_z"],
                 j["best_epoch"], ok))
    print(f"{d:34s} {str(got):>18s} {j['n_test']:>7d} {exp[3]:>7d} "
          f"{j['test_mse_z']:>9.5f} {j['test_mae_z']:>9.5f} {j['best_epoch']:>2d} "
          f"{j['test_access_during_fit']} {'OK' if ok else 'BAD'}")

print()
print(f"cells present: {len(rows)} / 12")
print("cells failing contract:", bad if bad else "none")