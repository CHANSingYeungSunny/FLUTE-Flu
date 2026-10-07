# IMPLEMENTATION IDENTITY

日期：2026-10-06
规则：**每个模型必须标明是 canonical / adapted / inspired / reconstructed。** 没有证据支持的「官方实现」主张一律禁止。

---

## 0. 一句话

**八个模型里，只有 NLinear 是 canonical 实现，MIFlu 是修正重构（reconstructed），PatchTST 是 inspired（不是 canonical），其余为自研重实现或 inspired 变体。** 换回官方仓库**不会**让其他模型自动变成「官方正确实现」。

---

## 1. 逐模型身份表

### Track A（作者 966 行数据，z 空间，3 seeds × 4 horizons）

| 模型 | 族 | 身份 | 源 | 可训练参数 | 输入/输出契约 |
|---|---|---|---|---|---|
| `miflu` | **LLM** | **reconstructed**（修正重构） | `scripts/miflu_model.py`（**有未提交修改**） | 1,030,056（L=24） | in (B,104,7) → out (B,L,7) |
| `notext` | **对照（保留 LLM）** | reconstructed ablation | `scripts/train_ablation.py` | 1,028,520 | 同上；**去文本，保留预测 GPT-2 与 LoRA** |
| `nlinear` | non-LLM | **canonical** | `scripts/innovation/backbones/dlinear.py::NLinear` | 2,520 / 3,780 / 5,040 / 6,300（随 L） | in (B,104,7) → out (B,L,7) |
| `dlinear` | non-LLM | own re-implementation | 同上 `::DLinear` | 5,040 … 12,600 | 同上 |
| `patchtst` | non-LLM | **INSPIRED — 不是 canonical PatchTST** | `scripts/innovation/backbones/patchtst.py::PatchTST` | 87,256 … 114,940 | 同上 |
| `itransformer` | non-LLM | own re-implementation | `scripts/innovation/backbones/itransformer.py::ITransformer` | 75,672 … 78,012 | 同上 |
| `timecma_llm` | LLM | **TimeCMA-INSPIRED** | `scripts/innovation/backbones/llm_inspired.py::TimeCMAInspired` | 1,391,016 … 1,584,804 | 冻结 GPT-2 + 检索对齐 + last-token 分支 |
| `qwen_time_llm` | LLM | **Time-LLM-INSPIRED** | `...::QwenTimeLLM` | 370,376 … 757,700 | 冻结 Qwen2.5-1.5B + patch 原型重编程 + Prompt-as-Prefix |
| `calf_llm` | LLM | **CALF-INSPIRED** | `...::CALFInspired` | 1,981,608 … 2,175,396 | 冻结 GPT-2 + 并行双分支 + 两个对齐损失 |
| `last_value_naive` | baseline | deterministic | `scripts/train_naive_966.py` | 0 | — |
| `seasonal_naive` | baseline | deterministic，**leakage-safe** | 同上 | 0 | lead>52 只重复观测到的最后一个季节周期 |

### Track B（July-2026 1025 行）— 仅作历史轨道

| 模型 | 身份 | 备注 |
|---|---|---|
| `gpt2_miflu` | reconstructed（与 A 轨 `miflu` 同族） | 可训练参数 1,030,056 … 1,223,844 |
| 其余 7 个 | 与 A 轨同名者相同身份 | 10 seeds |

---

## 2. 必须遵守的标注规则

1. **`notext` 不是普通 non-LLM。** 它**保留** GPT-2 预测骨干与 LoRA，只是移除文本通路。把它计入 non-LLM 组会污染组均值。**本报告一律把它列为独立 CONTROL。**
2. **"w/o multimodality" ≠ "没有 LLM"。** 论文 Table VIII 的最后一行的描述是 GPT4TS；移除的是**文本分支**，不是预测用的 GPT-2 本身。
3. **PatchTST 必须写 INSPIRED。** 其 `architecture_report()` 已逐条列出三条偏离。要声称 canonical PatchTST 必须另行实现。
4. **CALF / TimeCMA 必须写 INSPIRED/adaptation。** 核心对齐模块与损失是否与原文一致未经验证。
5. **Qwen Time-LLM 记录了 backbone 身份**：Qwen2.5-1.5B，冻结。**这是 adapter，不是 Time-LLM 官方实现。**
6. **不得**因为本轮换用官方 MIFlu 仓库做基础，就声称其他模型成为「官方正确实现」。它们与官方仓库无关。

---

## 3. 「LLM / non-LLM」分组的两套口径（引用时必须写明用哪套）

| 口径 | LLM 组 | non-LLM 组 | A 轨均值 | B 轨均值 |
|---|---|---|---|---|
| **4 vs 4**（持久化脚本 `recompute_eight.py` 的口径） | `miflu`/`timecma`/`qwen`/`calf` | `nlinear`/`dlinear`/`patchtst`/`itransformer` | **3.861596 vs 3.075638** | **1.242572 vs 1.142408** |
| 3 vs 5（仅 `*_llm` 三个骨干） | `timecma`/`qwen`/`calf` | 上述 4 个 + `miflu` | 4.468288 vs 2.868814 | 1.399805 vs 1.068101 |

> **两个数都对，但口径不同。** 引用时必须写明。Stage-6 报告初版曾把两套混用（已在其 §4.2 注明）。

**`notext` 在任何口径下都不计入任一组** —— 它是控制组，且仍含 LLM。

---

## 4. 组均值的解释边界

- 4 个 / 4 个**固定实现**不是从「所有 LLM 预测器」中的随机样本。
- 因此**不得**把组均值解读为对 LLM / non-LLM **家族**的统计推断。
- 主要结论必须基于**具体模型**与**预先声明的比较**（见 §5）。
- **组均值与组内最优会给出相反印象**（A 轨组内最优是 `notext`，B 轨组内最优是 LLM 的 `gpt2_miflu`）——**只报其一即为选择性报告**。

---

## 5. 预先声明的核心比较

| 优先级 | 比较 | 性质 |
|---|---|---|
| 主 | corrected MIFlu vs matched no-text MIFlu | 机制（文本的边际作用） |
| 主 | corrected MIFlu vs NLinear | 实践（多模态 vs 最简单线性） |
| 次 | 各模型 vs NLinear | 描述性配对 |
| 参考 | Last Value / Seasonal Naive | 廉价参照 |

---

## 6. 证据路径

| 类别 | 路径 |
|---|---|
| 模型实现 | `scripts/innovation/backbones/{dlinear,itransformer,patchtst,llm_inspired}.py` |
| MIFlu 实现 | `scripts/miflu_model.py`（⚠️ 有未提交修改） |
| 消融实现 | `scripts/train_ablation.py` |
| 骨干训练入口 | `scripts/train_backbone_966.py` |
| 确定性基线 | `scripts/train_naive_966.py` |
| 参数记录 | `results/v3_clean/analysis/analysis_dataset.csv`（`trainable_parameters` 列） |
| 身份说明（前序） | `recovery/stage6/cost_and_matrix_zh.md` §1 |
| 分组口径证据文件 | `recovery/stage6/recompute_eight.py` |