# Track C PTE / PIE 峰值评估报告（中文）

*补充指标，不影响 Test MSE 冠军赛结果。数值来自冻结的 Test 预测；未重新训练。*
*合同见 `TRACK_C_PEAK_CONTRACT.md`；逐峰数据见 `TRACK_C_PTE_PIE_PER_EVENT.csv`；逐模型见 `TRACK_C_PTE_PIE_PER_MODEL.csv`；判定矩阵见 `TRACK_C_PTE_PIE_PASS_MATRIX.csv`。*

## 1. 定义

- **PTE（峰值时间误差）** = |预测峰值周 − 真实峰值周|，单位：周。
- **PIE（峰值强度误差）** = |预测峰值强度 − 真实峰值强度| / 真实峰值强度，单位：%。
- 主峰目标 = **ILITOTAL**（流感活动量，病例数），物理单位反变换使用 Train-only 缩放器。

## 2. 判定标准（文献）

| 标准 | PTE | PIE | 来源 |
|---|---|---|---|
| **文献标准** | ≤ 1 周 | ≤ 25 % | Kramer & Shaman 2019, PLOS Comput Biol (DOI 10.1371/journal.pcbi.1006742)；与 CDC "Predict the Influenza Season Challenge" 同口径 |

> 两条件**同时满足**才记为一次峰值命中（按峰判定，不按均值）。"Peak Hit Rate ≥ 0.75" 等数字**不是** MIFlu 论文标准，已于历史报告订正移除。

## 3. 八模型结果（3 种子 × 4 horizon，每模型 36 个真实峰）

| 模型 | 真实峰 | 文献命中 (PTE≤1 & PIE≤25) | 文献率 | 平均 PTE(周) | 平均 PIE(%) |
|---|---:|---:|---:|---:|---:|
| **miflu（MSE 冠军）** | 36 | 15 | 41.7 % | 0.29 | 25.0 |
| **nlinear** | 36 | 36 | **100.0 %** | 0.28 | 3.14 |
| **dlinear** | 36 | 31 | 86.1 % | 0.92 | 17.72 |
| timecma_llm | 36 | 0 | 0.0 % | 1.38 | 50.44 |
| patchtst | 36 | 0 | 0.0 % | 0.67 | 66.61 |
| itransformer | 36 | 0 | 0.0 % | 0.72 | 66.16 |
| qwen_time_llm | 36 | 1 | 2.8 % | 0.96 | 36.33 |
| calf_llm | 36 | 0 | 0.0 % | 0.93 | 81.25 |

## 4. 关键发现

1. **MSE 冠军 ≠ 峰值冠军。** MIFlu 在 Test MSE 上排名第一，但峰值命中率仅 **41.7 %**，
   不满足文献峰值准则（主要受制于个别峰的 PIE 略超 25 %）。
2. **NLinear 同时满足文献两项准则（36/36，100 %）**，是本次八模型中的最佳峰值模型；DLinear 次之（86.1 %）。
3. **四个 LLM 侧模型（timecma / patchtst / itransformer / calf）峰值命中率均为 0 %**，
   qwen_time_llm 仅 2.8 %——LLM 侧模型在峰值强度上系统性高估（平均 PIE 50–81 %）。
4. **MSE 排名与峰值排名不同，但二者不冲突**：PTE/PIE 是季节/临床补充指标，
   Track C 冠军仍以一次 Test MSE 为准（MIFlu）。

## 5. 与最终报告的关系

- PTE/PIE 是 MSE 冠军赛的**补充指标**，用于回答"模型能否准确刻画流感峰"，不改变 Test 排名。
- 本评估仅采用文献标准作为峰值命中判定，不引入任何项目自定义门槛。
- Track C Test 窗口（2016-2020）不覆盖 2021 高 ILI 异常，故峰值评估不含 2021 幻觉峰（见 `TRACK_C_COVID_PERIOD_ANALYSIS.md`）。
