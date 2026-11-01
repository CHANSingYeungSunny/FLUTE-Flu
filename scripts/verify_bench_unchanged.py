#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_bench_unchanged.py — prove no number moved *except* on purpose.

Two frozen references exist in `paper_tables/`:

  * `*.post_evalwindow16.csv` — the CURRENT contract. Every (model, L[, step]) row
    must reappear with **bit-identical** metric values (exact float equality, not
    np.allclose). This is the reference a future merge (e.g. the MIFlu benchmark
    row) is checked against.
  * `*.pre_evalwindow16.csv` / `*.pre_miflu.csv` — history, kept for rollback
    (`AGENTS.md` `R3`). Rows must still all be present, but the metric values are
    *expected* to differ, because the shared evaluation-window rule
    (`(W // 16) * 16`, see `scripts/eval_windows.py`) re-derived every number on
    160/144/144/128 windows instead of 170/158/146/134.

Checks, always:
  1. every (model, L) row of the chosen baseline still exists;
  2. metrics are bit-identical to a `post_*` baseline, or their deltas are
     *reported and explained* against a `pre_*` baseline;
  3. for a `pre_*` baseline the new numbers are independently re-derived from the
     raw npz under the window rule and must match the written table;
  4. `dlinear` / `linear_ref` must not appear in any written table;
  5. `n_channels_used` must be 7 for every full 7-channel model and the 7-variable
     metrics must be NaN for any row whose `n_channels_used < 7`;
  6. `n_eval_windows` must be uniform across arms at each horizon and equal
     `eval_slice(n_windows_available)`.

Exit code 0 = all checks pass. Exit 1 = a check failed (details printed).

Usage:  python scripts/verify_bench_unchanged.py
        python scripts/verify_bench_unchanged.py --baseline pre_evalwindow16
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from eval_windows import eval_slice, assert_uniform  # noqa: E402

PT = os.path.join(ROOT, "paper_tables")
EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")

KEYS_ML = ["model", "L"]
METRICS_ML = ["mse_7var_z", "mae_7var_z", "mse_ilitotal_z", "mae_ilitotal_z",
              "mse_ilitotal_phys", "mae_ilitotal_phys"]
METRICS_STEP = ["mse_7var_z", "mae_7var_z"]
TABLES = ("BENCH_MSE_BY_MODEL_L", "BENCH_MSE_BY_STEP", "BENCH_PTE_PIE_BY_STEP",
          "BENCH_MSE_BY_FAMILY", "BENCH_MSE_BY_SIDE")
TAGS = ("post_evalwindow16", "pre_evalwindow16", "pre_miflu")

FAIL = []
DELTAS = {}


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def ok(msg):
    print(f"[ok]   {msg}")


def pick_baseline(table: str, requested: str):
    """Return (tag, path) of the reference to compare against."""
    order = list(TAGS) if requested == "auto" else [requested]
    for tag in order:
        p = os.path.join(PT, f"{table}.{tag}.csv")
        if os.path.exists(p):
            return tag, p
    return None, None


def compare(table, keys, metrics, requested):
    new_p = os.path.join(PT, f"{table}.csv")
    tag, old_p = pick_baseline(table, requested)
    if old_p is None or not os.path.exists(new_p):
        print(f"[skip] {table}: no baseline ({requested}) or new table missing")
        return
    new = pd.read_csv(new_p)
    old = pd.read_csv(old_p)
    # dlinear is excluded by design, so it is only expected in an old backup
    old = old[~old["model"].astype(str).str.lower().str.contains("dlinear")]
    m = old.merge(new, on=keys, how="left", suffixes=("_old", "_new"), indicator=True)
    missing = m[m["_merge"] != "both"]
    if len(missing):
        fail(f"{table}: {len(missing)} rows from {tag} are missing in the new table")
    exact_mode = tag.startswith("post_")
    n_cmp = 0
    for met in metrics:
        if f"{met}_old" not in m.columns:
            continue
        o, n = m[f"{met}_old"], m[f"{met}_new"]
        both = o.notna() & n.notna()
        if (~both).any():
            bad = ~(o.isna() & n.isna())
            if bad.any():
                fail(f"{table}.{met}: {int(bad.sum())} NaN mismatches")
            both = both & False
        ov, nv = o[both].to_numpy(), n[both].to_numpy()
        n_cmp += int(both.sum())
        if exact_mode:
            eq = (ov == nv)
            if not eq.all():
                d = float(np.max(np.abs(ov[~eq] - nv[~eq])))
                fail(f"{table}.{met}: {int((~eq).sum())} of {int(both.sum())} values "
                     f"differ from {tag} (max |diff| = {d:.3e})")
        else:
            d = float(np.max(np.abs(ov - nv))) if ov.size else 0.0
            DELTAS[f"{table}.{met}"] = d
    if exact_mode:
        if not FAIL:
            ok(f"{table}: {len(old)} rows x {len(metrics)} metrics BIT-IDENTICAL to "
               f"{tag} ({n_cmp} comparisons, max |diff| = 0.0)")
    else:
        ok(f"{table}: all {len(old)} rows of {tag} still present; metric values were "
           f"re-derived on the shared evaluation windows (deltas reported below)")


def assert_no_dlinear(table):
    p = os.path.join(PT, f"{table}.csv")
    if not os.path.exists(p):
        return
    txt = open(p, encoding="utf-8").read().lower()
    if "dlinear" in txt or "linear_ref" in txt:
        fail(f"{table}: DLinear appears in the written table")
    else:
        ok(f"{table}: DLinear absent")


