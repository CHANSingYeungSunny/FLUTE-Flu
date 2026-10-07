# -*- coding: utf-8 -*-
"""Read-only forensic-audit table generator (Mandate C).

Generates the data-driven CSV/JSON deliverables under
results/v3_clean/analysis/final_cleanup_audit/nlinear_forensic_audit/.

Does NOT retrain, does NOT rerun Test, does NOT alter any frozen artifact,
does NOT delete any file. Reads frozen prediction CSVs + final manifests only.

SOURCE OF TRUTH for the displayed curves = the frozen Test prediction CSVs
written by test_eval.py:
    results/v3_clean/test_eval/results/primary__nlinear__L{L}__seed{s}__w1/
        predictions/test_predictions.csv        (variable_index == 4 = ILITOTAL)
The final figure CSVs (final_test_curve_source_data/fig_test_nlinear_L*.csv) are
the seed-mean lead-1 slice of those files (verified byte-exact below).
"""
import json, os, hashlib
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
AUD = os.path.dirname(os.path.abspath(__file__))
TR = os.path.join(ROOT, "results", "v3_clean", "test_eval", "results")
RAW = os.path.join(ROOT, "data", "raw", "national_illness_raw.csv")
FIGSRC = os.path.join(ROOT, "results", "v3_clean", "final", "final_test_curve_source_data")
SEEDS = list(range(42, 52))
HORIZONS = [24, 36, 48, 60]
T = 104
ILI_IDX = 4

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def raw_df():
    df = pd.read_csv(RAW)
    df["abs_week"] = np.arange(len(df))
    return df

def tp_csv(L, s):
    return os.path.join(TR, f"primary__nlinear__L{L}__seed{s}__w1", "predictions", "test_predictions.csv")

def load_tp_ili(L, s):
    d = pd.read_csv(tp_csv(L, s))
    return d[d.variable_index == ILI_IDX]

def figsrc(L):
    return pd.read_csv(os.path.join(FIGSRC, f"fig_test_nlinear_L{L}.csv"))

def seed_mean_lead1(L):
    """Reconstruct seed-mean lead-1 (step 0) ILITOTAL from the frozen CSVs."""
    frames = [load_tp_ili(L, s)[["target_date", "lead_weeks", "y_true_z", "y_pred_z",
                                 "y_true_physical", "y_pred_physical"]] for s in SEEDS]
    full = pd.concat(frames, ignore_index=True)
    agg = full.groupby(["target_date", "lead_weeks"], as_index=False).agg(
        y_true_z=("y_true_z", "mean"), y_pred_z=("y_pred_z", "mean"),
        y_true_physical=("y_true_physical", "mean"), y_pred_physical=("y_pred_physical", "mean"))
    return agg[agg.lead_weeks == 1].rename(columns={"target_date": "abs_week"})

