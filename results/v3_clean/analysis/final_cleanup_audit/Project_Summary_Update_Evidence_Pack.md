# Project Summary Update — Evidence Pack

**Target document:** `58324980_CHAN_Sing_Yeung_Project_Summary_and_Planning_Chart_202627A` (not present in workspace; must NOT be overwritten — this pack provides versioned update content only).
**Source of truth:** `results/v3_clean/analysis/` (frozen protocol snapshot, analysis dataset, statistics, figures).
**Status:** Wave-1 complete (580/580 accepted). 18 deferred controls pending. Test/holdout sealed (0/0). Final champion not frozen.

---

## 1. Confirmed final project scope

Empirical and mechanistic comparison of Non-LLM versus LLM-based forecasting architectures for influenza-like-illness (ILI) forecasting, executed under a pre-registered ("frozen") selection rule on the national ILI dataset, with strict test/holdout isolation.

## 2. Problem statement

It is unclear whether integrating frozen large language models into time-series forecasters yields accuracy that is (a) superior to lightweight linear models and (b) attributable to the text/LLM mechanism rather than to the underlying seasonality of ILI data.

## 3. Research question

Across four Non-LLM and four LLM-based forecasting architectures, which performs best under the frozen selection rule, and does the LLM family as a whole reliably outperform the Non-LLM family?

## 4. Objectives

1. Run a pre-registered, seed-replicated (10 seeds × 4 horizons) benchmark of 8 architectures.
2. Identify best Non-LLM, best LLM, and overall Wave-1 validation champion under the frozen rule.
3. Ablate the LLM mechanism (LoRA, multimodal fusion, prompt components) to localize any text contribution.
4. Preserve strict test/holdout isolation and a quota-safe compact-checkpoint pipeline.

## 5. Completed methodology

- Dataset: national ILI, seven variables, z-space (train-only normalization).
- Horizons L ∈ {24, 36, 48, 60}; 10 frozen seeds 42–51; early stopping (patience 7).
- Frozen selection rule: rank by `average_MSE_4L` (mean of per-horizon mean MSE, lower better); key secondary `average_MAE_4L`; forbidden tie-breakers (peak-hit ratio, PTE/PIE, baseline-relative ratio, (r24+r60)/2).
- Execution: serial fail-stop controller, 580 rows accepted, 0 ledger FAIL events, test/holdout 0/0.

## 6. Models compared

- Non-LLM: `nlinear`, `dlinear`, `patchtst` (PatchTST-inspired), `itransformer`.
- LLM-based: `gpt2_miflu`, `qwen_time_llm`, `calf_llm`, `timecma_llm`.
- Deterministic references: `seasonal_naive`, `last_value_naive`.

## 7. Validated experimental scale

580 accepted rows = 320 primary + 8 baseline + 240 ablation + 12 negative control; 0 deleted / 0 duplicated.

## 8. Completed milestones

- Frozen protocol + selection rule recovered and verified (HPC_GUIDE SHA-256 verified).
- 580/580 durable packages reconciled; analysis dataset built (1 row/run).
- Primary ranking, family comparison, horizon/seed stability, baselines, ablations, controls, efficiency — all computed.

## 9. Current best Wave-1 validation result

- **Best Non-LLM:** `nlinear` — average MSE 4L = **1.0698** (95% CI [1.0677, 1.0719]).
- **Best LLM:** `gpt2_miflu` — average MSE 4L = **0.7709** (95% CI [0.7200, 0.8217]).
- **Overall Wave-1 validation champion:** `gpt2_miflu` (0.771); runner-up `nlinear` (1.070). Winner-vs-runner paired t = −13.33, p = 3.13×10⁻⁷.

## 10. LLM versus Non-LLM finding

The Non-LLM **family** (mean 1.142) is significantly more accurate than the LLM family (mean 1.243): paired t = −11.15, p = 1.44×10⁻⁶. The LLM win is one model (`gpt2_miflu`), not the paradigm. Additionally, the zero-parameter `seasonal_naive` beats `gpt2_miflu` at L24/L36/L48 (0.719/0.732/0.746 vs 0.732/0.778/0.760).

## 11. Completed ablation / control work

- 6 ablations: only `without_dataset_information` significant (+12.85%, p = 0.004); `without_lora` (p = 0.95), `without_multimodality` (p = 0.47), `without_task_instruction` (p = 0.40) not significant.
- 12 executed negative controls (exploratory, n = 6 cells): `zero_text` −0.063 (slightly better), `shuffled_text` +0.081 (worse).

## 12. Remaining 18 deferred controls

18 negative controls deferred to Wave-2; parent binding = BEST_VALIDATION_LLM_AFTER_SCREENING (= `gpt2_miflu`). Not run in Wave-1.

## 13. Remaining Test / holdout stage

Test and holdout remain sealed (access 0/0). Final publication champion not frozen. Final manuscript pending.

## 14. Revised timeline

1. Wave-2 deferred-control binding + execution.
2. Freeze audit + final champion selection (post-deferred-controls).
3. Test/holdout evaluation only after freeze.
4. Manuscript drafting and submission.

## 15. Risks and mitigations

| risk | mitigation |
|---|---|
| LLM "superiority" over-claimed | report family-level result + seasonal_naive honestly |
| gpt2_miflu seed instability (SD 0.071) | report seed SD + 95% CI; ordering still robust (non-overlapping CIs) |
| PTE/PIE (peak metrics) | now computed from reconstructed target week; secondary metric, never a tie-breaker |
| patchtst fidelity (no pretraining/RevIN) | carry "PatchTST-inspired" caveat |
| LLM cost (409× params, 28× time vs nlinear) | present cost table transparently |

## 16. Expected deliverables

Supervisor report (EN/ZH, DOCX/PDF), tutor brief (EN/ZH), evidence pack + change map, updated Project Summary draft (DOCX/PDF), QA + artifact manifests, all source tables/figures.

## 17. Three evidence-supported contributions (conservative wording)

1. **Empirical architecture comparison** — a pre-registered, seed-replicated (10 seeds × 4 horizons), test-isolated benchmark of 8 Non-LLM/LLM architectures under a frozen selection rule.
2. **Mechanism / ablation evidence** — localization of the LLM text contribution to the dataset-information component, with LoRA and multimodal fusion shown to be statistically inert.
3. **Reproducible quota-safe framework** — a fail-closed, compact-checkpoint experimental pipeline (580/580 accepted, 0 fail events, test/holdout 0/0) with bit-exact checkpoint compaction.
