#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_pte_pie_track_c.py
==========================
Peak Timing Error (PTE) and Peak Intensity Error (PIE) for the Track C
strict-966 eight-model Test championship.

Thresholds: LITERATURE convention (project decision 2026-10-08)
    PTE <= 1.0 week   AND   PIE <= 25.0 %   ->  the peak is a HIT
    Kramer SC, Shaman J. PLOS Comput Biol 2019. DOI 10.1371/journal.pcbi.1006742
    (same convention as the CDC "Predict the Influenza Season Challenge").

Judgement is PER PEAK, not on a mean across peaks. Averaging would let a
2-week-off peak be cancelled out by a 0-week-off peak, which is not what the
cited convention specifies.

Data sources
------------
* MIFlu (official repo, retrained 12 cells)
    results/v3_clean/analysis/peak_criteria/miflu/*/test_predictions_*.csv
    columns include: forecast_lead (1-based; 1 = one week ahead = step 0),
    feature_index, y_true_z, y_pred_z, target_start_row
* the other seven models (84 rescored cells, reused stage6 artefacts)
    audit_20260930/predictions_stage6/pred_<model>_L<L>_s<seed>.npz
    arrays: pred / target, shape (n_origins, 7, L), z-space

Scaling
-------
z -> physical for ILITOTAL (feature index 4):
    physical = z * 9003.15234375 + 9439.841796875
from scaler_train_only.json (fitted on train rows [0, 676) ONLY).
PIE is a relative error, so it MUST be computed in physical units; doing it in
z-space would divide by (value - mean) instead of value.

Usage: python scripts/compute_pte_pie_track_c.py
"""
from __future__ import annotations

import csv
import glob
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria")
MIFLU = os.path.join(OUT, "miflu")
NPZ = os.path.join(ROOT, "audit_20260930", "predictions_stage6")

ILI = 4                       # ILITOTAL feature index
MEAN_ILI = 9439.841796875     # scaler_train_only.json, train rows [0,676)
SCALE_ILI = 9003.15234375

TEST_START_ROW = 773          # strict-966 Test block starts at row 773
MIN_SEP_WEEKS = int(os.environ.get("MIN_SEP_WEEKS", "40"))
# Influenza seasons are annual, so true seasonal peaks must be far apart.
# 30 weeks was tried first and produced 16-week spacings near the series
# median, i.e. it counted off-season bumps as peaks. 40 weeks is a
# conservative lower bound on an annual cycle.
MATCH_TOL_WEEKS = 2           # existing project convention
THR_PTE_WEEKS = 1.0           # LITERATURE (Kramer & Shaman 2019)
THR_PIE_PCT = 25.0            # LITERATURE (Kramer & Shaman 2019)

MODELS = ["miflu", "nlinear", "dlinear", "timecma_llm", "patchtst",
          "itransformer", "qwen_time_llm", "calf_llm"]
HORIZONS = [24, 36, 48, 60]
SEEDS = [42, 43, 44]


def to_phys(z):
    return np.asarray(z, dtype=float) * SCALE_ILI + MEAN_ILI


AMP_MODE = os.environ.get("AMP_MODE", "mean")


def _floor(v):
    if AMP_MODE == "median":
        return float(np.median(v))
    if AMP_MODE == "mean_plus_half_sd":
        return float(np.mean(v) + 0.5 * np.std(v))
    return float(np.mean(v))


def pick_peaks(values, min_sep=MIN_SEP_WEEKS, floor=None):
    """Greedy seasonal peak picking.

    Repeatedly take the largest remaining point, then mask +/- min_sep//2
    around it. A candidate must exceed the amplitude floor, which defaults to
    the series MEAN: an influenza peak is a genuine seasonal surge and must
    stand above the period average. Using the MEDIAN instead let off-season
    bumps (21k-25k against a median of 18k) be counted as seasonal peaks,
    which inflated the peak count to ~5.5 per cell instead of ~3.
    Returns a list of indices, ascending."""
    v = np.asarray(values, dtype=float)
    if v.size == 0:
        return []
    work = v.copy()
    thr = _floor(v) if floor is None else float(floor)
    half = min_sep // 2
    out = []
    while True:
        i = int(np.argmax(work))
        if work[i] < thr or not np.isfinite(work[i]):
            break
        out.append(i)
        lo, hi = max(0, i - half), min(v.size, i + half + 1)
        work[lo:hi] = -np.inf
        if np.isfinite(work).sum() == 0:
            break
    return sorted(out)


def load_miflu(L, seed):
    pat = os.path.join(MIFLU, f"*L{L}*", f"test_predictions_*{L}__seed{seed}.csv")
    hits = glob.glob(pat)
    if not hits:
        pat2 = os.path.join(MIFLU, "**", f"test_predictions_*{L}*seed{seed}.csv")
        hits = glob.glob(pat2, recursive=True)
    if not hits:
        return None
    rows = {}
    with open(hits[0], newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if int(r["feature_index"]) != ILI:
                continue
            if int(r["forecast_lead"]) != 1:      # 1 = one week ahead = step 0
                continue
            rows[int(r["target_start_row"])] = (float(r["y_true_z"]),
                                                float(r["y_pred_z"]))
    order = sorted(rows)
    return (np.array(order),
            to_phys([rows[k][0] for k in order]),
            to_phys([rows[k][1] for k in order]))


def load_npz(model, L, seed):
    p = os.path.join(NPZ, f"pred_{model}_L{L}_s{seed}.npz")
    if not os.path.exists(p):
        return None
    d = np.load(p)
    pred = d["pred"]
    tgt = d["target"]
    # tolerate both (n, 7, L) and (n, L, 7)
    if pred.ndim == 3 and pred.shape[1] == 7:
        p0, t0 = pred[:, ILI, 0], tgt[:, ILI, 0]
    elif pred.ndim == 3 and pred.shape[2] == 7:
        p0, t0 = pred[:, 0, ILI], tgt[:, 0, ILI]
    else:
        return None
    n = p0.size
    rows = np.arange(TEST_START_ROW, TEST_START_ROW + n)
    return rows, to_phys(t0), to_phys(p0)


def evaluate(model, L, seed):
    if model == "miflu":
        got = load_miflu(L, seed)
    else:
        got = load_npz(model, L, seed)
    if got is None:
        return None, []
    rows, tv, pv = got

    tpeaks = pick_peaks(tv)
    ppeaks = pick_peaks(pv)

    per_peak = []
    used_pred = set()
    for ti in tpeaks:
        r_t, v_t = int(rows[ti]), float(tv[ti])
        best = None
        for pi in ppeaks:
            if pi in used_pred:
                continue
            r_p = int(rows[pi])
            if abs(r_p - r_t) <= MATCH_TOL_WEEKS:
                if best is None or abs(r_p - r_t) < abs(best[0] - r_t):
                    best = (r_p, pi)
        if best is None:
            per_peak.append(dict(model=model, L=L, seed=seed,
                                 true_row=r_t, pred_row="", PTE_wk="",
                                 true_val=round(v_t, 1), pred_val="",
                                 PIE_pct="", status="Missed"))
            continue
        r_p, pi = best
        used_pred.add(pi)
        v_p = float(pv[pi])
        pte = abs(r_p - r_t)
        pie = abs(v_p - v_t) / v_t * 100.0 if v_t else float("nan")
        hit = (pte <= THR_PTE_WEEKS) and (pie <= THR_PIE_PCT)
        per_peak.append(dict(model=model, L=L, seed=seed,
                             true_row=r_t, pred_row=r_p, PTE_wk=pte,
                             true_val=round(v_t, 1), pred_val=round(v_p, 1),
                             PIE_pct=round(pie, 2),
                             status="Hit" if hit else "MatchedNotHit"))
    for pi in ppeaks:
        if pi in used_pred:
            continue
        per_peak.append(dict(model=model, L=L, seed=seed,
                             true_row="", pred_row=int(rows[pi]), PTE_wk="",
                             true_val="", pred_val=round(float(pv[pi]), 1),
                             PIE_pct="", status="FalsePeak"))

    matched = [p for p in per_peak if p["status"] in ("Hit", "MatchedNotHit")]
    n_true = len(tpeaks)
    n_match = len(matched)
    n_hit = sum(1 for p in per_peak if p["status"] == "Hit")
    ptes = [float(p["PTE_wk"]) for p in matched]
    pies = [float(p["PIE_pct"]) for p in matched]
    summary = dict(
        model=model, L=L, seed=seed,
        n_true_peaks=n_true, n_matched=n_match, n_hit=n_hit,
        hit_rate_pct=round(n_hit / n_true * 100, 1) if n_true else "",
        mean_PTE_wk=round(float(np.mean(ptes)), 2) if ptes else "",
        mean_PIE_pct=round(float(np.mean(pies)), 2) if pies else "",
        series_weeks=int(rows.size),
        row_start=int(rows[0]), row_end=int(rows[-1]))
    return summary, per_peak


def main():
    os.makedirs(OUT, exist_ok=True)
    all_sum, all_peak = [], []
    for m in MODELS:
        for L in HORIZONS:
            for s in SEEDS:
                sm, pk = evaluate(m, L, seed=s)
                if sm is None:
                    print(f"[skip] {m} L={L} seed={s}")
                    continue
                all_sum.append(sm)
                all_peak.extend(pk)
                print(f"[ok] {m:14s} L={L:2d} s={s}  peaks={sm['n_true_peaks']}"
                      f"  hit={sm['n_hit']}/{sm['n_true_peaks']}"
                      f"  PTE={sm['mean_PTE_wk']}  PIE={sm['mean_PIE_pct']}")

    def dump(name, rows, fields):
        p = os.path.join(OUT, name)
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[write] {p}")

    dump("PTE_PIE_per_peak.csv", all_peak,
         ["model", "L", "seed", "true_row", "pred_row", "PTE_wk",
          "true_val", "pred_val", "PIE_pct", "status"])
    dump("PTE_PIE_per_cell.csv", all_sum,
         ["model", "L", "seed", "series_weeks", "row_start", "row_end",
          "n_true_peaks", "n_matched", "n_hit", "hit_rate_pct",
          "mean_PTE_wk", "mean_PIE_pct"])

    # per model, pooled over horizons x seeds
    pooled = []
    for m in MODELS:
        rs = [r for r in all_sum if r["model"] == m]
        if not rs:
            continue
        nt = sum(r["n_true_peaks"] for r in rs)
        nh = sum(r["n_hit"] for r in rs)
        ptes = [float(r["mean_PTE_wk"]) for r in rs if r["mean_PTE_wk"] != ""]
        pies = [float(r["mean_PIE_pct"]) for r in rs if r["mean_PIE_pct"] != ""]
        pooled.append(dict(
            model=m, cells=len(rs), n_true_peaks=nt, n_hit=nh,
            hit_rate_pct=round(nh / nt * 100, 1) if nt else "",
            mean_of_cell_PTE_wk=round(float(np.mean(ptes)), 2) if ptes else "",
            mean_of_cell_PIE_pct=round(float(np.mean(pies)), 2) if pies else ""))
    pooled.sort(key=lambda r: -(r["hit_rate_pct"] if r["hit_rate_pct"] != "" else -1))
    dump("PTE_PIE_by_model.csv", pooled,
         ["model", "cells", "n_true_peaks", "n_hit", "hit_rate_pct",
          "mean_of_cell_PTE_wk", "mean_of_cell_PIE_pct"])

    meta = dict(thresholds=dict(PTE_weeks=THR_PTE_WEEKS, PIE_pct=THR_PIE_PCT,
                                source="Kramer & Shaman 2019 PLOS Comput Biol "
                                       "DOI 10.1371/journal.pcbi.1006742"),
                judgement="per peak (NOT averaged across peaks)",
                match_tol_weeks=MATCH_TOL_WEEKS,
                min_sep_weeks=MIN_SEP_WEEKS,
                units="physical patient counts (ILITOTAL), train-only scaler",
                scaler=dict(mean=MEAN_ILI, scale=SCALE_ILI,
                            fit_on="train rows [0,676)"))
    with open(os.path.join(OUT, "PTE_PIE_METHOD.json"), "w",
              encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(f"[write] {os.path.join(OUT, 'PTE_PIE_METHOD.json')}")


if __name__ == "__main__":
    main()
