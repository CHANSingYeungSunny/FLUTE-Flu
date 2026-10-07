# FIGURE CORRECTIONS — IEEE JBHI submission

All figures regenerated on 2026-09-01 23:52 by `scripts/make_submission_figures.py`.

## What was fixed (summary)

- **Q3 (Y axis)**: every continuous figure now plots `*_ili_phys` (patient counts), NOT z-scores. The old figures showed 0–12 and were mislabeled "patient count".
- **Q2 (X axis)**: every figure uses real CDC epiweek dates from `cdc_calendar` (abs_week 820 -> 2018-01-28), not the synthetic grid that drifted ~19 weeks.
- **Q1 (aggregation)**: collapsed with `fixed_step, step=0` (constant 1-week-ahead lead); the mixed-lead `mean_over_lead` alternative is shown only as a contrast in the Q1 proof figure.
- **Q4/Q5 (recipe)**: `full` baseline is empirically optimal (MSE 2.5187) vs adamw_cosine (2.6642) / huber_clip / earlystop (2.8799).

## Per-figure table

| Figure Name | Q addressed | Key Fix Applied |
|---|---|---|
| fig_miflu_eval_continuous_L24.png | Q2, Q3 | Y-axis now PHYSICAL patient counts (was z 0-12); X-axis REAL CDC dates (was 19-week drift); COVID shading + hallucination annotation; peak markers; supplementary indicator box. |
| fig_miflu_eval_continuous_L36.png | Q2, Q3 | Same fixes as L24; phys columns + real dates attached via cdc_calendar. |
| fig_miflu_eval_continuous_L48.png | Q2, Q3 | Same fixes as L24; phys columns + real dates attached via cdc_calendar. |
| fig_miflu_eval_continuous_L60.png | Q2, Q3 | Same fixes as L24; phys columns + real dates attached via cdc_calendar. |
| fig_q1_aggregation_policy_proof.png | Q1 | NEW: fixed_step (182 wk, n_windows=1, constant lead) vs mean_over_lead (205 wk, n_windows 1..24, lead drift). |
| fig_q3_inverse_transform_proof.png | Q3 | NEW: z-space vs physical side-by-side; identical shape proves patient_count = z × 8853.4 + 9368.3. |
| fig_q4_training_recipe_comparison.png | Q4, Q5 | NEW: bar chart of 4 recipe MSE; baseline highlighted as optimal. |

## Data sources

- L24/36/48/60 (full, rep_01): `results/ili/journal_evidence/full/reps_1_to_10/rep_01/predictions_miflu_L{24,36,48,60}_paper_protocol.csv`
  (all four horizons drawn from the SAME 1025-row window, last-20% test set = 2018-2021; NO legacy/966-row CSVs)
- Scaler: `data\scaler_miflu_national.json` (mean_=9368.3, scale_=8853.4)
- Recipe MSE: `results\ili\journal_evidence\journal_table_viii_all_variants.csv`
