# L=24 National ILI 预测诊断图 — 图注与说明

**日期：** 2026-08-17
**数据来源：** `data/predictions_miflu_L24_paper_protocol.csv`（HPC job 506576，paper protocol，L=24，10 reps，bug-fix 后干净版本）
**脚本：** `scripts/make_miflu_evaluation_figure.py`（主路径，非 deprecated walk-forward）

---

## 图 1：连续预测曲线（TEST SET ONLY, L=24 weeks）

### 这张图画的是什么？

- **蓝色虚线** = Ground Truth（CDC 真实全国 ILITOTAL 就诊量）
- **红色实线** = MIFlu 模型预测值
- **倒三角（▼）** = GT 峰值位置
- **正三角（▲）** = 预测峰值位置
- **灰色虚线 + "val|test (test starts wk820)"** = 训练集/测试集分界线

### 关键事实：图中画的是否包含训练数据？

**没有。** 以下三项独立证据证明图中只画了 test split：

| 证据 | 来源 | 具体数值 |
|------|------|----------|
| **索引范围** | `docs/leakage_audit_report.md` §1 | train: `[0, 717)`；val: `[717, 819)`；test: `[819, 1025)` |
| **目标起点验证** | `tests/test_leakage_audit.py::test_test_target_starts_after_val_end` | L=24 的最小 test target_start = **820**，严格 > val_end=819 |
| **代码断言** | `make_miflu_evaluation_figure.py:331-332` | `assert "split" in df.columns` → `test_df = df[df["split"] == "test"]` |

**结论：** 图中所有数据点均来自 abs_week ≥ 820（约 2019 年末至 2021 年末），模型在训练期间从未见过这些周的数据。

### 右上角指标框说明

4 个指标均为 **supplementary / non-MIFlu-paper-protocol（本项目的补充诊断，由 compute_miflu_indicators.py 计算）**：
- MIFlu 论文（MIFlu_paper.md §V-B）的 National 评估协议**仅报告 MSE / MAE**
- 这 4 个指标是额外补充诊断，不进入 MIFlu 主结果表

| 指标 | 数值 | 阈值 | Verdict | 备注 |
|------|------|------|---------|------|
| Peak Hit | **0.50 (2/4)** | ≥0.75 | ❌ 未达标 | 4 个真峰匹配到 2 个，漏检 2 个 |
| Timing | **0.5 wk (based on 2/4 matched peaks)** | ≤2.0 | ✅ 达标 | 仅对通过 Peak Hit 的峰计算 |
| Peak Intensity | **31.7% (based on 2/4 matched peaks)** | ≤20.0 | ❌ 未达标 | 同上 |
| Direction | **0.70** | ≥0.60 | ✅ 达标 | 周间涨跌方向准确率 |

> ⚠️ Timing 和 Peak Intensity 绝不以孤立数字出现——始终附带 hit count `(based on 2/4 matched peaks)`。
> 若零峰匹配，则报告 `unmatched` 而非 0.0（Fix Brief #3 规范）。

---

## 图 2：诊断面板

### 左图 — Rolling Directional Accuracy（13-week window）
- 绿色曲线 = 局部方向准确率（13 周滑动窗口内，预测涨跌方向与真值一致的比例）
- 红色虚线 = 整体均值 0.70
- 灰色虚线 = 随机水平 0.5

**观察：** 2020 年初后方向准确率明显下降（COVID-19 NPIs 导致流感模式异常），2021 年末恢复。

### 右图 — Per-Peak Timing & Magnitude Error
- 蓝色柱 = 匹配到的时间偏移（Δt, 周）
- 橙色柱 = 峰值强度相对误差（%）
- 仅显示 Hit/Missed 状态的真峰（pk1~pk4 对应 4 个真峰中的匹配项）

---

## 关于"左边拟合好、右边拟合差"现象的解释

**观察到的现象：** 图左侧（约 2018–2019）预测与真值趋势大致一致；右侧（2020–2021）出现显著偏离，尤其是 COVID-19 第一波峰值（epiweek 202006 ≈ 111,361 例）被严重低估。

**这不是数据泄漏的证据。** 三项独立不变量已排除泄漏可能（见上文表格）。该现象的合理解释为：

> **待解释为 COVID-19 分布偏移假设，需在 leakage audit 通过前提下才可采用此解释。**

具体机制：
1. **训练数据范围**：模型仅在 2002–2019 数据上训练（train split 到 week ~717），从未见过 COVID-19 NPIs（封锁、社交距离、口罩令）导致的流感季异常平坦化。
2. **分布偏移（distribution shift）**：2020–2021 流感季的模式与 2002–2019 有本质差异——这是机器学习中的经典泛化失败场景，不是代码 bug 或数据混合。
3. **这正是 Phase 2 创新（ChatTime 替换 LLM backbone）的动机来源**：ChatTime 在 100 万条多样化时间序列上预训练，理论上对此类未见过的分布偏移更鲁棒。

**证据链完整性：**
- leakage_audit_report.md 通过 ✅ → 排除泄漏 → 才能合法地归因于分布偏移
- 如果 leakage audit 未通过，则"分布偏移"解释无效（可能是训练数据泄露到了测试期）

---

## 跨档一致性发现：pk1/pk2 稳定命中，pk3/pk4 全档漏检（回答导师第 5 问的现成素材）

**现象（已用 4 档 peak indicators CSV 实证，非推测）：**

| true_peak_idx | 对应峰 | L=24 | L=36 | L=48 | L=60 |
|---|---|---|---|---|---|
| 54 | pk1（早期季节峰） | Hit | Hit | Hit | Hit |
| 105 | pk2（中期季节峰） | Hit | Hit | Hit | Hit |
| 146 | **pk3（2019-20 异常大峰）** | **Missed** | **Missed** | **Missed** | **Missed** |
| 186 | **pk4（2021 小峰）** | **Missed** | **Missed** | **Missed** | **Missed** |

**业务故事（可直接写进 QA 文档）：**
- 模型对"正常"季节性峰值（pk1/pk2）的捕捉能力，不受预测跨度长短影响——L=24 到 L=60 四个独立训练的模型全部命中，非常稳定。
- 但对 COVID 期间那次异常大峰（pk3，GT 冲到 ~11.5，预测仅 ~6-7，明显低估）的漏检，也**同样不受预测跨度影响**——四个模型在同一个地方失手。
- **关键推论：** 这不是"预测得越远越不准"的常规误差累积（若是误差累积，L=60 应比 L=24 漏更多峰，但事实是四个档漏的峰完全一致）。这是**分布外（OOD）信息缺口**——pk3 对应的 2019-2020 异常大峰，其分布特征在训练数据（2002-2019）里没有先例，模型学不到，所以无论给它多长的历史窗口去预测，都补不上这个信息缺口。
- 这比单纯报"Peak Hit=0.50"更有说服力，直接回应导师"不要只讲数学指标，要讲业务故事"的要求。

**注意：** 此现象是 4 档训练全部完成后的后见观察，不依赖 Step 8 MSE/MAE 表的数值正确性。

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `results/ili/figures/fig_miflu_eval_continuous_L24.png` | 连续预测曲线（本图注主体） |
| `results/ili/figures/fig_miflu_eval_diagnostics_L24.png` | 诊断面板（方向准确率 + 峰误差柱状图） |
| `results/ili/metrics/miflu_L24_ili_peak_indicators.csv` | 逐峰原始数据 |
| `results/ili/metrics/miflu_L24_ili_peak_trend_summary.json` | 指标聚合 JSON |