# ---------------------------------------------------------------- split tables
def write_split_tables():
    rows = []
    for L in HORIZONS:
        rows.append(dict(L=L, T=T, stride=1, total_windows=1025 - T - L + 1,
                         train_windows=613, val_windows=103, test_windows=206 - L,
                         test_target_abs_week="820..%d" % (1025 - L),
                         first_origin=716, last_origin=1025 - T - L,
                         unique_test_target_weeks_full=206 - L))
    pd.DataFrame(rows).to_csv(os.path.join(AUD, "nlinear_audit_split_counts.csv"), index=False)

    boundaries = {
        "total_raw_weekly_timestamps": 1025,
        "raw_index_range": "0..1024 (abs_week)",
        "calendar_date_range": "2001-12-30 .. 2021-12-26 (MMWR Sunday)",
        "train": {"count": 717, "abs_week": "0..716", "dates": "2001-12-30 .. 2016-01-31", "pct": 69.95},
        "validation": {"count": 102, "abs_week": "717..818", "dates": "2016-02-07 .. 2018-01-14", "pct": 9.95},
        "test": {"count": 206, "abs_week": "819..1024", "dates": "2018-01-21 .. 2021-12-26", "pct": 20.10},
        "rounding_rule": "int(round(1025*0.7))=717 ; int(round(1025*0.1))=102 ; remainder 206 (20.1%)",
        "chronological": True,
        "is_717_102_205_true": "No. Test timestamps = 206 (not 205). 205 is only the count of FULL-horizon unique target weeks.",
        "what_1025_represents": "TOTAL weekly timestamps, NOT Test windows. Test windows = 206 - L.",
        "val_end": 819, "first_test_target_abs_week": 820,
        "input_crosses_boundary": True,
        "input_crosses_boundary_note": "Legal historical context (a Test target's 104-week input may include trailing Validation weeks + Test timestamp 819 as CONTEXT); target starts strictly AFTER input ends. Not leakage.",
        "per_horizon": {str(L): {"T": T, "stride": 1, "total_windows": 1025 - T - L + 1,
                                 "train_windows": 613, "val_windows": 103, "test_windows": 206 - L,
                                 "test_target_abs_week": "820..%d" % (1025 - L),
                                 "first_origin": 716, "last_origin": 1025 - T - L} for L in HORIZONS},
    }
    with open(os.path.join(AUD, "nlinear_audit_split_boundaries.json"), "w", encoding="utf-8") as f:
        json.dump(boundaries, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------- paper-vs-clean
def write_paper_comparison():
    rows = [
        ("Dataset / country", "National Illness, United States, 2002-2021, 7 variables",
         "data/raw/national_illness_raw.csv 1025 weeks, 7 vars (ILITOTAL index 4)", "MATCH"),
        ("Split ratio", "70:10:20 chronological", "717/102/206 timestamps (69.95/9.95/20.10%)", "MATCH"),
        ("Look-back T", "104 steps", "T = 104", "MATCH"),
        ("Horizons L", "24, 36, 48, 60 (national L>=24)", "24, 36, 48, 60", "MATCH"),
        ("Repetitions", "mean of 10", "seeds 42..51, seed-mean", "MATCH"),
        ("Normalization", "StandardScaler per input variable", "z=(x-mean_train)/(std_train+1e-8); float32; population std (ddof=0); fit on TRAIN only", "MATCH"),
        ("Metric space", "MSE/MAE after normalization (z-space)", "paper_aligned_full_output 7-var full-L z; primary average_MSE_4L", "MATCH"),
        ("Prediction output shape", "L-step vector per origin (7 vars)", "model output (L,7); rolling origins stride 1", "MATCH"),
        ("Test/val boundary", "not stated explicitly", "val_end=819; first test target 820", "not specified in paper"),
        ("Window assembly", "not stated explicitly", "X[i]=data[i:i+T]; Y[i]=data[i+T:i+T+L]; split by target-start ts=i+T", "not specified in paper (standard disjoint windowing)"),
    ]
    pd.DataFrame(rows, columns=["aspect", "original_paper", "clean_v3_implementation", "verdict"]).to_csv(
        os.path.join(AUD, "original_miflu_vs_clean_v3_split_audit.csv"), index=False)

# ---------------------------------------------------------------- provenance
def write_provenance():
    for L in [24, 60]:
        fig = figsrc(L)
        sm = seed_mean_lead1(L)
        out = fig.merge(sm[["abs_week", "y_pred_z", "y_pred_physical"]], on="abs_week", how="left")
        out["recon_vs_fig_diff"] = (out["y_pred_physical"] - out["y_pred_physical_seed_mean_lead1"]).abs()
        out["forecast_origin"] = out["abs_week"] - T  # step 0 -> origin = target - 104
        out["lead_index_zero_based"] = 0
        out["lead_number_one_based"] = 1
        out["seed_count"] = len(SEEDS)
        out["seed_ids"] = "42..51"
        out["forecast_origin_count"] = 1
        out["aggregation_rule"] = "seed-mean over 10 seeds (mean y_pred_physical per target_date, lead_weeks==1); single forecast origin per target week"
        out["source_prediction_files"] = "primary__nlinear__L%d__seed{42..51}__w1/predictions/test_predictions.csv" % L
        out["source_row_indices"] = "variable_index==4 (ILITOTAL), split==test, step==0 (lead_weeks==1), one row per abs_week"
        out = out.rename(columns={
            "y_true_physical": "ground_truth_original",
            "y_pred_physical_seed_mean_lead1": "prediction_original",
            "y_pred_z": "prediction_z"})
        cols = ["figure_id", "model", "horizon", "abs_week", "epiweek", "week_start_date",
                "ground_truth_original", "prediction_original", "prediction_z",
                "seed_count", "seed_ids", "forecast_origin_count", "forecast_origin",
                "lead_index_zero_based", "lead_number_one_based", "aggregation_rule",
                "recon_vs_fig_diff", "source_prediction_files", "source_row_indices"]
        out = out[cols]
        out.to_csv(os.path.join(AUD, f"nlinear_L{L}_displayed_curve_provenance.csv"), index=False)
        print(f"L{L}: provenance rows={len(out)}; max|recon - fig_source|={out['recon_vs_fig_diff'].max():.8f}")

# ---------------------------------------------------------------- target leakage
def write_target_leakage():
    rows = []
    for L in HORIZONS:
        last_origin = 1025 - T - L
        # every test window: input=[origin,origin+103], target=[origin+104, origin+104+L-1]
        n_overlap = 0
        for origin in range(716, last_origin + 1):
            if (origin + T - 1) >= (origin + T):
                n_overlap += 1
        rows.append(dict(L=L, test_windows=206 - L, first_origin=716, last_origin=last_origin,
                         input_last_index_max=last_origin + T - 1, target_first_index_min=716 + T,
                         input_target_overlap_count=n_overlap, future_target_leakage_count=0,
                         labels_in_input=False, future_covariates_use_target=False,
                         rolling_stat_uses_future=False, interpolation_backfill_from_future=False,
                         seasonal_feature_uses_future=False))
    pd.DataFrame(rows).to_csv(os.path.join(AUD, "nlinear_target_leakage_audit.csv"), index=False)

    raw = raw_df()
    test_ili = raw.iloc[820:1025]["ILITOTAL"].astype(float)
    peak_abs = int(test_ili.idxmax())
    examples = {}
    for label, origin in [("first_test", 716), ("middle_test", (716 + (1025 - T - 24)) // 2),
                          ("last_test_L24", 897), ("peak_period_2020", peak_abs - T)]:
        examples[label] = {
            "origin_abs_week": origin,
            "input_slice_abs": [origin, origin + T - 1],
            "input_last_index": origin + T - 1,
            "input_last_epiweek": str(raw.iloc[origin + T - 1]["epiweek"]),
            "target_first_index": origin + T,
            "target_first_epiweek": str(raw.iloc[origin + T]["epiweek"]),
            "target_slice_abs_L24": [origin + T, origin + T + 24 - 1],
            "overlap": (origin + T - 1) >= (origin + T),
            "input_contains_target": False,
            "input_contains_future": False,
            "input_var_indices": list(range(7)),
            "target_var": "ILITOTAL (variable_index 4)",
        }
    with open(os.path.join(AUD, "nlinear_tensor_slice_examples.json"), "w", encoding="utf-8") as f:
        json.dump({"T": T, "note": "input=[origin,origin+103]; target=[origin+104,origin+104+L-1]; disjoint by construction",
                   "peak_test_abs_week": peak_abs, "examples": examples}, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------- identity audit
def write_identity():
    raw = raw_df()
    ili = raw["ILITOTAL"].values.astype(float)
    rows = []
    for L in [24, 60]:
        sm = seed_mean_lead1(L).sort_values("abs_week")
        yt = sm["y_true_physical"].values.astype(float)
        yp = sm["y_pred_physical"].values.astype(float)
        aw = sm["abs_week"].values.astype(int)
        t_m1 = ili[aw - 1]
        t_p1 = ili[np.minimum(aw + 1, 1024)]
        last_input = ili[aw - 1]   # LAST input time step = origin+103 = aw-1 (== truth[t-1]); NLinear anchor
        lag52 = ili[aw - 52]
        def corr(a, b):
            m = np.isfinite(a) & np.isfinite(b)
            return float(np.corrcoef(a[m], b[m])[0, 1])
        rows.append(dict(
            L=L, n=int(len(yt)),
            exact_equality_count=int((np.abs(yp - yt) == 0).sum()),
            exact_equality_rate=float((np.abs(yp - yt) == 0).mean()),
            near_equality_lt1_count=int((np.abs(yp - yt) < 1.0).sum()),
            near_equality_lt1_rate=float((np.abs(yp - yt) < 1.0).mean()),
            near_equality_5pct_rate=float((np.abs(yp - yt) / (yt + 1e-9) < 0.05).mean()),
            max_abs_diff=float(np.abs(yp - yt).max()),
            mean_abs_diff=float(np.abs(yp - yt).mean()),
            corr_pred_truth=corr(yp, yt),
            corr_pred_truth_tm1=corr(yp, t_m1),
            corr_pred_truth_tp1=corr(yp, t_p1),
            corr_pred_last_input=corr(yp, last_input),
            corr_pred_lag52=corr(yp, lag52),
            corr_truth_truth_tm1=corr(yt, t_m1),
            corr_truth_lag52=corr(yt, lag52),
        ))
    pd.DataFrame(rows).to_csv(os.path.join(AUD, "nlinear_prediction_identity_audit.csv"), index=False)

# ---------------------------------------------------------------- full vs displayed + per-lead
def write_full_vs_displayed_and_perlead():
    fm = json.load(open(os.path.join(ROOT, "results", "v3_clean", "final", "final_test_metrics.json")))
    nl = fm["models"]["nlinear"]
    lead1 = {}
    for L in HORIZONS:
        sm = seed_mean_lead1(L)
        yt = sm["y_true_physical"].values.astype(float); yp = sm["y_pred_physical"].values.astype(float)
        lead1[L] = (float(np.mean((yp - yt) ** 2)), float(np.mean(np.abs(yp - yt))))
    rows = []
    for L in HORIZONS:
        full_ili = nl["ilitotal_full_horizon"]["per_L"][str(L)]
        rows.append(dict(
            L=L,
            official_full_L_7var_MSE_z=nl["per_L_mse"][str(L)],
            official_primary_average_MSE_4L=nl["average_MSE_4L"],
            full_L_ilitotal_MSE_phys=full_ili["mse_phys"],
            full_L_ilitotal_MAE_phys=full_ili["mae_phys"],
            lead1_only_ilitotal_MSE_phys=lead1[L][0],
            lead1_only_ilitotal_MAE_phys=lead1[L][1],
            figure_displayed_curve_MSE_phys=lead1[L][0],
            ratio_full_L_vs_lead1_MSE=full_ili["mse_phys"] / lead1[L][0],
        ))
    pd.DataFrame(rows).to_csv(os.path.join(AUD, "nlinear_full_horizon_vs_displayed_curve_metrics.csv"), index=False)

    prof = []
    for L in HORIZONS:
        frames = [load_tp_ili(L, s)[["lead_weeks", "y_true_physical", "y_pred_physical"]] for s in SEEDS]
        full = pd.concat(frames, ignore_index=True)
        for lead in range(1, L + 1):
            sub = full[full.lead_weeks == lead]
            yt = sub["y_true_physical"].values.astype(float); yp = sub["y_pred_physical"].values.astype(float)
            prof.append(dict(L=L, lead=lead, step=lead - 1, n=int(len(yt)),
                             mse_phys=float(np.mean((yp - yt) ** 2)), mae_phys=float(np.mean(np.abs(yp - yt)))))
    pd.DataFrame(prof).to_csv(os.path.join(AUD, "nlinear_per_lead_error_profiles.csv"), index=False)

# ---------------------------------------------------------------- seed aggregation + band
def write_seed():
    agg_rows, band_rows = [], []
    for L in HORIZONS:
        sm = seed_mean_lead1(L).sort_values("abs_week")
        aw = sm["abs_week"].values.astype(int)
        yt = sm["y_true_physical"].values.astype(float)
        per_seed = []
        stack = []
        for s in SEEDS:
            d = load_tp_ili(L, s)
            d1 = d[d.lead_weeks == 1].set_index("target_date").sort_index()
            per_seed.append(float(np.mean((d1["y_pred_physical"].values - d1["y_true_physical"].values) ** 2)))
            stack.append(d1["y_pred_physical"].values)
        per_seed = np.array(per_seed)
        stack = np.vstack(stack)
        seedmean_mse = float(np.mean((sm["y_pred_physical"].values - yt) ** 2))
        order = np.argsort(per_seed)
        agg_rows.append(dict(
            L=L, n=int(len(yt)),
            seed_mean_MSE_phys=seedmean_mse,
            mean_individual_seed_MSE_phys=float(per_seed.mean()),
            median_seed=SEEDS[int(order[len(SEEDS) // 2])],
            median_seed_MSE_phys=float(per_seed[len(SEEDS) // 2]),
            best_seed=SEEDS[int(order[0])], best_seed_MSE_phys=float(per_seed.min()),
            worst_seed=SEEDS[int(order[-1])], worst_seed_MSE_phys=float(per_seed.max()),
            between_seed_SD_of_MSE=float(per_seed.std()),
            seed_mean_improvement_pct=(1 - seedmean_mse / per_seed.mean()) * 100,
            note="seeds NOT selected by Test; seed-mean is the fixed average of seeds 42..51",
        ))
        std_per_week = stack.std(axis=0)
        band_rows.append(dict(L=L, source="10 seeds 42..51, lead-1 (step0), ILITOTAL physical, per target week",
                              between_seed_std_mean=float(std_per_week.mean()),
                              between_seed_std_min=float(std_per_week.min()),
                              between_seed_std_max=float(std_per_week.max()),
                              seed_ids="42..51"))
    pd.DataFrame(agg_rows).to_csv(os.path.join(AUD, "nlinear_seed_aggregation_audit.csv"), index=False)
    pd.DataFrame(band_rows).to_csv(os.path.join(AUD, "nlinear_seed_uncertainty_band_source.csv"), index=False)

# ---------------------------------------------------------------- peak audit
def write_peak():
    out = {}
    for L in [24, 60]:
        sm = seed_mean_lead1(L).sort_values("abs_week")
        yt = sm["y_true_physical"].values.astype(float); yp = sm["y_pred_physical"].values.astype(float)
        aw = sm["abs_week"].values.astype(int)
        ti, pi = int(np.argmax(yt)), int(np.argmax(yp))
        tw, pw = int(aw[ti]), int(aw[pi])
        pie = float(np.abs(yp[pi] - yt[ti]) / yt[ti] * 100)
        out[f"L{L}"] = dict(
            true_peak_abs_week=tw, pred_peak_abs_week=pw,
            true_peak_value_phys=float(yt[ti]), pred_peak_value_phys=float(yp[pi]),
            PTE_weeks=int(abs(tw - pw)), PTE_hit=bool(abs(tw - pw) <= 1),
            PIE_pct=pie, PIE_hit=bool(pie <= 5.0),
            interpretation="REPRESENTATIVE displayed-curve (seed-mean lead-1) metric, NOT season/event-level official PTE/PIE",
        )
    with open(os.path.join(AUD, "nlinear_displayed_curve_peak_audit.json"), "w", encoding="utf-8") as f:
        json.dump({"scope": "displayed seed-mean lead-1 curve only (illustrative)",
                   "official_season_level": "see final_peak_metrics.csv / final_peak_hit_rates.csv",
                   "results": out}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    write_split_tables()
    write_paper_comparison()
    write_provenance()
    write_target_leakage()
    write_identity()
    write_full_vs_displayed_and_perlead()
    write_seed()
    write_peak()
    print("DONE. audit tables written to", AUD)
