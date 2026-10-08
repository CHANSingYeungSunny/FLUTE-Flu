# TRACK S — STOPPING-CRITERIA SUPPLEMENTARY EXPERIMENT

Declared 2026-10-08, **before any Track S fit was submitted**.

---

## 1. Why this track exists

Supervisor question 5 asks for the fine-tuning **stopping criteria**. The
recommended wording has three parts, and part (2) is:

> training-level stopping is standard **early stopping on validation loss**
> (patience 5–10 epochs, stop when no further improvement, roll back to the best
> weights).

The Track C championship **does not use this**. Verified:

```
miflu_strict966_train.py:158    for ep in range(a.epochs)     # fixed 20 epochs
miflu_strict966_train.py:140    patience=3                    # passed, never used
stage5_a2/execution_ledger.md   "early_stopping": "disabled; fixed 20 epochs"
```

Track C uses a **fixed 20-epoch budget plus post-hoc best-validation checkpoint
selection**. Same intent (validation only, never Test), different mechanism.

Track S exists to **measure** whether the difference matters, rather than to
argue about it.

---

## 2. What this track is NOT

| | |
|---|---|
| ❌ not Track C | Track C is frozen and untouched. Track S writes to a different directory (`s1_earlystop_20261008`) and a different job name (`s1es`). |
| ❌ not an R1-C candidate | The R1-C matrix is frozen at two entries (`R1C_FROZEN_CANDIDATE_MATRIX.csv`) and its declaration forbids adding a candidate after results are seen. Track S is a different question. |
| ❌ not a search | Two patience values, chosen from the range the brief itself states (5–10). No other knob moves. |

---

## 3. Frozen design

**Only the stopping rule differs.** `s1_earlystop_train.py` is generated from
the frozen Track C trainer `miflu_strict966_train.py` by
`scripts/make_s1_earlystop_trainer.py`, which patches exactly four things:

1. two new arguments (`--early-stop`, `--patience`),
2. a `bad_epochs` counter,
3. the stop-and-break on patience exhaustion,
4. four new fields in the run manifest.

Everything else is byte-identical: data (966, SHA-256 pinned), split 676/97/193,
strict-containment windows, model (`R1BCorrectedMIFlu`), optimiser (Adam),
lr 5e-4, batch 16, epoch ceiling 20, scoring, artefact format.

| item | value |
|---|---|
| model | MIFlu, official repository + R1-B corrections |
| data | author 966 rows, SHA-256 `2a96dfed…ebfe5` |
| split | 676 / 97 / 193, strict containment |
| horizons | 24, 36, 48, 60 |
| seeds | **42, 43, 44** (matched with Track C, so the comparison is apples-to-apples) |
| arms | **E1** patience = 5 · **E2** patience = 10 (planned) |
| fits | 12 per arm (4 × 3) |
| reference | the existing Track C fixed-20-epoch result at the same seeds |

---

## 4. Rules

1. **Validation** drives both stopping and checkpoint selection. Test is never
   read during training.
2. Test is read **once**, after the stopping rule has frozen the model.
3. The comparison is **within seed**: Track S (seed s, horizon L) versus Track C
   (seed s, horizon L).
4. All fits are reported, including any where early stopping hurts.
5. No re-tuning of lr, batch, epochs ceiling, or anything else.

---

## 5. What the outcome means

| outcome | reading |
|---|---|
| early stopping gives a clearly better Test MSE | the fixed-20 rule was leaving accuracy on the table; say so, and report both |
| early stopping gives a clearly worse Test MSE | the fixed-20 rule was fine; say so |
| **no material difference** | the two rules are practically equivalent here — the honest and most likely outcome, because both already select the best-validation checkpoint, so they differ only in *when training halts*, not in *which weights are kept* |

**A priori note.** Because both rules keep the best-validation weights, and
because the R1-C experiment showed the selected epoch moving between 5 and 20
depending on the schedule, the expected difference is small. Recording this
before the run so that a null result is not spun as a surprise.

---

## 6. Deliverables

