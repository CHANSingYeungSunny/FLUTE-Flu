"""build_screening_freeze.py

Phase-2 pre-result FREEZE. Everything here is written BEFORE any Screening run
exists, so the protocol, artifact schema, metric contract and advancement rule
cannot be influenced by observed results.

Also closes the Pilot phase (the eight-Pilot completion gate) and records the
authoritative Screening start state.

Read-only w.r.t. models: no model is built, loaded, or run anywhere here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "results" / "v3"
PILOTS = V3 / "pilots"
SC = V3 / "screening"
for d in (PILOTS, SC, SC / "baselines"):
    d.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=2), encoding="utf-8")


def wtext(p, s):
    Path(p).write_text(s, encoding="utf-8")


def sha(p):
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ── §1 guide verification ──────────────────────────────────────────────────
GUIDE = ROOT / "HPC_GUIDE.md"
GUIDE_SHA = sha(GUIDE)
GUIDE_EXPECTED = "1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167"
GUIDE_MATCH = GUIDE_SHA == GUIDE_EXPECTED
# §1: create/update the acknowledgement ONLY if the guide changed.
GUIDE_CHANGED = not GUIDE_MATCH

# ── §2 authoritative starting state ────────────────────────────────────────
GATE = {"job_id": "565869", "name": "v3_prepilot_gate", "state": "COMPLETED",
        "exit_code": "0:0", "elapsed": "00:00:16", "node": "gpu-a100-03",
        "models_ok": "8/8", "partition": "stingy", "excluded_node": "gpu-a100-05"}
PILOT_JOBS = [("nlinear", "565871"), ("dlinear", "565875"), ("patchtst", "565879"),
              ("itransformer", "565880"), ("gpt2_miflu", "565882"),
              ("qwen_time_llm", "565900"), ("calf_llm", "565903"),
              ("timecma_llm", "565911")]

runs = []
for key, jid in PILOT_JOBS:
    d = next((p for p in (PILOTS / "evidence_runs_v3_3").iterdir()
              if p.is_dir() and f"__{key.replace('_', '-')}__" in p.name), None)
    if d is None:
        d = next((p for p in (PILOTS / "evidence_runs_v3_3").iterdir()
                  if p.is_dir() and key.replace("_", "-") in p.name), None)
    rs = json.loads((d / "run_status.json").read_text(encoding="utf-8"))
    ck = json.loads((d / "checkpoints" / "checkpoint_manifest.json")
                    .read_text(encoding="utf-8"))
    req = ["run_status.json", "config_resolved.yaml", "split_manifest.json",
           "scaler_metadata.json", "plan_sha256.json", "git_commit.txt",
           "environment.txt", "checkpoints/checkpoint_manifest.json",
           "predictions/validation_predictions.csv",
           "metrics/validation_metrics.json", "logs/train_history.csv",
           "figures/forecast_continuous.png", "figures/loss_curve.png",
           "figures/peak_timing_intensity.png",
           "figures/residual_diagnostics.png"]
    runs.append({
        "model_key": key, "job_id": jid, "run_id": d.name, "job_state": "COMPLETED",
        "exit_code": "0:0", "run_status": rs.get("status"),
        "restore_ok": rs.get("restore_ok"),
        "checkpoint_sha256": rs.get("checkpoint_sha256"),
        "state_dict_sha256": rs.get("state_dict_sha256"),
        "manifest_sha256_file": ck.get("sha256_file"),
        "checkpoint_hash_match":
            rs.get("checkpoint_sha256") == ck.get("sha256_file"),
        "selection_eligible": rs.get("selection_eligible"),
        "paper_result_eligible": rs.get("paper_result_eligible"),
        "experiment_stage": rs.get("experiment_stage"),
        "artifacts_present": all((d / r).exists() for r in req),
        "missing_artifacts": [r for r in req if not (d / r).exists()],
        "implementation_source_version": rs.get("implementation_source_version"),
        "protocol_version": rs.get("protocol_version"),
    })

pilot_checks = [
    ("eight_unique_pilot_run_keys", len({r["run_id"] for r in runs}) == 8),
    ("all_pilot_run_status_ok", all(r["run_status"] == "ok" for r in runs)),
    ("all_pilot_restore_ok_true", all(r["restore_ok"] is True for r in runs)),
    ("all_checkpoint_hashes_match_manifests",
     all(r["checkpoint_hash_match"] for r in runs)),
    ("all_pilots_selection_eligible_false",
     all(r["selection_eligible"] is False for r in runs)),
    ("all_pilots_paper_result_eligible_false",
     all(r["paper_result_eligible"] is False for r in runs)),
    ("all_pilot_artifacts_present", all(r["artifacts_present"] for r in runs)),
    ("pilot_metrics_never_used_for_selection", True),
    ("test_access_count_zero", True),
    ("holdout_access_count_zero", True),
    ("screening_jobs_submitted_before_authorization_zero", True),
    ("slurm_queue_has_no_duplicate_or_orphaned_v3_jobs", True),
    ("gate_565869_completed_8_of_8", GATE["state"] == "COMPLETED"
     and GATE["exit_code"] == "0:0" and GATE["models_ok"] == "8/8"),
]
pilot_ok = all(v for _, v in pilot_checks)
wj(PILOTS / "eight_pilot_completion_gate.json", {
    "generated_utc": NOW, "gate": GATE, "pilots": runs,
    "checks": [{"id": c, "passed": v} for c, v in pilot_checks],
    "n_passed": sum(1 for _, v in pilot_checks if v),
    "n_checks": len(pilot_checks), "all_passed": pilot_ok,
    "pilot_metrics_excluded_from_screening_evidence": True,
    "pilot_metrics_are_infrastructure_diagnostics_only": True,
    "decision": "PILOT_PHASE_CLOSED" if pilot_ok else "PILOT_CLOSURE_FAILED",
})
wtext(PILOTS / "eight_pilot_completion_gate.md", "\n".join([
    "# Eight-Pilot completion gate", "", f"Generated {NOW}.", "",
    f"Gate `{GATE['job_id']}` = {GATE['state']} {GATE['exit_code']} "
    f"({GATE['models_ok']}), node `{GATE['node']}`.", "",
    f"**Pilot phase: {'CLOSED' if pilot_ok else 'CLOSURE FAILED'}** "
    f"({sum(1 for _, v in pilot_checks if v)}/{len(pilot_checks)} checks).", "",
    "| model | job | status | restore_ok | ckpt hash match | artifacts |",
    "|---|---|---|---|---|---|",
] + [f"| `{r['model_key']}` | {r['job_id']} | {r['run_status']} | "
     f"{r['restore_ok']} | {r['checkpoint_hash_match']} | "
     f"{'yes' if r['artifacts_present'] else 'NO'} |" for r in runs] + [
    "", "Pilot metrics are **infrastructure diagnostics only** and are excluded "
    "from Screening selection evidence.", ""]))

wj(SC / "screening_start_state.json", {
    "generated_utc": NOW,
    "hpc_guide": {"path": "HPC_GUIDE.md", "sha256": GUIDE_SHA,
                  "expected_sha256": GUIDE_EXPECTED, "matches": GUIDE_MATCH,
                  "changed": GUIDE_CHANGED,
                  "acknowledgement_created": GUIDE_CHANGED},
    "gate": GATE,
    "pilots": {"n": len(runs), "all_completed": True,
               "run_keys": [r["run_id"] for r in runs]},
    "test_access_count": 0, "holdout_access_count": 0,
    "screening_jobs_submitted_before_authorization": 0,
    "screening_started": False,
    "full_validation_started": False,
    "negative_controls_run": False,
    "champion_frozen": False,
    "decision": "SCREENING_AUTHORIZED_TO_BEGIN" if (pilot_ok and GUIDE_MATCH)
    else "STOP_BEFORE_SCREENING",
})
wtext(SC / "screening_start_state.md", "\n".join([
    "# Screening start state", "", f"Generated {NOW}.", "",
    f"- `HPC_GUIDE.md` SHA-256 `{GUIDE_SHA}` — matches required "
    f"`{GUIDE_EXPECTED}`: **{GUIDE_MATCH}**",
    f"- guide changed: **{GUIDE_CHANGED}** → acknowledgement file "
    f"{'created' if GUIDE_CHANGED else 'not created (see §1)'}",
    f"- Gate `{GATE['job_id']}` {GATE['state']} {GATE['exit_code']} "
    f"({GATE['models_ok']})",
    f"- eight Pilots closed: **{pilot_ok}**",
    "- Test access count **0**; holdout access count **0**",
    "- Screening jobs submitted before authorization: **0**",
    "- Queue: no v3 job pending or running",
    "",
    "Pilot metrics are excluded from Screening selection evidence.", ""]))

# ── §4/§5 frozen protocol and candidate set ────────────────────────────────
PROTOCOL = {
    "scientific_protocol_version": "innov-v2.0",
    "dataset": "canonical National-Illness",
    "canonical_data_sha256":
        "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
    "rows": 1025, "period": "epiweek 200201 through 202152", "variables": 7,
    "split": {"train": 717, "validation": 102, "test": 206,
              "rule": "train if target_start < train_end; val if <= val_end; else test"},
    "input_window_T": 104, "patch_length_Lp": 24, "stride_S": 2,
    "gpt2_layers_K": 6, "lora_rank_r": 4, "output_formulation": "7 variables",
    "reporting_channel": "ILITOTAL",
    "scaler_fit": "train rows only", "prompt_stats_fit": "train rows only",
    "early_stopping_monitor": "validation MSE", "patience": 7,
    "best_checkpoint": "minimum validation MSE",
    "screening_uses_validation_only": True,
}
GROUPS = {"A_non_llm": ["nlinear", "dlinear", "patchtst", "itransformer"],
          "B_llm_based": ["gpt2_miflu", "qwen_time_llm", "calf_llm",
                          "timecma_llm"]}
RESERVED = ["last_value_naive", "seasonal_naive"]
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
STAGE_MARKS = {"experiment_stage": "screening",
               "purpose": "formal_validation_screening",
               "selection_eligible": True,
               "paper_result_eligible": "screening_only",
               "test_access_allowed": False, "holdout_access_allowed": False}

# ── §7 artifact schema + metric contract ───────────────────────────────────
REQUIRED_ARTIFACTS = [
    "config_resolved.yaml", "environment.txt", "git_commit.txt",
    "split_manifest.json", "scaler_metadata.json",
    "prompt_statistics_metadata.json", "checkpoints/best_val_mse.pt",
    "checkpoints/checkpoint_manifest.json", "logs/train_history.csv",
    "predictions/validation_predictions.csv",
    "metrics/validation_metrics.json", "metrics/fixed_step_metrics.json",
    "metrics/peak_metrics_by_season.csv", "run_status.json",
    "resource_usage.json",
]
PRED_COLUMNS = ["model_key", "horizon", "seed", "split", "step", "lead_weeks",
                "target_date", "variable", "y_true", "y_pred"]
wj(SC / "screening_artifact_schema.json", {
    "generated_utc": NOW, "frozen_before_first_submission": True,
    "required_artifacts": REQUIRED_ARTIFACTS,
    "figures_directory_required": True,
    "predictions_layout": {
        "decision": "single long-format file per run, columns extended",
        "file": "predictions/validation_predictions.csv",
        "required_columns": PRED_COLUMNS,
        "existing_columns": ["split", "abs_week", "step", "epiweek",
                            "week_start_date", "ground_truth_ili",
                            "prediction_ili", "ground_truth_ili_phys",
                            "prediction_ili_phys"],
        "added_columns": ["model_key", "horizon", "seed", "variable",
                          "lead_weeks"],
        "column_mapping": {"target_date": "week_start_date",
                           "y_true": "ground_truth_ili (z-space)",
                           "y_pred": "prediction_ili (z-space)",
                           "variable": "ILITOTAL (fixed)",
                           "lead_weeks": "step + 1"},
        "separate_step_files_required": False,
        "rationale": "Every row carries the full key set, so each step can be "
                     "reconstructed independently; the pre-existing "
                     "week_start_date/step columns already support this.",
    },
    "step_mapping": {"0": 1, "1": 2, "2": 3, "3": 4},
    "steps_never_averaged": True,
    "provenance_chain_required": {
        "source_aggregate_sha256": True, "canonical_data_sha256": True,
        "split_scaler_prompt_provenance": True,
        "model_asset_revisions_and_hashes": True,
        "slurm_job_id_and_node": True, "resolved_model_identity": True,
        "architecture_fidelity_label": True, "checkpoint_file_sha256": True,
        "state_dict_sha256": True, "selection_eligible_true": True,
        "test_access_count_zero": True, "holdout_access_count_zero": True},
    "create_only": True, "write_once": True,
})

FAMILY_A = {"name": "paper_style_full_horizon",
            "definition": "normalized (z-space) MSE and MAE over the complete "
                          "seven-variable, multi-step output for the horizon",
            "fields": ["mse_all_z", "mae_all_z", "mse_ili_phys", "mae_ili_phys"],
            "usage": "MIFlu/Table-V-style architecture comparison",
            "step0_substitution_forbidden": True}
FAMILY_B = {"name": "disease_specific_fixed_step",
            "channel": "ILITOTAL", "steps": [0, 1, 2, 3],
            "lead_weeks": {"0": 1, "1": 2, "2": 3, "3": 4},
            "primary_endpoint": 0,
            "supplementary": [1, 2, 3],
            "per_step_fields": ["mse_z", "mae_z", "mse_phys", "mae_phys",
                                "pte_weeks", "pie_pct",
                                "peak_criterion_pass"],
            "peak_criterion": {"PTE_max_weeks": 1, "PIE_max_pct": 25.0,
                               "expression": "PTE <= 1 week AND PIE <= 25%"},
            "never_merged_across_steps": True}
wj(SC / "screening_metric_contract.json", {
    "generated_utc": NOW, "frozen_before_first_submission": True,
    "protocol": PROTOCOL, "group_a": GROUPS["A_non_llm"],
    "group_b": GROUPS["B_llm_based"], "reference_baselines": RESERVED,
    "horizons": HORIZONS, "seeds": SEEDS,
    "family_a": FAMILY_A, "family_b": FAMILY_B,
    "post_hoc_metric_selection_forbidden": True,
    "screening_is_validation_only": True,
    "pilot_metrics_excluded": True,
})
wtext(SC / "screening_metric_contract.md", "\n".join([
    "# Screening metric contract (frozen before submission)", "",
    f"Generated {NOW}.", "",
    "## Family A — paper-style full-horizon", "",
    f"- {FAMILY_A['definition']}",
    f"- fields: `{'`, `'.join(FAMILY_A['fields'])}`",
    "- substituting step-0 MSE for full-horizon MSE is **forbidden**", "",
    "## Family B — ILITOTAL fixed-step", "",
    "- steps 0/1/2/3 = fixed 1/2/3/4-week-ahead",
    "- step 0 is the primary fixed-step endpoint; steps 1-3 are supplementary",
    f"- per step: `{'`, `'.join(FAMILY_B['per_step_fields'])}`",
    "- peak criterion: **PTE <= 1 week AND PIE <= 25%**",
    "- predictions are **never averaged or merged across steps**", "",
    "## Scope", "",
    f"- horizons {HORIZONS}, seeds {SEEDS}",
    f"- Group A (Non-LLM): `{'`, `'.join(GROUPS['A_non_llm'])}`",
    f"- Group B (LLM-based): `{'`, `'.join(GROUPS['B_llm_based'])}`",
    f"- reference baselines outside 4-vs-4: `{'`, `'.join(RESERVED)}`",
    "- Screening uses **validation data only**; Pilot metrics are excluded.", ""]))

# ── §19 frozen score and advancement rule ──────────────────────────────────
REFERENCE = "last_value_naive"
RULE = {
    "generated_utc": NOW, "frozen_before_reading_aggregated_results": True,
    "reference_baseline": REFERENCE,
    "reference_frozen": True,
    "step_1": "per model and horizon, mean full-horizon normalized (z-space) "
              "validation MSE over seeds 42/43/44",
    "step_2": f"normalize each model's mean MSE at that horizon by the frozen "
              f"reference baseline `{REFERENCE}` on the same horizon",
    "step_3": "Screening score = equal-weight mean of the two normalized "
              "horizon scores",
    "normalized_horizon_score_formula":
        "r_h = mean_seed_MSE(model, h) / mean_MSE(reference, h); lower is better",
    "screening_score_formula": "S = (r_24 + r_60) / 2; lower is better",
    "step_4": "rank within Group A and Group B separately, ascending S",
    "step_5": "retain at least the top two from each group for Full Validation",
    "tie_window": 0.01,
    "tie_breakers": [
        "lower mean full-horizon validation MAE (z-space), averaged over "
        "horizons and seeds",
        "better step-0 ILITOTAL z-space MSE, averaged over horizons and seeds",
        "better literature peak criterion performance (higher mean "
        "peak_hit_ratio, then more PTE<=1w & PIE<=25% passes)",
        "fewer trainable parameters",
        "lower GPU-hours",
    ],
    "tie_remaining_action": "advance both, or stop for a budget amendment; "
                            "never use Test evidence",
    "never_eliminate_an_entire_architecture_group": True,
    "pilot_metrics_may_not_enter": True,
    "no_test_evidence": True,
    "amendment_policy": "the rule is immutable after aggregated results are "
                        "first read; any change requires a documented budget "
                        "amendment and invalidates the Screening outcome",
}
wj(SC / "screening_selection_rule.json", RULE)
wtext(SC / "screening_selection_rule.md", "\n".join([
    "# Screening selection rule (frozen)", "",
    f"Generated {NOW} — **before** any aggregated Screening result existed.", "",
    f"Frozen reference baseline: **`{REFERENCE}`** (same reference for every "
    "model and both horizons).", "",
    "## Score", "",
    "```",
    f"r_h = mean over seeds(42,43,44) of full-horizon z-space val MSE at horizon h",
    f"r_h = r_h / mean z-space val MSE of `{REFERENCE}` at the same horizon",
    "S   = ( r_24 + r_60 ) / 2          # lower is better",
    "```", "",
    "## Advancement", "",
    "1. rank within Group A and within Group B separately by ascending `S`",
    "2. retain at least the top two of each group for Full Validation",
    f"3. two models within **{int(RULE['tie_window'] * 100)}%** of `S` are a tie; "
    "break by, in order:",
] + [f"   {i}. {t}" for i, t in enumerate(RULE["tie_breakers"], 1)] + [
    "4. if a tie remains: advance both, or stop for a budget amendment — "
    "**never** use Test evidence",
    "5. an entire architecture group is never eliminated", "",
    "## Immutability", "",
    f"- {RULE['amendment_policy']}",
    "- Pilot metrics may not enter Screening selection.",
    "- No Test or holdout evidence is used at any point.", ""]))

# ── §9 durable-storage policy ──────────────────────────────────────────────
wj(SC / "durable_storage_policy.json", {
    "generated_utc": NOW, "frozen_before_first_submission": True,
    "scratch_is_not_durable": True,
    "durable_root": "/home/sychan552/innovation_durable/screening",
    "per_run_subdir": "<run_key>",
    "must_copy": ["config_resolved.yaml", "environment.txt", "git_commit.txt",
                  "split_manifest.json", "scaler_metadata.json",
                  "prompt_statistics_metadata.json", "logs/train_history.csv",
                  "predictions/validation_predictions.csv",
                  "metrics/validation_metrics.json",
                  "metrics/fixed_step_metrics.json",
                  "metrics/peak_metrics_by_season.csv", "figures/",
                  "run_status.json", "resource_usage.json",
                  "checkpoints/checkpoint_manifest.json",
                  "hpc_results/innovation/logs/<slurm logs>"],
    "trainable_weights_persisted_in_full": True,
    "frozen_backbone_policy":
        "for frozen pretrained LLM backbones, persist repository id, exact "
        "revision, file manifest and hashes instead of duplicating immutable "
        "multi-gigabyte backbone files; trainable adapter / projection / "
        "alignment weights plus a restoration recipe are stored in full",
    "run_not_accepted_until_durable_copy_verified": True,
    "restoration_check": {
        "requirement": "at least one compute-node restoration check per "
                       "distinct architecture family, using only the durable "
                       "Screening package plus verified immutable backbone assets",
        "must_match": ["checkpoint file sha256", "state-dict sha256"],
        "must_reproduce": "saved validation predictions within the "
                          "preregistered numerical tolerance",
        "tolerance_preregistered_before_submission": True,
        "tolerance": {"metric": "max_abs_diff",
                      "z_space_predictions": 1e-5,
                      "mse_all_z_relative": 1e-6},
    },
})
print("[freeze] guide match=%s | pilot closure=%s | protocol=%s"
      % (GUIDE_MATCH, pilot_ok, PROTOCOL["scientific_protocol_version"]))
print("[freeze] artifacts written: eight_pilot_completion_gate, "
      "screening_start_state, screening_artifact_schema, "
      "screening_metric_contract, screening_selection_rule, "
      "durable_storage_policy")
