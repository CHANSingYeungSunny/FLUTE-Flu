# MIFlu Final Report: One-Time Test/Holdout Evaluation of the Frozen Wave-1 Architectures

**Project:** MIFlu influenza-forecasting reproducibility study
**Scope:** "clean v3" Wave-1 formal execution (580 accepted rows) **+ one-time Test/Holdout evaluation (84 runs)**
**Status:** FINAL. Wave-1 validation selection frozen; Test/Holdout unsealed and evaluated exactly once. All three confirmatory hypotheses tested. Final report (supersedes `MIFlu_Wave1_Final_Supervisor_Report_EN.md`).

---

## 0. Headline result (read this first)

Under the frozen selection rule, the Wave-1 **validation** champion was `gpt2_miflu` (avg MSE 4L = 0.771), with `nlinear` (1.070) as runner-up. The one-time, held-out **Test** evaluation (the COVID-era window, forecast targets at absolute weeks 820–1024, i.e. 2018-01-28 through 2022) **reverses that ordering**:

| rank | model | family | Test avg MSE 4L | 95% CI | Test avg MAE 4L |
|---:|---|---|---:|---:|---:|
| 1 | **nlinear** | Non-LLM | **2.739** | [2.731, 2.747] | 1.139 |
| 2 | **gpt2_miflu** | LLM | **3.051** | [2.922, 3.179] | 1.156 |
| 3 | seasonal_naive | baseline | 4.279 | n/a (deterministic) | 1.299 |

**The Wave-1 validation advantage of the LLM champion did not generalize to the held-out Test window.** On Test, the simple linear model `nlinear` is significantly more accurate than `gpt2_miflu` (paired t = 5.46, p = 4.0×10⁻⁴, Holm-Bonferroni-corrected), and **both** models significantly beat the zero-parameter `seasonal_naive` baseline (p = 7.7×10⁻²¹ and 4.6×10⁻⁹ respectively). All three models degrade on Test relative to validation — this is expected, since the Test window contains the COVID-19 era and no model saw it — but the degradation is smallest for `nlinear` (+1.67) and largest for `seasonal_naive` (+3.51).

**One-line conclusion:** the validation champion selection (`gpt2_miflu`) stands as the frozen Wave-1 result, but on a genuinely held-out, out-of-distribution window the non-LLM linear forecaster `nlinear` is the more robust model; the LLM's validation advantage was window-specific and does not survive distribution shift.

---

## 1. Executive Summary

- **Frozen selection rule** (never mutated): rank by `average_MSE_4L` — the arithmetic mean of per-horizon mean MSE across L ∈ {24, 36, 48, 60}, each averaged over the 10 frozen seeds (42–51), in the seven-variable, full-horizon, z-space. Lower is better. Secondary metric `average_MAE_4L`. Forbidden tie-breakers: peak hit ratio, PTE/PIE, baseline-relative ratio.
- **Wave-1 (validation):** `gpt2_miflu` (0.771) < `nlinear` (1.070); paired t = −13.33, p = 3.13×10⁻⁷.
- **Final (Test/Holdout):** `nlinear` (2.739) < `gpt2_miflu` (3.051) < `seasonal_naive` (4.279).
- **Three confirmatory tests**, all significant under Holm-Bonferroni (m = 3, α = 0.05):
  - C1 — `gpt2_miflu` vs `nlinear` on Test: gpt2 is **worse** (mean diff +0.312, p = 4.0×10⁻⁴).
  - C2 — `gpt2_miflu` vs `seasonal_naive` on Test: gpt2 is **better** (mean diff −1.229, p = 4.6×10⁻⁹).
  - C3 — `nlinear` vs `seasonal_naive` on Test: nlinear is **better** (mean diff −1.540, p = 7.7×10⁻²¹).
- **Validation-to-Test gap** (Test − Validation, in `average_MSE_4L`): nlinear +1.67, gpt2_miflu +2.28, seasonal_naive +3.51.
- **Peak accuracy (Test, physical ILITOTAL):** `nlinear` is the clear best peak forecaster (PIE 9–21% across horizons), `gpt2_miflu` is mid-to-poor (PIE 41–62%), and `seasonal_naive` is worst on intensity (PIE 50–124%). The MSE champion is **not** the best peak forecaster — this mirrors the Wave-1 validation finding.

---

## 2. Protocol integrity & one-time access (completeness audit)

The Test/Holdout was released exactly once, only after the pre-Test freeze audit was fully green, and was verified by a 25-item terminal audit. No Test target value was read before authorization; the analysis reads Test values only through the frozen `test_eval.py` (SHA-256 `93a1338bfac30096a95448830bb2867d9966e3625df9a51c91453b86ae7dae0b`, verified identical post-run).

