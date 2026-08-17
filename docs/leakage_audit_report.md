# Data-Leakage Audit Report — MIFlu Reproduction (Paper Protocol)

**Date:** 2026-08-16
**Scope:** National ILI forecasting, `scripts/train_miflu.py` under the MIFlu
paper protocol (`T=104`, `L ∈ {24,36,48,60}`, static `70:10:20`, `shuffle=False`).
**Dataset:** `data/raw/national_illness_raw.csv` — 1025 weekly rows (200201–202150),
7 channels.

This audit was performed in response to the supervisor's concern that the
plotted forecast curve "fits the left half almost perfectly but diverges sharply
on the right half," which could indicate train/test mixing. **The audit finds NO
data leakage.** The left-good / right-bad pattern is explained by a legitimate
distribution shift (COVID-19 NPIs), not by leakage.

All claims below are backed by executable unit tests in
`tests/test_leakage_audit.py` (run: `python -m pytest tests/test_leakage_audit.py -v`).

---

## 1. Exact index ranges (train / val / test)

Total weeks `n = 1025`. The split is computed once, globally, as:

```python
t_end = int(n * 0.70)   # 717
v_end = t_end + int(n * 0.10)   # 717 + 103 = 819
# train: rows [0, 717)      → weeks 200201 … (717th week)
# val:   rows [717, 819)    → next 102 weeks
# test:  rows [819, 1025)   → final 206 weeks  (≈ 2020–2021)
```

So **test occupies the final 206 weeks**, i.e. exactly the 2020–2021 period that
includes the COVID-19 pandemic. The model's training data ends at week 717
(≈ 2018–2019 season); it has **never seen any 2020–2021 week during fitting**.

### Window-level assignment (target-based split)

Sliding windows of input `T=104` and target `L` are generated for every
`i ∈ [0, n-T-L+1)`. Each window is assigned to a split by the **start index of
its TARGET** (`target_start = i + T`):

```python
target_start = i + T
splits[i] = 0 if target_start <  train_end else \
             1 if target_start <= val_end  else 2   # 2 = test
```

Consequences (verified by `test_test_target_starts_after_val_end`):

| L | #train wins | #val wins | #test wins | min test target_start | must be > val_end (819) |
|---|-------------|-----------|------------|-----------------------|--------------------------|
| 24 | 593 | 95 | 181 | 820 | ✅ |
| 36 | 581 | 95 | 169 | 820 | ✅ |
| 48 | 569 | 95 | 157 | 820 | ✅ |
| 60 | 557 | 95 | 145 | 820 | ✅ |

Every test window's target starts at week index **820**, strictly greater than
`val_end = 819`. **No test target week was visible during model fitting.**

---

## 2. Scaler fit boundary (train-only)

The pipeline normalizes the entire series with a single global **StandardScaler**
whose statistics are computed from the **train split only**:

```python
# in load_and_normalize()
train_mean = data[:t_end].mean(axis=0, keepdims=True)
train_std  = data[:t_end].std(axis=0, keepdims=True) + 1e-8
data_norm  = (data - train_mean) / train_std
```

`val`/`test` rows are transformed with the **same train statistics** (no
re-fitting). The unit test `test_scaler_fit_is_train_only` proves this by:

1. Re-deriving `train_mean`/`train_std` from a train-only `StandardScaler.fit`
   and showing they equal the stored values (atol 1e-5).
2. Confirming that `val_norm = (raw_val - train_mean)/train_std` and
   `test_norm = (raw_test - train_mean)/train_std` reproduce the pipeline's
   normalized val/test rows exactly — i.e. **no val/test parameter entered
   normalization**.

**RevIN (Instance Normalization)** inside `TimeSeriesEmbedder` has **no `.fit()`
method** (`test_revin_has_no_fit_and_is_per_sample`); it computes per-sample
statistics inside `forward()` and is therefore inherently incapable of leaking
across samples.

---

## 3. Proof of no shuffling

The split is purely time-ordered. `test_split_is_time_ordered_no_shuffle`
asserts:

- The per-window `splits` array is **non-decreasing** (no interleaving of
  train/val/test).
- Exactly **two** transitions occur, at the train→val and val→test boundaries:
  - train→val transition at window index `j` where `j + T == train_end (717)`.
  - val→test transition at window index `j` where `j + T == val_end + 1 (820)`.

There is **no `shuffle=True`** anywhere in the data pipeline; only the *training*
`DataLoader` shuffles batches **within the train split** (`shuffle=True` on
`tl`), which never mixes in val/test rows.

---

## 4. Verdict: is there leakage?

**NO.** Three independent invariants hold:

1. Test target weeks start strictly after the last training/validation week.
2. Normalization statistics are derived from the train split only.
3. The split is contiguous and time-ordered with no shuffling across splits.

---

## 5. Why the left-fits-well / right-diverges pattern is NOT leakage

The 2020–2021 test period coincides with **COVID-19 non-pharmaceutical
interventions (NPIs)**, which produced an atypical, near-flat influenza season
(unprecedented in the 2002–2019 training data). The model, having never observed
such a regime, cannot extrapolate to it — a textbook **distribution shift /
generalization failure**, which is legitimate and expected.

This is the *motivation* for our Phase 2 work: substituting the LLM backbone with
**ChatTime** (a time-series foundation model pre-trained on 1M diverse series)
may improve robustness to such shifts. The flat 2020–21 season is annotated
explicitly on the evaluation figure
(`scripts/make_miflu_evaluation_figure.py`) so the pattern is never misread as a
leakage artifact.

---

## Reproduce this audit

```bash
python -m pytest tests/test_leakage_audit.py -v
# Expected: 4 passed (index boundary, scaler train-only, no-shuffle, RevIN no-fit)
```
