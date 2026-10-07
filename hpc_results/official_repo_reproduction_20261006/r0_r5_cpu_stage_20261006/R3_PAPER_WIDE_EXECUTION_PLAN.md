# R3 — PAPER-WIDE EXECUTION PLAN

Generated 2026-10-06. A specific plan for every inventoried paper result.

## 1. What R3 must decide

For each paper item: can it be reproduced, and if not, what exactly blocks it. **An
unreleased Tier-3 dataset must not block the controlled MIFlu replacement indefinitely** —
it gets its own blocked verdict instead.

## 2. Main National-Illness results (Table V)

| Aspect | Plan |
|---|---|
| author-generated cells | **MIFlu's column only** — 8 cells (4 horizons x MSE/MAE). Target values **PDF-verified and Markdown-cross-verified** |
| required code path | the **R1-B** implementation (seven channels, prefixed text, LoRA, effective freeze) |
| target contract | seven variables, z-space, mean over origins x leads x variables |
| repetitions | the paper states **10**; R1-B's pilot runs **1**, and the expansion is a separate authorization |
| predicted outputs | 7-channel NPZ per (horizon, repetition) |
| metric aggregation | equal weight over the four horizons — verified arithmetically |
| directly reproducible? | **yes, on a reconstructed contract** — with pooling axes permanently unknown |
| cited baseline cells | **11 columns x 8 rows = 88 cells** are `CITED_BASELINE_RESULT`. **Not reproduced.** The paper says they are taken from refs [9] and [14] |
| Fig. 3 | derived: it is the 4-horizon mean of Table V, so it is regenerable **from Table V alone** once the numbers exist |

## 3. Regional forecasting (Table VI)

| Aspect | Finding |
|---|---|
| is the data released? | **NO** — the US-Region dataset is not in the released tree |
| preprocessing released? | no |
| target definitions / region definitions | described in the paper, not shipped |
| code path | the released repo has no regional entry point |
| **verdict** | **`BLOCKED_BY_MISSING_DATA`**; does **not** block the replacement |

## 4. Textual-input-embedder comparison (Table VII)

| Aspect | Plan |
|---|---|
| compared embedders | GPT-2 (MIFlu), LLaMA2-7B, BERT, and **X = "did not use textual input embedder"** |
| invariant | **only the textual embedder may vary** — the forecasting backbone, prompt, LoRA, seeds, horizons and metric stay fixed |
| consistency check the paper itself provides | the **X row's values equal Table V's GPT4TS column exactly** (verified in the inventory) — a free correctness check on the transcription |
| cost | 4 variants x 4 horizons x 10 reps = **160 fits** for a full run; a 1-rep pilot is 16 |
| verdict | `NOT_YET_RUN` |

## 5. Ablation study (Table VIII)

Seven variants with averages over L=24/36/48/60: full MIFlu 1.436/0.745 · w/o dataset 1.473/0.770 ·
w/o task 1.465/0.759 · w/o input-variable description 1.538/0.779 · w/o LoRA 1.570/0.794 ·
w/o multimodality 1.647/0.816 · w/o LoRA+multimodality 1.925/0.904.

**Each switch must be verified to function before its ablation counts**: per-variant trainable
parameter names, total/trainable counts, the active-text-path verdict, the LoRA-installation
verdict and the freezing verdict. **An ablation switch that does not function is not a
reproduced ablation** — that is exactly the released-code situation.

## 6. Sensitivity analyses (Figs 5, 6)

| Figure | Factor | Range | Dataset | Status |
|---|---|---|---|---|
| Fig. 5 | window size **T** | 10–50 | **US-Region, L=20** | `BLOCKED_BY_MISSING_DATA` |
| Fig. 6 | GPT-2 layers **K** | 1–7 | **US-Region, L=20** | `BLOCKED_BY_MISSING_DATA` |

**Both sensitivity studies are regional.** They cannot be run without the US-Region dataset,
and they must **not** be silently re-scoped onto the national data. One factor varies at a
time; all others fixed; matched repetitions; raw outputs saved.

## 7. Runtime and resource results (Table IX)

ReILIF **130 min**, MIFlu **119 min** — on an RTX 3090, regional. The HPC is an A100, so
**exact time equality is not required**; the verdict is `HARDWARE_NORMALIZED_ONLY`. Record
wall time, GPU-hours, peak VRAM, total/trainable parameters and checkpoint size.

## 8. Few-shot forecasting (Fig. 7)

| Aspect | Finding |
|---|---|
| training fractions | `UNRECOVERED` |
| chronological or random subsampling | `UNRECOVERED` |
| validation/Test definition, repetition count, plotted uncertainty | `UNRECOVERED` |
| **verdict** | **`BLOCKED_BY_MISSING_CONFIGURATION`** |

## 9. Ordering and gates

```
1. R1-B pilot (Tier-1)                     <- blocked on GPU authorization only
2. 10-repetition expansion                 <- only if the pilot is valid
3. Table VIII ablations                    <- needs 6 working switches
4. Table VII embedder comparison           <- needs 3 alternative embedder assets
5. Table IX runtime                        <- HARDWARE_NORMALIZED_ONLY
6. Table VI / Figs 5-6 / Fig 7             <- BLOCKED, do not block 1-5
```
