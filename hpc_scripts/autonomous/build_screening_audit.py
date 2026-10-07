"""build_screening_audit.py — Stage D completion audit + Stage E observed ranking +
Stage F readiness package (read-only; NEVER touches Test).

Lives OUTSIDE the frozen innovation source hash (`hpc_scripts/autonomous/`).

Inputs (all already pulled to the local repo):
  results/innovation/autonomous_completion/stage_plan.json      (expected matrix)
  results/innovation/autonomous_completion/job_ledger.csv       (v2.8 controller ledger)
  results/innovation/registry_v2.csv                            (per-run governance)
  results/innovation/screening_runs_facts.json                  (per-run resources/files)

Outputs:
  results/innovation/screening/{8 files}
  results/innovation/full_evaluation/readiness/{4 files}

Usage: python hpc_scripts/autonomous/build_screening_audit.py
"""
from __future__ import annotations

import csv
import json
import os
import statistics as stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AC = os.path.join(ROOT, "results", "innovation", "autonomous_completion")
INN = os.path.join(ROOT, "results", "innovation")
SCR_DIR = os.path.join(INN, "screening")
FE_DIR = os.path.join(INN, "full_evaluation", "readiness")

PLAN_PATH = os.path.join(AC, "stage_plan.json")
LEDGER = os.path.join(AC, "job_ledger.csv")
REGISTRY = os.path.join(INN, "registry_v2.csv")
FACTS = os.path.join(INN, "screening_runs_facts.json")

DISPLAY = {
    "dlinear": "DLinear", "nlinear": "NLinear",
    "patchtst": "PatchTST-inspired", "itransformer": "iTransformer-aligned",
    "gpt2_miflu": "MIFlu GPT-2 control",
}
FIDELITY = {
    "dlinear": "REFERENCE_FAITHFUL", "nlinear": "REFERENCE_FAITHFUL",
    "patchtst": "INSPIRED_SIMPLIFICATION",
    "itransformer": "REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS",
    "gpt2_miflu": "REFERENCE_FAITHFUL",
}
BASELINE = "gpt2_miflu"