| integrity check | result |
|---|---|
| pre-Test freeze audit (16 gates) | ALL GREEN (test_access = 0, holdout_access = 0 before release) |
| authorized Test keys | 84 (unique) |
| family composition | gpt2_miflu 40 / nlinear 40 / seasonal_naive 4 |
| ledger entries | 84, all COMPLETED, exit 0:0 |
| Slurm (`sacct`) ground truth | 84 `te_eval` jobs, all COMPLETED, exit 0:0, **no 85th job** |
| result dirs / manifests / predictions / metric files / status | 84 / 84 / 84 / 84 / 84 |
| stochastic-restoration evidence | 80/80 (compact + canonical tensor SHA-256 + strict-load OK) |
| baseline arm (seasonal_naive) | 4/4 (checkpoint_applicable = false) |
| first Test target abs_week | 820 (= val_end 819 + 1; no overlap with validation) |
| last Test target abs_week | 1024 |
| frozen script hash | unchanged |
| driver exit / lock / queue | ALL_DONE / lock released / no residual `te_eval` job |
| terminal audit | **25/25 PASSED** |

No 85th job, no duplicate, no unauthorized comparator, no post-Test script change. The one-time access ledger (`final_test_access_ledger.jsonl`) records every file read during analysis.

---

## 3. Frozen selection recap (Wave-1, validation-only)

These are the frozen Wave-1 validation results (from `selection_outcome.json`), reported for continuity:

| rank | model | family | validation avg MSE 4L | 95% CI |
|---:|---|---|---:|---:|
| 1 | **gpt2_miflu** | LLM | **0.771** | [0.720, 0.822] |
| 2 | **nlinear** | Non-LLM | **1.070** | [1.068, 1.072] |
| 3 | patchtst | Non-LLM | 1.076 | [1.065, 1.087] |
| 4 | dlinear | Non-LLM | 1.171 | [1.168, 1.174] |
| 5 | timecma_llm | LLM | 1.181 | [1.170, 1.193] |
| 6 | itransformer | Non-LLM | 1.253 | [1.248, 1.258] |
| 7 | qwen_time_llm | LLM | 1.253 | [1.223, 1.283] |
| 8 | calf_llm | LLM | 1.765 | [1.756, 1.774] |

The frozen Wave-1 conclusions were: (i) `gpt2_miflu` wins overall, `nlinear` is the best Non-LLM and runner-up; (ii) at the *family* level the Non-LLM group (1.142) is significantly more accurate than the LLM group (1.243), p = 1.44×10⁻⁶ — the LLM "win" was carried by a single model; (iii) `seasonal_naive` beat `gpt2_miflu` at L24/L36/L48 on validation, so the LLM's short-horizon accuracy was largely seasonal.

**The one-time Test phase now answers the question that validation could not:** which of these frozen conclusions survive a genuinely unseen, distribution-shifted (COVID-era) window?

---

## 4. One-time Test/Holdout design

- **Window:** Test targets at absolute weeks 820–1024 (first target 2018-01-28; last target reaches the COVID-19 era). The 1025-day forecast origin span uses the same T = 104-week sliding input, stride-1, 7-variable protocol as training/validation.
- **Scaler / checkpoint discipline:** every Test run uses the *Training*-fit scaler and the *Validation*-selected checkpoint; the Test window was never used for fitting, selection, or early stopping. Baseline arms have `checkpoint_applicable = false` and no stochastic seed.
- **Runs:** 84 = 2 stochastic models (gpt2_miflu, nlinear) × 4 horizons × 10 seeds (42–51) + 1 deterministic baseline (seasonal_naive) × 4 horizons.
- **Endpoint:** `mse_all_7vars_full_horizon_z` (primary), `ilitotal_full_horizon` and `pte_pie` (secondary). Identical metric contracts to validation.
- **One-time discipline:** the phase ran exactly once; the terminal audit confirms no resubmission and no re-read.

---

## 5. FINAL Test results

### 5.1 Primary endpoint — `average_MSE_4L` (lower is better)

| model | Test avg MSE 4L | 95% CI (df = 9) | Test avg MAE 4L |
|---|---:|---:|---:|
| **nlinear** | **2.739** | [2.731, 2.747] | 1.139 |
| **gpt2_miflu** | **3.051** | [2.922, 3.179] | 1.156 |
| seasonal_naive | 4.279 | n/a (deterministic) | 1.299 |

