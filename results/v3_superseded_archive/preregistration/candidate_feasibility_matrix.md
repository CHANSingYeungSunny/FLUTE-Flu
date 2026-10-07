# v3 candidate feasibility matrix (authoritative simplified protocol)

All candidates use the original GPT-2/MIFlu National-Illness data, `ILITOTAL`, verified split, train-only scaler/prompt statistics, horizons 24/36/48/60, formal seeds 42..51, and fixed steps 0..3. No external data or new holdout is active.

| model_key | group | status | limitation |
|---|---|---|---|
| `nlinear` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | reference-faithful implementation pending Phase 1 |
| `dlinear` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | reference-faithful implementation pending Phase 1 |
| `patchtst` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | inspired simplification disclosed |
| `itransformer` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | aligned deviations disclosed |
| `gpt2_miflu` | B_llm | READY_WITH_DISCLOSED_LIMITATIONS | local reconstruction with published-paper provenance |
| `qwen_time_llm` | B_llm | MODEL_ACCESS_USER_ACTION_REQUIRED | Qwen asset download/cache authorization pending |
| `calf_llm` | B_llm | READY_WITH_DISCLOSED_LIMITATIONS | inspired component contract pending implementation |
| `timecma_llm` | B_llm | LICENSE_REVIEW_REQUIRED | S-Lab License 1.0 review pending |

The two naive baselines remain references only. Negative controls remain validation-only secondary analyses.
