# Registry schema v2 — migration policy (innov-v2.3)

## Decision: a NEW versioned file, not an in-place widening

`results/innovation/registry.csv` holds 14 historical rows written before the governance
metadata existed. Widening it with 12 new columns would leave those rows with empty
governance fields — and an empty field must never be inferred as `true`. That ambiguity is
unacceptable for a selection gate, so:

* `registry.csv` — **frozen**. 14 rows, 9 legacy columns, never rewritten.
* `registry_v2.csv` — **new**, append-only, complete schema (`schema_version = 2`).

## Rules

| rule | value |
|---|---|
| history rewriting | forbidden |
| legacy rows | 14, unchanged, permanently ineligible if smoke/failed/missing fields |
| new runs | written to `registry_v2.csv` only |
| append-only | yes; no row is ever edited |
| duplicate `run_id` | rejected |
| write failure | must not be silently ignored |
| missing `selection_eligible` | `false` |
| missing `paper_result_eligible` | `false` |
| missing `test_access_allowed` | `false` |

## How legacy rows are consumed

`select_best_model.py` reads legacy records **only to exclude them**. It never infers a
missing eligibility field as true. The authoritative per-run eligibility still comes from
`run_status.json`, which the runner writes for every run.

Legacy ineligibility is recorded externally in
`results/innovation/governance/legacy_registry_annotation.json` (annotation only — the
artifacts themselves are not modified).

## Stage matrix

| stage | selection_eligible | paper_result_eligible | test_access_allowed |
|---|---|---|---|
| smoke | false | false | false |
| pilot | false | false | false |
| screening | true | true | false |
| full | true | true | false |
| validation / adhoc | false | false | false |
| test (frozen winner only) | false | true | **may be true**, only with frozen-winner manifest + checkpoint hash match + explicit authorization |

`test_access_allowed = true` for any non-`test` stage raises
`INVALID_TEST_ACCESS_FOR_EXPERIMENT_STAGE`.

## Exclusions downstream

Smoke and pilot runs are excluded from: model selection, screening summary, AUC-Best-so-far,
statistical analysis, manuscript tables and rankings. The shared exclusion is driven by
`experiment_stage` + the three fail-closed flags recorded in every layer.
