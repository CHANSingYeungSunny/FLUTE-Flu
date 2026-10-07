# v3 architecture equivalence report (static)

Generated 2026-09-16T08:38:52Z.
No model was constructed or loaded to produce this report; all checks are static

- implementation source: `scripts/innovation/backbones/llm_inspired.py`
- source SHA-256: `1dc2d8358a304a5ea17fc31d7c5f223861001161fff1797e954a79f652c0e6da`
- all defining components present (static): **True**
- import-time hazards: {'module_level_from_pretrained': False, 'from_pretrained_occurrences_in_module': 2, 'load_is_opt_in': True, 'raises_if_not_loaded': True}

## Component evidence

| architecture | component | present | evidence |
|---|---|---|---|
| QwenTimeLLM | time_series_patching | True | `patch_projection,patch_len` |
| QwenTimeLLM | prototype_based_reprogramming | True | `prototype_bank,prototype_query` |
| QwenTimeLLM | prompt_as_prefix | True | `build_prompt_as_prefix,set_train_statistics` |
| QwenTimeLLM | frozen_qwen_backbone | True | `_FrozenTextModel,load_backbone` |
| QwenTimeLLM | forecast_projection | True | `forecast_projection` |
| CALFInspired | temporal_target_branch | True | `temporal_branch,temporal_projection` |
| CALFInspired | textual_source_branch | True | `text,text_projection` |
| CALFInspired | cross_modal_matching | True | `cross_modal_match` |
| CALFInspired | feature_regularization_in_loss | True | `feature_regularization_loss` |
| CALFInspired | output_consistency_in_loss | True | `output_consistency_loss` |
| TimeCMAInspired | independent_time_series_branch | True | `time_series_branch` |
| TimeCMAInspired | independent_llm_prompt_branch | True | `text,prompt_projection` |
| TimeCMAInspired | cross_modality_retrieval | True | `retrieve_aligned_prompt,retrieval_query` |
| TimeCMAInspired | last_token_or_cached_prompt | True | `retrieve_aligned_prompt` |
| TimeCMAInspired | forecast_head | True | `forecast_head` |

## Distinctness argument

The three inspired architectures share only the frozen-backbone policy and a forecast
projection. Their defining mechanisms are disjoint:

- **Qwen Time-LLM-inspired**: patch projection into a prototype bank (`prototype_bank`, `prototype_query`) plus Prompt-as-Prefix built from train-only statistics. No temporal target branch, no consistency loss, no retrieval.
- **CALF-inspired**: parallel temporal/text branches joined by `cross_modal_match`, optimised with BOTH `feature_regularization_loss` and `output_consistency_loss`. No patch prototypes, no retrieval.
- **TimeCMA-inspired**: independent time-series and prompt branches joined by similarity retrieval (`retrieve_aligned_prompt`) using the last prompt token. No prototypes, no consistency loss.

They are therefore not 'the same model with three names'. Runtime shape, gradient and
component assertions are deferred to the compute-node Slurm gate.

## Provenance

- Sources are clean-room, paper-derived. No upstream repository source is copied.
- MIFlu/GPT-2 keeps `LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE`; we never claim official author code.
