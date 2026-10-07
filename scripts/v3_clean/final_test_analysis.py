"""final_test_analysis.py — step 11 of the Final Freeze / one-time Test phase.

Computes the FINAL Test/Holdout metrics from the 84 downloaded test-eval result
directories, strictly following the frozen contracts:

  * primary endpoint  = mse_all_7vars_full_horizon_z (per-L seed-mean, then
    average_MSE_4L = arithmetic mean over L in {24,36,48,60});
  * secondary         = mae_all_7vars_full_horizon_z, ILITOTAL full-horizon
    MSE/MAE (z + physical), PTE/PIE + hit rates (peak-evaluation-v1);
  * confidence        = t-distribution 95% CI across 10 seeds (df=9);
  * confirmatory      = C1 gpt2_miflu vs nlinear (paired t, 10 seeds),
    C2 gpt2_miflu vs seasonal_naive and C3 nlinear vs seasonal_naive
    (one-sample t on the seed differences against the deterministic reference),
    Holm-Bonferroni across the three PRIMARY (average_MSE_4L) tests, alpha=0.05;
  * generalization    = Validation-to-Test gap (Test - Validation), per-L and
    average_MSE_4L.

No model is loaded, no inference is run, no frozen value is changed. This script
only aggregates the SAVED test predictions/metrics. Fail-stop on any missing or
malformed artifact.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

TEST_RESULTS = os.path.join(ROOT, "results", "v3_clean", "test_eval", "results")
TEST_EVAL_DIR = os.path.join(ROOT, "results", "v3_clean", "test_eval")
LEDGER = os.path.join(TEST_EVAL_DIR, "test_eval_ledger.jsonl")
AUDIT = os.path.join(TEST_EVAL_DIR, "terminal_test_audit.json")
FINAL = os.path.join(ROOT, "results", "v3_clean", "final")
os.makedirs(FINAL, exist_ok=True)

HORIZONS = (24, 36, 48, 60)
SEEDS = tuple(range(42, 52))
LEADS = (1, 2, 3, 4)
MODELS = ("gpt2_miflu", "nlinear", "seasonal_naive")
ILITOTAL_INDEX = 4
T_CRIT = stats.t.ppf(0.975, 9)          # 2.262157 (df=9)

# Frozen validation baselines (from results/v3_clean/analysis/*).
VAL_AVG_MSE_4L = {
    "gpt2_miflu": 0.7708721562796242,
    "nlinear": 1.0697672040053035,
    "seasonal_naive": 0.7706732060919699,   # mean of the 4 per-L values below
}
VAL_PER_L_MSE = {
    "gpt2_miflu": {24: 0.7324420428409919, 36: 0.7781652358508216,
                   48: 0.7598191411721624, 60: 0.813062205254521},
    "nlinear": {24: 0.9791234190262845, 36: 1.0490394758439423,
                48: 1.1007642306107754, 60: 1.1501416905402109},
    "seasonal_naive": {24: 0.7193443203456401, 36: 0.7324035803523475,
                       48: 0.7460317981833594, 60: 0.8849131254865326},
}


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def season_of_epiweek(epiweek: int) -> str:
    yr, wk = epiweek // 100, epiweek % 100
    return f"{yr}/{yr + 1}" if wk >= 40 else f"{yr - 1}/{yr}"


def build_calendar():
    from cdc_calendar import load_week_calendar
    cal = load_week_calendar(os.path.join(ROOT, "data", "raw", "national_illness_raw.csv"))
    abs_to_epi = dict(zip(cal["abs_week"].astype(int), cal["epiweek"].astype(int)))
    return abs_to_epi


def list_runs():
    """Return [(run_key, manifest)] for all 84 test-eval dirs."""
    runs = []
    for d in sorted(os.listdir(TEST_RESULTS)):
        rd = os.path.join(TEST_RESULTS, d)
        mf = os.path.join(rd, "test_manifest.json")
        if os.path.isdir(rd) and os.path.isfile(mf):
            runs.append((d, load_json(mf)))
    if len(runs) != 84:
        raise SystemExit(f"expected 84 run dirs, found {len(runs)}")
    return runs


def run_summary(runs):
    """Per-run scalar metrics -> DataFrame keyed by (model, horizon, seed)."""
    rows = []
    for key, m in runs:
        rd = os.path.join(TEST_RESULTS, key)
        paper = load_json(os.path.join(rd, "metrics", "paper_aligned_full_output_metrics.json"))
        ilifull = load_json(os.path.join(rd, "metrics", "ilitotal_full_horizon_metrics.json"))
        rows.append({
            "run_key": key, "model": m["model"], "horizon": int(m["horizon"]),
            "seed": m["seed"], "arm": m["arm"],
            "mse_7v_z": paper["mse_all_7vars_full_horizon_z"],
            "mae_7v_z": paper["mae_all_7vars_full_horizon_z"],
            "mse_ili_z": ilifull["mse_z"], "mae_ili_z": ilifull["mae_z"],
            "mse_ili_phys": ilifull["mse_physical"],
            "mae_ili_phys": ilifull["mae_physical"],
        })
    df = pd.DataFrame(rows)
    if len(df) != 84:
        raise SystemExit(f"expected 84 run summaries, got {len(df)}")
    return df


def seed_ci(values):
    """Mean + t 95% CI (df=9) over the 10 seed values."""
    a = np.asarray(values, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    se = sd / np.sqrt(len(a))
    return {"mean": m, "sd": sd, "n": int(len(a)),
            "ci95_lo": m - T_CRIT * se, "ci95_hi": m + T_CRIT * se}


def per_seed_avg_mse_4l(df):
    """Per-seed average_MSE_4L = mean over the 4 horizons of that seed's MSE."""
    out = {}
    for model in ("gpt2_miflu", "nlinear"):
        g = df[df.model == model]
        vals = {}
        for seed in SEEDS:
            s = g[g.seed == seed].set_index("horizon")["mse_7v_z"]
            vals[int(seed)] = float(np.mean([s[h] for h in HORIZONS]))
        out[model] = vals
    return out


