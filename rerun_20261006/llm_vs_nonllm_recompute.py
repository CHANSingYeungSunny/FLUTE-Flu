#!/usr/bin/env python3
"""Independent re-run of the LLM vs non-LLM comparison (2026-10-06).

Auditor's own implementation. It does NOT import any project scoring module:
- A-track (author 966-row data): recomputed from the stored prediction NPZs,
  i.e. from raw (pred, target) tensors in z-space.
- B-track (July-2026 snapshot, 1025 rows): recomputed from the seed-level
  metric table, re-aggregated from scratch.

Aggregation rule (as declared by the project):
  mse_all(model, L, seed) = mean of squared error over
                            (test origins x leads x 7 variables), z-space
  average_MSE_4L(model)   = mean over seeds, then equal-weight mean over the
                            four horizons L=24/36/48/60

Outputs CSV + a console summary. Nothing is overwritten.
"""
import csv
import glob
import json
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)

STAGE6 = os.path.join(PROJ, "audit_20260930", "predictions_stage6")
STAGE5 = os.path.join(PROJ, "hpc_results", "stage5_a2", "scoring", "predictions")
SCORE6 = os.path.join(PROJ, "hpc_results", "stage6", "scoring", "score_matrix.csv")
B_SEED = os.path.join(PROJ, "results", "v3_clean", "analysis", "primary_seed_level.csv")

HORIZONS = [24, 36, 48, 60]

# Group definitions. Two conventions, both reported (never mixed silently).
GROUP_4V4 = {
    "llm": ["miflu", "gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"],
    "non_llm": ["nlinear", "dlinear", "patchtst", "itransformer"],
}
GROUP_3V5 = {
    "llm": ["qwen_time_llm", "calf_llm", "timecma_llm"],
    "non_llm": ["nlinear", "dlinear", "patchtst", "itransformer", "miflu", "gpt2_miflu"],
}


def cell_metric(path):
    """Recompute MSE/MAE in z-space straight from the prediction tensor."""
    z = np.load(path, allow_pickle=True)
    pred = np.asarray(z["pred"], dtype=np.float64)
    targ = np.asarray(z["target"], dtype=np.float64)
    assert pred.shape == targ.shape, (path, pred.shape, targ.shape)
    err = pred - targ
    return {
        "model": str(z["model"]),
        "L": int(z["L"]),
        "seed": int(z["seed"]),
        "space": str(z["space"]),
        "n_origins": int(pred.shape[0]),
        "n_vars": int(pred.shape[1]),
        "mse_all": float(np.mean(err ** 2)),
        "mae_all": float(np.mean(np.abs(err))),
    }


def collect_track(npz_dirs):
    """Latest occurrence wins, but stage6 (the unified scoring set) is loaded
    last so its cells take precedence over the stage5 duplicates."""
    cells = {}
    for d in npz_dirs:
        for p in sorted(glob.glob(os.path.join(d, "*.npz"))):
            c = cell_metric(p)
            cells[(c["model"], c["L"], c["seed"])] = c
    return cells


def average_4L(cells, models):
    """mean over seeds within each L, then equal-weight mean over L."""
    out = {}
    for m in models:
        per_L = {}
        for L in HORIZONS:
            v = [c["mse_all"] for (mm, LL, s), c in cells.items() if mm == m and LL == L]
            if v:
                per_L[L] = (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, len(v))
        if len(per_L) == 4:
            out[m] = {
                "average_MSE_4L": float(np.mean([per_L[L][0] for L in HORIZONS])),
                "per_L": per_L,
                "n_cells": sum(per_L[L][2] for L in HORIZONS),
            }
    return out


def group_stats(avg, groups, label):
    rows = []
    for grp, members in groups.items():
        members = [m for m in members if m in avg]
        if not members:
            continue
        v = [avg[m]["average_MSE_4L"] for m in members]
        rows.append({
            "convention": label, "group": grp, "n_models": len(members),
            "members": "|".join(members),
            "group_mean": float(np.mean(v)),
            "group_min": float(np.min(v)),
            "group_max": float(np.max(v)),
            "group_sd": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0,
        })
    return rows


def paired_vs(cells, model, ref):
    """Paired per-cell differences across the 12 (L, seed) cells."""
    keys = sorted({(L, s) for (m, L, s) in cells if m == model} &
                  {(L, s) for (m, L, s) in cells if m == ref})
    d = []
    for (L, s) in keys:
        a = cells.get((model, L, s))
        b = cells.get((ref, L, s))
        if a and b:
            d.append(a["mse_all"] - b["mse_all"])
    if len(d) < 2:
        return None
    d = np.asarray(d, dtype=float)
    n = len(d)
    mean, sd = d.mean(), d.std(ddof=1)
    se = sd / np.sqrt(n)
    t = mean / se if se > 0 else float("nan")
    return {"n_pairs": int(n), "mean_diff": float(mean), "sd": float(sd),
            "t": float(t), "wins": int((d < 0).sum())}


def read_b_track():
    """Re-aggregate the July-2026 seed-level table from scratch."""
    by = defaultdict(lambda: defaultdict(list))
    with open(B_SEED, newline="") as fh:
        for r in csv.DictReader(fh):
            by[r["model"]][int(r["horizon"])].append(float(r["mse_all_7vars_full_horizon_z"]))
    out = {}
    for m, per in by.items():
        if len(per) != 4:
            continue
        out[m] = {
            "average_MSE_4L": float(np.mean([np.mean(per[L]) for L in HORIZONS])),
            "per_L": {L: (float(np.mean(per[L])), float(np.std(per[L], ddof=1)), len(per[L]))
                      for L in HORIZONS},
            "n_cells": sum(len(per[L]) for L in HORIZONS),
        }
    return out


