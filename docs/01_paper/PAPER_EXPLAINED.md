# MIFlu 论文解读 / Paper Explained

> **What this is / 这是什么**：对 IEEE JBHI 2025 论文 *MIFlu: Large Language Model-Based
> Multimodal Influenza Forecasting Scheme*（DOI 10.1109/JBHI.2025.3561214）的零基础解读。
> 全文在 `reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md`。
> English body first; key points also in Chinese.

---

## 1. One-paragraph summary / 一段话总结

MIFlu forecasts weekly US influenza (ILI patient counts) up to 60 weeks ahead. Its key idea:
**let a text prompt carrying dataset statistics + expert domain knowledge be encoded by one LLM
(text embedder), fuse those text embeddings with patched time-series embeddings, and feed the
fusion to a second autoregressive LLM (GPT-2 + LoRA) that outputs the forecast.** Claimed result:
best MSE/MAE on the National-Illness benchmark vs 12 baselines (improvement up to 26.2%).

> 中文要点：MIFlu 用两个 LLM 做流感预测——一个把"数据描述+专家知识"的文本 prompt 编码成文本嵌入，
> 与时序嵌入拼接后送入第二个 LLM（GPT-2 + LoRA 微调）输出未来 24–60 周的 ILI 患者数。
> 论文称在 National-Illness 上全面超过 12 个基线（最多提升 26.2%）。

## 2. High-level design / 高层设计（三模块，对应论文 Fig. 1）

| # | Module | What it does | Trainable? |
|---|--------|--------------|-----------|
| 1 | **Textual input embedder** | Prompt → tokenizer → **frozen full GPT-2** → `h_text ∈ R^(len(token) × D)` | ❌ frozen |
| 2 | **Time-series input embedder** | Reversible **instance norm** → **patching** (patch len `Lp`, stride `S`) → **linear embedder** → `h_time ∈ R^(num_patches × D)` | ✅ linear layer |
| 3 | **Forecasting LLM** | Concat `[h_text; h_time]` → first **K layers of GPT-2** with **LoRA (r=4)** on the multi-head-attention (target `c_attn`), trainable positional encoding + LayerNorm, frozen FFN → output projection → forecast | ✅ LoRA + PE + LN + output head |

- **Why two LLMs?** The text embedder is kept *frozen and full-size* so its knowledge aligns with
  the forecasting LLM's (same GPT-2 family); only the forecasting side is adapted.
- **Why LoRA?** Fine-tuning full attention/FFN on ~966 weekly points causes catastrophic forgetting;
  LoRA adds small parallel low-rank adapters (rank r = 4) only to attention, preserving pre-trained
  knowledge and inference speed.
- **Why patches?** ILI has strong annual seasonality; patching (`Lp=24`, `S=2` for national) keeps
  short-term shapes and cuts sequence length (LLM cost).

> 中文要点：①文本嵌入器（冻结的完整 GPT-2）；②时序嵌入器（可逆 instance norm → patch 切分
> （国家任务 patch 长 24、步长 2）→ 可训练线性层）；③预测 LLM（GPT-2 前 K=6 层 + LoRA r=4
> 挂在注意力层，位置编码与 LayerNorm 可训练，FFN 冻结，最后线性投影出预测）。

## 3. Text prompt template / 文本模板（论文 Table I）

```
[Dataset information]
<Description of dataset>
Below (1) to (N) is the information about each feature:
***
[Input variable description]
(1) <Description of variable 1> + <Statistics: Max, Min> + <Domain knowledge from experts/users of variable 1>
...
(N) <Description of variable N> + <Statistics: Max, Min> + <Domain knowledge of variable N>
***
[Task instruction]
Predict the next <L> steps given the previous <T> steps for the information attached.
```

The prompt is **static per dataset** (statistics + user's knowledge, e.g. yearly peak counts and
trend description). This is the handle the paper suggests for injecting *user's prior knowledge*.

## 4. Predictive workflow / 预测工作流（一张图看懂）

```
X ∈ R^(N×T)  (N variables × T=104 past weeks)
   │  reversible instance norm (per variable)
   │  patching: patch Lp=24, stride S=2 → num_patches ≈ ⌊(T−Lp)/S⌋+2
   │  linear embedder (trainable)
   ▼
h_time  (num_patches × D)
                    ┐
prompt → tokenizer  ├─ concat → h_fuse (len(token)+num_patches, × D)
→ frozen GPT-2      │            │
   ▼                │            ▼  first K=6 GPT-2 blocks (+LoRA r=4 on attn Q/K)
h_text (len(token)×D)┘      h_forecast (same length)
                               │  drop the text-token positions
                               ▼
                        output projection (linear)
                               ▼
                     Ŷ ∈ R^(N×L),  L ∈ {24, 36, 48, 60}
```

