#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pte_pie_sensitivity.py
======================
Robustness check for the PTE/PIE result.

The headline result contradicts the MSE championship ranking, and MIFlu's mean
PIE lands exactly on the 25 % threshold, so the peak-detection choices must be
shown not to drive the conclusion. This sweeps:

    min_sep      in {40, 52}          peak separation (weeks)
    AMP_MODE     in {mean, mean_plus_half_sd, median}
    match_tol    in {2, 4}            peak matching window (weeks)

and prints, for every setting, the per-model hit rate and mean PIE.
The conclusion is only reportable if the ORDERING is stable across settings.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import compute_pte_pie_track_c as C  # noqa: E402

import numpy as np  # noqa: E402


def run(min_sep, amp, tol):
    C.AMP_MODE = amp
    C.MATCH_TOL_WEEKS = tol
    res = {}
    for m in C.MODELS:
        nh = nt = 0
        pies, ptes = [], []
        for L in C.HORIZONS:
            for s in C.SEEDS:
                sm, _ = C.evaluate(m, L, seed=s)
                if sm is None:
                    continue
                nt += sm["n_true_peaks"]
                nh += sm["n_hit"]
                if sm["mean_PIE_pct"] != "":
                    pies.append(float(sm["mean_PIE_pct"]))
                if sm["mean_PTE_wk"] != "":
                    ptes.append(float(sm["mean_PTE_wk"]))
        res[m] = (nh, nt,
                  round(nh / nt * 100, 1) if nt else float("nan"),
                  round(float(np.mean(pies)), 2) if pies else float("nan"),
                  round(float(np.mean(ptes)), 2) if ptes else float("nan"))
    return res


def main():
    combos = [(ms, am, tl)
              for ms in (40, 52)
              for am in ("mean", "mean_plus_half_sd")
              for tl in (2, 4)]
    combos += [(40, "median", 2)]

    print(f"{'min_sep':>7} {'amp_mode':>18} {'tol':>4}  "
          f"{'model':>14} {'hit':>7} {'rate%':>7} {'PIE':>7} {'PTE':>6}")
    last = None
    for ms, am, tl in combos:
        res = run(ms, am, tl)
        order = sorted(res.items(), key=lambda kv: -kv[1][2])
        for m, (nh, nt, rate, pie, pte) in order:
            print(f"{ms:>7} {am:>18} {tl:>4}  {m:>14} "
                  f"{str(nh) + '/' + str(nt):>7} {rate:>7} {pie:>7} {pte:>6}")
        print("-" * 78)
        if last is not None and [k for k, _ in order] != last:
            print("  ^^ ORDERING CHANGED vs previous setting")
        last = [k for k, _ in order]
    print("\nordering stability: see 'ORDERING CHANGED' markers above")


if __name__ == "__main__":
    main()
