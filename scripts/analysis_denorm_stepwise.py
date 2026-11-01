#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""analysis_denorm_stepwise.py  (v2 — per-season peak matched PTE/PIE)

Computes, entirely from the frozen local prediction artefacts
`audit_20260930/predictions_stage6/pred_<model>_L<L>_s<seed>.npz`:

  1. Denormalized (physical-unit) MSE / MAE per variable, per model, per L.
  2. Per-step MSE for lead s in {0,1,2,3} = (s+1) weeks ahead, plus the
     full-horizon L-step MSE, for every model x L x seed.
  3. Per-step PTE / PIE with the Kramer & Shaman (2019) criterion
     (PTE <= 1 week AND PIE <= 25%).

Why v2: v1 used one global argmax over the whole test span, which is invalid
because the 170-week test range contains ~3 influenza seasons; a single global
peak is not a "seasonal peak" and produced nonsense PTE values of 100+ weeks.
v2 detects each epidemic peak in the ground truth and matches the prediction's
strongest response within +/-8 weeks, then averages over seasons -- this is the
per-season definition K&S actually use.

Estimators (do not conflate):
  * `mse_z_7var`   : mean over (window, lead, variable) of squared z-scale
                     error. The essay-comparable reproduction metric.
  * `mse_phys_j`   : mse_z_j * std_j**2        (physical units squared)
  * `mse_phys_agg` : mean_j mse_z_j * std_j**2 (de-normalized aggregate;
                     mixed units -- order of magnitude only)
  * PTE/PIE        : per-season peak matched, on a chosen series. This is a
                     DIFFERENT estimator from the project's official
                     matched-event peak table (which yielded 15/36 etc.);
                     the two must not be quoted interchangeably.

Outputs -> paper_tables/ and results/stepwise_pte_pie/
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ_DIR = os.path.join(ROOT, "audit_20260930", "predictions_stage6")
SCALER_PATH = os.path.join(ROOT, "data", "scaler_miflu_author966.json")
OUT_TABLES = os.path.join(ROOT, "paper_tables")
OUT_FIGS = os.path.join(ROOT, "results", "stepwise_pte_pie")

MODELS = ["miflu", "notext", "nlinear", "dlinear", "patchtst",
          "itransformer", "timecma_llm", "qwen_time_llm", "calf_llm"]
LLM_SIDE = {"miflu": "LLM", "notext": "LLM-ablation", "timecma_llm": "LLM",
            "qwen_time_llm": "LLM", "calf_llm": "LLM",
            "nlinear": "non-LLM", "dlinear": "non-LLM", "patchtst": "non-LLM",
            "itransformer": "non-LLM"}

STEPS = [0, 1, 2, 3]
VAR_WILI = 0        # % WEIGHTED ILI -- Kramer & Shaman's ILI signal
VAR_ILITOTAL = 4
PEAK_PROM = 0.15    # prominence as a fraction of the series range
PEAK_DIST = 15      # minimum weeks between two distinct seasonal peaks
MATCH_WIN = 8       # +/- weeks allowed when matching a predicted peak