def paired_t(model_a, model_b, per_seed_values, a_name, b_name):
    """Paired t (matched seed) + Cohen's d_z over 10 seeds."""
    a = np.array([per_seed_values[a_name][s] for s in SEEDS], dtype=float)
    b = np.array([per_seed_values[b_name][s] for s in SEEDS], dtype=float)
    d = a - b
    t, p = stats.ttest_rel(a, b)
    dz = float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else float("nan")
    return {"test": f"{a_name} vs {b_name}", "type": "paired_t_matched_seed",
            "n_pairs": len(a), "mean_diff": float(d.mean()),
            "paired_t": float(t), "p_value": float(p),
            "cohens_dz": dz, "mean_a": float(a.mean()), "mean_b": float(b.mean())}


def vs_deterministic(model, reference_value, per_seed_values, ref_name):
    """One-sample t on (seed_i - reference) against the deterministic baseline."""
    a = np.array([per_seed_values[model][s] for s in SEEDS], dtype=float)
    d = a - reference_value
    t, p = stats.ttest_1samp(d, 0.0)
    dz = float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else float("nan")
    return {"test": f"{model} vs {ref_name}", "type": "one_sample_t_vs_deterministic",
            "n_pairs": len(a), "mean_diff": float(d.mean()),
            "paired_t": float(t), "p_value": float(p),
            "cohens_dz": dz, "mean_a": float(a.mean()),
            "mean_b": float(reference_value),
            "note": "deterministic reference has no seed variance; seed_i - reference "
                    "tested against 0 (df=9)."}


def holm_bonferroni(pvals, alpha=0.05):
    """Holm-Bonferroni step-down over a list of (label, p) sorted ascending."""
    ordered = sorted(pvals, key=lambda x: x[1])
    m = len(ordered)
    out = []
    for rank, (label, p) in enumerate(ordered, start=1):
        adj = p * (m - rank + 1)
        adj = min(adj, 1.0)
        out.append({"label": label, "raw_p": p, "holm_p": adj,
                    "reject": adj < alpha, "rank": rank, "m": m})
    return out


def load_seed_mean_curves(df, runs):
    """Per (model, horizon): ILITOTAL seed-mean curve indexed by target_date.

    Returns dict[(model, horizon)] = DataFrame[abs_week, y_true, y_pred, lead].
    Reads the SAVED prediction CSVs (seed-mean over 10 seeds for stochastic).
    """
    curves = {}
    for model in MODELS:
        for h in HORIZONS:
            frames = []
            keys = [k for k, m in runs if m["model"] == model and int(m["horizon"]) == h]
            for k in keys:
                p = os.path.join(TEST_RESULTS, k, "predictions", "test_predictions.csv")
                df_p = pd.read_csv(p)
                df_p = df_p[df_p["variable_index"] == ILITOTAL_INDEX]
                frames.append(df_p[["target_date", "lead_weeks", "y_true_physical",
                                    "y_pred_physical"]])
            full = pd.concat(frames, ignore_index=True)
            # seed-mean per (target_date, lead): y_true identical across seeds
            agg = (full.groupby(["target_date", "lead_weeks"], as_index=False)
                   .agg(y_true=("y_true_physical", "mean"),
                        y_pred=("y_pred_physical", "mean")))
            agg["abs_week"] = agg["target_date"].astype(int)
            curves[(model, h)] = agg
    return curves


