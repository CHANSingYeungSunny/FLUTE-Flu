# R1-C — BOUNDED REPRODUCTION-GAP ANALYSIS

Generated 2026-10-08. **Final: all 24 fits complete (24/24, all rc 0).**
Track R only. **Does not touch Track C.**

> **Revision note.** An earlier version of this file reported seed-1000-only
> numbers (C0 1.9477 / C1 1.8029, gap 35.68 % → 25.59 %). Those are superseded
> by the three-seed means below. The single-seed estimate was materially wrong:
> seed 1000 turned out to be an unlucky seed for C0 (1.9477 versus a 3-seed mean
> of 1.8561). This is exactly the failure mode the comparability audit warned
> about, and it is why the frozen selection rule requires a three-seed mean.

---

## 1. Question and constraints

**Question.** Can evidence-supported unresolved settings bring the
official-repository MIFlu result to within **5 %** of the paper's reported
four-horizon average MSE, without Test-driven tuning or accuracy hunting?

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
| all candidates reported, including poor ones | ✅ |
| no unrestricted hyperparameter search | ✅ two candidates total |

---

## 2. The candidate matrix

Exactly **one** unresolved setting qualified (`R1C_DOCUMENTARY_EVIDENCE.md` §2):
the **learning-rate scheduler**. Everything else was either already matched
(optimizer, T, epochs, batch, lr, LoRA rank, LoRA targets, gpt_layers) or was a
declared repair of a released defect whose reversion would reintroduce the
defect, or had no documentary instantiation.

| id | change | evidence |
|---|---|---|
| `C0_r1b_constant_lr` | reference — constant 5e-4 | `r1b_train.py` |
| `C1_released_type1_scheduler` | `lr = 5e-4` for epoch < 3, else `5e-4 × 0.9^(epoch-3)` | `utils/tools.py:26-27` |

---

## 3. Results — three-seed means (24/24 fits, all rc 0)

### 3.1 Per horizon

| L | paper MSE | C0 MSE | C0 SD | C1 MSE | C1 SD | C0 MAE | C1 MAE | C0 rel | C1 rel |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 | 1.542 | 2.0460 | 0.0911 | **2.0588** | 0.0410 | 0.9167 | 0.9203 | +32.7 % | **+33.5 %** |
| 36 | 1.422 | 1.9036 | 0.1043 | **1.8154** | 0.0630 | 0.9178 | 0.8693 | +33.9 % | **+27.7 %** |
| 48 | 1.414 | 1.7339 | 0.0948 | **1.7166** | 0.0701 | 0.8635 | 0.8751 | +22.6 % | **+21.4 %** |
| 60 | 1.364 | 1.7408 | 0.0807 | **1.6991** | 0.0065 | 0.8804 | 0.8704 | +27.6 % | **+24.6 %** |
| **mean** | **1.4355** | **1.8561** | 0.0878 | **1.8225** | 0.0405 | 0.8946 | 0.8838 | **+29.30 %** | **+26.96 %** |

**C1 is better on three of four horizons and worse on L=24.** It also has
roughly half the seed-to-seed spread (SD 0.0405 versus 0.0878).

Per-seed four-horizon means:

| seed | C0 | C1 |
|---|---:|---:|
| 1000 | 1.9477 | 1.8029 |
| 1001 | 1.8478 | 1.8691 |
| 1002 | 1.7727 | 1.7954 |

Note the overlap: C0's best seed (1.7727) beats C1's worst seed (1.8691).

### 3.2 Is the improvement real?

```
C0 mean = 1.8561   sd = 0.0878   (n = 3 seeds)
C1 mean = 1.8225   sd = 0.0405   (n = 3 seeds)
difference = 0.0336
Welch t = 0.602   df = 2.8
```

|t| = 0.602 is far below any conventional threshold. **The C1 − C0 improvement
is not distinguishable from seed noise at three seeds.** The honest reading is
that C1 is *not worse* and is more stable, not that C1 is *demonstrably better*.

---

## 4. Paper-gap arithmetic

```
paper target (four-horizon average MSE) = 1.4355

C0 absolute gap = 1.8561 - 1.4355 = 0.4206     relative = 0.4206/1.4355 x 100 = 29.30 %
C1 absolute gap = 1.8225 - 1.4355 = 0.3870     relative = 0.3870/1.4355 x 100 = 26.96 %

improvement C1 over C0 (absolute) = 1.8561 - 1.8225 = 0.0336
improvement C1 over C0 (relative) = 0.0336 / 1.8561 x 100 = 1.81 %
share of the original gap removed  = 0.0336 / 0.4206 x 100 = 7.99 %
distance still remaining to 5 %    = 26.96 - 5.00 = 21.96 percentage points
```

| quantity | C0 | C1 |
|---|---:|---:|
| mean `average_MSE_4L` (3 seeds) | 1.8561 | **1.8225** |
| SD across seeds | 0.0878 | **0.0405** |
| relative error vs paper | +29.30 % | **+26.96 %** |
| horizons inside ±0.10 MSE | 0 / 4 | **0 / 4** |
| horizons inside ±0.05 MAE | 0 / 4 | **0 / 4** |
| verdict | `REFERENCE / NO_EVIDENCE_SUPPORTED_IMPROVEMENT` | `IMPROVED_BUT_ABOVE_5_PERCENT` |

**MSE is not accuracy.** These are relative errors in a squared-error metric
against a reported value, not accuracy percentages.

> **Note on the verdict scale.** `R1C_SELECTION_RULE.md` §4 sets the boundary
> `NO_EVIDENCE_SUPPORTED_IMPROVEMENT if relative error >= 35.68 %`, which was
> written against the single-seed reference. Now that the reference is a
> three-seed mean at 29.30 %, C0 is labelled `REFERENCE / NO_EVIDENCE_SUPPORTED_
> IMPROVEMENT` **by definition** — it is the baseline against which improvement
> is measured, not a candidate that attempted a change. C1 is judged against it.

---

## 5. Why the improvement is bounded

The mechanism was predicted before execution (`R1C_DOCUMENTARY_EVIDENCE.md` §4)
and partly confirmed: decaying the learning rate lets late epochs become
competitive, so the selected epoch moves later (C1 reaches epoch 17–20 at L=60
versus epoch 11–12 for C0). But that only reshuffles which epoch is picked; it
does not change what the released evaluation contract can produce.

The two settings with the largest plausible leverage — Test-based checkpoint
selection and single-channel evaluation — are released **defects**. Reverting
them would make the number smaller and simultaneously make it meaningless, and
would require reading Test during selection, which the brief forbids. They were
excluded **by evidence, not by preference**.

**Four of eight paper/code conflicts are permanently unresolvable from the
released artifacts** (`R1_PAPER_CODE_CONFLICTS.md` §Summary), and whether
Table V's own MIFlu column was produced by this code at all is unstated.

---

## 6. Effect on the championship

**None.** Track C is frozen. R1-C is a different question on a different
contract (seeds 1000–1002 versus 42/43/44).

For the record: Track C MIFlu = **1.8652**, R1-C C1 = **1.8225**, R1-C C0 =
**1.8561**. C0 sits within one SD of the Track C champion, which is a useful
consistency check — same configuration, different seeds, nearly the same answer.
**Neither R1-C number is a challenger to the championship.**

---

## 7. Cost

| item | value |
|---|---|
| R1-C fits executed | 24 / 24, all rc 0 |
| measured cost per fit | ≈ 0.12 GPU-h |
| total | ≈ 2.9 GPU-h |
| partition | `stingy`, 1 × A100 per job |
| login-node computation | none |
