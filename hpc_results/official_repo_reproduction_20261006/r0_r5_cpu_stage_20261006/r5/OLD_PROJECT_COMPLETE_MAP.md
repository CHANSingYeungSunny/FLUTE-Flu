# OLD PROJECT — Complete Map (historical 4-LLM vs 4-non-LLM influenza comparison)

Read-only reconstruction, `C:\Users\Asus\Desktop\FYP code\MLFlu`. No file was modified, moved, renamed or deleted; this document and its siblings are the only new files created.

Scope: the comparison that was run BEFORE the author's official repository was cloned (clone = **2026-09-24 09:54:29 +0800**, `recovery/author_repo/.git/logs/HEAD`). Everything here is "Historical Track B" (project's own code).

---

## Q1 — Exact model set (4 LLM + 4 non-LLM)

Frozen in `results/v3_clean/analysis/frozen_analysis_protocol.json` →

```json
"family_membership": {
  "non_llm": ["nlinear", "dlinear", "patchtst", "itransformer"],
  "llm":     ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
}
```

and identically in `results/v3_clean/analysis/selection_outcome.json` and `results/v3_clean/runs/complete_specs_598.csv`. The expectation in the brief is **CONFIRMED** (no substitutions).

| Side | Exact `model` string | Implementation | Class |
|---|---|---|---|
| non-LLM | `nlinear` | `scripts/innovation/backbones/dlinear.py` | `NLinear` |
| non-LLM | `dlinear` | `scripts/innovation/backbones/dlinear.py` | `DLinear` |
| non-LLM | `patchtst` | `scripts/innovation/backbones/patchtst.py` | `PatchTST` |
| non-LLM | `itransformer` | `scripts/innovation/backbones/itransformer.py` | `ITransformer` |
| LLM | `gpt2_miflu` | `scripts/miflu_model.py` via `scripts/innovation/backbones/gpt2_miflu_adapter.py` | `MIFlu` / `GPT2MifluAdapter` |
| LLM | `qwen_time_llm` | `scripts/innovation/backbones/llm_inspired.py` | `QwenTimeLLM` |
| LLM | `calf_llm` | `scripts/innovation/backbones/llm_inspired.py` | `CALFInspired` |
| LLM | `timecma_llm` | `scripts/innovation/backbones/llm_inspired.py` | `TimeCMAInspired` |

Two deterministic baselines accompany the field: `last_value_naive`, `seasonal_naive`. Six ablations of `gpt2_miflu` and 12 negative controls were also run. See `OLD_4V4_EXACT_MODEL_IDENTITIES.csv` for identity status, architecture, backbone, text usage and parameter counts.

---

## Q2 — Distinct stages (NOT merged)

Five historical stages were identified. They use different datasets, splits and code paths and must not be combined.

### Stage A — `early_ili_july2026` : own-MIFlu paper-protocol track (2026-08-05 … 2026-09-07)
- Paths: `results/ili/`, `hpc_results/data/`, `hpc_results/paper_exact/`, `hpc_results/control966/`, `hpc_results/journal_evidence/`
- Contents: the project's own `scripts/miflu_model.py` run under the MIFlu paper protocol on 1025-row (`hpc_results/data`, `src_logs_0817`) and 966-row (`paper_exact`, `control966`) data; variant sweeps `full / gated_inject / no_lora_multi / no_multi / full__adamw_cosine / full__earlystop / full__huber_clip` (`results/ili/journal_evidence/`).
- Not a 4-vs-4 comparison; single-model (MIFlu) evidence + 5-advisor-question audits.
- Result header: `results/ili/National_Table_V_summary.md` (MSE_ILI 5.0559 / 6.8340 / 6.4049 / 7.0704 for L24/36/48/60).

