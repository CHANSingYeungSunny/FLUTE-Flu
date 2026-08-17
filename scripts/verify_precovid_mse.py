#!/usr/bin/env python
"""Compare full-test vs Pre-COVID (2002-2019) MSE/MAE on the StandardScaler-space
prediction CSVs, to test the hypothesis: 'deviation from paper is mainly driven by
COVID-era distribution shift + CDC revisions, not code error'.

Pre-COVID threshold: abs_week where the target week < 2020-01 (epidemic week 202001).
abs_week 0 = 200201 (ISO). A target week w corresponds to calendar year of w.
We use target start week = abs_week (since prediction_ili[s] is week abs_week+s).
Pre-COVID = rows whose abs_week < 938  (938 ~ 2020w01 approx).
"""
import os, datetime
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DATA = os.path.join(PROJECT_ROOT, "data")

# abs_week 0 = 2002w01. 2020w01 = 2002w01 + (2020-2002)*52 + offset.
# Compute exact: 2002-01-01 is a Monday (ISO week 1). 2020-01-01 is also ISO week 1.
# weeks from 2002w01 to 2020w01 = (2020-2002)*52 + (iso_week_2020w01 - iso_week_2002w01)
# 2002w01=1, 2020w01=1 -> 18*52 = 936. So abs_week 936 ~ 2020w01.
PRECOVID_MAX_WEEK = 935  # strictly before 2020w01

def wk_to_year(w):
    d = datetime.date(2002, 1, 1) + datetime.timedelta(weeks=int(w))
    return d.year

def mse_mae(gt, pr):
    gt = np.asarray(gt, float); pr = np.asarray(pr, float)
    return float(np.mean((gt-pr)**2)), float(np.mean(np.abs(gt-pr)))

print(f"{'L':>3} | {'FULL MSE':>10} {'FULL MAE':>9} | {'PRE-COVID MSE':>13} {'PRE-COVID MAE':>14} | {'ratio MSE':>9}")
print("-"*70)
for L in (24, 36, 48, 60):
    fp = os.path.join(DATA, f"predictions_miflu_L{L}_paper_protocol.csv")
    df = pd.read_csv(fp)
    t = df[df.split == "test"].copy()
    full_mse, full_mae = mse_mae(t.ground_truth_ili, t.prediction_ili)
    pre = t[t.abs_week <= PRECOVID_MAX_WEEK]
    if len(pre) == 0:
        print(f"{L:>3} | no pre-covid rows")
        continue
    pmse, pmae = mse_mae(pre.ground_truth_ili, pre.prediction_ili)
    ratio = full_mse / pmse if pmse > 0 else float('nan')
    print(f"{L:>3} | {full_mse:10.4f} {full_mae:9.4f} | {pmse:13.4f} {pmae:14.4f} | {ratio:9.2f}x")
    print(f"     pre-covid rows={len(pre)} (abs_week<={PRECOVID_MAX_WEEK}, years {wk_to_year(pre.abs_week.min())}-{wk_to_year(pre.abs_week.max())}); full rows={len(t)}")
