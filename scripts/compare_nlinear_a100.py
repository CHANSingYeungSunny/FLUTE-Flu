#!/usr/bin/env python
"""compare_nlinear_a100.py -- the V100 -> A100 hardware delta for the 12 NLinear cells.

WHY THIS EXISTS
---------------
`paper_tables/BENCH_GPU_PROVENANCE.csv` showed the 204 benchmark cells were not
homogeneous: 192 on A100-SXM4-80GB (job 715984) but the 12 NLinear cells on
V100-SXM2-32GB (job 717950, `gpu-v100s-04`). NLinear is the K&S champion, so its
numbers were measured on different silicon from its 15 competitors. Job 719191
re-ran exactly those 12 cells on A100/`stingy` and the V100 set was preserved in
`hpc_results/expanded_runs_v100_nlinear/`.

This script scores BOTH sets on the same shared evaluation windows
(`scripts/eval_windows.py`, `(W // 16) * 16` -> 160/144/144/128) with the SAME
formulas `scripts/analysis_expanded.py` uses, and prints the delta for every
metric that touches the K&S verdict: MSE, PTE, PIE and pass/16.

It writes `paper_tables/BENCH_NLINEAR_A100_DELTA.csv`.

No model is retrained; both sets of per-window predictions already exist.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from eval_windows import crop, eval_slice  # noqa: E402

SC = json.load(open(os.path.join(ROOT, "data", "scaler_miflu_author966.json")))
MEAN = np.array(SC["mean"], float)
STD = np.array(SC["std"], float)
ILI = 4
STEPS = [0, 1, 2, 3]

A100_DIR = os.path.join(ROOT, "hpc_results", "expanded_runs")
V100_DIR = os.path.join(ROOT, "hpc_results", "expanded_runs_v100_nlinear")


def _mean(a):
    a = np.asarray(a, float)
    return float(np.mean(a)) if np.isfinite(a).all() else float(np.nanmean(a))


def seasonal_pte_pie(wk, gt, pr):
    """Verbatim from `analysis_expanded.seasonal_pte_pie` (K&S peak matching)."""
    rng = float(gt.max() - gt.min())
    if rng <= 0:
        return None
    gi, _ = find_peaks(gt, prominence=0.15 * rng, distance=15)
    if len(gi) == 0:
        gi = np.array([int(np.argmax(gt))])
    P, E = [], []
    for g in gi:
        wg, vg = int(wk[g]), float(gt[g])
        mask = np.abs(wk - wg) <= 8
        if not mask.any() or vg == 0:
            continue
        k = int(np.argmax(pr[mask]))
        P.append(abs(int(wk[mask][k]) - wg))
        E.append(abs(float(pr[mask][k]) - vg) / abs(vg) * 100)
    if not P:
        return None
    return float(np.mean(P)), float(np.mean(E))


def load_root(root):
    """{(L): [(pred, target, ts, W_avail, n_eval), ...]} for the nlinear cells only."""
    cells = {}
    for p in sorted(glob.glob(os.path.join(root, "nlinear_L*_s*", "pred_*.npz"))):
        m = re.search(r"pred_nlinear_L(\d+)_s(\d+)\.npz$", p)
        if not m:
            continue
        L = int(m.group(1))
        d = np.load(p)
        pred, target, ts, W_avail, n_ev = crop(d["pred"], d["target"],
                                              d["target_start_row"], L=L,
                                              label=os.path.basename(p))
        cells.setdefault(L, []).append((pred, target, ts, W_avail, n_ev))
    return cells


def score(cells):
    """Per-L MSE and per-(L, step) PTE/PIE/pass, exactly as analysis_expanded does."""
    mse = {}
    pte_rows = []
    for L, lst in sorted(cells.items()):
        P = np.stack([a for a, _, _, _, _ in lst])
        T = np.stack([b for _, b, _, _, _ in lst])
        W = np.stack([c for _, _, c, _, _ in lst])
        assert P.shape[1] == lst[0][4] and P.shape[2] == 7 and P.shape[3] == L, P.shape
        mse[L] = _mean((P - T) ** 2)
        for s in STEPS:
            if s >= L:
                continue
            Ps, Es = [], []
            for i in range(P.shape[0]):
                wk = W[i] + s
                gt = T[i, :, ILI, s] * STD[ILI] + MEAN[ILI]
                pr = P[i, :, ILI, s] * STD[ILI] + MEAN[ILI]
                r = seasonal_pte_pie(wk, gt, pr)
                if r:
                    Ps.append(r[0])
                    Es.append(r[1])
            if Ps:
                pte_rows.append({"L": L, "step": s, "weeks_ahead": s + 1,
                                 "PTE_wk": float(np.mean(Ps)),
                                 "PIE_pct": float(np.mean(Es)),
                                 "pass": bool(np.mean(Ps) <= 1.0 and np.mean(Es) <= 25.0),
                                 "n_seeds": len(Ps),
                                 "n_eval_windows": lst[0][4]})
    return mse, pd.DataFrame(pte_rows)


def main():
    a_cells, v_cells = load_root(A100_DIR), load_root(V100_DIR)
    print(f"[cells] A100={sum(len(v) for v in a_cells.values())} "
          f"V100={sum(len(v) for v in v_cells.values())}")
    if not a_cells or not v_cells:
        print("[FATAL] missing one of the two cell sets"); return 1

    amse, apte = score(a_cells)
    vmse, vpte = score(v_cells)

    print("\n=== shared evaluation windows (the rule is (W//16)*16) ===")
    for L in sorted(amse):
        wa = a_cells[L][0][3]
        print(f"  L={L:2d} available={wa:3d} evaluated={eval_slice(wa):3d}")

    print("\n=== 7-variable MSE (z-space), mean over 3 seeds 42/43/44 ===")
    print(f"  {'L':>3} {'V100':>10} {'A100':>10} {'delta':>10} {'delta%':>9}")
    for L in sorted(amse):
        d = amse[L] - vmse[L]
        print(f"  {L:>3} {vmse[L]:>10.4f} {amse[L]:>10.4f} {d:>+10.4f} {d / vmse[L] * 100:>+8.2f}%")
    dm = np.mean([amse[L] for L in amse]) - np.mean([vmse[L] for L in vmse])
    print(f"  {'4L':>3} {np.mean([vmse[L] for L in vmse]):>10.4f} "
          f"{np.mean([amse[L] for L in amse]):>10.4f} {dm:>+10.4f} "
          f"{dm / np.mean([vmse[L] for L in vmse]) * 100:>+8.2f}%")

    print("\n=== PTE / PIE per (L, step) -- K&S pass = PTE <= 1 wk AND PIE <= 25% ===")
    mg = vpte.merge(apte, on=["L", "step", "weeks_ahead"], suffixes=("_v100", "_a100"))
    for _, r in mg.iterrows():
        mark = ""
        if r.pass_v100 != r.pass_a100:
            mark = "  <== VERDICT CHANGE"
        print(f"  L={int(r.L):>2} a={int(r.step)}  "
              f"PTE {r.PTE_wk_v100:5.2f} -> {r.PTE_wk_a100:5.2f}  "
              f"PIE {r.PIE_pct_v100:5.1f}% -> {r.PIE_pct_a100:5.1f}%  "
              f"{'PASS' if r.pass_v100 else 'FAIL'} -> {'PASS' if r.pass_a100 else 'FAIL'}{mark}")

    def summary(df, tag):
        n = len(df)
        p = int(df["pass"].sum())
        print(f"  {tag:<5} cells={n} pass={p}/{n}  PTE={df.PTE_wk.mean():.3f} wk  "
              f"PIE={df.PIE_pct.mean():.2f}%  "
              f"mse_4L={np.mean(list(amse.values() if tag == 'A100' else vmse.values())):.4f}")
        return p

    print("\n=== K&S summary (the 16 (L, step) cells) ===")
    pv = summary(vpte, "V100")
    pa = summary(apte, "A100")
    print(f"  pass/16: {pv}/16 -> {pa}/16   ({'UNCHANGED' if pv == pa else 'CHANGED'})")
    passing = apte[apte["pass"]]
    print("\n  passing cells on A100:",
          ", ".join(f"L{int(r.L)}/step{int(r.step)}" for _, r in passing.iterrows()) or "(none)")

    out = mg.copy()
    out["mse_4L_v100"] = np.mean(list(vmse.values()))
    out["mse_4L_a100"] = np.mean(list(amse.values()))
    path = os.path.join(ROOT, "paper_tables", "BENCH_NLINEAR_A100_DELTA.csv")
    out.to_csv(path, index=False)
    print(f"\n[wrote] {path}")

    with open(os.path.join(ROOT, "paper_tables", "_nlinear_a100_summary.json"), "w") as fh:
        json.dump({"mse_v100_4L": float(np.mean(list(vmse.values()))),
                   "mse_a100_4L": float(np.mean(list(amse.values()))),
                   "mse_by_L_v100": {str(k): float(v) for k, v in vmse.items()},
                   "mse_by_L_a100": {str(k): float(v) for k, v in amse.items()},
                   "pass_v100": pv, "pass_a100": pa,
                   "pte_mean_v100": float(vpte.PTE_wk.mean()),
                   "pte_mean_a100": float(apte.PTE_wk.mean()),
                   "pie_mean_v100": float(vpte.PIE_pct.mean()),
                   "pie_mean_a100": float(apte.PIE_pct.mean())}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