### Stage B — `innovation_v2_screening` : v2 screening (2026-09-14 … 2026-09-16)
- Path: `results/innovation/`
- A pre-4-vs-4 screening of DLinear/NLinear/PatchTST/iTransformer/fusion-forecaster/gpt2_miflu (`registry.csv`), validation-only selection, champion frozen = **`nlinear`** (`frozen_winners.json`, `frozen_utc 2026-09-15T14:47:32Z`), one-time Test on the nlinear cohort (52 cells, `final_nlinear_20260915T145710Z`).
- z-space results: `results/innovation/final_audit/primary_zspace_summary.csv` (nlinear 4.2966…5.6085; gpt2_miflu 5.6766…6.6225).
- **Superseded** by Stage C (`v3_superseded_archive/`, `amended_registry_audit.json`). Retained as history.

### Stage C — `wave1_validation_v3clean` : the headline 4-vs-4 validation ranking (2026-09-17 … 2026-09-21)
- Path: `results/v3_clean/`
- 8 architectures × 4 horizons × 10 seeds = **320 primary rows**; plus 240 ablation rows, 8 baseline rows, 12 negative-control rows → **580 accepted rows** (`analysis_dataset.csv`, `wave1_analysis_dataset.jsonl`).
- Ranking metric `average_MSE_4L`; winner `gpt2_miflu` **0.7708721562796242**; best non-LLM / runner-up `nlinear` **1.0697672040053035** (`model_ranking.csv`, `selection_outcome.json`).
- Frozen candidates: `final_candidate_freeze.json` → `gpt2_miflu`, plus mandatory comparators `nlinear`, `seasonal_naive`.

### Stage D — `final_test_holdout_v3clean` : one-time Test/Holdout + deferred controls (2026-09-21)
- Paths: `results/v3_clean/final/`, `results/v3_clean/test_eval/`
- Exactly 3 frozen models, **84 runs** (gpt2_miflu 40 / nlinear 40 / seasonal_naive 4), released once, 25/25 terminal audit, no 85th job.
- Result: **`nlinear` 2.7389 < `gpt2_miflu` 3.0505 < `seasonal_naive` 4.2792** — the documented generalization reversal.
- Deferred controls: Family A (`zero_text`/`shuffled_text`, parent `gpt2_miflu`, descriptive) and Family B (`llm_removed_or_alignment_only`, parent re-bound to `timecma_llm`, confirmatory, 6 new jobs). `preregistration/DEFERRED_CONTROLS_*`, `final/deferred_controls_statistical_interpretation.{json,md}`.

### Stage E — `a2_author966_stage5` / `stage6_author966_8model` : author-966 track (POST-clone, 2026-09-25/26)
- Paths: `recovery/stage5/`, `recovery/stage6/`, `hpc_results/stage5_a2/`, `hpc_results/stage6/`
- A2 = 3 learned models (`miflu`, `notext`, `nlinear`) + 8 baselines on the author 966-row data with `--containment strict`; Stage 6 = the eight-model field + `notext` control, 96 new fits + 24 reused, 116 Test artefacts.
- Results: `miflu` **2.041519** ≈ `nlinear` **2.049550** (paired t −0.11), `notext` **1.922158** best; the three pure-LLM backbones (`timecma` 2.670, `qwen` 5.220, `calf` 5.515) all worse than nlinear.
- **Post-clone** and using different data/splits — never mixed with Stages A–D.

### (Post-project) Stage F — official-repository lineage (2026-09-26 … 2026-10-06)
`hpc_results/official_repo_reproduction_20261006/` (A0-R released-code replay, A1-P, F1). Out of scope for the historical comparison; listed only so the boundary is explicit.

