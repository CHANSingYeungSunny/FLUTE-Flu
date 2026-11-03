# IMPORTANT DEADLINES
- Progress Report submission: **20 November 2026 (11:59 pm)** via FYP InfoNet
- Progress Presentation: **Week 12 (November 16-20)** to supervisor AND assessor
- Late penalty: sub-grade deduction per day
- Failure to present = zero mark

# ChatGPT 任务书：MIFlu 复现 + 28 模型基准 —— 请优化报告并研究创新点

> **你是学术写作专家。** 请先完整理解本项目（见 `PROJECT_HANDOFF.zip`），然后完成以下任务。

---

## 0. 项目一句话

我们独立复现了 **MIFlu**（Moon et al., IEEE JBHI 2025，流感预测 LLM 模型），并新增了 **28 个模型的基准对比**（16 常规模型 + MIFlu + 3 LLM-based + 11 冻结 LLM 编码器）。核心发现：**MSE 冠军 ≠ 峰值预测冠军**。

---

## 1. 请先阅读这些文件（按顺序）

1. `04_详细说明文档/REPRODUCTION_BENCHMARK_COMPARISON.md` ← **最重要**：全部参数对比表 + 差异原因
2. `04_详细说明文档/HANDOFF_20261102.md` ← 权威数字 + 项目状态
3. `04_详细说明文档/METHODOLOGY_METRICS_AND_SPLIT.md` ← 指标定义 + 数据泄漏防护
4. `02_数字表格/BENCH_MSE_BY_MODEL_L.csv` ← 28 模型 MSE/MAE
5. `02_数字表格/BENCH_PTE_PIE_BY_STEP.csv` ← PTE/PIE 逐 step
6. `01_最终报告/figures/` ← 116 张预测图（28 模型 × 4 跨度）

---

## 2. 关键数字（不可更改）

### 复现 Table V
| 跨度 | 论文 MSE | 我们的 MSE | 差异 |
|------|---------|-----------|------|
| L=24 | 1.542 | 1.3045 | **−15.4%** |
| L=36 | 1.422 | 1.3561 | **−4.6%** |
| L=48 | 1.414 | 1.6543 | **+17.0%** |
| L=60 | 1.364 | 1.6829 | **+23.4%** |
| **均值** | **1.4355** | **1.4995** | **+4.5%**，符号交叉 2-2 |

**红线**：绝不说"我们打败了论文"。只说 "reproduced within 4.5%, horizon-dependent sign crossover 2-2"。

### 基准
- **MSE 冠军**：MIFlu 1.5574（PatchTST 1.6621 第二）
- **峰值冠军**：NLinear（K&S 4/16 通过，PTE 1.68 周，PIE 9.5%）
- **LLM 编码器全部差**：最好 Hunyuan-1.8B = 4.7374，最差 Qwen2.5-1.5B = 5.2049
- **Pareto**：NLinear 2,520 参数 vs PatchTST 531,878（211 倍），只差 11.2% MSE

---

## 3. 请完成这些任务

### 任务 A：优化三份报告

**A1. 内部技术报告**（`report_internal_en/zh.docx`，约 23 页）
- 面向**零基础读者**（导师 + 我自己），语言要简单直接
- **必须包含**：
  - Table V 对比表 + 百分比差异 + 符号交叉说明
  - 完整参数对比表（我们 vs 原作者仓库）+ 每处差异的原因
  - 数据泄漏解释（为什么用验证集而非测试集选模型）
  - 7 变量 vs 单变量的解释
  - 28 模型 MSE/MAE 排名表
  - PTE/PIE/K&S 表 + 冠军解释
  - Pareto 前沿分析
  - LLM 编码器结论（w/o inference，11 臂全部差）
  - 每个模型至少一张预测图（116 张在 figures/）
  - MSE/MAE 柱状图
- **删除**：无关的技术细节、冗余的历史叙述

