# D6 GPT-2 padding repair audit

Generated 2026-09-16T16:38:09Z.

## Root cause

`_FrozenTextModel.encode_prompt` requested `padding=True`. Qwen's tokenizer defines a pad token; **GPT-2's does not**, so CALF and TimeCMA raised as soon as G2 routed them back to their preregistered GPT-2 backbone.

## Repair

- reuse the **existing EOS token** as the pad token when none is defined;
- **no** new vocabulary entry and **no** embedding resize (pretrained weights untouched);
- fail closed when neither pad nor eos exists;
- `encode_prompt` now returns `(hidden_states, attention_mask)`;
- CALF pools/aligns/regularises on the last **non-padding** token;
- TimeCMA retrieves the last **non-padding** token via the mask;
- Qwen is unchanged (its pad token already exists).

## Classification

**BEHAVIOR_CORRECTING_TOKENIZER_COMPATIBILITY_FIX** — a runtime-source change, so the full version/snapshot/bundle/deployment cascade is required.

## Hashes

- pre-repair `llm_inspired.py`: `ba6af7bc4053c459d5427b5dc871fb7fa268a17bb95e0b882886be3e6760f816`
- post-repair `llm_inspired.py`: `571237573439d972c9324cb1a931d180c91cdc06ccdf0ce4aaebf6d40301f45d`
- diff: `results/v3/implementation/d6_repair.diff` (9462 bytes)
- new aggregate: `94886a2980b7717e2db938bc851550f2e30d0b64a403eef374d8908a87155f2b`
- new bundle: `c0fff202849c03db57fb0f729e3128516b93dac66fa68deb78f9e52bb535f66f`