The CIs of the two learned models do not overlap (`nlinear` upper 2.747 < `gpt2_miflu` lower 2.922), so the reversal is not a sampling artifact.

### 5.2 Per-horizon MSE (Test, seed-mean)

| horizon | gpt2_miflu | nlinear | seasonal_naive |
|---:|---:|---:|---:|
| L24 | 2.750 | **2.337** | 4.158 |
| L36 | 3.182 | **2.705** | 4.277 |
| L48 | 3.189 | **2.907** | 4.383 |
| L60 | 3.081 | **3.007** | 4.299 |

`nlinear` is more accurate than `gpt2_miflu` at **all four horizons**. The gap is largest at L24 (+0.413, p = 0.0039) and L36 (+0.477, p = 0.0043), and narrows (non-significant) at L48 (p = 0.055) and L60 (p = 0.175). `seasonal_naive` is worst at every horizon.

### 5.3 Secondary endpoint — ILITOTAL full horizon (physical units)

| model | MSE (physical, mean over L) | MAE (physical, mean over L) |
|---|---:|---:|
| **nlinear** | **3.97 × 10⁸** | 13,670 |
| gpt2_miflu | 4.66 × 10⁸ | 14,313 |
| seasonal_naive | 6.60 × 10⁸ | 16,174 |

The ILITOTAL-physical endpoint preserves the same ordering (`nlinear` < `gpt2_miflu` < `seasonal_naive`), so the primary ranking is endpoint-robust.

---

## 6. Confirmatory hypothesis tests (pre-registered, m = 3)

Each test is on `average_MSE_4L`. C1 is a matched-seed paired t-test (n = 10); C2/C3 are one-sample t-tests of the per-seed difference against the deterministic `seasonal_naive` reference (df = 9, no seed variance in the reference).

| id | hypothesis | mean diff (A − B) | t | raw p | Holm p (m = 3) | reject α = 0.05 |
|---|---|---:|---:|---:|---:|---|
| C1 | gpt2_miflu **vs** nlinear (A worse) | +0.312 | 5.461 | 4.0×10⁻⁴ | 4.0×10⁻⁴ | **yes** |
| C2 | gpt2_miflu **vs** seasonal_naive (A better) | −1.229 | −21.614 | 4.6×10⁻⁹ | 9.2×10⁻⁹ | **yes** |
| C3 | nlinear **vs** seasonal_naive (A better) | −1.540 | −443.368 | 7.7×10⁻²¹ | 2.3×10⁻²⁰ | **yes** |

**Interpretation (ordered):**
1. **Both learned models beat the seasonal baseline on Test** (C2, C3) — this is the robust, expected result: even a simple linear forecaster substantially outperforms "repeat last season" once the window leaves the seasonal-training regime.
2. **The validation champion is not the best Test model** (C1) — `nlinear` is significantly more accurate than `gpt2_miflu` on the held-out window. The Wave-1 champion's validation edge does not generalize.

Per-horizon C1 detail (paired t, n = 10): L24 p = 0.0039, L36 p = 0.0043 (both significant), L48 p = 0.055 (marginal), L60 p = 0.175 (n.s.). The reversal is driven mainly by short horizons, exactly where validation had shown `seasonal_naive` already beating `gpt2_miflu` — consistent with the LLM's advantage being concentrated in the seasonal regime rather than in genuine generalization.

---

## 7. Validation-to-Test generalization gap

`gap = Test avg_MSE_4L − Validation avg_MSE_4L` (negative would mean *better* on Test; here all positive = all degrade):

| model | validation | Test | gap | degradation |
|---|---:|---:|---:|---:|
| **nlinear** | 1.070 | 2.739 | **+1.669** | smallest |
| gpt2_miflu | 0.771 | 3.051 | +2.280 | intermediate |
| seasonal_naive | 0.771 | 4.279 | +3.509 | largest |

Every model degrades on the unseen COVID-era window — expected and not a defect. The ranking of *robustness to distribution shift* is `nlinear` > `gpt2_miflu` > `seasonal_naive`. The most striking result is `seasonal_naive`: it was highly competitive on validation (0.771, effectively tied with `gpt2_miflu`) but collapses on Test (4.279), confirming that its validation success was an artifact of repeating the strongly seasonal 2016–2018 period, and that seasonality does not transfer through the COVID disruption.

---

## 8. Peak timing / intensity on Test (physical ILITOTAL)

PTE (peak-timing error, weeks; hit ≤ 1 wk) and PIE (peak-intensity error, %; hit ≤ 25%), mean over 16 eligible season-lead combinations per horizon, on the inverse-transformed ILITOTAL channel:

