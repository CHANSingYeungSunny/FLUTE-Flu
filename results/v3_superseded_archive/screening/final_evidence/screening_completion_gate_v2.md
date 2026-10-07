# Phase 2 completion gate v2

Generated 2026-09-17T03:10:20Z.

- supersedes `screening_completion_gate.json` → `SUPERSEDED_PREMATURE_COMPLETION_GATE_MISSING_FIGURE_QA` (old file **untouched**)
- **18/18 checks passed** → `PHASE2_SCREENING_COMPLETE_WITH_FIGURE_QA`

| check | passed |
|---|---|
| `accepted_48_of_48` | yes |
| `artifact_audit_48_of_48` | yes |
| `checkpoint_audit_48_of_48` | yes |
| `metadata_chain_audit_48_of_48` | yes |
| `durable_copy_audit_48_of_48` | yes |
| `restoration_8_of_8` | yes |
| `baseline_audit_passed` | yes |
| `statistical_report_complete` | yes |
| `candidate_serialization_corrected` | yes |
| `figure_inventory_complete` | yes |
| `figure_provenance_complete` | yes |
| `figure_qa_passed` | yes |
| `local_sync_passed` | yes |
| `pilot_metrics_excluded` | yes |
| `test_access_count_zero` | yes |
| `holdout_access_count_zero` | yes |
| `full_validation_submitted_zero` | yes |
| `champions_frozen_zero` | yes |

## Advancement (raw order preserved, tie-break applied)

- Group A raw score order: `['nlinear', 'dlinear', 'patchtst', 'itransformer']`
- Group A advanced after tie-break: **`['nlinear', 'patchtst']`**
- Group B raw score order: `['gpt2_miflu', 'qwen_time_llm', 'timecma_llm', 'calf_llm']`
- Group B advanced after tie-break: **`['gpt2_miflu', 'qwen_time_llm']`**, 
- tie ['dlinear', 'patchtst'] (Δ0.28%): `lower_mean_full_horizon_normalized_MAE` → winner `patchtst`

### dlinear vs patchtst disclosure

`dlinear` has a slightly **better raw S** than `patchtst`, but the difference is **below 1%**, so the frozen tie-breaker applies and the **lower mean full-horizon normalized MAE** selects `patchtst`. This is a preregistered rule application, not a post-hoc change.

## Boundaries

- no champion frozen; no Full Validation submitted;
- no formal negative controls; Test/holdout access = 0/0;
- no accepted Screening run, baseline or restoration re-executed.
