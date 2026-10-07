# SEAMLESS MIFLU REPLACEMENT PROTOCOL

Generated 2026-10-06. Answers whether the reproduced/reconstructed official MIFlu can be
transferred into the historical 4 LLM vs 4 non-LLM comparison while holding the other
seven components fixed.

---

## 1. The exact historical experiment

Recovered by the historical-inspection pass (R5).

| Side | Exact model strings |
|---|---|
| **LLM (4)** | `gpt2_miflu` · `qwen_time_llm` · `calf_llm` · `timecma_llm` |
| **non-LLM (4)** | `nlinear` · `dlinear` · `patchtst` · `itransformer` |

Source: `results/v3_clean/analysis/frozen_analysis_protocol.json` → `family_membership`,
identical in `selection_outcome.json` and `runs/complete_specs_598.csv`.
**The brief's expected identities are confirmed; no substitutions were needed.**

### The component to be replaced

| Item | Value |
|---|---|
| display name | `gpt2_miflu` |
| implementation | `scripts/miflu_model.py`, class `MIFlu` |
| adapter | `scripts/innovation/backbones/gpt2_miflu_adapter.py` (`GPT2MifluAdapter`) |
| identity | **the project's own from-scratch re-implementation — NOT the author's `models/GPT4TS_lora.py`** |
| as-run snapshot | byte-identical to `results/innovation/source_snapshot/` (`0e6bdb61…`) |
| trainable params | 1,030,056 (L24) … 1,223,844 (L60) |
| total params | `UNRECOVERED` |

### The two historical stages (kept separate)

| Stage | Content | Comparison |
|---|---|---|
| **C** `wave1_validation_v3clean` | 580 rows, 2026-09-20 | the **validation ranking** — `gpt2_miflu` **1st** (0.771) |
| **D** `final_test_holdout_v3clean` | 84 runs, one-time Test/Holdout | `gpt2_miflu` **lost** (3.0505) to `nlinear` (2.7389) |

**A verification reversal**: the model that won validation lost Test. Any replacement must
be evaluated on **both**, because they disagree.

---

## 2. Compatibility, field by field

| Field | Historical contract (Stage C/D) | R1-B / author-966 contract | Compatible? |
|---|---|---|---|
| dataset | **July-2026 1025 rows** | author 966 rows | ❌ |
| split | **717 / 102 / 206** | 676 / 97 / 193 | ❌ |
| date range | through 2021 | stored dates end 2020-06-30 | ❌ |
| variables | 7 | 7 | ✅ |
| target contract | z-space, 7-channel | z-space, 7-channel | ✅ |
| scaler | train-fit, per contract | train-fit | ✅ (different rows) |
| input length T | 104 | 104 | ✅ |
| horizons | 24/36/48/60 | 24/36/48/60 | ✅ |
| forecast origins | historical window rule | strict containment | ⚠️ must be checked per stage |
| seeds | 42–51 (10) | 42+ | ⚠️ |
| checkpoint rule | historical | validation-only (R1-B, B-5) | ⚠️ |
| prediction format | `test_predictions.csv` | NPZ | ⚠️ conversion needed |
| seasonal naive formula | **safe** | safe (corrected) | ✅ |

**Conclusion: the *data* contracts are incompatible.** An author-966 MIFlu result cannot be
inserted into a 1025-row ranking — the forecast keys are different origins on a different
series.

---

## 3. The eight questions

| # | Question | Answer |
|---|---|---|
| 1 | Which historical MIFlu entry must be replaced? | **`gpt2_miflu`**, i.e. `scripts/miflu_model.py::MIFlu` via the adapter |
| 2 | Can the reproduced **author-data** MIFlu result be inserted directly? | **NO** — different dataset, split and origins |
| 3 | Can official MIFlu predictions be scored on the exact historical keys? | **NO**, not as-is: the historical keys are 1025-row origins |
| 4 | Can the seven old model predictions remain unchanged? | **YES** — the final-Test predictions exist locally as `test_predictions.csv` in 84 run directories |
| 5 | Do the seven models require re-scoring? | **NO** for their own metrics; the *ranking* is re-aggregated, not re-scored |
| 6 | Do any require retraining? | **NO** |
| 7 | **Must official MIFlu be retrained on the historical 1025-row contract?** | **YES** |
| 8 | Would changing only MIFlu still be scientifically interpretable? | **YES**, if and only if the retrained MIFlu uses the historical contract exactly — then the other seven are untouched and the difference is attributable |

---

## 4. Verdict

# `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED`

per historical comparison stage:

| Stage | Verdict |
|---|---|
| **C** Wave-1 validation ranking | `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` |
| **D** final Test/Holdout | `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` |
| author-966 A2/stage-6 track | `INCOMPATIBLE_WITHOUT_NEW_CONTROLLED_EXPERIMENT` — a different data contract; not the historical comparison |

### What must be retrained, and what must be labelled

The run that replaces `gpt2_miflu` must be labelled:

> **official-repository-based MIFlu transferred to the historical comparison contract**

**It must NOT be called the paper reproduction.** It is the R1-B architecture and
mechanism trained under a *different* data contract in order to be comparable with the
seven fixed historical models.

If R1-B cannot be validated, the fallback is the **best-evidence official-repository-based
reconstruction**, with the same label plus `(reconstruction)`.

---

## 5. The controlled replacement, stated precisely

```
FIXED (7 components, unchanged):
    qwen_time_llm, calf_llm, timecma_llm        (LLM side, minus MIFlu)
    nlinear, dlinear, patchtst, itransformer    (non-LLM side)

REPLACED (1 component):
    gpt2_miflu:  scripts/miflu_model.py::MIFlu
             ->  R1-B on the historical 1025-row contract
                 (same 717/102/206 split, same scaler rule, same origins,
                  same seeds, same horizons, same metric)

UNCHANGED:
    the historical evaluation logic, metric definition, aggregation and
    the historical grouping (4 LLM vs 4 non-LLM)
```

**The one unavoidable new work item** is the retrained MIFlu itself. Everything else is
reused. That is the minimum scientifically necessary rerun.

---

## 6. Cost and data consequences

| Consequence | Detail |
|---|---|
| new learned fits | MIFlu × 4 horizons × the historical seed count (10) = **40 fits** on the historical contract |
| output location | `$HOME` — scratch is over quota and must not receive new output |
| dataset | the July-2026 1025-row snapshot, SHA-256 to be pinned at run time |
| the seven others | re-used from `results/v3_clean/`, **never re-scored** |
| checkpoint storage | see the S-track; the historical Qwen reduction techniques are directly relevant |

---

## 7. What must not happen

| Prohibited |
|---|
| inserting an author-966 metric into the 1025-row ranking |
| calling the transferred run the paper reproduction |
| retraining the other seven "for consistency" — that would break the control |
| using the F1 contract, which is a *third* data/contract combination |
| re-scoring the historical Test as if it were fresh — it is **exposed** and stays retrospective |