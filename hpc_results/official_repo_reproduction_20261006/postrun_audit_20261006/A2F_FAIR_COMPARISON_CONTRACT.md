# A2-F FAIR COMPARISON CONTRACT

Generated 2026-10-06. Append-only.

**A2-F** = the new fair LLM vs non-LLM comparison, using the author's official MIFlu
repository as the MIFlu implementation basis, under **one shared evaluation contract**.

**Status: `NOT_STARTED`.** This document defines the contract that a run must satisfy
before it may carry the A2-F label. No A2-F run exists yet.

---

## 1. Budget reality, stated first

The remaining GPU allowance is **0.05639 GPU-h**. A2-F cannot start without new quota.
See `NEXT_GPU_BUDGET_OPTIONS.md`. This contract is written so that, when quota arrives,
the run is unambiguous.

---

## 2. Shared conditions — all mandatory

| # | Condition | Rationale |
|---|---|---|
| S1 | **Same dataset version** — the author 966-row file, SHA-256 `31ffc169…b87a`, or another version only if the paper-contract audit justifies it | a different vintage is a different estimand |
| S2 | **Same chronological split** — 676 / 97 / 193, zero-based half-open | no leakage, no re-splitting per model |
| S3 | **Scalers fitted on training rows only** (rows `[0,676)`) | leakage rule |
| S4 | **Identical target variables** for every model | otherwise models are scored on different tasks |
| S5 | **Input length T = 104** | matches the released configuration |
| S6 | **Horizons L ∈ {24, 36, 48, 60}**, each trained independently | four independent runs, not one walk-forward |
| S7 | **Identical legal forecast origins** — full target containment (`[o+1, o+L]` inside the split) | removes the released code's silent window dropping |
| S8 | **Identical forecast leads** 1..L | — |
| S9 | **Identical feature keys** — the same channels scored for every model | the released code's channel-0-only behaviour must NOT be inherited |
| S10 | **Identical seeds** — one declared list used by every model | pairing must be real |
| S11 | **Validation-only checkpoint selection** | no Test leakage |
| S12 | **Test evaluated once**, after all checkpoints are frozen | one-shot evaluation |
| S13 | **Validation/Test not shuffled** | ordering is part of the protocol |
| S14 | **`drop_last = False`** in every loader | every eligible origin is scored |
| S15 | **Predictions and targets saved** per `(model, L, seed, origin, lead, variable)` | independent re-scoring must be possible |
| S16 | **Independent scorer** — not the training code's own metric path | self-scoring proves nothing |
| S17 | **No Test leakage** anywhere, including scaler, prompt statistics and model selection | — |
| S18 | **No cross-track checkpoint reuse** — nothing from Historical Track B | see `TRACK_SEPARATION_RULES.md` |
| S19 | **Manifests complete** — job id, code hash, data hash, config, seed list, per-run status | auditability |
| S20 | **Implementation identity documented** for every model | canonical / adapted / inspired / reconstructed |

**A run missing any single condition is not A2-F.** It may be reported, but under a
different label with the missing conditions named.

---

## 3. Model categories

The brief's four categories are adopted verbatim, because the LLM/unimodal distinction is
exactly where earlier reporting went wrong.

| Category | Definition | Members |
|---|---|---|
| **1. LLM-based multimodal** | uses a pretrained LLM **and** a non-numeric modality (text) that demonstrably reaches the forecast | corrected text-active MIFlu |
| **2. LLM-based unimodal** | uses a pretrained LLM backbone, **no** text input | matched no-text MIFlu (GPT-2 forecasting backbone retained) |
| **3. Dedicated / non-LLM** | no pretrained LLM at all | NLinear, DLinear, (canonical PatchTST, iTransformer if eligible) |
| **4. Naive references** | deterministic, no learned parameters | Last Value, leakage-safe Seasonal Naive |

### The rule that must not be broken

> A no-text MIFlu that retains the GPT-2 forecasting backbone is **LLM-based unimodal**.
> It is **not** a non-LLM model, and it must never be counted in the non-LLM group.

Earlier reporting put `notext` outside both groups, which was safe; the stricter
four-category scheme now places it explicitly in category 2.

---

## 4. Core A2-F model set

| Category | Model | Required state |
|---|---|---|
| 1 | **corrected text-active MIFlu** | text path verified active (see `A2_TEXT_ACTIVE_MAGNITUDE_AUDIT.md`); input in StandardScaler space |
| 2 | **matched no-text MIFlu** | same GPT-2 backbone, same LoRA, same budget — only the text path removed |
| 3 | **NLinear** | canonical |
| 3 | **DLinear** | own re-implementation, labelled as such |
| 4 | **Last Value** | deterministic |
| 4 | **leakage-safe Seasonal Naive** | for lead > 52, repeat only the last observed cycle; never read `y[o+k-52]` |

Optional, only with valid implementation identity: PatchTST, iTransformer, Qwen Time-LLM,
CALF, TimeCMA. **DeepSeek is explicitly excluded.**

---

## 5. The 2×2 mechanism design

To separate the text contribution from the LoRA contribution:

| Cell | text | LoRA | forecasting backbone |
|---|---|---|---|
| A | ✅ | ✅ | GPT-2 |
| B | ✗ | ✅ | GPT-2 |
| C | ✅ | ✗ | GPT-2 |
| D | ✗ | ✗ | GPT-2 |

**A vs B** is the matched text contrast. **A vs C** isolates LoRA. The released code's
"w/o multimodality" row is **not** cell D — it removes the text branch, not the backbone
— and Table VIII's last row is described as GPT4TS, so it does not isolate the value of a
pretrained LLM either.

---

## 6. Reporting contract

For the completed A2-F benchmark, report **all** of:

1. overall best individual model (lowest equal-weight four-horizon average MSE);
2. best LLM-based **multimodal** model;
3. best LLM-based **unimodal** model;
4. best dedicated/non-LLM model;
5. best naive reference;
6. matched mechanism result (A vs B), with the corrected win counts;
7. per-horizon winners L = 24/36/48/60;
8. stability — mean, SD, per-seed values, and any horizon reversals;
9. cost — training time, inference time, peak VRAM, total and trainable parameters,
   checkpoint size;
10. statistical comparison — paired cells, corrected win counts, uncertainty.

**Prohibited**: using "the mean of a selected group of LLMs vs a selected group of
non-LLMs" as the sole headline; or choosing only the group mean when the best individual
disagrees, or only the best individual when the group mean disagrees. **Report both,
clearly labelled.**

---

## 7. What A2-F will and will not support

| Will support | Will not support |
|---|---|
| which of the **selected implementations** performs best under this contract | a claim about "LLM forecasters" in general |
| whether the corrected MIFlu beats its matched no-text control | a reproduction of Table V |
| whether the official-repository basis changes the ranking (empirically tested) | a claim that the author's code was reproduced |

**The last row matters**: switching to the official repository **must not be assumed** to
improve MIFlu or to change the ranking. The question is answered by running it, not by
expecting it.