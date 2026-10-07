#!/usr/bin/env python3
"""analyze_wave1.py — apply the frozen selection rule to Wave-1 durable evidence.

Reads the aggregated JSONL dataset and the frozen selection rule, then computes
descriptive statistics, per-model ranking, Non-LLM / LLM / overall winners, and
matched-seed statistical comparisons. Never touches Test/holdout, never mutates
the selection rule, never runs deferred controls.

Outputs (under results/v3_clean/analysis/):
  analysis_dataset.csv
  primary_seed_level.csv          (320 rows: model x horizon x seed)
  primary_summary_statistics.csv  (model x horizon: n/mean/SD/median/min/max/CI)
  model_ranking.csv               (8 models: average_MSE_4L/MAE_4L, rank, family)
  selection_outcome.json
  paired_comparisons.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
PREREG = ROOT / "results" / "v3_clean" / "preregistration"
ANALYSIS.mkdir(parents=True, exist_ok=True)

NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
HORIZONS = [24, 36, 48, 60]
SEEDS = list(range(42, 52))


def load_dataset() -> pd.DataFrame:
    rows = []
    with (ANALYSIS / "wave1_analysis_dataset.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def t_ci(values: np.ndarray, conf: float = 0.95):
    n = len(values)
    if n < 2:
        return (None, None)
    m = float(np.mean(values))
    sd = float(np.std(values, ddof=1))
    se = sd / np.sqrt(n)
    tcrit = stats.t.ppf(1 - (1 - conf) / 2, df=n - 1)
    return m - tcrit * se, m + tcrit * se


def main() -> None:
    df = load_dataset()
    rule = json.loads((PREREG / "paper_aligned_selection_rule.json").read_text())
    endpoint = json.loads((PREREG / "endpoint_hierarchy.json").read_text())

    # ── full dataset flat CSV ─────────────────────────────────────────────
    df.to_csv(ANALYSIS / "analysis_dataset.csv", index=False)

    # ── primary-only seed level ───────────────────────────────────────────
    prim = df[(df["arm"] == "primary")].copy()
    prim["family"] = prim["model"].apply(
        lambda m: "non_llm" if m in NON_LLM else ("llm" if m in LLM else "other"))
    prim = prim[prim["family"].isin(["non_llm", "llm"])]
    seed_cols = ["model", "family", "horizon", "seed",
                 "mse_all_7vars_full_horizon_z", "mae_all_7vars_full_horizon_z"]
    seed_df = prim[seed_cols].copy()
    seed_df.to_csv(ANALYSIS / "primary_seed_level.csv", index=False)

    # ── per model x horizon descriptive statistics ────────────────────────
    summary_rows = []
    for (model, hor), g in prim.groupby(["model", "horizon"]):
        mse = g["mse_all_7vars_full_horizon_z"].to_numpy(dtype=float)
        mae = g["mae_all_7vars_full_horizon_z"].to_numpy(dtype=float)
        lo_m, hi_m = t_ci(mse)
        lo_a, hi_a = t_ci(mae)
        fam = "non_llm" if model in NON_LLM else "llm"
        summary_rows.append({
            "model": model, "family": fam, "horizon": int(hor),
            "n": int(len(mse)),
            "mse_mean": float(np.mean(mse)),
            "mse_sd": float(np.std(mse, ddof=1)),
            "mse_median": float(np.median(mse)),
            "mse_min": float(np.min(mse)),
            "mse_max": float(np.max(mse)),
            "mse_ci95_lo": lo_m, "mse_ci95_hi": hi_m,
            "mae_mean": float(np.mean(mae)),
            "mae_sd": float(np.std(mae, ddof=1)),
            "mae_ci95_lo": lo_a, "mae_ci95_hi": hi_a,
        })
    summary = pd.DataFrame(summary_rows).sort_values(["horizon", "mse_mean"])
    summary.to_csv(ANALYSIS / "primary_summary_statistics.csv", index=False)

    # ── per-model average_MSE_4L / average_MAE_4L ─────────────────────────
    # seed-level average over L, then mean over seeds (equivalent to L-mean of
    # seed-mean, because arithmetic means commute).
    ranking_rows = []
    for model in NON_LLM + LLM:
        g = prim[prim["model"] == model]
        # seed-level average_MSE_4L (10 values, one per seed)
        seed_mse = g.groupby("seed")["mse_all_7vars_full_horizon_z"].mean()
        seed_mae = g.groupby("seed")["mae_all_7vars_full_horizon_z"].mean()
        mse_vals = seed_mse.to_numpy(dtype=float)
        mae_vals = seed_mae.to_numpy(dtype=float)
        lo_m, hi_m = t_ci(mse_vals)
        lo_a, hi_a = t_ci(mae_vals)
        fam = "non_llm" if model in NON_LLM else "llm"
        ranking_rows.append({
            "model": model, "family": fam,
            "average_MSE_4L": float(np.mean(mse_vals)),
            "MSE_4L_sd": float(np.std(mse_vals, ddof=1)),
            "MSE_4L_ci95_lo": lo_m, "MSE_4L_ci95_hi": hi_m,
            "average_MAE_4L": float(np.mean(mae_vals)),
            "MAE_4L_sd": float(np.std(mae_vals, ddof=1)),
            "MAE_4L_ci95_lo": lo_a, "MAE_4L_ci95_hi": hi_a,
            "n_seeds": int(len(mse_vals)),
        })
    ranking = pd.DataFrame(ranking_rows).sort_values("average_MSE_4L")
    ranking["rank_MSE"] = range(1, len(ranking) + 1)
    ranking_mae = ranking.sort_values("average_MAE_4L")
    ranking["rank_MAE"] = pd.Series(
        range(1, len(ranking_mae) + 1),
        index=ranking_mae.index)
    ranking.to_csv(ANALYSIS / "model_ranking.csv", index=False)

    # ── winners ───────────────────────────────────────────────────────────
    nonllm = ranking[ranking["family"] == "non_llm"].sort_values("average_MSE_4L")
    llm = ranking[ranking["family"] == "llm"].sort_values("average_MSE_4L")
    overall = ranking.sort_values("average_MSE_4L")

    best_nonllm = nonllm.iloc[0]["model"]
    best_llm = llm.iloc[0]["model"]
    best_overall = overall.iloc[0]["model"]
    runner_overall = overall.iloc[1]["model"]

    # ── matched-seed paired comparisons ───────────────────────────────────
    # seed-level average_MSE_4L per model (10 seeds each), matched on seed.
    def seed_mse_4l(model):
        g = prim[prim["model"] == model]
        return g.groupby("seed")["mse_all_7vars_full_horizon_z"].mean()

    # (a) overall winner vs runner-up (matched seed, n=10)
    a = seed_mse_4l(best_overall).sort_index().to_numpy(dtype=float)
    b = seed_mse_4l(runner_overall).sort_index().to_numpy(dtype=float)
    t_wr = stats.ttest_rel(a, b)
    d_wr = float((np.mean(a) - np.mean(b)) / np.sqrt(
        (np.var(a, ddof=1) + np.var(b, ddof=1)) / 2))
    winner_vs_runner = {
        "winner": best_overall, "runner_up": runner_overall,
        "winner_mean": float(np.mean(a)), "runner_mean": float(np.mean(b)),
        "mean_diff": float(np.mean(a) - np.mean(b)),
        "paired_t": float(t_wr.statistic), "p_value": float(t_wr.pvalue),
        "cohens_d": d_wr, "n_pairs": int(len(a)),
        "note": "paired t-test on matched-seed average_MSE_4L (10 seeds)",
    }

    # (b) Non-LLM group vs LLM group (matched seed, n=10)
    def group_seed_mean(models):
        vals = np.zeros(len(SEEDS))
        for s in SEEDS:
            per = [seed_mse_4l(m).loc[s] for m in models]
            vals[SEEDS.index(s)] = float(np.mean(per))
        return vals

    nonllm_vals = group_seed_mean(NON_LLM)
    llm_vals = group_seed_mean(LLM)
    t_grp = stats.ttest_rel(nonllm_vals, llm_vals)
    pooled = np.sqrt((np.var(nonllm_vals, ddof=1) + np.var(llm_vals, ddof=1)) / 2)
    d_grp = float((np.mean(nonllm_vals) - np.mean(llm_vals)) / pooled)
    group_compare = {
        "non_llm_group_mean": float(np.mean(nonllm_vals)),
        "llm_group_mean": float(np.mean(llm_vals)),
        "mean_diff_nonllm_minus_llm": float(np.mean(nonllm_vals) - np.mean(llm_vals)),
        "paired_t": float(t_grp.statistic), "p_value": float(t_grp.pvalue),
        "cohens_d": d_grp, "n_pairs": int(len(nonllm_vals)),
        "note": "matched-seed paired t-test: per-seed mean of 4 models' "
                "average_MSE_4L, Non-LLM vs LLM (10 seeds)",
    }

    # per-horizon group comparison (40 pairs: seed x horizon)
    per_horizon_group = {}
    for hor in HORIZONS:
        sub = prim[prim["horizon"] == hor]
        def mse_at(model):
            return sub[sub["model"] == model]["mse_all_7vars_full_horizon_z"].to_numpy(dtype=float)
        nv = np.zeros(len(SEEDS)); lv = np.zeros(len(SEEDS))
        for s in SEEDS:
            nv[SEEDS.index(s)] = float(np.mean(
                [sub[(sub["model"] == m) & (sub["seed"] == s)]["mse_all_7vars_full_horizon_z"].mean() for m in NON_LLM]))
            lv[SEEDS.index(s)] = float(np.mean(
                [sub[(sub["model"] == m) & (sub["seed"] == s)]["mse_all_7vars_full_horizon_z"].mean() for m in LLM]))
        tt = stats.ttest_rel(nv, lv)
        per_horizon_group[str(hor)] = {
            "non_llm_mean": float(np.mean(nv)), "llm_mean": float(np.mean(lv)),
            "mean_diff": float(np.mean(nv) - np.mean(lv)),
            "paired_t": float(tt.statistic), "p_value": float(tt.pvalue),
        }

    # ── per-horizon per-model ranking (stability check) ───────────────────
    per_horizon_ranking = {}
    for hor in HORIZONS:
        sub = summary[summary["horizon"] == hor].sort_values("mse_mean")
        per_horizon_ranking[str(hor)] = {
            "best_model": sub.iloc[0]["model"],
            "best_mse": float(sub.iloc[0]["mse_mean"]),
            "best_family": sub.iloc[0]["family"],
            "order": sub["model"].tolist(),
        }

    # ── ILITOTAL full-horizon per-model ranking (endpoint stability) ──────
    ilitotal_rows = []
    for model in NON_LLM + LLM:
        g = prim[prim["model"] == model]
        seed_ili = g.groupby("seed")["ilitotal_full_mse_z"].mean()
        ilitotal_rows.append({
            "model": model,
            "family": "non_llm" if model in NON_LLM else "llm",
            "ilitotal_full_mse_z_4L_mean": float(np.mean(seed_ili)),
        })
    ilitotal_rank = pd.DataFrame(ilitotal_rows).sort_values("ilitotal_full_mse_z_4L_mean")
    ilitotal_rank.to_csv(ANALYSIS / "ilitotal_ranking.csv", index=False)

    # ── equivalence set ───────────────────────────────────────────────────
    # If winner vs runner-up indistinguishable (p > 0.05), report equivalence set.
    equivalence = []
    if winner_vs_runner["p_value"] > 0.05:
        equivalence = [best_overall, runner_overall]

    outcome = {
        "selection_rule_source": "results/v3_clean/preregistration/paper_aligned_selection_rule.json",
        "ranking_metric": rule["ranking_metric"],
        "lower_is_better": rule["lower_is_better"],
        "tie_break_order": rule["tie_break_order"],
        "forbidden": rule["forbidden"],
        "family_membership": {"non_llm": NON_LLM, "llm": LLM},
        "best_non_llm": best_nonllm,
        "best_llm": best_llm,
        "best_overall": best_overall,
        "runner_up_overall": runner_overall,
        "top_equivalence_set": equivalence,
        "winner_vs_runner": winner_vs_runner,
        "non_llm_vs_llm_group": group_compare,
        "per_horizon_group_compare": per_horizon_group,
        "per_horizon_ranking": per_horizon_ranking,
        "note_pte_pie_unavailable": "PTE/PIE are null in Wave-1 durable evidence "
            "because validation_predictions.csv stores target_date=None, so the "
            "seasonal peak detector cannot aggregate per target week. Reported "
            "explicitly, not silently imputed.",
    }
    (ANALYSIS / "selection_outcome.json").write_text(
        json.dumps(outcome, indent=2), encoding="utf-8")

    (ANALYSIS / "paired_comparisons.json").write_text(
        json.dumps({
            "winner_vs_runner": winner_vs_runner,
            "non_llm_vs_llm_group": group_compare,
            "per_horizon_group_compare": per_horizon_group,
        }, indent=2), encoding="utf-8")

    # ── console summary ───────────────────────────────────────────────────
    print("=== MODEL RANKING (average_MSE_4L, lower better) ===")
    print(ranking[["model", "family", "average_MSE_4L", "average_MAE_4L",
                   "rank_MSE"]].to_string(index=False))
    print("\nbest_non_llm =", best_nonllm)
    print("best_llm     =", best_llm)
    print("best_overall =", best_overall)
    print("runner_up    =", runner_overall)
    print("\nwinner vs runner:", json.dumps(winner_vs_runner, indent=2))
    print("\nnon_llm vs llm group:", json.dumps(group_compare, indent=2))
    print("\nper-horizon group:", json.dumps(per_horizon_group, indent=2))
    print("\nper-horizon ranking:", json.dumps(per_horizon_ranking, indent=2))
    print("\ntop_equivalence_set =", equivalence)


if __name__ == "__main__":
    main()
