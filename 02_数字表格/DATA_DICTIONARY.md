> Reviewed 2026-11-04: the exported BENCH_PAIRED_TESTS.csv p_holm column is defective. Recompute from p_raw using proper forward cumulative-max Holm. The actual 17-model family includes MIFlu and excludes DLinear and all frozen encoders. The source CSV is retained unchanged.

# DATA_DICTIONARY — every CSV in `02_数字表格/`

One row per file: rows × columns and the column names. All files are UTF-8 CSV with a
header. `02_数字表格/README.md` (in the full repo) describes the older exports.

## Key columns

| Column | Meaning |
|---|---|
| `mse_7var_z` / `mae_7var_z` | 7-variable aggregate MSE/MAE in standardised (z) space; the accuracy metric |
| `PTE_wk` | peak-timing error in weeks (K&S half 1; pass ≤ 1) |
| `PIE_pct` | peak-intensity error as % of the observed peak (K&S half 2; pass ≤ 25) |
| `kramer_shaman_pass` | True only if BOTH halves hold in the same (model, horizon, step) cell |
| `p_holm` | Holm–Bonferroni corrected p over all 136 model pairs |
| `effect_d` | Cohen's d for the paired difference |
| `on_pareto` | True if no other model has both lower MSE and fewer parameters |
| `params` | trained parameter count (blank for classical learners and MIFlu) |
| `rel_improve_vs_seasonal_pct` | % MSE improvement over the 52-week seasonal-naive baseline |

## Files

