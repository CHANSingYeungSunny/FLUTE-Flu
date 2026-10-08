#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pte_pie_deliverables.py
=============================
Re-package the Track C PTE/PIE results into the exact filenames required by the
final-report spec, and build the literature-vs-custom PASS MATRIX.

Inputs (already computed, frozen):
  PTE_PIE_per_peak.csv   -> TRACK_C_PTE_PIE_PER_EVENT.csv
  PTE_PIE_by_model.csv   -> TRACK_C_PTE_PIE_PER_MODEL.csv

New:
  TRACK_C_PTE_PIE_PASS_MATRIX.csv
"""
from __future__ import annotations

import csv
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria")

MODELS = ["miflu", "nlinear", "dlinear", "timecma_llm", "patchtst",
          "itransformer", "qwen_time_llm", "calf_llm"]
# ordered by MSE ranking for readability
MODELS_BY_MSE = ["miflu", "nlinear", "dlinear", "timecma_llm", "patchtst",
                 "itransformer", "qwen_time_llm", "calf_llm"]


def main():
    src_peak = os.path.join(OUT, "PTE_PIE_per_peak.csv")
    src_model = os.path.join(OUT, "PTE_PIE_by_model.csv")

    shutil.copy(src_peak, os.path.join(OUT, "TRACK_C_PTE_PIE_PER_EVENT.csv"))
    shutil.copy(src_model, os.path.join(OUT, "TRACK_C_PTE_PIE_PER_MODEL.csv"))
    print("[copy] PER_EVENT, PER_MODEL")

    peaks = list(csv.DictReader(open(src_peak, newline="", encoding="utf-8")))
    by_model = {r["model"]: r for r in csv.DictReader(
        open(src_model, newline="", encoding="utf-8"))}

    rows = []
    for m in MODELS_BY_MSE:
        pk = [r for r in peaks if r["model"] == m]
        n_true = sum(1 for r in pk if r["status"] in
                     ("Hit", "MatchedNotHit", "Missed"))
        n_lit = sum(1 for r in pk if r["status"] == "Hit")
        n_custom = 0
        for r in pk:
            if r["status"] not in ("Hit", "MatchedNotHit"):
                continue
            try:
                pte = float(r["PTE_wk"])
                pie = float(r["PIE_pct"])
            except ValueError:
                continue
            # PROJECT-CUSTOM: PTE <= 2 weeks AND PIE <= 20 %
            if pte <= 2.0 and pie <= 20.0:
                n_custom += 1
        bm = by_model.get(m, {})
        rows.append(dict(
            model=m,
            n_true_peaks=n_true,
            literature_hits_PTE1_PIE25=n_lit,
            literature_hit_rate_pct=round(n_lit / n_true * 100, 1) if n_true else "",
            custom_hits_PTE2_PIE20=n_custom,
            custom_hit_rate_pct=round(n_custom / n_true * 100, 1) if n_true else "",
            mean_PTE_wk=bm.get("mean_of_cell_PTE_wk", ""),
            mean_PIE_pct=bm.get("mean_of_cell_PIE_pct", ""),
            satisfies_literature=("YES" if n_lit == n_true and n_true
                                  else ("PARTIAL" if n_lit else "NO")),
            satisfies_custom=("YES" if n_custom == n_true and n_true
                             else ("PARTIAL" if n_custom else "NO"))))

    with open(os.path.join(OUT, "TRACK_C_PTE_PIE_PASS_MATRIX.csv"),
              "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[write] TRACK_C_PTE_PIE_PASS_MATRIX.csv")
    for r in rows:
        print(f"  {r['model']:13s} lit {r['literature_hits_PTE1_PIE25']:>2}/{r['n_true_peaks']}"
              f" ({r['literature_hit_rate_pct']}%)  custom {r['custom_hits_PTE2_PIE20']:>2}/"
              f"{r['n_true_peaks']} ({r['custom_hit_rate_pct']}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