def peak_metrics(curves, abs_to_epi):
    """peak-evaluation-v1: per (model, horizon, lead, season) PTE/PIE."""
    rows = []
    for (model, h), agg in curves.items():
        for lead in LEADS:
            g = agg[agg["lead_weeks"] == lead].sort_values("target_date")
            if g.empty:
                continue
            g = g.assign(season=g["abs_week"].map(abs_to_epi).map(season_of_epiweek))
            for season, sg in g.groupby("season"):
                sg = sg.sort_values("target_date")
                yt = sg["y_true"].to_numpy(dtype=float)
                yp = sg["y_pred"].to_numpy(dtype=float)
                nw = len(sg)
                if nw < 2:
                    rows.append(dict(model=model, horizon=h, lead=lead, season=season,
                                     n_weeks=nw, eligible=False, reason="<2 weeks",
                                     PTE=None, PIE=None))
                    continue
                obs_peak = float(yt.max())
                if obs_peak <= 0:
                    rows.append(dict(model=model, horizon=h, lead=lead, season=season,
                                     n_weeks=nw, eligible=False,
                                     reason="observed_peak_zero", PTE=None, PIE=None))
                    continue
                obs_i = int(np.argmax(yt))
                pred_i = int(np.argmax(yp))
                pte = float(abs(pred_i - obs_i))
                pie = float(abs(yp[pred_i] - obs_peak) / obs_peak * 100.0)
                rows.append(dict(model=model, horizon=h, lead=lead, season=season,
                                 n_weeks=nw, eligible=True, reason="",
                                 observed_peak_week=int(sg["target_date"].iloc[obs_i]),
                                 predicted_peak_week=int(sg["target_date"].iloc[pred_i]),
                                 observed_peak_value=obs_peak,
                                 predicted_peak_value=float(yp[pred_i]),
                                 PTE=pte, PIE=pie,
                                 PTE_hit=pte <= 1.0, PIE_hit=pie <= 25.0,
                                 joint_hit=(pte <= 1.0 and pie <= 25.0)))
    return pd.DataFrame(rows)


def hit_rates(peak_df):
    """Aggregate peak_df to per (model, horizon, lead) and per (model, horizon)."""
    elig = peak_df[peak_df.eligible]
    by_lead = []
    for (model, h, lead), g in elig.groupby(["model", "horizon", "lead"]):
        n = len(g)
        by_lead.append(dict(model=model, horizon=h, lead=lead, n_eligible=n,
                            mean_pte=float(g.PTE.mean()),
                            mean_pie=float(g.PIE.mean()),
                            pte_hit_rate=float(g.PTE_hit.mean()),
                            pie_hit_rate=float(g.PIE_hit.mean()),
                            joint_hit_rate=float(g.joint_hit.mean())))
    by_horizon = []
    for (model, h), g in elig.groupby(["model", "horizon"]):
        n = len(g)
        by_horizon.append(dict(model=model, horizon=h, n_eligible=n,
                               mean_pte=float(g.PTE.mean()),
                               mean_pie=float(g.PIE.mean()),
                               pte_hit_rate=float(g.PTE_hit.mean()),
                               pie_hit_rate=float(g.PIE_hit.mean()),
                               joint_hit_rate=float(g.joint_hit.mean())))
    return pd.DataFrame(by_lead), pd.DataFrame(by_horizon)


def build_access_ledger():
    """Reconcile the driver ledger with the authorization record."""
    lines = [json.loads(l) for l in open(LEDGER, "r", encoding="utf-8") if l.strip()]
    auth = load_json(os.path.join(FINAL, "pre_test_authorization_record.json"))
    out = {
        "ledger": "final_test_access_ledger",
        "authorized_models": auth["authorized_models"],
        "expected_job_count": auth["expected_job_count"],
        "observed_job_count": len(lines),
        "all_completed": all(e.get("state") == "COMPLETED" for e in lines),
        "all_exit_0_0": all(e.get("exit") == "0:0" for e in lines),
        "n_fail": sum(1 for e in lines if e.get("state") != "COMPLETED"
                      or e.get("exit") != "0:0"),
        "job_ids_unique": len({e["job_id"] for e in lines}) == len(lines),
        "entries": lines,
    }
    with open(os.path.join(FINAL, "final_test_access_ledger.jsonl"), "w",
              encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e) + "\n")
    return out


