# Screening static pre-submission gate

Generated 2026-09-16T21:32:15Z.

**31/31 checks passed** (48 specs).

| check | passed |
|---|---|
| `exactly_48_unique_primary_run_specs` | yes |
| `eight_models` | yes |
| `two_horizons_24_60` | yes |
| `three_seeds_42_43_44` | yes |
| `no_duplicate_run_keys` | yes |
| `no_duplicate_output_paths` | yes |
| `correct_stage_field_experiment_stage` | yes |
| `correct_purpose_field` | yes |
| `selection_eligible_true` | yes |
| `paper_result_eligible_screening_only` | yes |
| `test_permission_disabled` | yes |
| `holdout_permission_disabled` | yes |
| `correct_source_snapshot_hash` | yes |
| `correct_canonical_data_hash` | yes |
| `correct_per_model_backbone_routing` | yes |
| `gpt2_miflu_uses_gpt2_text_encoder` | yes |
| `calf_and_timecma_use_gpt2_not_qwen` | yes |
| `qwen_uses_pinned_revision` | yes |
| `fixed_step_schema_declared` | yes |
| `full_horizon_metric_schema_declared` | yes |
| `durable_destination_per_spec` | yes |
| `slurm_headers_and_node_exclusion` | yes |
| `all_48_entry_scripts_written` | yes |
| `every_entry_script_excludes_node` | yes |
| `every_entry_script_declares_screening_stage` | yes |
| `queue_safe_controller_required` | yes |
| `append_only_registry_behavior` | yes |
| `no_model_instantiation_during_metadata_generation` | yes |
| `no_login_node_computation` | yes |
| `no_pilot_metric_ingestion_into_screening_selection` | yes |
| `baselines_excluded_from_4v4_count` | yes |

## Frozen execution order

```
for model in frozen model order (Group A then Group B):
  for horizon in [24, 60]:
    for seed in [42, 43, 44]:
      submit exactly one run, wait for terminal state, verify, next
```

- excluded node: `gpu-a100-05` on every job
- deployment root: `/scratch/sychan552/innovation_deploy_root_v3_5`
- durable root: `/home/sychan552/innovation_durable/screening`

Nothing has been submitted at the time this gate was written.
