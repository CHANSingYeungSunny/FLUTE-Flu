# R3 ABLATION CONTRACTS (Table VIII)

The paper's seven ablation variants, the mechanism each is meant to remove, and the checks
that must pass before a variant counts as reproduced.

**Governing rule: an ablation switch that does not function is not a reproduced ablation.**

| Variant | Intended mechanism removed | Predicted output | Must be verified |
|---|---|---|---|
| **MIFlu (full)** | nothing | 1.436 / 0.745 | 12 LoRA tensors in `c_attn`; text `active`; trainable ~2 % |
| w/o dataset information | the dataset section of the prompt | 1.473 / 0.770 | prompt section actually absent from the encoded text |
| w/o task instruction | the task-instruction section | 1.465 / 0.759 | ditto |
| w/o input variable description | the variable-description section | 1.538 / 0.779 | ditto |
| w/o LoRA | PEFT; fine-tune PE + layer norms only | 1.570 / 0.794 | **0** LoRA tensors; trainable count drops by exactly 73,728 |
| w/o multimodality | the textual embedder; unimodal | 1.647 / 0.816 | no text passed; text-influence probe returns `text_inert` **by construction** |
| w/o LoRA + multimodality | both; **"the same as GPT4TS [9]"** | 1.925 / 0.904 | both of the above |

## Per-variant parameter audit (all seven rows produced)

For each variant record: **trainable parameter names**, total and trainable counts, the
active-text-path verdict, the LoRA-installation verdict and the freezing verdict.

The `w/o LoRA` row is the sharpest test: it must remove **exactly** the 12 `c_attn` LoRA
tensors and nothing else. The Tier-1 job measured the full model at **1,673,496** trainable
with LoRA and **1,599,768** without — a difference of **73,728**, exactly the LoRA count.

## A caveat the paper's own text invites

The last row is described as "the same as GPT4TS [9]" — a **unimodal, no-LoRA** model. So
Table VIII's bottom row removes the textual branch, **not** the forecasting LLM. It therefore
does **not** isolate the value of a pretrained LLM over a matched model with no LLM.

## Status

`NOT_YET_RUN` — needs six working switches and 1 repetition x 4 horizons x 7 variants =
**28 GPU fits** for a pilot-grade ablation.
