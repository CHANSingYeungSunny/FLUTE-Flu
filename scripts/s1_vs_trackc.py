#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s1_vs_trackc.py
===============
Compare Track S (patience=5 early stopping) MIFlu fits against the frozen
Track C MIFlu cells, within seed. Both are the same config; only the stopping
rule differs.

S1ES values are taken from the HPC job logs (grep "test mse"). The duplicate
L24/seed42 job (610793 and 610796, both = 1.885572) is collapsed to one cell.
"""
from __future__ import annotations

import csv
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (L, seed) -> (test_mse, test_mae, best_epoch)  from HPC s1es logs
S1ES = {
    (24, 42): (1.885572, 0.871653, 6),
    (36, 42): (1.809880, 0.856878, 14),
    (48, 42): (1.709283, 0.861811, 12),
    (60, 42): (1.761910, 0.870366, 15),
    (24, 43): (2.010233, 0.884279, 8),
    (36, 43): (2.161865, 0.929923, 10),
    (48, 43): (1.818424, 0.908483, 11),
    (60, 43): (2.024601, 0.974195, 3),
    (24, 44): (2.009913, 0.881989, 11),
    (36, 44): (1.827874, 0.870159, 15),
    (48, 44): (1.736302, 0.863173, 16),
    (60, 44): (1.770262, 0.878383, 15),
}


def main():
    p = os.path.join(ROOT, "hpc_results",
                     "official_repo_reproduction_20261006",
                     "r1_v2_verification_20261007", "TRACK_C_RESULTS_PER_CELL.csv")
    tc = {}
    with open(p, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if "miflu" in r["model"].lower():
                tc[(int(r["L"]), int(r["seed"]))] = float(r["mse"])

    print("L  seed  TrackC_MSE  S1ES_MSE   diff      best_ep")
    diffs, cs, es = [], [], []
    identical = 0
    for key in sorted(S1ES):
        L, s = key
        c = tc.get(key)
        v = S1ES[key]
        d = v[0] - c if c is not None else None
        cs.append(c)
        es.append(v[0])
        if c is not None and abs(d) < 1e-6:
            identical += 1
        diffs.append(d)
        print("{:>2} {:>4}  {:>9.6f}  {:>9.6f}  {:>+9.6f}  {:>5}".format(
            L, s, c if c is not None else 0.0, v[0], d if d is not None else 0.0,
            v[2]))

    n = len(S1ES)
    print("\nidentical cells (|diff|<1e-6): {}/{}".format(identical, n))
    print("TrackC mean(average_MSE_4L) = {:.6f}".format(statistics.mean(cs)))
    print("S1ES   mean(average_MSE_4L) = {:.6f}".format(statistics.mean(es)))
    print("mean abs diff = {:.6f}".format(statistics.mean(abs(x) for x in diffs
                                                          if x is not None)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
