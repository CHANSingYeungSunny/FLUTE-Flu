# Qwen2.5-1.5B Time-LLM-inspired — component implementation contract

Official basis: Time-LLM (ICLR 2024), https://github.com/KimMeen/Time-LLM,
pinned commit `b13e881f86cd0475ce1b72c17110430663334955`, Apache-2.0.

## Frozen data flow

```
window X (T=104, C=7, z-space)
  -> instance norm / revin (train-statistics only)
  -> PATCHING            : split each channel into patches (patch_len P, stride S)
  -> PROTOTYPE REPROGRAMMING : learnable text-prototype attention maps patched
                               series into the LLM embedding space (d_model=1536)
  -> PROMPT-AS-PREFIX    : declarative prefix tokens (dataset description, task
                           instruction, train-only statistics) embedded and
                           prepended to the reprogrammed series
  -> FROZEN QWEN2.5-1.5B : backbone kept frozen; no backbone weight update
  -> FORECAST PROJECTION : linear head over the forecast token positions -> L
```

## Mandatory components (all must be present)

| Component | Requirement | How verified |
|---|---|---|
| patching | patch_len/stride preregistered; channel-independent or channel-mixed declared | shape test |
| prototype reprogramming | learned prototypes + mapping into LLM embedding space, NOT a plain linear layer | component test + gradient test |
| Prompt-as-Prefix | prefix built from declarative text; statistics computed on TRAIN only | leakage test |
| frozen Qwen backbone | `requires_grad=False` for every backbone parameter | parameter-freeze assertion |
| forecast projection head | maps hidden states to the full horizon L in one head | shape test |

## Deviations to disclose

- Backbone is Qwen2.5-1.5B, whereas the official default is Llama-7B. The official
  README explicitly supports alternate backbones via `--llm_model` / `--llm_dim`.
- No self-supervised pretraining stage.
- Patch/prototype sizes are preregistered, not searched.

## NOT allowed

- Implementing this as "a linear model plus an LLM name".
- Sharing the reprogramming module with CALF/TimeCMA such that the three become identical.
