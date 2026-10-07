# MIFlu Wave-1 Final Experimental Results: Non-LLM versus LLM Architecture Comparison

**Project:** MIFlu influenza-forecasting reproducibility study
**Scope:** "clean v3" Wave-1 formal execution (580 accepted rows)
**Status:** Wave-1 primary architecture comparison complete. Deferred controls (18) pending Wave-2. Test/holdout sealed (access = 0/0). Champion NOT frozen for publication. **Validation-only result.**

---

## 1. Executive Summary

**Primary ranking metric** (frozen selection rule): `average_MSE_4L` — the arithmetic mean of per-horizon mean MSE across four horizons L ∈ {24, 36, 48, 60}, each averaged over the 10 frozen seeds (42–51), in the seven-variable, full-horizon, z-space. Lower is better. The key secondary metric is `average_MAE_4L`.

| rank | model | family | avg MSE 4L | 95% CI | avg MAE 4L |
|---:|---|---|---:|---:|---:|
| 1 | **gpt2_miflu** | LLM | **0.771** | [0.720, 0.822] | 0.487 |
| 2 | **nlinear** | Non-LLM | **1.070** | [1.068, 1.072] | 0.564 |
| 3 | patchtst | Non-LLM | 1.076 | [1.065, 1.087] | 0.556 |
| 4 | dlinear | Non-LLM | 1.171 | [1.168, 1.174] | 0.603 |
| 5 | timecma_llm | LLM | 1.181 | [1.170, 1.193] | 0.614 |
| 6 | itransformer | Non-LLM | 1.253 | [1.248, 1.258] | 0.598 |
| 7 | qwen_time_llm | LLM | 1.253 | [1.223, 1.283] | 0.649 |
| 8 | calf_llm | LLM | 1.765 | [1.756, 1.774] | 0.773 |

**Answers to the ten questions:**

