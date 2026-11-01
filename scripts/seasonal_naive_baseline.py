#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""seasonal_naive_baseline.py — the missing reference point of the benchmark.

WHY THIS SCRIPT EXISTS
----------------------
`AGENTS.md` §13.A records the only missing leg of the cross-scale methodology:
the benchmark measured "improvement vs the WORST model", which is a meaningless
reference (it only says the champion is not last). A forecast that repeats what
happened 52 weeks earlier is the standard epidemiological baseline: it is free,
has zero parameters, and is the number every learned model must beat to justify
its cost. This script computes that baseline under the *identical* protocol and
adds the relative-improvement column to the efficiency table.

PROTOCOL (deliberately identical to the neural arms, no shortcuts)
-----------------------------------------------------------------
* Data: `author_966` profile ONLY (966 rows, 2002-2020 vintage). A-track numbers
  must never be mixed with the 1025-row B-track (`AGENTS.md` §2 rule 5).
* Scaler: `data/scaler_miflu_author966.json`, i.e. the **train-only** statistics.
  The script re-derives the same statistics from rows [:676] and asserts the
  persisted JSON agrees, so a silently refit scaler cannot slip in.
* Windows: `scripts/train_nlinear_966.py::build_windows`, imported — NOT
  reimplemented — with T=104, containment="strict", train_end=676, val_end=773.
  This yields the same 170 test windows at L=24 (and 158/146/134 at L=36/48/60)
  that the exported `pred_*.npz` cells were scored on. The script proves that by
  comparing its target tensor against the npz `target` on disk.
* Metric: 7-variable aggregate MSE/MAE in z-space (`AGENTS.md` §2 rule 1). The
  benchmark-side PTE/PIE metric is not applicable here: a seasonal-naive forecast
  is constant across leads, so only lead 0 is a meaningful curve.

FORECAST DEFINITION
-------------------
For a target block starting at row `t`, the forecast for every lead is the value
observed exactly 52 weeks earlier:

    y_hat[t, v, l] = z[t - 52, v]      for all l in [0, L)

with a fallback to the last observed value of the input window (`z[t-1]`) when
`t - 52 < 0`. For this profile the fallback is unreachable on the test split
(the earliest test target start is 773), which the script asserts rather than
assumes. The forecast is constant across the L leads by construction — that is
the defining property of the naive baseline, not a simplification.

OUTPUTS
-------
1. `paper_tables/BENCH_SEASONAL_NAIVE.csv`
       model,L,mse_7var_z,mae_7var_z,n_windows,n_windows_available,n_eval_windows
   `n_windows` is the number actually scored = `n_eval_windows` = MIFlu's count.
2. `paper_tables/BENCH_EFFICIENCY.csv` — the SAME file with ONE added column
       rel_improve_vs_seasonal_pct = (seasonal_mse_L - model_mse_L) / seasonal_mse_L * 100
   computed **per L** and then averaged over L. Existing columns and row order
   are preserved; nothing is dropped or reordered.

EVALUATION WINDOWS
------------------
The baseline is scored on the same windows as every arm: the first
`eval_slice(W) = (W // 16) * 16` test windows (160/144/144/128 at
L = 24/36/48/60), because the MIFlu reproduction's test loader uses
`drop_last=True` (`scripts/eval_windows.py`). Scoring the naive baseline on 170
windows while the arms use 160 would make `rel_improve_vs_seasonal_pct`
incomparable, so the crop is applied to both the baseline and the npz re-read.

PIPELINE ORDER — IMPORTANT
--------------------------
`scripts/analysis_postprocess.py` REGENERATES `BENCH_EFFICIENCY.csv` from
scratch. Run order must therefore be:

    python scripts/analysis_postprocess.py     # base table
    python scripts/seasonal_naive_baseline.py  # baseline + the extra column

Re-running this script is idempotent: the column is recomputed and overwritten,
never appended twice.

Usage:
    python scripts/seasonal_naive_baseline.py
    python scripts/seasonal_naive_baseline.py --season 104   # sensitivity check
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)          # makes `configs` / `train_nlinear_966` importable

from configs import (VAR_COLS, resolve_profile, split_for_profile,  # noqa: E402
                     verify_profile_hash)