**How the stages differ:** dataset vintage (1025-row July snapshot for A–D except A's `paper_exact`/`control966` 966-row sub-arm vs 966-row author vintage for E); window rule (legacy target-start for A–D vs `containment strict` for E); seed count (10 for C/D, 3 for E); model set (1 in A, 6 in B, 8 in C/D, 8+notext in E); selection (validation-only in all; one-time Test in B/C-E).

---

## Q3 — Data contract per stage

Single source: `scripts/configs.py:90-112` (`DATA_PROFILES`). Details in `OLD_4V4_DATA_AND_EVALUATION_CONTRACT.md`. Summary:

| Stage | Dataset (sha256) | Rows | Split (train/val/test) | Date range / test targets | Scaler | Horizons | Seeds |
|---|---|---|---|---|---|---|---|
| A `early_ili` | `national_illness_raw.csv` (`c2b983af…`) + `national_illness_raw_paper_exact.csv` (`31ffc169…`) | 1025 / 966 | 717/102/206 and 676/96/194 | 2002–2021 / 2002–2020 | train-only StandardScaler | 24,36,48,60 | reps 1–10 |
| B `innovation_v2` | `national_illness_raw.csv` (`c2b983af…`) | 1025 | legacy target-start | 2002–2021 | train-only | 24,36,48,60 | 42–51 (nlinear), 42–44 (gpt2_miflu) |
| C+D `v3_clean` | `national_illness_raw.csv` (`c2b983af…`) | 1025 | **717/102/206**; test target weeks 820–1024 | 2002-01 … 2021-12 | train-only, `data[:717]`, ddof=0 +1e-8 | 24,36,48,60 | **42–51 (10)** |
| E `author_966` | `national_illness_raw_paper_exact.csv` (`31ffc169…`) | 966 | **676/97/193**; `containment strict` | 2002–2020 | train-only, `[0,676)` | 24,36,48,60 | **42–44 (3)** |

Variable order (all stages): `% WEIGHTED ILI, % UNWEIGHTED ILI, AGE 0-4, AGE 5-24, ILITOTAL, NUM. OF PROVIDERS, OT`; ILITOTAL index 4; T=104. Window counts for the strict rule (E): L24 549/74/170, L36 537/62/158, L48 525/50/146, L60 513/38/134.

---

## Q4 — Evaluation contract

- **Metric:** `mse_all_7vars_full_horizon_z` = MSE over all elements of the complete 7-variable, full-horizon output in train-fitted StandardScaler z-space. (Loss and metric live in the same z-space; the MIFlu model itself returns `yh_rev` in that space.)
- **Aggregation:** `average_MSE_4L` = arithmetic mean of the four per-L seed-mean MSEs. `average_MAE_4L` is the key secondary. Tie-break order `avg_MSE_4L → avg_MAE_4L → resource cost`.
- **Forbidden:** peak-hit-ratio / PTE-PIE tie-breakers, baseline-relative ratios, `(r24+r60)/2`.
- **Forecast keys:** long schema `model_key, horizon, seed_or_rep, split, forecast_origin, target_date, step, lead_weeks, variable, variable_index, y_true_z, y_pred_z, y_true_physical, y_pred_physical`.
- **Checkpoint rule:** lowest **validation** `mse_all` per (model, horizon, seed) inside a fixed 20-epoch Adam fit (lr 5e-4, batch 16). Ordinary validation loss, never peak-aware.
- **Test during selection? NO.** `frozen_analysis_protocol.json`: `"test_holdout_never_accessed": true`, `"test_access": 0, "holdout_access": 0`; A2/Stage-6 used `DEFER_TEST=1` so Test is scored only in a separate locked pass.
- **PTE/PIE:** secondary application metrics only (thresholds ≤1 week, ≤25%), never used in selection.

---

## Q5 — The historical MIFlu

See `OLD_MIFLU_IMPLEMENTATION_IDENTITY.md`. In brief: **`scripts/miflu_model.py`, class `MIFlu`** (sub-modules `TimeSeriesEmbedder` / `ModalityAligner` / `ForecastingLLM` / `LoRALinear`), wrapped by `scripts/innovation/backbones/gpt2_miflu_adapter.py::GPT2MifluAdapter` (registered name `gpt2_miflu`). It is the **project's own from-scratch re-implementation** of the MIFlu paper (IEEE JBHI 2025) — **not** the author's released `models/GPT4TS_lora.py`. Trainable params **1,030,056 (L24) … 1,223,844 (L60)**; LoRA contributes 73,728; total params **UNRECOVERED** (not recorded). Role: the LLM-side flagship that won Wave-1 validation (0.771) and lost the final Test (3.0505 vs nlinear 2.7389).

---

## Q6 — Old results (values quoted from the CSVs)

### Stage C — Wave-1 validation, `average_MSE_4L` (`results/v3_clean/analysis/model_ranking.csv`)
| rank | model | family | average_MSE_4L |
|---:|---|---|---:|
| 1 | gpt2_miflu | llm | 0.7708721562796242 |
| 2 | nlinear | non_llm | 1.0697672040053035 |
| 3 | patchtst | non_llm | 1.0759512350833647 |
| 4 | dlinear | non_llm | 1.1709330614104076 |
| 5 | timecma_llm | llm | 1.1814489108230537 |
| 6 | itransformer | non_llm | 1.2529821517131419 |
| 7 | qwen_time_llm | llm | 1.2530956837735059 |
| 8 | calf_llm | llm | 1.7648712774010924 |

Per-horizon means: `results/v3_clean/analysis/primary_summary_statistics.csv` (also in `OLD_4V4_RESULT_TABLE.csv`). e.g. gpt2_miflu 0.73244 / 0.77817 / 0.75982 / 0.81306; nlinear 0.97912 / 1.04904 / 1.10076 / 1.15014.

### Stage D — Final Test/Holdout (`results/v3_clean/final/final_test_metrics.json`)
| model | L24 | L36 | L48 | L60 | average_MSE_4L |
|---|---:|---:|---:|---:|---:|
| nlinear | 2.3367132666 | 2.7053989638 | 2.9067831522 | 3.0068188756 | **2.7389285646** |
| gpt2_miflu | 2.7501684778 | 3.1819887122 | 3.1893589477 | 3.0806078495 | **3.0505309968** |
| seasonal_naive | 4.1579892701 | 4.2769005266 | 4.3827147911 | 4.2991626233 | **4.2791918028** |

### Stage C baselines (validation, z-space)
| model | L24 | L36 | L48 | L60 |
|---|---:|---:|---:|---:|
| last_value_naive | 2.821200197815767 | 3.422431571802754 | 3.167843944134935 | 2.8250886828401813 |
| seasonal_naive | 0.7193443203456401 | 0.7324035803523475 | 0.7460317981833594 | 0.8849131254865326 |

Note: `seasonal_naive` (0.7193) **beats** `gpt2_miflu` (0.7324) at L24, and also at L36/L48, on validation (`baseline_comparison.csv`).

### Stage E — author-966 (`hpc_results/stage5_a2/scoring/average_mse_4L.csv`, `hpc_results/stage6/scoring/average_mse_4L.csv`)
| model | average_MSE_4L |
|---|---:|
| notext (control) | 1.922158 |
| miflu | 2.041519 |
| nlinear | 2.049550 |
| dlinear | 2.347832 |
| timecma_llm | 2.670009 |
| patchtst | 3.920470 |
| itransformer | 3.984699 |
| qwen_time_llm | 5.219555 |
| calf_llm | 5.515300 |

Full per-horizon values for every stage are in `OLD_4V4_RESULT_TABLE.csv`.

---

## Q7 — Prediction artefacts

**Yes — prediction artefacts exist locally, and they are re-scorable.**

- **Stage D (final Test/Holdout):** 84 run directories under `results/v3_clean/test_eval/results/<run_key>/`, each with `predictions/test_predictions.csv` (long schema, z + physical), 4 metric JSONs, `test_manifest.json`, `test_status.json`.
- **`test_eval/test_eval_download.tar.gz`** (146,022,533 B): a tar.gz of exactly the same 84 directories — **845 entries = 253 dirs + 592 files**; it contains **only CSV** predictions and JSON metrics/manifests — **no `.npy`/`.npz`**. (Listing only; extracted to a temp dir outside the repo — not into the repo.) Re-scoring the CSV reproduced the stored metrics bit-exactly (metric_discrepancies.md: 52/52).
- **Stage E (author-966):** 44 `.npz` in `hpc_results/stage5_a2/scoring/predictions/` (`pred_<model>_L<L>_s<seed>.npz`, keys `pred/target/target_start_row/...`). The **Stage-6 116 npz are NOT mirrored locally** (`results/stage6/scoring/predictions/` absent) — `UNRECOVERED` locally, though scores are retained.
- **Stage B (innovation v2):** per-run `validation_predictions.csv` under `results/innovation/runs/*/predictions/` and the one-time-Test predictions under `results/innovation/test_evaluations/final_nlinear_20260915T145710Z/predictions/`.
- **Stage A:** per-rep `predictions_miflu_L*_paper_protocol.csv` under `results/ili/journal_evidence/...` and `hpc_results/{data,paper_exact}/`.
- **Stage C Wave-1 8-model:** only aggregated metric rows survive locally (`wave1_analysis_dataset.jsonl` / `analysis_dataset.csv`); raw per-run Wave-1 prediction arrays were not mirrored (compact checkpoints only) → per-model raw predictions are **partial/UNRECOVERED**.

Full inventory: `OLD_4V4_PREDICTION_ARTIFACTS.csv`.

---

## Q8 — The Chinese final report (DOCX)

- **Exact path:** `results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版.docx`
- **SHA-256:** `9C573F48FB65E590C7973223D6CB5E0AB74E2DFA4F6DF11EC936F980A6B50EAD`
- **Size / mtime:** 1,372,896 B; 2026-09-22 02:24. Source markdown (earlier, 2026-09-21 17:16): `results/v3_clean/analysis/final_cleanup_audit/MIFlu_非LLM与LLM流感预测最终报告_中文版.md`.
- **Structure:** 139 paragraphs, all style `Normal` (no Heading styles applied). Section headings (in order): 一句话结论（先读这里）; 一、这份报告如何评估模型性能（零基础导读）; 二、研究方法与冻结选型规则; 三、Wave-1 验证阶段：8 个架构的筛选; 四、机制发现：LLM 的"创新点"到底有没有用; 五、一次性 Test/Holdout 最终评估 (5.1 最终对比（三个冻结模型）; 5.2 泛化反转：验证冠军 ≠ 最终 Test 冠军; 5.3 逐时长误差; 5.4 峰值预测误差（PTE / PIE）; 5.5 最终预测曲线 vs 地面真值（必看）); 六、统计方法与确认性检验; 七、最终工作流与证据完整性; 八、诚实结论; 九、局限性; 附录 A：12 张预测曲线面板（Test/Holdout）; 附录 B：数据与产物.
- **Tables (5):** (0) Final Test ranking — NLinear 2.739 / GPT-2 MIFlu 3.051 / Seasonal-Naive 4.279; (1) 8-stage workflow table; (2) PTE/PIE hit table; (3) confirmatory tests C1/C2/C3; (4) integrity checks (84 runs, 25/25 audit).
- **Figures:** 12 embedded PNGs (Figures A–H + panels); **Figure I has a caption but its image is missing** (13 captions, 12 images).

Report values traced to their CSVs in `OLD_4V4_REPORT_VALUE_PROVENANCE.csv`.

---

## Q9 — Seasonal Naive in the old project

Two **different** seasonal-naive formulas exist. This is a genuine discrepancy.

### Formula 1 — B-track / Wave-1 / clean-v3 (Stages A-D), `scripts/innovation/clean_metrics.py::naive_prediction_frame`
`src = (T - 1) + (k + 1) - lag`, `lag = 52`, then `src = min(max(src, 0), T - 1)`.
It indexes **inside the input window `X_val` (length T=104)** and **clamps** to `[0, T-1]`.
For L=60, `src = 52 + k`; for k ≥ 51 it clamps to `T-1 = 103` = the **last observed input row** (absolute `ts-1`). **It never reads a future target row.**
**Verified** on `results/v3_clean/test_eval/results/baseline__seasonal_naive__L60__seedna__w1/predictions/test_predictions.csv`: steps 51…59 all equal `8.653897` (the clamped last input value); `max|pred[s] − true[s−52]| = 7.37` (i.e. no leakage).

### Formula 2 — A2 / author-966 (Stage E), `scripts/train_naive_966.py::naive_predictions`
`ref = ts + s - SEASONAL_LAG` (`s` = step 0…L-1, `ts` = absolute target-start row), with only a `ref < 0 → 0` clamp.
**No upper clamp, so for L=60 with s = 52…59 it reads absolute rows `ts+0, ts+1, … ts+7` — the FIRST 8 rows of the target block, i.e. FUTURE (unobserved-at-origin) target rows.** The in-file assertion `ref < ts + s` passes but only compares a row to itself, so it does **not** prevent reading another target row; the docstring's "No future observation is ever read" is therefore **incorrect for L=60**.
**Verified** on `hpc_results/stage5_a2/scoring/predictions/pred_seasonal_naive_L60_s42.npz`: `max|pred[:,:,52] − target[:,:,0]| = 0.000e+00`, … `max|pred[:,:,59] − target[:,:,7]| = 0.000e+00`. (No leak for L=24/36/48, where s−52 stays before the target block.)

### Which historical results used which
- **Stages A–D (all `results/v3_clean` and `results/innovation` rankings, incl. `baseline_comparison.csv` and the DOCX) use Formula 1** (no leakage).
- **Stage E (`hpc_results/stage5_a2`, `hpc_results/stage6`, and `recovery/stage5/results_tables_zh.md`) use Formula 2** (leaks for L=60).

### Exact old seasonal_naive values per horizon

Formula 1 (B-track, z-space; `results/v3_clean/analysis/baseline_comparison.csv`, `wave1_analysis_dataset.jsonl`):
| L | 24 | 36 | 48 | 60 |
|---|---:|---:|---:|---:|
| seasonal_naive MSE_z | 0.7193443203456401 | 0.7324035803523475 | 0.7460317981833594 | 0.8849131254865326 |
| last_value_naive MSE_z | 2.821200197815767 | 3.422431571802754 | 3.167843944134935 | 2.8250886828401813 |

Final Test (Formula 1): seasonal_naive 4.1579892701 / 4.2769005266 / 4.3827147911 / 4.2991626233 (avg 4.2791918028).

Formula 2 (A2/author-966, z-space; `recovery/stage5/results_tables_zh.md` T1):
| L | 24 | 36 | 48 | 60 |
|---|---:|---:|---:|---:|
| seasonal_naive | 2.5638 | 2.2655 | 2.1425 | **2.1035** |
| last_value_naive | 6.2133 | 7.7138 | 7.8513 | 6.8849 |

(Tell-tale: under Formula 1 the L=60 baseline is the **worst** of the four; under Formula 2 it is the **best**, consistent with the L=60 future-row leak.)

---

## Q10 — Chronology

Full ordering in `OLD_PROJECT_CHRONOLOGY.md`. Key facts:

- The **complete historical comparison finished 2026-09-22** (the DOCX), **before the 2026-09-24 09:54:29 clone** → all of Stages A–D predate the author repository.
- The **author-966 8-model work (Stages E) is post-clone (2026-09-25/26)**, even though the 966-row CSV itself existed locally from 2026-08-28.
- Git history is unusable (single commit `1f6563f`); ordering rests on mtimes and embedded ledger stamps (`frozen_utc 2026-09-15T…`, `receipt_created_utc 2026-09-15T14:57:10Z`, `CHECKPOINT_LOCK_first_20260925T161329Z`, clones log line).

---

## Bottom line

- **Exact 4+4 strings — non-LLM:** `nlinear`, `dlinear`, `patchtst`, `itransformer`. **LLM:** `gpt2_miflu`, `qwen_time_llm`, `calf_llm`, `timecma_llm`.
- **Stages found:** A `early_ili_july2026` (own-MIFlu, Aug–Sep 2026); B `innovation_v2_screening` (Sep 14–16); C `wave1_validation_v3clean` (Sep 17–21, the headline ranking); D `final_test_holdout_v3clean` (Sep 21, one-time Test + deferred controls); E `a2_author966_stage5` / `stage6_author966_8model` (post-clone Sep 25–26).
- **Historical MIFlu implementation path:** `scripts/miflu_model.py` (class `MIFlu`), wrapped by `scripts/innovation/backbones/gpt2_miflu_adapter.py` — the project's own re-implementation, not the author's code.