1. **Best Non-LLM:** `nlinear` (1.070).
2. **Best LLM:** `gpt2_miflu` (0.771).
3. **Best overall:** `gpt2_miflu`; runner-up `nlinear`. The gap is large and significant (paired t = −13.33, p = 3.13×10⁻⁷, Cohen's d = −5.94).
4. **LLM vs Non-LLM at the family level:** the Non-LLM group (1.142) is **significantly better** than the LLM group (1.243) — paired t = −11.15, p = 1.44×10⁻⁶. The LLM "win" is driven entirely by a single model, `gpt2_miflu`; the other three LLMs (timecma_llm, qwen_time_llm, calf_llm) are all worse than the best Non-LLM.
5. **Horizon/endpoint stability:** `gpt2_miflu` is the best model at **all four horizons** and remains best under the ILITOTAL full-horizon endpoint (1.608). `nlinear` remains the best Non-LLM under both endpoints. Winner conclusions are stable.
6. **Seed stability:** Non-LLM models are extremely seed-stable (nlinear SD = 0.0029). `gpt2_miflu` has the largest SD (0.0711, ≈9.2% of its mean), so its advantage depends partly on favourable seeds — but its mean is still decisively below nlinear.
7. **Practical significance (vs. a deterministic seasonal baseline):** the zero-parameter `seasonal_naive` baseline achieves 0.719/0.732/0.746/0.885 at L24/36/48/60 — **beating `gpt2_miflu` at L24, L36, and L48**. The LLM's absolute accuracy advantage is therefore concentrated at the longest horizon (L60) and is not obviously incremental over a simple 52-week seasonal repeat for short horizons.
8. **Runtime/storage trade-off:** `nlinear` costs 2,520 params / 5.3 s / 10 KB; `gpt2_miflu` costs 1,030,056 params / 147 s / 4.1 MB (≈409× the parameters, ≈28× the training time). `seasonal_naive` costs zero parameters, zero training, zero storage.
9. **Baseline competitiveness:** `last_value_naive` is far worse (2.82–3.42). `seasonal_naive` is highly competitive and must be reported as a strong reference point.
10. **Mechanism:** the only significant ablation is `without_dataset_information` (+12.8%, p = 0.004); removing LoRA, multimodality, or the task instruction has no significant effect (all p > 0.4). Negative controls are exploratory (6 cells): `zero_text` −0.063 (slightly better than parent), `shuffled_text` +0.081 (worse). The text contribution appears concentrated in the dataset-description component.

---

## 1.1 How model performance is evaluated (zero-background primer)

**MSE is not an accuracy percentage.** Throughout this report, "MSE" (mean squared
error) is a *cost* in the model's standardized (z-space) units — the average squared
difference between predicted and observed values, aggregated over the 7 variables, the
full forecast horizon, and the 10 frozen seeds. It has **no "% correct" meaning**:
smaller is better, and two values can only be compared relative to one another (e.g.
the winner's 0.771 vs the runner-up's 1.070). `MAE` (mean absolute error) is the same
idea without the squaring, and is reported as the secondary metric.

The evaluation is a strict **Input → Process → Output** (IPO) flow:

1. **Input** — a sliding 104-week window of 7 ILI variables (e.g. % weighted ILI,
   ILITOTAL, age-group counts, provider counts; exact list in the protocol snapshot).
2. **Process** — standardize with a *train-only* scaler → the model predicts in
   z-space → the prediction is inverse-transformed back to physical units.
3. **Output** — a future horizon of L ∈ {24, 36, 48, 60} weeks × 7 variables.

The output is compared against the observed (never-seen) values for the same weeks to
produce per-prediction errors, then the aggregate MSE/MAE. The primary ranking metric
`average_MSE_4L` is the mean of the four per-horizon MSEs.

![Figure 13. How model performance is evaluated (Input → Process → Output).](../figures/fig13_evaluation_workflow.png)

---

## 2. Frozen Protocol & Completeness Audit

- **Source of the rules:** `results/v3_clean/preregistration/paper_aligned_selection_rule.json`, `endpoint_hierarchy.json`, `execution_wave_manifest.json`, `deferred_parent_binding_rule.json`. The frozen protocol snapshot is recorded in `results/v3_clean/analysis/frozen_analysis_protocol.json`.
- **HPC_GUIDE.md integrity:** SHA-256 `1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167`, verified via `Get-FileHash` before analysis.
- **Completeness:** 580/580 accepted rows, 0 deleted, 0 duplicated, 0 fail events in the ledger, controller exited normally (not fail-stop).
  - 320 primary (8 models × 4 horizons × 10 seeds)
  - 8 baselines (2 models × 4 horizons)
  - 240 ablations (6 × 4 × 10)
  - 12 negative controls (zero_text, shuffled_text over L24/L60 × seeds 42–44)
- **Scope held:** Test/holdout access = 0/0. Selection rule was never mutated. Baselines/ablations/controls were never included in the primary ranking.

---

## 3. Primary Architecture Comparison

### 3.1 Ranking (seed-level, n = 10 per model)

See the table in §1. The 95% CI is the seed-level t-interval around `average_MSE_4L`. The ranking is unambiguous at the top: `gpt2_miflu` (0.771) < `nlinear` (1.070) < `patchtst` (1.076), with non-overlapping CIs between the top two.

![Figure 1. Primary architecture ranking by average_MSE_4L with 95% CI over the 10 frozen seeds (42–51). Lower MSE is better. Validation-only (test/holdout sealed).](../figures/fig1_model_ranking_ci.png)

### 3.2 Q1 — Best Non-LLM

`nlinear` at `average_MSE_4L = 1.0698` (95% CI [1.0677, 1.0719], SD 0.0029). It beats `patchtst` (1.0760) and `dlinear` (1.1709) with non-overlapping CIs, so the Non-LLM winner is unambiguous.

### 3.3 Q2 — Best LLM

`gpt2_miflu` at `average_MSE_4L = 0.7709` (95% CI [0.7200, 0.8217], SD 0.0711). It decisively beats `timecma_llm` (1.1814), `qwen_time_llm` (1.2531), and `calf_llm` (1.7649).

### 3.4 Q3 — Best overall

`gpt2_miflu` is the overall winner. The winner-vs-runner-up comparison (matched-seed paired t on `average_MSE_4L`, 10 pairs):

- winner mean 0.7709 vs runner-up 1.0698 → mean difference −0.299
- paired t = −13.33, **p = 3.13×10⁻⁷**, Cohen's d = −5.94

The equivalence-set rule (report a set rather than a unique champion when statistically/practically indistinguishable) does not trigger — the top two are clearly separated, so a unique winner is justified.

### 3.5 Q4 — LLM vs Non-LLM at the family level

A matched-seed paired t-test on the per-seed mean of the four models' `average_MSE_4L` in each family (10 seeds):

- Non-LLM group mean 1.1424 vs LLM group mean 1.2426 → difference −0.100
- paired t = −11.15, **p = 1.44×10⁻⁶**, Cohen's d = −5.33

**Interpretation:** as a *family*, Non-LLM models are significantly more accurate than LLM-based models. The apparent LLM advantage at the top is entirely attributable to `gpt2_miflu`; the other three LLMs all underperform every Non-LLM except the worst. This is the single most important structural finding for the manuscript narrative: the result is not "LLMs beat classical forecasters" but "one particular LLM-adapter (`gpt2_miflu`) beats everything, while LLM integration in general does not reliably help."

![Figure 3. Non-LLM vs LLM family comparison (matched-seed, per horizon) with per-horizon p-values; overall p = 1.44×10⁻⁶. Lower MSE is better. Validation-only.](../figures/fig3_family_comparison.png)

### 3.6 Q5 — Horizon and endpoint stability

Per-horizon best model is `gpt2_miflu` at every horizon:

| horizon | best model | best MSE | best Non-LLM |
|---:|---|---:|---|
| 24 | gpt2_miflu | 0.7324 | nlinear (0.9791) |
| 36 | gpt2_miflu | 0.7782 | nlinear (1.0490) |
| 48 | gpt2_miflu | 0.7598 | patchtst (1.0768) |
| 60 | gpt2_miflu | 0.8131 | nlinear (1.1501) |

Per-horizon family comparison (Non-LLM vs LLM, all four horizons) is also significant and in the same direction (all p ≤ 0.0016; see `selection_outcome.json`).

![Figure 2. Per-horizon MSE for all 8 architectures at L24/L36/L48/L60. Markers = mean over 10 seeds; error bars = 95% CI. Lower MSE is better. Validation-only.](../figures/fig2_per_horizon.png)

**Endpoint check (ILITOTAL full horizon, lower better):**

| rank | model | ILITOTAL 4L mean |
|---:|---|---:|
| 1 | gpt2_miflu | 1.608 |
| 2 | nlinear | 2.333 |
| 3 | dlinear | 2.526 |
| 4 | patchtst | 2.544 |
| 5 | timecma_llm | 2.635 |
| 6 | qwen_time_llm | 2.658 |
| 7 | itransformer | 2.877 |
| 8 | calf_llm | 3.677 |

The winner and best-Non-LLM conclusions are unchanged. The only endpoint-sensitive detail is an internal swap between `dlinear` and `patchtst` (positions 3/4). Reported; not a ranking concern.

### 3.7 Q6 — Seed stability

- Non-LLM models are remarkably seed-stable: `nlinear` SD = 0.0029 (0.27% of mean), `dlinear` SD = 0.0037.
- `gpt2_miflu` is the **least** seed-stable model: SD = 0.0711 (≈9.2% of its mean), with per-horizon SDs of 0.135 (L24), 0.144 (L36), 0.186 (L48), 0.111 (L60). Its best-case seeds (e.g. L36 seed 42 = 0.477) are far better than its worst (L48 seed 47 = 1.117).
- `qwen_time_llm` is also unstable (SD 0.0416); the other models are intermediate.

Consequence: `gpt2_miflu`'s lead is real but partly seed-dependent. A cautious manuscript should (a) report the seed SD, and (b) note that the top ranking would hold even at the 95% CI upper bound of `gpt2_miflu` (0.822) versus the lower bound of `nlinear` (1.068) — the CIs do not overlap, so the ordering is robust despite the variance.

### 3.8 Q7 — Practical significance vs. a deterministic seasonal baseline

| horizon | seasonal_naive MSE | gpt2_miflu MSE | seasonal − gpt2 |
|---:|---:|---:|---:|
| 24 | 0.7193 | 0.7324 | **−0.0131** |
| 36 | 0.7324 | 0.7782 | **−0.0458** |
| 48 | 0.7460 | 0.7598 | **−0.0138** |
| 60 | 0.8849 | 0.8131 | +0.0719 |

A zero-parameter, zero-training, zero-storage `seasonal_naive` (repeat last season's value) is **more accurate than the overall LLM winner at L24, L36, and L48**. Only at L60 does `gpt2_miflu` pull ahead. This is a critical honesty point: much of `gpt2_miflu`'s absolute accuracy at short horizons is explained by seasonality, not by the text/LLM machinery. The manuscript must compare against `seasonal_naive` explicitly and not over-claim "LLM superiority" at short horizons.

![Figure 4. Deterministic seasonal_naive baseline vs gpt2_miflu (LLM winner) and nlinear (Non-LLM winner) across horizons. Lower MSE is better. Validation-only.](../figures/fig4_seasonal_vs_top.png)

### 3.9 Q8 — Runtime / storage trade-off

| model | family | trainable params | train time (s) | compact storage |
|---|---|---|---:|---:|---:|
| nlinear | Non-LLM | 2,520 | 5.3 | 10 KB |
| dlinear | Non-LLM | 5,040 | 5.7 | 20 KB |
| itransformer | Non-LLM | 75,672 | 8.5 | 305 KB |
| patchtst | Non-LLM | 87,256 | 8.4 | 351 KB |
| qwen_time_llm | LLM | 370,376 | 338.7 | 1.48 MB |
| gpt2_miflu | LLM | 1,030,056 | 147.3 | 4.14 MB |
| timecma_llm | LLM | 1,391,016 | 15.2 | 5.56 MB |
| calf_llm | LLM | 1,981,608 | 20.2 | 7.93 MB |
| seasonal_naive | baseline | 0 | 0 | 0 |

`gpt2_miflu` uses ~409× the parameters and ~28× the training time of `nlinear` to gain 0.299 in MSE (0.771 vs 1.070). The trade-off is substantial; the manuscript should present it transparently rather than claiming LLMs are "efficient".

### 3.10 Q9 — Baseline competitiveness

- `last_value_naive`: MSE 2.821 (L24), 3.422 (L36), 3.168 (L48), 2.825 (L60) — far worse than every model.
- `seasonal_naive`: 0.719 / 0.732 / 0.746 / 0.885 — a strong competitor (see §3.8).

### 3.11 Q10 — Mechanism (ablations + negative controls)

Ablations relative to parent `gpt2_miflu` (0.7709), sorted by effect size:

| ablation | avg MSE 4L | Δ vs parent | rel. Δ | p-value |
|---|---:|---:|---:|---:|
| without_lora | 0.7729 | +0.0020 | +0.26% | 0.947 |
| without_lora_and_multimodality | 0.7778 | +0.0070 | +0.90% | 0.766 |
| without_multimodality | 0.7859 | +0.0150 | +1.95% | 0.474 |
| without_task_instruction | 0.7926 | +0.0217 | +2.82% | 0.395 |
| without_input_variable_description | 0.8156 | +0.0447 | +5.80% | 0.079 |
| **without_dataset_information** | **0.8699** | **+0.0990** | **+12.85%** | **0.004** |

**Finding:** the only statistically significant prompt component is the **dataset information** (the textual description of the ILI dataset/context). Removing it degrades performance by 12.85% (p = 0.0036). Removing **LoRA** (p = 0.95), the **multimodality fusion** (p = 0.47), or the **task instruction** (p = 0.40) has no significant effect — the adaptive/alignment machinery contributes almost nothing to accuracy in this setting.

![Figure 5. Ablation paired effect vs parent gpt2_miflu (10 matched seeds); bars = Δ average_MSE_4L, annotated with p-value and relative change. Positive = worse. Validation-only.](../figures/fig5_ablation_paired.png)

Negative controls (6 cells each; L24/L60 × seeds 42–44; exploratory, small n):

| control | mean Δ vs parent | direction |
|---|---:|---|
| zero_text | −0.063 | slightly *better* than parent |
| shuffled_text | +0.081 | worse than parent |

- `shuffled_text` degrading performance (+0.081) suggests the text *content/order* carries information (not pure noise).
- `zero_text` being slightly better (−0.063) is counter-intuitive and suggests the prompt may act partly as noise in some cells; with n = 6 this is exploratory and must not be over-interpreted.

### 3.12 Q10.5 — Peak timing / intensity (secondary application metric)

Because ILI is used for outbreak detection, we additionally report peak-accuracy
metrics in the style of Kramer & Shaman (2019), computed on the inverse-transformed
ILITOTAL channel over two complete validation influenza seasons (2016-2017 and
2017-2018; observed peaks at abs weeks 769 and 821). These are **secondary application
metrics** and were **never** used in the frozen selection rule (PTE/PIE are explicitly
listed as forbidden tie-breakers). Since the durable `validation_predictions.csv`
stores `target_date = None`, the target week was *reconstructed* as
`forecast_origin + 104 + step` (verified against raw ILITOTAL, inverse-transform `|diff| < 1e-3`).

- **PTE** (peak timing error) = |predicted peak week − observed peak week|, in weeks (lower better; a "hit" is ≤ 1 week).
- **PIE** (peak intensity error) = |predicted − observed peak intensity| / observed × 100, in % (lower better; a "hit" is ≤ 25%).

Model means over the 4 leads and 2 seasons (lower is better for PTE/PIE):

| model | PTE (weeks) | PIE (%) | PTE hit rate | joint hit rate |
|---|---:|---:|---:|---:|
| patchtst | 1.609 | 49.7 | 0.497 | 0.025 |
| nlinear | 1.750 | 17.7 | 0.500 | 0.141 |
| itransformer | 1.753 | 53.2 | 0.444 | 0.000 |
| dlinear | 1.966 | 26.8 | 0.406 | 0.031 |
| calf_llm | 1.931 | 70.6 | 0.338 | 0.000 |
| gpt2_miflu | 2.122 | 41.5 | 0.484 | 0.097 |
| timecma_llm | 2.284 | 45.6 | 0.381 | 0.000 |
| qwen_time_llm | 2.688 | 35.4 | 0.297 | 0.122 |

Reference baseline `seasonal_naive`: PTE = 2.375 weeks, PIE = 42.6%. (`last_value_naive`
is a flat constant predictor with no peak structure, so its PTE/PIE are not meaningful
and are omitted.)

**Interpretation.** The MSE champion `gpt2_miflu` is **not** the best peak forecaster:
it sits mid-table on PTE (2.12 weeks) and PIE (41.5%). `nlinear` is best on peak
intensity (PIE 17.7%) and `patchtst` best on peak timing (PTE 1.61 weeks) — both
Non-LLM. `seasonal_naive`, despite its low MSE, has the weakest peak timing among the
deterministic references (2.38 weeks), consistent with the fact that a 52-week repeat
cannot track the year-to-year drift of the influenza peak. This reinforces the §3.8
caveat: low MSE in the "flat-season" weeks does not imply accurate peak detection.

![Figure 12. Peak timing / intensity across all 580 runs × 4 leads × 2 seasons (physical ILITOTAL).](../figures/fig12_peak_timing_intensity.png)

### 3.13 Representative prediction curves (physical ILITOTAL)

Figures 9-10 plot the inverse-transformed ILITOTAL over the forecast window only,
for a representative validation forecast (origin at abs week 715 = 2016-01-24,
forecast window starting 2018-01-21) at L24 and L60, for the
LLM winner (`gpt2_miflu`), the Non-LLM winner (`nlinear`), the deterministic
`seasonal_naive` reference, and one additional LLM (`calf_llm`), each at its median
seed. The dashed line is the prediction, the solid line the observed ILITOTAL, and the
star / triangle mark the observed / predicted seasonal peaks. Figure 11 shows the
best / median / worst-seed spread for `gpt2_miflu` at L24.

A complete gallery of all 580 accepted runs (one panel per run, same layout) is under
`../figures/gallery/` with an `index.csv` and `manifest.json`.

![Figure 9. Prediction curves at L24 (median seed).](../figures/fig9_prediction_curves_L24.png)

![Figure 10. Prediction curves at L60 (median seed).](../figures/fig10_prediction_curves_L60.png)

![Figure 11. Seed sensitivity of gpt2_miflu L24 (best/median/worst seed).](../figures/fig11_seed_sensitivity.png)

---

## 4. Statistical Methods

- Per-horizon point estimate = mean of 10 frozen seeds (42–51).
- `average_MSE_4L` = arithmetic mean of the four per-horizon means.
- 95% CI = seed-level t-interval (t-distribution, df = 9).
- Winner-vs-runner-up and family comparisons = matched-seed **paired t-tests** (n = 10 pairs) with Cohen's d (pooled SD).
- Ablations = matched-seed paired t vs parent; controls = matched (L, seed) comparison.
- No multiple-comparison correction was applied to the exploratory ablation/control set; the single significant ablation survives Bonferroni at α = 0.05/6 = 0.0083.

---

## 5. Limitations & Pending Work

1. **PTE/PIE reconstructed from durable evidence.** The durable `validation_predictions.csv` stores `target_date = None`, so peak metrics were not directly aggregatable. The target week was therefore reconstructed as `forecast_origin + 104 + step` (verified against raw ILITOTAL, inverse-transform |diff| < 1e-3) and PTE/PIE were computed on the inverse-transformed ILITOTAL channel over two complete validation seasons (2016-2017, 2017-2018). Reported as secondary application metrics only; never used in selection.
2. **18 deferred negative controls** are pending Wave-2 (parent binding = BEST_VALIDATION_LLM_AFTER_SCREENING, which is `gpt2_miflu`). They are not run here.
3. **Test/holdout are sealed** (access 0/0). No final publication champion is frozen; the Wave-1 winner is an interim screening result only.
4. Negative controls are **exploratory** (n = 6 cells, only L24/L60 × seeds 42–44); their conclusions are directional, not confirmatory.
5. `patchtst` is a "PatchTST-inspired" reimplementation (no self-supervised pretraining, no RevIN, reduced capacity) — the fidelity caveat must travel with any PatchTST claim.

---

## 6. Conclusions

1. Under the frozen selection rule, the Wave-1 winner is **`gpt2_miflu`** (avg MSE 4L = 0.771), with **`nlinear`** as the best Non-LLM (1.070) and overall runner-up. The gap is large and highly significant (p = 3.13×10⁻⁷).
2. The headline should **not** be "LLMs beat classical forecasters": the Non-LLM *family* is significantly more accurate than the LLM family (p = 1.44×10⁻⁶); the win is one model, not the paradigm.
3. The `gpt2_miflu` advantage over a zero-parameter `seasonal_naive` baseline is **negative at L24/L36/L48** and positive only at L60 — seasonality explains much of the short-horizon accuracy.
4. The only text component that matters is the **dataset information** (+12.85%, p = 0.004); LoRA and multimodal fusion are statistically inert here.
5. The manuscript must report the runtime/storage trade-off (gpt2_miflu ≈ 409× nlinear parameters, 28× training time) and the seed instability of the LLM winner (SD 0.071) honestly.
6. On the secondary peak metrics, the MSE champion is not the best peak forecaster: `nlinear` leads on peak intensity (PIE 17.7%) and `patchtst` on peak timing (PTE 1.61 weeks); `gpt2_miflu` is mid-table (PTE 2.12 weeks, PIE 41.5%). `seasonal_naive`'s low MSE does not transfer to peak timing (PTE 2.38 weeks).

**Artifacts:** ranking/summary tables and figures are under `results/v3_clean/analysis/` (`model_ranking.csv`, `primary_summary_statistics.csv`, `ilitotal_ranking.csv`, `selection_outcome.json`, `ablation_effects.csv`, `baseline_comparison.csv`, `resource_storage.csv`, `pte_pie_long.csv`, `pte_pie_aggregate.csv`, `pte_pie_audit.json`, `figures/`, and the full 580-panel gallery under `figures/gallery/`). The machine-readable protocol snapshot is `frozen_analysis_protocol.json`.

---

## 7. Recommended Next Steps

1. **Tutor sign-off on narrative framing** — confirm the paper claims "`gpt2_miflu` (a specific LLM adapter) beats baselines" rather than "LLM methods beat classical methods"; decide whether `seasonal_naive` becomes a formal main-table baseline.
2. **Wave-2 deferred controls** — bind the deferred parent (BEST_VALIDATION_LLM_AFTER_SCREENING = `gpt2_miflu`) and run the 18 deferred negative controls; do not finalize mechanism conclusions before they complete.
3. **Manuscript drafting** — draft the results section against the tables/figures here, carrying the seed-SD, seasonal-baseline, and cost-trade-off caveats verbatim.
4. **Test/holdout remains sealed** — only after the deferred controls are reconciled and the freeze audit passes should a final publication champion be considered. Do not call the Wave-1 champion the final champion.

---

## Appendix A — Seed-level stability

![Figure 6. Seed-level stability of average_MSE_4L (box = 10 frozen seeds, dots = individual seeds). Lower MSE is better. Validation-only.](../figures/fig6_seed_stability.png)

---

## Appendix B — Accuracy vs runtime / storage

![Figure 7. Accuracy vs runtime (a) and compact storage (b) for the 8 architectures. Lower MSE is better. Validation-only.](../figures/fig7_accuracy_vs_resource.png)

---

## Appendix C — Wave-1 workflow and evidence-integrity

![Figure 8. Wave-1 workflow and evidence-integrity. Validation-only.](../figures/fig8_workflow_evidence.png)