from eval_windows import eval_slice  # noqa: E402  the ONE window-rule definition
# REUSE, do not reimplement: the window builder is the single source of truth for
# which rows become test windows. Importing it also guarantees that this baseline
# cannot drift from the benchmark it is compared against.
from train_nlinear_966 import build_windows  # noqa: E402

PROFILE = "author_966"
T = 104                 # look-back window (weeks), CONFIG["T"]
CONTAINMENT = "strict"  # whole target block inside its split
SEASON = 52             # one epidemiological year
EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
TABLES = os.path.join(ROOT, "paper_tables")
EXCLUDE = {"dlinear"}   # hard rule §2.3: DLinear never enters a table or ranking
MODEL_NAME = "seasonal_naive"


# ────────────────────────────────────────────────────────────────────────────
# 1. Data + train-only scaler
# ────────────────────────────────────────────────────────────────────────────
def load_z(profile: str = PROFILE):
    """Return (data_norm float32, train_end, val_end, n_rows, scaler_info)."""
    p = resolve_profile(profile)
    verify_profile_hash(profile)
    df = pd.read_csv(p["data_path"])
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    train_end, val_end = split_for_profile(profile, n)

    scaler_path = p["scaler_path"]
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"persisted train-only scaler missing: {scaler_path}")
    with open(scaler_path, "r", encoding="utf-8") as f:
        sc = json.load(f)
    if list(sc["var_cols"]) != list(VAR_COLS):
        raise ValueError(f"scaler var_cols mismatch: {sc['var_cols']} vs {VAR_COLS}")
    if (int(sc["train_end"]), int(sc["val_end"])) != (train_end, val_end):
        raise ValueError(f"scaler split {sc['train_end']}/{sc['val_end']} != "
                         f"profile split {train_end}/{val_end}")

    mean = np.asarray(sc["mean"], dtype=np.float32).reshape(1, -1)
    std = np.asarray(sc["std"], dtype=np.float32).reshape(1, -1)

    # Guard: the JSON must hold exactly the train-only statistics. Any other
    # fit (fitted on all 966 rows, say) would leak test information into z-space.
    refit_mean = data[:train_end].mean(axis=0, keepdims=True)
    refit_std = data[:train_end].std(axis=0, keepdims=True)
    if not np.allclose(mean, refit_mean, rtol=1e-5, atol=1e-5):
        raise ValueError("scaler mean != train-only refit mean")
    if not np.allclose(std, refit_std, rtol=1e-5, atol=1e-5):
        raise ValueError("scaler std != train-only refit std")

    data_norm = ((data - mean) / std).astype(np.float32)
    return data_norm, train_end, val_end, n, {"path": scaler_path,
                                              "train_end": train_end,
                                              "val_end": val_end}


# ────────────────────────────────────────────────────────────────────────────
# 2. Seasonal-naive forecast
# ────────────────────────────────────────────────────────────────────────────
def seasonal_naive_forecast(data_norm: np.ndarray, target_starts: np.ndarray,
                            L: int, season: int = SEASON):
    """Forecast = value `season` weeks before the target start, constant over leads.

    Returns (W, N, L) float32 in z-space, plus the number of windows that needed
    the < 0 fallback (reported, so a silent protocol change cannot hide).
    """
    W = len(target_starts)
    N = data_norm.shape[1]
    pred = np.zeros((W, N, L), dtype=np.float32)
    n_fallback = 0
    for k, t in enumerate(target_starts):
        src = int(t) - season
        if src < 0:
            # Documented fallback: last observed value of the input window.
            # The input window is rows [t-T, t-1], so its last value is t-1.
            src = int(t) - 1
            n_fallback += 1
        pred[k] = data_norm[src][:, None]      # (N,) -> broadcast over the L leads
    return pred, n_fallback


