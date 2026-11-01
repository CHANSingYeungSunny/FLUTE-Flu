#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""compare_miflu_mse_mae_steps.py — MIFlu vs essay, MSE *and* MAE, step by step.

Essay Table V (Moon, Shim, Kim & Hwang, IEEE JBHI 29(10):7790-7801, 2025):
  MSE  L24 1.542 | L36 1.422 | L48 1.414 | L60 1.364   (mean 1.4355)
  MAE  L24 0.726 | L36 0.779 | L48 0.757 | L60 0.719   (mean 0.74525)
Ours: 7-variable aggregate, z-space, 3 seeds (42/43/44).
"""
from __future__ import annotations

import csv
import os

ROOT = r"c:/Users/Asus/Desktop/FYP code/MLFlu"
OUT = os.path.join(ROOT, "paper_tables", "MIFLU_ESSAY_MSE_MAE_BY_STEP.csv")

ESSAY = {
    24: {"mse": 1.542, "mae": 0.726},
    36: {"mse": 1.422, "mae": 0.779},
    48: {"mse": 1.414, "mae": 0.757},
    60: {"mse": 1.364, "mae": 0.719},
}
OURS = {
    24: {"mse": 1.9686, "mae": 0.9349},
    36: {"mse": 1.9332, "mae": 0.9239},
    48: {"mse": 1.7547, "mae": 0.8511},
    60: {"mse": 1.8042, "mae": 0.8269},
}
# C2 corrected-scheduler results (partial: L24 all 3 seeds, L36 2 of 3 seeds)
C2 = {
    24: [1.869887, 2.047165, 1.952757],
    36: [1.793492, 1.878340],
}

LS = [24, 36, 48, 60]
rows = []
print(f"{'L':>4} | {'ESSAY MSE':>10}{'OURS MSE':>10}{'Δ MSE':>9} | "
      f"{'ESSAY MAE':>10}{'OURS MAE':>10}{'Δ MAE':>9} | {'C2 MSE':>10}{'Δ C2':>8}")
print("-" * 92)
for L in LS:
    e, o = ESSAY[L], OURS[L]
    dmse = (o["mse"] - e["mse"]) / e["mse"] * 100
    dmae = (o["mae"] - e["mae"]) / e["mae"] * 100
    c2 = sum(C2[L]) / len(C2[L]) if L in C2 else None
    dc2 = (c2 - e["mse"]) / e["mse"] * 100 if c2 else None
    rows.append({
        "L": L,
        "essay_MSE": e["mse"], "ours_MSE": o["mse"], "delta_MSE_pct": round(dmse, 1),
        "essay_MAE": e["mae"], "ours_MAE": o["mae"], "delta_MAE_pct": round(dmae, 1),
        "c2_MSE": round(c2, 4) if c2 else "NA",
        "c2_delta_pct": round(dc2, 1) if dc2 is not None else "NA",
        "c2_n_seeds": len(C2.get(L, [])),
    })
    cs = f"{c2:>10.4f}{dc2:>7.1f}%" if c2 else f"{'pending':>18}"
    print(f"{L:>4} | {e['mse']:>10.4f}{o['mse']:>10.4f}{dmse:>8.1f}% | "
          f"{e['mae']:>10.4f}{o['mae']:>10.4f}{dmae:>8.1f}% | {cs}")

em = sum(ESSAY[L]["mse"] for L in LS) / 4
om = sum(OURS[L]["mse"] for L in LS) / 4
ema = sum(ESSAY[L]["mae"] for L in LS) / 4
oma = sum(OURS[L]["mae"] for L in LS) / 4
print("-" * 92)
print(f"{'4L':>4} | {em:>10.4f}{om:>10.4f}{(om-em)/em*100:>8.1f}% | "
      f"{ema:>10.4f}{oma:>10.4f}{(oma-ema)/ema*100:>8.1f}% |")

rows.append({
    "L": "4L-mean",
    "essay_MSE": round(em, 4), "ours_MSE": round(om, 4),
    "delta_MSE_pct": round((om - em) / em * 100, 1),
    "essay_MAE": round(ema, 4), "ours_MAE": round(oma, 4),
    "delta_MAE_pct": round((oma - ema) / ema * 100, 1),
    "c2_MSE": "NA", "c2_delta_pct": "NA", "c2_n_seeds": 0,
})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"\n[write] {OUT}")
