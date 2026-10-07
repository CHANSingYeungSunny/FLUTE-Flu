# v2 champion-selection equivalence audit (READ-ONLY)

Generated 2026-09-17T03:30:00Z.

## Verdict

**`NOT_EQUIVALENT`** → **`V3_V2_PROTOCOL_EQUIVALENCE_REVIEW_REQUIRED`**

The proposed primary endpoint **cannot be shown to be equivalent** to v2's actual
NLinear champion-selection endpoint. Per the instruction ("如不等价，立即停止"),
**no further action was taken**.

## Nothing was done

| Action | Status |
|---|---|
| old v3 archived | **no** |
| `results/v3_clean/` created | **no** (deliberately) |
| new isolated HPC root created | **no** |
| clean rerun started | **no** |
| contamination scan run | **no** |
| HPC jobs submitted this turn | **0** |

## Proposed endpoint

- **Primary**: `ILITOTAL fixed_step=0` validation MSE
- **Secondary**: `ILITOTAL fixed_step=0` MAE; `ILITOTAL` fixed steps 1/2/3 MSE/MAE (reported separately); `ILITOTAL` full-horizon MSE/MAE per `L`
- **Literature metrics**: `PTE = |predicted peak week - true peak week|`, `PIE = |predicted peak intensity - true peak intensity| / true peak intensity`, with `PTE <= 1 week` and `PIE <= 25%`
- **Forbidden**: Peak Hit Rate, custom 20% PIE, 2-week timing, ±2-week matching window, peak-aware checkpoint gate

## What v2 actually used

From `scripts/innovation/select_best_model.py` (docstring lines 23–26 and the scoring body) and `MIFlu_innovation_plan_v2.md` lines 86–89:

- **primary score** = mean over the **four horizons {24, 36, 48, 60}** of
  `mean_seeds(candidate best_val_mse) / mean_seeds(gpt2_miflu baseline best_val_mse)`
- **metric** = `best_val_mse` = the **full 7-variable, full-horizon** validation MSE
- **reference denominator** = the **`gpt2_miflu`** model (`BASELINE_MODEL`, line 53)
- **hard gate** = `peak_not_below_baseline` — a **peak-aware** rule
- **tie-breakers** = val MAE → **peak_hit_ratio** → trainable params → training time

## Material non-equivalences

| # | Proposed | v2 actual |
|---|---|---|
| NE1 | reference = `last_value_naive` (naive baseline) | reference = **`gpt2_miflu`** |
| NE2 | `ILITOTAL` channel only | **full 7-variable** validation MSE |
| NE3 | **fixed_step = 0** as primary | complete multi-step horizon; **no fixed-step endpoint** |
| NE4 | horizons **{24, 60}** (Screening) | **{24, 36, 48, 60}**, equally averaged |
| NE5 | forbids Peak Hit Rate / peak-aware gate | v2 used `peak_hit_ratio` as **both a gate and a tie-breaker** |
| NE6 | forbids ±2-week matching window | `metrics.py` `series_peak_metrics(..., match_tol=2)` implements a **±2-week** matched-peak window |
| NE7 | forbids 2-week timing | `compute_miflu_indicators.py` documents a **relaxed `PTE <= 2.0 wk`** variant |

**NE5–NE7 are direct conflicts**: the proposed protocol forbids constructs that v2
actually used in, or alongside, champion selection.

## What does match

`scripts/innovation/metrics.py` lines 43–44 set `PEAK_PTE_MAX_WEEKS = 1` and
`PEAK_PIE_MAX_PCT = 25.0`, which **do** match the literature thresholds. But they
govern the **reported peak criterion**, not v2 champion selection — so this
agreement is **not sufficient** to establish endpoint equivalence.

## Review decisions required

1. Is the new primary endpoint intended to **supersede** v2 selection semantics
   (a protocol revision) or to **reproduce** them?
2. If superseding, explicitly reconcile the **v2→v3 champion-continuity** claim:
   `nlinear` was chosen under a **different** rule.
3. Resolve the explicit conflicts (NE5–NE7): the new protocol forbids constructs
   v2 used.
4. Confirm the horizon set: keep **{24, 60}** or restore **{24, 36, 48, 60}** for
   comparability with v2.
5. Confirm the normalisation reference: `last_value_naive` vs the `gpt2_miflu` baseline.

## Boundaries

Test/holdout access counts remain **0/0**; no champion frozen; no Full Validation
submitted; no model computation performed (this audit is read-only over source and
JSON artifacts and was executed with no HPC jobs).
