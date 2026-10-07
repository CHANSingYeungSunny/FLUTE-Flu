# R1 — PAPER REPRODUCTION CONTRACT

Generated 2026-10-06. Companion files: `R1_PAPER_TARGET_VALUES.csv`,
`R1_HYPERPARAMETER_EVIDENCE.csv`, `R1_PAPER_CODE_CONFLICTS.md`,
`R1_UNRECOVERED_INFORMATION.md`.

---

## 1. What R1 is asked to do

> Reproduce the original MIFlu paper's **national** ILI results on the author's official
> GitHub repository, and establish honestly how close that reproduction is.

**Target values** (re-verified this round directly against the project's paper copy; the
four-horizon means reproduce exactly as arithmetic):

| L | MSE | MAE |
|---:|---:|---:|
| 24 | 1.542 | 0.726 |
| 36 | 1.422 | 0.779 |
| 48 | 1.414 | 0.757 |
| 60 | 1.364 | 0.719 |
| **mean** | **1.4355** | **0.74525** |

---

## 2. What R1 is NOT

| Not this | Why |
|---|---|
| running the released code and calling it a reproduction | it executes with `PEFT=0`, a no-op freeze, an inert text path, Test-based selection and a single channel — none of which is the paper's model |
| the previous four feature-0 / Test-selected horizon runs | those are **A0-R released-code behaviour replays** |
| F1 | F1 is `EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT` under a project-designed contract |
| a search for settings that land near 1.4355 | that is accuracy hunting and is prohibited |

---

## 3. The three-track structure

### R1-A — literal released-code reproduction

| Aspect | Definition |
|---|---|
| code | author repo `6ed210150b8819313947cf607eb1821c87b1bee3`, **behaviour unmodified** |
| settings | released argparse defaults (1 epoch, 1e-4, `PEFT=0`, `multimodal` as released) |
| purpose | answer **"what does the official repository actually produce?"** |
| output | feature-0 Test scores with Test-based checkpoint selection, plus the documented defects |
| status | **substantially complete** — four horizons already executed on A100 (jobs 606365 / 606378 / 606385 / 606412), reported as A0-R |
| is it the paper reproduction? | **no** |

**R1-A's measured result** (final-epoch Test MSE, one repetition each): L24 0.5793 ·
L36 0.5920 · L48 0.6088 · L60 0.6361. These are **lower** than the paper's values, which is
**not** evidence of a better reproduction — they are a different quantity (one channel,
Test-selected, single repetition).

### R1-B — paper-intended reconstruction on the official repository

Apply **only** changes supported by the paper, or necessary to restore a mechanism the paper
describes and the released code fails to implement. Every change recorded.

