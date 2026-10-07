# 结果（稿件可用，中文）

## 主指标口径

依照 MIFlu（IEEE JBHI 2025，§V-B），以归一化（z 空间）MSE 与 MAE 为**主**指标，
物理量纲数值作为补充。

## Test 集精度

| Horizon | NLinear MSE(z) | MIFlu(GPT-2) MSE(z) | 降幅 | NLinear MAE(z) | MIFlu MAE(z) |
|---|---|---|---|---|---|
| L=24 | 4.2966 | 5.6766 | 24.31% | 1.4013 | 1.6186 |
| L=36 | 4.9728 | 6.1983 | 19.77% | 1.5239 | 1.6733 |
| L=48 | 5.4046 | 5.7914 | 6.68% | 1.6058 | 1.5966 |
| L=60 | 5.6085 | 6.6225 | 15.31% | 1.6436 | 1.6948 |

冻结冠军 **nlinear** 在四个 horizon 上的 Test MSE 均**低于**冻结 MIFlu 基线 **gpt2_miflu**，
z 空间 MSE 的观测降幅为 6.68%–24.31%。
MAE 上两臂在 L=48 基本持平，基线略低。

## 统计表述限制（必须保留）

基线仅有 3 个 seed，因此每 horizon 的有效配对样本量为 **3**，而非十个。
对所有配对比较做 Holm 校正后，仅一项达到显著。因此我们只报 **observed best**，
**不声称广泛的统计优越性**。

## 峰值判据

唯一实现并报告的验收标准为文献判据：**PTE ≤ 1 周 且 PIE ≤ 25%**。

| 模型 | L | 平均 PTE（周） | 平均 PIE（%） | 判定 |
|---|---|---|---|---|
| nlinear | 24 | 1.67 | 9.50 | 未达标 |
| nlinear | 36 | 2.00 | 10.57 | 未达标 |
| nlinear | 48 | 0.35 | 3.33 | 达标 |
| nlinear | 60 | 0.15 | 2.08 | 达标 |
| gpt2_miflu | 24 | 4.67 | 72.18 | 未达标 |
| gpt2_miflu | 36 | 5.33 | 77.34 | 未达标 |
| gpt2_miflu | 48 | 2.00 | 25.29 | 未达标 |
| gpt2_miflu | 60 | 2.00 | 23.27 | 未达标 |

NLinear 在 L=48 与 L=60 达标，在 L=24 与 L=36 未达标；冻结 MIFlu 基线在所有
被评估 horizon 上均未达标。

## 命名忠实性

PatchTST 与 iTransformer 骨干为受已发表架构**启发**的重新实现，表述为
「PatchTST-inspired」与「iTransformer-aligned」，不声称官方参考实现。

## 不可用或延迟的候选族

TimesNet、TimeMixer/ModernTCN、TF-IDF+SVD、fastText、BERT/MiniLM、zero-text 与
shuffled-text 负对照、Time-LLM 风格 reprogramming、CALF/TimeCMA 风格对齐，以及
Chronos/TimesFM/Moirai 均**不可用或未完成**，故不作为结果报告。