def load_miflu_trackc():
    """MIFlu must come from the Track-C `miflu_strict966` CSVs (4L mean 1.8652),
    NOT from `audit_20260930/predictions_stage6/pred_miflu_*` which is the
    stage-6 / A-track instance (4L mean 2.0415). Mixing the two tracks is
    forbidden by the project rules: the A/B track numbers are not comparable.
    """
    cells = {}
    with open(SCALER_PATH, encoding="utf-8") as f:
        _sc = json.load(f)
    _mean = np.array(_sc["mean"], dtype=float)
    _std = np.array(_sc["std"], dtype=float)
    base = os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria", "miflu")
    for path in sorted(glob.glob(os.path.join(base, "**", "test_predictions_*L*seed*.csv"),
                                  recursive=True)):
        m = re.search(r"L(\d+)__seed(\d+)", os.path.basename(path))
        if not m:
            continue
        L, seed = int(m.group(1)), int(m.group(2))
        df = pd.read_csv(path)
        if df.empty:
            continue
        w = np.sort(df["target_start_row"].unique())
        wi = {int(v): i for i, v in enumerate(w)}
        V = 7
        pred = np.full((len(w), V, L), np.nan)
        target = np.full((len(w), V, L), np.nan)
        for r in df.itertuples(index=False):
            i = wi[int(r.target_start_row)]
            j = int(r.feature_index)
            k = int(r.forecast_lead) - 1
            if 0 <= k < L and 0 <= j < V:
                pred[i, j, k] = float(r.y_pred_z)
                target[i, j, k] = float(r.y_true_z)
        if np.isnan(pred).any():
            continue
        cells[("miflu", L, seed)] = {
            "pred": pred, "target": target, "tsr": w.astype(np.int64),
            "mean": _mean, "std": _std,
        }
    return cells


def load_cells():
    cells = {}
    for path in sorted(glob.glob(os.path.join(NPZ_DIR, "pred_*.npz"))):
        m = re.match(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(path))
        if not m:
            continue
        model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
        if model not in MODELS:
            continue
        d = np.load(path)
        cells[(model, L, seed)] = {
            "pred": np.asarray(d["pred"], dtype=np.float64),
            "target": np.asarray(d["target"], dtype=np.float64),
            "tsr": np.asarray(d["target_start_row"], dtype=np.int64),
            "mean": np.asarray(d["train_mean"], dtype=np.float64).reshape(-1),
            "std": np.asarray(d["train_std"], dtype=np.float64).reshape(-1),
        }
    # MIFlu: override with the Track-C strict966 instance.
    cells.update(load_miflu_trackc())
    return cells


def per_variable_errors(pred, target):
    err = pred - target
    return (err ** 2).mean(axis=(0, 2)), np.abs(err).mean(axis=(0, 2))


def aligned_series(cell, step, var):
    weeks = cell["tsr"] + step
    return weeks, cell["target"][:, var, step], cell["pred"][:, var, step]


