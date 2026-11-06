# Final Track B results — 2026-11-06 (harmonised seven-channel scoring)

Status: **1120/1120 cells complete**; **40/40 MIFlu seven-channel NPZ recovered from checkpoints**;
all 1120 cells scored on two identical-population panels.

## Panels

- `all_valid`: every valid test window (170/158/146/134 at L=24/36/48/60).
- `crop`: historical crop, first `(W//16)*16` windows (160/144/144/128).
- MSE/MAE are seven-channel z-space means over cells, then over seeds.

## Model means (all 28 arms)

| Model | MSE all-valid | MSE crop | MAE all-valid | MAE crop |
|---|---:|---:|---:|---:|
| miflu | **1.7944** | **1.4994** | 0.8529 | 0.8043 |
| patchtst | 1.9521 | 1.6352 | 0.9244 | 0.8743 |
| nlinear | 2.0782 | 1.9027 | 0.9652 | 0.9267 |
| dnn | 2.2802 | 2.1173 | 1.0401 | 0.9998 |
| timecma_llm | 2.6255 | 2.5765 | 1.0879 | 1.0662 |
| gradient_boosting | 3.6547 | 3.6645 | 1.2636 | 1.2521 |
| knn | 3.7791 | 3.7854 | 1.3369 | 1.3293 |
| random_forest | 3.8817 | 3.8888 | 1.2872 | 1.2768 |
| itransformer | 4.0631 | 4.0704 | 1.3681 | 1.3618 |
| decision_tree | 4.2905 | 4.2940 | 1.3842 | 1.3759 |
| hunyuan_1.8b | 4.7364 | 4.7393 | 1.4840 | 1.4753 |
| gru | 4.7954 | 4.8240 | 1.5052 | 1.5070 |
| hunyuan_7b | 4.7991 | 4.8217 | 1.4815 | 1.4772 |
| llama8b | 4.8059 | 4.8245 | 1.4842 | 1.4784 |
| qwen1.5b | 4.8467 | 4.8712 | 1.5123 | 1.5095 |
| qwen14b | 4.9171 | 4.9374 | 1.4966 | 1.4918 |
| contextpilot_8b | 5.0024 | 5.0441 | 1.5193 | 1.5196 |
| 32b | 5.0042 | 5.0402 | 1.5120 | 1.5109 |
| qwen7b | 5.0468 | 5.0713 | 1.5230 | 1.5206 |
| lstm | 5.0575 | 5.0609 | 1.5415 | 1.5405 |
| rnn | 5.0645 | 5.0930 | 1.5691 | 1.5719 |
| hunyuan_4b | 5.1203 | 5.1442 | 1.5477 | 1.5453 |
| qwen25_1.5b | 5.1386 | 5.1807 | 1.5679 | 1.5679 |
| contextpilot_14b | 5.1885 | 5.2223 | 1.5460 | 1.5451 |
| qwen_time_llm | 5.2829 | 5.3182 | 1.5955 | 1.5960 |
| svr | 5.3439 | 5.3388 | 1.5040 | 1.4986 |
| calf_llm | 5.5228 | 5.5853 | 1.6092 | 1.6203 |
| cnn | 5.9679 | 5.9990 | 1.7178 | 1.7212 |

**The all-valid and crop panels give the same leading order: MIFlu < PatchTST < NLinear.**
The crop panel reproduces the old means almost exactly (MIFlu 1.4994 vs 1.4995), which validates
the recovery; the all-valid panel raises every model but preserves the leading order.

## ILITOTAL peak metrics (K&S detector)

Detector: `find_peaks(prominence=0.15*range, distance=15)`, ±8-week matching, per lead, on the
common author_966 scaler channel 4. Each model has 1680 step rows (10 seeds × 168 leads).

| Model | mean PTE (wk) | mean PIE (%) | passes | pass rate |
|---|---:|---:|---:|---:|
| patchtst | **0.707** | **34.410** | 215 | 12.8% |
| miflu | 0.964 | 30.090 | **252** | **15.0%** |
| qwen_time_llm | 4.632 | 67.467 | 1 | 0.1% |
| nlinear | 2.013 | 42.350 | 57 | 3.4% |
| dnn | 1.690 | 51.536 | 0 | 0% |
| timecma_llm | 1.588 | 61.510 | 0 | 0% |
| decision_tree | 5.032 | 62.585 | 0 | 0% |
| gradient_boosting | 5.033 | 66.696 | 0 | 0% |

**This changes the historical peak conclusion.** The old snapshot had NLinear as the K&S
champion (4/16) and MIFlu/PatchTST at 4/16/0/16. On the new harmonised 1120-cell panel,
MIFlu and PatchTST have the most step-level passes; NLinear is far behind. The historical
16-unit table is not numerically comparable to 1680 step rows, so the old table must not be
replaced silently — it is a different scoring population.

## Event-level peak outcomes (181,868 events)

