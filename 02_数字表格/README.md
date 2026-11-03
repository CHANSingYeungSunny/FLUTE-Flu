# paper_tables/ — Authoritative Tables (Flat Copies)

These are flat copies of the authoritative TRACK_C tables used in the manuscript.
The originals live in `hpc_results/official_repo_reproduction_20261006/r1_v2_verification_20261007/docx_inputs/` (SHA-verified, unchanged).

| File | Description |
|------|-------------|
| `TRACK_C_TEST_MSE_RANKING.csv` | **Primary ranking**: test MSE for all 36 cells (4 models × 3 horizons × 3 seeds) |
| `TRACK_C_TEST_MAE_RANKING.csv` | Test MAE ranking (secondary metric) |
| `TRACK_C_PER_HORIZON_CHAMPIONS.csv` | Best model per horizon |
| `TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv` | Group means: LLM vs Non-LLM |
| `TRACK_C_CELL_CLASSIFICATION.csv` | Per-cell classification (seed42 L24 cells) |
| `TRACK_C_PAIRWISE_STATS_CORRECTED.csv` | Pairwise MIFlu vs baseline comparisons |
| `TRACK_C_PER_SEED_RANKINGS.csv` | Rankings per seed |
| `TRACK_C_MIFLU_RUN_MATRIX.csv` | MIFlu run matrix (4 configs) |
| `TRACK_C_COST_SUMMARY.csv` | Computational cost summary |
| `TRACK_C_DELIVERABLE_MANIFEST.csv` | Deliverable manifest |
| `TRACK_C_SHA256_MANIFEST.txt` | SHA256 integrity manifest |

> **Note**: All numbers use strict 966-row data with zero tolerance for missing values. MSE ≠ accuracy. See `../README.md` "Reproducibility & Honesty Notes" for the seven hard constraints.

> **中文**：以上为论文权威表平铺副本。所有数字基于严格 966 行数据（零容忍缺失值）。MSE ≠ accuracy。七条硬约束见根目录 README。