| File | Rows | Cols | Columns |
|---|---:|---:|---|
| `BENCH_CRPS_WIS.csv` | 68 | 8 | `model`, `L`, `n_seeds`, `n_eval_windows`, `crps_z`, `log_score`, `wis`, `mean_sigma_z` |
| `BENCH_CRPS_WIS.post_evalwindow16.csv` | 64 | 8 | `model`, `L`, `n_seeds`, `n_eval_windows`, `crps_z`, `log_score`, `wis`, `mean_sigma_z` |
| `BENCH_CRPS_WIS.post_evalwindow16_v100nlinear.csv` | 64 | 8 | `model`, `L`, `n_seeds`, `n_eval_windows`, `crps_z`, `log_score`, `wis`, `mean_sigma_z` |
| `BENCH_CRPS_WIS.pre_evalwindow16.csv` | 64 | 7 | `model`, `L`, `n_seeds`, `crps_z`, `log_score`, `wis`, `mean_sigma_z` |
| `BENCH_EFFICIENCY.csv` | 17 | 14 | `model`, `mse_mean`, `params`, `n_cells`, `improve_vs_worst_pct`, `params_B`, `n_eval_windows_L24`, `n_eval_windows_L36`, `n_eval_windows_L48`, `n_eval_windows_L60`, `on_pareto`, `mse_vs_log10params_slope`, `mse_vs_log10params_r2`, `rel_improve_vs_seasonal_pct` |
| `BENCH_EFFICIENCY.post_evalwindow16.csv` | 16 | 14 | `model`, `mse_mean`, `params`, `n_cells`, `improve_vs_worst_pct`, `params_B`, `n_eval_windows_L24`, `n_eval_windows_L36`, `n_eval_windows_L48`, `n_eval_windows_L60`, `on_pareto`, `mse_vs_log10params_slope`, `mse_vs_log10params_r2`, `rel_improve_vs_seasonal_pct` |
| `BENCH_EFFICIENCY.post_evalwindow16_v100nlinear.csv` | 16 | 14 | `model`, `mse_mean`, `params`, `n_cells`, `improve_vs_worst_pct`, `params_B`, `n_eval_windows_L24`, `n_eval_windows_L36`, `n_eval_windows_L48`, `n_eval_windows_L60`, `on_pareto`, `mse_vs_log10params_slope`, `mse_vs_log10params_r2`, `rel_improve_vs_seasonal_pct` |
| `BENCH_EFFICIENCY.pre_evalwindow16.csv` | 16 | 10 | `model`, `mse_mean`, `params`, `n_cells`, `improve_vs_worst_pct`, `params_B`, `on_pareto`, `mse_vs_log10params_slope`, `mse_vs_log10params_r2`, `rel_improve_vs_seasonal_pct` |
| `BENCH_GPU_PROVENANCE.csv` | 204 | 11 | `model`, `L`, `seed`, `job_id`, `node`, `gpu_type`, `gpu_count`, `source`, `npz_mtime`, `job_name`, `partition` |
| `BENCH_GPU_PROVENANCE.post_evalwindow16.csv` | 204 | 11 | `model`, `L`, `seed`, `job_id`, `node`, `gpu_type`, `gpu_count`, `source`, `npz_mtime`, `job_name`, `partition` |
| `BENCH_GPU_PROVENANCE.post_evalwindow16_v100nlinear.csv` | 204 | 11 | `model`, `L`, `seed`, `job_id`, `node`, `gpu_type`, `gpu_count`, `source`, `npz_mtime`, `job_name`, `partition` |
| `BENCH_GPU_PROVENANCE.pre_evalwindow16.csv` | 204 | 11 | `model`, `L`, `seed`, `job_id`, `node`, `gpu_type`, `gpu_count`, `source`, `npz_mtime`, `job_name`, `partition` |
| `BENCH_KS_CHAMPION_DETAIL.csv` | 448 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `verdict` |
| `BENCH_KS_CHAMPION_DETAIL.post_evalwindow16.csv` | 256 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `verdict` |
| `BENCH_KS_CHAMPION_DETAIL.post_evalwindow16_v100nlinear.csv` | 256 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `verdict` |
| `BENCH_KS_CHAMPION_DETAIL.pre_evalwindow16.csv` | 256 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `verdict` |
| `BENCH_MSE_BY_FAMILY.csv` | 6 | 6 | `family`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_FAMILY.post_evalwindow16.csv` | 5 | 6 | `family`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_FAMILY.post_evalwindow16_v100nlinear.csv` | 5 | 6 | `family`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_FAMILY.pre_evalwindow16.csv` | 5 | 6 | `family`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_FAMILY.pre_miflu.csv` | 6 | 6 | `family`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_MODEL_L.csv` | 112 | 15 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows`, `windows_discarded`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys`, … (+1) |
| `BENCH_MSE_BY_MODEL_L.post_evalwindow16.csv` | 64 | 15 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows`, `windows_discarded`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys`, … (+1) |
| `BENCH_MSE_BY_MODEL_L.post_evalwindow16_v100nlinear.csv` | 64 | 15 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows`, `windows_discarded`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys`, … (+1) |
| `BENCH_MSE_BY_MODEL_L.pre_evalwindow16.csv` | 64 | 12 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys`, `partial_export` |
| `BENCH_MSE_BY_MODEL_L.pre_miflu.csv` | 68 | 10 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys` |
| `BENCH_MSE_BY_SIDE.csv` | 2 | 6 | `side`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_SIDE.post_evalwindow16.csv` | 2 | 6 | `side`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_SIDE.post_evalwindow16_v100nlinear.csv` | 2 | 6 | `side`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_SIDE.pre_evalwindow16.csv` | 2 | 6 | `side`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_SIDE.pre_miflu.csv` | 2 | 6 | `side`, `24`, `36`, `48`, `60`, `mean` |
| `BENCH_MSE_BY_STEP.csv` | 448 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows` |
| `BENCH_MSE_BY_STEP.post_evalwindow16.csv` | 256 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows` |
| `BENCH_MSE_BY_STEP.post_evalwindow16_v100nlinear.csv` | 256 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z`, `n_channels_used`, `n_windows_available`, `n_eval_windows` |
| `BENCH_MSE_BY_STEP.pre_evalwindow16.csv` | 256 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z`, `n_channels_used` |
| `BENCH_MSE_BY_STEP.pre_miflu.csv` | 272 | 7 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z` |
| `BENCH_MSE_BY_STEP_CLEAN.csv` | 448 | 7 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z` |
| `BENCH_MSE_BY_STEP_CLEAN.post_evalwindow16.csv` | 256 | 7 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z` |
| `BENCH_MSE_BY_STEP_CLEAN.post_evalwindow16_v100nlinear.csv` | 256 | 7 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z` |
| `BENCH_MSE_BY_STEP_CLEAN.pre_evalwindow16.csv` | 256 | 7 | `model`, `family`, `L`, `step`, `weeks_ahead`, `mse_7var_z`, `mae_7var_z` |
| `BENCH_MSE_RANK_FULL.csv` | 112 | 10 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys` |
| `BENCH_MSE_RANK_FULL.post_evalwindow16.csv` | 64 | 10 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys` |
| `BENCH_MSE_RANK_FULL.post_evalwindow16_v100nlinear.csv` | 64 | 10 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys` |
| `BENCH_MSE_RANK_FULL.pre_evalwindow16.csv` | 64 | 10 | `model`, `family`, `L`, `n_seeds`, `mse_7var_z`, `mae_7var_z`, `mse_ilitotal_z`, `mae_ilitotal_z`, `mse_ilitotal_phys`, `mae_ilitotal_phys` |
| `BENCH_NLINEAR_A100_DELTA.csv` | 16 | 15 | `L`, `step`, `weeks_ahead`, `PTE_wk_v100`, `PIE_pct_v100`, `pass_v100`, `n_seeds_v100`, `n_eval_windows_v100`, `PTE_wk_a100`, `PIE_pct_a100`, `pass_a100`, `n_seeds_a100`, `n_eval_windows_a100`, `mse_4L_v100`, … (+1) |
| `BENCH_PAIRED_TESTS.csv` | 136 | 10 | `model_a`, `model_b`, `n`, `mean_diff`, `wins_a`, `p_raw`, `ci_lo`, `ci_hi`, `p_holm`, `effect_d` |
| `BENCH_PAIRED_TESTS.post_evalwindow16.csv` | 120 | 10 | `model_a`, `model_b`, `n`, `mean_diff`, `wins_a`, `p_raw`, `ci_lo`, `ci_hi`, `p_holm`, `effect_d` |
| `BENCH_PAIRED_TESTS.post_evalwindow16_v100nlinear.csv` | 120 | 10 | `model_a`, `model_b`, `n`, `mean_diff`, `wins_a`, `p_raw`, `ci_lo`, `ci_hi`, `p_holm`, `effect_d` |
| `BENCH_PAIRED_TESTS.pre_evalwindow16.csv` | 120 | 10 | `model_a`, `model_b`, `n`, `mean_diff`, `wins_a`, `p_raw`, `ci_lo`, `ci_hi`, `p_holm`, `effect_d` |
| `BENCH_PTE_PIE_BY_STEP.csv` | 448 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `kramer_shaman_pass`, `n_windows_available`, `n_eval_windows` |
| `BENCH_PTE_PIE_BY_STEP.post_evalwindow16.csv` | 256 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `kramer_shaman_pass`, `n_windows_available`, `n_eval_windows` |
| `BENCH_PTE_PIE_BY_STEP.post_evalwindow16_v100nlinear.csv` | 256 | 10 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `kramer_shaman_pass`, `n_windows_available`, `n_eval_windows` |
| `BENCH_PTE_PIE_BY_STEP.pre_evalwindow16.csv` | 256 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `kramer_shaman_pass` |
| `BENCH_PTE_PIE_BY_STEP.pre_miflu.csv` | 272 | 8 | `model`, `family`, `L`, `step`, `weeks_ahead`, `PTE_wk`, `PIE_pct`, `kramer_shaman_pass` |
| `BENCH_SEASONAL_NAIVE.csv` | 4 | 7 | `model`, `L`, `mse_7var_z`, `mae_7var_z`, `n_windows`, `n_windows_available`, `n_eval_windows` |
| `BENCH_SEASONAL_NAIVE.post_evalwindow16.csv` | 4 | 7 | `model`, `L`, `mse_7var_z`, `mae_7var_z`, `n_windows`, `n_windows_available`, `n_eval_windows` |
| `BENCH_SEASONAL_NAIVE.post_evalwindow16_v100nlinear.csv` | 4 | 7 | `model`, `L`, `mse_7var_z`, `mae_7var_z`, `n_windows`, `n_windows_available`, `n_eval_windows` |
| `BENCH_SEASONAL_NAIVE.pre_evalwindow16.csv` | 4 | 5 | `model`, `L`, `mse_7var_z`, `mae_7var_z`, `n_windows` |
| `DENORMALIZED_MSE_MAE_BY_VARIABLE.csv` | 756 | 11 | `model`, `side`, `L`, `seed`, `var_index`, `variable`, `std`, `mse_z`, `mae_z`, `mse_physical`, `mae_physical` |
| `ESSAY_VS_REPRODUCTION_TABLE_V.csv` | 5 | 9 | `model`, `L`, `paper_MSE`, `our_MSE`, `delta_pct`, `paper_MAE`, `our_MAE`, `protocol`, `delta_mae_pct` |
| `EXPANDED_COMBINED_TEST_MSE_RANKING.csv` | 19 | 19 | `rank_MSE`, `model`, `model_instance_id`, `cohort`, `mean_Test_MSE_4L`, `sd_Test_MSE_4L`, `mean_Test_MAE_4L`, `side`, `n_seeds`, `MSE_z_ILITOTAL`, `MSE_physical_ILITOTAL`, `MAE_z_ILITOTAL`, `MAE_physical_ILITOTAL`, `implementation_fidelity`, … (+5) |
| `MIFLU_ESSAY_MSE_MAE_BY_STEP.csv` | 5 | 10 | `L`, `essay_MSE`, `ours_MSE`, `delta_MSE_pct`, `essay_MAE`, `ours_MAE`, `delta_MAE_pct`, `c2_MSE`, `c2_delta_pct`, `c2_n_seeds` |
| `PER_STEP_MSE_BY_MODEL.csv` | 540 | 13 | `model`, `side`, `L`, `seed`, `step`, `weeks_ahead`, `mse_z_7var`, `mae_z_7var`, `mse_phys_agg`, `mse_z_wili`, `mse_phys_wili`, `mse_z_ilitotal`, `mse_phys_ilitotal` |
| `PER_STEP_PTE_PIE_BY_MODEL.csv` | 864 | 16 | `model`, `side`, `L`, `seed`, `step`, `weeks_ahead`, `series`, `n_seasons`, `PTE_wk`, `PIE_pct`, `PTE_max`, `PIE_max`, `n_season_pass`, `PTE_le_1wk`, … (+2) |
| `PER_STEP_PTE_PIE_PER_SEASON.csv` | 2,565 | 13 | `model`, `side`, `L`, `seed`, `step`, `weeks_ahead`, `series`, `gt_peak_week`, `gt_peak_val`, `pred_peak_week`, `pred_peak_val`, `PTE_wk`, `PIE_pct` |
| `PTE_PIE_GROUP_SUMMARY.csv` | 96 | 10 | `side`, `series`, `L`, `weeks_ahead`, `n_models`, `n_cells`, `n_pass`, `median_PTE`, `median_PIE`, `pass_rate_pct` |
| `TABLE_IX_REGIONAL_TRAINING_TIME.csv` | 2 | 18 | `model`, `region`, `L`, `seed`, `wall_seconds`, `minutes`, `gpu`, `run_device`, `partition`, `node`, `job_id`, `epochs`, `batch`, `K`, … (+4) |
| `TABLE_IX_REGIONAL_TRAINING_TIME_MEANS.csv` | 1 | 7 | `model`, `L`, `n_seeds`, `minutes_mean`, `minutes_sd`, `gpu`, `partition` |
| `TRACK_C_CELL_CLASSIFICATION.csv` | 96 | 6 | `model`, `L`, `seed`, `file`, `class`, `reason` |
| `TRACK_C_COST_SUMMARY.csv` | 14 | 2 | `item`, `value` |
| `TRACK_C_DELIVERABLE_MANIFEST.csv` | 36 | 5 | `deliverable`, `bytes`, `sha256`, `validation_status`, `path` |
| `TRACK_C_ILITOTAL_4L_MEAN.csv` | 8 | 6 | `model`, `n_cells`, `mse_z_ILITOTAL_4L`, `mae_z_ILITOTAL_4L`, `mse_physical_ILITOTAL_4L`, `mae_physical_ILITOTAL_4L` |
| `TRACK_C_ILITOTAL_CONSOLIDATED.csv` | 96 | 8 | `model`, `L`, `seed`, `mse_z_ILITOTAL`, `mae_z_ILITOTAL`, `mse_physical_ILITOTAL`, `mae_physical_ILITOTAL`, `source` |
| `TRACK_C_ILITOTAL_MSE_MAE.csv` | 8 | 15 | `model`, `track`, `n_seeds`, `mean_Test_MSE_4L`, `mean_Test_MAE_4L`, `n_raw_cells_found`, `n_raw_cells_required`, `MSE_z_ILITOTAL`, `MSE_physical_ILITOTAL`, `MAE_z_ILITOTAL`, `MAE_physical_ILITOTAL`, `physical_MSE_unit`, `physical_MAE_unit`, `status`, … (+1) |
| `TRACK_C_ILITOTAL_PER_L.csv` | 32 | 7 | `model`, `L`, `mse_z_ILITOTAL`, `mae_z_ILITOTAL`, `mse_physical_ILITOTAL`, `mae_physical_ILITOTAL`, `n_cells` |
| `TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv` | 2 | 2 | `side`, `mean_of_model_means_Test_MSE_4L` |
| `TRACK_C_MIFLU_RUN_MATRIX.csv` | 12 | 20 | `model`, `seed`, `horizon`, `window_train`, `window_validation`, `window_test`, `n_val_elements`, `n_test_elements`, `best_epoch`, `val_mse_z`, `test_mse_z`, `test_mae_z`, `total_parameters`, `trainable_parameters`, … (+6) |
| `TRACK_C_PAIRWISE_STATS_CORRECTED.csv` | 7 | 8 | `A`, `B`, `n_cells`, `mean_diff`, `median_diff`, `A_wins`, `B_wins`, `ties` |
| `TRACK_C_PER_HORIZON_CHAMPIONS.csv` | 32 | 5 | `L`, `model`, `mse`, `mae`, `rank` |
| `TRACK_C_PER_SEED_RANKINGS.csv` | 24 | 6 | `model`, `seed`, `mean_mse`, `mean_mae`, `n_L`, `rank_within_seed` |
| `TRACK_C_STEPWISE_MSE_PTE_PIE.csv` | 28 | 9 | `model`, `L`, `mse_7var`, `PTE_wk`, `PIE_pct`, `PTE_le_1wk`, `PIE_le_25pct`, `kramer_shaman_pass`, `hit_rate_pct` |
| `TRACK_C_TEST_MAE_RANKING.csv` | 8 | 4 | `rank_MAE`, `model`, `mean_Test_MAE_4L`, `mean_Test_MSE_4L` |
| `TRACK_C_TEST_MSE_RANKING.csv` | 8 | 7 | `rank_MSE`, `model`, `mean_Test_MSE_4L`, `sd_Test_MSE_4L`, `mean_Test_MAE_4L`, `side`, `n_seeds` |

## Provenance

Every value is re-derivable from the raw predictions in
`03_预测数据_证据/expanded_runs/**/pred_*.npz` (not in this pack), except the
reproduction table, which is gated against the per-seed oracle at |Δ| ≤ 1e-5 by
`05_程序代码/verify_miflu_oracle.py`.