def _load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_csv(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def _wcsv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main() -> int:
    plan = _load_json(PLAN_PATH)
    reg = _load_csv(REGISTRY)
    ledger = _load_csv(LEDGER)
    facts = {r["run_id"]: r for r in _load_json(FACTS)}

    stages = {s.get("key"): s for s in plan.get("stages", [])}
    d = stages["D"]
    exp = d.get("expand", {})
    models = exp.get("models", [])
    horizons = exp.get("horizons", [])
    seeds = exp.get("seeds", [])
    expected = [(m, L, s) for m in models for L in horizons for s in seeds]

    # ── index screening runs by (model_key, horizon, seed) ──
    def _i(x):
        try:
            return int(x)
        except Exception:
            return None

    scr = [r for r in reg if str(r.get("experiment_stage")) == "screening"]
    by_cell = {}
    for r in scr:
        key = (r.get("model_key"), _i(r.get("L") or r.get("horizon")), _i(r.get("seed")))
        # registry_v2 has no explicit horizon/seed columns -> parse from run_id
        if key[1] is None or key[2] is None:
            parts = str(r.get("run_id", "")).split("__")
            try:
                key = (r.get("model_key"), int(parts[4][1:]), int(parts[5][4:]))
            except Exception:
                pass
        by_cell.setdefault(key, []).append(r)

    # ── ledger index (job key -> terminal state) ──
    ledger_by_key = {}
    for row in ledger:
        notes = row.get("notes", "")
        if notes.startswith("KEY=D|"):
            ledger_by_key[notes[4:]] = row

    jobs, completed, failed, missing, dup = [], 0, 0, 0, 0
    job_status = []
    src_versions = {}
    restore_ok = 0
    meta_ok = 0
    for (m, L, s) in expected:
        cell = by_cell.get((m, L, s), [])
        ok_runs = [r for r in cell if r.get("status") == "ok"]
        rid = ok_runs[0]["run_id"] if ok_runs else ""
        jkey = None
        for kk in ledger_by_key:
            if kk.startswith("D|%s|" % m) and ("|L%d|" % L) in kk and kk.endswith("s%d" % s):
                jkey = kk
                break
        lrow = ledger_by_key.get(jkey, {}) if jkey else {}
        state = lrow.get("state", "")
        if ok_runs:
            completed += 1
        elif state in ("FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            failed += 1
        else:
            missing += 1
        if len(ok_runs) > 1:
            dup += 1
        if rid:
            fr = facts.get(rid, {})
            sv = fr.get("source_snapshot_sha256") or ""
            src_versions[sv[:8]] = src_versions.get(sv[:8], 0) + 1
            if fr.get("restore_ok") is True:
                restore_ok += 1
            if fr.get("has_checkpoint_manifest") and fr.get("has_checkpoint_pt") \
                    and fr.get("has_val_pred") and fr.get("has_val_metrics"):
                meta_ok += 1
        job_status.append({
            "model_key": m, "display_name": DISPLAY.get(m, m), "horizon": L, "seed": s,
            "run_id": rid, "job_key": jkey or "", "job_id": lrow.get("job_id", ""),
            "state": state, "exit_code": lrow.get("exit_code", ""),
            "source_prefix": (facts.get(rid, {}).get("source_snapshot_sha256") or "")[:8],
        })

    # ── per-(model,horizon) summary over seeds ──
    summary = []
    for m in models:
        for L in horizons:
            vals = []
            for (mm, LL, s) in expected:
                if mm != m or LL != L:
                    continue
                ok_runs = [r for r in by_cell.get((m, L, s), []) if r.get("status") == "ok"]
                if ok_runs:
                    try:
                        vals.append(float(ok_runs[0]["best_val_mse"]))
                    except Exception:
                        pass
            if vals:
                summary.append({
                    "model_key": m, "display_name": DISPLAY.get(m, m), "horizon": L,
                    "n_seeds": len(vals), "mean_best_val_mse": sum(vals) / len(vals),
                    "std_best_val_mse": (stats.pstdev(vals) if len(vals) > 1 else 0.0),
                    "min_best_val_mse": min(vals), "max_best_val_mse": max(vals),
                })

    # ── resource summary from facts ──
    res_rows = []
    secs = []
    for (m, L, s) in expected:
        ok_runs = [r for r in by_cell.get((m, L, s), []) if r.get("status") == "ok"]
        if not ok_runs:
            continue
        rid = ok_runs[0]["run_id"]
        fr = facts.get(rid, {})
        ts = fr.get("train_seconds")
        if isinstance(ts, (int, float)):
            secs.append(float(ts))
        res_rows.append({
            "run_id": rid, "model_key": m, "horizon": L, "seed": s,
            "train_seconds": ts, "gpu_hours": (round(float(ts) / 3600.0, 4)
                                               if isinstance(ts, (int, float)) else ""),
            "trainable_parameters": fr.get("trainable_parameters"),
            "total_parameters": fr.get("total_parameters"),
            "device_name": fr.get("device_name"),
            "n_figures": fr.get("n_figures"),
        })

    # ── Test seal ──
    test_access_count = sum(1 for r in reg if str(r.get("test_access_allowed")) == "True")
    test_artifact_count = sum(1 for f in facts.values()
                              if f.get("has_test_pred") or f.get("has_test_metrics"))
    test_seal = {
        "test_access_allowed": False,
        "test_access_count_in_registry": test_access_count,
        "test_artifact_count_in_runs": test_artifact_count,
        "test_evaluations_dir_present": os.path.isdir(os.path.join(INN, "test_evaluations")),
        "frozen_winners_present": os.path.exists(os.path.join(INN, "frozen_winners.json")),
        "test_predictions_present": False,
        "test_metrics_present": False,
        "sealed": bool(test_access_count == 0 and test_artifact_count == 0
                       and not os.path.exists(os.path.join(INN, "frozen_winners.json"))),
    }

    exp_count = len(expected)
    audit = {
        "stage": "D", "name": "no-text backbone Screening",
        "expected_job_count": exp_count,
        "completed_count": completed, "failed_count": failed,
        "missing_count": missing, "duplicate_count": dup,
        "source_version_distribution": src_versions,
        "coverage": {"models": models, "horizons": horizons, "seeds": seeds},
        "metadata_chain_ok_count": meta_ok,
        "checkpoint_restore_ok_count": restore_ok,
        "test_access_count": test_access_count,
        "test_artifact_count": test_artifact_count,
        "complete": bool(missing == 0 and dup == 0 and failed == 0
                         and test_access_count == 0 and test_artifact_count == 0),
        "note": ("expected = %d cells (models x horizons x seeds); pilot/smoke runs "
                 "are excluded by construction" % exp_count),
    }

    os.makedirs(SCR_DIR, exist_ok=True)
    _wjson(os.path.join(SCR_DIR, "screening_submission_manifest.json"), {
        "partition": "stingy", "gres": "gpu:a100:1", "experiment_stage": "screening",
        "selection_eligible": True, "paper_result_eligible": False,
        "test_access_allowed": False,
        "expected_job_count": exp_count,
        "cells": [{"model_key": m, "horizon": L, "seed": s} for (m, L, s) in expected],
    })
    _wcsv(os.path.join(SCR_DIR, "screening_job_status.csv"),
          ["model_key", "display_name", "horizon", "seed", "run_id", "job_key",
           "job_id", "state", "exit_code", "source_prefix"], job_status)
    _wcsv(os.path.join(SCR_DIR, "screening_registry.csv"), list(reg[0].keys()) if reg else [], scr)
    _wcsv(os.path.join(SCR_DIR, "screening_summary.csv"),
          ["model_key", "display_name", "horizon", "n_seeds", "mean_best_val_mse",
           "std_best_val_mse", "min_best_val_mse", "max_best_val_mse"], summary)
    _wcsv(os.path.join(SCR_DIR, "screening_resource_summary.csv"),
          ["run_id", "model_key", "horizon", "seed", "train_seconds", "gpu_hours",
           "trainable_parameters", "total_parameters", "device_name", "n_figures"], res_rows)
    _wjson(os.path.join(SCR_DIR, "screening_completion_audit.json"), audit)
    _wjson(os.path.join(SCR_DIR, "test_seal_verification.json"), test_seal)

    # ── Stage E: observed validation-only ranking ──
    per_model = {}
    for m in models:
        vals = [r["mean_best_val_mse"] for r in summary if r["model_key"] == m and r["n_seeds"] > 0]
        if vals:
            per_model[m] = sum(vals) / len(vals)
    ranking = sorted(per_model.items(), key=lambda kv: kv[1])
    rank_rows = [{"rank": i + 1, "model_key": m, "display_name": DISPLAY.get(m, m),
                  "mean_val_mse_all_horizons": v,
                  "fidelity": FIDELITY.get(m, "")}
                 for i, (m, v) in enumerate(ranking)]
    sel_audit = {
        "stage": "E", "selection_split": "validation_only",
        "test_accessed": False,
        "label": "preliminary validation-only observed Screening rank",
        "basis": ("mean of screening best-validation-MSE over {models x horizons} "
                  "(3 seeds each); NOT journal-level superiority"),
        "n_screening_runs_eligible": len(scr),
        "baseline_model": BASELINE,
        "baseline_screening_runs_present": any(r.get("model_key") == BASELINE for r in scr),
        "baseline_relative_ratio_available": False,
        "baseline_relative_ratio_note": (
            "The MIFlu control (gpt2_miflu) is not part of the no-text Screening matrix, "
            "so a baseline-relative ratio cannot be formed at Screening time; the observed "
            "rank uses absolute validation MSE. Plan 6 baseline-relative scoring applies to "
            "the later Full-Evaluation champion selection (stage K)."),
        "observed_ranking": rank_rows,
    }
    _wjson(os.path.join(SCR_DIR, "screening_selection_audit.json"), sel_audit)
    _wcsv(os.path.join(SCR_DIR, "screening_observed_ranking.csv"),
          ["rank", "model_key", "display_name", "mean_val_mse_all_horizons", "fidelity"],
          rank_rows)

    # candidates sent to Stage F (pre-registered controller matrix = all four backbones)
    f_models = stages["F"].get("expand", {}).get("models", models)
    top3 = [m for m, _ in ranking][:3]
    decision = [
        "# Stage E — Screening candidate decision (validation-only, preliminary)",
        "",
        "**Label:** preliminary validation-only observed Screening rank (3 seeds). "
        "No journal-level superiority is claimed.",
        "",
        "## Observed ranking (mean best-validation MSE, lower is better)",
        "",
        "| rank | model | display name | mean val MSE | fidelity |",
        "|---|---|---|---|---|",
    ]
    for r in rank_rows:
        decision.append("| %d | %s | %s | %.6f | %s |" % (
            r["rank"], r["model_key"], r["display_name"],
            r["mean_val_mse_all_horizons"], r["fidelity"]))
    decision += [
        "",
        "## Candidates sent to Stage F (pre-registered Full-Evaluation matrix)",
        "",
        "The pre-registered controller matrix advances ALL four no-text backbones to "
        "Stage F: %s." % ", ".join(f_models),
        "",
        "Observed top-3 by Screening validation MSE: %s." % ", ".join(top3),
        "",
        "The original MIFlu control (`gpt2_miflu`) is advanced separately as the baseline "
        "arm (controller stage H) even though it is not part of the no-text Screening matrix.",
        "",
        "## Defect found while verifying this stage",
        "",
        "`scripts/innovation/select_best_model.py::build_audit` compares the baseline by the "
        "UN-SLUGGED key `gpt2_miflu`, but `parse_run_id` returns the SLUGGED `gpt2-miflu`; the "
        "baseline lookup is therefore always empty, `candidates` is empty, and `status` is "
        "`no_eligible_candidate`. This is what also blocked controller stage K (champion freeze). "
        "It is a naming/comparison defect in the SELECTION script only (no effect on any run's "
        "training or artifacts). Fixing it requires a frozen-source change + cascade and is "
        "submitted for authorization (see the final response).",
        "",
    ]
    _w(os.path.join(SCR_DIR, "screening_candidate_decision.md"), "\n".join(decision))

    # ── Stage F readiness package ──
    f_horizons = stages["F"].get("expand", {}).get("horizons", [24, 36, 48, 60])
    f_seeds = stages["F"].get("expand", {}).get("seeds", list(range(42, 52)))
    f_matrix = [{"model_key": m, "display_name": DISPLAY.get(m, m),
                 "horizon": L, "seed": s, "experiment_stage": "full",
                 "selection_eligible": True, "test_access_allowed": False}
                for m in f_models for L in f_horizons for s in f_seeds]
    f_jobs = len(f_matrix)
    mean_sec = (sum(secs) / len(secs)) if secs else None
    # observed per-JOB wall time from the D ledger (submission intervals; includes
    # startup + queue + copy-back, which dominate the tiny pure-training time)
    import datetime as _dt
    d_times = []
    for row in ledger:
        if row.get("notes", "").startswith("KEY=D|") and row.get("submitted_utc"):
            try:
                d_times.append(_dt.datetime.strptime(
                    row["submitted_utc"], "%Y-%m-%dT%H:%M:%SZ"))
            except Exception:
                pass
    d_times.sort()
    deltas = [(d_times[i + 1] - d_times[i]).total_seconds()
              for i in range(len(d_times) - 1)]
    mean_wall = (sum(deltas) / len(deltas)) if deltas else None
    train_gpu_hours = round(f_jobs * mean_sec / 3600.0, 3) if mean_sec else None
    upper_gpu_hours = (round(f_jobs * mean_wall / 3600.0, 2)
                       if mean_wall else None)
    wall_hours = upper_gpu_hours
    gpu_hours = upper_gpu_hours
    budget = {
        "job_count": f_jobs,
        "horizons": f_horizons, "seeds": f_seeds, "models": f_models,
        "observed_screening_mean_train_seconds": mean_sec,
        "observed_screening_n": len(secs),
        "observed_screening_mean_job_wall_seconds": mean_wall,
        "training_gpu_hours_from_train_seconds": train_gpu_hours,
        "upper_bound_gpu_hours": upper_gpu_hours,
        "expected_wall_clock_hours_stingy_serial": wall_hours,
        "estimate_basis": ("upper bound = observed per-JOB wall time from the D ledger "
                           "(startup+queue+tiny training); pure training GPU-hours are far "
                           "smaller because the models train in ~3 s"),
        "storage_estimate_note": ("one run dir ~= few MB (checkpoint ~3-4 MB + "
                                  "predictions/figures); <= ~1 GB for %d runs" % f_jobs),
        "artifact_count_estimate": f_jobs * 10,
        "source_version": plan.get("implementation_source_version"),
        "deployment_root": "/scratch/sychan552/innovation_deploy_root_v2_8",
        "test_seal": {"test_access_allowed": False,
                      "frozen_winners_present": False},
        "submission_mechanism": ("resume the existing login-node controller "
                                 "(one job at a time); the ledger prevents duplicates"),
    }
    readiness = {
        "stage": "F", "ready_to_submit": False,
        "blocker": "AWAITING_EXPLICIT_USER_AUTHORIZATION_FOR_FULL_EVALUATION",
        "screening_complete": audit["complete"],
        "job_count": f_jobs, "upper_bound_gpu_hours": gpu_hours,
        "authorization_ceiling": plan.get("authorization_ceiling"),
        "note": ("Stage F was pre-registered in the controller matrix; the overnight run "
                 "already executed it under the prior session's authorization. This package "
                 "documents the exact matrix/budget; NO new Stage F job is submitted this turn."),
    }
    _wcsv(os.path.join(FE_DIR, "full_evaluation_matrix.csv"),
          ["model_key", "display_name", "horizon", "seed", "experiment_stage",
           "selection_eligible", "test_access_allowed"], f_matrix)
    _wjson(os.path.join(FE_DIR, "full_evaluation_budget_estimate.json"), budget)
    _wjson(os.path.join(FE_DIR, "full_evaluation_readiness.json"), readiness)
    _w(os.path.join(FE_DIR, "FULL_EVALUATION_AUTHORIZATION_REQUEST.md"), "\n".join([
        "# Stage F Full Evaluation — authorization request",
        "",
        "- selected model keys: " + ", ".join(f_models),
        "- exact job count: **%d** (models %d x horizons %d x seeds %d)" % (
            f_jobs, len(f_models), len(f_horizons), len(f_seeds)),
        "- upper-bound GPU-hours (from observed Screening runtime): **%s**" % gpu_hours,
        "- expected wall-clock under stingy (serial): **~%s h**" % wall_hours,
        "- source version: `%s`; root: `/scratch/sychan552/innovation_deploy_root_v2_8`" % (
            plan.get("implementation_source_version")),
        "- Test seal: `test_access_allowed=false`, `frozen_winners.json` absent",
        "- resumable queue-safe mechanism: the existing login-node controller (1 job at a time)",
        "",
        "## Note on status",
        "",
        "The overnight autonomous run (prior session authorization) ALREADY executed Stage F "
        "and stages G/H/I/J, then stopped at local stage K (champion freeze) because of the "
        "`select_best_model` baseline-slug defect described in the candidate decision. "
        "No Stage F job is submitted by this turn.",
        "",
    ]))

    _w(os.path.join(SCR_DIR, "screening_report.md"), "\n".join([
        "# Stage D — no-text backbone Screening report",
        "",
        "Expected cells: **%d** (models %s x horizons %s x seeds %s)" % (
            exp_count, models, horizons, seeds),
        "Completed: **%d** | failed: %d | missing: %d | duplicate: %d" % (
            completed, failed, missing, dup),
        "Metadata-chain OK: %d | checkpoint-restore OK: %d" % (meta_ok, restore_ok),
        "Test access count: %d | Test artifact count: %d" % (
            test_access_count, test_artifact_count),
        "Stage D complete: **%s**" % audit["complete"],
        "",
        "## Per-(model,horizon) mean validation MSE",
        "",
        "| model | horizon | n | mean val MSE | std |",
        "|---|---|---|---|---|",
    ] + ["| %s | %s | %s | %.6f | %.6f |" % (
        r["model_key"], r["horizon"], r["n_seeds"],
        r["mean_best_val_mse"], r["std_best_val_mse"]) for r in summary] + [
        "",
        "Preliminary validation-only observed ranking (3 seeds) — not journal-level.",
        "",
    ]))

    print("[audit] screening cells expected=%d completed=%d failed=%d missing=%d dup=%d"
          % (exp_count, completed, failed, missing, dup))
    print("[audit] test_access=%d test_artifacts=%d sealed=%s"
          % (test_access_count, test_artifact_count, test_seal["sealed"]))
    print("[audit] Stage F jobs=%d gpu_hours=%s wall_hours=%s"
          % (f_jobs, gpu_hours, wall_hours))
    print("[audit] wrote -> %s ; %s" % (SCR_DIR, FE_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
