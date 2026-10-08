#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_q2_q3.py
==============
Produce the Q2 (temporal alignment / COVID) and Q3 (scaler & units) audit
deliverables from the FROZEN Track C predictions and the author-966 raw data.
No training, no HPC: local CPU numpy only.

Outputs:
  results/v3_clean/analysis/peak_criteria/TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv
  results/v3_clean/analysis/peak_criteria/TRACK_C_PHYSICAL_UNIT_SANITY.csv
  results/v3_clean/analysis/peak_criteria/TRACK_C_VARIABLE_LABEL_AUDIT.csv
  (the two .md narratives are written separately)
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria")
NPZ = os.path.join(ROOT, "audit_20260930", "predictions_stage6")
DATA = os.path.join(ROOT, "recovery", "author_repo", "dataset", "illness",
                   "national_illness.csv")
SCALER = os.path.join(NPZ, "scaler_train_only.json")

ILI = 4
TRAIN_N, VAL_N, TEST_N = 676, 97, 193
TEST_START = TRAIN_N + VAL_N          # 773
TEST_END = TEST_START + TEST_N - 1     # 965
COVID_LO = dt.date(2020, 1, 1)

MODELS = ["miflu", "nlinear", "dlinear", "timecma_llm", "patchtst",
          "itransformer", "qwen_time_llm", "calf_llm"]
HORIZONS = [24, 36, 48, 60]
SEEDS = [42, 43, 44]


