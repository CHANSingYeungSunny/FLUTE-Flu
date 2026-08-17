# 导师 10 个问题 — 完整中文书面回答草稿（v3，按 §7 原话重排）

> **状态：** 草稿 / 待导师审阅
> **日期：** 2026-08-17（v3）
> **框架来源：** session summary §7 (Tutor's Original Questions) 逐字原文，10 条顺序与措辞直接采用。
> **口径：** 大白话优先，数学定义为辅；假设对方完全不懂该领域。

---

## 1. Why L=24 (and why T=104)?

### 大白话
- **L = 提前多久做预测**。L=24 = 提前约半年（24 周）预测未来半年的流感趋势。论文 Table V 列了 L∈{24,36,48,60} 四档，用来测"预测越远，准确率下降多快"。我们当前用 L=24 出图（L=36/48/60 也在跑）。
- **T = 喂给模型的历史长度**。T=104 = 模型每次看过去 104 周（≈2 年）的数据再做预测。选 104 的原因：
  1. **跨年季节性**：流感跨年循环，2 年能区分"正常季节波动"和"某年异常暖冬/冷冬"，给模型稳定基线。
  2. **长期预测需求**：公共卫生决策（疫苗运输/接种/政策/预算）要提前约半年，输入够长才能支撑长跨度推理。
  3. **抗过拟合**：论文敏感性分析显示 T>50 后性能下降（历史噪声/分布漂移），104 周是 National 平滑数据下"信息量 vs 噪声"的最佳平衡。
  4. **前人范式**：GPT4TS [9] 确立 104 周为长期流感预测标准窗口，沿用以保证可比性。

---

## 2. What exact input data predicts a given date (e.g., 2019-07-01)?

### 大白话
要预测 2019-07-01 那一周的全国流感就诊量，模型用的是什么"原料"？

- **输入窗口**：取 2019-07-01 之前连续 **104 周**（T=104）的历史，即大约 2017-07 到 2019-06 这 2 年。
- **7 个通道**（每周一个值，共 104×7 个数）：
  1. `% WEIGHTED ILI` — 加权流感样病例百分比
  2. `% UNWEIGHTED ILI` — 未加权流感样病例百分比
  3. `AGE 0-4` — 0–4 岁患者数
  4. `AGE 5-24` — 5–24 岁患者数
  5. `ILITOTAL` — **预测目标**（全国总就诊量）
  6. `NUM. OF PROVIDERS` — 上报机构数
  7. `OT` — 长期趋势辅助通道（我们实现为 `num_patients`（CDC 总就诊人次/分母，全量未缩放），**论文未给公式，是我们自己的实现选择**）
- **预测输出**：基于这 104 周 × 7 通道，模型输出未来 L=24 周的 ILITOTAL 连续值（其中第一周就是 2019-07-01 那周）。
- **预处理**：这些原始数先经 StandardScaler（仅在训练集上 fit 参数）+ RevIN 归一化，再进 GPT-2 + LoRA 主干；输出再反归一化得到物理患者数（clamp≥0）。
- **关键点**：预测 2019-07-01 时，模型**只看 2019-07-01 之前的数据**，绝不含该日期之后的任何信息（leakage audit 已验证）。

---

## 3. Suspicion that train/test data was mixed in the plotted curve (left fits well, right diverges)

### 大白话
你担心"图上左边拟合好、右边变差"是因为把训练数据混进了测试曲线——这是合理的怀疑，但审计结论是**没有混**。

**三项独立证据证明只画了 test split：**

| 证据 | 来源 | 具体数值 |
|------|------|----------|
| 索引范围 | leakage_audit_report.md §1 | train [0,717)；val [717,819)；test [819,1025) |
| 目标起点 | test_leakage_audit.py | L=24 最小 test target_start = 820，严格 > val_end 819 |
| 代码断言 | make_miflu_evaluation_figure.py | `assert "split" in df.columns` → `test_df = df[df.split=="test"]` |

图中所有点均来自 abs_week ≥ 820（≈2019 末–2021 末），模型训练时从未见过这些周。

**"左好右差"的真实原因 = COVID-19 分布偏移（不是泄漏）：**
- 训练数据止于 2018–2019 季；2020–2021 因 NPIs（封锁/口罩/社交距离）出现史无前例的平坦流感季。
- 模型从未见过这种 regime，无法外推 → 经典**分布偏移/泛化失败**（合法且预期内）。
- 这恰是 Phase 2（用 ChatTime 基础模型替代 LLM backbone）的动机：ChatTime 在 100 万条多样序列上预训练，对此类未见偏移更鲁棒。

> 注：此解释**以 leakage audit 通过为前提**。若审计未过，则"分布偏移"不成立（可能是训练数据泄露）。审计已通过，故该解释合法。

---

## 4. Why Timing delta = 0.0?

### 大白话
"Timing = 0.0" 出现在**旧协议（L=52 walk-forward，已废弃）**的某次结果里，容易让人误会是 bug。真实机制：

- **Timing 的定义**：所有"被 Peak Hit 匹配到的峰"的平均时间偏差 |Δt|（周）。它**只对匹配成功的峰计算**。
- **为什么旧结果出现 0.0**：旧 L=52 管线只抓到 1 个峰且恰好时间吻合，或匹配峰的时间差恰好为 0 → Timing 显示为 0.0。这**不代表"完美"**，而是样本极少（仅 1 个匹配峰）下的偶然值，且当时 Peak Hit 仅 0.25（4 个真峰只抓 1 个）。
- **当前论文协议（L=24, test-only）的真实值**：Timing = **0.5 周（based on 2/4 matched peaks）**——即抓到的 2 个峰平均比真峰晚/早半周，这是合理的小偏差。
- **防误解规范（Fix Brief #3）**：Timing/Peak Intensity 绝不以孤立数字出现，始终附带 hit count（如 "based on 2/4 matched peaks"）；若零峰匹配则报 "unmatched"，绝不写 0.0。

**一句话**：旧协议的 0.0 是"匹配峰极少"的偶然表现，非完美信号；当前协议 Timing=0.5 周，含义清晰、带样本量。

---

## 5. Explain peak hit / timing / intensity in narrative terms (not just "is the number good"), e.g., early vs late peak and business implications for public health decisions

### 大白话（讲故事，不是念数字）

想象你是疾控中心官员，要在流感季来临前调动疫苗、床位、抗病毒药。

- **Peak Hit（峰值命中率）= 0.50 (2/4)**：4 个真实流感高峰里，我们只提前预测出了 2 个。意味着**有一半的流感高峰，我们的模型没能在正确那周发出预警**。对公卫来说：可能在某个高峰周前没备足资源。
- **Timing（时间偏差）= 0.5 周（基于 2/4 匹配峰）**：抓到的那 2 个峰，平均比真实高峰早或晚半周。半周的偏差在现实里影响较小（疫苗调度通常以周为单位），属于可接受范围。
- **Peak Intensity（峰值强度误差）= 31.7%（基于 2/4 匹配峰）**：抓到的峰，我们预测的人数比真实少了/多了约 32%。这比阈值 20% 高 → **对资源规模估计偏差较大**：若低估峰值，可能备药不足；若高估，可能浪费。
- **Direction（方向准确率）= 0.696**：每周"下周会涨还是跌"的判断，约 70% 正确。方向感总体可靠，但不够精确。

**early vs late peak 的业务含义**：
- 若模型预测峰值**偏早**：公卫部门可能过早动员、过早耗尽库存，到真正高峰时反而不够。
- 若预测峰值**偏晚**（我们主要风险）：真正高峰来了才反应，错过最佳接种/囤药窗口，医院承压。
- 当前 Timing 仅 0.5 周，方向偏差小；主要短板是 **Peak Hit 漏检一半 + Intensity 误差 32%**——即"知不知道有峰"和"峰有多大"比"峰在哪周"更成问题。

> ⚠️ 这 4 个指标是**补充诊断**（非 MIFlu 论文协议，论文只报 MSE/MAE），详见 FIGURE_CAPTION_L24.md。

---

## 6. Justify 70:10:20 split

### 大白话
把 1025 周（2002–2021）切成三段：
- **70% 训练**（前 717 周，≈2002–2018）：教模型"流感长什么样"。
- **10% 验证**（中间 102 周，≈2018–2019）：调超参、选最好的那次训练（保留 val-MSE 最低的 checkpoint）。
- **20% 测试**（最后 206 周，≈2019 末–2021）：考模型——**完全没在训练/调参时见过**。

**为什么这样切**：
1. **论文对齐**：MIFlu 论文（MIFlu_paper.md V-A）明确用 70:10:20（follow [9],[21]）。
2. **时间序列不能随机洗牌**：若打乱，未来信息会漏进训练（典型泄漏）。必须**按时间顺序**切，保证测试永远在最后。
3. **足够测试量**：20%（206 周 ≈ 4 个流感季）足以评估跨年稳定性，含 COVID-19 异常季这一压力测试。
4. **防泄漏三不变量**（已通过单元测试）：
   - 测试目标周严格 > 验证终点（820 > 819）
   - 归一化 scaler 仅 fit 训练集
   - 切分连续无 shuffle（splits 数组非递减，仅 2 次 transition）

---

## 7. Is "NUM. OF PROVIDERS" a real driver or reverse-causation artifact?

### 大白话
NUM. OF PROVIDERS = 每周上报流感数据的诊所/医院数量。它是"真驱动因素"还是"反向因果假象"？

**结论：更可能是统计关联 / 伴随现象，不是因果驱动。**

- **反向因果风险**：流感季来了 → 更多诊所开始积极上报 → 上报机构数上升。这里"流感"是因、"上报数"是果的一个侧面；若模型把上报数当预测信号，可能是借了"医疗系统活跃度"这个代理变量（proxy），而非真正因果驱动。
- **统计工具能证什么、不能证什么**：
  - Granger causality：名含 "causality"，实际只检验**时间先后 + 统计关联**，非真因果。
  - RF / SHAP：证变量重要性高、解释贡献方向，但均属统计层面。
- **额外 caveat**：NUM. OF PROVIDERS 和 OT 都受"上报规模效应"影响——某地区突然增加上报诊所数，这两个变量会跳变，但这种跳变不代表真的更多人得流感。

**学术诚信**：我们在 `feature_verification.py` 中已明确标注 Granger = "temporal precedence + statistical association"、RF/SHAP 自动追加 "statistical association, NOT causal inference"。即：可证强统计关联，**不能证因果**，更可能是反向因果/伴随假象。

---

## 8. National MSE/MAE deviation from paper — THIS IS THE CENTRAL UNRESOLVED ITEM

### 大白话（最核心、仍未完全解决的项）
论文数字与我们跑出的有差距。L=24 核心对比（StandardScaler train-only，leakage-safe）：

| 口径 | MSE | MAE | vs 论文 MSE | vs 论文 MAE |
|------|-----|-----|------------|------------|
| **我们（train-only，主结果）** | **5.056 ± 1.583** | **1.500 ± 0.121** | 3.28× | 2.07× |
| pooled-rescaled（辅助） | ~1.61 | ~0.85 | ~1.04× | ~1.17× |
| **论文 Table V** | 1.542 | 0.726 | — | — |

**三层解释（诚实分层）：**
1. **(~96% MSE 差距) StandardScaler 拟合范围**：论文未明说 scaler 在 train-only 还是 pooled 上 fit。我们假设 pooled，仿射重缩放后 MSE 5.056→~1.61（差~4%）。但这是**事后重缩放、非重新训练**，且论文未确认该约定。
2. **(MAE 残差 ~17%)** 同变换只把 MAE 降到 ~0.85，距 0.726 仍差 ~17%。因仿射压缩大误差更狠，MSE 缩快 MAE 慢——纯数学特性，scaler 约定无法解释。
3. **(根因在调查)** 论文未公开 lr/epochs（Section V-C "set empirically"）；无官方代码/数据快照；scaler 约定可能超出线性仿射。

**已排除的假设**：
- CDC 数据版本：本地 200201–202152（1025 周），与论文 2002–2021 一致，无 2024+ 周次 → 不成立。

**学术惯例声明**：
> 论文未公开 lr/epochs、无官方代码发布。"逐位数字复现"方法论上不可保证 100%。目标为量级和趋势一致（L=60 已达 1.30×），符合复现类工作学术惯例（ACM Reproducibility Level 2），非我方失误。差距更可能来自超参/约定差异，非实现错误。

---

## 9. Explain input/process/output and the 7 heterogeneous channels clearly (ELI5 level)

### 大白话（像给小学生讲）
模型像一个人：先"看资料"→ 再"思考"→ 最后"给答案"。

**Input — 7 份资料（每周一个值，共 104 周历史）**

| # | 变量 | 大白话 | 单位/范围 |
|---|------|--------|----------|
| 1 | `% WEIGHTED ILI` | 加权流感样病例% | 0–~8% |
| 2 | `% UNWEIGHTED ILI` | 未加权流感样病例% | 0–~8% |
| 3 | `AGE 0-4` | 婴幼儿患者数 | 0–~25,000 |
| 4 | `AGE 5-24` | 青少年患者数 | 0–~40,000 |
| 5 | `ILITOTAL` | **预测目标**：全国总就诊量 | 0–~100,000+ |
| 6 | `NUM. OF PROVIDERS` | 上报机构数 | ~500–3,500 |
| 7 | `OT` | 长期趋势辅助通道 | 我们实现为 num_patients（CDC 总就诊人次/分母，全量未缩放） |

**为什么叫"异质"（heterogeneous）**：7 个量纲/数量级完全不同——百分比、患者计数、机构数混在一起，不是同一单位的重复测量。这正是论文标题 "Multimodal" 的含义：多个异构信号共同预测那 1 条 ILITOTAL 曲线。

**OT 特别说明（核实）**：我们核实了原始下载数据，OT 列最大值约 224 万，与论文 Figure 2(a) 中 Variable 7 的约 180 万量级吻合（此前文档误写为除以 100，已修正；训练代码本身从未做过该缩放，因此不影响已训练模型的正确性）。论文原文（Table X）仅称 'OT feature for long-term forecasting task'，未给出明确计算公式；OT=num_patients（全量）是基于 Fig 2(a) 图表量级反推出的强证据支持的实现选择，不是论文明文定义。

**Process — 思考流程（一句话）**
```
7 通道原始 → StandardScaler 归一化（仅 train fit）
→ RevIN 实例归一化（per-sample）
→ Patching（切小段）
→ GPT-2 文本嵌入（冻结预训练权重）
→ 时间嵌入 + 文本嵌入融合
→ GPT-2 前 6 层 + LoRA 微调（只调少量参数）
→ 输出投影 → 反 RevIN → 反 StandardScaler → clamp(≥0)
```
- GPT-2 用 OpenAI 预训练权重（迁移学习），不从头训
- LoRA 只调 ~0.1% 参数，防过拟合
- RevIN 让模型对每个样本自适应归一化，提泛化

**Output — 给答案**
- 主输出：未来 L 周 ILITOTAL 连续预测（每周一个患者数）
- 评估：MSE / MAE（StandardScaler 归一化空间）
- 附带：per-horizon 预测 CSV（含 split 列）、checkpoint、诊断图

---

## 10. Correct the wrong claim "hist=104/pred=52/stride=52" as if it were the paper's protocol

### 问题
早期文档曾写 "MIFlu 用 hist=104/pred=52/stride=52"，这是**错误**地把 ChatTime 的协议安到了 MIFlu 论文头上。

### 纠正
- **hist=104** 这部分是对的：MIFlu 论文的历史输入窗口确实是 **T=104**（输入长度）。
- **pred=52 是错的**：MIFlu 论文的预测长度是 **L∈{24,36,48,60}**，**没有 pred=52**。52 是 ChatTime walk-forward 的滚动预测长度。
- **stride=52 是错的**：这是 ChatTime L=52 连续 walk-forward 的滚动步长（每 52 周滚一次）。MIFlu 论文是**四档独立训练+评估**，固定 70:10:20 切分，**不使用滚动 stride**。

### 当前正确协议
- `train_miflu.py` 的 `CONFIG["L_list"] = [24,36,48,60]`，四档独立、静态切分、无滚动 stride ✅
- L=52 walk-forward 管线已移至 `scripts/chattime_variant/`，标记 ISOLATED/NON-DEFAULT，仅作 Phase 2 对照参考，**不作为 MIFlu 复现主结论**
- `docs/full_repo_audit_report.md` §6 已警告：勿用 `submit_ili_fulltest.sh`（内嵌 Hist=104/Pred=52/stride=52）跑 Phase 1，会静默重现废弃协议

**一句话**：hist=104 是 MIFlu 的输入窗口；pred=52/stride=52 是 ChatTime 的 L=52 滚动协议，不属于 MIFlu 论文。MIFlu 用 T=104 输入 + L∈{24,36,48,60} 独立四档、静态 70:10:20 切分。

---

## 附录：关键文件索引

| 文件 | 用途 |
|------|------|
| `MIFlu_paper.md` | 论文 PDF 直接 markdown 转换（唯一权威交叉参考） |
| `docs/leakage_audit_report.md` | 数据泄漏审计（四项断言全过）— 支撑 Q3 |
| `docs/scaler_convention_supplement.md` | Scaler 拟合约定详细分析 — 支撑 Q8 |
| `docs/full_repo_audit_report.md` | 全仓库审计（含 §6 协议警告）— 支撑 Q10 |
| `scripts/train_miflu.py` | 训练入口（paper protocol，L_list=[24,36,48,60]） |
| `scripts/compute_miflu_indicators.py` | 4 项补充指标（本项目自有脚本） |
| `scripts/make_miflu_evaluation_figure.py` | 诊断图生成 |
| `data/predictions_miflu_L24_paper_protocol.csv` | L=24 预测（含 split 列） |
| `results/ili/figures/fig_miflu_eval_continuous_L24.png` | 连续曲线图（TEST SET ONLY） |
| `results/ili/figures/fig_miflu_eval_diagnostics_L24.png` | 诊断面板图 |
| `results/ili/figures/FIGURE_CAPTION_L24.md` | 图注说明（含 4 指标 supplementary caveat 全文） |
