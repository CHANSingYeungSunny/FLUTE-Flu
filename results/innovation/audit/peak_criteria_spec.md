# Peak-criteria specification (revision 9) — FROZEN BEFORE COMPUTATION

This project implements and reports ONE literature peak criterion:

> **peak hit ⇔ PTE ≤ 1 week AND PIE ≤ 25 %**

where `PTE = |predicted peak week − true peak week|` (weeks) and
`PIE = |predicted peak intensity − true peak intensity| / true peak intensity`
(%). No project-custom thresholds (0.75 / 2.0 wk / 20 % / 0.60) are implemented
or reported anywhere in `scripts/innovation/`.

## Frozen definitions

| Aspect | Decision | Where enforced |
|---|---|---|
| Target variable | **ILITOTAL** (physical patient counts, channel index 4) | `metrics.py`, `ILI=4` |
| Season boundary | **MMWR week 40 of year Y → week 20 of year Y+1**; weeks 21–39 are off-season and NOT scored | `metrics.season_start_year`, `season_bounds` |
| Peak selection | `argmax` within the season window; **ties → earliest week** (`np.argmax` semantics) | `metrics.seasonal_peak_metrics` |
| Incomplete season | a season with **fewer than 26 observed weeks** is NOT scored (`status="incomplete_season"`); its peaks are excluded | `MIN_SEASON_WEEKS = 26` |
| Zero denominator | if the TRUE peak intensity is 0 → PIE is **null (not 0.0)**, `status="zero_denominator"`, and the season is not a hit | `seasonal_peak_metrics` |
| Aggregation | fixed-step (`step=0`) only — one constant lead time per point; never cross-lead mixing | `metrics.aggregate_fixed_step` |
| Horizon independence | each horizon scored independently; cross-horizon mixing forbidden | runner / selector |

## Reported quantities

Per season (CSV `peak_metrics_by_season.csv`): season, n_weeks, status, hit,
gt/pred peak week & value, pte_weeks, pie_pct.
Aggregate (JSON): n_seasons_total / evaluable / incomplete, n_hits,
`peak_hit_ratio` = hits / evaluable, mean PTE, mean PIE, and the frozen
thresholds.

## Note on the two peak definitions in the codebase

* `metrics.seasonal_peak_metrics` — **the reported, literature-standard,
  season-based** definition above.
* `metrics.series_peak_metrics` — a whole-series mirror of the EXISTING
  `compute_miflu_indicators.compute_peak_indicators`, used **only** by
  `tests/innovation/test_numeric_regression.py` to prove the innovation metrics
  layer reproduces the existing pipeline bit-for-bit on the same series.
  It is NEVER reported.
