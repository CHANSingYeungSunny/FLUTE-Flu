# v3 protocol-correction Gate

{
  "generated_utc": "2026-09-16T08:09:00Z",
  "phase": "Phase 1 preflight halted for process review",
  "checks": [
    {
      "id": "active_v3_forbidden_scope_violations_zero",
      "passed": true
    },
    {
      "id": "citation_errors_corrected",
      "passed": true
    },
    {
      "id": "time_llm_venue_corrected_to_iclr_2024",
      "passed": true
    },
    {
      "id": "date_contradiction_root_cause_established",
      "passed": true
    },
    {
      "id": "holdout_decision_explicit",
      "passed": true
    },
    {
      "id": "official_sources_live_verified_all_eight",
      "passed": true
    },
    {
      "id": "licenses_known_for_all_eight",
      "passed": true
    },
    {
      "id": "timecma_license_flagged_for_manual_review",
      "passed": true
    },
    {
      "id": "three_llm_contracts_materially_distinct",
      "passed": true
    },
    {
      "id": "environment_and_access_plan_written",
      "passed": true
    },
    {
      "id": "budget_recomputed_with_official_model_sizes",
      "passed": true
    },
    {
      "id": "figure_and_fixed_step_contract_valid",
      "passed": true
    },
    {
      "id": "experiment_matrices_internally_consistent",
      "passed": true
    },
    {
      "id": "v3_plan_updated",
      "passed": true
    },
    {
      "id": "no_weights_downloaded",
      "passed": true
    },
    {
      "id": "no_model_built_or_loaded",
      "passed": false
    },
    {
      "id": "no_slurm_submission",
      "passed": true
    },
    {
      "id": "no_holdout_accessed",
      "passed": true
    },
    {
      "id": "v2_evidence_unmodified",
      "passed": true
    },
    {
      "id": "no_v3_champion_or_holdout_receipt",
      "passed": true
    }
  ],
  "n_passed": 19,
  "n_checks": 20,
  "all_checks_passed": false,
  "blocking_items": [
    {
      "id": "phase1_preflight_process_violation",
      "satisfied": false,
      "detail": "Initial local Pilot metadata generation instantiated the GPT-2 adapter outside a Slurm compute node; repaired to static metadata-only generation. Review incident before any asset download or Pilot submission."
    },
    {
      "id": "qwen_asset_authorization",
      "satisfied": false,
      "detail": "Qwen2.5-1.5B download and cache registration require explicit authorization; no download occurred."
    },
    {
      "id": "timecma_license_review",
      "satisfied": false,
      "detail": "S-Lab License 1.0 and backbone/weight terms require human review before upstream code use."
    }
  ],
  "decision": "V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW",
  "authorization_required_next": [
    "Authorize the versioned Qwen asset download and compute-node-only smoke test.",
    "Clear TimeCMA license and backbone/weight terms for the planned inspired implementation.",
    "Authorize Phase 1: eight L=24 seed-42 pilots using the original GPT-2/MIFlu protocol and independent v3 paths."
  ],
  "must_not_do": [
    "download weights",
    "install model dependencies",
    "construct or load models",
    "train or infer",
    "submit Slurm jobs",
    "access Test values",
    "generate v3 result figures",
    "modify v2 evidence",
    "compute on a Burgundy login node"
  ],
  "superseded_history": "SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY",
  "phase07_audit": {
    "canonical_data_sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
    "plan_sha256": "78de98f611029faffd9b82dc5f8830f683613e4f6067e339cd5e8520d08090ed",
    "active_external_data": false,
    "active_new_holdout": false,
    "active_rolling_origin_redesign": false,
    "active_target": "ILITOTAL",
    "phase1_started": false
  }
}