| # | Change | Justification | Status |
|---|---|---|---|
| B-1 | **multivariate windows** (all seven channels) instead of `feat_id:feat_id+1` | the paper's task is explicitly over seven variables | required |
| B-2 | **functional text pathway** (text prefixed; patches read after it) | the paper's method *is* the text contribution; the released order provably makes text unreachable | required, declared algorithm change |
| B-3 | **`PEFT=1`** so LoRA is actually applied | the paper states LoRA r=4 is used | required |
| B-4 | **an effective freeze** | the paper says PE and layer-norm are tuned; the released loop is a no-op | required, with the trainable count reported |
| B-5 | **validation-only checkpoint selection** | the released rule selects on Test, which leaks | declared repair (the paper's rule is `UNRECOVERED`) |
| B-6 | **persist predictions and targets** | the released `np.save` calls are commented out, so nothing can be re-scored | required for independent scoring |
| B-7 | a **declared** training configuration | epochs/lr are undisclosed | `RECONSTRUCTED_ASSUMPTION`, declared before the run |

**B-2 is the single most consequential change**: it turns `text_inert` into `text_active`,
which is what the paper's claim requires. It must be labelled a *declared algorithm change*
pending author confirmation, never as "the released behaviour".

### R1-C — bounded sensitivity analysis

Only for Tier-A unrecovered items, and only two of them:

| Item | Predeclared candidate set | Basis |
|---|---|---|
| epochs | **{1, 20}** | 1 = released default; 20 = the project's prior declaration. Nothing else. |
| learning rate | **{1e-4, 5e-4}** | 1e-4 = released default; 5e-4 = the project's prior declaration. Nothing else. |

That is **4 combinations**, and no others. **Results are reported as a sensitivity band,
never as a reproduction.** Selecting a combination *because* it lands nearest 1.4355 is
prohibited.

---

## 4. Required settings and their status

Full per-setting classification is in `R1_HYPERPARAMETER_EVIDENCE.csv`. Summary:

| Class | Count | Examples |
|---|---:|---|
| `PAPER_EXPLICIT` | 8 | K=6, Lp=24, S=2, r=4, 10 repetitions, 70:10:20, full GPT-2 embedder, four-horizon equal-weight mean |
| `OFFICIAL_CODE_EXPLICIT` | 9 | batch 16, Adam, scaler-on-train, standardized space, col names, 676/97/193 |
| `LOG_RECOVERED` | 1 | the LR schedule behaviour (hard-coded 0.9 from epoch 4) |
| `CONFLICTING_EVIDENCE` | 4 | target identity; text order; LoRA applied?; trainable count |
| `UNRECOVERED` | 5 | pooling axes; epochs; lr; seeds; checkpoint rule |
| `UNRESOLVED` (paper prose vs file) | 1 | the 2002–2021 vs 2020-06-30 date span |

**The fully matchable items are the minority; the four structural conflicts and five
unrecovered items are what make `EXACT_OR_NEAR_REPRODUCTION` unlikely.**

---

## 5. The ten unresolved items the brief asks about

| # | Item | Answer | Class |
|---|---|---|---|
| 1 | Table V target identity | the paper never states which variable(s) the scalar covers; the code evaluates channel 0 (`% WEIGHTED ILI`) | `CONFLICTING_EVIDENCE` |
| 2 | single-target or seven-variable? | the **task** is seven-variable (paper L78/L238); the **released implementation** is single-channel | `CONFLICTING_EVIDENCE` |
| 3 | exact pooling axes | **not stated** | `UNRECOVERED` |
| 4 | MSE/MAE scale | **standardized** (paper agrees for national; code explicit) | `CODE_EXPLICIT` — the one clean match |
| 5 | checkpoint-selection rule | **not stated**; code selects on Test | `UNRECOVERED` |
| 6 | epoch count | **not disclosed**; code default 1 | `UNRECOVERED` |
| 7 | initial learning rate | **not disclosed**; code default 1e-4 | `UNRECOVERED` |
| 8 | LR scheduling | **not disclosed**; code applies a hard-coded 0.9 decay from epoch 4 | `UNRECOVERED` (paper) / `LOG_RECOVERED` (code) |
| 9 | ten-repetition aggregation | **arithmetic mean**, stated; mechanism is `--itr` | `PAPER_EXPLICIT` (rule) — the count is not recoverable |
| 10 | text sequence order | the paper **contradicts itself** (L205 vs L219); the code uses the order that makes text inert | `CONFLICTING_EVIDENCE` |
| 11 | does the paper-intended text pathway differ from the released one? | **yes, necessarily** — the released one provably cannot influence any read-out quantity | answered by measurement |
| 12 | does released code contain an error preventing faithful reproduction? | **yes, at least five**: single-channel windows, inert text, `PEFT=0`, no-op freeze, Test-based selection, no persisted predictions | answered by measurement |

**Items 11 and 12 are settled by evidence already gathered.** Items 3, 5, 6, 7, 8 are
permanently or practically unrecoverable.

---

## 6. Acceptance

R1 is **not** judged by whether a number lands near 1.4355. It is judged by whether:

1. the complete contract is stated, per-setting, with classifications;
2. every deviation from released behaviour is declared;
3. both R1-A and R1-B are executed and reported **separately**;
4. the verdict is drawn from the scale in `R1_REPRODUCTION_SUCCESS_GATES.md`;
5. the unrecoverable items are named, not papered over.

A `PARTIAL_REPRODUCTION` with a precise blocker list is a **successful R1 outcome**. A
number close to 1.4425 achieved by tuning would be a **failure**.