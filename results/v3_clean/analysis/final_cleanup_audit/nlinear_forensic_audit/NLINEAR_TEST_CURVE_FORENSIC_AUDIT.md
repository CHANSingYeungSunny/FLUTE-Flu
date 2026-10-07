# NLinear Data-Leakage and Prediction-Curve Forensic Audit — Final Report

Generated: 2026-09-21 · Mode: **read-only** (no figure/DOCX/PDF edits, no retrain, no rerun Test, no deletions)

## Verdict

```text
NLINEAR_TEST_CURVES_AND_SPLIT_VERIFIED
```

No data leakage, no target substitution, no split error, no scaler leakage, no
checkpoint leakage, and no unsupported metric claim were found. The NLinear Test
curve appears unusually close to Ground Truth for a fully-explained, legitimate
reason (below). One **wording-only** correction is recommended (the individual
NLinear panel captions should state "lead-1 (1-week-ahead) rolling seed-mean"),
prepared in `remediation_plan_if_needed.md` and **not** executed, per §15.

---

## 1. Why the NLinear curve looks so accurate

The displayed curve is **not** a single fixed-origin full L-week forecast. It is a
**rolling one-week-ahead (lead-1 / step-0) seed-mean** reconstruction:

1. **Rolling lead-1.** For each Test target week *t*, the prediction is the
   *first* forecast step (step 0, `lead_weeks == 1`) of the window whose origin is
   `t − 104`. Every target week has exactly **one** forecast origin; the only
   aggregation is across the 10 seeds (42–51). A 1-week-ahead forecast of a highly
   persistent series is inherently much easier than a 24/60-week-ahead forecast.

2. **High ILI autocorrelation.** `corr(truth_t, truth_{t−1}) = 0.971`. The
   series barely moves week-to-week, so any competent 1-week-ahead forecaster
   tracks it tightly.

