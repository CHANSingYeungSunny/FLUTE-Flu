# v3 architecture fidelity matrix (authoritative simplified protocol)

All eight candidates use the original GPT-2/MIFlu National-Illness workflow with `ILITOTAL`,
the verified train/validation/test split, train-only scaler and prompt statistics, and fixed
steps 0-3. The three LLM contracts remain component-distinct and are not implementations yet.

| model_key | fidelity/status | defining mechanism or limitation |
|---|---|---|
| `nlinear` | REFERENCE_FAITHFUL / READY_WITH_DISCLOSED_LIMITATIONS | normalized linear forecast |
| `dlinear` | REFERENCE_FAITHFUL / READY_WITH_DISCLOSED_LIMITATIONS | decomposition plus linear heads |
| `patchtst` | INSPIRED_SIMPLIFICATION / READY_WITH_DISCLOSED_LIMITATIONS | patch Transformer |
| `itransformer` | REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS / READY_WITH_DISCLOSED_LIMITATIONS | variate-token attention |
| `gpt2_miflu` | LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE / READY_WITH_DISCLOSED_LIMITATIONS | published paper, no official code snapshot |
| `qwen_time_llm` | INSPIRED / MODEL_ACCESS_USER_ACTION_REQUIRED | patching, prototype reprogramming, Prompt-as-Prefix, frozen Qwen |
| `calf_llm` | INSPIRED / READY_WITH_DISCLOSED_LIMITATIONS | temporal/text branches, matching, feature and output alignment |
| `timecma_llm` | INSPIRED / LICENSE_REVIEW_REQUIRED | dual branches, retrieval/alignment, last-token representation |

The approved figure template is reused directly; no Phase 0.6 result figure was generated.
