# F1 SCORER ACCEPTANCE TESTS

Generated 2026-10-06. Run **before** any F1 GPU time is spent.
Full transcripts: `logs/scorer_acceptance_tests.txt`, `logs/naive_leakage_safe_selftest.txt`.

## 1. Result

```
SCORER ACCEPTANCE TESTS  (all arrays SYNTHETIC - no model results)
RESULT: 20/20 checks passed

naive_leakage_safe self-test
ALL TESTS PASS  (6/6)
```

**Every array used here is SYNTHETIC.** No model result is simulated or fabricated; the
tests exercise rejection logic and arithmetic only.

---

## 2. Two defects found in existing code

### D1 — the scorer CRASHES on a shape mismatch instead of rejecting it

`scripts/score_predictions_independent.py::load_cell` records a shape error and then
immediately performs the subtraction, so the first malformed artefact raises
`ValueError: operands could not be broadcast together` instead of producing a structured
rejection.

**Consequence**: a pilot whose purpose is contract validation would fail with a *crash*
rather than a *diagnosis*.

**Fix**: `scorer_f1.py` validates **everything** before any arithmetic and returns
`(None, errors)`. It delegates the arithmetic to the original functions so the metrics
cannot drift from the audited implementation. **`score_predictions_independent.py` was
NOT modified** (append-only rule).

### D2 — Seasonal Naive leaks at L > 52

`scripts/train_naive_966.py` computes `ref = ts + s - 52`. At **L = 60** that references
rows `ts+0 … ts+7`, which are **actual target rows inside the forecast window**.

Verified: **8 leaking leads (s = 52…59)**. The in-file guard
`assert ts+s-52 < ts+s` is trivially true for any positive lag and checks nothing about
the origin.

**Fix**: `naive_leakage_safe.py` uses `ref = ts - 52 + (s mod 52)`, which is `<= origin`
for every lead and every lag ≥ 1 — proved by exhaustion across lags 1, 2, 7, 12, 52, 53,
104 × leads 0…59.

**Independent corroboration** — the corrected implementation reproduces the published
naive numbers **bit-identically wherever no leakage is possible**, and differs **only**
at L = 60:

| model | L | published (legacy) | leakage-safe | delta |
|---|---:|---:|---:|---:|
| seasonal_naive | 24 | 2.563768 | 2.563768 | 0.000000 |
| seasonal_naive | 36 | 2.265501 | 2.265501 | 0.000000 |
| seasonal_naive | 48 | 2.142458 | 2.142458 | 0.000000 |
| **seasonal_naive** | **60** | **2.103470** | **1.917433** | **−0.186037** |
| last_value_naive | 24 / 36 / 48 / 60 | identical | identical | 0.000000 |

That is exactly the expected signature: unchanged where there is no leakage, changed
where there is, and **Last Value unaffected at every horizon** because its formula never
used a seasonal lag.

**Consequence**: the project's published `seasonal_naive` four-horizon average
(2.268799) becomes **2.222290** under the corrected implementation. The existing
benchmark table's naive row is affected — recorded here, not silently changed.

---

## 3. The 20 checks

### A. Rejection — 15 checks, all PASS

| # | Check | Observed |
|---|---|---|
| A1 | missing prediction arrays | rejected: `missing array 'pred'` |
| A2 | wrong variable count | rejected: `expected 7 variables, got 6` |
| A3 | NaN | rejected: `non-finite values in pred (1 cells)` |
| A4 | Inf | rejected: `non-finite values in pred (1 cells)` |
| A5 | pred/target shape mismatch | rejected: `pred(5,7,24) != target(4,7,24)` |
| A6 | duplicate `(model, L, seed)` keys | 1 duplicated key group detected |
| A7 | expected-but-absent model | reported `['never_trained']` |
| A8 | incomplete horizon set | no aggregate produced |
| A9 | unbalanced seed counts | flagged `{24: 2, 36: 1, 48: 1, 60: 1}` |
| A10 | **Historical Track B artefact** | **rejected** |
| A11 | incompatible scaling space | rejected |
| A12 | non-strict containment | rejected |
| A13 | **Test-assisted checkpoint metadata** | **rejected** |
| A14 | missing variable keys | rejected |
| A15 | mixed seed identifiers | detectable for pairing |

### B. Correctness — 5 checks, all PASS

| # | Check | Observed |
|---|---|---|
| B1 | hand-computed MSE/MAE (all-ones error) | 1.000000 / 1.000000 |
| B2 | per-variable decomposition | 7 entries |
| B3 | per-lead decomposition | 24 entries |
| B4 | equal-weight four-horizon average (hand-computed 2.5) | 2.500000 |
| B5 | per-horizon values kept separately | `{24: 1.0, 36: 2.0, 48: 3.0, 60: 4.0}` |

The paired-statistics convention is covered separately by the four unit tests in
`../postrun_audit_20261006/paired_stats_unit_test_results.txt`: **A wins iff `diff < 0`**,
with `wins_A + wins_B + ties == n_cells` asserted on every row.

---

## 4. Dry run on real artefacts

`f1_score_all.py --allow-partial` was executed over the eight real leakage-safe naive
artefacts (4 horizons × 2 models):

```
artefacts found         : 8
accepted                : 8
REJECTED                : 0
forecast-key violations : 0
F1 STATUS               = PARTIAL_DRY_RUN_INTEGRITY_OK
```

The completeness gates correctly fail (the four learned arms have not run) — the intended
behaviour, and evidence that the gates discriminate rather than always passing.

Logs: `logs/f1_score_dryrun.txt`, `logs/f1_gate_report.json`,
`logs/f1_ranking_average_4L.csv`.

**One defect in my own dry run was found and fixed**: my first declared key list used
sanitized aliases (`_WEIGHTED_ILI`) where the project uses the raw CDC names
(`% WEIGHTED ILI`). The key check caught it immediately (`8 violations`), and after
correcting the list to match `scripts/configs.py::VAR_COLS` the violations went to zero.
That is the check doing its job on a real mistake.

---

## 5. What these tests do NOT establish

They do not show that any model is accurate, that the contract matches the paper, or that
the ranking will be meaningful. They establish only that **the measurement apparatus
rejects what it should reject and computes what it claims to compute** — the prerequisite
for spending GPU time at all.