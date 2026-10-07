#!/usr/bin/env python3
"""Independent recomputation of the primary metric from the stored prediction
artefacts. This is the auditor's OWN implementation: it does not import or call
the project's `recompute_eight.py`, so agreement is real corroboration rather
than a re-run of the same code.

Protocol being checked (as documented by the project):
  mse_all(model, L, seed) = mean over (test origins x forecast leads x 7
                            variables) of squared error in z-space
  average_MSE_4L(model)   = mean over seeds, then equal-weight mean over L
  z-scores are fitted on TRAIN rows only, i.e. rows [0, 676) of the 966-row
  author file.

Run with --probe to inspect the NPZ schema first.
"""
import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PAPER_EXACT = os.path.join(PROJ, "data", "raw", "national_illness_raw_paper_exact.csv")

VARS = ["_WEIGHTED_ILI", "_UNWEIGHTED_ILI", "AGE_04", "AGE_524",
        "ILITOTAL", "NUM_OF_PROVIDERS", "OT"]
N_TRAIN = 676


def probe(path):
    z = np.load(path, allow_pickle=True)
    print(f"--- {os.path.basename(path)}")
    for k in z.files:
        a = z[k]
        try:
            print(f"    {k:24s} shape={a.shape} dtype={a.dtype}")
        except AttributeError:
            print(f"    {k:24s} = {a!r}")


def load_index(npzdir, pattern="*.npz"):
    """Map (model, L, seed) -> file path, from the file names."""
    out = {}
    for p in sorted(glob.glob(os.path.join(npzdir, pattern))):
        z = np.load(p, allow_pickle=True)
        model = str(z["model"]) if "model" in z.files else None
        L = int(z["L"]) if "L" in z.files else None
        seed = int(z["seed"]) if "seed" in z.files else None
        if model is None:
            # fall back to parsing the file name
            b = os.path.basename(p)[:-4]
            parts = b.split("_")
            model, L, seed = parts[0], int(parts[1][1:]), int(parts[2][1:])
        out[(model, L, seed)] = p
    return out


