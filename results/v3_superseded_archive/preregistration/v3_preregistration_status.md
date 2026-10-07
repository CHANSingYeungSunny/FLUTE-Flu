# v3 Phase-0 preregistration — authoritative status

Generated 2026-09-16T17:01:14Z.

**Deliverable: COMPLETE.** Gating checks 26/26 passed.

## Supersession note

`preregistration_gate.json` was subsequently overwritten by a later authorised phase and now records the Phase-1 preflight halt (`V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW`). It is retained as history and was **not** rewritten; this file is the authoritative Phase-0 record.

## Checks

| Check | Passed |
|---|---|
| `v2_evidence_preserved_untouched` | yes |
| `active_v3_forbidden_scope_violations_zero` | yes |
| `v3_plan_written` | yes |
| `eight_primary_candidates_frozen` | yes |
| `two_naive_baselines_declared_separately` | yes |
| `negative_controls_bounded_and_secondary` | yes |
| `official_sources_and_licences_recorded` | yes |
| `architecture_fidelity_and_contracts_recorded` | yes |
| `holdout_decision_explicit` | yes |
| `figure_style_guide_and_reference_located` | yes |
| `shared_figure_module_api_valid` | yes |
| `one_style_covers_4_non_llm_4_llm_2_naive_and_controls` | yes |
| `fixed_steps_0_3_retained` | yes |
| `step_lead_mapping_declared_1_to_4_weeks` | yes |
| `step0_is_primary_others_mandatory_supplementary` | yes |
| `no_cross_step_averaging_rule_present` | yes |
| `common_target_date_intersection_rule_present` | yes |
| `figures_from_saved_artifacts_only` | yes |
| `provenance_sidecar_required` | yes |
| `automated_figure_qa_required` | yes |
| `proposed_matrices_written` | yes |
| `no_v3_result_figures_generated_yet` | yes |
| `no_weights_downloaded_this_round` | yes |
| `no_model_loaded_this_round` | yes |
| `no_slurm_submitted_this_round` | yes |
| `no_holdout_accessed_this_round` | yes |

## Figure contract

- style guide `4e2ee958bb1561e4…`, reference `06d8622152ef2bf0…`
- shared module `c8ae38a2b2a99f21…`, API valid `True`
- fixed steps [0, 1, 2, 3], lead weeks {'0': 1, '1': 2, '2': 3, '3': 4} (step s -> s+1 weeks), primary step 0
- 13 stable model identities cover the 4 Non-LLM, 4 LLM-based, 2 naive baselines and all negative controls
- 8 figure families defined; **0 v3 result figures generated**

## Matrices

- `proposed_pilot_matrix.csv` = 8 rows
- `proposed_screening_matrix.csv` = 48 rows
- `proposed_full_validation_matrix.csv` = 320 rows
- `proposed_baseline_matrix.csv` = 80 rows
- `proposed_negative_control_matrix.csv` = 30 rows

## Holdout

- decision **REJECTED** / `NO_UNTOUCHED_INTERVAL_AVAILABLE_INTERNAL`
- option 1 (unused internal weeks) **ELIMINATED**; options 2/3 require user acquisition

## This round did not

- download weights; load or construct models; submit any Slurm job; access any holdout;
- modify v2 evidence; generate v3 result figures.
