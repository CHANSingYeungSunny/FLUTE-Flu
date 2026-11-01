#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""analysis_postprocess.py — v2 (fixes the three defects recorded in AGENTS.md §10).

FIX 1  efficiency: replaced the inverted `mse/params_B` with a **Pareto frontier**
       (non-dominated in (MSE, params)) plus the **slope of MSE vs log10(params)**.
FIX 2  CRPS/WIS: now computed **against the real target**, not from spread alone.
       Predictive distribution = Gaussian whose mean is the across-seed ensemble
       mean and whose sd is the across-seed ensemble spread (3 members; crude but
       leak-free — no test labels enter the spread).
FIX 3  paired-test CI: percentile **bootstrap** (10k resamples) instead of the
       closed-form approximation.

EVALUATION WINDOWS: every cell is cropped on the window axis to
`eval_slice(W) = (W // 16) * 16` — the first 160/144/144/128 test windows at
L = 24/36/48/60 — before any metric is computed, because the MIFlu reproduction
scores only those (`train_miflu.train_L` uses `drop_last=True` on its test
loader). Efficiency, CRPS/WIS and the paired sign-flip tests are therefore all
computed on MIFlu's window set; see `scripts/eval_windows.py`. Each output table
carries `n_eval_windows` (or one column per horizon) and the script asserts the
count is uniform across arms at every horizon.

