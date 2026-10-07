"""make_final_figures.py — final Test figures for the one-time evaluation.

OUTSIDE the frozen source hash. Read-only: it never touches per-cell artifacts
and never overwrites a prediction or metric file.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
FIG = TEV / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def _j(p):
    import json
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


man = _j(TEV / "test_evaluation_manifest.json")
champ = man.get("champion", "nlinear")
stats = _rows(INN / "final" / "final_statistics.csv")
peak = _rows(INN / "final" / "final_peak_results.csv")

models = sorted({r["model_key"] for r in stats})
horizons = sorted({int(r["horizon"]) for r in stats})
base = [m for m in models if m != champ]
COLORS = {champ: "#1f77b4"}
for i, b in enumerate(base):
    COLORS[b] = ["#d62728", "#ff7f0e", "#2ca02c"][i % 3]


def _get(m, L, metric, key):
    for r in stats:
        if r["model_key"] == m and int(r["horizon"]) == L and r["metric"] == metric:
            return float(r[key])
    return np.nan


# ── Fig 1: MSE / MAE by horizon with bootstrap 95% CI ───────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
x = np.arange(len(horizons))
w = 0.8 / max(1, len(models))
for ax, metric in zip(axes, ("MSE", "MAE")):
    for i, m in enumerate(models):
        means = [_get(m, L, metric, "mean") for L in horizons]
        lo = [_get(m, L, metric, "mean") - _get(m, L, metric, "ci95_lo") for L in horizons]
        hi = [_get(m, L, metric, "ci95_hi") - _get(m, L, metric, "mean") for L in horizons]
        ax.bar(x + (i - (len(models) - 1) / 2) * w, means, w, label=m,
               color=COLORS.get(m), yerr=[lo, hi], capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"L={L}" for L in horizons])
    ax.set_title(f"Test {metric} (physical ILI units)")
    ax.set_ylabel(metric)
    ax.grid(axis="y", alpha=0.3)
axes[0].legend()
fig.suptitle(f"One-time final Test — {TEV_ID}")
fig.tight_layout()
p1 = FIG / "fig_test_mse_mae_by_horizon.png"
fig.savefig(p1, dpi=150)
plt.close(fig)

# ── Fig 2: peak timing / intensity vs literature criterion ──────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (key, title) in zip(axes, (("mean_pte_weeks", "PTE (weeks)"),
                                   ("mean_pie_pct", "PIE (%)"))):
    for i, m in enumerate(models):
        vals = []
        for L in horizons:
            v = np.nan
            for r in peak:
                if r["model_key"] == m and int(r["horizon"]) == L:
                    v = float(r[key])
            vals.append(v)
        ax.bar(x + (i - (len(models) - 1) / 2) * w, vals, w, label=m, color=COLORS.get(m))
    if key == "mean_pte_weeks":
        ax.axhline(1.0, ls="--", c="k", lw=1, label="PTE <= 1 week")
    else:
        ax.axhline(25.0, ls="--", c="k", lw=1, label="PIE <= 25%")
    ax.set_xticks(x)
    ax.set_xticklabels([f"L={L}" for L in horizons])
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
fig.suptitle("Peak timing / intensity on Test vs literature criterion")
fig.tight_layout()
p2 = FIG / "fig_test_peak_pte_pie.png"
fig.savefig(p2, dpi=150)
plt.close(fig)

# ── Fig 3: prediction vs ground truth (champion vs baseline) ────────────────
made = []
for L in horizons:
    pc = TEV / "predictions" / f"champion__{champ}__L{L}__s42.csv"
    pb = TEV / "predictions" / (f"baseline__{base[0]}__L{L}__s42.csv" if base else "")
    if not (pc.exists() and base and pb.exists()):
        continue
    dc = list(csv.DictReader(open(pc, encoding="utf-8")))
    db = {r["week_start_date"]: r for r in csv.DictReader(open(pb, encoding="utf-8"))}
    dates = [r["week_start_date"] for r in dc if r["week_start_date"] in db]
    gt = [float(r["ground_truth_ili_phys"]) for r in dc if r["week_start_date"] in db]
    a = [float(r["prediction_ili_phys"]) for r in dc if r["week_start_date"] in db]
    b = [float(db[d]["prediction_ili_phys"]) for d in dates]
    # collapse per forecast step: keep first occurrence of each date (step 0)
    seen, xs, g, ya, yb = set(), [], [], [], []
    for d, g0, a0, b0 in zip(dates, gt, a, b):
        if d in seen:
            continue
        seen.add(d)
        xs.append(d)
        g.append(g0)
        ya.append(a0)
        yb.append(b0)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(xs, g, label="Ground truth", color="black", lw=1.4)
    ax.plot(xs, ya, label=f"{champ} (champion)", color=COLORS[champ], lw=1.2)
    ax.plot(xs, yb, label=f"{base[0]} (baseline)", color=COLORS[base[0]], lw=1.2)
    ax.set_title(f"Test predictions, L={L}, seed 42 (step 0)")
    ax.set_ylabel("ILI (physical units)")
    ax.legend()
    ax.grid(alpha=0.3)
    step = max(1, len(xs) // 12)
    ax.set_xticks(range(0, len(xs), step))
    ax.set_xticklabels([xs[i] for i in range(0, len(xs), step)], rotation=45, ha="right")
    fig.tight_layout()
    p = FIG / f"fig_test_predictions_L{L}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    made.append(p.name)

print("[figures] wrote %s" % ", ".join([p1.name, p2.name] + made))
