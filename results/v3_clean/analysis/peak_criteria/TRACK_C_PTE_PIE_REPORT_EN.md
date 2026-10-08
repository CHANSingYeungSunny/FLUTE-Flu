# Track C PTE / PIE Peak Evaluation Report (English)

*Supplementary indicator; does not affect the Test-MSE championship. Values from
frozen Test predictions; no retraining. Contract: `TRACK_C_PEAK_CONTRACT.md`;
per-event: `TRACK_C_PTE_PIE_PER_EVENT.csv`; per-model: `TRACK_C_PTE_PIE_PER_MODEL.csv`;
pass matrix: `TRACK_C_PTE_PIE_PASS_MATRIX.csv`.*

## 1. Definitions

- **PTE (Peak Timing Error)** = |predicted peak week − true peak week|, in weeks.
- **PIE (Peak Intensity Error)** = |predicted peak intensity − true peak intensity| / true peak intensity, in %.
- Primary peak target = **ILITOTAL** (influenza activity, patient counts); physical inverse uses the Train-only scaler.

## 2. Acceptance criteria (literature)

| Criterion | PTE | PIE | Source |
|---|---|---|---|
| **Literature** | ≤ 1 week | ≤ 25 % | Kramer & Shaman 2019, PLOS Comput Biol (DOI 10.1371/journal.pcbi.1006742); same convention as CDC "Predict the Influenza Season Challenge" |

> A peak is a HIT only when BOTH conditions hold (judged per peak, not on a mean).
> "Peak Hit Rate ≥ 0.75" is NOT a MIFlu-paper threshold; it was removed in the historical report's correction.

## 3. Eight-model results (3 seeds × 4 horizons; 36 true peaks per model)

| Model | True peaks | Lit hits (PTE≤1 & PIE≤25) | Lit rate | Mean PTE (wk) | Mean PIE (%) |
|---|---:|---:|---:|---:|---:|
| **miflu (MSE champ)** | 36 | 15 | 41.7 % | 0.29 | 25.0 |
| **nlinear** | 36 | 36 | **100.0 %** | 0.28 | 3.14 |
| **dlinear** | 36 | 31 | 86.1 % | 0.92 | 17.72 |
| timecma_llm | 36 | 0 | 0.0 % | 1.38 | 50.44 |
| patchtst | 36 | 0 | 0.0 % | 0.67 | 66.61 |
| itransformer | 36 | 0 | 0.0 % | 0.72 | 66.16 |
| qwen_time_llm | 36 | 1 | 2.8 % | 0.96 | 36.33 |
| calf_llm | 36 | 0 | 0.0 % | 0.93 | 81.25 |

## 4. Key findings

1. **MSE champion ≠ peak-accuracy champion.** MIFlu ranks first on Test MSE but hits only
   **41.7 %** of peaks (mainly because a few peaks exceed the 25 % PIE bound).
2. **NLinear satisfies both literature criteria on 36/36 peaks (100 %)** — the best peak model;
   DLinear is second (86.1 %).
3. **All four LLM-side models (timecma / patchtst / itransformer / calf) hit 0 %** of peaks;
   qwen_time_llm hits 2.8 % — LLM-side models systematically over-estimate peak intensity
   (mean PIE 50–81 %).
4. **MSE ranking and peak ranking differ but do not conflict**: PTE/PIE are seasonal/clinical
   supplements; the Track C champion remains MIFlu by one-time Test MSE.

## 5. Relation to the final report

- PTE/PIE are SUPPLEMENTARY to the MSE championship; they answer "can the model capture the flu
  peak", and do not change the Test ranking.
- This evaluation uses the literature criteria only; no project-custom thresholds are introduced.
- The Track C Test window (2016-2020) does not contain the 2021 high-ILI anomaly, so peak
  evaluation excludes the 2021 hallucination peak (see `TRACK_C_COVID_PERIOD_ANALYSIS.md`).
