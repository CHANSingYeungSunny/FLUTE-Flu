#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""plot_bench.py — per-model, per-horizon 4-panel figures for the benchmark.

One figure per (model, L): 2x2 panels = step 0/1/2/3 = 1/2/3/4 weeks ahead.
  x = test week index, y = ILITOTAL de-normalised to patients.
  solid = ground truth, dashed = prediction, circles mark the matched peaks,
  title carries PTE / PIE and the Kramer & Shaman verdict.

EVALUATION WINDOWS: the figures draw exactly the windows the tables score — the
first `eval_slice(W) = (W // 16) * 16` test windows, i.e. MIFlu's evaluation set
(`train_miflu.train_L` uses `drop_last=True` on the test loader; see
`scripts/eval_windows.py`). The figure subtitle states the count, so a figure can
never disagree with `paper_tables/BENCH_*.csv`.

DLinear is EXCLUDED by request (it is the essay's own baseline, not a competitor).
"""
from __future__ import annotations
import glob, json, os, re, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)                 # makes `eval_windows` importable from anywhere
from eval_windows import crop, eval_slice  # noqa: E402

EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
OUT = os.path.join(ROOT, "results", "bench_figures")
SC = json.load(open(os.path.join(ROOT, "data", "scaler_miflu_author966.json")))
MEAN = np.array(SC["mean"], float); STD = np.array(SC["std"], float)
ILI = 4
EXCLUDE = {"dlinear"}

def pte_pie(wk, gt, pr):
    rng = float(gt.max() - gt.min())
    if rng <= 0: return None
    gi, _ = find_peaks(gt, prominence=0.15 * rng, distance=15)
    if len(gi) == 0: gi = np.array([int(np.argmax(gt))])
    rows = []
    for g in gi:
        wg, vg = int(wk[g]), float(gt[g])
        m = np.abs(wk - wg) <= 8
        if not m.any() or vg == 0: continue
        k = int(np.argmax(pr[m]))
        rows.append((abs(int(wk[m][k]) - wg), abs(float(pr[m][k]) - vg) / abs(vg) * 100,
                     wg, vg, int(wk[m][k]), float(pr[m][k])))
    if not rows: return None
    a = np.array([r[:2] for r in rows])
    return float(a[:, 0].mean()), float(a[:, 1].mean()), rows

os.makedirs(OUT, exist_ok=True)
by = {}
for p in sorted(glob.glob(os.path.join(EXP, "**", "pred_*.npz"), recursive=True)):
    m = re.search(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", p)
    if not m or m.group(1) in EXCLUDE: continue
    L = int(m.group(2))
    d = np.load(p)
    pred, target, ts, W_avail, n_ev = crop(
        d["pred"], d["target"], d["target_start_row"], L=L, label=os.path.basename(p))
    by.setdefault((m.group(1), L), []).append((pred, target, ts, W_avail, n_ev))

print("[eval-window] figures draw the same windows as the tables "
      "(first (W//16)*16 test windows):")
seen = {}
n = 0
for (model, L), lst in sorted(by.items()):
    n_ev = {v[4] for v in lst}
    W_avail = {v[3] for v in lst}
    assert len(n_ev) == 1 and len(W_avail) == 1, (model, L, n_ev, W_avail)
    n_ev, W_avail = n_ev.pop(), W_avail.pop()
    assert n_ev == eval_slice(W_avail)
    seen.setdefault(L, set()).add(n_ev)
    P = np.stack([a for a, _, _, _, _ in lst]).mean(0)      # seed-mean prediction
    T = np.stack([b for _, b, _, _, _ in lst]).mean(0)
    W = lst[0][2]
    assert P.shape[1] == 7 and P.shape[2] == L and P.shape[0] == n_ev
    fig, axes = plt.subplots(2, 2, figsize=(15, 8.5)); axes = axes.flatten()
    for s in range(4):
        if s >= L: axes[s].axis("off"); continue
        ax = axes[s]
        wk = W + s
        gt = T[:, ILI, s] * STD[ILI] + MEAN[ILI]
        pr = P[:, ILI, s] * STD[ILI] + MEAN[ILI]
        ax.plot(wk, gt, color="#1f77b4", lw=1.7, label="Ground truth")
        ax.plot(wk, pr, color="#d62728", lw=1.7, ls="--", label="Prediction")
        r = pte_pie(wk, gt, pr)
        if r:
            pte, pie, rows = r
            for _, _, wg, vg, wp, vp in rows:
                ax.plot(wg, vg, "o", ms=9, mfc="none", mec="#1f77b4", mew=1.6)
                ax.plot(wp, vp, "s", ms=8, mfc="none", mec="#d62728", mew=1.6)
            ok = pte <= 1.0 and pie <= 25.0
            ax.set_title(f"step {s} = {s+1} week{'s' if s else ''} ahead   "
                         f"PTE={pte:.1f}wk  PIE={pie:.1f}%  [{'PASS' if ok else 'FAIL'}]",
                         fontsize=10, fontweight="bold")
        else:
            ax.set_title(f"step {s} = {s+1} weeks ahead (no peak)", fontsize=10)
        ax.set_xlabel("test week index", fontsize=9)
        ax.set_ylabel("ILITOTAL (patients)", fontsize=9)
        ax.legend(loc="upper left", fontsize=8); ax.grid(alpha=0.3)
    fig.suptitle(f"{model}  L={L}  (seed-mean of {len(lst)})   |   "
                 f"{n_ev} evaluated test windows = (W={W_avail}//16)*16, "
                 f"identical to MIFlu   |   Kramer & Shaman: PTE<=1wk and PIE<=25%",
                 fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"{model}_L{L}.png"), dpi=110, bbox_inches="tight")
    plt.close()
    n += 1
for L, vals in sorted(seen.items()):
    assert len(vals) == 1, f"L={L}: figures disagree on n_eval_windows: {sorted(vals)}"
    print(f"   L={L:2d}  n_eval_windows={sorted(vals)[0]}")
print(f"figures written: {n} -> {OUT}")