def write_csv(path, rows, fields=None):
    if not rows:
        return
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    print("=" * 78)
    print("LLM vs non-LLM : independent recomputation, 2026-10-06")
    print("=" * 78)

    # ---------------- A track ------------------------------------------------
    cells = collect_track([STAGE5, STAGE6])
    models_a = sorted({m for (m, L, s) in cells})
    print(f"\n[A] author 966-row track: {len(cells)} cells, "
          f"{len(models_a)} models: {models_a}")
    avg_a = average_4L(cells, models_a)

    # cross-check against the project's own score matrix
    ok = bad = 0
    maxrel = 0.0
    if os.path.exists(SCORE6):
        with open(SCORE6, newline="") as fh:
            for r in csv.DictReader(fh):
                k = (r["model"], int(r["L"]), int(r["seed"]))
                if k in cells:
                    mine = cells[k]["mse_all"]
                    theirs = float(r["mse_all"])
                    rel = abs(mine - theirs) / max(abs(theirs), 1e-12)
                    maxrel = max(maxrel, rel)
                    if rel < 1e-5:
                        ok += 1
                    else:
                        bad += 1
        print(f"[A] cross-check vs project score_matrix: {ok} match / {bad} mismatch "
              f"(max rel diff {maxrel:.3e})")

    print("\n[A] average_MSE_4L (author 966, z-space, 3 seeds x 4 horizons)")
    for m in sorted(avg_a, key=lambda x: avg_a[x]["average_MSE_4L"]):
        print(f"    {m:18s} {avg_a[m]['average_MSE_4L']:.6f}   "
              f"(cells={avg_a[m]['n_cells']})")

    print("\n[A] paired vs nlinear (12 cells)")
    paired_rows = []
    for m in sorted(avg_a):
        if m == "nlinear":
            continue
        p = paired_vs(cells, m, "nlinear")
        if p:
            print(f"    {m:18s} mean_diff={p['mean_diff']:+.4f}  t={p['t']:+.2f}  "
                  f"wins={p['wins']}/{p['n_pairs']}")
            paired_rows.append({"track": "A_author966", "model": m, "ref": "nlinear", **p})

    # ---------------- B track -----------------------------------------------
    avg_b = read_b_track()
    print(f"\n[B] July-2026 snapshot track: {len(avg_b)} models, "
          f"{sum(v['n_cells'] for v in avg_b.values())} cells")
    print("\n[B] average_MSE_4L (July 1025, z-space, 10 seeds x 4 horizons)")
    for m in sorted(avg_b, key=lambda x: avg_b[x]["average_MSE_4L"]):
        print(f"    {m:18s} {avg_b[m]['average_MSE_4L']:.6f}   "
              f"(cells={avg_b[m]['n_cells']})")

    # ---------------- grouping ----------------------------------------------
    rows = []
    rows += group_stats(avg_a, GROUP_4V4, "4v4")
    rows += group_stats(avg_a, GROUP_3V5, "3v5")
    rows += group_stats(avg_b, GROUP_4V4, "4v4")

    print("\n" + "=" * 78)
    print("GROUP MEANS")
    print("=" * 78)
    for trk, tav in (("A_author966", avg_a), ("B_july1025", avg_b)):
        for conv, G in (("4v4", GROUP_4V4), ("3v5", GROUP_3V5)):
            members = {g: [m for m in ms if m in tav] for g, ms in G.items()}
            if not all(members.values()):
                continue
            lm = np.mean([tav[m]["average_MSE_4L"] for m in members["llm"]])
            nm = np.mean([tav[m]["average_MSE_4L"] for m in members["non_llm"]])
            print(f"  {trk} [{conv}]  LLM={lm:.6f} (n={len(members['llm'])})   "
                  f"non-LLM={nm:.6f} (n={len(members['non_llm'])})   "
                  f"gap={lm - nm:+.6f}")

    # ------------------------------------------------------------------ output
    write_csv(os.path.join(HERE, "recomputed_A_average_mse_4L.csv"),
              [{"model": m, **{f"MSE_L{L}": avg_a[m]["per_L"][L][0] for L in HORIZONS},
                "average_MSE_4L": avg_a[m]["average_MSE_4L"], "n_cells": avg_a[m]["n_cells"]}
               for m in sorted(avg_a, key=lambda x: avg_a[x]["average_MSE_4L"])])
    write_csv(os.path.join(HERE, "recomputed_B_average_mse_4L.csv"),
              [{"model": m, **{f"MSE_L{L}": avg_b[m]["per_L"][L][0] for L in HORIZONS},
                "average_MSE_4L": avg_b[m]["average_MSE_4L"], "n_cells": avg_b[m]["n_cells"]}
               for m in sorted(avg_b, key=lambda x: avg_b[x]["average_MSE_4L"])])
    write_csv(os.path.join(HERE, "group_means.csv"), rows)
    write_csv(os.path.join(HERE, "paired_vs_nlinear.csv"), paired_rows)

    with open(os.path.join(HERE, "recompute_summary.json"), "w") as fh:
        json.dump({
            "generated": "2026-10-06",
            "track_A": {"n_cells": len(cells),
                        "avg": {m: avg_a[m]["average_MSE_4L"] for m in avg_a}},
            "track_B": {"avg": {m: avg_b[m]["average_MSE_4L"] for m in avg_b}},
            "score_matrix_crosscheck": {"match": ok, "mismatch": bad, "max_rel": maxrel},
        }, fh, indent=2)
    print(f"\nwritten to {HERE}")


if __name__ == "__main__":
    main()