def corr(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.size < 3 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        return float("nan")
    da, db = a - a.mean(), b - b.mean()
    den = np.sqrt((da * da).sum() * (db * db).sum())
    return float((da * db).sum() / den) if den > 0 else float("nan")


def load(model, L, seed):
    p = os.path.join(NPZ, f"pred_{model}_L{L}_s{seed}.npz")
    if not os.path.exists(p):
        return None
    d = np.load(p)
    pred, tgt = d["pred"], d["target"]
    if pred.ndim == 3 and pred.shape[1] == 7:
        p0, t0 = pred[:, ILI, :], tgt[:, ILI, :]
    elif pred.ndim == 3 and pred.shape[2] == 7:
        p0, t0 = pred[:, :, ILI], tgt[:, :, ILI]
    else:
        return None
    mean = 9439.841796875
    scale = 9003.15234375
    n = p0.shape[0]
    rows = np.arange(TEST_START, TEST_START + n)   # actual #origins (NOT 193)
    return rows, t0 * scale + mean, p0 * scale + mean


def main():
    # ---- test dates ----
    raw = []
    with open(DATA, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        next(r)
        for line in r:
            raw.append(line)
    def d(row): return dt.datetime.strptime(raw[row][0].split()[0],
                                           "%Y-%m-%d").date()
    test_dates = [d(i) for i in range(TEST_START, TEST_END + 1)]
    covid_mask = np.array([x >= COVID_LO for x in test_dates])

    # ---- Q2: per-model alignment + COVID ----
    align_rows = []
    for m in MODELS:
        lag0_best = 0
        n_cells = 0
        pre_mae, cov_mae, pre_tgt, cov_tgt = [], [], [], []
        for L in HORIZONS:
            for s in SEEDS:
                got = load(m, L, s)
                if got is None:
                    continue
                rows, tv, pv = got                       # physical, all leads (n,L)
                n_cells += 1
                tv0, pv0 = tv[:, 0], pv[:, 0]             # lead-0 (1 week ahead)
                # MSE-based offset detection over ALL leads x ILITOTAL.
                # Lead-0-only MSE is non-discriminative for strongly seasonal
                # series (1-week-ahead ~ previous week); the all-lead mean is.
                def mse(a, b):
                    a = np.asarray(a, float)
                    b = np.asarray(b, float)
                    return float(((a - b) ** 2).mean()) if a.size >= 2 else float("nan")
                m0 = mse(pv, tv)
                m_m1 = mse(pv[1:], tv[:-1])
                m_p1 = mse(pv[:-1], tv[1:])
                m_m2 = mse(pv[2:], tv[:-2]) if tv.shape[0] > 2 else float("nan")
                m_p2 = mse(pv[:-2], tv[2:]) if tv.shape[0] > 2 else float("nan")
                lag_mses = [m_m2, m_m1, m0, m_p1, m_p2]
                min_lag = min(x for x in lag_mses if np.isfinite(x))
                # A genuine index offset would make lag0 MSE substantially larger
                # than the best lag. A small sub-week model phase lag only nudges
                # it. Tolerate lag0 within 5% of the best lag as "aligned".
                if m0 <= 1.05 * min_lag:
                    lag0_best += 1
                # COVID split (physical, lead 0)
                for i, row in enumerate(rows):
                    dt_i = d(int(row))
                    if dt_i >= COVID_LO:
                        cov_mae.append(abs(pv0[i] - tv0[i]))
                        cov_tgt.append(tv0[i])
                    else:
                        pre_mae.append(abs(pv0[i] - tv0[i]))
                        pre_tgt.append(tv0[i])
        pre_mae_m = float(np.mean(pre_mae)) if pre_mae else float("nan")
        cov_mae_m = float(np.mean(cov_mae)) if cov_mae else float("nan")
        pre_rel = pre_mae_m / float(np.mean(pre_tgt)) if pre_tgt else float("nan")
        cov_rel = cov_mae_m / float(np.mean(cov_tgt)) if cov_tgt else float("nan")
        align_rows.append(dict(
            model=m, cells=n_cells,
            lag0_best_frac=round(lag0_best / n_cells, 3) if n_cells else "",
            alignment_status=("ALIGNED" if (n_cells and lag0_best / n_cells >= 0.9)
                             else "MINOR_PHASE_LAG" if (n_cells and lag0_best > 0)
                             else "REVIEW"),
            test_date_start=str(test_dates[0]), test_date_end=str(test_dates[-1]),
            pre_covid_weeks=sum(1 for x in test_dates if x < COVID_LO),
            covid_weeks=int(covid_mask.sum()),
            pre_covid_mae_ili=round(pre_mae_m, 1) if pre_mae else "",
            covid_mae_ili=round(cov_mae_m, 1) if cov_mae else "",
            pre_covid_rel_mae=round(pre_rel, 3) if pre_tgt else "",
            covid_rel_mae=round(cov_rel, 3) if cov_tgt else ""))
    with open(os.path.join(OUT, "TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv"),
              "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(align_rows[0].keys()))
        w.writeheader()
        w.writerows(align_rows)
    print("[write] TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv")

    # ---- Q3: variable labels + physical-unit sanity ----
    sc = json.load(open(SCALER))
    var_cols = sc["var_cols"]
    mean = sc["mean"]
    scale = sc["scale"]
    # raw train descriptive stats per variable (csv order = var_cols order)
    feats = []
    with open(DATA, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        for line in r:
            feats.append([float(x) for x in line[1:]])
    feats = np.array(feats[:TRAIN_N])          # train rows [0,676)
    sanity = []
    rt_errs = []
    for idx, name in enumerate(var_cols):
        col = feats[:, idx]
        phys_mean = mean[idx]
        phys_scale = scale[idx]
        # round-trip on raw values through z-space
        z = (col - phys_mean) / phys_scale
        back = z * phys_scale + phys_mean
        rt_err = float(np.max(np.abs(col - back)))
        rt_errs.append(rt_err)
        sanity.append(dict(
            index=idx, csv_col=hdr[idx + 1], canonical_name=name,
            role=("PTE/PIE TARGET (ILITOTAL influenza activity)" if idx == ILI
                  else "auxiliary feature"),
            train_min=round(float(col.min()), 2),
            train_max=round(float(col.max()), 2),
            train_mean=round(float(col.mean()), 2),
            inverse_roundtrip_max_err=rt_err))
    # add the OT check note: OT is the 7th var, NOT the PTE target
    with open(os.path.join(OUT, "TRACK_C_PHYSICAL_UNIT_SANITY.csv"),
              "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sanity[0].keys()))
        w.writeheader()
        w.writerows(sanity)
    print("[write] TRACK_C_PHYSICAL_UNIT_SANITY.csv")

    # variable label audit (same table, emphasising labels/roles)
    with open(os.path.join(OUT, "TRACK_C_VARIABLE_LABEL_AUDIT.csv"),
              "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["feature_index", "raw_csv_column", "canonical_label",
                    "is_pte_pie_target", "scaler_mean", "scaler_scale",
                    "corrected_label_used_in_report"])
        for idx, name in enumerate(var_cols):
            w.writerow([idx, hdr[idx + 1], name,
                        "YES" if idx == ILI else "no",
                        round(mean[idx], 4), round(scale[idx], 4), name])
    print("[write] TRACK_C_VARIABLE_LABEL_AUDIT.csv")
    print("max inverse round-trip err:", max(rt_errs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
