# R1B SCORING CONTRACT

## Metric

| Item | Value |
|---|---|
| space | **StandardScaler z-space** (PAPER_EXPLICIT for national; the code never calls `inverse_transform`) |
| per-cell MSE | mean of squared error over **(origins x leads x 7 variables)** |
| per-cell MAE | mean absolute error over the same axes |
| four-horizon average | **equal weight** over L in {24,36,48,60} — PAPER_EXPLICIT (verified arithmetically: 1.4355 / 0.74525) |
| seed aggregation | mean over repetitions **first**, then equal-weight over horizons |

## Independent scoring

Scoring is performed by `f1_preflight_20261006/scorer_f1.py`, which:
* **validates before any arithmetic** — the original scorer raised on a shape mismatch
  instead of rejecting it;
* **delegates the arithmetic** to `scripts/score_predictions_independent.py`, so the two
  cannot drift;
* runs **20/20** acceptance checks, including rejection of missing keys, duplicate keys,
  shape mismatch, NaN, Inf, wrong variable count, wrong scaling space, non-strict
  containment, Historical-Track-B profile and **Test-selected checkpoint metadata**.

## Artefact schema

`pred_<tag>.npz` carries `pred`, `target`, `target_start_row`, `L`, `seed`, `var_cols`,
`train_mean`, `train_std`, `model`, `profile`, `containment`, `space`,
`checkpoint_selection`, `track`.

## The gate that was added because it was needed

`G3b_no_duplicate_keys` — a real F1 run produced **8 duplicate `(model, L, seed)` keys**
because `score_test_stage5.py` dumps its own naive baselines while the leakage-safe runner
dumps its own, and the aggregator silently **averaged the two**. Duplicate keys are now a
hard failure, unit-tested against a synthetic duplicate.
