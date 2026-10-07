# PAPER GAP — REDUCTION CALCULATION

Generated 2026-10-07. All values recomputed from persisted prediction artefacts;
none are copied from a summary.

---

## 1. The paper target

| horizon | paper MSE | paper MAE |
|---|---:|---:|
| L24 | 1.542 | 0.726 |
| L36 | 1.422 | 0.779 |
| L48 | 1.414 | 0.757 |
| L60 | 1.364 | 0.719 |
| **average** | **1.4355** | **0.74525** |

## 2. The two author-966 MIFlu results

Both are author-966, strict containment, 7-variable z-space, one-time Test.

**They do NOT share a seed policy.** The old A2 figure is a **3-seed mean**
(42/43/44). The R1-B figure is a **single repetition** (seed `1000 + repetition
index`), for which **SD is `n/a`** — the R1-B pilot report states explicitly
"SD is `n/a`, not 0 — one repetition", and gate C15 caps the verdict at
`PARTIAL_REPRODUCTION` *because of* that single repetition.

They also differ in implementation and in text asset (declared deviation D2).

> **Correction note (2026-10-07).** An earlier version of this file stated that
> both sides used "seeds 42/43/44" and were comparable on "checkpoint policy".
> That was wrong: the R1-B side is one repetition, and the A2 checkpoint policy
> was never recorded. See `PAPER_GAP_COMPARABILITY_AUDIT.csv`.

### (a) Old — project self-built MIFlu (A2)

Recomputed from `pred_miflu_L{L}_s{seed}.npz` (12 artefacts):

| horizon | per-seed mean MSE |
|---|---:|
| L24 | 2.443924 |
| L36 | 1.936020 |
| L48 | 1.767731 |
| L60 | 2.018403 |
| **average_MSE_4L** | **2.041519** |

**Cross-check:** A2's own recorded figure was **2.042**. The recomputation
reproduces it, which validates the arithmetic used for both sides.

### (b) New — official-repository-based corrected MIFlu (R1-B)

`average_MSE_4L` = **1.9477** (four-horizon pilot report).

## 3. The calculation

> ⚠️ **The arithmetic in this section is ILLUSTRATIVE ONLY and is NOT a claim.**
> It divides a **3-seed mean** by a **single repetition**, so an unknown part of
> the difference is estimator variance rather than implementation quality. No
> SD exists on the R1-B side, so no interval can be placed on it.
> Do not quote these percentages as an improvement result. See §6.

```
paper                       = 1.4355

old absolute gap  = 2.041519 - 1.4355 = 0.606019
new absolute gap  = 1.9477   - 1.4355 = 0.512200

old relative gap  = 0.606019 / 1.4355 * 100 = 42.22 %
new relative gap  = 0.512200 / 1.4355 * 100 = 35.68 %

percentage-point reduction = 42.22 - 35.68 = 6.54 pp

relative reduction in gap = (0.606019 - 0.512200) / 0.606019 * 100 = 15.5 %
```

| quantity | value |
|---|---:|
| old relative error vs paper | **+42.22 %** |
| new relative error vs paper | **+35.68 %** |
| percentage-point reduction | **6.54 pp** |
| relative reduction of the gap | **15.5 %** |
| remaining gap | **35.68 %** |

## 4. What this does and does not mean

**It suggests, but does not establish,** that replacing the project's self-built
reconstruction with the official repository's corrected MIFlu moved the
author-966 result closer to the paper: the nominal gap goes from 42.2 % to
35.7 %, i.e. 15.5 % of the nominal original gap.

**This is an observation about two numbers, not a demonstrated improvement.**
The two numbers come from different repetition counts, so the difference is not
separable from estimator variance. See §6.

**It does not mean** the paper is reproduced. The result remains **35.7 % above**
the paper's four-horizon average MSE, and **zero of four horizons** entered the
predeclared ±0.10 MSE band. The paper-level verdict stays `PARTIAL_REPRODUCTION`.

**Three honest qualifications.**

1. **Different repetition counts (blocking).** Old = 3-seed mean (42/43/44);
   new = **1 repetition** with SD `n/a`. An unknown part of the 6.54 pp is
   noise. This is a comparability defect, not a footnote.
2. **This is not "the same model improved."** The two results are different
   implementations — a self-built reconstruction versus the author's
   architecture. The comparison measures which implementation sits closer to the
   paper, not a tuning gain within one model. The A2 checkpoint policy is
   additionally **unrecorded**, so the two sides may not even share a selection
   rule.
3. **The text asset differs too** (declared deviation D2: the project's prompt
   encoder versus the author's `text_emb_label_0507_<L>.txt`). So the nominal
   gap reduction is attributable to the *combined* change of implementation and
   text asset, not to the architecture alone. Separating the two would require a
   further controlled run and has not been done.

## 5. Wording used in the report

> The current evidence-based official-repository reconstruction remains
> approximately **35.7 %** above the paper's reported four-horizon average MSE.

**MSE is not accuracy.** "35.7 %" is a relative error in a squared-error metric
against a reported value. It is **not** a model accuracy percentage, and a
"35.7 % less accurate" reading would be wrong.

## 6. Comparability — verdict `NOT_SUFFICIENTLY_COMPARABLE`

Full per-criterion audit: `PAPER_GAP_COMPARABILITY_AUDIT.csv`.

### Comparable (8 criteria)

dataset (identical SHA-256) · split (676/97/193) · variables (7) · metric space
(z-space) · horizons (24/36/48/60) · pooling (`average_MSE_4L`) · window rule ·
strict origins (170/…/134).

### Not comparable (3 blocking criteria)

| criterion | old (A2) | new (R1-B) |
|---|---|---|
| seed policy | **3 seeds** 42/43/44 | **1 repetition**, seed `1000+rep` |
| checkpoint policy | **UNVERIFIED** (never recorded) | Validation-only (B-5) |
| uncertainty statement | SD available | **SD = `n/a`** |

Two further criteria differ *by design* (implementation, text asset) and are not
comparability defects — they are the variable the comparison exists to measure.

### Required statement

> **A numerical reduction percentage cannot be presented without qualification
> because the old and new runs used different contracts.**

### Why this is not a claim

1. **Estimator variance.** A one-repetition mean is a strictly noisier estimator
   than a 3-seed mean. With no SD on the R1-B side, the 6.54 pp "reduction"
   cannot be separated from noise.
2. **Unverified old selection rule.** The A2 checkpoint policy was never
   recorded. Because the *released* author code selects on Test, an unrecorded
   A2 rule cannot be assumed validation-only — and if the A2 side also selected
   on Test, both sides would carry a selection bias of unknown size.
3. **Confounded change.** Implementation and text asset changed together, so
   even a clean difference would not be attributable to the architecture alone.

### How to make it comparable

Re-run the official-repository corrected MIFlu with **matched seeds 42/43/44**
(3 repetitions) and a recorded validation-only checkpoint policy. That yields a
3-seed mean with an SD on both sides and removes blocking criteria 1 and 3.
This is included as a candidate in the bounded R1-C matrix
(`R1C_FROZEN_CANDIDATE_MATRIX.csv`), where it serves the paper-gap question —
it does **not** alter the frozen Track C championship.