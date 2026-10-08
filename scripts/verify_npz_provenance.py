#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_npz_provenance.py
========================
Critical integrity check: do the audit_20260930/predictions_stage6/*.npz
arrays reproduce the OFFICIAL Track C championship per-cell MSE recorded in
TRACK_C_RESULTS_PER_CELL.csv?

If they match, the npz ARE the Track C predictions (a parallel export) and the
PTE/PIE computed from them is valid for Track C.
If they do NOT match, the npz belong to an earlier experiment and must not be
presented as Track C results.
"""
from __future__ import annotations

import csv
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(ROOT, "audit_20260930", "predictions_stage6")
CELL = os.path.join(ROOT, "hpc_results",
                    "official_repo_reproduction_20261006",
                    "r1_v2_verification_20261007", "TRACK_C_RESULTS_PER_CELL.csv")


def main():
    cells = {}
    with open(CELL, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            cells[(r["model"], int(r["L"]), int(r["seed"]))] = float(r["mse"])
    print("per-cell CSV has", len(cells), "cells; models:",
          sorted(set(k[0] for k in cells)))

    checked, matched = 0, 0
    for (model, L, seed), csv_mse in sorted(cells.items()):
        p = os.path.join(NPZ, f"pred_{model}_L{L}_s{seed}.npz")
        if not os.path.exists(p):
            print(f"[missing] {model} L{L} s{seed}")
            continue
        d = np.load(p)
        pred, tgt = d["pred"], d["target"]
        # try both axis orders
        if pred.ndim == 3 and pred.shape[1] == 7:
            pz = pred
        elif pred.ndim == 3 and pred.shape[2] == 7:
            pz = pred.transpose(0, 2, 1)
        else:
            continue
        # candidate MSE definitions
        mse_all = float(((pz - tgt.transpose(0, 2, 1) if tgt.ndim == 3 and tgt.shape[2] == 7 else tgt) ** 2).mean()) if False else None
        # rebuild tgt order consistently
        if tgt.ndim == 3 and tgt.shape[1] == 7:
            tz = tgt
        else:
            tz = tgt.transpose(0, 2, 1)
        mse_all7 = float(((pz - tz) ** 2).mean())
        mse_ili = float(((pz[:, 4, :] - tz[:, 4, :]) ** 2).mean())
        mse_ili_lead0 = float(((pz[:, 4, 0] - tz[:, 4, 0]) ** 2).mean())
        checked += 1
        ok = min(abs(mse_all7 - csv_mse), abs(mse_ili - csv_mse)) < 0.05
        if ok:
            matched += 1
        if checked <= 8 or not ok:
            print(f"[{'OK' if ok else 'DIFF'}] {model:13s} L{L:2d} s{seed} "
                  f"csv={csv_mse:.4f} all7={mse_all7:.4f} ili={mse_ili:.4f} "
                  f"ili_l0={mse_ili_lead0:.4f}")
    print(f"\nmatched {matched}/{checked} cells within 0.05 of CSV (all7 or ili)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
