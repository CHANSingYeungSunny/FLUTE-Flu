#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_notext_ablation.py — Is our text pathway HELPING or HURTING?

stage6 has both `pred_miflu_*` and `pred_miflu_notext_*`. If the no-text variant
scores BETTER (lower MSE) than the text variant, then our text/text-fusion branch is
actively degrading MIFlu — which would explain why our MIFlu sits ~26% above the
essay while our non-text baselines (DLinear +8.2%) are close.
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np

STAGE6 = "/home/sychan552/stage5_a2_durable/stage6/predictions"
LS = [24, 36, 48, 60]

res = {}
for path in sorted(glob.glob(os.path.join(STAGE6, "pred_*.npz"))):
    m = re.match(r"pred_(miflu|notext)_L(\d+)_s(\d+)\.npz$", os.path.basename(path))
    if not m:
        continue
    model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
    d = np.load(path)
    pred = gt = None
    for k in ("pred", "preds", "prediction", "predictions", "y_pred"):
        if k in d.files:
            pred = np.asarray(d[k]); break
    for k in ("gt", "true", "truth", "y_true", "target", "targets", "label"):
        if k in d.files:
            gt = np.asarray(d[k]); break
    if pred is None or gt is None:
        continue
    mse = float(np.mean((pred - gt) ** 2))
    mae = float(np.mean(np.abs(pred - gt)))
    res.setdefault(model, {}).setdefault(L, []).append((seed, mse, mae))

for model in sorted(res):
    per_L = res[model]
    means = [np.mean([x[1] for x in per_L[L]]) for L in LS if L in per_L]
    print(f"\n=== {model} (7-variable aggregate) ===")
    print(f"{'L':>5}{'n':>4}{'MSE':>12}{'MAE':>10}")
    for L in LS:
        if L not in per_L:
            continue
        vals = per_L[L]
        print(f"{L:>5}{len(vals):>4}{np.mean([x[1] for x in vals]):>12.4f}"
              f"{np.mean([x[2] for x in vals]):>10.4f}")
    if means:
        print(f"{'4L':>5}{'':>4}{np.mean(means):>12.4f}")

# direct comparison
if "miflu" in res and "miflu_notext" in res:
    a = np.mean([np.mean([x[1] for x in res["miflu"][L]]) for L in LS if L in res["miflu"]])
    b = np.mean([np.mean([x[1] for x in res["miflu_notext"][L]]) for L in LS if L in res["miflu_notext"]])
    print("\n" + "=" * 60)
    print(f"MIFlu (with text)   4L MSE = {a:.4f}")
    print(f"MIFlu (no text)     4L MSE = {b:.4f}")
    diff = a - b
    print(f"difference (with - without) = {diff:+.4f}  ({diff/b*100:+.1f}% relative)")
    if diff > 0:
        print(">>> TEXT PATHWAY IS HURTING: notext is BETTER.")
        print(">>> Our text fusion likely misaligns/degrades the forecast.")
    else:
        print(">>> Text pathway helps (notext is worse) -> not the cause.")
    print(f"\nEssay MIFlu = 1.4355")
    print(f"  with text : {a:.4f}  ({(a-1.4355)/1.4355*100:+.1f}%)")
    print(f"  no text   : {b:.4f}  ({(b-1.4355)/1.4355*100:+.1f}%)")