**A2. FYP 进度报告**（`progress_report_en/zh.docx`）
- 学校模板（PART A + PART B 八节），**无页数限制**
- 截止 **2026-11-20**，需向导师+评阅人展示
- 重点：**项目目标、方法、进度、已获成果**
- 精选 2-4 张图

**A3. IEEE 稿件**（`ieee_manuscript_en/zh.docx`，目标 IEEE JBHI）
- **页数限制 8-14 页**
- 精选 4-6 张图（请根据 JBHI 惯例和页数限制选择最佳图表组合）
- 需要完整的 Abstract / Introduction / Related Work / Methods / Experiments / Conclusion
- 引用格式 IEEE

### 任务 B：选择最佳图表组合

对于进度报告和 IEEE 稿件，请你根据以下约束**选择最佳图表**：

| 报告 | 页数 | 常见图数 | 约束 |
|------|------|---------|------|
| FYP 进度报告 | 无硬限 | 2-4 | 学校模板，重点展示成果 |
| IEEE JBHI | 8-14 页 | 4-6 | 顶刊惯例 |

可选图表（116 张 + 5 张总览）：
- `fig_forecast_<model>_L<L>.png`：逐 step 预测（28 模型 × 4 跨度）
- `fig_pareto_frontier.png`：准确率 vs 参数量
- `fig_pte_pie_heatmap.png`：峰值预测热力图
- `fig_all_models_ranking.png`：28 模型 MSE 排名
- `fig_llm_encoders_vs_baseline.png`：LLM 编码器对比

请给出你选择的图表组合和理由。

### 任务 C：研究创新点（最重要！）

当前只有 1 个发现：**MSE 冠军 ≠ 峰值冠军**。这只是"发现"，不是"创新"。

**请你研究以下三个创新方向，评估哪个最适合发表在 IEEE JBHI 或其他顶刊**：

**C1. 校准感知的模型选择准则**
- 主张："用 K&S 标准选模型（而非 MSE）能避免部署失准的模型，代价可量化"
- 实验：比较 MSE-based vs K&S-based 选择的决策差异 + 准确率代价表
- 成本：0 GPU 小时（纯分析）

**C2. 混合预测器**
- 主张："结合 PatchTST 的时间捕捉和 NLinear 的峰值校准"
- 实验：PatchTST 点预测 + NLinear 式区间重校准
- 成本：20-60 A100 小时

**C3. 冻结 LLM 编码器选型指南**
- 主张："冻结 LLM 表征不自动改善流行病学预测；编码器家族选择和参数成本可量化"
- 实验：11 臂分析：Qwen/DeepSeek/Tencent 家族对比、参数成本缩放、Llama-8B vs Qwen-7B 架构对比
- 成本：0 GPU 小时（数据已有）
- **最便宜，数据已在手**

**请评估**：
1. 哪个创新点最有发表价值？
2. 如何设计实验来支撑它？
3. 需要补充什么实验/分析？
4. 该投哪个期刊（IEEE JBHI / npj Digital Medicine / Nature Communications / 其他）？

### 任务 D0：核实 Kramer & Shaman 判据（最紧急！）

**问题**：我们使用 `PTE ≤ 1 周 且 PIE ≤ 25%` 作为"预测命中"标准，归因于 Kramer & Shaman (2019)。
但项目内部标记为 **`[to verify]`** —— 从未对照原文核实！

**请你**：
1. 查阅 Kramer & Shaman (2019) 原文（PLOS Comput Biol 15(2):e1006742, DOI: 10.1371/journal.pcbi.1006742）
2. 核实 PTE/PIE 的**确切定义**（公式、单位）
3. 核实 "PTE ≤ 1 week AND PIE ≤ 25%" 这个阈值**是否真的出现在原文**（给出章节 + 页码）
4. 如果原文用的是不同阈值，**必须改用原文阈值**并重新计算
5. 峰值检测参数（find_peaks prominence=0.15·range, distance=15, ±8周匹配）**完全是我们的工程选择**，论文中必须写 "in this study"

