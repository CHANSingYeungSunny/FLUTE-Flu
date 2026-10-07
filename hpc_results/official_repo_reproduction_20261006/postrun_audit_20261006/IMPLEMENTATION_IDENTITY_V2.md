# IMPLEMENTATION IDENTITY — V2

Generated 2026-10-06. Append-only refinement of `../IMPLEMENTATION_IDENTITY.md`.
Machine-readable form: `A2F_MODEL_ELIGIBILITY_MATRIX.csv`.

---

## 1. The rule that governs everything below

> Using the author's official MIFlu repository as the **basis** for the MIFlu arm does
> **not** make any other model an "official implementation".

NLinear, DLinear, PatchTST, iTransformer, Qwen Time-LLM, CALF and TimeCMA come from their
own sources or from this project's own re-implementations. Their identity labels below are
independent of which repository hosts the MIFlu arm.

---

## 2. Identity labels

| Model | Label | Source | Why this label |
|---|---|---|---|
| **corrected MIFlu** | `reconstructed` | project `scripts/miflu_model.py` on the author 966-row contract | a from-scratch re-implementation with a repaired text path; **not** the released `GPT4TS_lora.py` |
| **matched no-text MIFlu** | `reconstructed ablation` | `scripts/train_ablation.py` | same implementation with the text branch removed |
| **NLinear** | **`canonical`** | `scripts/innovation/backbones/dlinear.py::NLinear` | matches the published formulation |
| **DLinear** | `own re-implementation` | `...::DLinear` | correct in structure but authored here; not claimed as the authors' code |
| **PatchTST** | **`INSPIRED` — explicitly NOT canonical** | `...patchtst.py::PatchTST` | its own `architecture_report()` lists three deviations from canonical PatchTST |
| **iTransformer** | `own re-implementation` | `...itransformer.py::ITransformer` | structure matches; fidelity review recommended before identity claims |
| **TimeCMA** | `INSPIRED / adaptation` | `...llm_inspired.py::TimeCMAInspired` | retrieval alignment not verified against the paper |
| **CALF** | `INSPIRED / adaptation` | `...::CALFInspired` | principal alignment modules and losses not verified |
| **Qwen Time-LLM** | `INSPIRED / adaptation` | `...::QwenTimeLLM` | frozen Qwen2.5-1.5B, patch-prototype reprogramming, Prompt-as-Prefix — **not** the official Time-LLM |
| **Last Value / Seasonal Naive** | `deterministic reference` | `scripts/train_naive_966.py` | zero learned parameters |

**Only NLinear is canonical.** Everything else is qualified.

---

## 3. The four-category scheme (replacing the old two-group scheme)

| Category | Members | Note |
|---|---|---|
| **1. LLM-based multimodal** | corrected text-active MIFlu; TimeCMA/CALF/Qwen (adapted) | text input that demonstrably reaches the forecast |
| **2. LLM-based unimodal** | **matched no-text MIFlu**; and any other LLM backbone without text | **this is where `no-text` now lives** |
| **3. Dedicated / non-LLM** | NLinear, DLinear, PatchTST-inspired, iTransformer | no pretrained LLM |
| **4. Naive references** | Last Value, leakage-safe Seasonal Naive | deterministic |

### The correction that matters most

> A no-text MIFlu that retains the GPT-2 forecasting backbone is **LLM-based unimodal**.
> It is **not** a non-LLM model.

Earlier reporting kept `notext` outside both groups (safe, but imprecise). Under the
four-category scheme it belongs to category 2 explicitly. **Counting it as non-LLM would
inflate the non-LLM group with a model that contains an 82.7 M-parameter pretrained
transformer.**

---

## 4. Trainable parameters (measured)

| Model | Trainable (L=24) | Note |
|---|---:|---|
| corrected MIFlu | 1,030,056 | GPT-2 frozen; LoRA `c_attn` r=4 + head |
| no-text MIFlu | 1,028,520 | same minus the text path |
| Qwen Time-LLM | 370,376 | frozen 1.5 B base; adapter + head only |
| CALF | 1,981,608 | |
| TimeCMA | 1,391,016 | |
| PatchTST | 87,256 | |
| iTransformer | 75,672 | |
| DLinear | 5,040 | |
| NLinear | 2,520 | |

**A million trainable parameters is not a million-parameter model.** For the Qwen arm in
particular, 370 k trainable sits on top of a frozen 1.5 B backbone, so "370 k parameters"
in a table would be misleading unless the base is named in the same row.

---

## 5. What must accompany every model in the A2-F report

Per `A2F_FAIR_COMPARISON_CONTRACT.md`: source repository · source commit · local
modifications · canonical/adapted/inspired/reconstructed status · architecture ·
pretrained backbone · text usage · total parameters · trainable parameters ·
input/output contract · dataset · target · checkpoint-selection rule · evaluation
contract · independent-score status.

All of these are populated in `A2F_MODEL_ELIGIBILITY_MATRIX.csv`.

---

## 6. Standing caveats

1. `scripts/miflu_model.py` carries **uncommitted changes**, and the repository has a
   single commit, so the exact training-time code version is **not recoverable from git**.
2. PatchTST must **never** be called canonical without a new implementation.
3. CALF / TimeCMA / Qwen must **never** be called official.
4. HISTORICAL Track-B artifacts must **never** be used as A2-F results
   (`TRACK_SEPARATION_RULES.md`).
5. DeepSeek is excluded by the brief and is not present.