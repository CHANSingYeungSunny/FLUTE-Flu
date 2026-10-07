# TRACK C — 冠军报告（中文）

`AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP`
生成于 2026-10-07，全部数值取自已验证的结果文件，无任何手写数字。

---

## 结论

**冠军：官方仓库修正版 MIFlu。**
作者 966 行数据、严格包含窗口、匹配种子 42/43/44、一次性测试集评价：
四 horizon 等权平均 **MSE = 1.8652**（标准差 0.0916），**MAE = 0.8842**。

该模型在 **L=24/36/48/60 四个 horizon 上全部排名第一**
（1.9686 · 1.9332 · 1.7547 · 1.8042），冠军不依赖平均值掩盖局部落后。

## 最终测试集排名

| 排名 | 模型 | 阵营 | 平均 MSE₄ₗ | 标准差 | 平均 MAE₄ₗ |
|---:|---|---|---:|---:|---:|
| 1 | **MIFlu（官方仓库修正版）** | LLM | **1.8652** | 0.0916 | **0.8842** |
| 2 | NLinear | 非 LLM | 2.0495 | 0.0299 | 0.9566 |
| 3 | DLinear | 非 LLM | 2.3478 | 0.0040 | 1.0884 |
| 4 | TimeCMA-LLM | LLM | 2.6700 | 0.0177 | 1.0927 |
| 5 | PatchTST | 非 LLM | 3.9205 | 0.0543 | 1.3826 |
| 6 | iTransformer | 非 LLM | 3.9847 | 0.0317 | 1.3545 |
| 7 | Qwen-Time-LLM | LLM | 5.2196 | 0.0701 | 1.5784 |
| 8 | CALF-LLM | LLM | 5.5153 | 0.0307 | 1.6080 |

按 MAE 排序次序与 MSE 完全一致。

## 配对统计（diff = MIFlu − 对手；仅当 diff < 0 时 MIFlu 获胜）

| 对手 | 平均差异 | MIFlu 胜 | 对手胜 |
|---|---:|---:|---:|
| NLinear | −0.1844 | **11 / 12** | 1 |
| DLinear | −0.4827 | 12 / 12 | 0 |
| TimeCMA-LLM | −0.8049 | 12 / 12 | 0 |
| PatchTST | −2.0553 | 12 / 12 | 0 |
| iTransformer | −2.1195 | 12 / 12 | 0 |
| Qwen-Time-LLM | −3.3544 | 12 / 12 | 0 |
| CALF-LLM | −3.6501 | 12 / 12 | 0 |

NLinear 一行为完整性校验：差异符号与胜场计数一致，且确有 1 个单元格由 NLinear 获胜。
若出现反向计数缺陷，此处将显示为 1/12。

## 必须同时保留的两个结论

1. **修正版 MIFlu 是最佳单一模型**；
2. **非 LLM 侧组平均优于 LLM 侧组平均** —— 非 LLM **3.0756**，LLM **3.8175**。

两者不矛盾：MIFlu 是 LLM 侧唯一强于任一非 LLM 模型的成员，
而 Qwen-Time-LLM（5.2196）与 CALF-LLM（5.5153）拉低了 LLM 组均值。

## 契约与门禁

- 数据集 sha `2a96dfed…ebfe5`，966 行，划分 **676 / 97 / 193**，T = 104
- 严格包含；起点数 549/74/170 · 537/62/158 · 525/50/146 · 513/38/134
- 规范键集 SHA `4ad79bb1…d1961`；重复键 **0**
- **种子 42 门禁：22 项通过 / 0 项失败**
- **评分器：96 个单元格全部计分，0 个被拒**
- 任何单元格在训练期间均未读取 Test（`test_access_during_fit = False`）
- 单元格分类：84 个 `RESCORE_ONLY`，12 个 `GPU_RETRAIN`

### 被拒绝的产物

stage-6 的 `pred_miflu_*` 通过了全部结构性检查，仍被判定不可用：它与 A2 产物
逐字节相同（sha256 `76b81b5b0dfa5bde`），即项目自建重构版，而非官方仓库实现。
**键兼容不等于实现身份。** 因此 12 个 MIFlu 单元格全部重新训练。

## 成本与存储

- 12 个 GPU 作业，共 **1.5083 GPU 小时**，全部退出码 0
- 评分与门禁为 CPU-only 作业，不占 GPU 小时
- 配额（取自 `mmlsquota`，非文件系统空闲空间）：
  home **31 / 50 GB**（余量 19 GB）；scratch **285 / 300 GB**（余量 15 GB）；
  两者 grace 均为 `none`
- checkpoint 仅保留锁定式格式（每单元格约 6.7–9.8 MB），不保留逐 epoch 与优化器状态

## 局限性

- 结论仅适用于本数据集、本划分、本窗口规则、本种子集合与本 checkpoint 策略
- 三个种子可给出标准差，但不足以支撑强显著性主张；本报告不宣称 p 值
- horizon 之间并非相互独立的重复实验
- `qwen_time_llm` / `calf_llm` / `timecma_llm` 为「受启发的简化实现」
  （冻结骨干 + 命名组件契约），**并非**已发表系统的复现，
  故「LLM 侧偏弱」的表述限于本实验实现口径
- MIFlu 的论文级复现结论仍为 **`PARTIAL_REPRODUCTION`**；
  赢得 Track C 并不等于「论文已复现」

## 轨道隔离

| 轨道 | 内容 | 是否为冠军 |
|---|---|---|
| H | 1025 行历史受控替换，旧自建 MIFlu，划分跨界污染 | 否 —— `PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE` |
| R | 作者 966 行 R1-B 论文复现 | 否 —— `PARTIAL_REPRODUCTION` |
| **C** | **本报告** | **是** |

绝对 MSE 数值一律不跨轨道比较。

## 受阻的论文表图（状态未变）

- Table VI（US-Region）—— `BLOCKED_BY_MISSING_DATA`
- Fig. 7（few-shot）—— `BLOCKED_BY_MISSING_CONFIGURATION`
- Table III —— 仅 US-Region，源 PDF 不可读