**另外核实**：
- "4/16" 的含义：16 = 4 跨度 × 4 步长，4 格通过 = NLinear 在 step 0（1周前）4 个跨度全部通过
- 7 变量 vs ILITOTAL 的解释是否正确（OT 均值 493,629 vs %ILI 1.74，量纲差 283,650 倍）
- 数据泄漏解释是否正确（原作者用测试集选 checkpoint）

### 任务 D：验证推理

请对报告中的每个推理/因果链进行验证：
1. "NLinear 峰值更好是因为它在峰值处反应更锐利" —— 这是假设还是已验证？
2. "LLM 编码器差是因为冻结表征不迁移" —— 有没有其他解释？
3. "数据泄漏导致论文数字偏乐观" —— 量化影响多少？
4. "drop_last 丢弃的窗口更难 1.41×" —— 这个证据可靠吗？

对每个推理给出：**已验证 / 合理假设 / 需要额外实验**。

---

## 4. 最终交付

完成优化后，请提供：
1. **三份报告的优化版本**（Overleaf-ready LaTeX 或改进的 Word）
2. **图表选择清单**（哪张图放哪里，为什么）
3. **创新点评估报告**（选哪个、实验设计、成本、投稿目标）
4. **Overleaf 项目**：LaTeX 源码 + 编译好的 PDF + zip 包（可直接上传 Overleaf）
5. **推理验证清单**（任务 D 的结果）

---

## 5. 不可违反的红线

1. **绝不说"我们打败了论文"**。+4.5% 更差，符号交叉 2-2。
2. **论文 Table V 是 1.542/1.422/1.414/1.364**（均值 1.4355）。不要用其他版本。
3. **绝不用 2026-11-02 03:57:47 之前的 LLM ±sd**（种子 bug 导致 sd=0）。
4. **`--no-text` 是逐位相同的结构验证**，不是消融效应。
5. **绝不编造数字**。写 "not yet available" 并说明原因。
6. **DLinear 被排除**（用户决定）。NLinear 是唯一线性模型。
7. **硬件**：A100-SXM4-80GB，CityU HPC，分区 stingy/gpu_a100。
8. **两套种子协议不能混**：复现 10-seed (2021-2030) vs 基准 3-seed (42/43/44)。
9. **Kramer & Shaman 标准**：PTE ≤ 1 周 且 PIE ≤ 25%（合取式）。

---

## 6. 当前项目状态

| 项目 | 状态 |
|------|------|
| 复现 | ✅ 完成（+4.5%，2-2 交叉） |
| 28 模型基准 | ✅ 完成 |
| 11 LLM 编码器 | ✅ 聚合完成 |
| Table VIII 消融 | ✅ 60/60 完成 |
| Table VI 区域 | 🔄 19/72 完成 |
| 滚动起点 | ❌ 未跑（155-360 A100-h） |
| 跨数据集 | ❌ 未开始（~10 A100-h） |
| 创新点 | ❌ 待研究 |
| 116 张预测图 | ✅ 全部生成 |


## CRITICAL: Explanation Placement Rules (Main Focus)

Every explanation must be placed IMMEDIATELY AFTER the content it explains, NOT collected at the end.
This rule applies to ALL THREE reports (internal, FYP progress, IEEE manuscript):

