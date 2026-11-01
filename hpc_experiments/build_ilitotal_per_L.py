#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_ilitotal_per_L.py — ILITOTAL-only MSE/MAE per model per horizon (L=24/36/48/60).

Answers the user's request: separate MSE for EACH step, not just the 4-step mean.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict

STD = 9003.15234375
OUT_DIR = "/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/paper_tables"
SRC = os.path.join(OUT_DIR, "TRACK_C_ILITOTAL_CONSOLIDATED.csv")

MODELS = ["miflu", "nlinear", "dlinear", "timecma_llm",
          "patchtst", "itransformer", "qwen_time_llm", "calf_llm"]
LS = ["24", "36", "48", "60"]

rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
by = defaultdict(list)
for r in rows:
    by[r["model"]].append(r)

out = []
for m in MODELS:
    for L in LS:
        cs = [r for r in by[m] if r["L"] == L]
        if not cs:
            continue
        mz = sum(float(r["mse_z_ILITOTAL"]) for r in cs) / len(cs)
        az = sum(float(r["mae_z_ILITOTAL"]) for r in cs) / len(cs)
        out.append({
            "model": m, "L": L,
            "mse_z_ILITOTAL": round(mz, 4),
            "mae_z_ILITOTAL": round(az, 4),
            "mse_physical_ILITOTAL": round(mz * STD ** 2, 2),
            "mae_physical_ILITOTAL": round(az * STD, 2),
            "n_cells": len(cs),
        })

# best / worst step per model
summary = {}
for m in MODELS:
    ms = [o for o in out if o["model"] == m]
    if not ms:
        continue
    best = min(ms, key=lambda x: x["mse_z_ILITOTAL"])
    worst = max(ms, key=lambda x: x["mse_z_ILITOTAL"])
    summary[m] = (best["L"], best["mse_z_ILITOTAL"], worst["L"], worst["mse_z_ILITOTAL"])

dst = os.path.join(OUT_DIR, "TRACK_C_ILITOTAL_PER_L.csv")
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print(f"[write] {dst} ({len(out)} rows)")

print("\n=== ILITOTAL-only per horizon (z-space MSE) ===")
print(f"{'model':<16}" + "".join(f"{'L'+L:>12}" for L in LS) + f"{'best':>8}{'worst':>8}")
for m in MODELS:
    ms = {o["L"]: o["mse_z_ILITOTAL"] for o in out if o["model"] == m}
    line = f"{m:<16}"
    for L in LS:
        line += f"{ms.get(L, float('nan')):>12.4f}"
    if m in summary:
        b, _, w, _ = summary[m]
        line += f"{'L'+b:>8}{'L'+w:>8}"
    print(line)
