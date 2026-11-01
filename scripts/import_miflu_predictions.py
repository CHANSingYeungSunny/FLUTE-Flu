#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_miflu_predictions.py -- convert MIFlu prediction exports into the
benchmark npz cell format used by `hpc_results/expanded_runs/`.

WHY THIS EXISTS
---------------
The benchmark tables are built from `hpc_results/expanded_runs/<model>_L<L>_s<seed>/
pred_<model>_L<L>_s<seed>.npz`, each holding a `(W, 7, L)` cube. MIFlu's predictions
were exported by the reproduction runner as CSVs, so they are not in that directory
and MIFlu is missing from `paper_tables/BENCH_*.csv` -- which is absurd for a paper
whose subject is MIFlu.

WHAT IT GUARANTEES (no silent protocol mixing)
----------------------------------------------
Before a single file is written, every export is checked against an *existing*
benchmark cell of the same horizon:

  1. the set of test windows must match `target_start_row` exactly;
  2. the exported ground truth must equal the benchmark `target[:, 4, :]`
     (ILITOTAL, z-space) to <= GT_TOL;
  3. the (L, n_windows) shape must match.

If any check fails, the script prints the mismatch and exits non-zero without
writing anything. This is the guard that stops a prediction file produced under a
different split / scaler / window rule from being merged into the champion tables.

THREE INPUT FORMATS (auto-detected)
----------------------------------
  csv-partial   `split,abs_week,step,...,ground_truth_ili,prediction_ili,...`
                (the reproduction runner's export: ILITOTAL only, 193 test weeks
                e.g. `author_runs/L24_s2021/predictions_miflu_L24_paper_protocol.csv`).
                Only channel 4 (ILITOTAL) is filled; all other channels are NaN and
                the npz is stamped `partial=True` so the analysis can never report a
                7-variable number for it.
  csv-full      `dataset_hash,seed,horizon,split,forecast_origin,target_start_row,
                target_end_row,forecast_lead,feature_index,...,y_true_z,y_pred_z`
                (all 7 variables, strict966 export). Written as a complete cell.
  npz           an already-benchmark-format `(W, 7, L)` npz (validated, not trusted).

USAGE
-----
  # verify only, write nothing (safe; run this first)
  python scripts/import_miflu_predictions.py --check

  # convert the HPC/reproduction CSVs (seed 2021, the reproduction seed)
  python scripts/import_miflu_predictions.py --csv-pattern "author_runs/L{L}_s2021/predictions_miflu_L{L}_paper_protocol.csv"

  # convert a 7-variable strict966 export directory
  python scripts/import_miflu_predictions.py --csv-pattern "results/v3_clean/analysis/peak_criteria/miflu/miflu_strict966__L{L}__seed{S}/test_predictions_miflu_strict966__L{L}__seed{S}.csv" --seeds 42 43 44 --seed-source dir

  # pass through an existing npz set
  python scripts/import_miflu_predictions.py --npz-dir hpc_results/stage5_a2/scoring/predictions

See AGENTS.md 13.E for the current status of the merge.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
SCALER = os.path.join(ROOT, "data", "scaler_miflu_author966.json")
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
# Column-name slugs used by the all-7-variable wide export
# (hpc_experiments/export_miflu_all7.py). Index 4 (ILITOTAL) is `ili`.
SLUGS = ["wili", "unwili", "age_0_4", "age_5_24", "ili", "num_providers", "ot"]
ILI = 4
GT_TOL = 1e-4          # max |GT_export - GT_benchmark| tolerated (z-space)
MIFLU_TRAINABLE_PARAMS = 1673496   # AGENTS.md 3, author-faithful count
PARTIAL_NOTE = "ILITOTAL only; 7-var aggregate unavailable from this export"