3. **NLinear last-value anchoring.** NLinear computes
   `last = x[:,:,-1:] ; s = x − last ; y = Linear(T→L)(s) ; return y + last`
   (`scripts/innovation/backbones/dlinear.py:110-118`). Its prediction is anchored
   at the **last observed input value** (= last week's truth), then adds a linear
   correction. The forensic signature confirms this:

| Correlation | L24 lead-1 | L60 lead-1 |
|---|---|---|
| corr(pred, truth) | 0.9774 | 0.9798 |
| **corr(pred, truth[t−1])** (anchor) | **0.9937** | **0.9949** |
| corr(pred, truth[t+1]) | 0.9200 | 0.9239 |
| corr(pred, lag-52) | 0.4883 | 0.8207 |
| corr(truth, truth[t−1]) | 0.9713 | 0.9707 |

`corr(pred, truth[t−1]) > corr(pred, truth) > corr(pred, truth[t+1])` is the
**persistence/anchor** signature, not the copy signature (a copy would give
`corr = 1.0` and exact equality).

---

## 2. Rolling lead-1 vs fixed-origin full L

**Rolling lead-1.** Confirmed by byte-exact reconstruction: averaging the 10
frozen per-seed `test_predictions.csv` files (variable_index == 4) over
`(target_date, lead_weeks)` and taking `lead_weeks == 1` reproduces
`final_test_curve_source_data/fig_test_nlinear_L*.csv` with **max |diff| = 0.0**.

The curves cover long calendar spans (182 weeks for L24, 146 for L60) because
each week contributes its own 1-week-ahead point — not because a single origin
predicts the full horizon.

---

## 3. Split counts and the correct meaning of "1025"

| Split | Timestamps | abs_week | Dates |
|---|---|---|---|
| Train | **717** | 0–716 | 2001-12-30 → 2016-01-31 |
| Validation | **102** | 717–818 | 2016-02-07 → 2018-01-14 |
| Test | **206** | 819–1024 | 2018-01-21 → 2021-12-26 |
| **Total** | **1025** | 0–1024 | 2001-12-30 → 2021-12-26 |

- **1025 = the TOTAL number of weekly timestamps**, not the Test window count.
- Sliding windows (T = 104, stride 1, split by target-start week): **Train 613 /
  Validation 103 / Test (206 − L)** → 182 / 170 / 158 / 146 for L = 24/36/48/60.
- The earlier report wording "训练 717 / 验证 102 / 测试 1025 个窗口" was already
  corrected in the prior split audit to "1025 周时间点；训练 717 / 验证 102 / 测试 206
  时间点；窗口 613 / 103 / (206−L)". (Confirmed present in the DOCX/PDF.)

---

## 4. Data-leakage results

| Check | Result |
|---|---|
| input_target_overlap_count | **0** |
| future_target_leakage_count | **0** |
| scaler fit split | **Training only** (`data[:717]`) |
| checkpoint selection split | **Validation only** (`best_val_mse`) |
| plotted target split | **Test/Holdout** (820 … 1025−L) |
| labels concatenated into inputs | No |
| future covariates from target | No |
| rolling stats using future | No |
| backfill/interpolation from future | No |
| seasonal feature using future | No |

Tensor-slice examples (first/middle/last/peak origins) all satisfy
`input_last_index < target_first_index` (input ends one week before the target
begins). A Test target's input may legally include earlier Validation weeks and
Test timestamp 819 as **context** — this is historical context, not leakage.

---

## 5. Prediction-identity results

- **exact_equality_rate = 0.0** for both L24 and L60 (prediction never equals truth).
- near-equality (< 1 ILI unit) = 0.0; within 5% = 33.5% (L24) / 37.7% (L60).
- mean |pred − truth| ≈ 2,929 (L24) / 2,975 (L60) ILI visits (real error, not a copy).
- The corr signature (table above) shows anchoring to `truth[t−1]`, **not** copying
  truth, future truth, last-input-104-weeks-ago, or the seasonal lag.

---

## 6. Seed-mean smoothing results

| Horizon | seed-mean MSE | mean individual-seed MSE | improvement |
|---|---|---|---|
| L24 | 24,202,928 | 27,343,784 | **11.5%** |
| L36 | 24,070,444 | 28,070,431 | **14.2%** |
| L48 | 25,591,597 | 29,450,276 | **13.1%** |
| L60 | 26,133,564 | 30,281,097 | **13.7%** |

The seed-mean is a **fixed** average of seeds 42–51 (no seed selected by Test).
`MSE(mean prediction) < mean(individual MSEs)` follows from the bias–variance
decomposition: averaging cancels uncorrelated per-seed errors. This is a modest,
genuine smoothing effect, **not** an artificial boost.

---

## 7. Official metric vs displayed curve

| Horizon | official full-L ILITOTAL MSE (phys) | displayed lead-1 MSE (phys) | ratio |
|---|---|---|---|
| L24 | 336,730,127 | 24,202,928 | 13.9× |
| L36 | 388,370,878 | 24,070,444 | 16.1× |
| L48 | 423,713,897 | 25,591,597 | 16.6× |
| L60 | 438,721,623 | 26,133,564 | 16.8× |

The official primary metric (`average_MSE_4L`, 7-variable full-L z-space) is
**2.739** for NLinear (vs 3.051 GPT-2 MIFlu, 4.279 seasonal-naive). The displayed
lead-1 curve is **~14–17× easier** than the official full-L metric. The report
already frames the curves as **representative ("代表曲线")** in §5.4, so this is
disclosed — but the individual panel captions should say "lead-1" explicitly.

---

## 8. PTE / PIE interpretation

The figure annotations are **representative displayed-curve** (seed-mean lead-1)
values, **not** official season/event-level PTE/PIE:

| Horizon | PTE (weeks) | PIE (%) | true peak | pred peak |
|---|---|---|---|---|
| L24 | 1 | 0.17% | abs 925 | abs 926 |
| L60 | 1 | 0.97% | abs 925 | abs 926 |

Official season-level PTE/PIE and joint-hit rates live in
`final_peak_metrics.csv` / `final_peak_hit_rates.csv` (NLinear hits both 4/4
horizons; GPT-2 MIFlu 0/4; seasonal-naive PIE-only 0/4). No metric is fabricated;
the representative-vs-official distinction is already caveated in the report.

---

## 9. Comparison with the original `step0` reference

Verdict: **EQUIVALENT WITH DOCUMENTED DIFFERENCE** (full field table in
`reference_step0_vs_final_nlinear_semantics.json`). Essential semantics match:
`step 0 == lead-1`, rolling fixed-lead seed-mean, ILITOTAL physical, week-start
x-axis. Differences are the model (NLinear vs MIFlu GPT-2) and cosmetic style
(colors/peak markers).

---

## 10. Figure and source-data locations

- NLinear L24: `results/v3_clean/final/final_test_prediction_figures/fig_test_nlinear_L24.png` (SHA-256 `2c8450…`), embedded in the DOCX as `word/media/image8.png`.
- NLinear L60: `results/v3_clean/final/final_test_prediction_figures/fig_test_nlinear_L60.png` (SHA-256 `5d700c…`), embedded as `word/media/image9.png`.
- Gallery (3-model × 4-horizon): `results/v3_clean/final/final_test_prediction_gallery/final_test_prediction_gallery.png` (SHA-256 `197089…`), embedded as `word/media/image7.png`.
- Source CSVs: `results/v3_clean/final/final_test_curve_source_data/fig_test_nlinear_L{24,60}.csv`.
- Per-seed predictions: `results/v3_clean/test_eval/results/primary__nlinear__L{L}__seed{s}__w1/predictions/test_predictions.csv`.
- Generator: `scripts/v3_clean/final_test_figures.py`.

The NLinear PNGs inside the DOCX are **byte-identical** (SHA-256) to the final
Test figures. Full map in `nlinear_figure_location_manifest.json`.

---

## 11. May the current reports be used?

**Yes**, for the figures. No leakage or substitution exists. The only residual
issue is **wording**: the individual NLinear L24/L60 captions ("solid = ground
truth, dashed = prediction") should state the curve is a **lead-1 (1-week-ahead)
rolling seed-mean** so it cannot be misread as the full-horizon forecast. This is
a caption clarification, not a figure error; the report's §5.4 already carries the
"代表曲线" caveat.

---

## 12. Required remediation (prepared, not executed)

See `remediation_plan_if_needed.md`. Summary: (a) caption wording for NLinear (and,
for consistency, GPT-2) L24/L60 panels; (b) optional caption note on the gallery
panel; (c) re-QA after any caption change. No figure regeneration and no metric
change are required.

---

## 13. Audit-output paths and SHA-256

See `nlinear_forensic_artifact_manifest.json` for the authoritative list with
per-file SHA-256.

## Final token

```text
NLINEAR_TEST_CURVES_AND_SPLIT_VERIFIED
```
