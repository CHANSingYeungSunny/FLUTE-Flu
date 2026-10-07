# Wave-1 controller static audit

- version: `innov-v3.12-gate-validator-schema-alignment`  |  Gate: **570846** (19/19)
- Wave-1 rows: **580**  |  deferred: **18**
- **controller launched: NO**

**31/31 checks passed**

- [PASS] `wave1_unique_run_keys` — 580 keys, 580 unique
- [PASS] `zero_deferred_rows_in_wave1` — 0
- [PASS] `zero_duplicates` — 0
- [PASS] `zero_missing_scripts` — []
- [PASS] `zero_extra_scripts` — []
- [PASS] `zero_crlf_scripts` — []
- [PASS] `all_scripts_pass_bash_n` — []
- [PASS] `order_is_monotonic` — orders 1..580
- [PASS] `order_file_is_lf_only` — no CR bytes in order/controller/launcher
- [PASS] `deferred_count_18` — 18
- [PASS] `matrix_total_598` — 598
- [PASS] `source_identity_is_v3_12` — innov-v3.12-gate-validator-schema-alignment
- [PASS] `specs_carry_v3_12_identity` — ok
- [PASS] `controller_has_single_instance_lock` — ok
- [PASS] `controller_requires_authorization_token` — ok
- [PASS] `controller_unsets_token_before_any_sbatch` — ok
- [PASS] `controller_enforces_one_active_job` — counts numeric job ids only
- [PASS] `active_job_count_ignores_scheduler_banner` — the 'Last update in N seconds ago' banner is not counted
- [PASS] `controller_exports_row_script_contract` — ok
- [PASS] `jobroot_matches_runner_default_out_root` — ok
- [PASS] `controller_records_job_id_immediately` — ok
- [PASS] `controller_has_append_only_ledger` — ok
- [PASS] `controller_is_resumable` — ok
- [PASS] `controller_fail_stops` — ok
- [PASS] `controller_verifies_durable_copy` — ok
- [PASS] `controller_stops_after_wave1` — ok
- [PASS] `controller_has_no_forbidden_tooling` — []
- [PASS] `controller_never_touches_archive_or_test_or_holdout` — []
- [PASS] `controller_not_running` — pgrep found no wave1_controller.sh process
- [PASS] `formal_submissions_remain_0` — 0/598 (no row submitted this turn)
- [PASS] `lock_not_held` — free

## Launch requirement
Launching requires `WAVE1_AUTHORIZATION_TOKEN` to be set AND to equal the contents of `results/v3_clean/runs/wave1_authorization.token` (which does not exist yet). Without both, the controller exits immediately with FAIL-STOP.
