"""Stage 5 A2 — build the supplementary reporting tables from the locked score matrix.

Reads only hpc_results/stage5_a2/scoring/score_matrix.csv (which the independent
recompute step already proved identical to the raw prediction artefacts) and emits
the per-L/seed, per-variable, original-unit and paired-by-seed tables used by the
Chinese report. No model code, no GPU.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = os.path.join("hpc_results", "stage5_a2", "scoring")
OUT = os.path.join("recovery", "stage5")
LEARNED = ["miflu", "notext", "nlinear"]
BASE = ["last_value_naive", "seasonal_naive"]
SHORT = {"mse_pct_WEIGHTED_ILI": "mse_WILI", "mae_pct_WEIGHTED_ILI": "mae_WILI",
         "mse_pct_UNWEIGHTED_ILI": "mse_UILI", "mae_pct_UNWEIGHTED_ILI": "mae_UILI",
         "mse_AGE_0_4": "mse_A04", "mae_AGE_0_4": "mae_A04",
         "mse_AGE_5_24": "mse_A524", "mae_AGE_5_24": "mae_A524",
         "mse_ILITOTAL": "mse_ILIT", "mae_ILITOTAL": "mae_ILIT",
         "mse_NUM_OF_PROVIDERS": "mse_PROV", "mae_NUM_OF_PROVIDERS": "mae_PROV",
         "mse_OT": "mse_OT", "mae_OT": "mae_OT"}

d = pd.read_csv(os.path.join(ROOT, "score_matrix.csv"))
lock = pd.read_csv(os.path.join(ROOT, "CHECKPOINT_LOCK.csv"))
lines = []


def emit(s=""):
    print(s)
    lines.append(s)


emit("### T1  per (model, L): 7-var z-space MSE / MAE (mean +- sd over seeds 42,43,44)")
emit()
emit("| model | L | MSE mean | MSE sd | MAE mean | ILITOTAL MSE | ILITOTAL MAE | ILITOTAL PCC |")
emit("|---|---:|---:|---:|---:|---:|---:|---:|")
for m in LEARNED + BASE:
    for L in (24, 36, 48, 60):
        s = d[(d.model == m) & (d.L == L)]
        if not len(s):
            continue
        sd = f"{s.mse_all.std(ddof=1):.4f}" if len(s) > 1 else "—"
        emit(f"| {m} | {L} | {s.mse_all.mean():.4f} | {sd} | {s.mae_all.mean():.4f} | "
             f"{s.mse_ili.mean():.4f} | {s.mae_ili.mean():.4f} | {s.pcc_ili.mean():.4f} |")

emit()
emit("### T2  per (model, L, seed) 7-var z-space MSE, next to the validation value that chose the checkpoint")
emit()
emit("| model | L | seed | best val MSE (selection) | best epoch | Test MSE (7-var z) |")
emit("|---|---:|---:|---:|---:|---:|")
for _, r in lock.iterrows():
    t = d[(d.model == r.model) & (d.L == r.L) & (d.seed == r.seed)]
    be = "—" if pd.isna(r.best_epoch) else int(r.best_epoch)
    emit(f"| {r.model} | {r.L} | {r.seed} | {r.best_val_mse_7var_z:.6f} | {be} | "
         f"{t.mse_all.iloc[0]:.6f} |")

emit()
emit("### T3  per-variable Test MSE, mean over seeds (standardized space)")
emit()
pv = [c for c in d.columns if c.startswith("mse_") and c not in ("mse_all", "mse_ili")]
emit("| model | " + " | ".join(SHORT.get(c, c[4:]) for c in pv) + " |")
emit("|---" * (len(pv) + 1) + "|")
for m in LEARNED + BASE:
    g = d[d.model == m][pv].mean()
    emit(f"| {m} | " + " | ".join(f"{g[c]:.4f}" for c in pv) + " |")

emit()
emit("### T4  per-variable Test MAE in ORIGINAL units, mean over seeds and horizons")
emit()
qv = [c for c in d.columns if c.startswith("mae_phys_")]
emit("| model | " + " | ".join(c[9:] for c in qv) + " |")
emit("|---" * (len(qv) + 1) + "|")
for m in LEARNED + BASE:
    g = d[d.model == m][qv].mean()
    emit(f"| {m} | " + " | ".join(f"{g[c]:.3f}" for c in qv) + " |")

emit()
emit("### T5  average_MSE_4L (primary): mean over seeds within L, then equal-weight mean over L")
emit()
per = d[d.model.isin(LEARNED + BASE)].groupby(["model", "L"]).mse_all.mean().reset_index()
avg = per.groupby("model").mse_all.mean()
sd4 = d[d.model.isin(LEARNED)].groupby(["model", "L"]).mse_all.std(ddof=1).reset_index()
sem = sd4.groupby("model").mse_all.mean() / 2.0
emit("| model | average_MSE_4L | avg MAE_4L | per-L SD of seed mean (avg over L) |")
emit("|---|---:|---:|---:|")
for m in LEARNED + BASE:
    mae4 = d[d.model == m].groupby("L").mae_all.mean().mean()
    s = f"{sem[m]:.4f}" if m in sem.index else "—"
    emit(f"| {m} | {avg[m]:.6f} | {mae4:.4f} | {s} |")

emit()
emit("### T6  paired-by-seed differences (optimisation randomness only, NOT time-generalisation uncertainty)")
emit()
emit("Paired on seed s at the same L, in 7-var z-space MSE. Positive = first model worse.")
emit()
w = d[d.model.isin(LEARNED)].pivot_table(index=["L", "seed"], columns="model", values="mse_all")
for a, b in (("miflu", "notext"), ("miflu", "nlinear"), ("notext", "nlinear")):
    diff = (w[a] - w[b])
    emit(f"**{a} - {b}**  mean {diff.mean():+.4f}  sd {diff.std(ddof=1):.4f}  "
         f"per-L mean: " + ", ".join(f"L{L}={diff.loc[L].mean():+.4f}" for L in (24, 36, 48, 60)))
    emit(f"  seeds all same sign: {'yes' if (diff > 0).all() or (diff < 0).all() else 'no'} "
         f"(wins for {a} over {b}: {int((diff > 0).sum())}/12 cells)")

emit()
emit("### T7  seed spread of the 7-var z-space Test MSE (optimisation randomness)")
emit()
for m in LEARNED:
    g = d[d.model == m].groupby("L").mse_all.agg(["mean", "std", "min", "max"]).round(4)
    emit(f"**{m}**")
    emit()
    emit("| L | mean | sd | min | max |")
    emit("|---:|---:|---:|---:|---:|")
    for L, r in g.iterrows():
        emit(f"| {L} | {r['mean']:.4f} | {r['std']:.4f} | {r['min']:.4f} | {r['max']:.4f} |")
    emit()

with open(os.path.join(OUT, "results_tables_zh.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n[written]", os.path.join(OUT, "results_tables_zh.md"))
