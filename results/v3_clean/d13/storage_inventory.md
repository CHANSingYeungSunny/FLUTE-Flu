# D13 storage inventory (2026-09-18T13:58:47Z)

- durable root: `/home/sychan552/innovation_durable` — **284** entries
- scratch root: `/gpfs1/scratch/sychan552` — **34** top-level entries
- files > 50 MiB: **82**

## Capacity model

- `home_used_gib_now` = 101.0
- `home_hard_limit_gib` = 100.0
- `home_soft_quota_gib` = 50.0
- `durable_total_gib` = 88.0
- `freed_if_legacy_weights_quarantined_gib` = 42.0
- `freed_if_partial_copy_quarantined_gib` = 5.1
- `wave1_big_weights_gib` = 40.4
- `remaining_rows_full_policy_gib` = {'qwen_time_llm': 201.2, 'calf_llm': 18.8, 'timecma_llm': 18.8, 'gpt2_miflu': 78.1, 'baseline': 0.0}
- `remaining_rows_full_policy_total_gib` = 316.9
- `verdict` = INFEASIBLE under the current full-copy policy: the remaining 375 rows would need ~317 GiB against a 100 GiB home hard limit. The compact-checkpoint policy is MANDATORY, and even then the Wave-1 durable footprint must first be reduced.
- `safety_margin_required_gib` = 20.0

## Deletion candidates (quarantine first, delete after)

- **38** candidates, **51.07 GiB**

| size GiB | class | path |
|---|---|---|
| 5.754 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L60_seed42/checkpoints/best_val_mse.pt` |
| 5.754 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L60_seed43/checkpoints/best_val_mse.pt` |
| 5.754 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L60_seed44/checkpoints/best_val_mse.pt` |
| 5.752 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L24_seed42/checkpoints/best_val_mse.pt` |
| 5.752 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L24_seed44/checkpoints/best_val_mse.pt` |
| 5.752 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_qwen_time_llm_L24_seed43/checkpoints/best_val_mse.pt` |
| 5.086 | H_PARTIAL_FAILED_COPY | `/home/sychan552/innovation_durable/screening/primary__qwen_time_llm__L24__seed46__w1/checkpoints/best_val_mse.pt` |
| 0.472 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L60_seed43/checkpoints/best_val_mse.pt` |
| 0.472 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L60_seed44/checkpoints/best_val_mse.pt` |
| 0.472 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L60_seed42/checkpoints/best_val_mse.pt` |
| 0.471 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L24_seed43/checkpoints/best_val_mse.pt` |
| 0.471 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L24_seed42/checkpoints/best_val_mse.pt` |
| 0.471 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_calf_llm_L24_seed44/checkpoints/best_val_mse.pt` |
| 0.47 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L60_seed43/checkpoints/best_val_mse.pt` |
| 0.47 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L60_seed44/checkpoints/best_val_mse.pt` |
| 0.47 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L60_seed42/checkpoints/best_val_mse.pt` |
| 0.469 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L24_seed44/checkpoints/best_val_mse.pt` |
| 0.469 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L24_seed42/checkpoints/best_val_mse.pt` |
| 0.469 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_timecma_llm_L24_seed43/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L60_seed42/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L60_seed43/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L60_seed44/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L60__seed42__20260915T030458Z__nogit/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L60__seed43__20260915T030754Z__nogit/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L60__seed44__20260915T031155Z__nogit/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L48__seed44__20260915T030052Z__nogit/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L48__seed43__20260915T025621Z__nogit/checkpoints/best_val_mse.pt` |
| 0.307 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L48__seed42__20260915T025321Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L36__seed42__20260915T024318Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L36__seed43__20260915T024719Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L36__seed44__20260915T025020Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L24_seed43/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L24_seed42/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/screening/screening_gpt2_miflu_L24_seed44/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L24__seed43__20260915T023717Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L24__seed42__20260915T023509Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L24__seed44__20260915T024018Z__nogit/checkpoints/best_val_mse.pt` |
| 0.306 | E_SUPERSEDED_MIFLU_BULK_REGENERABLE | `/home/sychan552/innovation_durable/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L24__seed42__20260914T225532Z__nogit/checkpoints/best_val_mse.pt` |

> No file has been deleted or moved. This manifest is create-only.
