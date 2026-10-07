# Canonical indicator regression

- canonical script: `scripts/compute_miflu_indicators.py` `bf72d37ce9eaa21cb052f18568764d913163caf237ba9ce0cf76f15d98f46c0f`
- peak criterion: PTE <= 1.0 week AND PIE <= 25.0% (only one implemented)
- trained any model: **false** | innovation test artifacts: **0**
- passed: **True**

## Trusted prediction references

| path | sha256 | split | horizon | predates incident | eligible |
|---|---|---|---|---|---|
| `data/predictions_miflu_L24_paper_protocol.csv` | `7ffd66e94b0ebefc…` | test_rows_of_preserved_reproduction_export | 24 | True | True |

## Comparison

| metric | expected | recomputed | abs diff | rel diff | tolerance | result |
|---|---|---|---|---|---|---|
| mse | 244345300.3600282 | 244345300.3600282 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| mae | 9904.792338276957 | 9904.792338276957 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| pte | 1.5 | 1.5 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| pie | 19.489857508005123 | 19.489857508005123 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| row_count | 182 | 182 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| date_start | 2018-01-28 | 2018-01-28 |  |  | exact string | **PASS** |
| date_end | 2021-07-18 | 2021-07-18 |  |  | exact string | **PASS** |
| n_true_peaks | 3 | 3 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| n_hit | 2 | 2 | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| literature_peak_hit | False | False | 0.0 | 0.0 | rtol=1e-09, atol=1e-12 | **PASS** |
| fixed_step_aggregation | fixed_step:step=0 | fixed_step:step=0 |  |  | exact string | **PASS** |

Reference provenance: results/innovation/audit/aggregation_regression_report.json; results/ili/metrics/miflu_L24_ili_peak_trend_summary.json
