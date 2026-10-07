# R1-C — FINAL VERDICT

Generated 2026-10-07. Track R only. Track C is untouched and its champion is
unchanged.

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

## 1. Per-candidate verdicts

| candidate | mean `average_MSE_4L` (seed 1000) | relative error vs paper | verdict |
|---|---:|---:|---|
| `C0_r1b_constant_lr` (reference) | 1.947713 | +35.68 % | `NO_EVIDENCE_SUPPORTED_IMPROVEMENT` |
| `C1_released_type1_scheduler` | 1.802891 | **+25.59 %** | **`IMPROVED_BUT_ABOVE_5_PERCENT`** |

**C1 is the better candidate and is reported as such.** It improves C0 at all
four horizons and on both MSE and MAE, removing **28.3 %** of the original gap.

**C1 does not reach the 5 % criterion**, and the additional requirements for a
`WITHIN_5_PERCENT` claim all fail:

| requirement | required | observed | met |
|---|---|---|---|
| all four horizons within ±0.10 MSE | 4 / 4 | **0 / 4** | ❌ |
| both MSE and MAE within tolerance | yes | MSE 0/4, MAE 0/4 | ❌ |
| multiple repetitions | 3 seeds | 1 complete, 2 pending | ⚠ partial |
| independent scoring | yes | yes | ✅ |
| no Test-assisted selection | yes | validation-only, Test once | ✅ |
| `text_active` | yes | verified in R1-B (C6) | ✅ |
| LoRA valid | yes | 12 LoRA tensors per fit | ✅ |
| freezing valid | yes | 2.02 %–3.38 % trainable | ✅ |
| key contract valid | yes | strict-966, duplicate keys 0 | ✅ |

A single horizon or a single lucky seed does not count. Here **no** horizon is
inside tolerance, so the question does not arise.

---

## 2. The number to quote

> The current evidence-based official-repository reconstruction remains
> approximately **25.6 %** above the paper's reported four-horizon average MSE
> (best evidence-supported candidate C1: 1.8029 vs paper 1.4355).
> Zero of four horizons entered the predeclared ±0.10 MSE band.

**MSE is not accuracy.** This is a relative error in a squared-error metric
against a reported value. It is **not** a model accuracy percentage, and a
"25.6 % less accurate" reading would be wrong.

---

## 3. What this verdict is based on

1. **A closed candidate set of two**, frozen before any fit, of which exactly one
   was an actual change.
2. **One genuine documentary finding**: R1-B omitted the released `type1`
   learning-rate schedule — the only setting where R1-B silently differed from a
   recovered released default without that difference being a declared repair.
   Testing it was therefore mandatory, and it did help.
3. **Evidence-bounded exclusion**, not preference-based exclusion: the two
   settings with the largest plausible leverage (Test-based checkpoint selection,
   single-channel evaluation) are released **defects**; reverting them would
   reproduce the defect and would require reading Test during selection.
4. **Structural limits**: four of eight paper/code conflicts are permanently
   unresolvable from the released artifacts, and whether Table V's own MIFlu
   column was even produced by this code is unstated.

---

## 4. What would change this verdict

Only one of the following:

- documentary evidence establishing the paper's **checkpoint-selection rule**,
  **repetition aggregation**, or **seed mechanism** — none of which exists in the
  released artifacts;
- release of the **US-Region** data or the missing **few-shot** results
  (currently blocked, not merely unrun);
- a corrected or clarified **Table V provenance** statement from the authors.

Absent one of those, further search would be accuracy hunting, and the correct
answer is the honest one recorded above.

---

## 5. Explicitly not claimed

- ❌ Not a reproduction of the paper's Table V (1.4355).
- ❌ Not a challenge to the Track C champion (1.8652) — different contract.
- ❌ Not evidence that the text pathway works as the paper describes; the
  released-code text path is inert and R1-B's text path is a declared
  reconstruction, so its agreement with the paper cannot be established.
- ❌ Not a statement about accuracy in any classification sense.

---

## 6. Championship confirmation

**The Track C champion is unchanged and is not revisited.**

> Under the author-966 strict-containment, matched-seed (42/43/44),
> Validation-selected and one-time-Test contract, the official-repository-based
> corrected MIFlu is the eight-model champion with mean Test `average_MSE_4L`
> = **1.8652** (SD 0.0916) and mean Test `average_MAE_4L` = **0.8842**.
