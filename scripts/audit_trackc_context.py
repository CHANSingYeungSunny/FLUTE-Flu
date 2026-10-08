#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_trackc_context.py
=======================
Track-C context checks for the Q2 (temporal/COVID) and Q3 (scaler/units) audits.

* Maps the strict-966 Train/Val/Test row ranges to real calendar dates.
* Checks whether the COVID-19 period (2020-01 .. 2021-12) overlaps the Track C
  Test block -- the historical Q2 "2021-02-07 hallucination peak" lived in a
  DIFFERENT (earlier, wider) test split and may NOT appear under the strict-966
  contract.
* Computes raw descriptive statistics of every column over Train rows [0,676)
  for the Q3 variable-label / physical-unit sanity check.
* Verifies the train-only scaler round-trip.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "recovery", "author_repo", "dataset", "illness",
                   "national_illness.csv")
SCALER = os.path.join(ROOT, "audit_20260930", "predictions_stage6",
                      "scaler_train_only.json")

TRAIN_N, VAL_N, TEST_N = 676, 97, 193
TEST_START = TRAIN_N + VAL_N          # 773
TEST_END = TEST_START + TEST_N - 1    # 965


def main():
    rows = []
    with open(DATA, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        header = next(r)
        for line in r:
            rows.append(line)
    print("header:", header)
    print("total data rows:", len(rows))
    # columns: date,1,2,3,4,5,6,OT  -> 7 features + date
    feats = header[1:]                # ['1','2','3','4','5','6','OT']

    def date_of(row_idx):
        return dt.datetime.strptime(rows[row_idx][0].split()[0], "%Y-%m-%d").date()

    print("\n=== row -> date map ===")
    for label, idx in [("train_start", 0), ("train_end", TRAIN_N - 1),
                       ("val_start", TRAIN_N), ("val_end", TRAIN_N + VAL_N - 1),
                       ("test_start", TEST_START), ("test_end", TEST_END),
                       ("data_end", len(rows) - 1)]:
        print(f"  {label:11s} row {idx:4d} -> {date_of(idx)}")

    # COVID overlap with test block
    covid_lo = dt.date(2020, 1, 1)
    covid_hi = dt.date(2021, 12, 31)
    ts, te = date_of(TEST_START), date_of(TEST_END)
    print("\n=== COVID overlap with Track C Test ===")
    print(f"  Test block: {ts} .. {te}")
    print(f"  COVID window: {covid_lo} .. {covid_hi}")
    print(f"  Test overlaps COVID window: {ts <= covid_hi and te >= covid_lo}")
    print(f"  Test fully inside COVID window: {ts >= covid_lo and te <= covid_hi}")
    print(f"  Test weeks inside COVID window: "
          f"{max(0, (min(te, covid_hi) - max(ts, covid_lo)).days // 7 + 1)}")
    # is 2021-02-07 inside test?
    peak = dt.date(2021, 2, 7)
    print(f"  2021-02-07 (historical hallucination peak) in Test: "
          f"{ts <= peak <= te}")

    # descriptive stats over train rows [0,676) per feature
    print("\n=== Train [0,676) descriptive stats (raw units) ===")
    print(f"  {'feat':>4} {'min':>12} {'max':>12} {'mean':>12}")
    for ci, name in enumerate(feats):
        vals = []
        for ri in range(TRAIN_N):
            try:
                vals.append(float(rows[ri][ci + 1]))
            except ValueError:
                pass
        if vals:
            print(f"  {name:>4} {min(vals):>12.2f} {max(vals):>12.2f} "
                  f"{sum(vals)/len(vals):>12.2f}")

    # scaler round trip on the target variable index used by PTE/PIE (ILI=4)
    if os.path.exists(SCALER):
        sc = json.load(open(SCALER))
        print("\n=== scaler_train_only.json ===")
        print(json.dumps(sc, indent=2))
        # find which key corresponds to target index 4
        print("\n=== round-trip check on raw column values (train) ===")
        for ci, name in enumerate(feats):
            if name not in sc:
                continue
            mean = sc[name]["mean"]
            scale = sc[name]["scale"]
            sample = [float(rows[ri][ci + 1]) for ri in range(0, 5)]
            rt = [v * scale + mean for v in sample]
            back = [(v - mean) / scale for v in rt]
            err = max(abs(sample[i] - back[i]) for i in range(len(sample)))
            print(f"  feat {name}: physical_mean={mean:.4f} scale={scale:.4f} "
                  f"roundtrip_max_err={err:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
