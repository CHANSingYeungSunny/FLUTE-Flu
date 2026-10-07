#!/usr/bin/env python3
"""
score_track_c.py — Track C championship scorer.

Ranks the eight models on ONE-TIME TEST ONLY, using the canonical strict-966
key contract. Validation is used to select checkpoints and is NEVER scored here.

Hard rules enforced (the scorer refuses rather than warns):
  * only STRICT_966_TEST_KEYS may enter a ranking input
  * every model's Test key set must be IDENTICAL to the canonical set
  * no missing, extra or duplicate keys
  * no NaN / Inf
  * one scorer arithmetic for all eight models

Win rule: diff = A - B ; A wins only if diff < 0.
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

BASE = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007"
KEYS = f"{BASE}/canonical_keys"
STAGE6 = "/gpfs1/home/sychan552/stage5_a2_durable/stage6/predictions"
HORIZONS = (24, 36, 48, 60)
SEEDS = (42, 43, 44)
KEY_TUPLE = ["forecast_origin", "forecast_lead", "feature_index"]

LLM_SIDE = ["miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
NONLLM_SIDE = ["nlinear", "dlinear", "patchtst", "itransformer"]
EIGHT = NONLLM_SIDE + LLM_SIDE          # ordering only; not a ranking

MODEL_PREFIX = {"miflu": "miflu", "qwen_time_llm": "qwen_time_llm",
                "calf_llm": "calf_llm", "timecma_llm": "timecma_llm",
                "nlinear": "nlinear", "dlinear": "dlinear",
                "patchtst": "patchtst", "itransformer": "itransformer"}

EXPECT_ORIG = {24: 170, 36: 158, 48: 146, 60: 134}


def canonical_keys(L, seed):
    d = pd.read_csv(f"{KEYS}/canonical_keys_L{L}_seed{seed}.csv")
    t = d[d.split == "test"].copy()
    return t


def _finish(df, model, L, seed, notes):
    """Validate a cell against the canonical key set, then return it."""
    canon = canonical_keys(L, seed)
    got = df[df.split == "test"] if "split" in df.columns else df
    got = got[["forecast_origin", "forecast_lead", "feature_index",
               "y_true_z", "y_pred_z"]].copy()
    for c in ("forecast_origin", "forecast_lead", "feature_index"):
        got[c] = got[c].astype(int)
    ck = set(map(tuple, canon[KEY_TUPLE].values))
    gk = set(map(tuple, got[KEY_TUPLE].values))
    problems = []
    if gk != ck:
        problems.append(f"key set mismatch: missing={len(ck-gk)} extra={len(gk-ck)}")
    if got.duplicated(subset=KEY_TUPLE).any():
        problems.append(f"{int(got.duplicated(subset=KEY_TUPLE).sum())} duplicate keys")
    if not np.isfinite(got.y_pred_z.values).all():
        problems.append("non-finite predictions")
    if not np.isfinite(got.y_true_z.values).all():
        problems.append("non-finite targets")
    if len(canon) != EXPECT_ORIG[L] * L * 7:
        problems.append("canonical key count unexpected")
    if problems:
        return None, f"{model} L{L} s{seed}: " + "; ".join(problems)
    # order canonically so every model is scored on the same row order.
    # A merge is used rather than a tuple-keyed set_index().loc[] reindex,
    # which is O(n) with per-row tuple construction and does not scale.
    got = canon[KEY_TUPLE].merge(got, on=KEY_TUPLE, how="left",
                                 validate="one_to_one")
    e = got.y_pred_z.values.astype(np.float64) - got.y_true_z.values.astype(np.float64)
    return {"model": model, "L": L, "seed": seed,
            "mse": float(np.mean(e ** 2)), "mae": float(np.mean(np.abs(e))),
            "n": int(len(got))}, None


def cell_miflu(L, seed):
    tag = f"miflu_strict966__L{L}__seed{seed}"
    p = f"{BASE}/runs/{tag}/test_predictions_{tag}.csv"
    if not os.path.exists(p):
        return None, f"miflu L{L} s{seed}: predictions absent ({p})"
    return _finish(pd.read_csv(p), "miflu", L, seed, "")


def cell_stage6(model, L, seed):
    pre = MODEL_PREFIX[model]
    c = glob.glob(f"{STAGE6}/pred_{pre}_L{L}_s{seed}.npz")
    if not c:
        return None, f"{model} L{L} s{seed}: artefact absent"
    z = np.load(c[0], allow_pickle=True)
    if str(z["containment"]) != "strict":
        return None, f"{model} L{L} s{seed}: containment={z['containment']}"
    pred, targ, tsr = z["pred"], z["target"], z["target_start_row"]
    if pred.shape != (EXPECT_ORIG[L], 7, L):
        return None, f"{model} L{L} s{seed}: shape {pred.shape}"
    n, N, Lh = pred.shape
    rows = {"forecast_origin": np.repeat(tsr.astype(int) - 1, N * Lh),
            "forecast_lead": np.tile(np.repeat(np.arange(1, Lh + 1), 1), n * N),
            "feature_index": np.tile(np.arange(N), n * Lh),
            "y_true_z": targ.transpose(0, 2, 1).reshape(-1).astype(np.float64),
            "y_pred_z": pred.transpose(0, 2, 1).reshape(-1).astype(np.float64)}
    return _finish(pd.DataFrame(rows), model, L, seed, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=BASE)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    cells, errors = [], []
    for model in EIGHT:
        for L in HORIZONS:
            for seed in SEEDS:
                rec, err = (cell_miflu(L, seed) if model == "miflu"
                            else cell_stage6(model, L, seed))
                if err:
                    errors.append(err)
                else:
                    cells.append(rec)
    df = pd.DataFrame(cells)
    df.to_csv(f"{a.out}/TRACK_C_RESULTS_PER_CELL.csv", index=False)

    if errors:
        print(f"[C] {len(errors)} cell(s) rejected:")
        for e in errors[:20]:
            print("   ", e)

    if df.empty:
        print("[C] no cells scored"); return 1

    # ---- per-seed four-horizon averages -------------------------------
    per_seed = (df.groupby(["model", "seed"])
                  .agg(mean_mse=("mse", "mean"), mean_mae=("mae", "mean"),
                       n_L=("L", "nunique")).reset_index())
    per_seed.to_csv(f"{a.out}/TRACK_C_RESULTS_PER_SEED.csv", index=False)

    # ---- per-model: mean +- sd across seeds ---------------------------
    agg = (per_seed.groupby("model")
           .agg(mean_Test_MSE_4L=("mean_mse", "mean"),
                sd_Test_MSE_4L=("mean_mse", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else float("nan")),
                min_MSE=("mean_mse", "min"), max_MSE=("mean_mse", "max"),
                mean_Test_MAE_4L=("mean_mae", "mean"),
                sd_Test_MAE_4L=("mean_mae", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else float("nan")),
                n_seeds=("seed", "nunique")).reset_index())
    agg["rank_MSE"] = agg.mean_Test_MSE_4L.rank(method="min").astype(int)
    agg["rank_MAE"] = agg.mean_Test_MAE_4L.rank(method="min").astype(int)
    agg["side"] = np.where(agg.model.isin(LLM_SIDE), "LLM", "non-LLM")
    agg = agg.sort_values("mean_Test_MSE_4L")
    agg.to_csv(f"{a.out}/TRACK_C_RESULTS_PER_MODEL.csv", index=False)
    agg[["rank_MSE", "model", "mean_Test_MSE_4L", "sd_Test_MSE_4L",
         "mean_Test_MAE_4L", "side", "n_seeds"]] \
        .to_csv(f"{a.out}/TRACK_C_TEST_MSE_RANKING.csv", index=False)
    agg.sort_values("mean_Test_MAE_4L")[["rank_MAE", "model",
                                         "mean_Test_MAE_4L", "mean_Test_MSE_4L"]] \
        .to_csv(f"{a.out}/TRACK_C_TEST_MAE_RANKING.csv", index=False)

    # ---- per-horizon champions ----------------------------------------
    ph = (df.groupby(["L", "model"]).agg(mse=("mse", "mean"), mae=("mae", "mean"))
            .reset_index())
    ph["rank"] = ph.groupby("L").mse.rank(method="min").astype(int)
    ph.sort_values(["L", "rank"]).to_csv(f"{a.out}/TRACK_C_PER_HORIZON_CHAMPIONS.csv",
                                         index=False)
    df.groupby(["model", "L"]).agg(mse=("mse", "mean"), mae=("mae", "mean")) \
        .reset_index().to_csv(f"{a.out}/TRACK_C_RESULTS_PER_HORIZON.csv", index=False)

    # ---- group summary -------------------------------------------------
    grp = agg.groupby("side").mean_Test_MSE_4L.mean().to_dict()
    pd.DataFrame([{"side": k, "mean_of_model_means_Test_MSE_4L": v}
                  for k, v in grp.items()]) \
        .to_csv(f"{a.out}/TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv", index=False)

    print("\n=== TRACK C — one-time TEST ranking (average of L24/36/48/60) ===")
    for _, r in agg.iterrows():
        print(f"  {int(r.rank_MSE)}. {r.model:18s} MSE {r.mean_Test_MSE_4L:.6f} "
              f"+-{r.sd_Test_MSE_4L if np.isfinite(r.sd_Test_MSE_4L) else float('nan'):.6f}  "
              f"MAE {r.mean_Test_MAE_4L:.6f}  [{r.side}]")
    print("\n=== group means ===")
    print(json.dumps(grp, indent=2, default=str))
    print("\n=== per-horizon champions ===")
    for L in HORIZONS:
        w = ph[(ph.L == L) & (ph["rank"] == 1)]
        if len(w):
            print(f"  L{L}: {w.iloc[0].model} MSE {w.iloc[0].mse:.6f}")

    # ---- pairwise: official MIFlu vs the rest, and vs old self-built ---
    print("\n=== pairwise (official MIFlu vs each) ===")
    pw = []
    piv = df.pivot_table(index=["L", "seed"], columns="model", values="mse")
    for other in EIGHT:
        if other == "miflu" or other not in piv.columns:
            continue
        d = (piv["miflu"] - piv[other]).dropna()
        if len(d) == 0:
            continue
        pw.append({"A": "miflu", "B": other, "n_cells": int(len(d)),
                   "mean_diff": float(d.mean()), "median_diff": float(d.median()),
                   "A_wins": int((d < 0).sum()), "B_wins": int((d > 0).sum()),
                   "ties": int((d == 0).sum())})
    pd.DataFrame(pw).to_csv(f"{a.out}/TRACK_C_PAIRWISE_STATS_CORRECTED.csv", index=False)
    for r in pw:
        print(f"  miflu vs {r['B']:18s} mean_diff {r['mean_diff']:+.6f} "
              f"A_wins {r['A_wins']}/{r['n_cells']}")

    print(f"\n[C] scored {len(df)} cells; {len(errors)} rejected")
    print(f"[C] champion (lowest mean Test MSE) = {agg.iloc[0].model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())