def check_channel_semantics():
    p = os.path.join(PT, "BENCH_MSE_BY_MODEL_L.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    if "n_channels_used" not in d.columns:
        fail("BENCH_MSE_BY_MODEL_L.csv has no n_channels_used column")
        return
    full = d[d["n_channels_used"] == 7]
    part = d[d["n_channels_used"] < 7]
    if full["mse_7var_z"].isna().any():
        fail(f"{int(full['mse_7var_z'].isna().sum())} full 7-channel rows have a NaN 7-var MSE")
    else:
        ok(f"n_channels_used: {len(full)} full rows report a 7-var MSE")
    if len(part):
        bad = part["mse_7var_z"].notna() | part["mae_7var_z"].notna()
        if bad.any():
            fail(f"{int(bad.sum())} partial rows were given a 7-variable number "
                 f"({part.loc[bad, ['model','L']].to_dict('records')})")
        else:
            ok(f"n_channels_used: {len(part)} partial rows correctly report NaN 7-var "
               f"metrics (models: {sorted(part['model'].unique())})")
        if part["mse_ilitotal_z"].isna().any():
            fail("a partial row has no ILITOTAL MSE")


def check_eval_windows():
    """The ruled invariant: one window count per horizon, for every arm."""
    for table in ("BENCH_MSE_BY_MODEL_L", "BENCH_MSE_BY_STEP", "BENCH_PTE_PIE_BY_STEP",
                  "BENCH_CRPS_WIS", "BENCH_SEASONAL_NAIVE"):
        p = os.path.join(PT, f"{table}.csv")
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        if "n_eval_windows" not in d.columns:
            fail(f"{table}: no n_eval_windows column — window rule not applied")
            continue
        try:
            assert_uniform(d, by=("L",), col="n_eval_windows", what="arms")
        except AssertionError as e:
            fail(f"{table}: {e}")
            continue
        got = {int(L): int(sorted(set(g))[0])
               for L, g in d.groupby("L")["n_eval_windows"]}
        # the count must be the author's own (W//16)*16, i.e. a multiple of 16 that
        # equals eval_slice(n_windows_available) when that column is present
        bad = [L for L, n in got.items() if n <= 0 or n % 16 != 0]
        if "n_windows_available" in d.columns:
            for L, g in d.groupby("L"):
                avail = int(sorted(set(int(v) for v in g["n_windows_available"]))[0])
                if got[int(L)] != eval_slice(avail):
                    bad.append(int(L))
        if bad:
            fail(f"{table}: n_eval_windows != eval_slice(W) at L={sorted(set(bad))} "
                 f"(got {got})")
        else:
            ok(f"{table}: n_eval_windows uniform across arms and == eval_slice(W) "
               f"at every horizon {got}")


def redrive_from_npz():
    """Independently recompute the 7-var MSE from the npz under the window rule.

    The table's `mse_7var_z` is `np.mean` over the whole `(S, W, 7, L)` cube; this
    check averages per seed and then over seeds. The two are algebraically
    identical but differ in float summation order at the ~1e-9 level, hence the
    RTOL below (four orders of magnitude tighter than the 4-dp reporting).
    """
    RTOL = 1e-7
    p = os.path.join(PT, "BENCH_MSE_BY_MODEL_L.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p).set_index(["model", "L"])
    acc = {}
    for f in sorted(glob.glob(os.path.join(EXP, "*_L*_s*", "pred_*.npz"))):
        m = re.search(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(f))
        if not m or m.group(1) == "dlinear":
            continue
        model, L = m.group(1), int(m.group(2))
        z = np.load(f)
        pred, tgt = np.asarray(z["pred"], float), np.asarray(z["target"], float)
        n = eval_slice(pred.shape[0])
        if not np.isfinite(pred[:n]).all():
            continue          # partial export: no 7-var number by design
        acc.setdefault((model, L), []).append(float(np.mean((pred[:n] - tgt[:n]) ** 2)))
    worst, n_ok = 0.0, 0
    for k, v in acc.items():
        if k not in d.index:
            continue
        if not np.isfinite(float(d.loc[k, "mse_7var_z"])):
            continue
        diff = abs(float(np.mean(v)) - float(d.loc[k, "mse_7var_z"]))
        worst = max(worst, diff)
        n_ok += 1
        if diff > RTOL:
            fail(f"redrive {k}: npz gives {float(np.mean(v)):.9f} but the table says "
                 f"{float(d.loc[k, 'mse_7var_z']):.9f}")
    if worst <= RTOL:
        ok(f"redrive: {n_ok} (model, L) 7-var MSEs recomputed from the npz on "
           f"eval_slice(W) windows match the table (max |diff| = {worst:.1e} "
           f"<= {RTOL:g})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", default="auto", choices=("auto",) + TAGS,
                    help="frozen reference to compare against (default: auto = "
                         "post_evalwindow16 if present, else the older freezes)")
    args = ap.parse_args()

    compare("BENCH_MSE_BY_MODEL_L", KEYS_ML, METRICS_ML, args.baseline)
    compare("BENCH_MSE_BY_STEP", ["model", "L", "step"], METRICS_STEP, args.baseline)
    compare("BENCH_PTE_PIE_BY_STEP", ["model", "L", "step"], ["PTE_wk", "PIE_pct"],
            args.baseline)
    for t in TABLES:
        assert_no_dlinear(t)
    check_channel_semantics()
    check_eval_windows()
    redrive_from_npz()

    if DELTAS:
        print("\nreported deltas vs the pre-window baseline (expected: non-zero, the "
              "window rule re-derived every number):")
        for k, v in sorted(DELTAS.items()):
            print(f"   {k:<45s} max |diff| = {v:.4e}")

    print("\n" + "=" * 72)
    if FAIL:
        print(f"RESULT: {len(FAIL)} CHECK(S) FAILED")
        return 1
    print("RESULT: PASS — no unexplained change, DLinear absent, window rule uniform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