METRICS_COLS = ["backbone", "L", "seed", "fidelity_label", "mse_all", "mae_all",
                "mse_ili", "mae_ili", "best_val", "best_epoch", "n_train", "n_val",
                "n_test", "total_parameters", "trainable_parameters", "ckpt",
                "ckpt_sidecar"]


# --------------------------------------------------------------------------- #
# reference cell: the benchmark cube we must agree with
# --------------------------------------------------------------------------- #
def reference_cell(L):
    """Return (target, target_start_row) of an existing benchmark cell at horizon L."""
    for pat in (f"patchtst_L{L}_s42/pred_patchtst_L{L}_s42.npz",
                f"nlinear_L{L}_s42/pred_nlinear_L{L}_s42.npz"):
        p = os.path.join(EXP, pat)
        if os.path.exists(p):
            d = np.load(p, allow_pickle=True)
            return np.asarray(d["target"], float), np.asarray(d["target_start_row"], int), p
    hits = sorted(glob.glob(os.path.join(EXP, f"*_L{L}_s42", "pred_*.npz")))
    if not hits:
        raise SystemExit(f"no benchmark reference cell found for L={L} in {EXP}")
    d = np.load(hits[0], allow_pickle=True)
    return np.asarray(d["target"], float), np.asarray(d["target_start_row"], int), hits[0]


