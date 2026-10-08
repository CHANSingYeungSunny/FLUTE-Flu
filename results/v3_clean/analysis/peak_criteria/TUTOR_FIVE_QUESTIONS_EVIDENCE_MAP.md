# 导师五大疑问 — 对照 Track C 的证据映射（Evidence Map）

*将每条历史疑问（来源：`MIFlu_导师五大疑问_回复报告.md`，2026-09 证据核实版）映射到当前 Track C 合同，标注其相关性、是否被取代、以及当前证据文件。*

| 疑问 | 原始来源主张 | 原始代码/产物 | 原始数据集 | 指代 1025 行 | 指代 966 行 | 对 Track C 适用 | 是否取代 | 当前 Track C 证据 | 类别 |
|---|---|---|---|---|---|---|---|---|---|
| Q1 聚合策略 | `fixed_step/step=0` 修复跨 lead 平均；论文按 L 分别报 | `scripts/q1_step_sweep.py` · `q1_step_sweep.csv` | 1025/更宽 4368 行（2018–2021 切分） | 是 | 否 | 部分（方法有效，数字不适用） | 否（方法）/ 是（数字） | `TRACK_C` 保留 L24/36/48/60 分别计分；`average_MSE_4L` 为显式汇总 | A+B+C |
| Q2 时间对齐/COVID | Test 覆盖 2018–2021；2021-02-07 幻觉峰 ≈2.2× | `scripts/q2_alignment_check.py` · `q2_alignment_check.csv` | 1025/更宽切分 | 是 | 否 | 否（对 2021 峰） | 是（2021 结论） | `TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv` · `TRACK_C_COVID_PERIOD_ANALYSIS.md` | B+C |
| Q3 缩放器/单位 | Train-only scaler（mean 9368.29/scale 8853.43/train[:717]） | `scripts/q3_scaler_sanity_check.py` · `data/scaler_miflu_national.json` | 1025/717-train | 是 | 否 | 部分（方法有效，数值取代） | 是（数值） | `TRACK_C_SCALER_CONTRACT.md` · `TRACK_C_PHYSICAL_UNIT_SANITY.csv` · `TRACK_C_VARIABLE_LABEL_AUDIT.csv` | A+B+C |
| Q4 训练配方 | 4 配方网格；baseline 最接近论文但差距在噪声内 | `scripts/q4_recipe_comparison.py` · `train_ablation.py` | 1025 行 | 是 | 否 | 否 | 是（被 R1-C 取代） | `R1C_FINAL_VERDICT.md` · `R1C_PAPER_GAP_ANALYSIS.md` | B+C |
| Q5 PTE/PIE 停止准则 | PTE≤1周/PIE≤25%（Kramer&Shaman 2019）；val-loss 早停 | `scripts/compute_miflu_indicators.py` · `scripts/early_stopping.py` | 混合（1025 + Track C） | 部分 | 是 | 是 | 否 | `TRACK_C_PTE_PIE_PASS_MATRIX.csv` · `TRACK_C_PEAK_CONTRACT.md` | A+D |
| Q6 多模态（加分项） | 内部流传"注意力是假的"强形式不成立 | `scripts/q6_text_attention_audit.py` | 1025 行 | 是 | 否 | 仅背景 | 否 | 文献背景（E） | E |

## 类别约定

- **A** — 方法学仍有效（文献或可辩护的工程原则）。
- **B** — 特指 1025 行历史实验（数字/切分不可直接当作 Track C）。
- **C** — 被 strict containment（严格包含）或 R1-C 取代。
- **D** — 需从 Track C 冻结预测重新计算（已完成）。
- **E** — 仅文献/背景（不属于 Track C 结论）。

## 关键事实

1. Q1/Q2/Q3 的原始"代码验证"数字来自**更宽切分或 1025 行实验**，不是 Track C：
   - Q1 的 step 扫描窗口到 2021-07-18（Track C Test 止于 2020-06-30）；
   - Q2 的 2021-02-07 幻觉峰**不在** Track C Test 窗口；
   - Q3 的 mean 9368.29/scale 8853.43/train[:717] 与 Track C 的 9439.84/9003.15/[0,676) **不同**。
2. Q4 的 1025 行配方网格已被 **R1-C**（官方仓库复现，3 种子 24 拟合）取代，作为论文复现的权威证据。
3. Q5 的 PTE/PIE 与停止准则已在 Track C 上**重新计算**：文献准则 PTE≤1周&PIE≤25% 下 NLinear 36/36(100%)、MIFlu 15/36(41.7%)；停止准则（Track S 早停）与固定 20 epoch 等价（11/12 相同）。
