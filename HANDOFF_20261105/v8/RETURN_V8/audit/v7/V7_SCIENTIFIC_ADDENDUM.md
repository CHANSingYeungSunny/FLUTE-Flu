# V7 scientific addendum — new 1120-cell common panel (2026-11-06)

This addendum supersedes the *execution status* and the *peak* conclusions of revision 9.2.
It does **not** overwrite the frozen historical CSVs. Historical and new panels are separate.

## 1. What is complete

- National common panel: **1120 / 1120 cells** (28 models × 4 lengths × 10 seeds 2021–2030).
- MIFlu seven-channel recovery: **40 / 40** checkpoints exported; every target array equals the
  NLinear target array exactly (shape, values, `target_start_row`; max diff 0.0).
- fix40 (`ds_r1_distill_qwen1_5b`): **40 / 40 rc=0, validated=yes**.
- Core 160/160 (MIFlu/NLinear/PatchTST/DLinear) remains complete.

## 2. New harmonised MSE/MAE (seven-channel z-space)

Two panels with identical target populations:

- `all_valid`: 170/158/146/134 windows at L=24/36/48/60.
- `crop`: first `(W//16)*16` windows (160/144/144/128), the historical panel.

| Model | MSE all-valid | MSE crop | MAE all-valid |
|---|---:|---:|---:|
| MIFlu | **1.7944** | **1.4994** | 0.8529 |
| PatchTST | 1.9521 | 1.6352 | 0.9244 |
| NLinear | 2.0782 | 1.9027 | 0.9652 |
| DNN | 2.2802 | 2.1173 | 1.0401 |
| TimeCMA | 2.6255 | 2.5765 | 1.0879 |
| GradientBoosting | 3.6547 | 3.6645 | 1.2636 |
| KNN | 3.7791 | 3.7854 | 1.3369 |
| RandomForest | 3.8817 | 3.8888 | 1.2872 |
| iTransformer | 4.0631 | 4.0704 | 1.3681 |
| DecisionTree | 4.2905 | 4.2940 | 1.3842 |

**The leading order is the same on both panels: MIFlu < PatchTST < NLinear.** The crop panel
reproduces the historical MIFlu mean 1.4995 at 1.4994, which validates the recovery; the
all-valid panel raises all errors but does not reorder the leaders.

## 3. Peak skill — the historical conclusion changes

Step-level K&S detector: `find_peaks(prominence=0.15*range, distance=15)`, ±8-week matching,
ILITOTAL channel, 1,680 step rows per model (10 seeds × 168 leads).

| Model | mean PTE (wk) | mean PIE (%) | passes | pass rate |
|---|---:|---:|---:|---:|
| PatchTST | **0.707** | 34.410 | 215 | 12.8% |
| MIFlu | 0.964 | **30.090** | **252** | **15.0%** |
| NLinear | 2.013 | 42.350 | 57 | 3.4% |
| DNN | 1.690 | 51.536 | 0 | 0% |
| TimeCMA | 1.588 | 61.510 | 0 | 0% |

Event-level (181,868 events): iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8% detection
and PIE 30.4%; PatchTST 97.6% and PIE 34.6%; NLinear 92.6% and PIE 40.6%.

**Historical claim retired:** NLinear was the K&S champion in the old 16-unit snapshot. On the new
1120-cell panel, MIFlu and PatchTST have far more step-level passes. The old 16-unit table is a
different scoring population and must not be silently replaced.

## 4. Ablation ladder

| Variant | n | mean MSE |
|---|---:|---:|
| K4 | 12 | **1.4989** |
| K6 reference | 10 | 1.5457 |
| K2 | 12 | 1.5813 |
| K8 | 12 | 1.6124 |
| no_lora | 12 | 1.6330 |
| K12 | 12 | 1.7604 |

**No monotonic depth trend.** K4 is best, K12 worst; the K6 reference has 10/12 matched cells.

## 5. Table VI and walk-forward

- Regional: **53 / 53** valid `mse_z` rows after rerunning L13/s2030 and L15/s2026. These are
  10-variable regional aggregates, not comparable to the seven-channel national means.
- Walk-forward: **802 / 1,020** rows valid after direct seven-channel recomputation from raw NPZ;
  **218** have no NPZ. The stored metrics.csv had 329 non-finite values, but those are recovered
  from the predictions; 218 cells remain missing and walk-forward is still not complete.
- `final_llm_import` remains TODO and its lane returns `idle-no-work`.

## 6. Statistics

- Exploratory paired Wilcoxon on 28 models, 378 pairs, 40 `(L,seed)` cells, Holm:
  **349 / 378 rejections**, min adjusted p ≈ 6.9e-10.
- **Exploratory only**: cells share one national series and overlapping targets; a
  dependence-aware/blocked analysis is not done.

## 7. What the documents must say

1. Historical 28-arm/Holm/peak numbers remain the **old snapshot**.
2. New 1120 panel is a **separate panel**; report it as such.
3. Replace the old peak conclusion with the new step/event tables; explicitly state that the
   historical NLinear peak champion is not reproduced.
4. Do not claim an ablation depth trend.
5. Do not claim walk-forward is complete.
6. Keep the frozen CSVs and owner-edited PPTX byte-identical.

## 8. Files

- `final/CELL_METRICS.csv`, `MODEL_L_PANEL.csv`, `MODEL_MEANS_BY_PANEL.csv`
- `final/PEAK_BY_STEP.csv`, `PEAK_EVENTS.csv`, `PEAK_MODEL_SUMMARY.csv`, `PEAK_EVENT_SUMMARY.csv`
- `final/PAIRED_HOLM_NEW.csv`
- `final/ABLATION_CELLS.csv`, `ABLATION_MEANS.csv`
- `final/REGIONAL_CELLS.csv`, `REGIONAL_MEANS.csv`, `WF_CELLS.csv`, `WF_MEANS.csv`
- `final/SCIENTIFIC_AUDIT.md`, `final/FINAL_RESULTS.md`