# --------------------------------------------------------------------------- #
# readers -> (pred, target) cubes of shape (W, 7, L)
# --------------------------------------------------------------------------- #
def _cube_from_csv(csv_path, L, ref_target, ref_windows):
    df = pd.read_csv(csv_path)
    cols = set(df.columns)

    # ---- format B: full 7-variable long export ---------------------------- #
    if {"target_start_row", "feature_index", "forecast_lead", "y_true_z", "y_pred_z"} <= cols:
        t = df[df["split"] == "test"] if "split" in cols else df
        if "horizon" in cols:
            t = t[t["horizon"] == L]
        W = len(ref_windows)
        cube = np.full((W, 7, L, 2), np.nan)
        pos = {int(w): i for i, w in enumerate(ref_windows)}
        ws = t["target_start_row"].to_numpy(int)
        ss = t["forecast_lead"].to_numpy(int) - 1
        fs = t["feature_index"].to_numpy(int)
        gv = t["y_true_z"].to_numpy(float)
        pv = t["y_pred_z"].to_numpy(float)
        for k in range(len(ws)):
            w, s, f = int(ws[k]), int(ss[k]), int(fs[k])
            if w not in pos or not (0 <= s < L) or not (0 <= f < 7):
                continue
            cube[pos[w], f, s, 0] = gv[k]
            cube[pos[w], f, s, 1] = pv[k]
        if np.isnan(cube).any():
            raise SystemExit(f"[FAIL] {csv_path}: {int(np.isnan(cube).sum())} of "
                             f"{cube.size} cells missing for L={L}")
        return cube[:, :, :, 1], cube[:, :, :, 0], "csv-full"

    # ---- format C: all-7-variable WIDE export ----------------------------- #
    # `hpc_experiments/export_miflu_all7.py` writes one row per (window, lead)
    # carrying all seven variables in z-space. Must be tested BEFORE format A,
    # which would otherwise match the same file and silently keep only ch4.
    if all(f"ground_truth_{s}" in cols and f"prediction_{s}" in cols for s in SLUGS):
        t = df[df["split"] == "test"].copy()
        if t.empty:
            raise SystemExit(f"[FAIL] {csv_path}: no rows with split == 'test'")
        # `abs_week` is the predicted week, so the producing window starts at
        # abs_week - step (same convention as train_miflu.export_prediction_csv).
        t["window"] = t["abs_week"].astype(int) - t["step"].astype(int)
        W = len(ref_windows)
        pos = {int(w): i for i, w in enumerate(ref_windows)}
        pred = np.full((W, 7, L), np.nan)
        targ = np.full((W, 7, L), np.nan)
        ws = t["window"].to_numpy(int)
        ss = t["step"].to_numpy(int)
        gts = [t[f"ground_truth_{s}"].to_numpy(float) for s in SLUGS]
        prs = [t[f"prediction_{s}"].to_numpy(float) for s in SLUGS]
        for k in range(len(ws)):
            w, s = int(ws[k]), int(ss[k])
            if w not in pos or not (0 <= s < L):
                continue
            i = pos[w]
            for f in range(7):
                targ[i, f, s] = gts[f][k]
                pred[i, f, s] = prs[f][k]
        for f, s_name in enumerate(SLUGS):
            if np.isnan(targ[:, f, :]).any():
                raise SystemExit(f"[FAIL] {csv_path}: variable '{s_name}' incomplete for L={L}")
        return pred, targ, "csv-wide7"

    # ---- format A: reproduction export, ILITOTAL only --------------------- #
    need = {"split", "abs_week", "step"}
    if not need <= cols:
        raise SystemExit(f"[FAIL] {csv_path}: unrecognised schema {sorted(cols)}")
    t = df[df["split"] == "test"].copy()
    if t.empty:
        raise SystemExit(f"[FAIL] {csv_path}: no rows with split == 'test'")
    # `abs_week` is the absolute week index of the *predicted* week, so the window
    # that produced the row starts at abs_week - step (train_miflu.export_prediction_csv).
    t["window"] = t["abs_week"].astype(int) - t["step"].astype(int)
    gt_col = "ground_truth_ili" if "ground_truth_ili" in cols else "y_true_z"
    pr_col = "prediction_ili" if "prediction_ili" in cols else "y_pred_z"
    if "ground_truth_ili_phys" in cols:
        # the reproduction export carries patients directly; prefer it and convert
        # back with the train-only scaler so both sides are in the same z-space
        sc = json.load(open(SCALER))
        mean, std = np.array(sc["mean"], float), np.array(sc["std"], float)
        t["gt_z_tmp"] = (t["ground_truth_ili_phys"].astype(float) - mean[ILI]) / std[ILI]
        t["pr_z_tmp"] = (t["prediction_ili_phys"].astype(float) - mean[ILI]) / std[ILI]
        gt_col, pr_col = "gt_z_tmp", "pr_z_tmp"

    W = len(ref_windows)
    pos = {int(w): i for i, w in enumerate(ref_windows)}
    pred = np.full((W, 7, L), np.nan)
    targ = np.full((W, 7, L), np.nan)
    ws = t["window"].to_numpy(int)
    ss = t["step"].to_numpy(int)
    gv = t[gt_col].to_numpy(float)
    pv = t[pr_col].to_numpy(float)
    for k in range(len(ws)):
        w, s = int(ws[k]), int(ss[k])
        if w not in pos or not (0 <= s < L):
            continue
        pred[pos[w], ILI, s] = pv[k]
        targ[pos[w], ILI, s] = gv[k]
    if np.isnan(targ[:, ILI, :]).any():
        raise SystemExit(f"[FAIL] {csv_path}: ILITOTAL channel incomplete for L={L}")
    return pred, targ, "csv-partial"


def _npz_path(npz_dir, L, seed):
    """Locate the npz for one (L, seed) in either supported layout.

    1. benchmark-style flat cell dir:  <npz_dir>/pred_miflu_L{L}_s{seed}.npz
    2. the exporter's own layout:      <npz_dir>/L{L}_all7/pred_miflu_L{L}_seed{seed}.npz
       (`hpc_experiments/export_miflu_all7.py` writes one directory per horizon,
       and names the file with `_seed`), so a single `--npz-dir author_runs`
       imports all 40 cells without copying them into a staging directory.
    """
    for p in (os.path.join(npz_dir, f"pred_miflu_L{L}_s{seed}.npz"),
              os.path.join(npz_dir, f"L{L}_all7", f"pred_miflu_L{L}_seed{seed}.npz")):
        if os.path.exists(p):
            return p
    return None


