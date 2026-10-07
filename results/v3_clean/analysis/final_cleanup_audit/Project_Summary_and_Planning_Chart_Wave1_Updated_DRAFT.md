# Project Summary and Planning Chart — Wave-1 Updated DRAFT

> **DRAFT — pending student / tutor review. Do NOT submit as final.**
> This draft preserves the original form structure and identity fields, and updates only the fields supported by the Wave-1 evidence pack. Original: `58324980_CHAN_Sing_Yeung_Project_Summary_and_Planning_Chart_202627A`.

---

## 1. Student and course identifiers
*(RETAIN unchanged — copy from the submitted original.)*

| Field | Value |
|-------|-------|
| Student ID | 58324980 |
| Student name | CHAN Sing Yeung |
| Course / programme | [RETAIN original] |
| Academic year / term | 2026/27 A |
| Supervisor | [RETAIN original] |

## 2. Project title
[RETAIN original title; if it over-claims LLM superiority, add the qualifier below.]

> Qualifier (recommended): "…with explicit reporting of Non-LLM baselines and the seasonal-naive reference."

## 3. Problem statement
*(UPDATE)*

It is unclear whether integrating frozen large language models into time-series forecasters yields accuracy that is (a) superior to lightweight linear models and (b) attributable to the text/LLM mechanism rather than to the underlying seasonality of influenza-like-illness (ILI) data.

## 4. Research question and objectives
*(UPDATE)*

**Research question:** Across four Non-LLM and four LLM-based forecasting architectures, which performs best under the frozen selection rule, and does the LLM family as a whole reliably outperform the Non-LLM family?

**Objectives:**

1. Run a pre-registered, seed-replicated (10 seeds × 4 horizons) benchmark of 8 architectures.
2. Identify best Non-LLM, best LLM, and overall Wave-1 validation champion under the frozen rule.
3. Ablate the LLM mechanism (LoRA, multimodal fusion, prompt components) to localize any text contribution.
4. Preserve strict test/holdout isolation and a quota-safe compact-checkpoint pipeline.

## 5. Completed methodology
*(UPDATE)*

| Item | Value |
|------|-------|
| Dataset | National ILI, seven variables, z-space (train-only normalization) |
| Horizons | 24, 36, 48, 60 |
| Seeds | 42–51 (10 frozen) |
| Early stopping | patience 7 |
| Selection rule | rank by `average_MSE_4L` (mean of per-horizon mean MSE, lower better); secondary `average_MAE_4L` |
| Execution | serial fail-stop controller, 580 accepted, 0 ledger FAIL, test/holdout 0/0 |

## 6. Models compared
*(UPDATE)*

| Family | Models |
|--------|--------|
| Non-LLM | nlinear, dlinear, patchtst (PatchTST-inspired), itransformer |
| LLM-based | gpt2_miflu, qwen_time_llm, calf_llm, timecma_llm |
| Deterministic references | seasonal_naive, last_value_naive |

## 7. Validated experimental scale
*(UPDATE)*

580 accepted rows = 320 primary + 8 baseline + 240 ablation + 12 negative control; 0 deleted / 0 duplicated.

## 8. Current progress and best Wave-1 result
*(REPLACE)*

| Result | Model | Value |
|--------|-------|-------|
| Best Non-LLM | nlinear | avg MSE 4L = 1.0698 (95% CI [1.0677, 1.0719]) |
| Best LLM | gpt2_miflu | avg MSE 4L = 0.7709 (95% CI [0.7200, 0.8217]) |
| Overall Wave-1 validation champion | gpt2_miflu | runner-up nlinear (paired t = −13.33, p = 3.13×10⁻⁷) |
| Family finding | Non-LLM (1.142) vs LLM (1.243) | p = 1.44×10⁻⁶ |
| Peak metrics (secondary) | nlinear (PIE 17.7%) / patchtst (PTE 1.61 wk) | gpt2_miflu mid-table (PTE 2.12 wk, PIE 41.5%) |

Caveat: the zero-parameter `seasonal_naive` beats `gpt2_miflu` at L24/L36/L48.

## 9. Contributions
*(REPLACE — conservative, evidence-supported)*

1. Empirical architecture comparison — pre-registered, seed-replicated, test-isolated benchmark of 8 Non-LLM/LLM architectures under a frozen selection rule.
2. Mechanism / ablation evidence — the LLM text contribution localized to the dataset-information component; LoRA and multimodal fusion statistically inert.
3. Reproducible quota-safe framework — fail-closed compact-checkpoint pipeline (580/580 accepted, 0 fail events, test/holdout 0/0).

## 10. Ablation and control work
*(UPDATE)*

6 ablations: only `without_dataset_information` significant (+12.85%, p = 0.004); LoRA / multimodality / task-instruction not significant. 12 executed negative controls (exploratory): zero_text −0.063, shuffled_text +0.081.

## 11. Remaining work
*(REPLACE)*

18 deferred negative controls pending Wave-2 (parent binding = `gpt2_miflu`); test/holdout sealed; final champion not frozen; final manuscript pending.

## 12. Revised timeline
*(REPLACE)*

1. Wave-2 deferred-control binding + execution.
2. Freeze audit + final champion selection (post-deferred-controls).
3. Test/holdout evaluation only after freeze.
4. Manuscript drafting and submission.

## 13. Risks and mitigations
*(REPLACE)*

| Risk | Mitigation |
|------|------------|
| LLM superiority over-claimed | report family-level result + seasonal_naive honestly |
| gpt2_miflu seed instability (SD 0.071) | report seed SD + 95% CI; ordering robust (non-overlapping CIs) |
| PTE/PIE (peak metrics) | now computed from reconstructed target week; secondary metric, never a tie-breaker |
| patchtst fidelity (no pretraining/RevIN) | carry "PatchTST-inspired" caveat |
| LLM cost (409× params, 28× time vs nlinear) | present cost table transparently |

## 14. Status labels
*(ADD — must appear verbatim)*

- Wave 1 complete
- 18 deferred controls pending binding/execution
- Test/holdout not accessed
- final champion not frozen
- final report/manuscript pending
