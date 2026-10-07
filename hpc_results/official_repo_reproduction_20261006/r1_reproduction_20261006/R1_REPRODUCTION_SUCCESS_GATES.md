# R1 — REPRODUCTION SUCCESS GATES

Generated 2026-10-06. **Predeclared.** No tolerance below may be adjusted after seeing a
result.

---

## 1. The verdict scale

| Verdict | Definition |
|---|---|
| `EXACT_OR_NEAR_REPRODUCTION` | same contract; all major settings recovered; differences within the predeclared tolerance |
| `PARTIAL_REPRODUCTION` | same qualitative setup; some settings reconstructed; results directionally similar but outside tolerance |
| `EXECUTABLE_BUT_NOT_REPRODUCED` | the repository runs; the contract or the values do not match |
| `NOT_REPRODUCIBLE_FROM_RELEASED_ARTIFACTS` | essential information or a functional implementation is missing, and a reasonable evidence-based reconstruction cannot reproduce the results |

---

## 2. Predeclared numerical tolerance

| Metric | Tolerance | Basis |
|---|---|---|
| per-horizon MSE | **± 0.10 absolute** on the paper value | one order of magnitude below the smallest real inter-model gap in Table V (PatchTST 1.319 vs GPT4TS 2.063 at L=24 is 0.744; MIFlu vs GPT4TS at L=48 is 0.376). A 0.10 band is tight enough to be meaningful and wide enough to survive hardware/seed variation. |
| per-horizon MAE | **± 0.05 absolute** | same reasoning, scaled to the MAE column |
| four-horizon mean MSE | **± 0.08 absolute** | tighter than the per-horizon band because averaging four horizons cancels independent errors |

**Tolerance is fixed before execution and is not tuned.** If a horizon lands at 1.60
against a paper value of 1.542, that is +0.058 — inside the band. If it lands at 1.92, it is
+0.378 — outside.

### The band is necessary but not sufficient

`EXACT_OR_NEAR_REPRODUCTION` requires **both**:
1. all four horizons inside the tolerance, **and**
2. the contract items recovered (see §3).

**A single horizon inside the band is not success.** The brief forbids that explicitly.

---

## 3. Contract gates — all must pass for `EXACT_OR_NEAR`

| # | Gate | How it is verified |
|---|---|---|
| C1 | dataset is the author 966-row file, SHA-256 pinned | checked at job start; exit 4 on mismatch |
| C2 | split is 676 / 97 / 193, chronological | asserted by the trainer |
| C3 | scaler fitted on train rows only | asserted |
| C4 | **seven** channels evaluated | prediction arrays are `(n_origins, 7, L)` |
| C5 | identical forecast origins across horizons, matching the containment rule | window manifest |
| C6 | **the text pathway is functional** | text-path probe on each checkpoint returns `text_active` |
| C7 | LoRA actually applied | trainable parameter count printed and non-trivial but ≪ total |
| C8 | the freeze is effective | trainable count ≪ total (this is the diagnostic that also validates the budget) |
| C9 | checkpoint selection is validation-only | provenance record; no Test quantity computed during the fit |
| C10 | Test evaluated once | `DEFER_TEST`-style gate |
| C11 | predictions **and** targets persisted | artefacts exist and are re-scorable |
| C12 | **independent scoring** reproduces the reported numbers | `scorer_f1.py` arithmetic, not the training code's metric path |
| C13 | no Historical Track B artefact used | enforced rejection |
| C14 | every deviation from released behaviour is declared | the B-1…B-7 ledger |
| C15 | **the repetition count is stated honestly** | one repetition ⇒ **no verdict better than `PARTIAL_REPRODUCTION`**, regardless of the numbers |

**C15 is the gate most likely to be violated by accident.** The paper reports ten
repetitions; a one-repetition pilot cannot satisfy item 6 of the brief.

---

## 4. Pilot gate report (what the pilot must produce)

| Field | Per horizon |
|---|---|
| paper value (MSE and MAE) | from `R1_PAPER_TARGET_VALUES.csv` |
| reproduced mean | from the independent scorer |
| reproduced SD | `n/a` at one repetition — must be stated as `n/a`, not as 0 |
| absolute difference | computed |
| relative difference | computed |
| repetition count | **1** |
| exact contract | the declared R1-B contract |
| inside the predeclared tolerance? | yes/no per horizon |
| contract gates C1–C15 | pass/fail each |

---

## 5. Decision rule after the pilot

```
if all C1..C14 pass and all four horizons are inside the tolerance:
        pilot verdict = PARTIAL_REPRODUCTION   (cannot be better at 1 repetition)
        decision      = expand to 10 repetitions, then re-judge for EXACT_OR_NEAR
elif all C1..C14 pass and horizons are outside the tolerance:
        pilot verdict = EXECUTABLE_BUT_NOT_REPRODUCED
        decision      = do NOT expand; consider R1-C sensitivity (declared), or report the block
elif C6 or C7 or C8 fails:
        pilot verdict = the restoration is not working
        decision      = fix the reconstruction; do NOT spend T2
elif C4 or C11 or C12 fails:
        pilot verdict = the measurement is invalid
        decision      = fix before any expansion
```

**A failed pilot is reported as a failed pilot.** It is not re-run with different settings
to obtain a better number.

---

## 6. What the verdict will and will not mean

| Will mean | Will not mean |
|---|---|
| whether a **declared reconstruction** on the author's code lands near the paper | that the paper's own experiment has been reproduced |
| whether the restored mechanism (text, LoRA, freeze, seven channels) is what moves the numbers | that the authors used this configuration |
| how far the released code is from the paper, with a measured distance | that the paper's pooled quantity is the same as ours (**Q12 is `UNRECOVERED`**) |

**Because Q12 (pooling axes) and A6 (Table V column provenance) are permanently
unrecoverable, `EXACT_OR_NEAR_REPRODUCTION` here can only ever mean "near, under a
reconstructed contract of the same kind, with the ambiguity disclosed".** It must never be
shortened to "we reproduced the paper".

---

## 7. Prohibited

| Prohibited | Why |
|---|---|
| tuning epochs, lr or any setting toward 1.4355 | accuracy hunting |
| widening the tolerance after seeing the result | predeclaration violated |
| reporting the best horizon only | the brief forbids one-horizon success claims |
| reporting one repetition as a paper-level result | C15 |
| calling R1-A, A0-R or F1 a reproduction | all three are something else |
| re-labelling a `PARTIAL_REPRODUCTION` as `EXACT_OR_NEAR` because one horizon matched | C15 + §2 |