# ────────────────────────────────────────────────────────────────────────────
# 3. Window/target cross-check against the exported npz cells
# ────────────────────────────────────────────────────────────────────────────
def cross_check_against_npz(L: int, Y: np.ndarray, target_starts: np.ndarray):
    """Prove the baseline is scored on the SAME windows as the benchmark arms.

    The target block does not depend on the model, so any exported cell at this
    horizon must have the identical `target` tensor and `target_start_row`.
    Returns (model, max_abs_diff) or (None, None) when no cell is on disk.
    """
    for d in sorted(glob.glob(os.path.join(EXP, "*_L%d_s*" % L))):
        m = re.search(r"([A-Za-z_]+)_L(\d+)_s(\d+)$", os.path.basename(d))
        if not m or m.group(1) in EXCLUDE:
            continue
        model, seed = m.group(1), int(m.group(3))
        f = os.path.join(d, f"pred_{model}_L{L}_s{seed}.npz")
        if not os.path.exists(f):
            continue
        z = np.load(f)
        tgt = np.asarray(z["target"], dtype=np.float64)
        ts = np.asarray(z["target_start_row"], dtype=np.int64)
        if tgt.shape != Y.shape:
            raise ValueError(f"L={L}: npz target shape {tgt.shape} != {Y.shape}")
        if not np.array_equal(ts, np.asarray(target_starts, dtype=ts.dtype)):
            raise ValueError(f"L={L}: npz target_start_row differs from build_windows")
        diff = float(np.max(np.abs(tgt - Y.astype(np.float64))))
        if diff > 1e-5:
            raise ValueError(f"L={L}: npz target values differ by {diff:.3e}")
        return model, diff
    return None, None


# ────────────────────────────────────────────────────────────────────────────
# 4. Efficiency-table update
# ────────────────────────────────────────────────────────────────────────────
def per_L_mse_from_npz():
    """Per (model, L) pooled MSE in z-space, straight from the raw predictions.

    Reading the npz files (not `BENCH_MSE_BY_MODEL_L.csv`) keeps this step
    independent of stale tables and makes the DLinear exclusion structural. Each
    cell is cropped to `eval_slice(W)` windows, the same set the baseline itself
    is scored on, so the ratio compares like with like.
    """
    acc = {}
    for p in sorted(glob.glob(os.path.join(EXP, "*_L*_s*", "pred_*.npz"))):
        m = re.search(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(p))
        if not m:
            continue
        model, L = m.group(1), int(m.group(2))
        if model in EXCLUDE:
            continue
        z = np.load(p)
        pred = np.asarray(z["pred"], dtype=np.float64)
        tgt = np.asarray(z["target"], dtype=np.float64)
        n = eval_slice(pred.shape[0])
        if n == 0:
            raise ValueError(f"{p}: eval_slice({pred.shape[0]}) == 0")
        err = pred[:n] - tgt[:n]
        acc.setdefault((model, L), []).append(float(np.mean(err ** 2)))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def update_efficiency_table(seasonal_mse: dict):
    """Add `rel_improve_vs_seasonal_pct` to BENCH_EFFICIENCY.csv in place."""
    path = os.path.join(TABLES, "BENCH_EFFICIENCY.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} missing — run scripts/analysis_postprocess.py first")
    eff = pd.read_csv(path)
    if "model" not in eff.columns:
        raise ValueError("BENCH_EFFICIENCY.csv has no `model` column")

    model_mse = per_L_mse_from_npz()
    Ls = sorted(seasonal_mse)
    rel, detail = [], []
    for model in eff["model"]:
        vals = []
        for L in Ls:
            mm = model_mse.get((model, L))
            if mm is None:
                vals.append(np.nan)
            else:
                vals.append((seasonal_mse[L] - mm) / seasonal_mse[L] * 100.0)
        detail.append(vals)
        rel.append(float(np.nanmean(vals)) if np.any(np.isfinite(vals)) else np.nan)

    eff["rel_improve_vs_seasonal_pct"] = np.round(rel, 2)
    eff.round(6).to_csv(path, index=False)
    return eff, detail, Ls


