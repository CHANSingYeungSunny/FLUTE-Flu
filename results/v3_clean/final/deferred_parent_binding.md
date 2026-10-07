# Deferred-Parent Binding — BEST_VALIDATION_LLM_AFTER_SCREENING = gpt2_miflu

## 1. What happened

The pre-registered **deferred-parent binding rule** (`deferred_parent_binding_rule.json`) left the parent of the
18 Wave-2 deferred controls as the placeholder `BEST_VALIDATION_LLM_AFTER_SCREENING`, to be resolved only after the
complete clean-v3 primary validation phase finished. That phase is now complete (580/580 ACCEPTED). This binding
executes the rule lawfully and resolves the placeholder.

## 2. The rule (pre-existed, immutable)

- Source: `results/v3_clean/preregistration/deferred_parent_binding_rule.json`
- Generated: `2026-09-17T15:52:55Z` — **before any Wave-1 result was viewed**.
- SHA-256: `d0f708796e353017f1212ce4e2a4244d47582937117116049da2e0da5dae6b13`

Steps (verbatim):
1. compare ONLY the four LLM primary candidates;
2. use the full seven-variable, full-horizon z-space MSE;
3. average over seeds 42..51 within each L;
4. take the arithmetic average over L = {24,36,48,60};
5. the LLM with the lowest `average_MSE_4L` becomes the parent of the deferred controls.

Forbidden for binding: old v3 ranking / checkpoint / prediction / candidate list, ILITOTAL fixed-step metrics,
PTE/PIE, resource cost, GPT-relative ratio, naive-relative ratio, `(r24+r60)/2`.

Equivalence policy: if a top-equivalence set arises, STOP and await adjudication — do not arbitrarily pick one LLM.

## 3. The selection outcome (frozen rule applied)

- Selection rule: `results/v3_clean/preregistration/paper_aligned_selection_rule.json`
  (SHA-256 `afa7a780010aeed20fd7a2d361300ae2ce4411baeed1d458581538d3df359325`).
- Outcome: `results/v3_clean/analysis/selection_outcome.json`
  (SHA-256 `f93e711288023703b7c6ed7818009e7598c70f6dc9ed4c9274691ea16f667dc4`).

| Field | Value |
| --- | --- |
| LLM family | `gpt2_miflu`, `qwen_time_llm`, `calf_llm`, `timecma_llm` |
| `best_llm` | **gpt2_miflu** |
| `best_llm` average_MSE_4L | **0.7708721562796242** |
| `top_equivalence_set` | `[]` (empty — no adjudication needed) |
| winner vs runner-up (nlinear) | paired t = −13.33, p = 3.13e−07 |

`gpt2_miflu` is the unique LLM with the lowest `average_MSE_4L`; no equivalence set was reported, so the
equivalence-policy STOP clause was not triggered.

## 4. Resolution

```
BEST_VALIDATION_LLM_AFTER_SCREENING  =  gpt2_miflu
```

- The 18 deferred Wave-2 controls now have `parent_model = gpt2_miflu` and are submittable.
- The 12 Wave-1 fixed-parent negative controls (already `gpt2_miflu`) are unaffected.

## 5. Deferred controls (18) now submittable

| Control | Horizons × Seeds | Count |
| --- | --- | --- |
| `zero_text` | L24, L60 × {42,43,44} | 6 |
| `shuffled_text` | L24, L60 × {42,43,44} | 6 |
| `llm_removed_or_alignment_only` | L24, L60 × {42,43,44} | 6 |

All 18 are `arm = negative_control`, `wave = 2`, `submittable = true` after this binding.

## 6. Identity locks

- Base model: **gpt2** backbone (`TextualInputEmbedder` / `gpt2_miflu` adapter).
- Source version: `innov-v3.19-baseline-no-checkpoint-finalization`,
  aggregate SHA-256 `ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa`.
- gpt2-related source files hash-locked (see JSON `selected_parent_base_model_identity.gpt2_related_source_files`).
- Prompt/config artifacts hash-locked from HPC durable evidence
  (see JSON `selected_parent_prompt_config_identity`).
- Supporting accepted rows: 40 gpt2_miflu primary rows, horizons {24,36,48,60} × seeds {42..51}.

## 7. Timestamps & isolation

- Rule generated: `2026-09-17T15:52:55Z` (pre-existed).
- Wave-1 controller completion: `2026-09-20T05:27:50Z`.
- Frozen analysis protocol: `2026-09-20T06:10:00Z`.
- Binding executed: `2026-09-21T00:14:51Z`.
- Test access = 0, Holdout access = 0. Selection rule never mutated. No post-hoc selection.

---

Machine-readable record: `deferred_parent_binding.json`.
Hash manifest: `deferred_parent_binding_hash_manifest.json`.