def read_score_matrix(path):
    with open(path, newline="") as fh:
        return { (r["model"], int(r["L"]), int(r["seed"])): r
                 for r in csv.DictReader(fh) }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--stage6", default=os.path.join(HERE, "predictions_stage6"))
    ap.add_argument("--stage5", default=os.path.join(
        PROJ, "hpc_results", "stage5_a2", "scoring", "predictions"))
    ap.add_argument("--score6", default=os.path.join(
        PROJ, "hpc_results", "stage6", "scoring", "score_matrix.csv"))
    ap.add_argument("--score5", default=os.path.join(
        PROJ, "hpc_results", "stage5_a2", "scoring", "score_matrix.csv"))
    args = ap.parse_args()

    if args.probe:
        f6 = sorted(glob.glob(os.path.join(args.stage6, "*.npz")))
        f5 = sorted(glob.glob(os.path.join(args.stage5, "*.npz")))
        print(f"stage6 npz={len(f6)}  stage5 npz={len(f5)}")
        if f6:
            probe(f6[0])
            print()
            probe(f6[-1])
        if f5:
            print()
            probe(f5[0])
        return

    # ---- independent z-scoring, fitted on the train block only --------------
    raw = np.genfromtxt(PAPER_EXACT, delimiter=",", names=True, dtype=None,
                        encoding="utf-8")
    names = list(raw.dtype.names)
    print(f"[audit] author data: {len(raw)} rows, columns = {names}")
    missing = [v for v in VARS if v not in names]
    if missing:
        print(f"[audit] ABORT: expected variables not found: {missing}")
        sys.exit(2)
    X = np.column_stack([raw[v].astype(float) for v in VARS])
    train = X[:N_TRAIN]
    mu, sd = train.mean(axis=0), train.std(axis=0)
    print(f"[audit] scaler fitted on rows [0,{N_TRAIN}); mu[0..2]={mu[:3]}")
    print(f"[audit] sd[0..2]={sd[:3]}")

    idx6 = load_index(args.stage6)
    idx5 = load_index(args.stage5)
    print(f"[audit] stage6 cells={len(idx6)}  stage5 cells={len(idx5)}")

    sm6 = read_score_matrix(args.score6)
    sm5 = read_score_matrix(args.score5)

    # ---- the scaler stored inside the artefacts must match a scaler that I
    #      fitted myself on rows [0, 676); otherwise "z-space" is not a shared
    #      definition and the comparison is meaningless.
    if idx6:
        any6 = np.load(sorted(idx6.values())[0], allow_pickle=True)
        sm_mu = np.asarray(any6["train_mean"], dtype=float).ravel()
        sm_sd = np.asarray(any6["train_std"], dtype=float).ravel()
        print(f"[audit] artefact var_cols = {list(any6['var_cols'])}")
        print(f"[audit] artefact space    = {any6['space']!r}")
        print(f"[audit] artefact profile  = {any6['profile']!r}  "
              f"containment={any6['containment']!r}")
        print(f"[audit] artefact train_mean = {np.round(sm_mu, 6)}")
        print(f"[audit] my       train_mean = {np.round(mu, 6)}")
        print(f"[audit] artefact train_std  = {np.round(sm_sd, 6)}")
        print(f"[audit] my       train_std  = {np.round(sd, 6)}")
        print(f"[audit] scaler max|diff| mean={np.max(np.abs(sm_mu - mu)):.3e} "
              f"std={np.max(np.abs(sm_sd - sd)):.3e}")

    for label, idx, sm in (("stage6", idx6, sm6), ("stage5", idx5, sm5)):
        print()
        print("=" * 70)
        print(f"{label}: recompute vs stored score_matrix ({len(sm)} stored rows)")
        print("=" * 70)
        worst = 0.0
        worst_rel = 0.0
        worst_key = None
        n = 0
        checked = 0
        per_cell = {}
        for key, path in sorted(idx.items()):
            if key not in sm:
                continue
            checked += 1
            z = np.load(path, allow_pickle=True)
            keys = set(z.files)
            pred = np.asarray(z["pred"], dtype=np.float64)
            tgt = np.asarray(z["target"], dtype=np.float64)
            mine = float(np.mean((pred - tgt) ** 2))
            stored = float(sm[key]["mse_all"])
            per_cell[key] = mine
            d = abs(mine - stored)
            rel = d / abs(stored) if stored else 0.0
            n += 1
            if rel > worst_rel:
                worst_rel, worst, worst_key = rel, d, key
        print(f"  cells compared          = {n} (of {checked} present in both)")
        print(f"  worst absolute diff     = {worst:.3e}   at {worst_key}")
        print(f"  worst RELATIVE diff     = {worst_rel:.3e}  at {worst_key}")
        # float32 artefacts cannot resolve better than ~1.2e-7 relative
        print("  note: artefacts are float32, so ~1.2e-7 is the storage floor")
        print(f"  verdict: {'PASS' if worst_rel < 1e-5 else 'REVIEW (differs)'}")

        # ---- average_MSE_4L: mean over seeds, then equal-weight mean over L ---
        if per_cell:
            agg = {}
            for (m, L, s), v in per_cell.items():
                if m.endswith("_naive"):
                    continue
                agg.setdefault(m, {}).setdefault(L, []).append(v)
            print()
            print("  recomputed average_MSE_4L (independent):")
            table = {}
            for m in sorted(agg):
                per_L = {L: float(np.mean(vs)) for L, vs in agg[m].items()}
                table[m] = float(np.mean(list(per_L.values())))
                print(f"    {m:18s} {table[m]:.6f}   "
                      f"(L values: {', '.join(f'{L}:{v:.4f}' for L, v in sorted(per_L.items()))})")
            ref = os.path.join(PROJ, "hpc_results", "stage6" if label == "stage6"
                               else "stage5_a2", "scoring", "average_mse_4L.csv")
            if os.path.exists(ref):
                print(f"\n  stored  -> {ref}")
                with open(ref, newline="") as fh:
                    for r in csv.DictReader(fh):
                        k = list(r.keys())
                        m = r.get("model") or r.get(k[0])
                        v = r.get("average_MSE_4L") or r.get(k[-1])
                        if m in table:
                            try:
                                diff = abs(table[m] - float(v))
                            except (TypeError, ValueError):
                                continue
                            print(f"    {m:18s} stored={float(v):.6f}  mine={table[m]:.6f}"
                                  f"  diff={diff:.3e}")
            outpath = os.path.join(HERE, f"independent_average_mse_4L_{label}.csv")
            with open(outpath, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["model", "average_MSE_4L_independent"])
                for m in sorted(table):
                    w.writerow([m, f"{table[m]:.9f}"])
            print(f"  written -> {outpath}")


if __name__ == "__main__":
    main()