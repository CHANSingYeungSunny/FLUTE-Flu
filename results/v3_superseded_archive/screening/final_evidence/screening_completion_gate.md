# Phase 2 Screening completion gate

Generated 2026-09-17T01:45:38Z.

**12/12 checks passed** → `PHASE2_SCREENING_COMPLETE`

| check | passed |
|---|---|
| `accepted_primary_runs_48_of_48` | yes |
| `unique_run_keys_48` | yes |
| `unresolved_cells_zero` | yes |
| `durable_copies_48_of_48` | yes |
| `checkpoint_manifests_48_of_48` | yes |
| `restoration_verification_passed` | yes |
| `naive_baselines_complete` | yes |
| `test_access_count_zero` | yes |
| `holdout_access_count_zero` | yes |
| `pilot_metrics_excluded` | yes |
| `screening_cells_not_rerun` | yes |
| `frozen_selection_rule_unchanged` | yes |

## Observed rankings (frozen rule: S = (r24+r60)/2, lower better)

Reference denominator: **last_value_naive** (L24 MSE 2.821200, L60 MSE 2.825089).

### group_a

| rank | model | r24 | r60 | S |
|---|---|---|---|---|
| 1 | `nlinear` | 0.7643 | 0.8830 | 0.8237 |
| 2 | `dlinear` | 0.8212 | 0.9592 | 0.8902 |
| 3 | `patchtst` | 0.8501 | 0.9353 | 0.8927 |
| 4 | `itransformer` | 0.9506 | 1.0834 | 1.0170 |

- advanced (proposed Full Validation candidates): ['nlinear', 'dlinear', 'patchtst']
- tie ['dlinear', 'patchtst'] (Δ0.28%): `lower_mean_full_horizon_normalized_MAE` → winner `patchtst`

### group_b

| rank | model | r24 | r60 | S |
|---|---|---|---|---|
| 1 | `gpt2_miflu` | 0.4745 | 0.6287 | 0.5516 |
| 2 | `qwen_time_llm` | 0.8623 | 1.0096 | 0.9359 |
| 3 | `timecma_llm` | 0.8652 | 1.0429 | 0.9541 |
| 4 | `calf_llm` | 1.2536 | 1.3858 | 1.3197 |

- advanced (proposed Full Validation candidates): ['gpt2_miflu', 'qwen_time_llm', 'timecma_llm']

## Caveats

- results are **validation-only**; three seeds are **preliminary**;
- ranks are an **observed Screening ranking**, not final champions;
- Pilot metrics are **excluded** entirely;
- no champion frozen; no Full Validation submitted; Test/holdout access = 0/0.
