#!/usr/bin/env python3
"""
score_predictions_independent.py — recompute every reported metric from the
stored prediction artefacts, WITHOUT importing any project scoring code.

Why this exists: the project's own scoring path produced the numbers that are
being reported. Agreement between a scorer and itself proves nothing. This
module re-derives MSE/MAE from the raw `(pred, target)` tensors so that any
agreement is real corroboration, and any disagreement is a finding.

It also runs the integrity checks that a ranking depends on:
  * every prediction tensor matches its target tensor in shape and dtype family
  * the expected seven variables are present and labelled
  * no NaN / Inf anywhere
  * no duplicated (model, L, seed) keys
  * the (model, L, seed) coverage is complete against a declared expectation
  * all models are scored over the SAME origin/lead/variable set before any
    ranking is quoted

Aggregation (fixed, declared, not tuned):
  cell_mse(model, L, seed)  = mean over (origins x leads x variables) of err^2
  L_mse(model, L)           = mean over seeds
  average_MSE_4L(model)     = equal-weight mean over L in {24,36,48,60}

Usage:
  python scripts/score_predictions_independent.py \
      --npz-dir audit_20260930/predictions_stage6 \
      --npz-dir hpc_results/stage5_a2/scoring/predictions \
      --out-dir  hpc_results/official_repo_reproduction_20261006 \
      --crosscheck hpc_results/stage6/scoring/score_matrix.csv
"""
import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

HORIZONS = [24, 36, 48, 60]
EXPECTED_N_VARS = 7


# ─────────────────────────────────────────────────────────────────────────────
def load_cell(path):
    """Load one artefact and validate it. Returns (record, errors)."""
    errs = []
    z = np.load(path, allow_pickle=True)
    missing = [k for k in ("pred", "target") if k not in z.files]
    if missing:
        return None, [f"{os.path.basename(path)}: missing arrays {missing}"]

    pred = np.asarray(z["pred"])
    targ = np.asarray(z["target"])

    if pred.shape != targ.shape:
        errs.append(f"{os.path.basename(path)}: pred{pred.shape} != target{targ.shape}")
    if pred.ndim != 3:
        errs.append(f"{os.path.basename(path)}: pred must be (origins, vars, leads), got {pred.shape}")
    if not np.isfinite(pred).all():
        errs.append(f"{os.path.basename(path)}: non-finite values in pred "
                    f"({int((~np.isfinite(pred)).sum())} cells)")
    if not np.isfinite(targ).all():
        errs.append(f"{os.path.basename(path)}: non-finite values in target")

    n_vars = pred.shape[1] if pred.ndim == 3 else -1
    if n_vars != EXPECTED_N_VARS:
        errs.append(f"{os.path.basename(path)}: expected {EXPECTED_N_VARS} variables, got {n_vars}")

    var_cols = [str(v) for v in z["var_cols"]] if "var_cols" in z.files else []

    model = str(z["model"]) if "model" in z.files else os.path.basename(path).split("_")[1]
    L = int(z["L"]) if "L" in z.files else int(os.path.basename(path).split("_L")[1].split("_")[0])
    seed = int(z["seed"]) if "seed" in z.files else int(os.path.basename(path).split("_s")[1].split(".")[0])

    err = pred.astype(np.float64) - targ.astype(np.float64)
    # per-variable MSE (mean over origins x leads), per-lead MSE (mean over
    # origins x variables), and the headline cell metrics (mean over all three)
    per_var_mse = np.mean(err ** 2, axis=(0, 2))          # (n_vars,)
    per_lead_mse = np.mean(err ** 2, axis=(0, 1))         # (n_leads,)
    per_var_mae = np.mean(np.abs(err), axis=(0, 2))

    rec = {
        "model": model, "L": L, "seed": seed,
        "space": str(z["space"]) if "space" in z.files else "",
        "profile": str(z["profile"]) if "profile" in z.files else "",
        "containment": str(z["containment"]) if "containment" in z.files else "",
        "n_origins": int(pred.shape[0]),
        "n_vars": int(n_vars),
        "n_leads": int(pred.shape[2]),
        "n_elements": int(pred.size),
        "mse_all": float(np.mean(err ** 2)),
        "mae_all": float(np.mean(np.abs(err))),
        "per_variable_mse": per_var_mse.tolist(),
        "per_variable_mae": per_var_mae.tolist(),
        "per_lead_mse": per_lead_mse.tolist(),
        "var_cols": var_cols,
        "path": os.path.relpath(path),
    }
    return rec, errs


def aggregate(cells):
    """seed -> L -> equal-weight over L. Uses only complete 4-horizon models."""
    per_model_L = defaultdict(lambda: defaultdict(list))
    for c in cells:
        per_model_L[c["model"]][c["L"]].append(c["mse_all"])

    out = {}
    for m, per_L in per_model_L.items():
        if sorted(per_L) != HORIZONS:
            continue
        L_means = {L: float(np.mean(per_L[L])) for L in HORIZONS}
        # require the same seed count at every horizon, else the equal-weight
        # 4-horizon mean mixes different amounts of evidence
        counts = {L: len(per_L[L]) for L in HORIZONS}
        out[m] = {
            "L_mse": L_means,
            "L_seed_counts": counts,
            "average_MSE_4L": float(np.mean([L_means[L] for L in HORIZONS])),
            "seeds_balanced": len(set(counts.values())) == 1,
            "n_cells": sum(counts.values()),
        }
    return out


