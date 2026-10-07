# CROSS-TRACK COMPARISON RULES

Generated 2026-10-06. Companion to `CROSS_TRACK_COMPATIBILITY_MATRIX.csv` and
`TRACK_SEPARATION_RULES.md`.

---

## 1. The default

```
INCOMPATIBLE_ACROSS_TRACKS_UNLESS_PROVEN_OTHERWISE
```

A cross-track comparison is admissible **only** when every field in
`CROSS_TRACK_COMPATIBILITY_MATRIX.csv` is either identical or explicitly shown to be
irrelevant to the quantity being compared. In practice that has not happened for any pair
yet, so **every pairwise verdict in the matrix is `NOT_DIRECTLY_COMPARABLE`.**

---

## 2. Why even A1-P vs A2-F fails

They share repository, commit, dataset, split, scaler, input length and horizons — the
most of any pair — and they **still** differ in:

- checkpoint-selection rule,
- text-path behaviour,
- epoch / lr configuration,
- metric aggregation scope.

Those four differences are exactly the ones that determine the number. Sharing a
codebase is not the same as sharing a contract.

---

## 3. Worked example: what must never be written

The following are prohibited statements, with the reason:

| Prohibited | Why |
|---|---|
| "Track A 2.0415 vs Track B 0.7709" | different dataset, seed count, scaler and test window — the 2.6× gap is protocol, not performance |
| "A0-R 0.5793 beats the paper's 1.542" | different measurement: one channel vs seven, Test-selected vs (unknown) rule, 1 repetition vs 10 |
| "Historical Qwen 5.22 vs new Qwen X" | the historical artifact was **reduced after training** (4,167×), so it is not the trained model |
| "the group mean of LLMs is worse, therefore LLMs are worse" | the implementations are a fixed selection, not a random sample; and the best individual is an LLM on one track |
| "we reproduced Table V" | no Table V number has been reproduced at all (`TABLE_V_REPRODUCIBILITY_VERDICT.md`) |

---

## 4. Admissible statements

| Statement | Why admissible |
|---|---|
| "the released code's text path is inactive under deterministic equal-length intervention" | single track (A0-R), verified on CPU and A100, positive control included |
| "MIFlu wins 7 of 12 paired cells against NLinear within the A2-basis protocol, mean difference −0.0080" | within one track, one protocol, one pairing |
| "the four A0-R horizons took 942/978/1014/1054 s" | measured, single track |
| "the historical deployment family is 204.6 GiB and only 66.7 MiB of it is byte-identical" | storage fact, independent of any model comparison |

---

## 5. Reporting template

Every table that contains numbers must carry:

```
track        = one of A0-R | A1-P | A2-F | Historical_Track_B | July2026_dataset
protocol_id  = an identifier for the exact contract used
independent_scoring = yes | no | impossible
```

Tables that would mix `track` values must be **split**, not annotated.

---

## 6. Enforcement checklist before publishing any comparison

- [ ] both sides carry the same `track` value, or the table is split
- [ ] the dataset version is identical and stated
- [ ] the split, scaler and containment rule are identical
- [ ] the evaluated variables are identical
- [ ] the checkpoint-selection rule is identical
- [ ] the aggregation rule is identical
- [ ] seeds are paired, or the unpaired nature is stated
- [ ] predictions exist for both sides, or "cannot be independently scored" is stated
- [ ] the win-count direction convention is stated (`A wins iff diff < 0`)

If any box is unchecked, the comparison is reported as `NOT_DIRECTLY_COMPARABLE` and the
difference is described qualitatively instead.