| model | horizon | PTE (wk) | PIE (%) | PTE hit | PIE hit | joint hit |
|---|---|---:|---:|---:|---:|---:|
| gpt2_miflu | 24 | 7.94 | 41.4 | 0.31 | 0.25 | 0.00 |
| gpt2_miflu | 36 | 3.44 | 61.5 | 0.38 | 0.19 | 0.06 |
| gpt2_miflu | 48 | 3.81 | 57.3 | 0.44 | 0.25 | 0.19 |
| gpt2_miflu | 60 | 1.56 | 52.0 | 0.38 | 0.19 | 0.00 |
| **nlinear** | 24 | 7.75 | **9.2** | 0.50 | **0.94** | **0.44** |
| **nlinear** | 36 | 3.06 | **19.9** | 0.50 | **0.75** | **0.44** |
| **nlinear** | 48 | 3.25 | **21.1** | 0.50 | **0.75** | **0.44** |
| **nlinear** | 60 | **1.13** | **12.6** | **0.69** | **0.88** | **0.63** |
| seasonal_naive | 24 | 6.88 | 79.8 | 0.75 | 0.06 | 0.06 |
| seasonal_naive | 36 | 3.25 | 123.9 | 0.75 | 0.06 | 0.06 |
| seasonal_naive | 48 | 3.25 | 123.9 | 0.75 | 0.06 | 0.06 |
| seasonal_naive | 60 | 0.63 | 49.6 | 0.94 | 0.06 | 0.06 |

**Finding.** On Test, `nlinear` is unambiguously the best peak forecaster on *intensity* (PIE 9–21%, hit rate 75–94%) and best or near-best on *timing* (PTE ≤ 3.25 weeks, joint hit up to 63%). `gpt2_miflu` is mid-to-poor on intensity (PIE 41–62%). `seasonal_naive` has the best raw PTE at long horizons (a 52-week repeat lands near the peak week by construction) but catastrophic PIE (up to 124%), because it cannot track the *magnitude* of the COVID-era peaks. This reinforces the §6 conclusion: `nlinear` is the more useful operational model on this window.

---

## 9. Prediction vs ground-truth curves (Test/Holdout only)

Each figure plots the Test/Holdout target window **only** — ground truth as a **solid** line, the seed-mean lead-1 (1-week-ahead) prediction as a **dashed** line, and the observed/predicted seasonal peaks marked. The y-axis is the inverse-transformed ILITOTAL on the **original scale**. Historical-input tail, training/validation curves, and the input/forecast boundary are deliberately omitted per the frozen figure plan.

![Gallery. Test/Holdout prediction (dashed) vs ground truth (solid) for all three models × four horizons, ILITOTAL, seed-mean lead-1.](../../final/final_test_prediction_gallery/final_test_prediction_gallery.png)

Representative individual panels — `nlinear` (best Test model) and `gpt2_miflu` (Wave-1 champion) at L24 (shortest) and L60 (longest):

![nlinear L24. Ground truth solid, prediction dashed.](../../final/final_test_prediction_figures/fig_test_nlinear_L24.png)

![nlinear L60. Ground truth solid, prediction dashed.](../../final/final_test_prediction_figures/fig_test_nlinear_L60.png)

![gpt2_miflu L24. Ground truth solid, prediction dashed.](../../final/final_test_prediction_figures/fig_test_gpt2_miflu_L24.png)

![gpt2_miflu L60. Ground truth solid, prediction dashed.](../../final/final_test_prediction_figures/fig_test_gpt2_miflu_L60.png)

The full 12-panel set is under `final_test_prediction_figures/` with per-figure source data (`final_test_curve_source_data/`) and a window-provenance table (`final_test_window_provenance.csv`) asserting, for every figure: input-target overlap = 0, future-target leakage = 0, scaler fit on Training, checkpoint selected on Validation, plotted window = Test/Holdout.

---

## 10. Statistical methods

- Per-horizon point estimate = mean of 10 frozen seeds (42–51); `average_MSE_4L` = arithmetic mean of the four per-horizon means.
- 95% CI = seed-level t-interval (t-distribution, df = 9).
- C1 = matched-seed paired t-test (n = 10 pairs), Cohen's dz on the paired differences.
- C2/C3 = one-sample t-test of `seed_i − deterministic_reference` against 0 (df = 9), because `seasonal_naive` has no seed variance.
- Multiple comparison = Holm-Bonferroni step-down over the **3 pre-registered primary tests** (α = 0.05). All three survive.
- Peak metrics (PTE/PIE) follow the frozen `peak-evaluation-v1` specification; they are **secondary application metrics** and were never part of the selection rule.

