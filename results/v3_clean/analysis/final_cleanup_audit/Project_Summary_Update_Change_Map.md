# Project Summary & Planning Chart — Change Map

**Target:** `58324980_CHAN_Sing_Yeung_Project_Summary_and_Planning_Chart_202627A`
**Important:** the original form is **not present in the workspace**. The field names below are the *typical* sections of a CityUHK "Project Summary and Planning Chart" and must be checked against the actual form by the student before applying. This map identifies every section as **retain** / **update** / **replace**, with the exact proposed wording and the evidence source. Versioned draft only — do NOT overwrite the submitted original.

---

## 1. Student identity / programme / course identifiers
- **Action:** RETAIN (unchanged).
- **Evidence:** none required.

## 2. Project title
- **Action:** RETAIN unless the student wants to narrow the scope wording.
- **Note:** current Wave-1 results suggest the title should NOT over-claim "LLM superiority". If the title mentions "LLM-enhanced forecasting", keep it but ensure the abstract qualifies the claim.
- **Evidence:** `MIFlu_Wave1_Final_Supervisor_Report_EN.md` §3.5, §3.8.

## 3. Problem statement
- **Action:** UPDATE.
- **Proposed wording:**
  "It is unclear whether integrating frozen large language models into time-series forecasters yields accuracy that is (a) superior to lightweight linear models and (b) attributable to the text/LLM mechanism rather than to the underlying seasonality of influenza-like-illness data."
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §2.

## 4. Research question / objectives
- **Action:** UPDATE.
- **Proposed wording:**
  - Research question: "Across four Non-LLM and four LLM-based forecasting architectures, which performs best under the frozen selection rule, and does the LLM family as a whole reliably outperform the Non-LLM family?"
  - Objectives: (1) pre-registered, seed-replicated benchmark of 8 architectures; (2) identify best Non-LLM, best LLM, and overall Wave-1 validation champion; (3) ablate the LLM mechanism to localize the text contribution; (4) preserve strict test/holdout isolation and a quota-safe compact-checkpoint pipeline.
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §3–§4.

## 5. Completed methodology
- **Action:** UPDATE.
- **Proposed wording:**
  "National ILI dataset (seven variables, z-space, train-only normalization); horizons L ∈ {24, 36, 48, 60}; 10 frozen seeds 42–51; early stopping (patience 7); frozen selection rule ranks by average_MSE_4L (mean of per-horizon mean MSE, lower better) with average_MAE_4L as key secondary; serial fail-stop execution, 580 rows accepted, 0 ledger FAIL events, test/holdout 0/0."
- **Evidence:** `frozen_analysis_protocol.json`; `Project_Summary_Update_Evidence_Pack.md` §5.

## 6. Models compared
- **Action:** UPDATE.
- **Proposed wording:**
  "Non-LLM: nlinear, dlinear, patchtst (PatchTST-inspired), itransformer. LLM-based: gpt2_miflu, qwen_time_llm, calf_llm, timecma_llm. Deterministic references: seasonal_naive, last_value_naive."
- **Evidence:** `frozen_analysis_protocol.json` (family_membership); `Project_Summary_Update_Evidence_Pack.md` §6.

## 7. Validated experimental scale
- **Action:** UPDATE.
- **Proposed wording:** "580 accepted rows = 320 primary + 8 baseline + 240 ablation + 12 negative control; 0 deleted / 0 duplicated."
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §7.

## 8. Current progress / best result
- **Action:** REPLACE (this is the section with the largest substantive change).
- **Proposed wording:**
  - Best Non-LLM: `nlinear` — average MSE 4L = 1.0698 (95% CI [1.0677, 1.0719]).
  - Best LLM: `gpt2_miflu` — average MSE 4L = 0.7709 (95% CI [0.7200, 0.8217]).
  - Overall Wave-1 validation champion: `gpt2_miflu`; runner-up `nlinear` (paired t = −13.33, p = 3.13×10⁻⁷).
  - Family finding: Non-LLM family (1.142) significantly better than LLM family (1.243), p = 1.44×10⁻⁶.
  - Caveat: zero-parameter `seasonal_naive` beats `gpt2_miflu` at L24/L36/L48.
- **Evidence:** `model_ranking.csv`, `selection_outcome.json`; `Project_Summary_Update_Evidence_Pack.md` §9–§10.

## 9. Contributions
- **Action:** REPLACE with three conservative, evidence-supported contributions.
- **Proposed wording (see evidence pack §17):**
  1. Empirical architecture comparison — pre-registered, seed-replicated, test-isolated benchmark of 8 Non-LLM/LLM architectures under a frozen selection rule.
  2. Mechanism / ablation evidence — the LLM text contribution localized to the dataset-information component; LoRA and multimodal fusion statistically inert.
  3. Reproducible quota-safe framework — fail-closed compact-checkpoint pipeline (580/580 accepted, 0 fail events, test/holdout 0/0).
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §17.

## 10. Ablation / control work
- **Action:** UPDATE.
- **Proposed wording:** "6 ablations: only `without_dataset_information` significant (+12.85%, p = 0.004); LoRA / multimodality / task-instruction not significant. 12 executed negative controls (exploratory): zero_text −0.063, shuffled_text +0.081."
- **Evidence:** `ablation_effects.csv`, `control_effects_summary.csv`; `Project_Summary_Update_Evidence_Pack.md` §11.

## 11. Remaining work
- **Action:** REPLACE.
- **Proposed wording:** "18 deferred negative controls pending Wave-2 (parent binding = gpt2_miflu); test/holdout sealed; final champion not frozen; final manuscript pending."
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §12–§13.

## 12. Timeline
- **Action:** REPLACE with revised timeline.
- **Proposed wording:** (1) Wave-2 deferred-control binding + execution; (2) freeze audit + final champion selection; (3) test/holdout evaluation only after freeze; (4) manuscript drafting/submission.
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §14.

## 13. Risks and mitigations
- **Action:** REPLACE with the risk table.
- **Proposed wording:** see `Project_Summary_Update_Evidence_Pack.md` §15 (5 risks: over-claim, seed instability, PTE/PIE (peak metrics), patchtst fidelity, LLM cost).
- **Evidence:** `Project_Summary_Update_Evidence_Pack.md` §15.

## 14. Status labels (must appear verbatim)
- **Action:** ADD to any progress/status field.
- **Proposed wording:** "Wave 1 complete; 18 deferred controls pending binding/execution; Test/holdout not accessed; final champion not frozen; final report/manuscript pending."
- **Evidence:** `frozen_analysis_protocol.json` (scope_restrictions).
