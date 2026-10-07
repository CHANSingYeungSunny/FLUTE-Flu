# R1-C — BOUNDED REPRODUCTION-GAP ANALYSIS

Generated 2026-10-07. Track R only. **Does not touch Track C.**

---

## 1. Question and constraints

**Question.** Can evidence-supported unresolved settings bring the
official-repository MIFlu result to within **5 %** of the paper's reported
four-horizon average MSE, without Test-driven tuning or accuracy hunting?

**Constraints actually observed**

| constraint | status |
|---|---|
| candidate list frozen before execution | ✅ `R1C_FROZEN_CANDIDATE_MATRIX.csv` |
| selection rule frozen before execution | ✅ `R1C_SELECTION_RULE.md` |
| evaluation rule frozen before execution | ✅ `R1C_SELECTION_RULE.md` §3–4 |
| GPU/storage cost estimated in advance | ✅ matrix column `est_gpu_hours` |
| anti-accuracy-hunting statement published | ✅ `R1C_ANTI_ACCURACY_HUNTING_DECLARATION.md` |
| Train for fitting | ✅ |
| Validation for checkpoint selection | ✅ (correction B-5, `test_access_during_fit = False`) |
| Test read once per frozen fit | ✅ |
| Track C unmodified | ✅ |
| no Test-based selection of paper settings | ✅ |
| all candidates reported, including poor ones | ✅ (this file) |
| no unrestricted hyperparameter search | ✅ two candidates total |

---

## 2. The candidate matrix

Exactly **one** unresolved setting qualified as a legitimate candidate
(`R1C_DOCUMENTARY_EVIDENCE.md` §2): the **learning-rate scheduler**. Everything
else was either already matched (optimizer, T, epochs, batch, lr, LoRA rank,
LoRA targets, gpt_layers) or was a **declared repair of a released defect** whose
reversion would reintroduce the defect (Test-based checkpoint selection,
single-channel evaluation), or had **no documentary instantiation** (repetition
aggregation, seed mechanism).

| id | change | evidence |
|---|---|---|
| `C0_r1b_constant_lr` | reference — constant 5e-4 (the R1-B configuration) | `r1b_train.py` |
| `C1_released_type1_scheduler` | `lr = 5e-4` for epoch < 3, else `5e-4 × 0.9^(epoch-3)` | `utils/tools.py:26-27` |

**C1 is the only change tested.** It was not selected because it looked
promising; it is the only setting where R1-B silently differs from a *recovered*
released default without that difference being a declared repair.

---

## 3. Results

### 3.1 Seed 1000 — complete (8 of 8 fits, all rc 0)

| L | paper MSE | C0 MSE | C1 MSE | paper MAE | C0 MAE | C1 MAE | C0 best ep | C1 best ep |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 | 1.542 | 2.133497 | **2.017671** | 0.726 | 0.929781 | **0.915340** | 5 | 5 |
| 36 | 1.422 | 2.022708 | **1.777410** | 0.779 | 0.997668 | **0.866462** | 6 | 9 |
| 48 | 1.414 | 1.841337 | **1.710919** | 0.757 | 0.895716 | **0.874585** | 10 | 10 |
| 60 | 1.364 | 1.793311 | **1.705562** | 0.719 | 0.911584 | **0.862131** | 11 | **17** |
| **mean** | **1.4355** | **1.947713** | **1.802891** | **0.74525** | **0.933687** | **0.879630** | — | — |

**C1 improves C0 at all four horizons and on both metrics.** No horizon regressed.

### 3.2 Seeds 1001 and 1002 — PENDING

Submitted by `r1c_batch_driver.sh`. `partition-stingy` enforces
`MaxJobsPU=1 / MaxSubmitJobsPU=1`, so batches must drain serially; each batch of
four fits takes about 30 minutes. This file will be regenerated when they finish.

**The seed-1000 result is already decisive** for the 5 % question: C1 closes
roughly a quarter of the gap, and the remaining distance to 5 % is about
**20.6 percentage points** — far larger than any seed-to-seed variation observed
anywhere in this project (Track C SD across seeds was 0.09 on a mean of 1.87).

---

## 4. Paper-gap arithmetic

