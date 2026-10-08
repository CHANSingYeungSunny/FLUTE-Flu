#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_r1c_results.py
====================
Parse every R1-C Slurm log into a tidy per-fit table and write the final
three-seed candidate means.

Reads:  hpc_results/official_repo_reproduction_20261006/
            r1_v2_verification_20261007/r1c_logs/logs/r1c_*.out
Writes: R1C_RESULTS_PER_CANDIDATE.csv   (per fit + per-seed mean_4L + 3-seed mean)
        R1C_PAPER_GAP_ANALYSIS.json     (gap arithmetic, recomputed)
"""
from __future__ import annotations

import glob
import json
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGDIR = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                      "r1_v2_verification_20261007", "r1c_logs", "logs")
OUTDIR = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                      "r1_v2_verification_20261007")

PAPER_MSE = {24: 1.542, 36: 1.422, 48: 1.414, 60: 1.364}
PAPER_MAE = {24: 0.726, 36: 0.779, 48: 0.757, 60: 0.719}
PAPER_MSE_MEAN = 1.4355
PAPER_MAE_MEAN = 0.74525

ARM_NAME = {"C0": "C0_r1b_constant_lr", "C1": "C1_released_type1_scheduler"}


def main():
    fits = []
    for p in sorted(glob.glob(os.path.join(LOGDIR, "r1c_*.out"))):
        txt = open(p, encoding="utf-8", errors="replace").read()
        mjob = re.search(r"job=(\S+)\s+arm=(\S+)\s+sched=(\S+)\s+L=(\d+)\s+seed=(\d+)", txt)
        mres = re.search(r"test mse=([\d.]+)\s+mae=([\d.]+)\s+n=\d+\s+best_ep=(\d+)", txt)
        mval = re.search(r"val mse=([\d.]+)", txt)
        if not (mjob and mres):
            continue
        job, arm, sched, L, seed = mjob.groups()
        mse, mae, ep = mres.groups()
        fits.append(dict(
            job=job, arm=ARM_NAME.get(arm, arm), sched=sched,
            L=int(L), seed=int(seed),
            test_mse=float(mse), test_mae=float(mae),
            best_epoch=int(ep),
            val_mse=float(mval.group(1)) if mval else ""))

    if not fits:
        print("[parse] no fits found")
        return 1

    rows = []
    for f in sorted(fits, key=lambda r: (r["arm"], r["seed"], r["L"])):
        rows.append([f["arm"], f["seed"], f["L"], f["test_mse"], f["test_mae"],
                     f["best_epoch"], f["val_mse"], f["job"], 0, "COMPLETE"])

    # per (arm, seed) mean over the four horizons
    summary = {}
    for arm in sorted({f["arm"] for f in fits}):
        for seed in sorted({f["seed"] for f in fits if f["arm"] == arm}):
            fs = [f for f in fits if f["arm"] == arm and f["seed"] == seed]
            if len(fs) != 4:
                continue
            mse = statistics.mean(f["test_mse"] for f in fs)
            mae = statistics.mean(f["test_mae"] for f in fs)
            rows.append([arm, seed, "mean_4L", round(mse, 6), round(mae, 6),
                         "", "", "-", "", "COMPLETE"])
            summary.setdefault(arm, {})[seed] = dict(mse=mse, mae=mae)

    # per arm: mean over the three seeds
    final = {}
    for arm, byseed in summary.items():
        if len(byseed) < 2:
            continue
        mses = [v["mse"] for v in byseed.values()]
        maes = [v["mae"] for v in byseed.values()]
        m = statistics.mean(mses)
        sd = statistics.stdev(mses) if len(mses) > 1 else 0.0
        rows.append([arm, "ALL", "mean_3seed_4L", round(m, 6),
                     round(statistics.mean(maes), 6),
                     "", "", "-", "",
                     f"SD={sd:.4f} n_seeds={len(mses)}"])
        final[arm] = dict(mean_mse=m, sd_mse=sd, mean_mae=statistics.mean(maes),
                          n_seeds=len(mses))

    out = os.path.join(OUTDIR, "R1C_RESULTS_PER_CANDIDATE.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        fh.write("candidate_id,seed,horizon,test_mse,test_mae,best_epoch,"
                 "val_mse,job_id,rc,status\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    print(f"[write] {out}")

    # gap arithmetic
    gap = {}
    for arm, d in final.items():
        m = d["mean_mse"]
        gap[arm] = dict(
            mean_average_MSE_4L=round(m, 6),
            sd=round(d["sd_mse"], 6),
            mean_average_MAE_4L=round(d["mean_mae"], 6),
            n_seeds=d["n_seeds"],
            absolute_gap_vs_paper=round(m - PAPER_MSE_MEAN, 6),
            relative_gap_pct=round((m - PAPER_MSE_MEAN) / PAPER_MSE_MEAN * 100, 2),
            inside_pm0p10_of_4=0)
    # per-horizon band check using the per-seed mean
    for arm in final:
        cnt = 0
        for L in (24, 36, 48, 60):
            vs = [f["test_mse"] for f in fits if f["arm"] == arm and f["L"] == L]
            if vs and abs(statistics.mean(vs) - PAPER_MSE[L]) <= 0.10:
                cnt += 1
        gap[arm]["inside_pm0p10_of_4"] = cnt

    jout = os.path.join(OUTDIR, "R1C_PAPER_GAP_ANALYSIS.json")
    with open(jout, "w", encoding="utf-8") as fh:
        json.dump(dict(paper_target=dict(MSE_mean=PAPER_MSE_MEAN,
                                         MAE_mean=PAPER_MAE_MEAN,
                                         by_L_MSE=PAPER_MSE),
                       candidates=gap,
                       note="three-seed means; judgement per candidate"),
                  fh, indent=2)
    print(f"[write] {jout}")

    print("\n=== FINAL (3-seed) ===")
    for arm, d in gap.items():
        print(f"{arm:32s} MSE={d['mean_average_MSE_4L']:.4f} "
              f"SD={d['sd']:.4f}  rel_gap={d['relative_gap_pct']}%  "
              f"inside_band={d['inside_pm0p10_of_4']}/4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
