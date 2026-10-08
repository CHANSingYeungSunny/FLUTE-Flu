#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s1_write_csvs.py
================
Emit the Track S deliverable CSVs from the HPC job logs (test mse/mae/best_ep)
and the frozen Track C MIFlu per-cell values.

Outputs (results/v3_clean/analysis/peak_criteria/):
  S1ES_RESULTS_PER_FIT.csv   - one row per Track S fit
  S1ES_VS_TRACK_C.csv         - within-seed comparison vs the frozen champion
"""
from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria")

# (L, seed): (test_mse, test_mae, best_epoch, elapsed_sec)
# from HPC s1es logs; L60/seed43 is the one cell where early stopping diverges.
S1ES = {
    (24, 42): (1.885572, 0.871653, 6, 265),
    (36, 42): (1.809880, 0.856878, 14, 435),
    (48, 42): (1.709283, 0.861811, 12, 379),
    (60, 42): (1.761910, 0.870366, 15, 432),
    (24, 43): (2.010233, 0.884279, 8, 311),
    (36, 43): (2.161865, 0.929923, 10, 346),
    (48, 43): (1.818424, 0.908483, 11, 358),
    (60, 43): (2.024601, 0.974195, 3, 178),
    (24, 44): (2.009913, 0.881989, 11, 379),
    (36, 44): (1.827874, 0.870159, 15, 457),
    (48, 44): (1.736302, 0.863173, 16, 443),
    (60, 44): (1.770262, 0.878383, 15, 429),
}

PATIENCE = 5


def main():
    # Track C MIFlu per-cell
    p = os.path.join(ROOT, "hpc_results",
                     "official_repo_reproduction_20261006",
                     "r1_v2_verification_20261007", "TRACK_C_RESULTS_PER_CELL.csv")
    tc = {}
    with open(p, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if "miflu" in r["model"].lower():
                tc[(int(r["L"]), int(r["seed"]))] = float(r["mse"])

    # S1ES_RESULTS_PER_FIT.csv
    per = os.path.join(OUT, "S1ES_RESULTS_PER_FIT.csv")
    with open(per, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["patience", "L", "seed", "test_mse", "test_mae",
                    "best_epoch", "stopped_at_epoch", "epochs_run", "elapsed_sec"])
        for (L, s), (mse, mae, bep, el) in sorted(S1ES.items()):
            stopped = min(bep + PATIENCE, 20)
            w.writerow([PATIENCE, L, s, mse, mae, bep, stopped, stopped, el])
    print(f"[write] {per}")

    # S1ES_VS_TRACK_C.csv
    comp = os.path.join(OUT, "S1ES_VS_TRACK_C.csv")
    with open(comp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["L", "seed", "track_c_mse", "s1es_mse", "abs_diff",
                    "best_epoch_s1es", "stopped_at_epoch", "identical"])
        for (L, s), (mse, mae, bep, el) in sorted(S1ES.items()):
            c = tc.get((L, s))
            diff = ""
            identical = ""
            if c is not None:
                diff = round(mse - c, 6)
                identical = "YES" if abs(diff) < 1e-6 else "NO"
            stopped = min(bep + PATIENCE, 20)
            w.writerow([L, s, c, mse, diff, bep, stopped, identical])
    print(f"[write] {comp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
