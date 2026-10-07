# G1/G2 Gate-harness repair audit

Generated 2026-09-16T16:20:39Z.

- harness version **`v3-prepilot-gate-g1g2-fixed`**
- scope **harness only**; frozen runtime source, bundle and deployment root are unchanged

## G1 — Qwen train-statistics initialization

- symptom: `RuntimeError: train-only Prompt-as-Prefix statistics were not set`
- cause: the harness never called the model's official API before `forward`
- repair: `train_only_prompt_statistics()` builds the statistics **exclusively** from `raw.iloc[: scaler.train_end]`; the harness calls `set_train_statistics(...)` before forward and fails closed if the model does not accept them
- provenance: training split only, `contains_validation_or_test = false`

## G2 — per-model backbone routing

- symptom: CALF and TimeCMA ran on Qwen rather than their preregistered GPT-2
- cause: the harness sent `model_id=Qwen` to every LLM branch; both constructors accept `model_id`, so broad `**kwargs` filtering did not stop it
- repair: explicit `MODEL_ROUTING` per model contract plus `assert_no_qwen_leakage()`

| model | backbone | extra kwargs |
|---|---|---|
| qwen_time_llm | Qwen/Qwen2.5-1.5B (verified snapshot) | model_id, load_backbone |
| calf_llm | gpt2 | load_backbone |
| timecma_llm | gpt2 | load_backbone |
| gpt2_miflu | gpt2_miflu_control | none |
| nlinear/dlinear/patchtst/itransformer | none | none |

## Hashes

- pre-repair `v3_prepilot_gate.py`: `4377592be45e275c1bf7a5424face4980c0fae64c1f51f3fa1cd67bec215a13e`
- post-repair `v3_prepilot_gate.py`: `942804cc2b415a1c8ca02dd981d216ff658b991fadbd318eb36f3046fc025758`
- pre-repair `v3_prepilot_gate.sh`: `de0382f68c7d4aa240f19545a91dc8b2c0a4254c0cd4252cf51b746e2d6a8848`
- post-repair `v3_prepilot_gate.sh`: `de0382f68c7d4aa240f19545a91dc8b2c0a4254c0cd4252cf51b746e2d6a8848`
- textual diff: `results/v3/implementation/g1_g2_harness_repair.diff` (8312 bytes)

## Classification

**BEHAVIOR_NEUTRAL_HARNESS_ONLY.** No dataset, split, target, scaler, prompt statistic, architecture mechanism, dimension, loss, early-stopping rule, metric, fixed-step mapping, candidate set or search budget was changed.
