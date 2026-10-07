# Final pre-Pilot Gate status

Generated 2026-09-16T16:27:02Z.

Job **565860** — `stingy`, `gpu-a100-03`, `--exclude=gpu-a100-05`, harness `v3-prepilot-gate-g1g2-fixed`, create-only output `gate_565860/`.

**State: FAILED (1:0, 00:00:20). 6/8 models passed. No Pilot submitted.**

| model | result |
|---|---|
| nlinear | OK |
| dlinear | OK |
| patchtst | OK |
| itransformer | OK |
| gpt2_miflu | OK |
| qwen_time_llm | OK |
| calf_llm | FAILED |
| timecma_llm | FAILED |

## G1 — repaired and proven

`qwen_time_llm` now passes (**1.7 s**): the harness calls `set_train_statistics(...)` before `forward`, with statistics derived exclusively from the frozen training split (`raw.iloc[: scaler.train_end]`).

## G2 — repaired and proven

| model | backbone kwargs |
|---|---|
| qwen_time_llm | `model_id=Qwen/Qwen2.5-1.5B, load_backbone=True` |
| calf_llm | `load_backbone=True` (keeps preregistered **gpt2**) |
| timecma_llm | `load_backbone=True` (keeps preregistered **gpt2**) |
| gpt2_miflu | none |

The leakage guard passed: no non-Qwen model received any Qwen argument.

## New defect D6 (frozen runtime, not the harness)

With G2 fixed, CALF and TimeCMA correctly load GPT-2 — and then fail:

```
ValueError: Asking to pad but the tokenizer does not have a padding token.
Please select a token to use as `pad_token` (tokenizer.pad_token =
tokenizer.eos_token e.g.) or add a new pad token via
tokenizer.add_special_tokens({'pad_token': '[PAD]'})
```

`_FrozenTextModel.encode_prompt` calls the tokenizer with `padding=True`. Qwen's tokenizer has a pad token; **GPT-2's does not**. This is a genuine defect in the frozen runtime source, so per the repair scope it cannot be patched by the harness.

## Decision

Gate reached only 6/8. This prompt authorizes **no further Gate retry** and no Pilot submission. Evidence for all five Gate jobs is preserved.
