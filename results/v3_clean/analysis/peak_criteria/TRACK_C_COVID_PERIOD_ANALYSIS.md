# Track C 时间对齐与 COVID 分布偏移审计

*Companion to `TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv`. Computed from the frozen
Track C Test predictions (`audit_20260930/predictions_stage6/*.npz`) and the
author-966 raw data (`recovery/author_repo/dataset/illness/national_illness.csv`).
No retraining; local CPU only.*

## 1. Test 区间的真实日期（关键修正）

Track C 采用严格 966 行合同：Train 676 / Val 97 / Test 193，行索引 0-675 / 676-772 / 773-965。
数据集为周频，起始 2002-01-01。映射后：

| 块 | 行范围 | 日期 |
|---|---|---|
| Train | 0–675 | 2002-01-01 → 2014-12-09 |
| Val | 676–772 | 2014-12-16 → 2016-10-18 |
| **Test** | **773–965** | **2016-10-25 → 2020-06-30** |

每个 horizon 的有效预测起点数 = 193 − (L−1)（例如 L24 → 170 个原点，L60 → 134 个原点）。

## 2. COVID 期是否在 Track C Test 内？—— 否（对历史报告的订正）

- COVID-19 期定义为 2020-01-01 → 2021-12-31。
- Track C Test（2016-10-25 → 2020-06-30）**仅在最后 26 周（2020-01 → 2020-06-30）与 COVID 期重叠**，且 Test 于 2020-06-30 结束。
- **历史报告中著名的 "2021-02-07 幻觉峰"（pred=30,524 vs gt=14,108，约 2.2× 高估）不在 Track C Test 窗口内。**

> 该 2021 峰属于**历史 1025 行实验所用的更宽测试切分（2018-2021）**，并非严格 966 行合同。
> 在严格 966 行合同下，该结论**不可复现**，必须归类为"被严格包含性取代（superseded）"，
> 不得作为 Track C 结果呈现。这是本审计最重要的诚实修正之一。

## 3. Track C Test 实际覆盖的 COVID 信号

Track C Test 的 COVID 重叠段（2020-01 → 2020-06-30）对应的是 **2020 春季 ILI 骤降**（NPI 导致），
而非 2021 的高 ILI 异常。因此：

- 绝对值 MAE 在 COVID 段普遍更低，但这只是因为该段 ILI 量级本身被压低、曲线更平滑，**不是模型更好地处理了分布偏移**；
- 相对 MAE（MAE / 该段真实均值）更能反映难度。

| 模型 | 非COVID 段相对 MAE | COVID 段相对 MAE | 解读 |
|---|---|---|---|
| miflu | 0.287 | 0.320 | COVID 段略难 |
| nlinear | 0.121 | 0.191 | COVID 段明显更难 |
| dlinear | 0.185 | 0.140 | COVID 段更易（低ILI平滑） |
| timecma_llm | 0.347 | 0.251 | 同上 |
| patchtst | 0.486 | 0.319 | 同上 |
| itransformer | 0.489 | 0.292 | 同上 |
| qwen_time_llm | 0.345 | 0.310 | 略易 |
| calf_llm | 0.590 | 0.209 | 明显更易（低ILI） |

## 4. 对齐诊断（无索引错位）

- 对 8 个模型 × 4 horizon × 3 seed（96 单元）的 **全 lead × ILITOTAL** MSE 在 lag −2/+2 内检测：
  **7/8 模型在 lag 0 处最小化（ALIGNED）**；nlinear 在 9/12 单元 lag 0 位于最优 lag 的 5% 容差内
  （MINOR_PHASE_LAG），属真实预测相位滞后，非数据标签缺陷。
- 独立佐证：这些 npz 的 all-7-variable MSE **逐格精确复现** Track C 冠军赛 `TRACK_C_RESULTS_PER_CELL.csv`
  （如 calf_llm L24 s42：npz=5.2273，CSV=5.2273）。评分器使用的正是同一对齐方式，故对齐为其内置对齐。
- 结论：**未发现一步或 T 步索引错位**；任何亚周相位滞后是模型特性。

## 5. 措辞指引（给最终报告）

- 可写："Track C 测试窗口（2016-2020）仅在其末尾 26 周覆盖 2020 春季 COVID 导致的 ILI 骤降；
  2021 年高 ILI 异常不在本合同的测试集内。"
- 不可写："模型在 COVID 期产生幻觉式高估峰值" 作为 Track C 结论——该 2021 峰不在 Test 内。
- 若讨论分布偏移，使用文献支持的弱表述："分布偏移下的预测高估 / 异常期峰值高估方向，
  与既有 LLM 时间序列预测的域外先验依赖发现一致"，而非"已被证实的幻觉"。