def build_analysis_dataset(runs):
    """Concatenate all 84 test_predictions.csv with a run_key provenance column."""
    frames = []
    for key, m in runs:
        p = os.path.join(TEST_RESULTS, key, "predictions", "test_predictions.csv")
        d = pd.read_csv(p)
        d.insert(0, "run_key", key)
        frames.append(d)
    ds = pd.concat(frames, ignore_index=True)
    ds.to_csv(os.path.join(FINAL, "final_test_analysis_dataset.csv"), index=False)
    return len(ds)


def main() -> int:
    runs = list_runs()
    abs_to_epi = build_calendar()
    df = run_summary(runs)
    per_seed_avg = per_seed_avg_mse_4l(df)

    # ---- primary / secondary per model --------------------------------
    metrics = {"models": {}}
    seed_level_rows = []
    for model in MODELS:
        g = df[df.model == model]
        per_L = {}
        avg_mse = {}
        avg_mae = {}
        ili = {"mse_z": {}, "mae_z": {}, "mse_phys": {}, "mae_phys": {}}
        for h in HORIZONS:
            gh = g[g.horizon == h]
            if len(gh) == 1:            # deterministic baseline
                r = gh.iloc[0]
                mse, mae = r["mse_7v_z"], r["mae_7v_z"]
                per_L[h] = {"mse": mse, "mae": mae, "n_seeds": 1, "deterministic": True}
            else:                        # 10 seeds
                ci_m = seed_ci(gh["mse_7v_z"])
                ci_a = seed_ci(gh["mae_7v_z"])
                per_L[h] = {"mse": ci_m["mean"], "mae": ci_a["mean"],
                            "n_seeds": 10, "deterministic": False,
                            "mse_sd": ci_m["sd"], "mse_ci95": [ci_m["ci95_lo"], ci_m["ci95_hi"]],
                            "mae_sd": ci_a["sd"], "mae_ci95": [ci_a["ci95_lo"], ci_a["ci95_hi"]]}
            avg_mse[h] = per_L[h]["mse"]
            avg_mae[h] = per_L[h]["mae"]
            ili["mse_z"][h] = float(gh["mse_ili_z"].mean())
            ili["mae_z"][h] = float(gh["mae_ili_z"].mean())
            ili["mse_phys"][h] = float(gh["mse_ili_phys"].mean())
            ili["mae_phys"][h] = float(gh["mae_ili_phys"].mean())
        # average_MSE_4L: stochastic -> mean over L of per-L seed-means;
        # CI across the 10 per-seed average_MSE_4L values.
        avg4 = float(np.mean([avg_mse[h] for h in HORIZONS]))
        avg_mae4 = float(np.mean([avg_mae[h] for h in HORIZONS]))
        if model in per_seed_avg:
            ci_avg4 = seed_ci(list(per_seed_avg[model].values()))
        else:
            ci_avg4 = {"mean": avg4, "sd": None, "n": 1, "ci95_lo": None, "ci95_hi": None}
        metrics["models"][model] = {
            "average_MSE_4L": avg4, "average_MAE_4L": avg_mae4,
            "average_MSE_4L_ci95": [ci_avg4["ci95_lo"], ci_avg4["ci95_hi"]],
            "per_L_mse": {str(h): avg_mse[h] for h in HORIZONS},
            "per_L_mae": {str(h): avg_mae[h] for h in HORIZONS},
            "per_L_detail": {str(h): per_L[h] for h in HORIZONS},
            "ilitotal_full_horizon": {
                "mse_z_mean_over_L": float(np.mean(list(ili["mse_z"].values()))),
                "mae_z_mean_over_L": float(np.mean(list(ili["mae_z"].values()))),
                "mse_physical_mean_over_L": float(np.mean(list(ili["mse_phys"].values()))),
                "mae_physical_mean_over_L": float(np.mean(list(ili["mae_phys"].values()))),
                "per_L": {str(h): {"mse_z": ili["mse_z"][h], "mae_z": ili["mae_z"][h],
                                   "mse_phys": ili["mse_phys"][h],
                                   "mae_phys": ili["mae_phys"][h]} for h in HORIZONS},
            },
        }
        # seed-level rows (for the durable seed-level CSV)
        for _, r in g.iterrows():
            seed_level_rows.append({"run_key": r["run_key"], "model": model,
                                    "horizon": r["horizon"], "seed": r["seed"],
                                    "mse_7v_z": r["mse_7v_z"], "mae_7v_z": r["mae_7v_z"],
                                    "mse_ili_z": r["mse_ili_z"], "mae_ili_z": r["mae_ili_z"],
                                    "mse_ili_phys": r["mse_ili_phys"],
                                    "mae_ili_phys": r["mae_ili_phys"]})

    # ---- confirmatory tests ------------------------------------------
    confirmatory = {}
    # per-L paired t for C1 (stochastic vs stochastic)
    c1_per_L = {}
    for h in HORIZONS:
        vals = {m: {s: float(df[(df.model == m) & (df.horizon == h) & (df.seed == s)]
                              ["mse_7v_z"].iloc[0]) for s in SEEDS}
                for m in ("gpt2_miflu", "nlinear")}
        c1_per_L[h] = paired_t("gpt2_miflu", "nlinear", vals,
                               "gpt2_miflu", "nlinear")
    c1_avg = paired_t("gpt2_miflu", "nlinear", per_seed_avg,
                      "gpt2_miflu", "nlinear")

    # C2/C3 vs deterministic seasonal_naive (one-sample t)
    def vs_sn(model, ref_val):
        per_L = {}
        for h in HORIZONS:
            vals = {s: float(df[(df.model == model) & (df.horizon == h) & (df.seed == s)]
                             ["mse_7v_z"].iloc[0]) for s in SEEDS}
            per_L[h] = vs_deterministic(model, ref_val["per_L"][h], {model: vals},
                                        "seasonal_naive")
        avg = vs_deterministic(model, ref_val["avg"], per_seed_avg, "seasonal_naive")
        return {"per_L": per_L, "average_MSE_4L": avg}

    # Reference for C2/C3 is seasonal_naive's TEST MSE (Test-vs-Test, per plan).
    sn_test_per_L = {h: metrics["models"]["seasonal_naive"]["per_L_mse"][str(h)]
                     for h in HORIZONS}
    sn_test_avg = metrics["models"]["seasonal_naive"]["average_MSE_4L"]
    sn_ref = {"per_L": sn_test_per_L, "avg": sn_test_avg}
    c2 = vs_sn("gpt2_miflu", sn_ref)
    c3 = vs_sn("nlinear", sn_ref)

    confirmatory["C1_gpt2_miflu_vs_nlinear"] = {"per_L": c1_per_L,
                                                "average_MSE_4L": c1_avg}
    confirmatory["C2_gpt2_miflu_vs_seasonal_naive"] = c2
    confirmatory["C3_nlinear_vs_seasonal_naive"] = c3

    # Holm-Bonferroni across the 3 PRIMARY (average_MSE_4L) tests
    holm = holm_bonferroni([
        ("C1_gpt2_miflu_vs_nlinear", c1_avg["p_value"]),
        ("C2_gpt2_miflu_vs_seasonal_naive", c2["average_MSE_4L"]["p_value"]),
        ("C3_nlinear_vs_seasonal_naive", c3["average_MSE_4L"]["p_value"]),
    ])
    confirmatory["multiple_comparison"] = {
        "method": "Holm-Bonferroni (step-down)",
        "family": "3 confirmatory PRIMARY tests (average_MSE_4L), alpha=0.05",
        "tests": holm,
    }

    # ---- validation-to-test gap --------------------------------------
    gap_rows = []
    for model in MODELS:
        tm = metrics["models"][model]
        for h in HORIZONS:
            gap_rows.append(dict(model=model, horizon=h,
                                 test_mse=tm["per_L_mse"][str(h)],
                                 validation_mse=VAL_PER_L_MSE[model][h],
                                 gap=float(tm["per_L_mse"][str(h)]
                                           - VAL_PER_L_MSE[model][h])))
        gap_rows.append(dict(model=model, horizon="avg_4L",
                             test_mse=tm["average_MSE_4L"],
                             validation_mse=VAL_AVG_MSE_4L[model],
                             gap=float(tm["average_MSE_4L"] - VAL_AVG_MSE_4L[model])))
    gap_df = pd.DataFrame(gap_rows)
    gap_df.to_csv(os.path.join(FINAL, "final_generalization_comparison.csv"),
                  index=False)
    metrics["validation_to_test_gap"] = {
        "definition": "Test average_MSE_4L - Validation average_MSE_4L (negative = better on Test)",
        "per_model_avg": {m: float(metrics["models"][m]["average_MSE_4L"]
                                   - VAL_AVG_MSE_4L[m]) for m in MODELS},
    }

    # ---- PTE/PIE + hit rates -----------------------------------------
    curves = load_seed_mean_curves(df, runs)
    peak_df = peak_metrics(curves, abs_to_epi)
    peak_df.to_csv(os.path.join(FINAL, "final_peak_metrics.csv"), index=False)
    by_lead, by_horizon = hit_rates(peak_df)
    by_lead.to_csv(os.path.join(FINAL, "final_peak_hit_rates.csv"), index=False)
    metrics["pte_pie"] = {
        "spec": "peak-evaluation-v1",
        "per_horizon": by_horizon.to_dict(orient="records"),
        "per_horizon_lead": by_lead.to_dict(orient="records"),
        "n_eligible_season_leads": int(peak_df.eligible.sum()),
        "summary_notes": ("PTE<=1wk / PIE<=25% / joint, per eligible season and lead, "
                          "aggregated per horizon; secondary public-health metrics."),
    }

    # ---- assemble + write final_test_metrics.json --------------------
    metrics["confirmatory_tests"] = confirmatory
    metrics["meta"] = {
        "generated_utc": pd.Timestamp.utcnow().isoformat() + "Z",
        "split": "Test/Holdout",
        "n_runs": 84, "n_test_windows": "per-run (see manifests)",
        "primary_endpoint": "mse_all_7vars_full_horizon_z (average_MSE_4L)",
        "confidence": "t-distribution 95% CI across 10 seeds (df=9)",
        "rounding": "full precision stored; 4 significant figures applied in reports",
    }
    with open(os.path.join(FINAL, "final_test_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # ---- seed-level CSV + access ledger + dataset + manifest ---------
    pd.DataFrame(seed_level_rows).to_csv(
        os.path.join(FINAL, "final_test_seed_level.csv"), index=False)
    ledger = build_access_ledger()
    n_ds = build_analysis_dataset(runs)

    manifest = {
        "phase": "final_test",
        "n_runs": 84,
        "n_dataset_rows": n_ds,
        "terminal_audit": load_json(AUDIT),
        "access_ledger_summary": {k: ledger[k] for k in ledger if k != "entries"},
        "artifacts": {
            "final_test_analysis_dataset.csv": "concatenated 84 test_predictions.csv + run_key",
            "final_test_metrics.json": "primary/secondary/PTE-PIE/confirmatory/gap",
            "final_test_seed_level.csv": "per-run scalar metrics",
            "final_peak_metrics.csv": "per (model,horizon,lead,season) PTE/PIE",
            "final_peak_hit_rates.csv": "per (model,horizon,lead) hit rates",
            "final_generalization_comparison.csv": "validation vs test gap",
            "final_test_access_ledger.jsonl": "84 reconciled access records",
        },
    }
    with open(os.path.join(FINAL, "final_test_artifact_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # ---- concise console report --------------------------------------
    print("FINAL TEST METRICS (average_MSE_4L, lower=better)")
    for m in MODELS:
        tm = metrics["models"][m]
        ci = tm["average_MSE_4L_ci95"]
        ci_s = (f"[{ci[0]:.6f},{ci[1]:.6f}]" if ci[0] is not None else "n/a (deterministic)")
        print(f"  {m:15s} test={tm['average_MSE_4L']:.6f} "
              f"CI95={ci_s} "
              f"val={VAL_AVG_MSE_4L[m]:.6f} "
              f"gap={tm['average_MSE_4L']-VAL_AVG_MSE_4L[m]:+.6f}")
    print("CONFIRMATORY (average_MSE_4L)")
    for t in holm:
        print(f"  {t['label']:40s} raw_p={t['raw_p']:.3e} holm_p={t['holm_p']:.3e} "
              f"reject={t['reject']}")
    print(f"PTE/PIE eligible season-leads = {int(peak_df.eligible.sum())}")
    print(f"Dataset rows = {n_ds}")
    print(f"Access ledger entries = {ledger['observed_job_count']}, "
          f"fail = {ledger['n_fail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
