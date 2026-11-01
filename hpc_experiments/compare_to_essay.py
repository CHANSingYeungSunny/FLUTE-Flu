#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""compare_to_essay.py — STEP 1 (user-mandated FIRST step).

Side-by-side comparison of OUR reproduction (7-variable aggregate MSE, z-space)
against the ESSAY's Table V, for every model that appears in BOTH.

Essay: Moon, Shim, Kim & Hwang, "MIFlu: Large Language Model-Based Multimodal
Influenza Forecasting Scheme", IEEE JBHI 29(10):7790-7801, 2025.
Table V values transcribed verbatim from
  reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md

Essay's comparison set (Table IV):
  GPT4TS, DLinear, PatchTST, TimesNet, FEDformer, Autoformer, Stationary,
  ETSformer, LightTS, Informer, Reformer
Our comparison set (TRACK_C):
  MIFlu, NLinear, DLinear, TimeCMA, PatchTST, iTransformer, Qwen-Time-LLM, CALF
=> Overlap: MIFlu, DLinear, PatchTST  (3 models)
"""
from __future__ import annotations

import csv
import os

ROOT = r"c:/Users/Asus/Desktop/FYP code/MLFlu"
OUT = os.path.join(ROOT, "paper_tables", "ESSAY_VS_REPRODUCTION_TABLE_V.csv")

# ---- Essay Table V (MSE), transcribed verbatim ----
ESSAY_MSE = {
    "MIFlu":     {24: 1.542, 36: 1.422, 48: 1.414, 60: 1.364},
    "GPT4TS":    {24: 2.063, 36: 1.868, 48: 1.790, 60: 1.979},
    "DLinear":   {24: 2.215, 36: 1.963, 48: 2.130, 60: 2.368},
    "PatchTST":  {24: 1.319, 36: 1.430, 48: 1.553, 60: 1.470},
    "TimesNet":  {24: 2.317, 36: 1.972, 48: 2.238, 60: 2.027},
    "FEDformer": {24: 3.228, 36: 2.679, 48: 2.622, 60: 2.857},
    "Autoformer":{24: 3.483, 36: 3.103, 48: 2.669, 60: 2.770},
    "Stationary":{24: 2.294, 36: 1.825, 48: 2.010, 60: 2.178},
    "ETSformer": {24: 2.527, 36: 2.615, 48: 2.359, 60: 2.487},
    "LightTS":   {24: 8.313, 36: 6.631, 48: 7.299, 60: 7.283},
    "Informer":  {24: 5.764, 36: 4.755, 48: 4.763, 60: 4.882},
    "Reformer":  {24: 4.400, 36: 4.783, 48: 4.832, 60: 4.882},
}
ESSAY_MAE = {
    "MIFlu":     {24: 0.726, 36: 0.779, 48: 0.757, 60: 0.719},
    "GPT4TS":    {24: 0.881, 36: 0.892, 48: 0.884, 60: 0.957},
    "DLinear":   {24: 1.081, 36: 0.963, 48: 1.024, 60: 1.096},
    "PatchTST":  {24: 0.754, 36: 0.834, 48: 0.815, 60: 0.788},
}

# ---- Our TRACK_C per-L MSE (7-variable aggregate, z-space) ----
OUR_MSE = {
    "miflu":         {24: 1.9686, 36: 1.9332, 48: 1.7547, 60: 1.8042},
    "dlinear":       {24: 2.2850, 36: 2.2780, 48: 2.3558, 60: 2.4726},
    "patchtst":      {24: 3.8884, 36: 3.7766, 48: 3.9525, 60: 4.0643},
}
OUR_MAE = {
    "miflu":         {24: 0.9349, 36: 0.9239, 48: 0.8511, 60: 0.8269},
    "dlinear":       {24: 1.0579, 36: 1.0399, 48: 1.1020, 60: 1.1538},
    "patchtst":      {24: 1.3900, 36: 1.3594, 48: 1.3767, 60: 1.4039},
}

PAIR = [("miflu", "MIFlu"), ("dlinear", "DLinear"), ("patchtst", "PatchTST")]
LS = [24, 36, 48, 60]

rows = []
for our_key, essay_key in PAIR:
    for L in LS:
        e = ESSAY_MSE[essay_key][L]
        o = OUR_MSE[our_key][L]
        rows.append({
            "model": essay_key, "L": L,
            "essay_MSE": e, "ours_MSE": round(o, 4),
            "delta_pct": round((o - e) / e * 100, 1),
            "essay_MAE": ESSAY_MAE[essay_key][L],
            "ours_MAE": round(OUR_MAE[our_key][L], 4),
        })
    # 4-step mean row
    em = sum(ESSAY_MSE[essay_key][L] for L in LS) / 4
    om = sum(OUR_MSE[our_key][L] for L in LS) / 4
    rows.append({
        "model": essay_key, "L": "4L-mean",
        "essay_MSE": round(em, 4), "ours_MSE": round(om, 4),
        "delta_pct": round((om - em) / em * 100, 1),
        "essay_MAE": round(sum(ESSAY_MAE[essay_key][L] for L in LS) / 4, 4),
        "ours_MAE": round(sum(OUR_MAE[our_key][L] for L in LS) / 4, 4),
    })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"[write] {OUT} ({len(rows)} rows)")

print("\n" + "=" * 78)
print("ESSAY Table V  vs  OUR REPRODUCTION   (7-variable aggregate MSE, z-space)")
print("=" * 78)
print(f"{'model':<11}{'L':>9}{'essay MSE':>12}{'ours MSE':>11}{'delta%':>10}{'essay MAE':>12}{'ours MAE':>11}")
print("-" * 78)
for r in rows:
    marker = "  <<<" if r["L"] == "4L-mean" else ""
    print(f"{r['model']:<11}{str(r['L']):>9}{r['essay_MSE']:>12}{r['ours_MSE']:>11}"
          f"{r['delta_pct']:>9.1f}%{r['essay_MAE']:>12}{r['ours_MAE']:>11}{marker}")

print("\n=== 4-step mean deviation summary ===")
for r in rows:
    if r["L"] == "4L-mean":
        print(f"  {r['model']:<11} essay={r['essay_MSE']:<8} ours={r['ours_MSE']:<8} delta={r['delta_pct']:+.1f}%")