DLinear excluded (hard rule 3).
"""
from __future__ import annotations
import glob, itertools, os, re, sys
import numpy as np, pandas as pd
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)                 # makes `eval_windows` importable from anywhere
from eval_windows import crop, eval_slice, assert_uniform  # noqa: E402

EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
OUT = os.path.join(ROOT, "paper_tables")
EXCLUDE = {"dlinear"}
RNG = np.random.default_rng(0)

# ─────────────── load predictions and targets per (model, L, seed) ───────────────
cells = {}
for d in sorted(glob.glob(os.path.join(EXP, "*_L*_s*"))):
    m = re.search(r"([A-Za-z_]+)_L(\d+)_s(\d+)$", os.path.basename(d))
    if not m:
        continue
    model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
    if model in EXCLUDE:
        continue
    f = os.path.join(d, f"pred_{model}_L{L}_s{seed}.npz")
    if not os.path.exists(f):
        continue
    z = np.load(f)
    pred, target, _ts, W_avail, n_ev = crop(
        z["pred"], z["target"], z["target_start_row"], L=L,
        label=os.path.basename(f))
    if n_ev == 0:
        raise ValueError(f"{f}: eval_slice({W_avail}) == 0")
    params = np.nan
    mc = os.path.join(d, "metrics.csv")
    if os.path.exists(mc):
        try:
            t = pd.read_csv(mc)
            if "total_parameters" in t.columns and len(t):
                params = float(t["total_parameters"].iloc[0])
        except Exception:
            pass
    cells[(model, L, seed)] = {"pred": pred, "target": target, "params": params,
                               "n_eval_windows": n_ev,
                               "n_windows_available": W_avail}
models = sorted({k[0] for k in cells})
print(f"cells={len(cells)} models={len(models)}")
# the shared evaluation-window rule: one count per horizon, identical for all arms
window_by_L = {}
for (mo, L, sd), c in cells.items():
    window_by_L.setdefault(L, set()).add(c["n_eval_windows"])
for L, vals in sorted(window_by_L.items()):
    assert len(vals) == 1, f"L={L}: arms disagree on n_eval_windows: {sorted(vals)}"
    n = sorted(vals)[0]
    assert n == eval_slice(max(c["n_windows_available"] for k, c in cells.items() if k[1] == L))
    print(f"[eval-window] L={L:2d}  n_eval_windows={n:3d}  (uniform across "
          f"{len({k[0] for k in cells if k[1] == L})} models)")


# ─────────────── 1. efficiency: Pareto + log-parameter slope ───────────────
agg = []
for mo in models:
    ks = [k for k in cells if k[0] == mo]
    mse = float(np.mean([np.mean((cells[k]["pred"] - cells[k]["target"]) ** 2) for k in ks]))
    prm = next((cells[k]["params"] for k in ks if not np.isnan(cells[k]["params"])), np.nan)
    agg.append({"model": mo, "mse_mean": mse, "params": prm,
                "n_cells": len(ks)})
E = pd.DataFrame(agg).sort_values("mse_mean").reset_index(drop=True)
E["improve_vs_worst_pct"] = ((E.mse_mean.max() - E.mse_mean) / E.mse_mean.max() * 100).round(2)
E["params_B"] = (E.params / 1e9).round(6)
# the shared evaluation-window count, one column per horizon (a model spans all
# four horizons, so a single scalar would hide the L=60 difference)
for L in sorted(window_by_L):
    E[f"n_eval_windows_L{L}"] = sorted(window_by_L[L])[0]
assert_uniform(pd.DataFrame([{"model": k[0], "L": k[1],
                             "n_eval_windows": c["n_eval_windows"],
                             "n_windows_available": c["n_windows_available"]}
                            for k, c in cells.items()]),
               by=("L",), col="n_eval_windows", what="cells")

# Pareto frontier over models that HAVE a parameter count
P = E[E.params.notna()].copy()
P = P.sort_values("params")
keep, best = [], np.inf
for r in P.itertuples():
    if r.mse_mean < best - 1e-12:
        keep.append(r.model)
        best = r.mse_mean
P["on_pareto"] = P.model.isin(keep)
E = E.merge(P[["model", "on_pareto"]], on="model", how="left")

# slope of MSE vs log10(params) across parametrised models
x = np.log10(P.params.values); y = P.mse_mean.values
slope, intercept = np.polyfit(x, y, 1)
r2 = 1 - np.sum((y - (slope * x + intercept)) ** 2) / np.sum((y - y.mean()) ** 2)
E["mse_vs_log10params_slope"] = round(float(slope), 4)
E["mse_vs_log10params_r2"] = round(float(r2), 4)
E.round(6).to_csv(os.path.join(OUT, "BENCH_EFFICIENCY.csv"), index=False)

# ─────────────── 2. true CRPS / log score / WIS against the target ───────────────
LEVELS = [0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50,
          0.60, 0.70, 0.80, 0.90, 0.95, 0.98]

def wis(mu, sd, y, alphas=(0.02, 0.05, 0.10, 0.20, 0.30, 0.40,
                           0.60, 0.70, 0.80, 0.90, 0.95, 0.98)):
    """Weighted interval score (Bracher et al. 2021) for a Gaussian forecast.

    alphas must lie strictly inside (0, 1); using 2k/K up to 2.0 makes
    norm.ppf(1 - a/2) = ppf(0) = -inf, which is what produced NaN in v2.0.
    Normalisation: (0.5*|y-m| + sum_k (a_k/2)*IS_k) / (0.5 + sum_k a_k/2).
    """
    tot = 0.5 * np.abs(y - mu)
    wsum = 0.5
    for a in alphas:
        lo = mu - norm.ppf(1 - a / 2) * sd
        hi = mu + norm.ppf(1 - a / 2) * sd
        inter = (hi - lo) + (2 / a) * np.maximum(lo - y, 0) + (2 / a) * np.maximum(y - hi, 0)
        tot = tot + (a / 2) * inter
        wsum += a / 2
    return tot / wsum

prow = []
for (mo, L), grp in pd.DataFrame([{"model": k[0], "L": k[1], "seed": k[2]}
                                  for k in cells]).groupby(["model", "L"]):
    ks = [k for k in cells if k[0] == mo and k[1] == L]
    if len(ks) < 2:
        continue
    Pst = np.stack([cells[k]["pred"] for k in ks])      # (S, W, V, L)
    Y = cells[ks[0]]["target"]                          # same across seeds
    mu = Pst.mean(0)
    # Deterministic models (DT/RF/GB/SVR/KNN/NLinear) have ZERO cross-seed spread,
    # which sends the Gaussian log density to infinity. Floor sigma at 5% of a
    # standard deviation (the data are z-scored, so sd=1 is the unit scale): a
    # forecast may not claim more certainty than 0.05 sd. Documented limitation.
    sd = np.maximum(Pst.std(0, ddof=1), 0.05)
    zz = (Y - mu) / sd
    Phi = norm.cdf(zz); phi = norm.pdf(zz)
    crps = float(np.mean(sd * (zz * (2 * Phi - 1) + 2 * phi - 1 / np.sqrt(np.pi))))
    ls = float(np.mean(-0.5 * np.log(2 * np.pi * sd ** 2) - 0.5 * zz ** 2))
    W = float(np.mean(wis(mu, sd, Y)))
    prow.append({"model": mo, "L": L, "n_seeds": len(ks),
                 "n_eval_windows": cells[ks[0]]["n_eval_windows"],
                 "crps_z": crps, "log_score": ls, "wis": W,
                 "mean_sigma_z": float(np.mean(sd))})
pd.DataFrame(prow).round(6).to_csv(os.path.join(OUT, "BENCH_CRPS_WIS.csv"), index=False)

# ─────────────── 3. paired tests with bootstrap CI ───────────────
piv = pd.DataFrame([{"L": k[1], "seed": k[2], "model": k[0],
                     "mse": float(np.mean((cells[k]["pred"] - cells[k]["target"]) ** 2))}
                    for k in cells]).pivot_table(index=["L", "seed"],
                                                 columns="model", values="mse")
pairs = []
for a, b in itertools.combinations(models, 2):
    if a not in piv or b not in piv:
        continue
    d = (piv[a] - piv[b]).dropna().values
    nz = d[d != 0]
    if nz.size == 0:
        pairs.append({"model_a": a, "model_b": b, "n": 0, "mean_diff": 0.0,
                      "wins_a": 0, "p_raw": 1.0, "ci_lo": 0.0, "ci_hi": 0.0})
        continue
    obs = abs(nz.mean()); cnt = tot = 0
    for signs in itertools.product([1, -1], repeat=nz.size):
        tot += 1
        if abs((nz * np.array(signs)).mean()) >= obs - 1e-12:
            cnt += 1
    boots = np.array([RNG.choice(nz, nz.size, replace=True).mean() for _ in range(10000)])
    pairs.append({"model_a": a, "model_b": b, "n": int(nz.size),
                  "mean_diff": float(nz.mean()),
                  "wins_a": int((nz < 0).sum()),
                  "p_raw": cnt / tot,
                  "ci_lo": float(np.percentile(boots, 2.5)),
                  "ci_hi": float(np.percentile(boots, 97.5))})
PT = pd.DataFrame(pairs).sort_values("p_raw").reset_index(drop=True)
m = len(PT)
PT["p_holm"] = np.minimum.accumulate(
    np.clip(PT.p_raw * (m - np.arange(m)), 0, 1)[::-1])[::-1]
sd = piv.std()
PT["effect_d"] = [abs(r.mean_diff) / np.sqrt((sd.get(r.model_a, np.nan) ** 2 +
                                              sd.get(r.model_b, np.nan) ** 2) / 2)
                  for r in PT.itertuples()]
PT.round(6).to_csv(os.path.join(OUT, "BENCH_PAIRED_TESTS.csv"), index=False)

# ─────────────── report ───────────────
pd.set_option("display.width", 200)
print("\n=== efficiency: Pareto frontier (parametrised models only) ===")
print(E[E.params.notna()][["model", "mse_mean", "params", "params_B",
                           "improve_vs_worst_pct", "on_pareto"]]
      .round(4).to_string(index=False))
print(f"\nslope(MSE vs log10 params) = {slope:.4f}  R2 = {r2:.3f}"
      f"   -> {'MORE params = LOWER MSE' if slope < 0 else 'MORE params = HIGHER MSE'}")
print("\n=== probabilistic skill (Gaussian, mean/spread across 3 seeds) ===")
cw = pd.read_csv(os.path.join(OUT, "BENCH_CRPS_WIS.csv"))
print(cw.groupby("model")[["crps_z", "log_score", "wis"]].mean()
      .sort_values("crps_z").round(4).to_string())
print("\n=== paired tests (bootstrap CI, Holm) — top separations ===")
print(PT.head(10)[["model_a", "model_b", "n", "mean_diff", "wins_a",
                   "p_raw", "p_holm", "ci_lo", "ci_hi", "effect_d"]]
      .round(5).to_string(index=False))
print("\nfiles -> BENCH_EFFICIENCY.csv, BENCH_CRPS_WIS.csv, BENCH_PAIRED_TESTS.csv")
print("        all of them are computed on the shared evaluation windows "
      + ", ".join(f"L{L}={sorted(v)[0]}" for L, v in sorted(window_by_L.items()))
      + " — identical to MIFlu's (W//16)*16 count")
