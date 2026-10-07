#!/usr/bin/env python3
"""analyze_wave1_secondary.py — baselines, ablations, controls, resource/storage.

Reads the aggregated JSONL and produces secondary analyses for the Wave-1
supervisor report:
  - deterministic baselines vs the primary field (per horizon)
  - the six gpt2_miflu ablations vs parent (mechanism evidence)
  - the 12 executed negative controls (zero_text / shuffled_text) vs parent
  - runtime / parameter / compact-storage trade-off per model

Never touches Test/holdout; never runs deferred controls.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
ANALYSIS.mkdir(parents=True, exist_ok=True)

NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
ABLATIONS = ["without_dataset_information", "without_task_instruction",
             "without_input_variable_description", "without_lora",
             "without_multimodality", "without_lora_and_multimodality"]
PARENT = "gpt2_miflu"


def load() -> pd.DataFrame:
    rows = []
    with (ANALYSIS / "wave1_analysis_dataset.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def seed_4l_mean(df: pd.DataFrame, model: str) -> np.ndarray:
    g = df[df["model"] == model]
    return g.groupby("seed")["mse_all_7vars_full_horizon_z"].mean().to_numpy(dtype=float)


def main() -> None:
    df = load()
    prim = df[df["arm"] == "primary"]

    # ── baselines vs primary (per horizon) ────────────────────────────────
    base_rows = []
    for (model, hor), g in df[df["arm"] == "baseline"].groupby(["model", "horizon"]):
        base_rows.append({
            "model": model, "horizon": int(hor),
            "mse_z": float(g["mse_all_7vars_full_horizon_z"].iloc[0]),
            "mae_z": float(g["mae_all_7vars_full_horizon_z"].iloc[0]),
        })
    baseline = pd.DataFrame(base_rows)
    # best primary model per horizon for comparison
    prim_best = (prim.groupby(["horizon"])["mse_all_7vars_full_horizon_z"]
                 .mean().reset_index().rename(columns={"mse_all_7vars_full_horizon_z": "best_primary_mse"}))
    # actually compute per-model-horizon mean then min
    prim_mh = (prim.groupby(["model", "horizon"])["mse_all_7vars_full_horizon_z"]
               .mean().reset_index())
    prim_best = (prim_mh.loc[prim_mh.groupby("horizon")["mse_all_7vars_full_horizon_z"].idxmin()]
                 [["horizon", "model", "mse_all_7vars_full_horizon_z"]]
                 .rename(columns={"model": "best_primary_model",
                                  "mse_all_7vars_full_horizon_z": "best_primary_mse"}))
    baseline = baseline.merge(prim_best, on="horizon", how="left")
    baseline["baseline_minus_best_primary"] = baseline["mse_z"] - baseline["best_primary_mse"]
    baseline.to_csv(ANALYSIS / "baseline_comparison.csv", index=False)

    # ── ablations vs parent ───────────────────────────────────────────────
    parent_4l = seed_4l_mean(prim, PARENT)
    ablation_rows = []
    for ab in ABLATIONS:
        g = df[df["model"] == ab]
        vals = seed_4l_mean(df, ab)
        lo, hi = (None, None)
        if len(vals) >= 2:
            se = np.std(vals, ddof=1) / np.sqrt(len(vals))
            tcrit = stats.t.ppf(0.975, df=len(vals) - 1)
            lo, hi = np.mean(vals) - tcrit * se, np.mean(vals) + tcrit * se
        # paired vs parent (matched seed)
        p = g.groupby("seed")["mse_all_7vars_full_horizon_z"].mean()
        pp = prim[prim["model"] == PARENT].groupby("seed")["mse_all_7vars_full_horizon_z"].mean()
        common = p.index.intersection(pp.index)
        a = p.loc[common].to_numpy(dtype=float)
        b = pp.loc[common].to_numpy(dtype=float)
        t = stats.ttest_rel(a, b)
        ablation_rows.append({
            "ablation": ab,
            "ablation_avg_MSE_4L": float(np.mean(vals)),
            "parent_avg_MSE_4L": float(np.mean(parent_4l)),
            "delta_vs_parent": float(np.mean(vals) - np.mean(parent_4l)),
            "rel_delta_pct": float((np.mean(vals) - np.mean(parent_4l)) / np.mean(parent_4l) * 100),
            "ci95_lo": lo, "ci95_hi": hi,
            "paired_t_vs_parent": float(t.statistic),
            "p_value_vs_parent": float(t.pvalue),
            "n_seeds": int(len(vals)),
        })
    ablation = pd.DataFrame(ablation_rows).sort_values("delta_vs_parent")
    ablation.to_csv(ANALYSIS / "ablation_effects.csv", index=False)

    # per-horizon ablation mean (for tables)
    ab_mh = (df[df["model"].isin(ABLATIONS)].groupby(["model", "horizon"])
             ["mse_all_7vars_full_horizon_z"].mean().reset_index())
    par_mh = (prim[prim["model"] == PARENT].groupby("horizon")
              ["mse_all_7vars_full_horizon_z"].mean().reset_index()
              .rename(columns={"mse_all_7vars_full_horizon_z": "parent_mse"}))
    ab_mh = ab_mh.merge(par_mh, on="horizon", how="left")
    ab_mh["delta"] = ab_mh["mse_all_7vars_full_horizon_z"] - ab_mh["parent_mse"]
    ab_mh.to_csv(ANALYSIS / "ablation_per_horizon.csv", index=False)

    # ── negative controls vs parent (matched L & seed) ────────────────────
    ctrl = df[df["arm"] == "negative_control"].copy()
    ctrl_rows = []
    for _, r in ctrl.iterrows():
        hor, seed = r["horizon"], r["seed"]
        p = prim[(prim["model"] == PARENT) & (prim["horizon"] == hor)
                 & (prim["seed"] == seed)]["mse_all_7vars_full_horizon_z"]
        if len(p) == 0:
            continue
        ctrl_rows.append({
            "control": r["model"], "horizon": int(hor), "seed": int(seed),
            "control_mse": float(r["mse_all_7vars_full_horizon_z"]),
            "parent_mse": float(p.iloc[0]),
            "delta": float(r["mse_all_7vars_full_horizon_z"] - p.iloc[0]),
        })
    ctrl_df = pd.DataFrame(ctrl_rows)
    ctrl_df.to_csv(ANALYSIS / "control_effects.csv", index=False)
    ctrl_agg = (ctrl_df.groupby("control")
                .agg(n=("delta", "count"),
                     mean_delta=("delta", "mean"),
                     mean_control_mse=("control_mse", "mean"),
                     mean_parent_mse=("parent_mse", "mean"))
                .reset_index())
    ctrl_agg.to_csv(ANALYSIS / "control_effects_summary.csv", index=False)

    # ── resource / storage trade-off ──────────────────────────────────────
    res_rows = []
    for model in NON_LLM + LLM:
        g = prim[prim["model"] == model]
        res_rows.append({
            "model": model,
            "family": "non_llm" if model in NON_LLM else "llm",
            "train_seconds_mean": float(g["train_seconds"].mean()),
            "trainable_parameters": int(g["trainable_parameters"].iloc[0]),
            "compact_bytes": int(g["compact_bytes"].iloc[0]),
            "best_epoch_mean": float(g["best_epoch"].mean()),
        })
    resource = pd.DataFrame(res_rows)
    # baselines have no checkpoint
    for model in ["last_value_naive", "seasonal_naive"]:
        g = df[df["model"] == model]
        resource = pd.concat([resource, pd.DataFrame([{
            "model": model, "family": "baseline",
            "train_seconds_mean": 0.0, "trainable_parameters": 0,
            "compact_bytes": 0, "best_epoch_mean": None}])], ignore_index=True)
    resource = resource.sort_values("compact_bytes")
    resource.to_csv(ANALYSIS / "resource_storage.csv", index=False)

    # ── console ───────────────────────────────────────────────────────────
    print("=== BASELINES ===")
    print(baseline.to_string(index=False))
    print("\n=== ABLATIONS (avg MSE 4L, vs parent gpt2_miflu) ===")
    print(ablation[["ablation", "ablation_avg_MSE_4L", "delta_vs_parent",
                    "rel_delta_pct", "p_value_vs_parent"]].to_string(index=False))
    print("\n=== CONTROLS summary ===")
    print(ctrl_agg.to_string(index=False))
    print("\n=== RESOURCE/STORAGE ===")
    print(resource.to_string(index=False))


if __name__ == "__main__":
    main()