def _load_npz_set(npz_dir, L, seed):
    p = _npz_path(npz_dir, L, seed)
    if p is None:
        return None
    d = np.load(p, allow_pickle=True)
    return (np.asarray(d["pred"], float), np.asarray(d["target"], float),
            np.asarray(d["target_start_row"], int), d, p)


# --------------------------------------------------------------------------- #
# alignment check + write
# --------------------------------------------------------------------------- #
def check_alignment(pred, target, windows, ref_target, ref_windows, L, label=""):
    ok = True
    if not np.array_equal(np.asarray(windows, int), np.asarray(ref_windows, int)):
        print(f"  [FAIL] {label}: window set differs from the benchmark cell "
              f"({len(windows)} vs {len(ref_windows)} windows)")
        ok = False
    if pred.shape != ref_target.shape:
        print(f"  [FAIL] {label}: cube shape {pred.shape} != benchmark {ref_target.shape}")
        return False
    finite = np.isfinite(target[:, ILI, :])
    d = float(np.max(np.abs(target[:, ILI, :][finite] - ref_target[:, ILI, :][finite])))
    print(f"  {'[ok]  ' if d <= GT_TOL else '[FAIL]'} {label}: max |GT(ch4) - benchmark target| "
          f"= {d:.3e}  (tol {GT_TOL:g})")
    ok &= d <= GT_TOL
    return bool(ok)


def write_cell(pred, target, windows, L, seed, partial, out_root=EXP):
    d = os.path.join(out_root, f"miflu_L{L}_s{seed}")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"pred_miflu_L{L}_s{seed}.npz")
    payload = dict(
        pred=pred.astype(np.float32),
        target=target.astype(np.float32),
        target_start_row=np.asarray(windows, np.int32),
        L=np.int32(L),
        seed=np.int32(seed),
        var_cols=np.asarray(VAR_COLS),
        model=np.array("miflu"),
        profile=np.array("author_966"),
        containment=np.array("strict"),
        space=np.array("standardized_train_fit_z"),
    )
    if partial:
        payload["partial"] = np.array(True)
        payload["note"] = np.array(PARTIAL_NOTE)
    else:
        payload["partial"] = np.array(False)
    np.savez_compressed(out, **payload)
    return out


