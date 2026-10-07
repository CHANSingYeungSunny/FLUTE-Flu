# Screening metric contract (frozen before submission)

Generated 2026-09-16T21:06:49Z.

## Family A — paper-style full-horizon

- normalized (z-space) MSE and MAE over the complete seven-variable, multi-step output for the horizon
- fields: `mse_all_z`, `mae_all_z`, `mse_ili_phys`, `mae_ili_phys`
- substituting step-0 MSE for full-horizon MSE is **forbidden**

## Family B — ILITOTAL fixed-step

- steps 0/1/2/3 = fixed 1/2/3/4-week-ahead
- step 0 is the primary fixed-step endpoint; steps 1-3 are supplementary
- per step: `mse_z`, `mae_z`, `mse_phys`, `mae_phys`, `pte_weeks`, `pie_pct`, `peak_criterion_pass`
- peak criterion: **PTE <= 1 week AND PIE <= 25%**
- predictions are **never averaged or merged across steps**

## Scope

- horizons [24, 60], seeds [42, 43, 44]
- Group A (Non-LLM): `nlinear`, `dlinear`, `patchtst`, `itransformer`
- Group B (LLM-based): `gpt2_miflu`, `qwen_time_llm`, `calf_llm`, `timecma_llm`
- reference baselines outside 4-vs-4: `last_value_naive`, `seasonal_naive`
- Screening uses **validation data only**; Pilot metrics are excluded.
