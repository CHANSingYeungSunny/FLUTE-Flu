# R1-C — FINAL VERDICT

Generated 2026-10-08. **All 24 fits complete, all rc 0.**
Track R only. Track C is untouched and its champion is unchanged.

---

## FINAL VERDICT

```
NOT_REPRODUCIBLE_WITHIN_5_PERCENT_FROM_RELEASED_ARTIFACTS
```

The paper-level reproduction verdict remains:

```
PARTIAL_REPRODUCTION
```

---

## 1. Per-candidate verdicts (three-seed means)

| candidate | mean `average_MSE_4L` | SD | relative error vs paper | verdict |
|---|---:|---:|---:|---|
| `C0_r1b_constant_lr` (reference) | 1.8561 | 0.0878 | +29.30 % | `REFERENCE / NO_EVIDENCE_SUPPORTED_IMPROVEMENT` |
| `C1_released_type1_scheduler` | **1.8225** | **0.0405** | **+26.96 %** | **`IMPROVED_BUT_ABOVE_5_PERCENT`** |

**C1 is reported as the better candidate, with an explicit caveat:** the
difference (0.0336) gives Welch t = 0.602 at df = 2.8, so it is **not
distinguishable from seed noise at three seeds**. C1 is not worse, and it is
more stable (half the spread), but "demonstrably better" is not a claim this
experiment supports.

**C1 does not reach the 5 % criterion.** Additional requirements for a
`WITHIN_5_PERCENT` claim:

| requirement | required | observed | met |
|---|---|---|---|
| all four horizons within ±0.10 MSE | 4 / 4 | **0 / 4** | ❌ |
| both MSE and MAE within tolerance | yes | MSE 0/4, MAE 0/4 | ❌ |
| multiple repetitions | 3 seeds | 3 ✅ | ✅ |
| independent scoring | yes | yes | ✅ |
| no Test-assisted selection | yes | validation-only, Test once | ✅ |
| `text_active` | yes | verified in R1-B (C6) | ✅ |
| LoRA valid | yes | 12 LoRA tensors per fit | ✅ |
| freezing valid | yes | 2.02 %–3.38 % trainable | ✅ |
| key contract valid | yes | strict-966, duplicate keys 0 | ✅ |

**Zero of four horizons** is inside tolerance, so the question of a single lucky
horizon or seed does not even arise.

---

## 2. The number to quote

> The current evidence-based official-repository reconstruction remains
> approximately **27 %** above the paper's reported four-horizon average MSE
> (best evidence-supported candidate C1: 1.8225 versus paper 1.4355, three
> seeds). **Zero of four horizons** entered the predeclared ±0.10 MSE band, and
> the improvement over the reference is within seed noise.

**MSE is not accuracy.** This is a relative error in a squared-error metric
against a reported value. It is **not** a model accuracy percentage, and a
"27 % less accurate" reading would be wrong.

---

## 3. What changed from the provisional (seed-1000) verdict

| | provisional | final |
|---|---:|---:|
| C0 | 1.9477 (+35.68 %) | **1.8561 (+29.30 %)** |
| C1 | 1.8029 (+25.59 %) | **1.8225 (+26.96 %)** |
| gap closed | 28.3 % | **8.0 %** |

Seed 1000 was unlucky for C0. **The provisional verdict understated C0 by about
6 percentage points and overstated the benefit of C1 by a factor of ~3.5.** This
is recorded rather than quietly corrected, because it is the empirical
demonstration of why the frozen rule requires multiple repetitions.

---

## 4. What this verdict is based on

1. **A closed candidate set of two**, frozen before any fit, of which one was a
   real change.
2. **One genuine documentary finding**: R1-B omitted the released `type1`
   learning-rate schedule — the only setting where R1-B silently differed from a
   recovered released default without that difference being a declared repair.
3. **Evidence-bounded exclusion**: the two settings with the largest plausible
   leverage (Test-based checkpoint selection, single-channel evaluation) are
   released defects; reverting them would reproduce the defect and would require
   reading Test during selection.
4. **Structural limits**: four of eight paper/code conflicts are permanently
   unresolvable from the released artifacts, and whether Table V's own MIFlu
   column was even produced by this code is unstated.

---

## 5. What would change this verdict

Only one of:

- documentary evidence establishing the paper's **checkpoint-selection rule**,
  **repetition aggregation**, or **seed mechanism** — none exists in the
  released artifacts;
- release of the **US-Region** data or the missing **few-shot** results;
- a clarified **Table V provenance** statement from the authors.

Absent one of those, further search would be accuracy hunting.

---

## 6. Explicitly not claimed

- ❌ Not a reproduction of the paper's Table V (1.4355).
- ❌ Not a challenge to the Track C champion (1.8652) — different contract.
- ❌ Not evidence that C1 is significantly better than C0 (t = 0.602).
- ❌ Not evidence that the text pathway works as the paper describes; the
  released text path is inert and R1-B's text path is a declared reconstruction.
- ❌ Not a statement about accuracy in any classification sense.

---

## 7. Championship confirmation

**The Track C champion is unchanged and is not revisited.**

> Under the author-966 strict-containment, matched-seed (42/43/44),
> Validation-selected and one-time-Test contract, the official-repository-based
> corrected MIFlu is the eight-model champion with mean Test `average_MSE_4L`
> = **1.8652** (SD 0.0916) and mean Test `average_MAE_4L` = **0.8842**.

**Separately**, under the peak-acceptance criteria of supervisor question 5
(PTE ≤ 1 week and PIE ≤ 25 %, Kramer & Shaman 2019, judged per peak), the
ordering is different: **NLinear 36/36 (100 %)**, DLinear 31/36, MIFlu 15/36
(41.7 %). See `results/v3_clean/analysis/peak_criteria/PTE_PIE_TRACK_C_REPORT.md`.
MSE ranking and peak acceptance are **two different questions** and are reported
separately; neither replaces the other.
