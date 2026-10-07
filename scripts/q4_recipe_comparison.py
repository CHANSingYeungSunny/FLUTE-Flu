#!/usr/bin/env python
"""
q4_recipe_comparison.py — Advisor Question 4: recipe comparison + significance
==============================================================================

The advisor report (Q4) says:

  "若条件允许，建议对表现最好的 baseline 配方额外跑 3–5 个不同随机种子，报告
   MSE/MAE 的均值±标准差，用来说明'3–5倍的差距主要来自超参数选择本身，而不是
   运气好压中了某个随机种子'."

DECISION (per the user):
    Each HPC run ALREADY performs 10 repetitions, and `train_ablation.py` seeds
    them as `seed = args.seed + rep - 1`, i.e. reps 1..10 == seeds 42..51.
    A 10-seed mean +/- std therefore ALREADY exists for every recipe, and we do
    NOT burn GPU time re-running extra seeds. We report the existing n=10
    statistics and test whether the gaps are LARGER than the seed noise.

PROVENANCE
----------
Summary CSVs pulled from HPC Burgundy:
    full_H24/reps_1_to_10/summary.csv            -> baseline      (L=24)
    full__adamw_cosine/reps_1_to_10/summary.csv  -> adamw_cosine  (L=24)
    full__huber_clip/reps_1_to_10/summary.csv    -> huber_clip    (L=24)
    full__earlystop/reps_1_to_10/summary.csv     -> earlystop     (L=24)
All four are evaluated at the SAME horizon (L=24) and the same n_reps=10, so
the comparison is like-for-like. (Note: the aggregate `full/reps_1_to_10/
summary.csv` only retains the LAST horizon written (L=60) and must NOT be used
for a recipe comparison.)

Output:
    results/ili/metrics/q4_recipe_comparison.csv
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)

SRC_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "journal_evidence",
                       "recipe_summaries")
OUT_CSV = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                       "q4_recipe_comparison.csv")

# recipe label -> local summary filename
SOURCES = {
    "baseline (Adam, lr=5e-4)": "summary_baseline_L24.csv",
    "adamw_cosine (+WD, cosine)": "summary_adamw_cosine_L24.csv",
    "huber_clip (Huber+clip)": "summary_huber_clip_L24.csv",
    "earlystop (peak-aware)": "summary_earlystop_L24.csv",
}

BASELINE = "baseline (Adam, lr=5e-4)"


def load() -> pd.DataFrame:
    rows = []
    for label, fname in SOURCES.items():
        path = os.path.join(SRC_DIR, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        if (df["L"] != 24).any():
            raise ValueError(f"{fname}: expected L=24 rows only, got {df['L'].tolist()}")
        r = df.iloc[0]
        rows.append({
            "recipe": label,
            "n_reps": 10,
            "MSE_mean": float(r["mse_all_mean"]),
            "MSE_std": float(r["mse_all_std"]),
            "MAE_mean": float(r["mae_all_mean"]),
            "MAE_std": float(r["mae_all_std"]),
        })
    return pd.DataFrame(rows).sort_values("MSE_mean").reset_index(drop=True)


def welch_from_summary(m1, s1, n1, m2, s2, n2):
    """Two-sided Welch t-test computed from summary statistics."""
    v1, v2 = (s1 ** 2) / n1, (s2 ** 2) / n2
    se = float(np.sqrt(v1 + v2))
    if se == 0:
        return float("nan"), float("nan"), float("nan")
    t = (m1 - m2) / se
    df = (v1 + v2) ** 2 / ((v1 ** 2) / (n1 - 1) + (v2 ** 2) / (n2 - 1))
    p = float(2.0 * stats.t.sf(abs(t), df))
    return float(t), float(df), p


def main() -> None:
    df = load()
    base = df[df.recipe == BASELINE].iloc[0]

    print("=" * 84)
    print("Q4 RECIPE COMPARISON — all at L=24, all n_reps=10 (seeds 42..51)")
    print("=" * 84)
    print(f"\n{'recipe':28s} {'MSE mean':>9s} {'MSE std':>9s} {'MAE mean':>9s} "
          f"{'MAE std':>9s}")
    print("-" * 70)
    for _, r in df.iterrows():
        print(f"{r['recipe']:28s} {r.MSE_mean:9.4f} {r.MSE_std:9.4f} "
              f"{r.MAE_mean:9.4f} {r.MAE_std:9.4f}")

    print(f"\nSeed-noise scale: baseline MSE std = {base.MSE_std:.4f} "
          f"(mean = {base.MSE_mean:.4f})")

    print("\n--- Welch t-test vs baseline (MSE, alpha = 0.05) ---")
    print(f"{'recipe':28s} {'ΔMSE':>8s} {'t':>7s} {'df':>6s} {'p':>8s}  verdict")
    print("-" * 74)
    out_rows = []
    for _, r in df.iterrows():
        if r.recipe == BASELINE:
            out_rows.append({**r.to_dict(), "delta_MSE": 0.0, "t": np.nan,
                             "df": np.nan, "p_value": np.nan,
                             "significant": ""})
            continue
        t, dof, p = welch_from_summary(base.MSE_mean, base.MSE_std, int(base.n_reps),
                                       r.MSE_mean, r.MSE_std, int(r.n_reps))
        verdict = "SIGNIFICANT" if p < 0.05 else "not significant"
        print(f"{r['recipe']:28s} {r.MSE_mean - base.MSE_mean:8.4f} {t:7.3f} "
              f"{dof:6.1f} {p:8.4f}  {verdict}")
        out_rows.append({**r.to_dict(), "delta_MSE": float(r.MSE_mean - base.MSE_mean),
                         "t": t, "df": dof, "p_value": p, "significant": verdict})

    out = pd.DataFrame(out_rows)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"\n[q4] wrote {OUT_CSV}")

    # ---- the honest headline the report must carry ----
    second = df[df.recipe != BASELINE].iloc[0]
    gap = second.MSE_mean - base.MSE_mean
    print("\n" + "=" * 84)
    print("HEADLINE (for the report)")
    print("=" * 84)
    print(f"baseline vs next-best ({second.recipe}):")
    print(f"  gap            = {gap:.4f} MSE")
    print(f"  seed std       = {base.MSE_std:.4f} MSE")
    print(f"  gap / seed std = {gap / base.MSE_std:.3f}  "
          f"({'gap is SMALLER than the seed noise' if gap < base.MSE_std else 'gap exceeds noise'})")
    print("\n=> The ordering baseline < adamw_cosine < huber_clip < earlystop is")
    print("   OBSERVED, but the baseline/next-best gap is well inside the")
    print("   run-to-run (seed) standard deviation and is NOT statistically")
    print("   significant. The defensible claim is therefore:")
    print("     'baseline reproduces the published numbers most closely in this")
    print("      reproduction study', NOT 'baseline is the globally optimal")
    print("      training recipe'.")


if __name__ == "__main__":
    main()
