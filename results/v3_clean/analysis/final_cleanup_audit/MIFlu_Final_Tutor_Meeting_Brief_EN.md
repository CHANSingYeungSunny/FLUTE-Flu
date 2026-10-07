# Tutor Meeting Brief (EN) — Final Test/Holdout Results

**One-line conclusion:** the Wave-1 validation champion `gpt2_miflu` (0.771) did **not** generalize to the held-out COVID-era Test window — there the simple linear model `nlinear` (2.739) significantly beats it (3.051, p = 4.0×10⁻⁴); both models still beat the zero-parameter `seasonal_naive` baseline (4.279), which collapses under distribution shift.

---

## Three facts the tutor must see

### Fact 1: the validation ranking reverses on Test

| model | validation avg MSE 4L | Test avg MSE 4L | 95% CI (Test) |
|---|---:|---:|---:|
| `nlinear` | 1.070 | **2.739** | [2.731, 2.747] |
| `gpt2_miflu` | **0.771** | 3.051 | [2.922, 3.179] |
| `seasonal_naive` | 0.771 | 4.279 | n/a |

The champion's validation advantage was window-specific. On Test, `nlinear` is better at **all four horizons** (L24 +0.413, p = 0.004; L36 +0.477, p = 0.004; L48 p = 0.055; L60 p = 0.175). Confirmatory test C1 (paired t = 5.46, p = 4.0×10⁻⁴, Holm-corrected) rejects the hypothesis that the two are equal.

### Fact 2: seasonality is not a forecast — the baseline collapses on Test

| | validation | Test | gap |
|---|---:|---:|---:|
| `seasonal_naive` | 0.771 | 4.279 | **+3.51** |

On validation, `seasonal_naive` was tied with `gpt2_miflu` — its success was memorizing the strongly seasonal 2016–2018 period. On the COVID-era Test window it is the worst model by a wide margin, and its peak-intensity error reaches 124%. This is the study's cleanest demonstration that "repeat last year" is not forecasting.

### Fact 3: `nlinear` is the best operational model on Test (and the simplest)

| | params | Test avg MSE 4L | Test PIE (peak intensity) |
|---|---:|---:|---:|
| `nlinear` | 2,520 | 2.739 | 9–21% (hit 75–94%) |
| `gpt2_miflu` | 1,030,056 | 3.051 | 41–62% |

For peak *intensity* forecasting — the metric that matters for outbreak detection — `nlinear` is dramatically better. Both learned models still beat the baseline (C2 p = 4.6×10⁻⁹, C3 p = 7.7×10⁻²¹).

---

## Questions to discuss / decide with the tutor

1. **Framing the final narrative:** should the paper's headline be "a simple linear forecaster outperforms an LLM on held-out data" rather than any LLM-superiority claim?
2. **Champion status:** the frozen Wave-1 selection stands as a *validation* result, but the Test winner is `nlinear`. How do we phrase "frozen selection" vs "final recommendation" so neither contradicts the other?
3. **`seasonal_naive` as a formal baseline:** its validation-vs-Test collapse is the most illustrative result — promote it to a main-table baseline?
4. **Cost argument:** `nlinear` is 409× fewer params and ~28× faster to train, and now *also* more accurate on Test. Does the LLM machinery retain any justification in the final paper?
5. **Limitations wording:** the Test window is a single contiguous COVID-era window — confirm we state "distribution shift conflated with COVID" explicitly rather than over-claiming robustness.

---

## Quick numbers (citable)

- Test primary: `nlinear` 2.739, `gpt2_miflu` 3.051, `seasonal_naive` 4.279.
- Confirmatory (all Holm-significant, m = 3): C1 gpt2 vs nlinear p = 4.0×10⁻⁴; C2 gpt2 vs seasonal p = 4.6×10⁻⁹; C3 nlinear vs seasonal p = 7.7×10⁻²¹.
- Validation-to-Test gap: nlinear +1.67, gpt2 +2.28, seasonal +3.51.
- Test peak intensity (PIE): nlinear 9–21%, gpt2 41–62%, seasonal 50–124%.
- Integrity: 84/84 runs, 25/25 terminal audit, no 85th job, frozen script hash unchanged.

**Artifact paths:** full reports `MIFlu_Final_Supervisor_Report_EN.md` / `_ZH.md` (+ .docx/.pdf); metrics and figures under `results/v3_clean/final/`.
