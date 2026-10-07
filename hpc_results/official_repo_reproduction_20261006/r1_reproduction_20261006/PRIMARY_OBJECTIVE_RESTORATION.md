# PRIMARY OBJECTIVE RESTORATION

Generated 2026-10-06. This document restores the original workflow and states plainly how
the recent execution diverged from it.

---

## 1. The original required workflow (restored)

> **1.** First reproduce the original MIFlu paper results using the author's official
> GitHub repository.
> **2.** Only after the official-repository MIFlu reproduction is successfully
> established, inspect the complete earlier 4 LLM vs 4 non-LLM project that was already
> completed **before** pulling the author's repository.
> **3.** Preserve that earlier comparison framework, datasets, model set and evaluation
> logic as far as scientifically valid.
> **4.** Replace **only** the old self-built MIFlu implementation with the correctly
> reproduced official-repository MIFlu.
> **5.** Rerun the original 4 LLM vs 4 non-LLM comparison and determine how replacing
> MIFlu changes the results and ranking.

**The scientific shape of this design is worth stating explicitly**, because it is what
makes it the right primary objective:

> The old comparison is a **controlled experiment**. Seven of its eight components stay
> fixed; **one** — the MIFlu implementation — is swapped. The resulting change in ranking
> is therefore **attributable to that swap**, which is exactly the question "does using
> the authors' own code change our conclusion?".

F1 could not answer that question, because it replaced **the entire model set and the
entire evaluation contract** at the same time. Nothing in F1 is attributable to the MIFlu
swap alone.

---

## 2. How execution diverged

| Step | What the restored workflow requires | What happened |
|---|---|---|
| 1 | reproduce the paper on the official repo | **not attempted.** Instead: an A2-basis eight-model benchmark (stage 6), A0-R released-code replays, and then a **project-designed** A2-F contract (F1) |
| 2 | only *then* inspect the old 4-vs-4 project | the old comparison was **never opened** for this purpose; the July-2026 1025-row track was treated as an isolated historical artifact |
| 3 | preserve the old framework/datasets/logic | not done — the A2-F contract **redefined** the target, the model set and the aggregation |
| 4 | replace **only** MIFlu | **not done** — F1 replaced the whole set and the contract |
| 5 | rerun 4-vs-4 and measure the MIFlu effect | **not done** |

**Root cause of the divergence**: the recovery plan's own §5 ("Exact MIFlu reproduction
specification") and the A2-F contract were both treated as the primary path at different
times, and neither is the workflow above. The plan is a *recovery* document; the objective
is a *controlled replacement experiment*. They were conflated.

**A second contributing cause, stated honestly**: the paper-reproduction track was
correctly diagnosed as **blocked by missing information** (Q12 pooling axes, target
identity, checkpoint rule), and rather than reporting that block and stopping, execution
pivoted to experiments that *were* executable. That pivot was not authorized as a
substitution.

---

## 3. The corrected order (mandatory)

| Stage | Content | Gate to the next stage |
|---|---|---|
| **R1** | reproduce the original MIFlu paper on the author's official repository | a reproduction verdict of `EXACT_OR_NEAR_REPRODUCTION` or an explicit decision to proceed on a `PARTIAL_REPRODUCTION` |
| **R2** | verify whether the reproduction genuinely matches the paper | contract comparison + numerical comparison, per horizon and metric, with repetition count stated |
| **R3** | inspect and reconstruct the old pre-official-repository 4 LLM vs 4 non-LLM comparison | a frozen record of the old set, datasets, protocol and results |
| **R4** | replace **only** the old self-built MIFlu with the reproduced official-repository MIFlu | a documented swap, with everything else held fixed |
| **R5** | rerun the same 4-vs-4 comparison under a clearly defined replacement protocol | complete run matrix with the same model set |
| **R6** | compare old versus new, and identify how the replacement changes the ranking | a ranking-change report |

**A2-F and F1 are supplementary.** They may be cited as corrected-contract evidence, but
they do not satisfy, replace, or shortcut any of R1–R6.

---

## 4. The one thing that must not be repeated

The previous rounds spent GPU time on experiments that were executable rather than on the
experiment that was **required**. The corrected order inverts that priority: R1 is
attempted first, and if R1 is genuinely blocked, **the block is reported and the decision
is escalated** — not silently replaced by a different experiment.

---

## 5. What "done" means for the primary objective

The primary objective is complete only when R6 has been executed and reported, i.e. when
it is known **how replacing the self-built MIFlu with the reproduced official MIFlu
changes the original 4 LLM vs 4 non-LLM ranking**.

If R1 cannot be achieved, the honest terminus is:
*"the paper could not be reproduced from the released artifacts; the replacement
experiment therefore could not be run as specified"* — with the reasons recorded, not
substituted.