# Gate 569016 failure-signature matrix (v3.10)

- Job: **569016** — FAILED `1:0`, `00:24:33`, `gpu-a100-06`, **1/19 passed**
- Root: `/scratch/sychan552/innovation_deploy_root_v3_clean4` (v3.10)
- Paths: **18/18** all rc=1
- Distinct traceback signatures: **2**
- Distinct failing lines: **[263, 330]**
- Missing directories: **['logs', 'predictions']**

## Root cause D11
`clean_runner.py` writes into `logs/` and `predictions/` without creating them. `metrics/` and `checkpoints/` DO get created, which is why those artifacts exist.

## Per-path matrix

| path_key | arm | model | exc | line | missing | data | model | trained | ckpt | metrics |
|---|---|---|---|---|---|---|---|---|---|---|
| ablation__without_dataset_information__L24__seed42__w1 | ablation | without_dataset_information | OSError | 330 | logs | True | True | True | True | False |
| ablation__without_input_variable_description__L24__seed42__w1 | ablation | without_input_variable_description | OSError | 330 | logs | True | True | True | True | False |
| ablation__without_lora__L24__seed42__w1 | ablation | without_lora | OSError | 330 | logs | True | True | True | True | False |
| ablation__without_lora_and_multimodality__L24__seed42__w1 | ablation | without_lora_and_multimodality | OSError | 330 | logs | True | True | True | True | False |
| ablation__without_multimodality__L24__seed42__w1 | ablation | without_multimodality | OSError | 330 | logs | True | True | True | True | False |
| ablation__without_task_instruction__L24__seed42__w1 | ablation | without_task_instruction | OSError | 330 | logs | True | True | True | True | False |
| baseline__last_value_naive__L24__seedna__w1 | baseline | last_value_naive | OSError | 263 | predictions | True | True | False | False | True |
| baseline__seasonal_naive__L24__seedna__w1 | baseline | seasonal_naive | OSError | 263 | predictions | True | True | False | False | True |
| negative_control__shuffled_text__L24__seed42__w1 | negative_control | shuffled_text | OSError | 330 | logs | True | True | True | True | False |
| negative_control__zero_text__L24__seed42__w1 | negative_control | zero_text | OSError | 330 | logs | True | True | True | True | False |
| primary__calf_llm__L24__seed42__w1 | primary | calf_llm | OSError | 330 | logs | True | True | True | True | False |
| primary__dlinear__L24__seed42__w1 | primary | dlinear | OSError | 330 | logs | True | True | True | True | False |
| primary__gpt2_miflu__L24__seed42__w1 | primary | gpt2_miflu | OSError | 330 | logs | True | True | True | True | False |
| primary__itransformer__L24__seed42__w1 | primary | itransformer | OSError | 330 | logs | True | True | True | True | False |
| primary__nlinear__L24__seed42__w1 | primary | nlinear | OSError | 330 | logs | True | True | True | True | False |
| primary__patchtst__L24__seed42__w1 | primary | patchtst | OSError | 330 | logs | True | True | True | True | False |
| primary__qwen_time_llm__L24__seed42__w1 | primary | qwen_time_llm | OSError | 330 | logs | True | True | True | True | False |
| primary__timecma_llm__L24__seed42__w1 | primary | timecma_llm | OSError | 330 | logs | True | True | True | True | False |

## Confirmed-working (previous repairs)

- **D8** import path: runner imports fine (all paths executed).
- **D9** backbone kwarg: 16/18 completed full training + checkpoint.
- **D10** gate run-key: baseline dirs use `seedna`.
- **Four metric artifacts** produced by both baselines.
- **Baseline no-checkpoint semantics** honoured.