- Regional task differs: predicts only the next `L` weeks of ILI in each region (output shape
  `R^L` per region), `K=4` layers, `Lp=4`, `S=2`.
- Autoregressive LLM semantics: input and output token positions line up 1:1, so the text part of
  the output is discarded and only the patch positions are projected to numbers.

## 5. Data splitting / 数据切分（复现的锚点）

| Dataset | Content | Rows/Range | Split | Sizes used here |
|---------|---------|-----------|-------|-----------------|
| **National-Illness** | 7 national ILI variables (US) | 966 rows, 2002–2021 | **70 : 10 : 20** | 676 / 97 / 193 |
| **US-Region** | 10 HHS regions' ILI | 1997w40–2020w18 | **50 : 10 : 40** | — (not reproduced here) |

**National-Illness 7 variables** (Table II): 1) %ILI visits (weighted) 2) %ILI visits (unweighted)
3) ILI count age 0-4 4) age 5-24 5) **total ILI count** 6) number of providers 7) total patient
visits (the denominator). Window `T = 104` weeks (2 years), horizons `L = 24/36/48/60` weeks
(≈6/9/12/15 months ahead) — i.e. **long-term** national forecasting.

> 中文要点：National-Illness 共 966 行、7 个变量，按 70:10:20 切为 676/97/193；
> 输入窗 T=104 周，预测步长 L∈{24,36,48,60} 周；**注意作者 CSV 的 date 列是合成等距标签
> （2002-01-01 起每 7 天一行），不是真实 CDC 观测周**。

## 6. Metrics & training config / 指标与训练配置

- **National task**: MSE + MAE **in StandardScaler-normalized space** (paper Eqs. 3–4). MSE is
  peak-intensity-sensitive; MAE is the general level error. *MSE is not accuracy.*
- **Regional task**: RMSE + PCC after de-normalization (paper Eqs. 5–6).
- Config (paper Table IV): epochs **20**, batch **16**, lr **5e-4**, `T=104`, `L=24/36/48/60`,
  GPT-2 first **K=6** layers, LoRA **r=4**, patch **Lp=24**, stride **S=2**, textual embedder =
  **full GPT-2**; result = **mean of 10 repetitions**; Python 3.9.18 + PyTorch 2.1.0 + RTX 3090.

⚠️ **Repo default ≠ paper setting** (see `AUTHOR_REPO_EXPLAINED.md`): the released
`main_ILI_lora.py` argparse defaults differ (e.g. lr 1e-4, epochs 1, lradj `type1`), so paper
numbers require explicitly passing Table IV values.

## 7. Paper's headline result / 论文核心结果（Table V, national）

| L | MIFlu MSE | MIFlu MAE | Best baseline MSE | Note |
|---|-----------|-----------|-------------------|------|
| 24 | 1.542 | **0.726** | PatchTST 1.319 | only MSE loss to a baseline |
| 36 | **1.422** | **0.779** | PatchTST 1.430 | |
| 48 | **1.414** | **0.757** | PatchTST 1.553 | |
| 60 | **1.364** | **0.719** | PatchTST 1.470 | |
| **avg** | **1.4355** | 0.745 | — | the "paper target" of our reproduction |

Baselines: GPT4TS, DLinear, PatchTST, TimesNet, FEDformer, Autoformer, Stationary, ETSformer,
LightTS, Informer, Reformer (all national numbers taken from GPT4TS paper [9] per paper's Section V-C).

## 8. What our project reproduces / 本项目复现范围

- **Scope**: National-Illness only (US-Region tables are blocked: author artifact unavailable).
- **Our MIFlu final Test result** = Test average_MSE_4L = **1.8652** vs paper target **1.4355**
  (+29.9%) → verdict **PARTIAL_REPRODUCTION** (5% tolerance not met; optimizer/scheduler/seeds
  not fully disclosed by the paper/repo). Framing rule: only this unified pair is compared in the
  report — no scheduler-variant comparisons.
- **Championship context**: an 8-model benchmark (4 non-LLM: NLinear, DLinear, PatchTST,
  iTransformer; 4 LLM-side: MIFlu, TimeCMA-LLM, Qwen-Time-LLM, CALF-LLM) under a frozen strict
  966-row contract; MIFlu is the Test-MSE champion (1.8652) but NOT the peak-accuracy champion
  (NLinear hits 36/36 literature PTE/PIE peaks vs MIFlu 15/36). MSE ≠ accuracy.

## 9. Glossary picks / 关键词速查

See `docs/GLOSSARY.md` for the full list. Core: **PEFT/LoRA** (lightweight adapters on frozen LLM),
**instance norm** (reversible per-variable normalization), **patching** (overlapping time patches as
tokens), **PTE/PIE** (peak timing/intensity error, literature criterion ≤1 week & ≤25%),
**z-space MSE** (MSE after StandardScaler normalization — the national-task metric space).
