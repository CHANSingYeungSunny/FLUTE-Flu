# Fresh pre-Pilot Gate status

Generated 2026-09-16T16:10:53Z.

Job **565844** — `stingy`, `gpu-a100-03`, `--exclude=gpu-a100-05` (two evidence-backed CUDA failures occurred there).

**State: FAILED (1:0, 00:00:36). 7/8 models passed. No Pilot submitted.**

| model | result |
|---|---|
| nlinear | OK |
| dlinear | OK |
| patchtst | OK |
| itransformer | OK |
| gpt2_miflu | OK |
| qwen_time_llm | **FAILED** |
| calf_llm | OK |
| timecma_llm | OK |

## What this proves

- **D5 is resolved**: Qwen loaded **offline from the verified snapshot** (`/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/8faed761d45a263340a0528343f099c05c9a4323`).
- **The GPT-2 cache fix worked**: CALF (3.2 s) and TimeCMA (2.0 s) now build and backpropagate, where previously all three LLM branches failed.
- CUDA is healthy on gpu-a100-03; the earlier failures were node-specific.

## Why the Gate still failed

- **G1** the gate harness omits `set_train_statistics(...)` before the Qwen forward pass, so `forward` raises *"train-only Prompt-as-Prefix statistics were not set"* — the runtime contract is correct, the harness call is missing.
- **G2** the harness passed `model_id=Qwen/Qwen2.5-1.5B` to CALF and TimeCMA, overriding their preregistered `gpt2` backbone.

Both are confined to `hpc_scripts/v3_prepilot_gate.py`, which sits **outside** the 87-file frozen runtime source, so fixing them needs no scientific cascade — but the Gate must reach **8/8** before any Pilot may be submitted, and this prompt grants no further Gate retry.
