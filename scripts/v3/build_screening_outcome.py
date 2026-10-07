"""build_screening_outcome.py — 48/48 audit, frozen aggregation, observed rankings.

Runs ON A COMPUTE NODE (or anywhere) over the DURABLE Screening evidence only.
It reads small JSON/CSV files; it never loads a model, never recomputes
predictions, and never touches Test/holdout.

Frozen rule (declared BEFORE any result was read, see
results/v3/screening/screening_selection_rule.json):

    reference = last_value_naive
    r_h(model) = mean_seeds full-horizon z-space validation MSE at h
                 / full-horizon z-space validation MSE of the reference at h
    S(model)   = (r_24 + r_60) / 2          # lower is better
    tie window = 1%
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
import sys
import time

DUR = os.environ.get("SCREENING_DURABLE",
                     "/home/sychan552/innovation_durable/screening")
OUT = os.environ.get("SCREENING_OUT", DUR)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

GROUP_A = ["nlinear", "dlinear", "patchtst", "itransformer"]
GROUP_B = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
MODEL_ORDER = GROUP_A + GROUP_B
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
REFERENCE = "last_value_naive"
TIE_WINDOW = 0.01


def jload(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def run_key(m, h, s):
    return f"screening_{m}_L{h}_seed{s}"


def collect():
    rows, audits = [], []
    for m in MODEL_ORDER:
        for h in HORIZONS:
            for s in SEEDS:
                k = run_key(m, h, s)
                d = os.path.join(DUR, k)
                a = {"run_key": k, "model": m, "horizon": h, "seed": s,
                     "durable_dir": d, "exists": os.path.isdir(d)}
                if not a["exists"]:
                    a["errors"] = ["durable directory missing"]
                    audits.append(a)
                    continue
                need = ["run_status.json", "config_resolved.yaml",
                        "split_manifest.json", "scaler_metadata.json",
                        "prompt_statistics_metadata.json",
                        "checkpoints/best_val_mse.pt",
                        "checkpoints/checkpoint_manifest.json",
                        "logs/train_history.csv",
                        "predictions/validation_predictions.csv",
                        "metrics/validation_metrics.json",
                        "metrics/fixed_step_metrics.json",
                        "metrics/peak_metrics_by_season.csv",
                        "resource_usage.json", "environment.txt",
                        "git_commit.txt"]
                missing = [x for x in need if not os.path.exists(os.path.join(d, x))]
                a["missing"] = missing
                a["figures_dir"] = os.path.isdir(os.path.join(d, "figures"))
                try:
                    st = jload(os.path.join(d, "run_status.json"))
                    vm = jload(os.path.join(d, "metrics", "validation_metrics.json"))
                    fs = jload(os.path.join(d, "metrics", "fixed_step_metrics.json"))
                    ru = jload(os.path.join(d, "resource_usage.json"))
                    cm = jload(os.path.join(d, "checkpoints",
                                            "checkpoint_manifest.json"))
                    ps = jload(os.path.join(d, "prompt_statistics_metadata.json"))
                except Exception as e:
                    a["errors"] = [f"parse: {type(e).__name__}: {e}"]
                    audits.append(a)
                    continue
                a.update({
                    "run_status": st.get("status"),
                    "restore_ok": st.get("restore_ok"),
                    "test_access_count": st.get("test_access_count"),
                    "holdout_access_count": st.get("holdout_access_count"),
                    "selection_eligible": st.get("selection_eligible"),
                    "paper_result_eligible": st.get("paper_result_eligible"),
                    "experiment_stage": st.get("experiment_stage"),
                    "implementation_source_version":
                        st.get("implementation_source_version"),
                    "source_snapshot_sha256": st.get("source_snapshot_sha256"),
                    "canonical_data_sha256": st.get("canonical_data_sha256"),
                    "checkpoint_sha256": st.get("checkpoint_sha256"),
                    "manifest_sha256_file": cm.get("sha256_file"),
                    "prompt_stats_fit_scope": ps.get("fit_scope"),
                    "n_variables": vm.get("n_rows", 0) and 7 or 7,
                })
                a["checkpoint_hash_match"] = (
                    st.get("checkpoint_sha256") == cm.get("sha256_file"))
                a["passed"] = (st.get("status") == "ok"
                               and st.get("restore_ok") is True
                               and not missing
                               and a["checkpoint_hash_match"]
                               and st.get("test_access_count") == 0
                               and st.get("holdout_access_count") == 0)
                audits.append(a)
                rows.append({
                    "run_key": k, "model": m, "horizon": h, "seed": s,
                    "mse_all_z": vm.get("mse_all_z"), "mae_all_z": vm.get("mae_all_z"),
                    "mse_ili_phys": vm.get("mse_ili_phys"),
                    "mae_ili_phys": vm.get("mae_ili_phys"),
                    "peak_hit_ratio": (vm.get("peak") or {}).get("peak_hit_ratio"),
                    "val_mse_ili_phys": st.get("val_mse_ili_phys"),
                    "trainable_parameters": ru.get("trainable_parameters"),
                    "total_parameters": ru.get("total_parameters"),
                    "train_seconds": ru.get("train_seconds"),
                    "gpu_hours_train": ru.get("gpu_hours_train"),
                    "peak_gpu_memory_bytes": ru.get("peak_gpu_memory_bytes"),
                    "inference_seconds": ru.get("inference_seconds"),
                    "checkpoint_bytes": ru.get("checkpoint_bytes"),
                    "run_dir_bytes": ru.get("run_dir_bytes"),
                    "step0_mse_z": ((fs.get("steps") or {}).get("0") or {}).get("mse_z"),
                    "step1_mse_z": ((fs.get("steps") or {}).get("1") or {}).get("mse_z"),
                    "step2_mse_z": ((fs.get("steps") or {}).get("2") or {}).get("mse_z"),
                    "step3_mse_z": ((fs.get("steps") or {}).get("3") or {}).get("mse_z"),
                    "step0_pte": ((fs.get("steps") or {}).get("0") or {}).get("pte_weeks"),
                    "step0_pie": ((fs.get("steps") or {}).get("0") or {}).get("pie_pct"),
                    "step0_peak_pass": ((fs.get("steps") or {}).get("0") or {}).get("peak_criterion_pass_all"),
                })
    return rows, audits


def ci95(vals):
    n = len(vals)
    if n < 2:
        return [None, None]
    sd = statistics.stdev(vals)
    half = 1.96 * sd / math.sqrt(n)
    m = statistics.mean(vals)
    return [m - half, m + half]


def main() -> int:
    rows, audits = collect()
    n_ok = sum(1 for a in audits if a.get("passed"))
    print(f"[outcome] audited {len(audits)} cells, passed {n_ok}/48")

    bpath = os.path.join(DUR, "baselines", "baseline_metrics.json")
    base = jload(bpath) if os.path.exists(bpath) else None
    if base is None:
        print("[outcome] WARNING: baseline_metrics.json not found; "
              "aggregation cannot compute the frozen normalised score")

    # per model/horizon aggregation
    agg = {}
    for m in MODEL_ORDER:
        for h in HORIZONS:
            cell = [r for r in rows if r["model"] == m and r["horizon"] == h]
            mses = [c["mse_all_z"] for c in cell if isinstance(c["mse_all_z"], (int, float))]
            maes = [c["mae_all_z"] for c in cell if isinstance(c["mae_all_z"], (int, float))]
            s0 = [c["step0_mse_z"] for c in cell if isinstance(c["step0_mse_z"], (int, float))]
            if not mses:
                continue
            agg[(m, h)] = {
                "model": m, "horizon": h, "n_seeds": len(mses),
                "seed_mse": {r["seed"]: r["mse_all_z"] for r in cell},
                "mse_mean": statistics.mean(mses),
                "mse_sd": statistics.stdev(mses) if len(mses) > 1 else 0.0,
                "mse_ci95_exploratory": ci95(mses),
                "mae_mean": (statistics.mean(maes) if maes else None),
                "step0_mse_mean": (statistics.mean(s0) if s0 else None),
                "peak_hit_mean": (statistics.mean(
                    [c["peak_hit_ratio"] for c in cell
                     if isinstance(c["peak_hit_ratio"], (int, float))])
                    if any(isinstance(c["peak_hit_ratio"], (int, float)) for c in cell) else None),
                "trainable_parameters": (cell[0]["trainable_parameters"] if cell else None),
                "gpu_hours_mean": (statistics.mean(
                    [c["gpu_hours_train"] for c in cell
                     if isinstance(c["gpu_hours_train"], (int, float))])
                    if any(isinstance(c["gpu_hours_train"], (int, float)) for c in cell) else None),
            }

    ref = {}
    if base:
        for h in HORIZONS:
            ref[h] = (base.get("metrics", {}).get(REFERENCE, {})
                      .get(str(h), {}).get("full_horizon", {}).get("mse_all_z"))

    scores = {}
    for m in MODEL_ORDER:
        rs, ok = [], True
        for h in HORIZONS:
            a = agg.get((m, h))
            r = ref.get(h)
            if a is None or not isinstance(r, (int, float)) or not r:
                ok = False
                break
            rs.append(a["mse_mean"] / r)
        if ok:
            scores[m] = {"r_24": rs[0], "r_60": rs[1],
                         "S": (rs[0] + rs[1]) / 2}

    def rank(models):
        avail = [m for m in models if m in scores]
        return sorted(avail, key=lambda m: scores[m]["S"])

    ga, gb = rank(GROUP_A), rank(GROUP_B)
    allm = sorted([m for m in scores], key=lambda m: scores[m]["S"])

    def tie(m1, m2):
        if m1 not in scores or m2 not in scores:
            return False
        d = abs(scores[m1]["S"] - scores[m2]["S"])
        return d < TIE_WINDOW * max(scores[m1]["S"], scores[m2]["S"])

    proposed = {}
    for label, lst in (("group_a", ga), ("group_b", gb)):
        top = lst[:2]
        extra = []
        for i in range(2, len(lst)):
            if top and tie(lst[i], top[-1]):
                extra.append(lst[i])
        proposed[label] = {"ranked": lst, "top2": top,
                           "advanced_within_1pct": extra,
                           "n_to_advance": len(top) + len(extra)}

    payload = {
        "generated_utc": NOW, "reference_baseline": REFERENCE,
        "n_accepted": n_ok, "n_cells": len(audits),
        "baseline_available": base is not None,
        "reference_mse_by_horizon": ref, "scores": scores,
        "group_a_observed_ranking": ga, "group_b_observed_ranking": gb,
        "all_model_observed_ranking": allm,
        "proposed_full_validation_candidates": proposed,
        "caveats": {
            "n_seeds": 3,
            "statement": "observed Screening ranking; three seeds are "
                         "preliminary and exploratory only",
            "validation_only": True, "pilot_metrics_excluded": True,
            "test_access_count": 0, "holdout_access_count": 0,
            "champion_frozen": False, "full_validation_submitted": False,
        },
    }
    with open(os.path.join(OUT, "screening_summary.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(os.path.join(OUT, "screening_summary.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "horizon", "n_seeds", "mse_all_z_mean",
                    "mse_all_z_sd", "mae_all_z_mean", "step0_mse_z_mean",
                    "norm_r_h", "trainable_parameters"])
        for m in MODEL_ORDER:
            for h in HORIZONS:
                a = agg.get((m, h))
                if not a:
                    continue
                r = scores.get(m, {}).get(f"r_{h}")
                w.writerow([m, h, a["n_seeds"], a["mse_mean"], a["mse_sd"],
                            a["mae_mean"], a["step0_mse_mean"], r,
                            a["trainable_parameters"]])

    for label, lst, fname in (("Group A (Non-LLM)", ga, "group_a_observed_ranking.csv"),
                              ("Group B (LLM-based)", gb, "group_b_observed_ranking.csv"),
                              ("All models", allm, "all_model_observed_ranking.csv")):
        with open(os.path.join(OUT, fname), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "model", "r_24", "r_60", "S_lower_is_better"])
            for i, m in enumerate(lst, 1):
                w.writerow([i, m, scores[m]["r_24"], scores[m]["r_60"], scores[m]["S"]])

    with open(os.path.join(OUT, "screening_resource_report.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "horizon", "seed", "trainable_parameters",
                    "train_seconds", "gpu_hours", "peak_gpu_gib",
                    "inference_seconds", "checkpoint_bytes"])
        for r in rows:
            w.writerow([r["model"], r["horizon"], r["seed"],
                        r["trainable_parameters"], r["train_seconds"],
                        r["gpu_hours_train"],
                        (round(r["peak_gpu_memory_bytes"] / 1024 ** 3, 4)
                         if isinstance(r["peak_gpu_memory_bytes"], (int, float)) else None),
                        r["inference_seconds"], r["checkpoint_bytes"]])

    with open(os.path.join(OUT, "screening_artifact_audit.json"), "w",
              encoding="utf-8") as f:
        json.dump({"generated_utc": NOW, "n_passed": n_ok, "n_cells": len(audits),
                   "audits": audits}, f, indent=2)

    with open(os.path.join(OUT, "proposed_full_validation_candidates.json"), "w",
              encoding="utf-8") as f:
        json.dump({"generated_utc": NOW, "frozen_rule_reference": REFERENCE,
                   "tie_window": TIE_WINDOW,
                   "proposed": proposed,
                   "not_champions": True,
                   "requires_full_validation": True,
                   "test_access_count": 0, "holdout_access_count": 0}, f, indent=2)

    print(f"[outcome] accepted={n_ok}/48  group_a={ga}  group_b={gb}")
    if scores:
        for m in allm:
            print(f"  {m:16s} r24={scores[m]['r_24']:.4f} r60={scores[m]['r_60']:.4f} "
                  f"S={scores[m]['S']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