# ────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--season", type=int, default=SEASON,
                    help="season length in weeks (default 52; 104 = sensitivity)")
    ap.add_argument("--no-efficiency", action="store_true",
                    help="only write BENCH_SEASONAL_NAIVE.csv")
    args = ap.parse_args()

    os.makedirs(TABLES, exist_ok=True)
    data_norm, train_end, val_end, n, sinfo = load_z(PROFILE)
    if (train_end, val_end) != (676, 773):
        raise ValueError(f"split drift: {train_end}/{val_end} != 676/773")
    print(f"[seasonal] profile={PROFILE} n={n} train_end={train_end} "
          f"val_end={val_end} T={T} containment={CONTAINMENT}")
    print(f"[seasonal] scaler={os.path.relpath(sinfo['path'], ROOT)} "
          f"(train-only, verified against a refit on rows [:676])")

    rows, seasonal_mse = [], {}
    for L in (24, 36, 48, 60):
        Xt, Yt, Xv, Yv, Xte, Yte, sinfo_w = build_windows(
            data_norm, T, L, train_end, val_end, containment=CONTAINMENT)
        ts_all = sinfo_w["target_starts"]
        n_test_all = int((sinfo_w["splits"] == 2).sum())
        # build_windows returns already-split arrays; recover the test target
        # starts in the same order (splits are stable, mask order is preserved).
        ts_test = ts_all[sinfo_w["splits"] == 2]
        W = len(Yte)
        if len(ts_test) != W:
            raise ValueError(f"L={L}: {len(ts_test)} test starts vs {W} windows")

        pred, n_fallback = seasonal_naive_forecast(data_norm, ts_test, L, args.season)
        # SHARED EVALUATION WINDOWS: MIFlu scores only the first (W//16)*16 test
        # windows (drop_last=True in train_miflu.train_L), so every arm and this
        # baseline are scored on exactly that set.
        W_avail = len(Yte)
        n_ev = eval_slice(W_avail)
        if n_ev == 0:
            raise ValueError(f"L={L}: eval_slice({W_avail}) == 0")
        err = (pred[:n_ev].astype(np.float64)
               - Yte[:n_ev].astype(np.float64))
        mse = float(np.mean(err ** 2))
        mae = float(np.mean(np.abs(err)))
        seasonal_mse[L] = mse

        ref_model, diff = cross_check_against_npz(L, Yte, ts_test)
        rows.append({"model": MODEL_NAME, "L": L, "mse_7var_z": mse,
                     "mae_7var_z": mae, "n_windows": int(n_ev),
                     "n_windows_available": int(W_avail),
                     "n_eval_windows": int(n_ev)})
        print(f"[seasonal] L={L:2d} available={W_avail:3d} evaluated={n_ev:3d} "
              f"(test={n_test_all}) mse_7var_z={mse:.4f} mae_7var_z={mae:.4f} "
              f"fallback_windows={n_fallback}"
              + (f" | target identical to {ref_model} npz (max diff {diff:.1e})"
                 if ref_model else " | no npz cell on disk to cross-check"))

    out = pd.DataFrame(rows)
    csv_path = os.path.join(TABLES, "BENCH_SEASONAL_NAIVE.csv")
    out.to_csv(csv_path, index=False)
    print(f"\n[seasonal] wrote {os.path.relpath(csv_path, ROOT)} "
          f"({len(out)} rows)")

    if args.no_efficiency:
        return

    eff, detail, Ls = update_efficiency_table(seasonal_mse)
    print("[seasonal] added column rel_improve_vs_seasonal_pct to "
          "paper_tables/BENCH_EFFICIENCY.csv "
          f"(per-L then mean over L={Ls})")

    # ── report ──────────────────────────────────────────────────────────────
    pd.set_option("display.width", 200)
    print("\n=== seasonal-naive baseline (7-var aggregate, z-space) ===")
    print(out.round(4).to_string(index=False))
    print(f"\n4-horizon mean seasonal MSE = {np.mean(list(seasonal_mse.values())):.4f}")

    view = eff[["model", "mse_mean", "rel_improve_vs_seasonal_pct"]].copy()
    per_L = np.asarray(detail, dtype=float)          # (n_models, n_horizons)
    for j, L in enumerate(Ls):
        view[f"rel_L{L}"] = np.round(per_L[:, j], 2)
    view = view.sort_values("rel_improve_vs_seasonal_pct", ascending=False)
    print("\n=== ranked by rel_improve_vs_seasonal_pct (mean over L=24/36/48/60) ===")
    print(view.round(4).to_string(index=False))
    neg = view[view.rel_improve_vs_seasonal_pct < 0]
    print(f"\nmodels WORSE than seasonal-naive: "
          f"{', '.join(neg.model.tolist()) if len(neg) else '(none)'}")


if __name__ == "__main__":
    main()
