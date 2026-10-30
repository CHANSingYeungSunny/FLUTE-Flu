# GLOSSARY — 零基础术语表

> Terms in this project + in the MIFlu paper, explained for a reader with no background.
> 中英对照，按主题分组。

## 1. The task / 任务

| Term | Meaning |
|------|---------|
| **ILI** | Influenza-like illness — patients seeing a doctor with flu-like symptoms. Not lab-confirmed flu. |
| **ILI forecasting** | Predicting future weekly ILI counts. Here: US national, weeks ahead. |
| **National-Illness dataset** | Author's 966-row, 7-variable US national ILI series (2002–2021). The official data of this project. |
| **US-Region dataset** | 10 US HHS regions' ILI (1997–2020). Used by the paper; NOT reproduced here. |
| **ILITOTAL** | Variable 5 of the dataset = total ILI patient count (the peak-audit target). |
| **OT** | Variable 7 = total patient visits (the denominator of ILI percentages). |
| **MMWR epiweek** | CDC's official surveillance week calendar. Note: the author CSV's `date` column is a **synthetic** 7-day index, not real epiweeks. |
| **Vintage** | Which snapshot/revision of a data series. Two vintages exist here (author 2023-era 966 rows vs 2026-07 FluView 1025 rows) — values differ from MMWR 2016w40 onward. |

## 2. Time-series forecasting / 时序预测

| Term | Meaning |
|------|---------|
| **T (input window / seq_len)** | How many past weeks the model looks at. Here **T = 104** (2 years). |
| **L (horizon / pred_len)** | How many future weeks to predict. Here **L ∈ {24, 36, 48, 60}** (6–15 months). |
| **Multivariate / features=M** | Predicting all N variables together (N = 7) from all N variables. |
| **Train/Val/Test split** | Chronological 70:10:20 = 676/97/193 rows. Val picks checkpoints; Test is scored **once**. |
| **Strict containment** | The Test target rows must not include any Train/Val rows. The old 1025-row window contract violated this; the current contract fixes it. |
| **Seed** | Random-number seed; same config + different seeds = slightly different results. Report mean ± SD over seeds. |
| **Repetition** | The paper averages 10 runs; our championship uses 3 seeds (42/43/44). |

## 3. Metrics / 指标

| Term | Meaning |
|------|---------|
| **MSE** | Mean squared error. Sensitive to big mistakes (e.g. wrong peak intensity). Lower = better. **MSE is not accuracy.** |
| **MAE** | Mean absolute error. Typical size of a miss. Lower = better. |
| **z-space / normalized space** | Errors computed after StandardScaler normalization (the paper's national-task convention). Not the same as physical-unit errors. |
| **RMSE / PCC** | Regional-task metrics (root MSE / Pearson correlation). Not used in our national benchmark. |
| **PTE** | Peak Timing Error = \|predicted peak week − true peak week\| (weeks). |
| **PIE** | Peak Intensity Error = \|predicted − true peak intensity\| / true peak intensity (%). |
| **Literature peak criterion** | A peak counts as **hit** only if **PTE ≤ 1 week AND PIE ≤ 25%** simultaneously, judged per peak (Kramer & Shaman 2019). |
| **±0.10 band** | Pre-declared tolerance for paper reproduction (5% of the paper MSE). Not met → PARTIAL_REPRODUCTION. |

## 4. The MIFlu model / 模型

| Term | Meaning |
|------|---------|
| **LLM** | Large language model (here GPT-2). |
| **Textual input embedder** | Turns a text prompt (dataset info + variable stats + expert knowledge) into vectors, using a **frozen** full GPT-2. |
| **Prompt template** | `[Dataset information] + [Input variable description (Max/Min + domain knowledge)] + [Task instruction]`. |
| **Time-series input embedder** | reversible **instance norm** → **patching** → trainable **linear embedder**. |
| **Instance norm (reversible)** | Subtract mean, divide by std per variable; invertible, so predictions can be mapped back to physical units. |
| **Patching** | Cutting the time axis into overlapping patches (here length 24, stride 2) so each patch becomes one LLM token. |
| **Forecasting LLM** | First **K=6** GPT-2 layers consuming the fused [text; time] embeddings. |
| **LoRA / PEFT** | Low-Rank Adaptation: tiny trainable matrices (rank r=4) inserted in parallel to attention weights; the rest of the LLM stays frozen. PEFT = parameter-efficient fine-tuning. |
| **Output projection** | Final linear layer turning LLM hidden states into numbers (the forecast). |
| **Multimodal** | Using two modalities: text + time series. |
| **GPT4TS** | The unimodal baseline (GPT-2 on time series only, no text path). |
| **Ablation (notext)** | Same model with the text path switched off — used to test whether text helps (see hard constraint #2: unresolved). |

## 5. Our experiment framework / 实验框架

| Term | Meaning |
|------|---------|
| **Track C** | The strict 966-row 8-model Test championship (frozen contract; the authoritative benchmark). |
| **Track R / R1-B / R1-C** | Paper-reproduction runs against the author's repo (R1-C = 24 fits, 3 seeds, final). |
| **Track H** | Historical 1025-row experiments (superseded; background only). |
| **Track S** | Early-stopping sensitivity check (supplementary; does not change the champion). |
| **Canonical scorer** | The single independent scoring script all models are compared with (z-space). |
| **Train-only scaler** | Normalization fitted on Train rows only, then applied to Test (no leakage). |
| **8-model championship** | 4 non-LLM (NLinear, DLinear, PatchTST, iTransformer) + 4 LLM-side (MIFlu, TimeCMA-LLM, Qwen-Time-LLM, CALF-LLM). |
| **LLM-side vs non-LLM** | MIFlu's backbone is GPT-2 → MIFlu counts as LLM-side. Group means are reported 4 vs 4. |
| **Champion / 冠军** | Best model on one-time Test `average_MSE_4L` under the frozen contract. |
| **PARTIAL_REPRODUCTION** | Reproduction verdict: directionally close but outside the 5% tolerance. |
| **SUPERSEDED / COMPREHENSIVE / AUTHORITATIVE** | Report authority labels: old → evidence → current (see `docs/EVIDENCE_INDEX.md`). |
| **Frozen / 冻结** | Contract, predictions, or data locked before evaluation so results can't be tuned post-hoc. |

## 6. Reading numbers safely / 安全引用数字

- Always quote **track + seed count + space** (e.g. "A-track, 3 seeds, z-space MSE").
- Never compare A-track (966 rows) with B-track (1025 rows) numbers.
- Never compare z-space MSE with physical-unit peak errors.
- "MSE champion" and "peak champion" are different statements about different strengths.
