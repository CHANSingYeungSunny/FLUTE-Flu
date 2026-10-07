# SEASONAL NAIVE — CODE PATH MAP

Two seasonal-naive implementations exist in this project. **One leaks; one does not.**
This map traces which code path produced which result, so no correction is applied to a
track that never had the defect.

## Path A — the SAFE implementation

```
file     : results/v3_clean/.../clean_metrics.py
formula  : src = (T-1) + (k+1) - 52      # relative to the INPUT window, clamped
clamp    : yes - the reference is clamped to the last observed input row
future read at L=60?  NO
            verified: for L=60 the leads beyond 52 clamp to the last input value
used by  : Stage C  wave1_validation_v3clean   (the historical 4-vs-4 validation ranking)
           Stage D  final_test_holdout_v3clean (the historical one-time Test/Holdout)
values   : L24 0.71934 | L36 0.73240 | L48 0.74603 | L60 0.88491 | mean 0.77067
```

## Path B — the LEAKY implementation

```
file     : scripts/train_naive_966.py :: naive_predictions()
formula  : ref = ts + s - 52             # ts = the FIRST TARGET row; origin = ts-1
guard    : assert ts + s - 52 < ts + s   # trivially true for ANY positive lag
clamp    : NONE on the upper side
future read at L=60?  YES - 8 leads
            s = 0..51  -> ref = ts-52 .. ts-1      available at the origin
            s = 52..59 -> ref = ts+0  .. ts+7      ACTUAL TARGET ROWS
            independently confirmed: pred[:, :, 52] == target[:, :, 0] to 0.000e+00
used by  : Stage E  a2_author966_stage5 / stage6  (the author-966 A2 basis)
values   : L24 2.5638 | L36 2.2655 | L48 2.1425 | L60 2.1035 (LEAKY) | mean 2.26880
corrected: L24 2.5638 | L36 2.2655 | L48 2.1425 | L60 1.9174        | mean 2.22229
```

## Path C — the corrected implementation

```
file     : f1_preflight_20261006/naive_leakage_safe.py
formula  : ref = ts - 52 + (s mod 52)
property : ref <= origin for EVERY lead and EVERY lag >= 1
            proved by exhaustion over lags {1,2,7,12,52,53,104} x leads 0..59
policy   : insufficient history marks the lead INVALID rather than clamping to row 0
           (silently forecasting from row 0 fabricates a value)
used by  : F1 (frozen)
```

## The traceability conclusion

| Stage | Path | Affected |
|---|---|---|
| C — Wave-1 validation (the historical 4-vs-4) | **A (safe)** | **NO** |
| D — final Test/Holdout | **A (safe)** | **NO** |
| E — author-966 A2 / stage-5 / stage-6 | **B (leaky)** | **YES, L=60 only** |
| F1 | C (corrected) | no |

> **The historical 4-vs-4 comparison is not affected, so the controlled MIFlu replacement
> does not inherit the defect.** Only author-966 statements quoting the L=60 seasonal-naive
> value or its four-horizon mean need a correction.

## Why the guard failed

`assert ts + s - SEASONAL_LAG < ts + s` asserts the reference precedes the **target**. It is
true for every positive lag and therefore constrains nothing. The correct invariant is
`ref <= origin = ts - 1`.

## What was done about it

`scripts/train_naive_966.py` was **not edited** — the defect record must survive. The
corrected implementation lives in a new file and is used by F1.
