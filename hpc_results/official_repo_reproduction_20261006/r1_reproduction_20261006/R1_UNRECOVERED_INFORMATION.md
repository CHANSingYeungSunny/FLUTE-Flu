# R1 — UNRECOVERED INFORMATION

Generated 2026-10-06. What is **not knowable** from the paper plus the released artifacts,
and what each gap does to a reproduction attempt.

---

## 1. The three tiers

| Tier | Meaning | Handling |
|---|---|---|
| **A — permanently unrecoverable** | no evidence exists anywhere in the paper, the released tree, the logs, or the project's prior work | declare, do not guess |
| **B — recoverable only by author inquiry** | the information existed but was never published | an approved inquiry could close it |
| **C — recoverable with more work** | derivable from artifacts already held | do the work |

---

## 2. Tier A — permanently unrecoverable

| # | Item | Why it is unrecoverable | Effect on R1 |
|---|---|---|---|
| A1 | **Table V pooling axes** (Q12) | the paper states no pooling rule; no code path is identified as producing Table V | the reproduced scalar cannot be proven to be the same quantity |
| A2 | **epochs** | "set empirically" with no value; the released default (1) is not a paper value | R1-B must declare a reconstruction |
| A3 | **initial learning rate** | same | same |
| A4 | **optimizer / scheduler as used by the authors** | not stated; the released defaults are the only evidence and are not paper values | R1-B uses the code defaults as declared defaults |
| A5 | **the seed list** (paper) | the paper says only "the mean of 10 repetitions"; there is no list | R1 must declare its own list, or use the released harness's implicit mechanism |
| A6 | **whether Table V's MIFlu column is quoted or re-run** | Section V-C names only the baseline provenance | caps any reproduction verdict |
| A7 | **whether the released tree is the code that produced Table V** | nothing links the released commit to the reported numbers | same |

**No amount of execution closes Tier A.**

---

## 3. Tier B — recoverable only by author inquiry

| # | Item | What would close it |
|---|---|---|
| B1 | actual epochs and learning rate | a one-line answer, or the launch script/CI config that was not published |
| B2 | actual checkpoint-selection rule | whether the authors selected on Test or validation |
| B3 | the token order actually used | resolves the paper's internal L205/L219 contradiction |
| B4 | whether the text pathway was functional in the authors' own runs | distinguishes "the released code is defective" from "the method does not use text" |
| B5 | which data file and date span were used | resolves paper prose "2002–2021" vs the file's 2020-06-30 |
| B6 | the exact Table V command line | would settle A1, A2, A3 and A5 at once |

**An inquiry must be drafted and approved before sending** (`EE4080_MIFlu_Research_Recovery_Plan.md` §12 item 10). It has not been drafted or sent.

---

## 4. Tier C — recoverable with more work

| # | Item | Work required |
|---|---|---|
| C1 | is `% WEIGHTED ILI` the right semantic mapping for channel 0? | compare the released numeric header against the CDC field definitions — **partially done**; the OT identity was already proven (`100 * col5 / OT` reproduces col2 to ~5e-6) |
| C2 | does the released `freeze` no-op actually leave every parameter trainable? | **done** — measured 82,705,944/82,705,944 |
| C3 | is the released text path really inert? | **done** — CPU and A100, positive control included |
| C4 | what exactly does the released `mse_mean` mean? | **done** — mean over `itr` of the final-epoch Test MSE |
| C5 | the LR schedule actually applied | **done** — hard-coded 0.9 from epoch 4; `decay_fac` inert (verified arithmetically) |
| C6 | per-(model, L, seed) coverage and window counts | **done** — 549/74/170, 537/62/158, 525/50/146, 513/38/134 |

**Tier C is essentially exhausted.** The remaining gaps are A and B.

---

## 5. The honest consequence for the R1 verdict

Because **A1 (pooling axes)** and **A6 (Table V column provenance)** are permanently
unrecoverable, R1 **cannot** deliver `EXACT_OR_NEAR_REPRODUCTION` in the strong sense of
"same contract, all major settings recovered".

The realistic best outcomes are:

| Verdict | Reachable? | Meaning here |
|---|---|---|
| `EXACT_OR_NEAR_REPRODUCTION` | **only if** the tolerance is applied to a **declared** contract, with the pooled-axis ambiguity disclosed | "near, under a reconstructed contract of the same *kind*" |
| `PARTIAL_REPRODUCTION` | **most likely** | qualitative setup matched; some settings reconstructed; results directionally similar |
| `EXECUTABLE_BUT_NOT_REPRODUCED` | possible | the reconstruction runs but the numbers/contract do not match |
| `NOT_REPRODUCIBLE_FROM_RELEASED_ARTIFACTS` | possible | if the R1-B reconstruction cannot even produce the right *kind* of output |

**What must never be written**: "we reproduced the paper's 1.4355" — regardless of how close
a number lands, given A1 and A6.

---

## 6. What R1 can still contribute honestly

1. A precise, evidence-graded statement of **what the released code does** (R1-A) — already
   substantially done and verified on GPU.
2. A **declared reconstruction** of the paper-intended mechanism (R1-B), with every
   deviation listed, and a measured distance to the reported values under a stated tolerance.
3. A **bounded sensitivity band** (R1-C) over the two Tier-A training settings, reported as
   sensitivity, never as reproduction.
4. A clear statement of the **six** things that would be needed to do better — five of which
   are author-inquiry items.

That is a defensible FYP outcome: *a partially reproduced result with precisely localized
blockers* — which `EE4080_MIFlu_Research_Recovery_Plan.md` §5 already anticipated as a
legitimate endpoint.