# Partial Track B results (pre-final, 2026-11-05 14:05 HKT)

**Status: PARTIAL — not a final result, not for a Table in the manuscript.**

## Coverage

- Cells with usable metrics: **610 / 1120**
- Models represented: **22 / 28**
- Model×L summary rows: **88 / 112**
- Fully complete (40/40): `miflu`, `calf_llm`, `cnn`, `dnn`, `ds_r1_distill_32b`, `ds_r1_distill_llama8b`
- Partial: `patchtst` 26, `nlinear` 27, `itransformer` 27, `rnn` 27, `gru` 26, `lstm` 26,
  `qwen_time_llm` 27, `timecma_llm` 13, `qwen25_1_5b` 27, `qwen7b` 27, `qwen14b` 39,
  `contextpilot_8b` 14, `contextpilot_14b` 24, `hunyuan_1.8b` 13, `hunyuan_4b` 13,
  `hunyuan_7b` 14, `gradient_boosting`/`knn`/`svr`/`random_forest` pending in this snapshot.

## Partial per-model means (7-variable z-space)

| Model | cells | MSE | MAE | MSE_ILI |
|---|---:|---:|---:|---:|
| miflu | 40 | **1.4994** | 0.8043 | 2.8137 |
| patchtst | 26 | 1.9551 | 0.9247 | 3.7421 |
| nlinear | 27 | 2.0767 | 0.9642 | 4.0869 |
| dnn | 40 | 2.2802 | 1.0401 | 4.4918 |
| timecma_llm | 13 | 2.6200 | 1.0862 | 5.9074 |
| itransformer | 27 | 4.0769 | 1.3709 | 8.1371 |
| hunyuan_7b | 14 | 4.7846 | 1.4801 | 9.4828 |
| hunyuan_1.8b | 13 | 4.7876 | 1.4903 | 9.1016 |
| gru | 26 | 4.8021 | 1.5063 | 9.4980 |
| llama8b | 40 | 4.8059 | 1.4842 | 9.4070 |
| qwen14b | 39 | 4.9068 | 1.4949 | 9.6838 |
| 32b | 40 | 5.0042 | 1.5120 | 9.8114 |
| lstm | 26 | 5.0095 | 1.5333 | 9.4987 |
| contextpilot_8b | 14 | 5.0312 | 1.5236 | 9.8945 |
| rnn | 27 | 5.0482 | 1.5690 | 9.5324 |
| qwen7b | 27 | 5.0658 | 1.5242 | 9.7414 |
| hunyuan_4b | 13 | 5.1004 | 1.5455 | 9.7696 |
| qwen25_1.5b | 27 | 5.1270 | 1.5662 | 9.8749 |
| contextpilot_14b | 24 | 5.2068 | 1.5486 | 10.3038 |
| qwen_time_llm | 27 | 5.2906 | 1.5961 | 9.9740 |
| calf_llm | 40 | 5.5228 | 1.6092 | 10.5837 |
| cnn | 40 | 5.9679 | 1.7178 | 11.3095 |

`miflu` mean 1.4994 is consistent with the reproduction mean 1.4995 — a useful cross-check, not a new claim.

## Peak metrics (MIFlu only, partial)

- `TRACKB_PEAK_PARTIAL.csv`: **40 MIFlu cells × 42 steps = 1680 step rows**.
- MIFlu L24 s2021 step 0: PTE 0.0, PIE 18.8, pass — consistent with the old snapshot.
- Other models are not in this peak table yet: their prediction artefacts are `.npz`, not the
  per-step CSV used by `aggregate_peak.py`. A separate npz loader is required for a full
  peak table.

## What this partial version may and may not support

May support:

- pipeline validation (metrics schema, aggregation, peak detector);
- a sanity check that MIFlu reproduces the old mean;
- early detection of broken models/rows.

May **not** support:

- any final ranking, because 18 models are partial and 510 cells are missing;
- Holm/paired statistics: the family is incomplete;
- a "28-model benchmark" claim;
- a Track B peak table beyond MIFlu.

## Reproduce

```bash
python /gpfs1/scratch/sychan552/trackB_20261104/all/aggregate_all.py
python /gpfs1/scratch/sychan552/trackB_20261104/all/aggregate_peak_all.py
```

Files in this folder:

- `TRACKB_PARTIAL.csv` — 610 cell rows
- `TRACKB_PARTIAL_SUMMARY.csv` — 88 model×L rows
- `TRACKB_PEAK_PARTIAL.csv` — 1680 MIFlu step rows