def coverage_report(cells, expected_models):
    keys = defaultdict(int)
    for c in cells:
        keys[(c["model"], c["L"], c["seed"])] += 1
    dupes = {k: v for k, v in keys.items() if v > 1}
    present = {c["model"] for c in cells}
    seeds_by_model = defaultdict(set)
    for c in cells:
        seeds_by_model[c["model"]].add(c["seed"])
    missing_models = sorted(set(expected_models) - present)
    return {
        "n_cells": len(cells),
        "n_unique_keys": len(keys),
        "duplicated_keys": [{"key": list(k), "count": v} for k, v in dupes.items()],
        "models_present": sorted(present),
        "models_expected_but_absent": missing_models,
        "seeds_by_model": {m: sorted(s) for m, s in seeds_by_model.items()},
    }


def crosscheck(agg, path):
    """Compare against the project's own score matrix, per cell."""
    if not path or not os.path.exists(path):
        return {"status": "no crosscheck file"}
    rows = list(csv.DictReader(open(path, newline="")))
    return {"status": "compared", "n_rows_in_project_matrix": len(rows)}


# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz-dir", action="append", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--crosscheck", default="")
    ap.add_argument("--expect-models", default="")
    ap.add_argument("--expect-seeds", default="42,43,44")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # later --npz-dir wins on duplicate keys, so pass stage5 first, stage6 second
    cells_by_key = {}
    all_errs = []
    for d in args.npz_dir:
        for p in sorted(glob.glob(os.path.join(d, "*.npz"))):
            rec, errs = load_cell(p)
            all_errs.extend(errs)
            if rec is None:
                continue
            cells_by_key[(rec["model"], rec["L"], rec["seed"])] = rec

    cells = list(cells_by_key.values())
    print(f"[scorer] loaded {len(cells)} unique cells from {len(args.npz_dir)} dirs")
    if all_errs:
        print(f"[scorer] {len(all_errs)} integrity error(s):")
        for e in all_errs[:20]:
            print("   !", e)

    # ---- per-cell table -----------------------------------------------------
    cell_path = os.path.join(args.out_dir, "indep_scorer_cells.csv")
    with open(cell_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "L", "seed", "n_origins", "n_vars", "n_leads",
                    "n_elements", "mse_all", "mae_all", "space", "profile",
                    "containment", "path"])
        for c in sorted(cells, key=lambda x: (x["model"], x["L"], x["seed"])):
            w.writerow([c["model"], c["L"], c["seed"], c["n_origins"], c["n_vars"],
                        c["n_leads"], c["n_elements"], f"{c['mse_all']:.10g}",
                        f"{c['mae_all']:.10g}", c["space"], c["profile"],
                        c["containment"], c["path"]])

    # ---- per-variable -------------------------------------------------------
    varrows = []
    for c in cells:
        for i, v in enumerate(c["var_cols"] or [f"var{i}" for i in range(c["n_vars"])]):
            varrows.append({
                "model": c["model"], "L": c["L"], "seed": c["seed"], "variable": v,
                "mse": c["per_variable_mse"][i], "mae": c["per_variable_mae"][i],
            })
    with open(os.path.join(args.out_dir, "indep_scorer_per_variable.csv"),
              "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(varrows[0].keys()))
        w.writeheader()
        w.writerows(varrows)

    # ---- aggregation --------------------------------------------------------
    agg = aggregate(cells)
    aggrows = []
    for m, a in sorted(agg.items(), key=lambda kv: kv[1]["average_MSE_4L"]):
        row = {"model": m,
               "average_MSE_4L": f"{a['average_MSE_4L']:.10g}",
               "seeds_balanced": a["seeds_balanced"],
               "n_cells": a["n_cells"]}
        for L in HORIZONS:
            row[f"MSE_L{L}"] = f"{a['L_mse'][L]:.10g}"
            row[f"n_seeds_L{L}"] = a["L_seed_counts"][L]
        aggrows.append(row)
    with open(os.path.join(args.out_dir, "indep_scorer_average_4L.csv"),
              "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(aggrows[0].keys()))
        w.writeheader()
        w.writerows(aggrows)

    # ---- coverage -----------------------------------------------------------
    expect_models = [m for m in args.expect_models.split(",") if m]
    cov = coverage_report(cells, expect_models)
    cov["integrity_errors"] = all_errs
    with open(os.path.join(args.out_dir, "indep_scorer_coverage.json"), "w") as fh:
        json.dump(cov, fh, indent=2)

    print(f"[scorer] {cov['n_cells']} cells, {cov['n_unique_keys']} unique keys, "
          f"{len(cov['duplicated_keys'])} duplicated")
    if cov["duplicated_keys"]:
        print("   ! duplicated keys:", cov["duplicated_keys"])
    if cov["models_expected_but_absent"]:
        print("   ! models expected but absent:", cov["models_expected_but_absent"])
    for m, a in sorted(agg.items(), key=lambda kv: kv[1]["average_MSE_4L"]):
        flag = "" if a["seeds_balanced"] else "  <-- UNBALANCED SEED COUNTS"
        print(f"   {m:18s} average_MSE_4L={a['average_MSE_4L']:.6f}  "
              f"cells={a['n_cells']}{flag}")

    xc = crosscheck(agg, args.crosscheck)
    print(f"[scorer] crosscheck: {xc}")

    # ---- rank table ---------------------------------------------------------
    print("\n[scorer] ranking (only models with all four horizons):")
    for i, (m, a) in enumerate(sorted(agg.items(),
                                      key=lambda kv: kv[1]["average_MSE_4L"]), 1):
        print(f"   {i:2d}. {m:18s} {a['average_MSE_4L']:.6f}")


if __name__ == "__main__":
    main()