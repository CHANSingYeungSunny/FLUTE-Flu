# TRACK SEPARATION RULES

Generated 2026-10-06. Append-only.

## 1. The separation is anchored to one date

```
2026-09-24 09:54:29 +0800   author repo clone (recovery/author_repo/.git/logs/HEAD)
```

* Everything produced **before** it is Historical Track B and uses the **self-built**
  implementation.
* Everything produced **after** it uses the **author's** repository as the basis.

This boundary is **filesystem-proven**, and the brief's account of the ordering is
**corroborated** rather than merely accepted: every `innovation_deploy_root_v3_*`
directory has its latest file mtime between **2026-09-16** and **2026-09-21**, i.e.
strictly before the clone. (`HISTORICAL_TRACK_B_DEPLOYMENT_INVENTORY.csv`.)

## 2. Hard rules

| # | Rule |
|---|---|
| R1 | Historical Track B results may never be averaged, ranked or tabulated together with A0-R, A1-P or A2-F results. |
| R2 | A Track-B checkpoint may never be scored as an A0-R / A1-P / A2-F result. |
| R3 | A model from the author's repo being present does **not** make any other model (NLinear, DLinear, PatchTST, iTransformer, Qwen Time-LLM, CALF, TimeCMA) an "official implementation". Each keeps its own provenance label. |
| R4 | A no-text MIFlu that retains the GPT-2 forecasting backbone is **LLM-based unimodal**. It is not a non-LLM model and must never be counted in the non-LLM group. |
| R5 | The July-2026 1025-row dataset is a **dataset track**, orthogonal to the codebase lineages. Crossing it with a codebase lineage produces a new, separately-labelled track. |
| R6 | Default cross-track compatibility verdict is `INCOMPATIBLE_ACROSS_TRACKS_UNLESS_PROVEN_OTHERWISE`. An exception needs an evidence-backed entry in `CROSS_TRACK_COMPATIBILITY_MATRIX.csv`. |
| R7 | Absolute MSE values from different tracks are never compared. Only within-track comparisons carry meaning. |
| R8 | The exposed Test set stays labelled **retrospective**; renaming an old interval does not create a fresh holdout. |

## 3. What each track may and may not support

| Track | May support | May NOT support |
|---|---|---|
| Historical Track B | statements about the self-built implementation and its deployment | any claim about the author's code or the paper |
| A0-R | statements about **what the released code does** (including its defects) | claims of paper reproduction, clean holdout, or fair benchmarking |
| A1-P | the paper-reproduction attempt, with its reconstruction ledger disclosed | claims about released-code behaviour |
| A2-F | the fair LLM vs non-LLM comparison under the shared contract | claims of paper reproduction |

## 4. Enforcement

Every new result table must carry a `track` column whose value is exactly one of
`A0-R`, `A1-P`, `A2-F`, `Historical_Track_B`, `July2026_dataset`. Tables that would mix
values must be split. `CROSS_TRACK_COMPATIBILITY_MATRIX.csv` records, field by field,
why a cross-track comparison is or is not admissible.