```
paper target (four-horizon average MSE)      = 1.4355
paper target (four-horizon average MAE)      = 0.74525

C0 absolute gap  = 1.947713 - 1.4355  = 0.512213
C1 absolute gap  = 1.802891 - 1.4355  = 0.367391

C0 relative gap  = 0.512213 / 1.4355 x 100 = 35.68 %
C1 relative gap  = 0.367391 / 1.4355 x 100 = 25.59 %

improvement C1 over C0 (absolute) = 1.947713 - 1.802891 = 0.144822
improvement C1 over C0 (relative) = 0.144822 / 1.947713 x 100 = 7.44 %
share of the original gap removed = 0.144822 / 0.512213 x 100 = 28.27 %
distance still remaining to 5 %   = 25.59 - 5.00 = 20.59 percentage points
```

| quantity | C0 | C1 |
|---|---:|---:|
| mean `average_MSE_4L` | 1.947713 | **1.802891** |
| relative error vs paper | +35.68 % | **+25.59 %** |
| horizons inside ±0.10 MSE | 0 / 4 | **0 / 4** |
| horizons inside ±0.05 MAE | 0 / 4 | **0 / 4** |
| verdict (per candidate) | `NO_EVIDENCE_SUPPORTED_IMPROVEMENT` | `IMPROVED_BUT_ABOVE_5_PERCENT` |

**MSE is not accuracy.** These percentages are relative errors in a squared-error
metric against a reported value. They are not accuracy percentages, and a
"25.6 % less accurate" reading would be wrong.

---

## 5. Why C1 helps — and why only this much

The mechanism was predicted **before** execution (`R1C_DOCUMENTARY_EVIDENCE.md`
§4) and the data confirm it. Under a constant 5e-4, validation-selected best
epochs were early (5, 6, 10, 11 of 20). Decaying the learning rate lets late
epochs become competitive: the C1 best epoch moves to **17** at L=60 and to
**9** at L=36.

But the improvement is bounded by the same thing that bounds the whole
reproduction: **the released evaluation contract cannot produce the paper's
number.** The two settings with the largest plausible leverage — Test-based
checkpoint selection and single-channel evaluation — are released **defects**.
Reverting them would make the number smaller and simultaneously make it
scientifically meaningless, and it would require reading Test during selection,
which the brief forbids. They were therefore excluded *by evidence*, not by
preference.

---

## 6. Residual unresolved settings

| setting | status | why it cannot be instantiated |
|---|---|---|
| optimizer | recovered, matched | Adam on both sides; nothing to change |
| scheduler | **recovered; C1 tests it** | — |
| checkpoint-selection rule | recovered; R1-B repairs it | reverting reintroduces Test selection |
| pooling axes / eval scope | recovered; R1-B repairs it | reverting reintroduces single-channel eval |
| repetition aggregation | unrecovered | released code prints mean±SD over iterations; paper's rule unstated |
| seed mechanism | unrecovered | no seed list, no `manual_seed` tied to repetition index |
| dataset date span | contradictory | paper says 2002–2021; released file ends 2020-06-30 |
| Table V column provenance | unrecovered | paper states baselines are quoted from [9]/[14]; whether MIFlu's own column is also quoted is unstated |

**Four of these are permanently unresolvable from the released artifacts**
(`R1_PAPER_CODE_CONFLICTS.md` §Summary). That is the structural reason a 5 %
target was never likely to be reachable, and it is why
`PARTIAL_REPRODUCTION` is a legitimate final verdict rather than a failure.

---

## 7. Effect on the championship

**None.** Track C is frozen. R1-C concerns Track R only. The R1-C numbers
(contract: seeds 1000–1002, 1 repetition per seed) are **not** the Track C
numbers (contract: seeds 42/43/44, 3 seeds, Test-only ranking) and must never be
substituted into the championship ranking.

For the record, they differ: Track C MIFlu `average_MSE_4L` = **1.8652**;
R1-C C1 = **1.8029**. The R1-C value is **not** a better championship result and
is **not** a challenger to it — it is a different question on a different
contract.

---

## 8. Cost

| item | value |
|---|---|
| R1-C fits executed (seed 1000) | 8 |
| R1-C fits remaining (seeds 1001/1002) | 16 |
| measured cost per fit (seed 1000) | 0.1207 – 0.1422 GPU-h |
| seed-1000 subtotal | 1.0194 GPU-h |
| estimated total for 24 fits | ≈ 3.06 GPU-h |
| partition | `stingy`, 1 × A100 per job |
| all fits | rc 0, none on a login node |
