# R9 — EXPECTED OUTPUT SCHEMA

## Files the replacement experiment must produce

| File | Contents |
|---|---|
| `replacement_miflu_per_seed.csv` | one row per (horizon, seed): MSE, MAE, checkpoint path, seed |
| `replacement_miflu_aggregate.csv` | per-horizon mean and SD over the 10 seeds, plus `average_MSE_4L` |
| `old_vs_new_miflu.csv` | old and new values side by side, per horizon, with absolute and relative differences |
| `ranking_old.csv` / `ranking_new.csv` | the 8-model ranking at each stage, with rank deltas |
| `group_summaries_old_new.csv` | LLM-side and non-LLM-side means, **labelled as descriptive** |
| `paired_tests_corrected.csv` | every pairwise comparison with `wins_A + wins_B + ties == n_cells` asserted |
| `per_seed_deltas.csv` | new − old per seed, so dispersion is visible rather than hidden in a mean |
| `cost_comparison.csv` | GPU-hours, wall time, peak VRAM, checkpoint bytes, on both sides |
| `replacement_gate_report.json` | the gates below |
| `REPLACEMENT_REPORT_ZH.md` / `_EN.md` | the write-up |

## Gates the replacement must pass

| # | Gate |
|---|---|
| R1 | the new MIFlu origins are **identical** to the historical origins at every horizon |
| R2 | `var_cols` identical across all eight models |
| R3 | no duplicate `(model, horizon, seed)` keys |
| R4 | one scorer used for all eight |
| R5 | the seasonal-naive reference is the **safe** formula |
| R6 | the historical dataset hash is pinned and verified |
| R7 | the run is labelled "transferred to the historical comparison contract" |
| R8 | the seven historical models' predictions are **unchanged** |

## Prohibited outputs

| Prohibited |
|---|
| a ranking that mixes author-966 and 1025-row values |
| a "best model" claim from the group mean alone, or from the best-in-group alone |
| any label suggesting the transferred run reproduces the paper |
| overwriting any historical CSV, figure or report |
