# Split & Figure-Semantics Read-Only Audit

Generated: 2026-09-21

## Verdict

| Item | Result |
|---|---|
| Report split sentence | **INCORRECT** — "训练 717 / 验证 102 / 测试 1025 个窗口" is false. 1025 is the **total** weekly-timestamp count, not the Test window count. |
| Figure semantics | **CONSISTENT** — "seed-mean lead-1" equals `fig_q1_step_sweep` step0; both are rolling-origin lead-1 concatenations. |
| Action | Correct the report sentence with machine-extracted counts; figures are already semantically correct (no regeneration); regenerate DOCX/PDF; re-QA. |

## 1. Paper settings (cross-checked against `reference_papers/MIFlu_...pdf`)

- **National-Illness:** 7 variables, United States, 2002–2021, including ages 0–4, number of outpatient providers, and total national ILI.
- **Split:** training / validation / test at **70:10:20** (chronological).
- **Look-back:** T = **104** steps ("Predict the next 24 steps given the previous 104 steps").
- **Horizons:** L = **24, 36, 48, 60** (national is long-term, L ≥ 24).
- **Repetitions:** mean of **10** repetitions.
- **Metric space:** MSE and MAE are computed **after StandardScaler normalization** of each input variable (z-space).

All of these match the frozen config (`scripts/configs.py`, `data/scaler_miflu_national.json`).

## 2. Frozen split (timestamps, not windows)

The raw file `data/raw/national_illness_raw.csv` has **1025** weekly rows (`epiweek` 200201–202152; abs_week 0–1024). The 966-row variant (`national_illness_raw_paper_exact.csv`, 200240–202113) is rejected by `assert_full_window`.

| Split | Timestamps | abs_week | Dates (MMWR Sunday) | % of 1025 |
|---|---|---|---|---|
| Train | **717** | 0–716 | 2001-12-30 → 2016-01-31 | 69.95% |
| Validation | **102** | 717–818 | 2016-02-07 → 2018-01-14 | 9.95% |
| Test | **206** | 819–1024 | 2018-01-21 → 2021-12-26 | 20.10% |
| **Total** | **1025** | 0–1024 | 2001-12-30 → 2021-12-26 | 100% |

- `val_end = 819`; first Test **target** abs_week = **820** (2018-01-28).
- Test timestamp 819 (2018-01-21) is **input-context only**, never a target.

## 3. Sliding-window counts (per horizon)

Window generation (`data_pipeline.build_windows` / `date_mapping_and_leakage_audit.py`): T = 104, stride = 1, `nw = 1025 − 104 − L + 1 = 922 − L`, split by **target-start week** `ts = origin + 104`.

| L | Total windows | Train | Validation | Test | Test target abs | First origin | Last origin |
|---|---|---|---|---|---|---|---|
| 24 | 898 | 613 | 103 | **182** | 820–1001 | 716 | 897 |
| 36 | 886 | 613 | 103 | **170** | 820–989 | 716 | 885 |
| 48 | 874 | 613 | 103 | **158** | 820–977 | 716 | 873 |
| 60 | 862 | 613 | 103 | **146** | 820–965 | 716 | 861 |

- Train windows = **613** and Validation windows = **103** for every horizon (independent of L).
- Test windows = **206 − L** (182 / 170 / 158 / 146).

See `split_window_counts_by_horizon.csv`.

## 4. Do not conflate

| Quantity | Value |
|---|---|
| Total weekly timepoints | 1025 |
| Split timepoints | 717 / 102 / 206 |
| Sliding-window count | 613 / 103 / (206 − L) |
| Unique target weeks | 205 (full horizon) or 206 − L (lead-1) |

**The report's error:** it wrote "训练 717 / 验证 102 / 测试 1025 个窗口" — mixing timestamp counts (717, 102) with the total count (1025) and calling it "Test windows". The correct Test window counts are 182/170/158/146 for L = 24/36/48/60.

## 5. Split-boundary facts

- **Input crosses the split boundary (intentional, no leakage):** a window's input is `data[ts−104 : ts]`, so a Test target's input legitimately includes the trailing validation weeks and even the first Test timestamp 819 as *context*; the target starts strictly after the input ends.
- **Full future L must lie inside the data:** test target starts are capped at `1025 − L`, so the last L−1 test timestamps (1026−L … 1024) are reached only via step ≥ 1 of earlier windows, never as a window start.

## 6. Figure semantics

| Aspect | Reference (`fig_q1_step_sweep` step0) | Final Test figures |
|---|---|---|
| Aggregation | `aggregate_lead_time(mode="fixed_step", step=0)` | `load_seed_mean_curves` + `lead1_curve` (lead_weeks == 1) |
| step0 meaning | keep only step 0 → lead-1 (1-week-ahead) | lead_weeks == 1 |
| Curve type | rolling-origin **lead-1** concatenation | rolling-origin **lead-1** concatenation |
| x-axis | week_start_date | week_start_date (MMWR via `cdc_calendar`) |
| y-axis | ILITOTAL physical | ILITOTAL physical (inverse-scaled) |
| GT / pred style | solid black / dashed red | solid blue / dashed red + peak markers |

**Conclusion:**
- `seed-mean lead-1` **equals** step0 — both are the 1-week-ahead slice, averaged over seeds.
- The curves are **rolling-origin fixed-lead (lead-1) concatenations**, not single-origin full-L-step forecasts.
- At a fixed lead, each target week has **exactly one** forecast origin (`origin = target_week − 104 − step`); the only averaging is across the 7 variables (filtered to ILITOTAL, index 4) and the 10 seeds (seed-mean). This is exactly the fix the old `mean_over_lead` bug needed.
- Figure semantics are **consistent**; no figure regeneration is required. Full comparison in `reference_vs_final_figure_semantics.json`.

## 7. Report fixes applied

1. `MIFlu_非LLM与LLM流感预测最终报告_中文版.md` line 44 — split sentence replaced with machine-extracted timestamp/window counts (see §2–§3).
2. Line 13 — "至 2022 年" corrected to "至 2021-12-26" (last Test target abs_week 1024).
3. Project Summary — already correct (no split-count sentence; caption already says "seed-mean lead-1"); no change required.
