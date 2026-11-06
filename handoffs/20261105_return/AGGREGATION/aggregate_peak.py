#!/usr/bin/env python3
"""Compute K&S peak metrics from Track B prediction CSVs.

The export column is named `*_ili` but the training target is ILITOTAL
(`target_name: ILITOTAL` in train_backbone_966.py); the physical columns are
patient counts.  Detector and matching follow the project convention:
find_peaks(prominence=0.15*range, distance=15), +-8 week matching, per step.
"""
import csv, glob, os, re, sys
import numpy as np
from scipy.signal import find_peaks

B = "/gpfs1/scratch/sychan552/trackB_20261104/core"

def pte_pie(wk, gt, pr):
    rng = float(gt.max() - gt.min())
    if rng <= 0:
        return None
    gi, _ = find_peaks(gt, prominence=0.15 * rng, distance=15)
    if len(gi) == 0:
        gi = np.array([int(np.argmax(gt))])
    rows = []
    for g in gi:
        wg, vg = float(wk[g]), float(gt[g])
        m = np.abs(wk - wg) <= 8
        if not m.any() or vg == 0:
            continue
        k = int(np.argmax(pr[m]))
        rows.append((abs(float(wk[m][k]) - wg), abs(float(pr[m][k]) - vg) / abs(vg) * 100))
    if not rows:
        return None
    a = np.array(rows)
    return float(a[:, 0].mean()), float(a[:, 1].mean())

out_rows = []
for pred in sorted(glob.glob(os.path.join(B, "export", "*", "L*_s*", "predictions_*.csv"))):
    cell = os.path.dirname(pred)
    model = os.path.basename(os.path.dirname(cell))
    L, seed = re.match(r"L(\d+)_s(\d+)", os.path.basename(cell)).groups()
    L, seed = int(L), int(seed)
    data = {}
    with open(pred) as fh:
        for r in csv.DictReader(fh):
            if r["split"] != "test":
                continue
            data.setdefault(int(r["step"]), []).append(
                (float(r["abs_week"]), float(r["ground_truth_ili_phys"]), float(r["prediction_ili_phys"])))
    for step in sorted(data):
        arr = np.array(sorted(data[step]))
        wk, gt, pr = arr[:, 0], arr[:, 1], arr[:, 2]
        r = pte_pie(wk, gt, pr)
        if r is None:
            out_rows.append(dict(model=model, L=L, seed=seed, step=step,
                                 pte="", pie="", passed="", n_windows=len(wk)))
        else:
            pte, pie = r
            out_rows.append(dict(model=model, L=L, seed=seed, step=step,
                                 pte=f"{pte:.6f}", pie=f"{pie:.6f}",
                                 passed=int(pte <= 1.0 and pie <= 25.0), n_windows=len(wk)))

out = os.path.join(B, "TRACKB_PEAK_PARTIAL.csv")
fields = ["model", "L", "seed", "step", "pte", "pie", "passed", "n_windows"]
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out_rows)
print("rows", len(out_rows), "->", out)
if out_rows:
    print("cells", len({(r["model"], r["L"], r["seed"]) for r in out_rows}))
