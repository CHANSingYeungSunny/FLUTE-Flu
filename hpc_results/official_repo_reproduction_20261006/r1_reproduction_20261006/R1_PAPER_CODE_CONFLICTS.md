# R1 — PAPER vs OFFICIAL-CODE CONFLICTS

Generated 2026-10-06. These are the places where the paper and the author's released code
**disagree**. They are the reason R1 needs an R1-A / R1-B / R1-C split rather than a single run.

---

## Conflict 1 — target identity and window shape (the largest)

| | Paper | Released code |
|---|---|---|
| task | national ILI **plus several sub-indicator variables**; seven variables listed in Table X | — |
| window | multivariate in intent | `seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]` → **one channel**; every split is univariate |
| Test coverage | not stated | `__len__` omits `× enc_in` for Test, so `feat_id` is identically 0 → **channel 0 only** |
| evidence | `MIFlu_paper.md` L78, L238, L464-510 | `data_loader.py` L299, L305, L312-317 |

**Consequence**: the released code **cannot produce a seven-variable score**. It is not a
"multivariate model with a Test bug" — it is a univariate formulation end to end.

**R1 implication**: R1-A reproduces this faithfully and reports it as released behaviour.
**R1-B must use a multivariate formulation**, which is a *declared reconstruction*.

---

## Conflict 2 — text pathway (the mechanism conflict)

| | Paper | Released code |
|---|---|---|
| sequence order | **self-contradictory**: L205 writes `R^{(len(token)+num(patches))×D}` (text first); L219 writes `R^{(num(patches)+len(token))×D}` (text last) | `cat((outputs, text_emb))` → text **after** patches |
| truncation | prose L222 "the token portion is discarded"; formula L225 `h_forecast[len(token):]` | `outputs[:, :self.patch_num, :]` → keeps the first `patch_num` positions |
| **functional effect** | text is the method's contribution | **VERIFIED `text_inert`**: equal-length different-content substitution changes the prediction by exactly 0; text gradient exactly 0 (CPU **and** A100, positive control included) |

**Consequence**: the paper's formula does not determine the order; and of the two candidate
orders, "time first" necessarily makes text unreachable under causal attention. The
released code implements that order and is provably inert.

**R1 implication**: R1-B must restore a text pathway that can function (text prefixed,
patches read after it), and must report this as a **declared algorithm change**, never as
"the released behaviour".

---

## Conflict 3 — LoRA

| | Paper | Released code |
|---|---|---|
| role | LoRA fine-tuning is part of why MIFlu works | `--PEFT` defaults to **0**, so the `get_peft_model` branch **never executes** |
| evidence | `MIFlu_paper.md` L300, L214 | `main_ILI_lora.py` L48, L74-90 |

**Consequence**: running the released defaults is *not* the paper's model.

**R1 implication**: R1-B sets `PEFT=1`. Note the argparse trap: `--target_modules` is
declared `type=str` with a **list** default, so any CLI override becomes a bare string and
`get_peft_model` raises `Target modules c_attn not found`. R1-B must **not** pass that flag.

---

## Conflict 4 — parameter freezing

| | Paper | Released code |
|---|---|---|
| rule | "only PE and layer-normalization typically fine-tuned" | the freeze loop only ever sets `requires_grad = True`; nothing is ever frozen → **82,705,944 / 82,705,944 = 100 % trainable** |
| evidence | `MIFlu_paper.md` L214 | `main_ILI_lora.py` L58-61 |

**Consequence**: the released default trains the entire GPT-2 stack.

**R1 implication**: R1-B must implement an actual freeze consistent with the paper's
description and **report the resulting trainable-parameter count**.

---

## Conflict 5 — checkpoint selection and Test exposure

| | Paper | Released code |
|---|---|---|
| rule | **not stated** | Test MSE selects the best epoch, **every epoch** (`min_mse` at L225, saved at L264); early stopping is instantiated but its call is commented out (L235-236) |

**Consequence**: released-code numbers are **Test-selected** and therefore not a clean
held-out score. A0-R's four horizon runs inherit this.

**R1 implication**: R1-B should use validation-only selection as a declared repair, **unless**
direct evidence establishes that the paper selected on Test. No such evidence exists —
the item is `UNRECOVERED`.

---

## Conflict 6 — undisclosed training configuration

| | Paper | Released code |
|---|---|---|
| epochs | **"set empirically"**, no number (`MIFlu_paper.md` L298; `paper_text.txt` L601-603) | `--train_epochs` default **1** |
| learning rate | **no number** | `--learning_rate` default **1e-4** |
| project used | — | 20 epochs / 5e-4, originating in `scripts/configs.py` and **mis-labelled "Paper:"** in the recovery plan L161 and the CodeBuddy prompt L63 |

**Consequence**: three different values exist (paper: none; code: 1 / 1e-4; project: 20 / 5e-4)
and **none can be called the paper's**.

**R1 implication**: R1-B declares a single reconstruction; **R1-C** may run a small
predeclared candidate set over these two items only. Neither may be tuned toward 1.4355.

---

## Conflict 7 — dataset date description

| | Paper | Released code / file |
|---|---|---|
| span | "national ILIs occurring in the US **between 2002 and 2021**" (Section V-A) | the released CSV's stored dates form a 7-day sequence ending **2020-06-30** |

**Consequence**: either the paper's prose is loose, or the released file is not the file
used. Both possibilities are live; the item is `UNRESOLVED`.

**R1 implication**: R1 must state which file it uses and never silently substitute one.

---

## Conflict 8 — provenance of Table V's own column

| | Paper |
|---|---|
| Section V-C, verbatim | *"The results for the national and regional ILI forecasting models are taken from [9] and [14], respectively."* |

In context this means the **baseline columns are quoted, not re-run**. Whether **MIFlu's own
column** is also quoted is **not stated** (`UNRECOVERED`).

**Consequence**: even a perfect execution of the released code might not be comparable to
Table V's MIFlu column, because that column may not have come from this code at all.

**R1 implication**: R1 must report this as a limitation on *any* reproduction verdict.

---

## Summary

| # | Conflict | Can R1-B resolve it? | Or is it permanent? |
|---|---|---|---|
| 1 | target identity / window shape | yes, by declaration | — |
| 2 | text pathway | yes, by declaration | — |
| 3 | LoRA | yes, by setting `PEFT=1` | — |
| 4 | freezing | yes, by implementing it | — |
| 5 | checkpoint rule | **partly** — the paper's rule is unknowable | permanent ambiguity |
| 6 | epochs / lr | **no** — nothing to recover | permanent; R1-C only |
| 7 | dataset span | **no** — prose vs file disagree | permanent ambiguity |
| 8 | Table V column provenance | **no** | permanent limitation |

**Four of eight conflicts are permanently unresolvable from the released artifacts.**
That is why the R1 verdict scale includes `NOT_REPRODUCIBLE_FROM_RELEASED_ARTIFACTS` and why
a `PARTIAL_REPRODUCTION` outcome is a legitimate and expected result.