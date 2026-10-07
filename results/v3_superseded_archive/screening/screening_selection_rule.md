# Screening selection rule (frozen)

Generated 2026-09-16T21:06:49Z — **before** any aggregated Screening result existed.

Frozen reference baseline: **`last_value_naive`** (same reference for every model and both horizons).

## Score

```
r_h = mean over seeds(42,43,44) of full-horizon z-space val MSE at horizon h
r_h = r_h / mean z-space val MSE of `last_value_naive` at the same horizon
S   = ( r_24 + r_60 ) / 2          # lower is better
```

## Advancement

1. rank within Group A and within Group B separately by ascending `S`
2. retain at least the top two of each group for Full Validation
3. two models within **1%** of `S` are a tie; break by, in order:
   1. lower mean full-horizon validation MAE (z-space), averaged over horizons and seeds
   2. better step-0 ILITOTAL z-space MSE, averaged over horizons and seeds
   3. better literature peak criterion performance (higher mean peak_hit_ratio, then more PTE<=1w & PIE<=25% passes)
   4. fewer trainable parameters
   5. lower GPU-hours
4. if a tie remains: advance both, or stop for a budget amendment — **never** use Test evidence
5. an entire architecture group is never eliminated

## Immutability

- the rule is immutable after aggregated results are first read; any change requires a documented budget amendment and invalidates the Screening outcome
- Pilot metrics may not enter Screening selection.
- No Test or holdout evidence is used at any point.
