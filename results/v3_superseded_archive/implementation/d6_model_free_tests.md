# D6 model-free tests

Generated 2026-09-16T16:38:09Z.

- no real tokenizer or model was loaded; fake tokenizer/backbone used
- monkey-patched to fail: `from_pretrained`, `socket.*`, `torch.cuda`

- suite: **53 passed, 1 skipped**

| ID | check | test | result |
|---|---|---|---|
| D6-T1 | GPT-2-like tokenizer without a pad token reuses EOS | `test_gpt2_without_pad_reuses_eos` | passed |
| D6-T2 | no vocabulary token added and no embedding resize | `test_no_vocab_growth_and_no_resize` | passed |
| D6-T3 | existing Qwen pad-token configuration is untouched | `test_qwen_existing_pad_token_is_untouched` | passed |
| D6-T4 | missing pad AND eos fails closed | `test_missing_pad_and_eos_fails_closed` | passed |
| D6-T5 | attention mask identifies non-padding tokens | `test_last_non_pad_selects_real_token` | passed |
| D6-T6 | TimeCMA uses the last non-padding token | `test_timecma_uses_last_non_padding_token` | passed |
| D6-T7 | CALF pooling/alignment ignores padded positions | `test_calf_pooling_ignores_padding` | passed |
| D6-T8 | single and batched prompt shapes are correct | `test_last_non_pad_shapes` | passed |
| D6-T9 | empty/fully-padded prompts do not corrupt selection | `test_prompt_edge_cases` | passed |
| D6-T10 | G1 train-only statistics remain required | `test_g1_statistics_still_required` | passed |
| D6-T11 | G2 routing and D5 Qwen snapshot remain correct | `test_g2_routing_and_d5_snapshot_unchanged` | passed |
| D6-T12 | source never resizes embeddings or adds tokens | `test_source_never_resizes_or_adds_tokens` | passed |
| D6-T13 | eight Pilot specs remain scientifically unchanged | `test_eight_pilot_specs_unchanged` | passed |

## Pilot specs after regeneration

| model | L | seed | stage | purpose | selection | paper | test |
|---|---|---|---|---|---|---|---|
| nlinear | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| gpt2_miflu | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| dlinear | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| patchtst | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| itransformer | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| qwen_time_llm | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| calf_llm | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |
| timecma_llm | 24 | 42 | pilot | infrastructure_verification_only | False | False | False |

specs carrying a stale aggregate: **NONE**
