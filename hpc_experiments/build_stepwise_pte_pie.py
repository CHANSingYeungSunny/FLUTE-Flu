#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_stepwise_pte_pie.py — User requirement #2 deliverable.

For each model x each horizon L in {24,36,48,60}, produce:
  * MSE  (7-variable aggregate, z-space)  <- official comparison scope
  * PTE  (weeks), PIE (%)                 <- peak criteria
  * PTE <= 1 week ?   PIE <= 25% ?   Combined PASS ?   (Kramer & Shaman 2019)

Sources:
  * MSE per L : paper_tables/TRACK_C_PER_HORIZON_CHAMPIONS.csv
  * PTE/PIE   : results/v3_clean/analysis/peak_criteria/peak_criteria.json (reconstructed CONSENSUS)
"""
from __future__ import annotations

import csv
import json
import os

import pandas as pd

ROOT = r"c:/Users/Asus/Desktop/FYP code/MLFlu"
MSE_SRC = os.path.join(ROOT, "paper_tables", "TRACK_C_PER_HORIZON_CHAMPIONS.csv")
PK_SRC = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria", "peak_criteria.json")
OUT = os.path.join(ROOT, "paper_tables", "TRACK_C_STEPWISE_MSE_PTE_PIE.csv")

# ---- load per-L MSE ----
mse_rows = list(csv.DictReader(open(MSE_SRC, encoding="utf-8")))
mse_map = {}
for r in mse_rows:
    mse_map[(r["model"], str(int(float(r["L"]))))] = float(r["mse"])

# ---- load PTE/PIE ----
pk = json.load(open(PK_SRC, encoding="utf-8"))
models_cfg = pk["CONSENSUS"]["models"]

# Only ONE linear model is kept: NLinear. DLinear is EXCLUDED (user decision
# 2026-10-31). Rationale: the essay's baseline figures are cited literature values
# from [9] rather than re-runs, so appearing in the essay is not grounds to keep
# DLinear; NLinear is retained as the single linear reference model.
EXCLUDE = {"dlinear"}

rows = []
for model, cfg in models_cfg.items():
    if model in EXCLUDE:
        continue
    per_L = cfg.get("per_L", {})
    for L in ("24", "36", "48", "60"):
        e = per_L.get(L)
        if not e:
            continue
        pte = e.get("mean_PTE_wk")
        pie = e.get("mean_PIE_pct")
        mse = mse_map.get((model, L))
        rows.append({
            "model": model,
            "L": L,
            "mse_7var": round(mse, 4) if mse is not None else "NA",
            "PTE_wk": round(pte, 2) if pte is not None else "NA",
            "PIE_pct": round(pie, 2) if pie is not None else "NA",
            "PTE_le_1wk": "PASS" if (pte is not None and pte <= 1.0) else "FAIL",
            "PIE_le_25pct": "PASS" if (pie is not None and pie <= 25.0) else "FAIL",
            "kramer_shaman_pass": "PASS" if (pte is not None and pie is not None
                                              and pte <= 1.0 and pie <= 25.0) else "FAIL",
            "hit_rate_pct": round(e.get("hit_rate_pct", 0), 1),
        })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"[write] {OUT} ({len(rows)} rows)\n")

# ---- print grouped by model ----
SIDE = {"miflu": "LLM", "nlinear": "non-LLM", "dlinear": "non-LLM", "timecma_llm": "LLM",
        "patchtst": "non-LLM", "itransformer": "non-LLM", "qwen_time_llm": "LLM", "calf_llm": "LLM"}
for side in ("non-LLM", "LLM"):
    print(f"\n########## {side} ##########")
    print(f"{'model':<16}{'L':>4}{'MSE':>9}{'PTE_wk':>9}{'PIE_%':>9}{'PTE<=1':>8}{'PIE<=25':>9}{'KS_PASS':>9}")
    print("-" * 66)
    for r in rows:
        if SIDE.get(r["model"]) != side:
            continue
        print(f"{r['model']:<16}{r['L']:>4}{r['mse_7var']:>9}{r['PTE_wk']:>9}{r['PIE_pct']:>9}"
              f"{r['PTE_le_1wk']:>8}{r['PIE_le_25pct']:>9}{r['kramer_shaman_pass']:>9}")
