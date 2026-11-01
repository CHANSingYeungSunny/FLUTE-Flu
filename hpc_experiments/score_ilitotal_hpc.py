#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""score_ilitotal_hpc.py — Compute ILITOTAL-only MSE/MAE for all 8 TRACK_C models on HPC.

Reads the frozen stage6 predictions (pred_<model>_L<L>_s<seed>.npz), extracts
ILITOTAL (feature index 4), and computes both z-space and physical-unit (patient
count) errors. This completes the Task-2 evidence that was previously blocked.

Usage:
    python score_ilitotal_hpc.py \
        --pred-dir /home/sychan552/stage5_a2_durable/stage6/predictions \
        --scaler   /home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/inputs/handoff/03_data/scaler_miflu_author966.json \
        --out      /home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/paper_tables/TRACK_C_ILITOTAL_ALL8.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re

import numpy as np

# The 8 authoritative TRACK_C models
TRACK_C_MODELS = [
    "miflu", "nlinear", "dlinear", "timecma_llm",
    "patchtst", "itransformer", "qwen_time_llm", "calf_llm",
]
ILITOTAL_IDX = 4  # feature index of ILITOTAL in the 7-variable schema


def load_scaler(path):
    with open(path, "r", encoding="utf-8") as f:
        s = json.load(f)
    return s["mean"][ILITOTAL_IDX], s["std"][ILITOTAL_IDX]


def parse_cell(fname):
    """pred_miflu_L24_s42.npz -> ('miflu', 24, 42)"""
    m = re.match(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(fname))
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-dir", required=True)
    ap.add_argument("--scaler", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mean_i, std_i = load_scaler(args.scaler)
    print(f"[scaler] ILITOTAL mean={mean_i} std={std_i}")

    rows = []
    files = sorted(glob.glob(os.path.join(args.pred_dir, "pred_*.npz")))
    print(f"[scan] {len(files)} npz files")

    for path in files:
        cell = parse_cell(path)
        if cell is None:
            continue
        model, L, seed = cell
        if model not in TRACK_C_MODELS:
            continue
        try:
            d = np.load(path)
        except Exception as e:
            print(f"  [skip] {os.path.basename(path)}: {e}")
            continue

        # Find prediction / ground-truth arrays
        pred = None
        gt = None
        for pk in ("pred", "preds", "prediction", "predictions", "y_pred"):
            if pk in d.files:
                pred = d[pk]
                break
        for gk in ("gt", "true", "truth", "y_true", "target", "targets", "label"):
            if gk in d.files:
                gt = d[gk]
                break
        if pred is None or gt is None:
            print(f"  [skip] {os.path.basename(path)} keys={d.files}")
            continue

        pred = np.asarray(pred)
        gt = np.asarray(gt)
        if pred.ndim == 3 and pred.shape[-1] > ILITOTAL_IDX:
            p_i = pred[..., ILITOTAL_IDX]
            g_i = gt[..., ILITOTAL_IDX]
        elif pred.ndim == 2:
            # already ILITOTAL-only
            p_i, g_i = pred, gt
        else:
            print(f"  [skip] {os.path.basename(path)} shape={pred.shape}")
            continue

        mse_z = float(np.mean((p_i - g_i) ** 2))
        mae_z = float(np.mean(np.abs(p_i - g_i)))
        mse_phys = mse_z * (std_i ** 2)
        mae_phys = mae_z * std_i

        rows.append({
            "model": model, "L": L, "seed": seed,
            "mse_z_ILITOTAL": round(mse_z, 6),
            "mae_z_ILITOTAL": round(mae_z, 6),
            "mse_physical_ILITOTAL": round(mse_phys, 4),
            "mae_physical_ILITOTAL": round(mae_phys, 4),
            "n_points": int(np.size(g_i)),
        })

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                           ["model", "L", "seed", "mse_z_ILITOTAL", "mae_z_ILITOTAL",
                            "mse_physical_ILITOTAL", "mae_physical_ILITOTAL", "n_points"])
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {args.out} ({len(rows)} rows)")

    # Per-model 4L mean summary
    print("\n=== Per-model ILITOTAL-only (4L mean) ===")
    for model in TRACK_C_MODELS:
        mrows = [r for r in rows if r["model"] == model]
        if not mrows:
            print(f"  {model}: NO DATA")
            continue
        mm = np.mean([r["mse_z_ILITOTAL"] for r in mrows])
        mp = np.mean([r["mse_physical_ILITOTAL"] for r in mrows])
        print(f"  {model}: MSE_z={mm:.4f}  MSE_phys={mp:,.0f} patient-count^2  (n={len(mrows)})")


if __name__ == "__main__":
    main()