| Explanation | MUST be placed AFTER |
|---|---|
| Why 676/97/193 (70/10/20) split? | The Data section text mentioning the split |
| Why (W//16)*16 evaluation windows? | Immediately after the split explanation |
| Why 3 seeds in benchmark but 10 in reproduction? | Immediately after the bench_params comparison table |
| Why ILITOTAL for PTE/PIE but 7-var for MSE? | Immediately after the 3-seed explanation |
| What are the two [DEVIATION] items? | Immediately after the repro_params comparison table |
| What is the Pareto frontier? | Immediately after the "Benchmark 3: Pareto" section title |

## CRITICAL: Section Numbering Rules

Sections must be numbered sequentially from 1 to the end (no gaps):
- Internal report: 1.Data → 2.Method → 3.Reproduction → 4-7.Benchmark 1-4 → 8.LLM → 9.Ablation → 10.References
- FYP progress: PART A + PART B sections 1-7 (per school template)
- IEEE: Roman numerals I-X

## Main Focus Checklist (must be in all reports)

1. MSE champion != peak champion (MIFlu 1.5574 vs NLinear K&S 4/16)
2. LLM encoders do NOT help (MSE 4.73-5.20, none passes K&S)
3. Reproduction: +4.5% mean, sign crossover 2-2
4. Table V comparison with percentage differences and MAE
5. us vs essay parameter comparison table (repro_params)
6. Benchmark comparison table (bench_params: 3 seeds vs fix_seed=2021)
7. Four benchmarks: MSE/MAE, PTE/PIE (K&S), Pareto, Statistical significance
8. Key definitions: Horizon L, Step s, PTE, PIE, K&S [to verify], (W//16)*16


## TASK: Generate PPT Presentation and Talking Script (演讲稿)

### Deadline Context
- **Progress Report submission**: 20 November 2026 (11:59 pm) via FYP InfoNet
- **Progress Presentation**: Week 12 (November 16-20), to supervisor AND assessor
- **Late penalty**: sub-grade deduction per day
- **Failure to present**: zero mark

### What to Generate
1. **PPT file** (PowerPoint, .pptx) — presentation slides for the FYP progress presentation
2. **Talking script (演讲稿)** — a complete script the student can read/refer to during the presentation

### PPT Content Guidelines (based on the rubric in Appendix II.pdf)

The rubric has 4 criteria (each 0-4 points):
1. **Technical Content — Relevance and accuracy** (4 pts): Relevant details, clear/accurate statements, strongly supported
2. **Technical Knowledge — depth and breadth** (4 pts): Fully explains underlying principles, answers challenging technical questions
3. **Delivery — Organization, preparation, effectiveness** (4 pts): Confident, well-organized, correct English
4. **Delivery — Style, pacing, body language, time management** (4 pts): Eye contact, appropriate pacing

### PPT Structure (suggested, ~10-12 slides for 10-15 min presentation)
1. **Title slide**: Project title, student name, supervisor, date
2. **Problem statement**: Why influenza forecasting matters, what MIFlu claims
3. **Objectives**: 3 clear objectives
4. **Methodology overview**: Two protocols (reproduction + benchmark), key design choices
5. **Reproduction results**: Table V comparison (us vs paper), sign crossover
6. **Benchmark 1 — MSE/MAE**: 28 models, champion = MIFlu
7. **Benchmark 2 — PTE/PIE**: Peak skill, champion = NLinear, K&S criterion
8. **Core finding**: MSE champion != peak champion (THE key message)
9. **Benchmark 3 — Pareto**: Accuracy vs efficiency trade-off
10. **Benchmark 4 — Statistical significance**: NLinear vs PatchTST not significant
11. **LLM encoder results**: All poor, negative result
12. **Conclusion + future work**: Innovation plans, paper submission target

### PPT Design Guidelines
- Use the figures from `01_最终报告/figures/` (especially `fig_compare_L24.png`, `fig_ks_ranking.png`, `fig_pareto_frontier.png`)
- Keep text minimal on slides — use bullet points, not paragraphs
- Include the comparison tables (repro_params, benchmark results)
- Highlight the core finding prominently

### Talking Script Guidelines
- Write in English (presentation language)
- Structure: Introduction (1 min) → Methodology (2 min) → Results (5 min) → Core finding (2 min) → Conclusion (1 min)
- Include speaker notes for each slide
- Anticipate technical questions from supervisor/assessor and prepare answers
- Reference the rubric criteria explicitly to maximize marks

### Source Materials for PPT
- **Internal report** (`report_internal_zh.pdf`): Main results and findings
- **FYP progress report** (`progress_report_zh.pdf`): Structure and achievements
- **Main focus** (`project_main_focus.md` memory): Core claims and definitions
- **Figures** (`01_最终报告/figures/`): All charts and graphs
- **Tables** (`02_数字表格/`): All CSV data