One-to-one nearest matching, ±8 weeks; `event_success = matched/(matched+missed)`,
`false_alarm_rate = false_alarm/(matched+false_alarm)`.

| Model | matched | missed | false alarm | event success | false-alarm rate | PTE (matched) | PIE (matched) |
|---|---:|---:|---:|---:|---:|---:|---:|
| itransformer | 4331 | 39 | 223 | **99.1%** | 4.9% | 1.483 | 71.2% |
| miflu | 4318 | 52 | 949 | 98.8% | 18.0% | 0.978 | **30.4%** |
| knn | 4310 | 60 | 390 | 98.6% | 8.3% | 2.636 | 68.5% |
| patchtst | 4264 | 106 | 690 | 97.6% | 13.9% | **0.733** | 34.6% |
| calf_llm | 4250 | 120 | 160 | 97.3% | 3.6% | 2.555 | 81.1% |
| dnn | 4172 | 198 | 151 | 95.5% | 3.5% | 1.706 | 51.1% |
| timecma_llm | 4166 | 204 | 122 | 95.3% | 2.8% | 1.647 | 61.3% |
| nlinear | 4048 | 322 | 341 | 92.6% | 7.8% | 1.980 | 40.6% |
| llama8b | 3627 | 743 | 1881 | 83.0% | 34.2% | 4.968 | 76.7% |
| lstm | 3624 | 746 | 891 | 82.9% | 19.7% | 3.733 | 71.8% |

This separates **detection** from **timing/height**: iTransformer/KNN detect most events but have
large height errors; MIFlu/PatchTST combine high detection with much lower PIE.

## New paired statistics (exploratory)

- 28 models, **378 pairs**, Wilcoxon signed-rank on 40 `(L, seed)` cells, Holm forward cumulative.
- **349 / 378 rejections**, min adjusted p ≈ 6.9e-10.
- Cells share the same national series and overlapping targets, so this is **exploratory**, not
  independent-sample confirmation. A dependence-aware/blocked analysis is still pending.

## Ablation ladder (60 cells + matched K=6 reference)

Mean seven-channel MSE by depth variant (3 seeds × 4 lengths unless noted):

| Variant | n cells | mean MSE |
|---|---:|---:|
| K4 | 12 | **1.4989** |
| K6 reference | 10 | 1.5457 |
| K2 | 12 | 1.5813 |
| K8 | 12 | 1.6124 |
| no_lora | 12 | 1.6330 |
| K12 | 12 | 1.7604 |

**No monotonic depth trend.** K4 is the best mean; K12 is the worst; `no_lora` is worse than
K4/K6. The K6 reference has 10/12 matched cells (two seed logs missing), so the K6 mean is
partial and must not be treated as a complete 3-seed reference.

## Legacy regional (Table VI) and walk-forward validation

**Regional**: 53 output directories, **53 / 53 valid `mse_z` aggregate rows**, no missing cells
after the two reruns (L13/s2030, L15/s2026). These are 10-variable regional aggregates, not the
7-channel national metric; do not mix them.

| Lead L | n | mean mse_z |
|---:|---:|---:|
| 2 | 7 | 0.8341 |
| 3 | 7 | 1.3096 |
| 5 | 6 | 1.4156 |
| 10 | 10 | 2.7941 |
| 13 | 10 | 3.4128 |
| 15 | 7 | 3.7559 |
| 20 | 6 | 2.8858 |

**Walk-forward**: 1,020 cell directories, **802 valid MSE rows recomputed from raw NPZ**, **218 with no NPZ**.
The stored `metrics.csv` alone was misleading: 329 rows were non-finite there, but direct seven-channel
recomputation from the raw predictions recovered the legacy DONE set. This does **not** create new
cells; it validates the 802 that exist.

Valid WF means: MIFlu 2.215, PatchTST 3.827, NLinear 3.834, GradientBoosting 3.915, KNN 3.967,
DNN 4.310, DecisionTree 4.515, CNN 4.792, CALF 5.350, iTransformer 5.814, RNN 5.646, GRU 6.684,
LSTM 6.753, TimeCMA 4.565, Qwen-Time 6.315 (n varies; MIFlu 51).

## Files

- `CELL_METRICS.csv` — 2240 rows (1120 cells × 2 panels)
- `MODEL_L_PANEL.csv` — 224 rows (model × L × panel)
- `MODEL_MEANS_BY_PANEL.csv` — 28 model means
- `PEAK_BY_STEP.csv` — 47,040 step rows
- `PEAK_MODEL_SUMMARY.csv` — model peak summary

## Not done

- Paired significance / proper Holm for the new 1120 family: **NOT COMPUTED**.
- Table VI / walk-forward aggregation from legacy: **NOT VALIDATED**; the legacy queue still has
  one `final_llm_import` TODO and many historical `rc=3` attempts.
- Manuscript v7 / Q&A companion / return ZIP: **NOT UPDATED**.

Do not call this a submission-ready manuscript result; it is the new scored panel.
