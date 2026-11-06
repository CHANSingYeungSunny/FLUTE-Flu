#!/usr/bin/env python3
"""Inspect WF prediction NPZ schema + candidate MSE formulas.

Runs ONLY via sbatch on a compute node (never on the Burgundy login node).
"""
import glob
import os
import sys
import numpy as np

W = "/gpfs1/home/sychan552/stage5_a2_durable/hpc_results/walk_forward"
samples = [
    "f1/L24_s42/pred_miflu_L24_seed42.npz",
    "f1/calf_llm_L24_s42/pred_calf_llm_L24_s42.npz",
    "f2/nlinear_L24_s42/pred_nlinear_L24_s42.npz",
    "f3/nlinear_L24_s42/pred_nlinear_L24_s42.npz",
]
for rel in samples:
    p = os.path.join(W, rel)
    if not os.path.exists(p):
        print("MISSING", p)
        continue
    z = np.load(p, allow_pickle=False)
    print("=" * 70)
    print("FILE", rel, "size", os.path.getsize(p))
    print("KEYS", list(z.files))
    for k in z.files:
        a = z[k]
        try:
            print("  ", k, "shape", getattr(a, "shape", None), "dtype", getattr(a, "dtype", None),
                  "value", (a.item() if a.ndim == 0 else (a.ravel()[:3].tolist() if a.size <= 3e6 else "...")))
        except Exception as e:
            print("  ", k, "ERR", e)
    if "pred" in z.files and "target" in z.files:
        pred, tgt = np.asarray(z["pred"], dtype=float), np.asarray(z["target"], dtype=float)
        print("  pred.shape", pred.shape, "target.shape", tgt.shape)
        if pred.shape == tgt.shape:
            d = pred - tgt
            print("  mse_all", float(np.nanmean(d ** 2)))
            print("  mse_mean_axis_last", float(np.nanmean(np.nanmean(d ** 2, axis=-1))))
            print("  finite pred", np.isfinite(pred).mean(), "finite tgt", np.isfinite(tgt).mean())
            print("  abs mean", float(np.nanmean(np.abs(d))))
        else:
            print("  SHAPE MISMATCH")
print("=" * 70)
print("NPZ inventory by fold (pred_*.npz):")
for f in ["f1", "f2", "f3", "f4", "f5"]:
    files = glob.glob(os.path.join(W, f, "*", "pred_*.npz"))
    print(" ", f, len(files))
sys.exit(0)
