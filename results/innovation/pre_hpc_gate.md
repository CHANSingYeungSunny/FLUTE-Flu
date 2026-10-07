# Pre-HPC gate

- Readiness — pilot generation: **True**
- Readiness — pilot submission: **False** (blocker: `UNVERIFIED_HPC_SOURCE_DEPLOYMENT`)
- Readiness — full-sweep submission: **False** (pilot has not been run/reviewed; the full sweep remains blocked until pilot evidence is accepted)

- source snapshot: `5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d` (77 files)
- `submission_attempted`: False
- `sbatch_invoked`: False
- test sealed: True | frozen winner created: False

## Checks

- `plan_sha256_matches`: True
- `four_pilot_scripts_present`: True
- `pilot_specs_json_present`: True
- `gpt2_cache_available`: True
- `aggregation_regression_ok`: True
- `pipeline_regression_ok`: True
- `gpt2_control_repro_ok`: True
- `slurm_validation_ok`: True
- `submission_guards_present`: True
- `test_split_sealed`: True
- `no_test_artifacts_under_runs`: True
- `source_snapshot_dir_present`: True
- `source_snapshot_manifest_present`: True
- `pilot_specs_carry_snapshot_sha`: True
- `pilot_specs_selection_eligible_false`: True

## Pilot scripts (generated, NOT submitted)

- `hpc_scripts\pilot_dlinear_L24_seed42.sh`
- `hpc_scripts\pilot_gpt2_miflu_L24_seed42.sh`
- `hpc_scripts\pilot_itransformer_L24_seed42.sh`
- `hpc_scripts\pilot_patchtst_L24_seed42.sh`