# Gate 570452 failure-signature matrix (v3.11)

- Job **570452** — FAILED `1:0`, `00:26:38`, `gpu-a100-03`, **1/19 passed**
- Root `/scratch/sychan552/innovation_deploy_root_v3_clean5` (innov-v3.11-artifact-directory-initialization)
- **ALL 18/18 runners returned `rc=0`**

## Headline
Every scientific and artifact check PASSES on all 18 paths. Only **three Gate-harness assertions (D12)** fail.

## Failing checks

- `artifact_completeness` — 2 paths
- `baseline_no_checkpoint` — 2 paths
- `checkpoint_file_present` — 16 paths

## Per-path

| run_key | rc | passed | failing checks |
|---|---|---|---|
| deferred_guard | None | True | [] |
| primary__nlinear__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__dlinear__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__patchtst__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__itransformer__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__gpt2_miflu__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__qwen_time_llm__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__calf_llm__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| primary__timecma_llm__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| baseline__last_value_naive__L24__seedna__w1 | 0 | False | ['artifact_completeness', 'baseline_no_checkpoint'] |
| baseline__seasonal_naive__L24__seedna__w1 | 0 | False | ['artifact_completeness', 'baseline_no_checkpoint'] |
| ablation__without_dataset_information__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| ablation__without_task_instruction__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| ablation__without_input_variable_description__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| ablation__without_lora__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| ablation__without_multimodality__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| ablation__without_lora_and_multimodality__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| negative_control__zero_text__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |
| negative_control__shuffled_text__L24__seed42__w1 | 0 | False | ['checkpoint_file_present'] |

## Root cause D12 (Gate harness only)

- `checkpoint_file_present` looks for `best_validation.pt`; the runner writes `best_val_mse.pt` (restore already succeeded).
- `baseline_no_checkpoint` requires the `checkpoints/` DIRECTORY to be absent, but the D11 initializer creates it for every run — the audit must assert the semantic property instead.
- `artifact_completeness` uses one shared list that is not baseline-aware.

> Runner behaviour and the scientific protocol are unchanged and correct; Gate outputs remain infrastructure diagnostics only.
