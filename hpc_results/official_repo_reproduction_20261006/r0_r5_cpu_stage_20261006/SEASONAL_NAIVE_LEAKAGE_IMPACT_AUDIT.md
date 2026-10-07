# SEASONAL NAIVE LEAKAGE IMPACT AUDIT

Generated 2026-10-06. Traces the known Seasonal-Naive defect through every affected
artifact. **Nothing is overwritten**; this is an audit.

---

## 1. The two formulas — and why only one leaks

The project contains **two different seasonal-naive implementations**. They are not
equivalent, and only one of them is leaky.

| | **A — the SAFE one** | **B — the LEAKY one** |
|---|---|---|
| file | `results/v3_clean/.../clean_metrics.py` | `scripts/train_naive_966.py::naive_predictions` |
| reference index | `src = (T-1) + (k+1) - 52`, **clamped** | `ref = ts + s - 52`, **no upper clamp** |
| where `ts` is | — | the **first target row**, so the origin is `ts-1` |
| guard | clamp to the last observed input row | `assert ref < ts + s` — **trivially true for any positive lag** |
| **future read at L=60?** | **NO** | **YES** |

### The leak, stated exactly

For lead index `s` (0-based), the target row is `ts + s`. The leaky formula references
`ts + s - 52`. That reference lies **after the origin** `ts - 1` whenever `s ≥ 52`:

| s | reference row | available at origin `ts-1`? |
|---:|---|---|
| 0 … 51 | `ts-52 … ts-1` | ✅ yes |
| **52 … 59** | **`ts+0 … ts+7`** | ❌ **these are ACTUAL TARGET ROWS inside the forecast window** |

So **8 of the 60 leads** at L=60 read the future. L=24, 36 and 48 are unaffected, because
`s` never reaches 52.

**Independent confirmation** (from the historical-inspection agent): in the A2/966
artifacts, `pred[:, :, 52] == target[:, :, 0]` to **0.000e+00** — the forecast for lead 53
is literally the actual value of lead 1.

**Second confirmation** (this round): `naive_leakage_safe.py` reproduces the published
values **bit-identically at L=24/36/48** and differs **only at L=60**.

---

## 2. Which stages are affected

| Stage | Formula used | Affected? | Evidence |
|---|---|---|---|
| **A** `early_ili_july2026` (`results/ili`, `hpc_results/data`) | own paper-protocol track | **not assessed here** | separate track; no 4-vs-4 role |
| **B** `innovation_v2_screening` (`results/innovation`) | — | n/a | nlinear was the champion; seasonal naive not the reported comparator |
| **C** `wave1_validation_v3clean` — **the historical 4-vs-4** | **A (SAFE)** | **NO** | `clean_metrics.py` clamps; verified L60 steps 51-59 clamp to the last input value |
| **D** `final_test_holdout_v3clean` | **A (SAFE)** | **NO** | same code path |
| **E** `a2_author966_stage5` / `stage6_author966_8model` | **B (LEAKY)** | **YES, at L=60** | `train_naive_966.py` |
| **F1** (frozen) | leakage-safe corrected | **NO** | `naive_leakage_safe.py`, verified |

### The headline conclusion

> **The historical 4 LLM vs 4 non-LLM comparison is NOT affected.** It used the safe
> formula. Its seasonal_naive values (L24/36/48/60 = **0.71934 / 0.73240 / 0.74603 /
> 0.88491**) are leakage-free.
>
> **The author-966 A2/stage-5/stage-6 track IS affected**, at L=60 only.

This matters directly for the primary objective: **the controlled MIFlu replacement will
not inherit a leakage defect from the historical comparison.**

---

## 3. Numerical impact

| Track | L=24 | L=36 | L=48 | **L=60** | 4-horizon mean |
|---|---:|---:|---:|---:|---:|
| **C/D — safe (historical 4-vs-4)** | 0.71934 | 0.73240 | 0.74603 | **0.88491** | **0.77067** |
| E — leaky (author-966 A2) | 2.5638 | 2.2655 | 2.1425 | **2.1035** | 2.26880 |
| E — corrected | 2.5638 | 2.2655 | 2.1425 | **1.9174** | **2.22229** |

**The correction changes the author-966 seasonal naive at L=60 by −0.186**, and its
four-horizon mean from 2.26880 to **2.22229**.

### Does it change any ranking?

| Ranking | Effect |
|---|---|
| historical 4-vs-4 Validation (Wave-1) | **none** — safe formula |
| historical 4-vs-4 final Test/Holdout | **none** — safe formula |
| author-966 A2-basis ranking | seasonal naive moves 2.2688 → 2.2223; it was 5th of 5 learned+naive entries either way, so **no rank change**, but the *margin* to NLinear (2.0496) narrows |
| F1 | already uses the corrected value |

### Does it change any conclusion?

- Historical report: **no**, because that track is unaffected.
- Any statement quoting the author-966 seasonal naive at L=60 or its 4-horizon mean:
  **yes**, must be updated to 1.9174 / 2.22229.

---

## 4. Which artifacts must be corrected

| Artifact | Affected? | Action required | Overwritten? |
|---|---|---|---|
| `scripts/train_naive_966.py` | **yes** — the defect lives here | **do not edit**; superseded by `naive_leakage_safe.py` | ❌ no |
| `hpc_results/official_repo_reproduction_20261006/benchmark_results_average_4L.csv` | yes (seasonal row) | additive correction note | ❌ no |
| `hpc_results/official_repo_reproduction_20261006/benchmark_results_trackB_july.csv` | **no** (safe formula) | none | ❌ no |
| `results/v3_clean/**` | **no** | none | ❌ no |
| the Chinese DOCX final report | **no**, on this defect | but see the DOCX dependency map | ❌ no |
| F1 outputs | no (already corrected) | none | ❌ no |

**Nothing was overwritten.** Corrections are carried additively, as the project rules require.

---

## 5. Why the guard failed, and the fix

```python
assert ts + s - SEASONAL_LAG < ts + s          # in train_naive_966.py
```

This asserts that the reference precedes the **target** row. It is true for **every**
positive lag and therefore checks nothing about the **origin**. The correct invariant is
`ref <= origin = ts - 1`.

The corrected implementation (`naive_leakage_safe.py`) uses

```
ref = ts - 52 + (s mod 52)
```

which satisfies `ref <= origin` for every lead and every lag ≥ 1 — proved by exhaustion
across lags {1, 2, 7, 12, 52, 53, 104} × leads 0…59 in its self-test.

---

## 6. What must NOT be done

| Prohibited | Why |
|---|---|
| copying F1's corrected seasonal value into the historical 1025-row ranking | different dataset and forecast keys |
| "fixing" `train_naive_966.py` in place | append-only rule; the defect record must survive |
| re-running the historical comparison to fix a defect it does not have | the historical track is unaffected |
| reporting the corrected value without naming the contract it belongs to | the two tracks are not comparable |