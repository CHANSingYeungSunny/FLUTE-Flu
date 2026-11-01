# Blockers & Next Steps

> Last updated: 2026-10-30 (round 2). Status: **PARTIAL_REPRODUCTION**.

## Resolved (local fixes applied)

| Issue | Resolution |
|-------|-----------|
| Paper title wrong (was "Hong Kong") | Corrected to "MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme" (US CDC National-Illness) |
| Project attribution | Clarified: CHAN Sing Yeung Sunny is sole author; Moon et al. is reference paper |
| 7-variable denormalization invalid | Documented: must extract ILITOTAL-only first; 7-var aggregate stays z-space |
| Peak criteria misattribution | Corrected: 31/36 is **DLinear**, not MIFlu. Actual: NLinear 36/36, DLinear 31/36, MIFlu 15/36 |
| Peak lead time confusion | Documented: peak analysis uses k=1 (one-week-ahead), not L=24–60 |
| `r1b_model.py` missing from zip | Added to handoff zip (`05b_r1b_model/`) |
| `HPC_GUIDE.md` missing from zip | Added to handoff zip (`00b_HPC_GUIDE.md`) |
| `peak_criteria.json` missing | **RECONSTRUCTED** by ChatGPT from frozen CSV evidence → `results/v3_clean/analysis/peak_criteria/peak_criteria.json` |
| ILITOTAL-only MSE for MIFlu | **COMPUTED**: 3.7020 z² = 300,071,219.88 patient-count² |
| C2 scheduler experiment | **PREPARED**: `hpc_experiments/submit_c2.sh` (12-cell sweep, not yet run) |
| LLM arm experiments | **PREPARED**: `hpc_experiments/submit_qwen.sh`, `submit_deepseek.sh` (48 cells planned, not yet run) |
| Expanded benchmark tables | **INTEGRATED**: `paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv` (19 instances, 76 per-L rows) |

## Remaining Blockers

| Blocker | What's needed | Priority |
|---------|---------------|----------|
| **C2 experiment not executed** | Run `hpc_experiments/submit_c2.sh` on HPC (`burgundy.hpc.cityu.edu.hk`) | HIGH |
| **LLM arms not executed** | Download Qwen/DeepSeek weights, run `submit_qwen.sh` / `submit_deepseek.sh` on HPC | HIGH |
| **7 non-MIFlu ILITOTAL scores = NA** | Extract `test_eval_download.tar.gz` for raw predictions → run `hpc_experiments/score_ilitotal.py` | MEDIUM |
| **HPC unreachable from ChatGPT** | User must submit jobs manually or provide HPC access | HIGH |

## Files Produced (ChatGPT round 2)

| File | Location | Content |
|------|----------|---------|
| `peak_criteria.json` | `results/v3_clean/analysis/peak_criteria/` | Reconstructed CONSENSUS with per-model/per-L/per-seed data |
| `TRACK_C_ILITOTAL_MSE_MAE.csv` | `paper_tables/` | ILITOTAL-only MSE/MAE (MIFlu computed, others NA) |
| `EXPANDED_COMBINED_TEST_MSE_RANKING.csv` | `paper_tables/` | 19-model combined ranking |
| `submit_c2.sh` | `hpc_experiments/` | C2 scheduler HPC job |
| `submit_qwen.sh` | `hpc_experiments/` | Qwen LLM arm HPC job |
| `submit_deepseek.sh` | `hpc_experiments/` | DeepSeek LLM arm HPC job |
| `run_llm_features.py` | `hpc_experiments/` | LLM feature extraction runner |
| `score_ilitotal.py` | `hpc_experiments/` | ILITOTAL-only scorer |

## Next Actions (for user)

1. **Submit C2 job on HPC**: `ssh sychan552@burgundy.hpc.cityu.edu.hk "sbatch hpc_experiments/submit_c2.sh"`
2. **Download LLM weights**: `bash hpc_experiments/download_llm_weights.sh`
3. **Submit LLM jobs**: `sbatch submit_qwen.sh` then `sbatch submit_deepseek.sh`
4. **Extract test_eval_download.tar.gz** when available → run `score_ilitotal.py` for remaining 7 models
5. **Pull results**: `bash hpc_experiments/pull_results.sh`