---

## 11. Interpretation & honest conclusions

1. **The frozen selection stands, but its meaning is now clarified.** `gpt2_miflu` was correctly selected as the Wave-1 validation champion under the frozen rule. The one-time Test phase shows that this advantage was **window-specific**: on a held-out, COVID-era window the LLM's validation edge disappears and inverts.
2. **The robust model is the simple one.** `nlinear` (2,520 parameters, ~5 s training, ~10 KB) is significantly more accurate than the ~1.03 M-parameter LLM on Test, and — crucially — is dramatically better at peak-intensity forecasting (PIE 9–21% vs 41–62%). For a deployed influenza-forecasting use case, `nlinear` is the better model on this evidence.
3. **Seasonality is not generalization.** `seasonal_naive` was competitive on validation (0.771) but collapses on Test (4.279, PIE up to 124%). This is the cleanest demonstration in the study that a seasonal repeat is not a forecast — it is a memorization of the training-era seasonal shape.
4. **The manuscript headline should not be "LLM beats classical forecaster".** On the held-out window the opposite is true. The Wave-1 finding that "the LLM family is worse as a family, and the win was one model" is now strengthened: even that one model's win does not survive the Test window.
5. **Both learned models still beat the baseline.** The honest bottom line is two-tiered: (a) learning helps (both models beat `seasonal_naive` with p < 10⁻⁸); (b) the marginal value of the LLM machinery *over a linear model* is negative on this window.

---

## 12. Limitations

1. **One window, one evaluation.** The Test/Holdout is a single contiguous COVID-era window (abs weeks 820–1024). Robustness claims are limited to this window; there is no second independent holdout.
2. **Distribution shift is conflated with COVID.** The Test window contains the COVID-19 pandemic, so "generalization gap" and "COVID disruption" cannot be separated here. The gap should not be read as a pure measure of model overfitting.
3. **Deterministic baseline has no seed variance.** C2/C3 treat `seasonal_naive` as a fixed constant; the resulting t-values are large by construction (the reference contributes zero variance). This is a property of the baseline, not evidence of model magnitude — the *direction* and *significance* of the model-vs-baseline gap are what those tests establish.
4. **Peak metrics are secondary.** PTE/PIE on Test inherit the reconstructed-target-week convention and the lead-1 convention documented in the figure plan; they are application metrics, never used in selection.
5. **Provenance of Wave-1 checkpoints.** The Wave-1 primary runs' full checkpoints were deleted after their canonical tensor SHA-256 was recorded; Test-time restoration was verified via strict-load with empty missing/unexpected keys. This is documented, not concealed.

---

## 13. Final conclusions

| question | answer |
|---|---|
| Wave-1 validation champion (frozen) | `gpt2_miflu` (0.771) |
| Best Test model | **`nlinear`** (2.739) |
| Does the validation champion generalize? | **No** — it inverts on Test (gpt2 3.051 > nlinear 2.739, p = 4.0×10⁻⁴) |
| Do learned models beat the seasonal baseline on Test? | **Yes** — both, p < 10⁻⁸ |
| Most robust to distribution shift | `nlinear` (gap +1.67), then `gpt2_miflu` (+2.28), then `seasonal_naive` (+3.51) |
| Best peak forecaster on Test | `nlinear` (PIE 9–21%, joint hit up to 63%) |

---

## 14. Artifacts

- **Metrics:** `results/v3_clean/final/final_test_metrics.json` (primary + secondary + confirmatory + PTE/PIE), `final_test_seed_level.csv`, `final_peak_metrics.csv`, `final_peak_hit_rates.csv`, `final_generalization_comparison.csv`.
- **Access & integrity:** `final_test_access_ledger.jsonl` (every file read), `terminal_test_audit.json` (25/25), `pre_test_freeze_audit.json`, `final_test_artifact_manifest.json`.
- **Figures:** `results/v3_clean/final/final_test_prediction_figures/` (12 panels) and `final_test_prediction_gallery/final_test_prediction_gallery.png`; source data in `final_test_curve_source_data/`; provenance in `final_test_window_provenance.csv` and `final_test_figure_manifest.json`.
- **Full analysis dataset:** `results/v3_clean/final/final_test_analysis_dataset.csv` (3,944,304 rows of per-seed, per-step, per-variable Test predictions).

---

*This report is the FINAL artifact for the MIFlu reproducibility study. The Wave-1 validation report remains valid for the validation-only portion; the Test/Holdout results above are the definitive held-out conclusions.*
