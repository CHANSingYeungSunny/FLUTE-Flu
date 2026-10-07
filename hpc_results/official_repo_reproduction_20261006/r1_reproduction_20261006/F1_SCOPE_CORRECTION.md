# F1 SCOPE CORRECTION

Generated 2026-10-06. **F1 is frozen. Nothing in it has been deleted or altered**
(29/29 artefacts re-verified byte-identical against `F1_EXECUTION_MANIFEST.csv`).

## New classification

# `EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT`

F1 was a **genuinely designed and correctly executed** experiment. It is reclassified
because it **answered a question that was not the primary one**, not because anything in
it was wrong.

---

## 1. What F1 actually was

A six-model, one-seed pilot under a **newly designed** seven-channel A2-F contract:

| Model | Category |
|---|---|
| corrected text-active MIFlu | LLM multimodal |
| matched no-text MIFlu | LLM unimodal |
| NLinear | dedicated / non-LLM |
| DLinear | dedicated / non-LLM |
| Last Value | naive reference |
| leakage-safe Seasonal Naive | naive reference |

Result (avg4L MSE): notext 1.8870 · nlinear 2.0351 · miflu 2.0484 · seasonal_naive 2.2223 ·
dlinear 2.3521 · last_value 7.1658. GPU cost 0.25000 / 0.60 granted. All 8 gates passed.

---

## 2. What F1 was NOT

| Claim | Status |
|---|---|
| the original paper reproduction | ❌ **not attempted** — F1 used a *new* contract, not the paper's |
| the requested MIFlu-replacement experiment | ❌ **no** — the old 4-vs-4 comparison was never loaded |
| the new 4 LLM vs 4 non-LLM comparison | ❌ **no** — only 2 of the 8 models were present |
| permission to proceed to F2 | ❌ **revoked** — F2 is not to be run |
| the main project completion result | ❌ **no** — it is supplementary |

### The three specific divergences

1. **It did not reproduce the paper.** F1 used seven channels in StandardScaler space with
   an equal-weight four-horizon average — a **project-designed** contract. The paper's
   Table V contract is partly `UNRECOVERED` (pooling axes Q12, target identity, checkpoint
   rule). F1 therefore could not have been a reproduction, and was never labelled one.
2. **It did not replace MIFlu inside the old experiment.** The old pre-official-repository
   4 LLM vs 4 non-LLM comparison was never opened. F1 contains **two** of its eight
   models.
3. **It did not rerun the 4-vs-4 set.** Qwen Time-LLM, CALF, TimeCMA, PatchTST and
   iTransformer were absent by design (the F1 contract excluded them).

---

## 3. Why F1 is still worth keeping

| Value | Detail |
|---|---|
| it is a **contract-validated, independently scored** six-model comparison | 24 artefacts, 0 rejected, 0 duplicate keys, 0 forecast-key violations, all gates pass |
| it **empirically answers** whether the official-repository basis changes the ranking | partly — it shows the corrected MIFlu *does not* beat NLinear or no-text at one seed |
| it produced **model-level cost at pilot scale** | 0.0533 GPU-h/MIFlu fit measured again (0.25 for 8 fits) |
| it **verified the corrected text path is active** on trained checkpoints | 4/4 `text_active` |
| it exposed and fixed **five real defects** | see the execution report §9 |

So F1 stands as `EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT` — a supplementary corrected-contract
experiment. It is **not** on the primary path.

---

## 4. Restrictions now in force

| # | Restriction |
|---|---|
| 1 | **F1 is frozen.** No deletion, no alteration, no re-scoring under a different contract. |
| 2 | **F2 is not to be run.** Three-seed expansion is cancelled, not deferred. |
| 3 | **The remaining 0.35 GPU-h of the F1 authorization must not be spent** on F2 or any other experiment. |
| 4 | **No GPU work at all** until the corrected plan and the reproduction requirements are established and a *reproduction-specific* authorization is given. |
| 5 | F1 must never be cited as the paper reproduction, the MIFlu replacement, or the 4-vs-4 comparison. |

---

## 5. Referring to F1 from now on

**Correct**: *"An exploratory corrected-contract pilot (F1) compared six models under a
project-designed seven-channel contract and found no separation between the corrected
MIFlu and NLinear at one seed. It is supplementary to the primary reproduction workflow."*

**Incorrect**: any phrasing implying F1 reproduced the paper, replaced MIFlu inside the old
benchmark, or constitutes the 4 LLM vs 4 non-LLM comparison.

---

## 6. Interaction with the remaining budget

| Item | Value |
|---|---:|
| F1 authorization | 0.60 GPU-h |
| F1 consumed | 0.25000 GPU-h |
| F1 **unused remainder** | **0.35000 GPU-h** |
| may it be spent on F2? | ❌ **no** |
| may it be spent on anything else? | ❌ **no** — the authorization was exclusive to the F1 six-model contract |

The 0.35 remainder is **parked**. It is not an allowance for the R1 reproduction, which
requires its own authorization.