#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_stage6_all7.py — Check whether stage6 npz aggregate matches authoritative Track C.

Track C 7-variable aggregate MSE (authoritative):
  miflu 1.8652, nlinear 2.0495, dlinear 2.3478, timecma_llm 2.6700,
  patchtst 3.9205, itransformer 3.9847, qwen_time_llm 5.2196, calf_llm 5.5153

If stage6 all-7 aggregate matches these numbers, stage6 IS the Track C prediction set
and its ILITOTAL-only figures are valid for Track C. If not, stage6 is a DIFFERENT
experimental instance and must be labelled as such.
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np

TRACK_C = {
    "miflu": 1.8652, "nlinear": 2.0495, "dlinear": 2.3478, "timecma_llm": 2.6700,
    "patchtst": 3.9205, "itransformer": 3.9847, "qwen_time_llm": 5.2196, "calf_llm": 5.5153,
}


def parse_cell(fname):
    m = re.match(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(fname))
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


def main():
    pred_dir = "/home/sychan552/stage5_a2_durable/stage6/predictions"
    files = sorted(glob.glob(os.path.join(pred_dir, "pred_*.npz")))

    agg = {}
    for path in files:
        cell = parse_cell(path)
        if not cell:
            continue
        model, L, seed = cell
        if model not in TRACK_C:
            continue
        d = np.load(path)
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
            continue
        pred = np.asarray(pred)
        gt = np.asarray(gt)
        # all-7 aggregate: mean over all feature channels
        mse = float(np.mean((pred - gt) ** 2))
        agg.setdefault(model, []).append(mse)

    print(f"{'model':<16}{'stage6_all7':>14}{'TrackC':>12}{'match?':>10}")
    print("-" * 54)
    for model in TRACK_C:
        vals = agg.get(model, [])
        if not vals:
            print(f"{model:<16}{'NO DATA':>14}")
            continue
        m = float(np.mean(vals))
        tc = TRACK_C[model]
        ok = "MATCH" if abs(m - tc) < 0.05 else "DIFFERS"
        print(f"{model:<16}{m:>14.4f}{tc:>12.4f}{ok:>10}")


if __name__ == "__main__":
    main()
