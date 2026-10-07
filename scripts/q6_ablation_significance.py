#!/usr/bin/env python
"""
q6_ablation_significance.py — is the TEXT modality statistically doing anything?
================================================================================

This is the decisive test for the claim that "MIFlu's multimodal attention is
fake / the gain is purely a LayerNorm shortcut".

The logic is simple and does NOT depend on any attention-weight measurement:

  * If the text modality were inert, REMOVING it would not change the error.
  * `no_multi` removes the textual input embedder entirely (text replaced by a
    single zero token). If MSE barely moves, text is decorative.
  * `no_text_ln` keeps text but removes the LayerNorm applied to it. This
    isolates the hypothesised "LayerNorm statistical shortcut".

Comparing the two against `full` decomposes the text contribution:
    total text contribution      = MSE(no_multi)   - MSE(full)
    LayerNorm-attributable share = MSE(no_text_ln) - MSE(full)
    residual (non-LN)            = difference of the two

Welch's t-test is computed from the reported per-rep mean/std (n = 10 seeds
each), exactly as in `q4_recipe_comparison.py`.

Output: results/ili/metrics/q6_ablation_significance.csv
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)

SRC = os.path.join(PROJECT_ROOT, "results", "ili", "journal_evidence",
                   "journal_table_viii_all_variants.csv")
OUT_CSV = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                       "q6_ablation_significance.csv")

BASELINE = "full"
# variant -> what is removed
ABLATIONS = {
    "no_multi": "textual input embedder removed (1 zero token)",
    "no_text_ln": "text kept, text-LayerNorm removed",
    "no_lora": "LoRA removed (text + LN intact)",
    "no_lora_multi": "LoRA + text removed (== GPT4TS setting)",
    "gated_inject": "ModalityAligner + unfreeze_first_k=2 (custom)",
}


def welch_from_summary(m1, s1, n1, m2, s2, n2):
    v1, v2 = (s1 ** 2) / n1, (s2 ** 2) / n2
    se = float(np.sqrt(v1 + v2))
    if se == 0:
        return float("nan"), float("nan"), float("nan")
    t = (m1 - m2) / se
    df = (v1 + v2) ** 2 / ((v1 ** 2) / (n1 - 1) + (v2 ** 2) / (n2 - 1))
    p = float(2.0 * stats.t.sf(abs(t), df))
    return float(t), float(df), p


def main() -> None:
    df = pd.read_csv(SRC).set_index("experiment")
    base = df.loc[BASELINE]

    print("=" * 84)
    print("Q6 ABLATION SIGNIFICANCE — does the TEXT modality matter?")
    print("=" * 84)
    print(f"\nbaseline `{BASELINE}`: MSE = {base.MSE_AllVars_mean:.4f} "
          f"+/- {base.MSE_AllVars_std:.4f}  (n = {int(base.n_reps)} seeds)\n")

    print(f"{'variant':16s} {'MSE':>8s} {'dMSE':>8s} {'t':>7s} {'df':>6s} "
          f"{'p':>8s}  {'verdict':16s} removed")
    print("-" * 96)
    rows = []
    for name, what in ABLATIONS.items():
        if name not in df.index:
            print(f"{name:16s}  (missing from the results table)")
            continue
        r = df.loc[name]
        t, dof, p = welch_from_summary(
            base.MSE_AllVars_mean, base.MSE_AllVars_std, int(base.n_reps),
            r.MSE_AllVars_mean, r.MSE_AllVars_std, int(r.n_reps))
        verdict = "SIGNIFICANT" if p < 0.05 else "not significant"
        d = float(r.MSE_AllVars_mean - base.MSE_AllVars_mean)
        print(f"{name:16s} {r.MSE_AllVars_mean:8.4f} {d:+8.4f} {t:7.3f} "
              f"{dof:6.1f} {p:8.4f}  {verdict:16s} {what}")
        rows.append({"variant": name, "removed": what,
                     "MSE": float(r.MSE_AllVars_mean),
                     "MSE_std": float(r.MSE_AllVars_std),
                     "delta_MSE": d, "t": t, "df": dof, "p_value": p,
                     "significant": verdict})

    out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"\n[q6] wrote {OUT_CSV}")

    # ---- decomposition of the text contribution --------------------------
    try:
        tot = float(df.loc["no_multi"].MSE_AllVars_mean
                    - base.MSE_AllVars_mean)
        ln = float(df.loc["no_text_ln"].MSE_AllVars_mean
                   - base.MSE_AllVars_mean)
        print("\n" + "=" * 84)
        print("DECOMPOSITION OF THE TEXT CONTRIBUTION (MSE units)")
        print("=" * 84)
        print(f"  removing ALL text      (no_multi)   : {tot:+.4f}")
        print(f"  removing only text-LN  (no_text_ln) : {ln:+.4f}")
        print(f"  residual (text effects NOT via LN)  : {tot - ln:+.4f}")
        if abs(tot) > 1e-9:
            print(f"  LayerNorm-attributable share        : "
                  f"{100.0 * ln / tot:.1f}% of the total text contribution")
        print("\n  => If the residual is large, text contributes through more")
        print("     than the LayerNorm, and the 'pure shortcut' claim fails.")
    except KeyError as e:
        print(f"[q6] decomposition skipped, missing variant: {e}")


if __name__ == "__main__":
    main()