def seasonal_pte_pie(weeks, gt, pr):
    """Per-season peak matched PTE/PIE (Kramer & Shaman 2019)."""
    rng = float(gt.max() - gt.min())
    if rng <= 0:
        return None
    gi, _ = find_peaks(gt, prominence=PEAK_PROM * rng, distance=PEAK_DIST)
    if len(gi) == 0:
        gi = np.array([int(np.argmax(gt))])
    rows = []
    for g in gi:
        wg, vg = int(weeks[g]), float(gt[g])
        mask = np.abs(weeks - wg) <= MATCH_WIN
        if not mask.any() or vg == 0:
            continue
        pv = pr[mask]
        pw = weeks[mask]
        k = int(np.argmax(pv))
        rows.append({
            "gt_peak_week": wg, "gt_peak_val": vg,
            "pred_peak_week": int(pw[k]), "pred_peak_val": float(pv[k]),
            "PTE_wk": abs(int(pw[k]) - wg),
            "PIE_pct": abs(float(pv[k]) - vg) / abs(vg) * 100.0,
        })
    if not rows:
        return None
    d = pd.DataFrame(rows)
    return {
        "n_seasons": len(d),
        "PTE_wk": float(d["PTE_wk"].mean()),
        "PIE_pct": float(d["PIE_pct"].mean()),
        "PTE_max": float(d["PTE_wk"].max()),
        "PIE_max": float(d["PIE_pct"].max()),
        "n_season_pass": int(((d["PTE_wk"] <= 1.0) & (d["PIE_pct"] <= 25.0)).sum()),
        "seasons": d.to_dict("records"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot-seed", type=int, default=42)
    ap.add_argument("--no-figs", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT_TABLES, exist_ok=True)
    os.makedirs(OUT_FIGS, exist_ok=True)

    with open(SCALER_PATH, encoding="utf-8") as f:
        scaler = json.load(f)
    var_cols = scaler["var_cols"]

    cells = load_cells()
    print(f"loaded {len(cells)} cells from {NPZ_DIR}")

    # ── (1) per-variable denormalized errors ──────────────────────────
    var_rows = []
    for (model, L, seed), c in sorted(cells.items()):
        mse_z, mae_z = per_variable_errors(c["pred"], c["target"])
        std = c["std"]
        for j, name in enumerate(var_cols):
            var_rows.append({
                "model": model, "side": LLM_SIDE.get(model, "?"),
                "L": L, "seed": seed, "var_index": j, "variable": name,
                "std": round(float(std[j]), 4),
                "mse_z": round(float(mse_z[j]), 6),
                "mae_z": round(float(mae_z[j]), 6),
                "mse_physical": round(float(mse_z[j] * std[j] ** 2), 2),
                "mae_physical": round(float(mae_z[j] * std[j]), 2),
            })
    dfv = pd.DataFrame(var_rows)
    dfv.to_csv(os.path.join(OUT_TABLES, "DENORMALIZED_MSE_MAE_BY_VARIABLE.csv"), index=False)

    # ── (2) per-step + full-horizon MSE ───────────────────────────────
    step_rows = []
    for (model, L, seed), c in sorted(cells.items()):
        pred, target, std = c["pred"], c["target"], c["std"]
        err = pred - target
        mse_z_j_full = (err ** 2).mean(axis=(0, 2))
        step_rows.append({
            "model": model, "side": LLM_SIDE.get(model, "?"),
            "L": L, "seed": seed, "step": "full", "weeks_ahead": L,
            "mse_z_7var": round(float((err ** 2).mean()), 6),
            "mae_z_7var": round(float(np.abs(err).mean()), 6),
            "mse_phys_agg": round(float((mse_z_j_full * std ** 2).mean()), 2),
            "mse_z_wili": round(float(mse_z_j_full[VAR_WILI]), 6),
            "mse_phys_wili": round(float(mse_z_j_full[VAR_WILI] * std[VAR_WILI] ** 2), 6),
            "mse_z_ilitotal": round(float(mse_z_j_full[VAR_ILITOTAL]), 6),
            "mse_phys_ilitotal": round(float(mse_z_j_full[VAR_ILITOTAL] * std[VAR_ILITOTAL] ** 2), 2),
        })
        for s in STEPS:
            if s >= L:
                continue
            e = pred[:, :, s] - target[:, :, s]
            mse_j = (e ** 2).mean(axis=0)
            step_rows.append({
                "model": model, "side": LLM_SIDE.get(model, "?"),
                "L": L, "seed": seed, "step": s, "weeks_ahead": s + 1,
                "mse_z_7var": round(float((e ** 2).mean()), 6),
                "mae_z_7var": round(float(np.abs(e).mean()), 6),
                "mse_phys_agg": round(float((mse_j * std ** 2).mean()), 2),
                "mse_z_wili": round(float(mse_j[VAR_WILI]), 6),
                "mse_phys_wili": round(float(mse_j[VAR_WILI] * std[VAR_WILI] ** 2), 6),
                "mse_z_ilitotal": round(float(mse_j[VAR_ILITOTAL]), 6),
                "mse_phys_ilitotal": round(float(mse_j[VAR_ILITOTAL] * std[VAR_ILITOTAL] ** 2), 2),
            })
    dfs = pd.DataFrame(step_rows)
    dfs.to_csv(os.path.join(OUT_TABLES, "PER_STEP_MSE_BY_MODEL.csv"), index=False)

    # ── (3) per-step PTE/PIE (per-season peak matched) ────────────────
    pte_rows, season_rows = [], []
    for (model, L, seed), c in sorted(cells.items()):
        for s in STEPS:
            if s >= L:
                continue
            for var, tag in ((VAR_WILI, "%WEIGHTED_ILI"), (VAR_ILITOTAL, "ILITOTAL")):
                weeks, gt, pr = aligned_series(c, s, var)
                r = seasonal_pte_pie(weeks, gt, pr)
                base = {"model": model, "side": LLM_SIDE.get(model, "?"),
                        "L": L, "seed": seed, "step": s,
                        "weeks_ahead": s + 1, "series": tag}
                if r is None:
                    pte_rows.append({**base, "n_seasons": 0, "PTE_wk": np.nan,
                                     "PIE_pct": np.nan, "PTE_max": np.nan, "PIE_max": np.nan,
                                     "n_season_pass": 0, "PTE_le_1wk": False,
                                     "PIE_le_25pct": False, "kramer_shaman_pass": False})
                    continue
                seasons = r.pop("seasons")
                pte_rows.append({**base, **r,
                                 "PTE_le_1wk": bool(r["PTE_wk"] <= 1.0),
                                 "PIE_le_25pct": bool(r["PIE_pct"] <= 25.0),
                                 "kramer_shaman_pass": bool(r["PTE_wk"] <= 1.0 and r["PIE_pct"] <= 25.0)})
                for sv in seasons:
                    season_rows.append({**base, **sv})
    dfp = pd.DataFrame(pte_rows)
    dfp.to_csv(os.path.join(OUT_TABLES, "PER_STEP_PTE_PIE_BY_MODEL.csv"), index=False)
    pd.DataFrame(season_rows).to_csv(
        os.path.join(OUT_TABLES, "PER_STEP_PTE_PIE_PER_SEASON.csv"), index=False)

    # 4-vs-4 group summary (median over cells; pass = cell-level K&S verdict)
    grp = (dfp.groupby(["side", "series", "L", "weeks_ahead"])
              .agg(n_models=("model", "nunique"),
                   n_cells=("kramer_shaman_pass", "size"),
                   n_pass=("kramer_shaman_pass", "sum"),
                   median_PTE=("PTE_wk", "median"),
                   median_PIE=("PIE_pct", "median"))
              .reset_index())
    grp["pass_rate_pct"] = (grp["n_pass"] / grp["n_cells"] * 100).round(1)
    grp.to_csv(os.path.join(OUT_TABLES, "PTE_PIE_GROUP_SUMMARY.csv"), index=False)

    if not args.no_figs:
        make_figures(cells, args.plot_seed)

    # ── console ───────────────────────────────────────────────────────
    pd.set_option("display.width", 220)
    print("\n=== 7-var MSE (z), mean over seeds, per horizon ===")
    piv = (dfs[dfs.step == "full"].groupby(["model", "L"])["mse_z_7var"]
           .mean().unstack("L"))
    piv["4L_mean"] = piv.mean(axis=1)
    print(piv.round(4).sort_values("4L_mean").to_string())

    print("\n=== per-step MSE (7-var z), L=24, mean over seeds ===")
    sub = dfs[(dfs.L == 24) & (dfs.step != "full")]
    print(sub.pivot_table(index="model", columns="weeks_ahead",
                          values="mse_z_7var", aggfunc="mean").round(4).to_string())

    print("\n=== denormalized MSE: % WEIGHTED ILI (physical %, x1e-4) L=24 ===")
    d24 = dfv[(dfv.L == 24) & (dfv.var_index == VAR_WILI)]
    t = d24.groupby("model")[["mse_z", "mse_physical", "mae_physical"]].mean()
    t["mse_physical_x1e4"] = (t["mse_physical"] * 1e4).round(2)
    print(t.round(4).to_string())

    print("\n=== PTE/PIE, % WEIGHTED ILI series, L=24, median over seeds ===")
    g = grp[(grp.series == "%WEIGHTED_ILI") & (grp.L == 24)]
    print(g[["side", "weeks_ahead", "n_models", "n_cells", "n_pass",
             "pass_rate_pct", "median_PTE", "median_PIE"]].to_string(index=False))
    print("\nfiles:")
    for n in ("DENORMALIZED_MSE_MAE_BY_VARIABLE.csv", "PER_STEP_MSE_BY_MODEL.csv",
              "PER_STEP_PTE_PIE_BY_MODEL.csv", "PER_STEP_PTE_PIE_PER_SEASON.csv",
              "PTE_PIE_GROUP_SUMMARY.csv"):
        print("  paper_tables/" + n)


def _agg_series(cell, step):
    """7-variable aggregate de-normalized to x training mean (unitless)."""
    gt = np.zeros(cell["tsr"].shape[0])
    pr = np.zeros(cell["tsr"].shape[0])
    for j in range(7):
        gt += cell["target"][:, j, step] / cell["mean"][j]
        pr += cell["pred"][:, j, step] / cell["mean"][j]
    return gt / 7.0, pr / 7.0


def make_figures(cells, seed):
    models = [m for m in MODELS if any(k[0] == m and k[2] == seed for k in cells)]
    for model in models:
        for L in sorted({k[1] for k in cells if k[0] == model and k[2] == seed}):
            c = cells.get((model, L, seed))
            if c is None:
                continue
            for kind in ("agg", "wili"):
                fig, axes = plt.subplots(2, 2, figsize=(15, 9))
                axes = axes.flatten()
                for step in STEPS:
                    if step >= L:
                        continue
                    ax = axes[step]
                    weeks, gt, pr = aligned_series(c, step, VAR_WILI)
                    if kind == "agg":
                        gt, pr = _agg_series(c, step)
                        ylab = "7-var aggregate (de-normalized, x train mean)"
                    else:
                        j = VAR_WILI
                        gt = c["target"][:, j, step] * c["std"][j] + c["mean"][j]
                        pr = c["pred"][:, j, step] * c["std"][j] + c["mean"][j]
                        ylab = "% WEIGHTED ILI (de-normalized)"

                    ax.plot(weeks, gt, color="#1f77b4", lw=1.6, label="Ground truth")
                    ax.plot(weeks, pr, color="#d62728", lw=1.6, ls="--", label="Prediction")

                    r = seasonal_pte_pie(weeks, gt, pr)
                    if r:
                        for sv in r["seasons"]:
                            ax.plot(sv["gt_peak_week"], sv["gt_peak_val"], "o", ms=9, mfc="none",
                                    mec="#1f77b4", mew=1.6, zorder=5)
                            ax.plot(sv["pred_peak_week"], sv["pred_peak_val"], "s", ms=8, mfc="none",
                                    mec="#d62728", mew=1.6, zorder=5)
                        ttl = (f"step {step} = {step+1} week{'s' if step else ''} ahead   "
                               f"PTE={r['PTE_wk']:.1f}wk  PIE={r['PIE_pct']:.1f}%  "
                               f"[{'PASS' if r['PTE_wk']<=1 and r['PIE_pct']<=25 else 'FAIL'}]"
                               f"  ({r['n_seasons']} seasons)")
                    else:
                        ttl = f"step {step} = {step+1} week ahead (no peak)"
                    ax.set_title(ttl, fontsize=9.5, fontweight="bold")
                    ax.set_xlabel("test week index (data row)", fontsize=9)
                    ax.set_ylabel(ylab, fontsize=9)
                    ax.legend(loc="upper left", fontsize=8)
                    ax.grid(alpha=0.3)
                for k in range(len(STEPS), 4):
                    axes[k].axis("off")
                fig.suptitle(f"{model}  L={L}  seed={seed}   |   "
                             f"Kramer & Shaman (2019): PTE<=1 week and PIE<=25%",
                             fontsize=12, fontweight="bold")
                plt.tight_layout()
                tag = "agg_" if kind == "agg" else "wili_"
                out = os.path.join(OUT_FIGS, f"stepwise_{tag}{model}_L{L}_s{seed}.png")
                plt.savefig(out, dpi=120, bbox_inches="tight")
                plt.close()
    print(f"  figures -> {OUT_FIGS}")


if __name__ == "__main__":
    main()
