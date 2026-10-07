# v3 holdout forensics report (read-only)

Generated 2026-09-15T19:59:40Z.
No holdout labels were accessed; no model was run.

## 1. Root cause of the date contradiction

- `release_date` has only **8 distinct values** across 1025 rows, max **2023-10-06**.
- `epiweek` has **1025 distinct values**, range **200201..202152**.
- Therefore `release_date` is the **dataset release stamp**, not the observation date.
- The last observation is **epiweek 202152 (2021 week 52)**, i.e. the week ending 2021-12-26.

## 2. What v2 actually used

| Segment | Rows | epiweeks | Classification |
|---|---|---|---|
| train | 0..716 | 200201-201605 | PROVEN_USED_IN_V2_TRAIN |
| validation | 717..819 | 201606-201804 | PROVEN_USED_IN_V2_VALIDATION |
| test_input_context | 716..819 | 201605-201804 | PROVEN_USED_IN_V2_TEST_INPUT |
| test_target | 820..1024 | 201805-202152 | PROVEN_USED_IN_V2_TEST_TARGET |

- Test target epiweeks: **201805..202152** (205 distinct) - identical to the exported v2 predictions.
- Window arithmetic: `n_windows = N - T - L + 1`; L=24 gives 182 and L=60 gives 146, both implying the same 309-row test segment.

## 3. Content identity

- Canonical SHA-256 **c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d** (72100 bytes)
- All four copies (local + three HPC paths) are byte-identical: **True**
- This is content-level proof, not mtime-based.

## 4. Verdict on the 2022-2023 interval

**REFERENCE_UNAVAILABLE.** There are **0 rows** with epiweek > 202152. The interval does not exist in this dataset, so it can be neither proven untouched nor proposed as a holdout.

## 5. Consequences

- Internal option 1 (future ILI weeks already in the file) is **eliminated**.
- A v3 final holdout requires **new external or genuinely future data**, which needs user acquisition and a licence/access record.
- Until then v3 is **validation-only** and must stop before final holdout evaluation (`V3_VALIDATION_ONLY_NO_NEW_HOLDOUT`).
