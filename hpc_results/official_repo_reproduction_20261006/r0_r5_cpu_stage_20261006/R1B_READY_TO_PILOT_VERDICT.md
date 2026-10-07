# R1-B READY-TO-PILOT VERDICT

Generated 2026-10-06.

# Verdict: `NOT_READY_CONTRACT_UNRESOLVED`

**Not an engineering failure.** The R1-B implementation exists and 27 of 30 acceptance
tests pass, including every test that can be run without a GPU. The blocker is that
**three contract items remain unresolved**, and two engineering gates can only be
exercised on the HPC.

---

## 1. What is done

| Item | Status |
|---|---|
| R1-B trainer **exists** | ✅ `r1b/r1b_train.py` (built on the author's code, which is unmodified) |
| R1-B corrected model **exists** | ✅ `r1b/r1b_model.py` — subclasses `models.GPT4TS_lora.GPT4TS` |
| seven-channel windows (B-1) | ✅ verified: output `(2, 24, 7)` |
| **functional text pathway (B-2)** | ✅ verified: `max\|Δ\|` **0.0 → 5.88e-02**, `\|grad_text\|` **0 → 1.04e-03**, verdict **`text_inert` → `text_active`** |
| **effective freeze (B-4)** | ✅ verified: trainable **100 % → 1.93 %** (1,599,768 / 82,705,944) |
| validation-only selection (B-5) | ✅ implemented; Test unused until after selection |
| persisted predictions (B-6) | ✅ NPZ schema matches the audited scorer |
| paper-explicit configuration (B-7) | ✅ epochs 20 / lr 5e-4 / batch 16, **`PAPER_EXPLICIT` via Table IV** |
| author tree untouched | ✅ `git diff --stat` = 9 files, 0 insertions, 0 deletions |
| acceptance tests | **27 PASS / 3 NOT_YET_RUN / 0 FAIL** |

---

## 2. Why not `READY_TO_PILOT`

### 2.1 Engineering gates that can only run on the HPC (2)

| Gate | Why it cannot run locally |
|---|---|
| T19 LoRA modules exist | `peft` is not installed in the local interpreter. The HPC env has peft 0.17.1 and the author's branch was verified to work there earlier (job 606365 ran `PEFT=1` successfully). |
| T20 LoRA parameters trainable | same |
| T29 checkpoint reload reproduces predictions | needs a fitted checkpoint |

These are **expected** to pass — the author's PEFT=1 path already ran successfully in an
earlier round — but they are **not yet verified for the R1-B subclass**, and the brief
requires mandatory engineering gates to pass before submission.

### 2.2 Contract items still unresolved (the real blocker)

| # | Item | Status | Why it blocks |
|---|---|---|---|
| **C1** | **pooling axes** | `UNRECOVERED` | the paper states no pooling rule; without it the reproduced scalar cannot be proven to be the same quantity as Table V's |
| **C2** | **checkpoint-selection rule** | `UNRECOVERED` | R1-B uses validation-only as a **declared repair**; the paper's rule is unknown |
| **C3** | **optimizer and scheduler** | `UNRECOVERED` | Table IV gives epochs/lr/batch/T but **no optimizer**; the released default is Adam with a hard-coded 0.9 decay from epoch 4 |

C1 and C2 are **not blockers to running** — they are blockers to *claiming* what a result
means. The brief allows a pilot whose verdict is `PILOT_INVALID_CONTRACT`; but it also
requires the Tier-1 contract to be "sufficiently defined" first, and C1 in particular is
unresolvable by any amount of work.

**Recommendation**: treat C1 as a **permanent disclosed limitation** rather than a
blocker, adopt the paper-explicit items from Table IV, declare B-2/B-5 as deviations, and
re-issue the verdict as `READY_TO_PILOT` **once T19/T20/T29 are exercised on the HPC by a
CPU-only job** — which needs no GPU authorization.

---

## 3. The two paths forward

| Path | Action | Needs GPU? |
|---|---|---|
| **A (recommended)** | run a **CPU-only HPC job** that imports the R1-B subclass with `PEFT=1` and reports the LoRA tensor count, the trainable count, and a checkpoint reload round-trip. Then re-issue this verdict. | **no** |
| B | accept the local evidence and submit the pilot | requires the reproduction GPU authorization, which is **not granted** |

---

## 4. What a pilot verdict could then be

Even with everything passing, **a one-repetition pilot cannot exceed
`PARTIAL_REPRODUCTION`** and must be reported with:

- the Table IV configuration as `PAPER_EXPLICIT`;
- B-2 and B-5 as **declared deviations**;
- C1 (pooling axes) as a **permanent limitation** — so "near" can only ever mean "near
  under a reconstructed contract of the same kind";
- the **MIFlu column only** as the reproduction target: the paper states its other eleven
  Table V columns are taken from refs [9] and [14], so they are `CITED_BASELINE_RESULT`
  and reproducing them is `NOT_APPLICABLE`.

---

## 5. Gates the pilot must still satisfy before submission

1. T19, T20, T29 exercised (CPU-only HPC job).
2. A **new reproduction-specific GPU authorization** — the F1 remainder (0.35 GPU-h) and
   the older 0.05639 remainder are **sealed and may not be used**.
3. `STORAGE_READY` from the S-track storage guard.
4. The predeclared tolerance in `R1_REPRODUCTION_SUCCESS_GATES.md` unchanged.

---

## 6. Summary

| Question | Answer |
|---|---|
| does the R1-B implementation exist? | **YES** |
| do the corrections work? | **YES** — B-1, B-2 and B-4 are measured, not asserted |
| all CPU gates pass? | **27/30**, 0 failures, 3 not-yet-run |
| ready to pilot? | **NOT YET** — verdict `NOT_READY_CONTRACT_UNRESOLVED` |
| is that an engineering failure? | **no** |
| what is the next action? | a **CPU-only HPC job** to close T19/T20/T29, then re-issue |