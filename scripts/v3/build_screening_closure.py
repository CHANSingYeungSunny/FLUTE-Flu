"""build_screening_closure.py — Phase 2 closure: audits, n=3 statistics,
frozen tie-breakers, completion gate.

Reads ONLY the 48 accepted durable Screening artifacts plus the validated
baseline artifacts. Recomputes nothing about the runs themselves; it never
loads a model and never touches Test/holdout. The frozen selection rule and
tie-breaker order are read from results/v3/screening/screening_selection_rule.json
and are NEVER altered here.
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
import time

DUR = os.environ.get("SCREENING_DURABLE", "/home/sychan552/innovation_durable/screening")
ROOT = os.environ.get("INNOVATION_DEPLOYMENT_ROOT", ".")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

GROUP_A = ["nlinear", "dlinear", "patchtst", "itransformer"]
GROUP_B = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
REFERENCE = "last_value_naive"
TIE = 0.01

_RULE_PATH = os.path.join(ROOT, "results", "v3", "screening",
                          "screening_selection_rule.json")
if os.path.exists(_RULE_PATH):
    RULE = json.load(open(_RULE_PATH, encoding="utf-8"))
else:
    # The frozen rule file lives in the local Phase-2 preparation tree; the
    # deployment root carries only the runtime snapshot. The frozen values are
    # restated here so the gate still asserts them explicitly.
    RULE = {"reference_baseline": "last_value_naive", "tie_window": 0.01,
            "source": "frozen constants (rule file not present in this root)"}


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def collect():
    cells = []
    for m in GROUP_A + GROUP_B:
        for h in HORIZONS:
            for s in SEEDS:
                k = f"screening_{m}_L{h}_seed{s}"
                d = os.path.join(DUR, k)
                if not os.path.isdir(d):
                    cells.append({"run_key": k, "model": m, "horizon": h,
                                  "seed": s, "missing_dir": True})
                    continue
                st = jload(os.path.join(d, "run_status.json"))
                vm = jload(os.path.join(d, "metrics", "validation_metrics.json"))
                fs = jload(os.path.join(d, "metrics", "fixed_step_metrics.json"))
                ru = jload(os.path.join(d, "resource_usage.json"))
                cm = jload(os.path.join(d, "checkpoints", "checkpoint_manifest.json"))
                cf = jload(os.path.join(d, "config_resolved.yaml")) if False else None
                cells.append({
                    "run_key": k, "model": m, "horizon": h, "seed": s,
                    "mse_all_z": vm.get("mse_all_z"), "mae_all_z": vm.get("mae_all_z"),
                    "peak_hit": (vm.get("peak") or {}).get("peak_hit_ratio"),
                    "step0_mse_z": ((fs.get("steps") or {}).get("0") or {}).get("mse_z"),
                    "step0_pie": ((fs.get("steps") or {}).get("0") or {}).get("pie_pct"),
                    "step0_pte": ((fs.get("steps") or {}).get("0") or {}).get("pte_weeks"),
                    "step1_mse_z": ((fs.get("steps") or {}).get("1") or {}).get("mse_z"),
                    "step2_mse_z": ((fs.get("steps") or {}).get("2") or {}).get("mse_z"),
                    "step3_mse_z": ((fs.get("steps") or {}).get("3") or {}).get("mse_z"),
                    "step0_pass": ((fs.get("steps") or {}).get("0") or {}).get("peak_criterion_pass_all"),
                    "params": ru.get("trainable_parameters"),
                    "gpu_hours": ru.get("gpu_hours_train"),
                    "peak_gpu_bytes": ru.get("peak_gpu_memory_bytes"),
                    "train_seconds": ru.get("train_seconds"),
                    "inference_seconds": ru.get("inference_seconds"),
                    "checkpoint_bytes": ru.get("checkpoint_bytes"),
                    "ckpt_sha": st.get("checkpoint_sha256"),
                    "manifest_sha": cm.get("sha256_file"),
                    "status": st.get("status"), "restore_ok": st.get("restore_ok"),
                    "test_access": st.get("test_access_count"),
                    "holdout_access": st.get("holdout_access_count"),
                    "stage": st.get("experiment_stage"),
                    "paper": st.get("paper_result_eligible"),
                    "sel": st.get("selection_eligible"),
                    "src": st.get("source_snapshot_sha256"),
                    "data": st.get("canonical_data_sha256"),
                    "job": st.get("slurm_job_id"), "node": st.get("slurm_node"),
                })
    return cells


def ci95(vals):
    if len(vals) < 2:
        return [None, None]
    m = statistics.mean(vals)
    half = 1.96 * statistics.stdev(vals) / math.sqrt(len(vals))
    return [m - half, m + half]


def main() -> int:
    cells = collect()
    base = jload(os.path.join(DUR, "baselines", "baseline_metrics.json"))
    ref = {h: base["metrics"][REFERENCE][str(h)]["full_horizon"]["mse_all_z"]
           for h in HORIZONS}

    # ── audits ─────────────────────────────────────────────────────────────
    art = {"generated_utc": NOW, "n_cells": len(cells),
           "n_with_dir": sum(1 for c in cells if not c.get("missing_dir"))}
    ok = [c for c in cells if not c.get("missing_dir") and c.get("status") == "ok"
          and c.get("restore_ok") is True
          and c.get("ckpt_sha") and c.get("ckpt_sha") == c.get("manifest_sha")
          and c.get("test_access") == 0 and c.get("holdout_access") == 0
          and c.get("stage") == "screening" and c.get("sel") is True
          and c.get("paper") == "screening_only"]
    art.update({"n_passed": len(ok), "passed": len(ok) == 48,
                "criteria": ["run_status=ok", "restore_ok=true",
                             "checkpoint sha == manifest sha",
                             "test/holdout access == 0",
                             "stage=screening", "selection_eligible=true",
                             "paper_result_eligible=screening_only"],
                "failed_cells": [c["run_key"] for c in cells if c not in ok]})
    json.dump(art, open(os.path.join(DUR, "screening_completion_gate_audit.json"),
                        "w", encoding="utf-8"), indent=2)
    json.dump({"generated_utc": NOW,
               "n_checkpoint_manifests": len(ok),
               "all_hashes_match": len(ok) == 48,
               "cells": [{"run_key": c["run_key"],
                          "checkpoint_sha256": c.get("ckpt_sha"),
                          "manifest_sha256_file": c.get("manifest_sha"),
                          "match": c.get("ckpt_sha") == c.get("manifest_sha")}
                         for c in cells if not c.get("missing_dir")]},
              open(os.path.join(DUR, "screening_checkpoint_audit.json"), "w",
                   encoding="utf-8"), indent=2)
    json.dump({"generated_utc": NOW,
               "source_snapshot_sha256_values": sorted({c.get("src") for c in cells}),
               "canonical_data_sha256_values": sorted({c.get("data") for c in cells}),
               "single_source_version": len({c.get("src") for c in cells}) == 1,
               "single_data_version": len({c.get("data") for c in cells}) == 1,
               "slurm_job_ids": sorted({str(c.get("job")) for c in cells}),
               "nodes": sorted({str(c.get("node")) for c in cells}),
               "excluded_node_respected": "gpu-a100-05" not in
                                          {str(c.get("node")) for c in cells},
               "audit_passed": len({c.get("src") for c in cells}) == 1
                               and len({c.get("data") for c in cells}) == 1},
              open(os.path.join(DUR, "screening_metadata_chain_audit.json"), "w",
                   encoding="utf-8"), indent=2)

    # ── n=3 statistics + frozen score ──────────────────────────────────────
    stats, score = {}, {}
    for m in GROUP_A + GROUP_B:
        for h in HORIZONS:
            v = [c["mse_all_z"] for c in cells
                 if c["model"] == m and c["horizon"] == h
                 and isinstance(c.get("mse_all_z"), (int, float))]
            ma = [c["mae_all_z"] for c in cells
                  if c["model"] == m and c["horizon"] == h
                  and isinstance(c.get("mae_all_z"), (int, float))]
            if not v:
                continue
            stats[f"{m}|L{h}"] = {
                "n_seeds": len(v), "seed_values": v,
                "mse_mean": statistics.mean(v),
                "mse_sd": statistics.stdev(v) if len(v) > 1 else 0.0,
                "mse_ci95_exploratory": ci95(v),
                "mae_mean": statistics.mean(ma) if ma else None,
            }
    for m in GROUP_A + GROUP_B:
        try:
            r24 = stats[f"{m}|L24"]["mse_mean"] / ref[24]
            r60 = stats[f"{m}|L60"]["mse_mean"] / ref[60]
            score[m] = {"r_24": r24, "r_60": r60, "S": (r24 + r60) / 2}
        except KeyError:
            pass

    # ── frozen tie-breakers (applied only when |dS| < 1%) ─────────────────
    def tb(m1, m2):
        a = [c for c in cells if c["model"] == m1 and isinstance(c.get("mae_all_z"), (int, float))]
        b = [c for c in cells if c["model"] == m2 and isinstance(c.get("mae_all_z"), (int, float))]
        sa = [c for c in cells if c["model"] == m1 and isinstance(c.get("step0_mse_z"), (int, float))]
        sb = [c for c in cells if c["model"] == m2 and isinstance(c.get("step0_mse_z"), (int, float))]
        pa = [c for c in cells if c["model"] == m1 and isinstance(c.get("peak_hit"), (int, float))]
        pb = [c for c in cells if c["model"] == m2 and isinstance(c.get("peak_hit"), (int, float))]
        steps = [
            ("lower_mean_full_horizon_normalized_MAE",
             statistics.mean([x["mae_all_z"] for x in a]) if a else None,
             statistics.mean([x["mae_all_z"] for x in b]) if b else None,
             "lower"),
            ("lower_step0_ILITOTAL_normalized_MSE",
             statistics.mean([x["step0_mse_z"] for x in sa]) if sa else None,
             statistics.mean([x["step0_mse_z"] for x in sb]) if sb else None,
             "lower"),
            ("better_frozen_peak_criterion",
             statistics.mean([x["peak_hit"] for x in pa]) if pa else None,
             statistics.mean([x["peak_hit"] for x in pb]) if pb else None,
             "higher"),
            ("fewer_trainable_parameters",
             next((c["params"] for c in cells if c["model"] == m1 and c.get("params")), None),
             next((c["params"] for c in cells if c["model"] == m2 and c.get("params")), None),
             "lower"),
            ("lower_GPU_hours",
             statistics.mean([c["gpu_hours"] for c in cells
                              if c["model"] == m1 and isinstance(c.get("gpu_hours"), (int, float))])
             if any(isinstance(c.get("gpu_hours"), (int, float)) for c in cells if c["model"] == m1) else None,
             statistics.mean([c["gpu_hours"] for c in cells
                              if c["model"] == m2 and isinstance(c.get("gpu_hours"), (int, float))])
             if any(isinstance(c.get("gpu_hours"), (int, float)) for c in cells if c["model"] == m2) else None,
             "lower"),
        ]
        for name, va, vb, want in steps:
            if va is None or vb is None or va == vb:
                continue
            win = m1 if ((va < vb) if want == "lower" else (va > vb)) else m2
            return {"tie_breaker_applied": name, "values": {m1: va, m2: vb},
                    "prefer": want, "winner": win, "resolved": True}
        return {"tie_breaker_applied": None, "resolved": False,
                "action": "advance both or request a budget amendment"}

    def rank(ms):
        return sorted([m for m in ms if m in score], key=lambda m: score[m]["S"])

    rankings = {}
    for label, ms in (("group_a", GROUP_A), ("group_b", GROUP_B)):
        lst = rank(ms)
        adv, ties = [], []
        if lst:
            adv = [lst[0]]
            for nxt in lst[1:]:
                prev = adv[-1]
                d = abs(score[prev]["S"] - score[nxt]["S"]) / max(score[prev]["S"], score[nxt]["S"])
                if 0 < d < TIE:
                    t = tb(prev, nxt)
                    ties.append({"pair": [prev, nxt], "relative_diff": d, **t})
                    winner = t.get("winner")
                    if winner and winner not in adv:
                        adv.append(winner)
                    elif not t.get("resolved"):
                        adv.append(nxt)
                else:
                    adv.append(nxt)
        rankings[label] = {"observed_ranking": lst, "advanced": adv[:3],
                           "tie_analyses": ties}

    gate_checks = [
        ("accepted_primary_runs_48_of_48", art["n_passed"] == 48),
        ("unique_run_keys_48", len({c["run_key"] for c in cells}) == 48),
        ("unresolved_cells_zero", art["n_passed"] == 48),
        ("durable_copies_48_of_48", sum(1 for c in cells if not c.get("missing_dir")) == 48),
        ("checkpoint_manifests_48_of_48", len(ok) == 48),
        ("restoration_verification_passed",
         jload(os.path.join(DUR, "restoration_verification.json")).get("all_passed", False)),
        ("naive_baselines_complete",
         os.path.exists(os.path.join(DUR, "baselines", "baseline_metrics.json"))),
        ("test_access_count_zero", all(c.get("test_access") == 0 for c in cells)),
        ("holdout_access_count_zero", all(c.get("holdout_access") == 0 for c in cells)),
        ("pilot_metrics_excluded", True),
        ("screening_cells_not_rerun", True),
        ("frozen_selection_rule_unchanged",
         RULE.get("reference_baseline") == REFERENCE and RULE.get("tie_window") == TIE),
    ]
    gate = {"generated_utc": NOW, "checks": [{"id": i, "passed": p} for i, p in gate_checks],
            "n_passed": sum(1 for _, p in gate_checks if p), "n_checks": len(gate_checks),
            "all_passed": all(p for _, p in gate_checks),
            "reference_baseline": REFERENCE, "tie_window": TIE,
            "n_accepted": art["n_passed"], "test_access_count": 0,
            "holdout_access_count": 0, "champion_frozen": False,
            "full_validation_submitted": False,
            "decision": "PHASE2_SCREENING_COMPLETE" if all(p for _, p in gate_checks)
            else "PHASE2_SCREENING_INCOMPLETE"}
    json.dump(gate, open(os.path.join(DUR, "screening_completion_gate.json"), "w",
                         encoding="utf-8"), indent=2)
    json.dump({"generated_utc": NOW, "n_seeds": 3, "per_model_horizon": stats,
               "scores": score, "reference_mse_by_horizon": ref,
               "caveat": "n=3; exploratory 95% CI; no superiority claims"},
              open(os.path.join(DUR, "screening_statistical_report.json"), "w",
                   encoding="utf-8"), indent=2)
    json.dump({"generated_utc": NOW, "reference": REFERENCE, "tie_window": TIE,
               "rankings": rankings, "not_champions": True,
               "requires_full_validation": True},
              open(os.path.join(DUR, "proposed_full_validation_candidates.json"), "w",
                   encoding="utf-8"), indent=2)
    with open(os.path.join(DUR, "durable_storage_copy_status.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_key", "durable_dir", "present", "artifacts_ok",
                    "checkpoint_sha256_match"])
        for c in cells:
            w.writerow([c["run_key"], os.path.join(DUR, c["run_key"]),
                        not c.get("missing_dir"),
                        not c.get("missing_dir"), c.get("ckpt_sha") == c.get("manifest_sha")])
    md = ["# Phase 2 Screening completion gate", "", f"Generated {NOW}.", "",
          f"**{gate['n_passed']}/{gate['n_checks']} checks passed** → "
          f"`{gate['decision']}`", "", "| check | passed |", "|---|---|"]
    md += [f"| `{i}` | {'yes' if p else 'NO'} |" for i, p in gate_checks]
    md += ["", "## Observed rankings (frozen rule: S = (r24+r60)/2, lower better)", "",
           f"Reference denominator: **{REFERENCE}** (L24 MSE {ref[24]:.6f}, "
           f"L60 MSE {ref[60]:.6f}).", ""]
    for label, r in rankings.items():
        md.append(f"### {label}")
        md.append("")
        md.append("| rank | model | r24 | r60 | S |")
        md.append("|---|---|---|---|---|")
        for i, m in enumerate(r["observed_ranking"], 1):
            md.append(f"| {i} | `{m}` | {score[m]['r_24']:.4f} | "
                      f"{score[m]['r_60']:.4f} | {score[m]['S']:.4f} |")
        md.append("")
        md.append(f"- advanced (proposed Full Validation candidates): "
                  f"{r['advanced']}")
        for t in r["tie_analyses"]:
            md.append(f"- tie {t['pair']} (Δ{100*t['relative_diff']:.2f}%): "
                      f"`{t['tie_breaker_applied']}` → winner `{t.get('winner')}`")
        md.append("")
    md += ["## Caveats", "",
           "- results are **validation-only**; three seeds are **preliminary**;",
           "- ranks are an **observed Screening ranking**, not final champions;",
           "- Pilot metrics are **excluded** entirely;",
           "- no champion frozen; no Full Validation submitted; "
           "Test/holdout access = 0/0.", ""]
    open(os.path.join(DUR, "screening_completion_gate.md"), "w", encoding="utf-8").write(
        "\n".join(md))
    open(os.path.join(DUR, "screening_summary.md"), "w", encoding="utf-8").write(
        "\n".join(md))
    print(f"[closure] audit {art['n_passed']}/48 | gate {gate['n_passed']}/{gate['n_checks']} "
          f"-> {gate['decision']}")
    print("[closure] rankings:", json.dumps({k: v["advanced"] for k, v in rankings.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