def write_metrics(L, seed, pred, target, out_root=EXP):
    """Companion metrics.csv, schema-identical to the other benchmark cells."""
    finite = np.isfinite(pred)
    err = (pred - target)[finite]
    mse_all = float(np.mean(err ** 2))
    mae_all = float(np.mean(np.abs(err)))
    e4 = (pred[:, ILI, :] - target[:, ILI, :])
    row = dict(backbone="miflu", L=L, seed=seed,
               fidelity_label="MIFlu reproduction export (author-faithful, 1,673,496 trainable)",
               mse_all=mse_all, mae_all=mae_all,
               mse_ili=float(np.mean(e4 ** 2)), mae_ili=float(np.mean(np.abs(e4))),
               best_val="", best_epoch="",
               n_train="", n_val="", n_test=int(pred.shape[0]),
               total_parameters=MIFLU_TRAINABLE_PARAMS,
               trainable_parameters=MIFLU_TRAINABLE_PARAMS, ckpt="", ckpt_sidecar="")
    # n_train / n_val follow the strict-containment counts of the same L
    counts = {24: (549, 74), 36: (537, 62), 48: (525, 50), 60: (513, 38)}
    if L in counts:
        row["n_train"], row["n_val"] = counts[L]
    d = os.path.join(out_root, f"miflu_L{L}_s{seed}")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "metrics.csv")
    pd.DataFrame([row])[METRICS_COLS].to_csv(p, index=False)
    return p


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Import MIFlu predictions into the benchmark cell format.")
    ap.add_argument("--horizons", type=int, nargs="+", default=[24, 36, 48, 60])
    ap.add_argument("--csv-pattern", default="author_runs/L{L}_s2021/predictions_miflu_L{L}_paper_protocol.csv",
                    help="path pattern; {L} and {S} are substituted")
    ap.add_argument("--npz-dir", default="", help="directory with pred_miflu_L{L}_s{seed}.npz")
    ap.add_argument("--seeds", type=int, nargs="+", default=[2021])
    ap.add_argument("--resolve-seed-from-path", action="store_true",
                    help="read the seed from '__seed<N>' in the file name")
    ap.add_argument("--check", action="store_true", help="verify alignment only; write nothing")
    ap.add_argument("--out-root", default=EXP)
    args = ap.parse_args()

    written, failed = [], []
    for L in args.horizons:
        ref_target, ref_windows, ref_path = reference_cell(L)
        print(f"\n=== L={L}  reference: {os.path.relpath(ref_path, ROOT)} "
              f"({ref_target.shape[0]} windows, {ref_windows.min()}..{ref_windows.max()})")
        seeds = args.seeds
        for seed in seeds:
            label, pred = "", None
            if args.npz_dir:
                got = _load_npz_set(os.path.join(ROOT, args.npz_dir) if not os.path.isabs(args.npz_dir) else args.npz_dir, L, seed)
                if got is None:
                    print(f"  [skip] no npz for seed {seed}")
                    continue
                pred, target, windows, raw, path = got
                label = os.path.relpath(path, ROOT)
                if not check_alignment(pred, target, windows, ref_target, ref_windows, L, label):
                    failed.append(path); continue
                partial = bool(np.asarray(raw.get("partial", False)).ravel()[0]) if "partial" in raw.files else False
                if not args.check:
                    out = write_cell(pred, target, windows, L, seed, partial, args.out_root)
                    mp = write_metrics(L, seed, pred, target, args.out_root)
                    written += [out, mp]
                    print(f"  [ok]  wrote {os.path.relpath(out, ROOT)} + metrics.csv")
                continue

            path = args.csv_pattern.replace("{L}", str(L)).replace("{S}", str(seed))
            if not os.path.isabs(path):
                path = os.path.join(ROOT, path)
            if not os.path.exists(path):
                print(f"  [skip] missing {os.path.relpath(path, ROOT)}")
                continue
            if args.resolve_seed_from_path:
                m = re.search(r"__seed(\d+)", os.path.basename(path))
                if m:
                    seed = int(m.group(1))
            pred, target, kind = _cube_from_csv(path, L, ref_target, ref_windows)
            label = f"{os.path.relpath(path, ROOT)} [{kind}]"
            windows = ref_windows
            if not check_alignment(pred, target, windows, ref_target, ref_windows, L, label):
                failed.append(path); continue
            partial = (kind == "csv-partial")
            chans = int(sum(np.isfinite(pred[:, c, :]).any() for c in range(7)))
            print(f"  [ok]  channels filled = {chans}/7  partial={partial}")
            if not args.check:
                out = write_cell(pred, target, windows, L, seed, partial, args.out_root)
                mp = write_metrics(L, seed, pred, target, args.out_root)
                written += [out, mp]
                print(f"  [ok]  wrote {os.path.relpath(out, ROOT)} + metrics.csv")

    print("\n" + "=" * 70)
    if args.check:
        print("CHECK MODE: nothing written.")
    else:
        print(f"cells written: {len(written)//2}, files: {len(written)}")
        for w in written:
            print("   ", os.path.relpath(w, ROOT))
    if failed:
        print(f"FAILED alignment ({len(failed)}):")
        for f in failed:
            print("   ", os.path.relpath(f, ROOT))
        return 1
    if not written and not any(os.path.exists(args.csv_pattern.replace('{L}', str(L)).replace('{S}', str(args.seeds[0]))) for L in args.horizons):
        print("nothing found and nothing written -- the source exports are absent "
              "(see AGENTS.md 13.E: HPC fetch blocked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
