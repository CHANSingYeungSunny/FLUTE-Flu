#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_s1_results.py
====================
Parse every Track S (patience-based early stopping) fit and compare it, within
seed, against the frozen Track C MIFlu cell.

Reads:  results/v3_clean/analysis/peak_criteria/s1es_runs/runs/<tag>/...
Writes: results/v3_clean/analysis/peak_criteria/S1ES_RESULTS_PER_FIT.csv
        results/v3_clean/analysis/peak_criteria/S1ES_VS_TRACK_C.csv
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria")
RUNS = os.path.join(BASE, "s1es_runs", "runs")

HOR = {0: 24, 1: 36, 2: 48, 3: 60}


def main():
    fits = []
    for outp in glob.glob(os.path.join(RUNS, "*", "*.out")):
        txt = open(outp, encoding="utf-8", errors="replace").read()
        h = re.search(r"S1 early_stop=\d+ patience=(\d+) L=(\d+) seed=(\d+)", txt)
        m = re.search(r"test mse=([\d.]+) mae=([\d.]+).*best_ep=(\d+)", txt)
        if not (h and m):
            continue
        pat, L, seed = h.groups()
        # derive the tag dir to locate the manifest
        d = os.path.dirname(outp)
        man = None
        for j in glob.glob(os.path.join(d, "*.json")):
            try:
                man = json.load(open(j))
            except Exception:
                continue
            break
        fits.append(dict(
            patience=int(pat), L=int(L), seed=int(seed),
            test_mse=float(m.group(1)), test_mae=float(m.group(2)),
            best_epoch=int(m.group(3)),
            stopped_at=man.get("stopped_at_epoch") if man else None,
            epochs_run=man.get("epochs_run") if man else None))
    if not fits:
        print("[parse] no fits parsed")
        return 1
    fits.sort(key=lambda r: (r["L"], r["seed"]))

    # ---- Track C MIFlu cells ------------------------------------------
    tc = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                      "r1_v2_verification_20261007", "TRACK_C_RESULTS_PER_CELL.csv")
    tc_cell = {}
    if os.path.exists(tc):
        with open(tc, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if "miflu" in r.get("model", "").lower():
                    tc_cell[(int(r["L"]), int(r["seed"]))] = float(r["test_mse"])

    # ---- write per-fit -------------------------------------------------
    per = os.path.join(BASE, "S1ES_RESULTS_PER_FIT.csv")
    with open(per, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["patience", "L", "seed", "test_mse", "test_mae",
                    "best_epoch", "stopped_at_epoch", "epochs_run"])
        for f in fits:
            w.writerow([f["patience"], f["L"], f["seed"], f["test_mse"],
                        f["test_mae"], f["best_epoch"], f["stopped_at_epoch"],
                        f["epochs_run"]])
    print(f"[write] {per}")

    # ---- within-seed comparison ---------------------------------------
    comp = os.path.join(BASE, "S1ES_VS_TRACK_C.csv")
    with open(comp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["L", "seed", "track_c_mse", "s1es_mse", "abs_diff",
                    "best_epoch_s1es", "stopped_at", "identical"])
        for f in fits:
            key = (f["L"], f["seed"])
            tc_mse = tc_cell.get(key)
            diff = ""
            identical = ""
            if tc_mse is not None:
                diff = round(f["test_mse"] - tc_mse, 6)
                identical = "YES" if abs(diff) < 1e-6 else "no"
            w.writerow([f["L"], f["seed"], tc_mse, f["test_mse"], diff,
                        f["best_epoch"], f["stopped_at_epoch"], identical])
    print(f"[write] {comp}")

    # ---- summary -------------------------------------------------------
    same = sum(1 for f in fits if tc_cell.get((f["L"], f["seed"])) is not None
              and abs(f["test_mse"] - tc_cell[(f["L"], f["seed"])]) < 1e-6)
    print(f"\n=== summary: {len(fits)} fits, {same} identical to Track C ===")
    print(f"{'L':>3} {'seed':>4} {'TrackC':>9} {'S1ES':>9} {'diff':>9} "
          f"{'best_ep':>7} {'stopped':>7}")
    for f in fits:
        tc_mse = tc_cell.get((f["L"], f["seed"]))
        tc_s = f"{tc_mse:.6f}" if tc_mse is not None else "   n/a"
        print(f"{f['L']:>3} {f['seed']:>4} {tc_s:>9} {f['test_mse']:>9.6f} "
              f"{(f['test_mse']-tc_mse if tc_mse else 0):>+9.6f} "
              f"{f['best_epoch']:>7} {str(f['stopped_at_epoch']):>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
