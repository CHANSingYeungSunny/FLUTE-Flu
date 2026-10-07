#!/usr/bin/env python3
"""
score_4v4_replacement.py — Phase F.

Builds the OLD and NEW 4-vs-4 rankings from stored predictions, using ONE
scorer, so the only difference between the two sides is the MIFlu slot.

OLD side : the 8 historical models exactly as they stand.
NEW side : identical, except `gpt2_miflu` -> `miflu_official_transferred`.

Metric arithmetic follows clean_metrics.py:
    mse_all_7vars_full_horizon_z = mean over all valid (origin, var, step)
    average_MSE_4L               = mean of the four per-L values

Win rule (per the authorisation): diff = A - B; A wins only when diff < 0.
Lower MSE/MAE is better.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re

import numpy as np
import pandas as pd

LLM_SIDE_OLD = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
NONLLM_SIDE = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM_SIDE_NEW = ["miflu_official_transferred", "qwen_time_llm", "calf_llm",
                "timecma_llm"]
HORIZONS = (24, 36, 48, 60)
OLD_MIFLU = "gpt2_miflu"
NEW_MIFLU = "miflu_official_transferred"


def mse_mae(df):
    e = df.y_pred_z.values.astype(np.float64) - df.y_true_z.values.astype(np.float64)
    return float(np.mean(e ** 2)), float(np.mean(np.abs(e)))


def collect_old(durable, split):
    """model -> L -> seed -> (mse, mae, n)"""
    out = {}
    for name in os.listdir(durable):
        m = re.match(r"primary__([a-z0-9_]+)__L(24|36|48|60)__seed(4[2-9]|5[01])__w1$", name)
        if not m:
            continue
        model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
        p = os.path.join(durable, name, "predictions", f"{split}_predictions.csv")
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            continue
        df = pd.read_csv(p, usecols=["y_true_z", "y_pred_z"])
        out.setdefault(model, {}).setdefault(L, {})[seed] = mse_mae(df) + (len(df),)
    return out


def collect_new(runs_root, split):
    out = {}
    if not os.path.isdir(runs_root):
        return out
    for name in os.listdir(runs_root):
        m = re.match(r"miflu_transfer__L(24|36|48|60)__seed(\d+)$", name)
        if not m:
            continue
        L, seed = int(m.group(1)), int(m.group(2))
        p = os.path.join(runs_root, name, f"{split}_predictions_{name}.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p, usecols=["y_true_z", "y_pred_z"])
        out.setdefault(NEW_MIFLU, {}).setdefault(L, {})[seed] = mse_mae(df) + (len(df),)
    return out


def avg4(store, model):
    per = []
    for L in HORIZONS:
        vals = [v[0] for v in store.get(model, {}).get(L, {}).values()]
        if vals:
            per.append(float(np.mean(vals)))
    return float(np.mean(per)) if len(per) == 4 else None


def ranking(store, models):
    rows = []
    for mo in models:
        per = {L: (float(np.mean([v[0] for v in store.get(mo, {}).get(L, {}).values()]))
                   if store.get(mo, {}).get(L) else None) for L in HORIZONS}
        a = avg4(store, mo)
        n = sum(len(store.get(mo, {}).get(L, {})) for L in HORIZONS)
        rows.append({"model": mo, "average_MSE_4L": a,
                     **{f"L{L}": per[L] for L in HORIZONS}, "n_runs": n})
    rows = [r for r in rows if r["average_MSE_4L"] is not None]
    rows.sort(key=lambda r: r["average_MSE_4L"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--durable", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    res = {}

    # ---------- VALIDATION ranking ----------
    old_v = collect_old(a.durable, "validation")
    new_v = collect_new(a.runs, "validation")
    merged = {k: v for k, v in old_v.items()}
    merged[NEW_MIFLU] = new_v.get(NEW_MIFLU, {})

    old_rank = ranking({k: v for k, v in old_v.items()}, LLM_SIDE_OLD + NONLLM_SIDE)
    new_rank = ranking({**{k: v for k, v in old_v.items() if k != OLD_MIFLU},
                        NEW_MIFLU: new_v.get(NEW_MIFLU, {})},
                       LLM_SIDE_NEW + NONLLM_SIDE)

    res["validation_old"] = old_rank
    res["validation_new"] = new_rank

    # ---------- TEST/HOLDOUT comparison ----------
    # historical Test scope (verified): gpt2_miflu, nlinear, seasonal_naive
    old_t = collect_old(a.durable, "test")
    new_t = collect_new(a.runs, "test")
    res["test_old"] = ranking(old_t, [OLD_MIFLU, "nlinear"])
    res["test_new"] = ranking({**{k: v for k, v in old_t.items() if k != OLD_MIFLU},
                               NEW_MIFLU: new_t.get(NEW_MIFLU, {})},
                              [NEW_MIFLU, "nlinear"])

    # ---------- per-seed direction, old vs new MIFlu (validation) ----------
    per_seed = []
    for L in HORIZONS:
        for s in sorted(set(old_v.get(OLD_MIFLU, {}).get(L, {})) |
                        set(new_v.get(NEW_MIFLU, {}).get(L, {}))):
            o = old_v.get(OLD_MIFLU, {}).get(L, {}).get(s)
            n = new_v.get(NEW_MIFLU, {}).get(L, {}).get(s)
            if o and n:
                per_seed.append({"L": L, "seed": s,
                                 "old_mse": o[0], "new_mse": n[0],
                                 "diff": n[0] - o[0],
                                 "new_wins": (n[0] - o[0]) < 0})
    res["per_seed_validation"] = per_seed

    if per_seed:
        res["per_seed_summary"] = {
            "n": len(per_seed),
            "new_wins": int(sum(1 for r in per_seed if r["new_wins"])),
            "old_wins": int(sum(1 for r in per_seed if not r["new_wins"])),
            "mean_diff": float(np.mean([r["diff"] for r in per_seed])),
        }

    # ---------- group averages ----------
    def group_avg(store, models):
        vals = [avg4(store, mo) for mo in models]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None

    res["groups"] = {
        "old_validation": {
            "LLM_side": group_avg(old_v, LLM_SIDE_OLD),
            "nonLLM_side": group_avg(old_v, NONLLM_SIDE),
        },
        "new_validation": {
            "LLM_side": group_avg({**{k: v for k, v in old_v.items() if k != OLD_MIFLU},
                                   NEW_MIFLU: new_v.get(NEW_MIFLU, {})}, LLM_SIDE_NEW),
            "nonLLM_side": group_avg(old_v, NONLLM_SIDE),
        },
    }

    # ---------- rank change ----------
    orank = {r["model"]: r["rank"] for r in old_rank}
    nrank = {r["model"]: r["rank"] for r in new_rank}
    res["rank_change"] = {
        "old_miflu_rank": orank.get(OLD_MIFLU),
        "new_miflu_rank": nrank.get(NEW_MIFLU),
        "old_miflu_avg_MSE_4L": avg4(old_v, OLD_MIFLU),
        "new_miflu_avg_MSE_4L": avg4(new_v, NEW_MIFLU),
        "best_individual_old": old_rank[0]["model"] if old_rank else None,
        "best_individual_new": new_rank[0]["model"] if new_rank else None,
    }
    if (res["rank_change"]["old_miflu_avg_MSE_4L"] and
            res["rank_change"]["new_miflu_avg_MSE_4L"]):
        o = res["rank_change"]["old_miflu_avg_MSE_4L"]
        n = res["rank_change"]["new_miflu_avg_MSE_4L"]
        res["rank_change"]["abs_change"] = n - o
        res["rank_change"]["rel_change_pct"] = 100 * (n - o) / o

    json.dump(res, open(os.path.join(a.out, "FINAL_4V4_REPLACEMENT_RESULTS.json"), "w"),
              indent=2, default=str)

    # CSV for the record
    with open(os.path.join(a.out, "FINAL_4V4_REPLACEMENT_RESULTS.csv"), "w") as fh:
        fh.write("side,rank,model,average_MSE_4L,L24,L36,L48,L60,n_runs\n")
        for side, rows in (("old_validation", old_rank), ("new_validation", new_rank)):
            for r in rows:
                fh.write(f"{side},{r['rank']},{r['model']},{r['average_MSE_4L']:.6f},"
                         f"{r['L24']:.6f},{r['L36']:.6f},{r['L48']:.6f},{r['L60']:.6f},"
                         f"{r['n_runs']}\n")

    print("=== VALIDATION — OLD ===")
    for r in old_rank:
        print(f"  {r['rank']}. {r['model']:28s} avg_MSE_4L={r['average_MSE_4L']:.6f} (n={r['n_runs']})")
    print("=== VALIDATION — NEW (MIFlu slot replaced) ===")
    for r in new_rank:
        print(f"  {r['rank']}. {r['model']:28s} avg_MSE_4L={r['average_MSE_4L']:.6f} (n={r['n_runs']})")
    print("=== rank change ===")
    print(json.dumps(res["rank_change"], indent=2, default=str))
    if "per_seed_summary" in res:
        print("=== per-seed ===")
        print(json.dumps(res["per_seed_summary"], indent=2))
    print("=== groups ===")
    print(json.dumps(res["groups"], indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())