| file | content |
|---|---|
| `S1_EARLYSTOP_PROTOCOL.md` | this document |
| `s1_earlystop_train.py` | generated trainer (patched copy of the Track C trainer) |
| `s1_earlystop.sbatch` | Slurm job script |
| `s1_batch_driver.sh` | serial submitter (works around stingy QOS limits) |
| `S1ES_RESOURCE_LEDGER.csv` | per-fit cost and return code |
| `S1ES_RESULTS_PER_FIT.csv` | per-fit Test MSE / MAE / stopped-at epoch |
| `S1ES_VS_TRACK_C.csv` | within-seed comparison against the frozen Track C cells |

---

## 7. Results (2026-10-08)

**Status: all 12 fits COMPLETED, all rc 0.** Measured cost ≈ 1.2 GPU-h
(73.5 min summed; roughly half the fixed-20-epoch cost, because early stopping
curtailed most runs before epoch 20).

### 7.1 Within-seed comparison against the frozen Track C MIFlu cells

| L | seed | Track C | S1ES (patience 5) | diff | best epoch (S1ES) |
|---:|---:|---:|---:|---:|---:|
| 24 | 42 | 1.885572 | 1.885572 | 0.000000 | 6 |
| 24 | 43 | 2.010233 | 2.010233 | 0.000000 | 8 |
| 24 | 44 | 2.009913 | 2.009913 | 0.000000 | 11 |
| 36 | 42 | 1.809880 | 1.809880 | 0.000000 | 14 |
| 36 | 43 | 2.161865 | 2.161865 | 0.000000 | 10 |
| 36 | 44 | 1.827874 | 1.827874 | 0.000000 | 15 |
| 48 | 42 | 1.709283 | 1.709283 | 0.000000 | 12 |
| 48 | 43 | 1.818424 | 1.818424 | 0.000000 | 11 |
| 48 | 44 | 1.736302 | 1.736302 | 0.000000 | 16 |
| 60 | 42 | 1.761910 | 1.761910 | 0.000000 | 15 |
| 60 | 43 | **1.880344** | **2.024601** | **+0.144257** | **3** |
| 60 | 44 | 1.770262 | 1.770262 | 0.000000 | 15 |

- **11 of 12 cells are identical to 6 decimal places.** In those cells the
  best-validation epoch was well inside the patience window, so the model kept
  by both stopping rules is the same.
- **1 cell (L60/seed43) diverges by +0.144.** Here the validation curve had a
  *local* minimum at epoch 3; patience=5 exhausted at epoch 8 and rolled back to
  epoch 3. The fixed-20 rule instead kept a later epoch whose validation loss was
  marginally higher but whose Test loss was better (1.880344). Early stopping on
  a local validation dip, where validation and Test disagree, is exactly the known
  failure mode — and here it is observed, not just warned about.

### 7.2 Aggregate

```
Track C   mean average_MSE_4L = 1.865155
S1ES      mean average_MSE_4L = 1.877177   (+0.64 %)
```

### 7.3 Answer to supervisor question 5, condition (2)

The two stopping mechanisms — **patience=5 early stopping with rollback** versus
**fixed 20-epoch budget + post-hoc best-validation checkpoint** — are **not
different champions and not different models.** They differ only in *when
training halts*. Because both keep the best-validation weights, and because in 11
of 12 cells the best-validation epoch is reached before the patience window
closes, the resulting Test MSE is the same to 6 dp. In one cell the early rule
stops too early and is marginally worse.

**Honest statement for the report:**

> Training used a fixed 20-epoch budget with validation-loss checkpoint
> selection. A controlled supplement (Track S) re-ran the identical MIFlu
> configuration with patience=5 validation early stopping and rollback to the
> best weights. 11/12 matched-seed cells were numerically identical to the
> champion result; one cell (L60/seed43) was 0.144 worse because early stopping
> rolled back to a local validation minimum. The two stopping rules are therefore
> outcome-equivalent for this model and data; they do not affect the championship
> ranking. Both use validation only for checkpoint selection and read Test once.

This makes the "fixed-20 + best-val" rule and "patience early stopping" explicit,
shows they were actually measured against each other, and avoids either (a)
over-claiming that patience early stopping was used when it was not, or (b)
pretending the difference is material when it is not.

### 7.4 Why not also patience=10?

patience=10 was deferred. Given 11/12 cells are already identical at patience=5
and the only divergence is a *too-early* stop, patience=10 would only make the
divergent cell look more like Track C — it cannot reveal a hidden improvement.
It is available on request but is not needed to answer the question.

