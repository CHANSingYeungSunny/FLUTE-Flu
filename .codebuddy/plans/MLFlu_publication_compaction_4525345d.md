---
name: MLFlu_publication_compaction
overview: 发表级极简重构：删除旧结果树与历史文档（git 可恢复）、只留 966 行复现链与审计证据；checkpoints/results 最新链路与所有未追踪文件一律保留；README/docs 重写为发表版（保留七条硬约束）；新增一键复现入口；重建紧凑版 handoff zip；提交并推送。
todos:
  - id: purge-old-trees
    content: git rm 四棵旧结果树、archive/、hpc_scripts/ 与根目录旧文档，未追踪文件全保留
    status: completed
  - id: prune-scripts
    content: 用 [subagent:code-explorer] 分类后删除一次性脚本、.pyc 与失效测试
    status: completed
    dependencies:
      - purge-old-trees
  - id: repro-entry
    content: 相对化 HPC 绝对路径并新增 reproduce_all.py 一键复现入口
    status: completed
    dependencies:
      - prune-scripts
  - id: rewrite-docs
    content: 重写 README/START_HERE/docs 发表版，逐字保留七条硬约束
    status: completed
    dependencies:
      - purge-old-trees
  - id: rebuild-zip
    content: 更新 build_handoff_zip.py 适配新结构并重建紧凑交接 zip
    status: completed
    dependencies:
      - repro-entry
      - rewrite-docs
  - id: acceptance
    content: 用 [skill:docx] 核对 SHA、MUST_CONTAIN 六串与权威数字，确认 zip 无大二进制
    status: completed
    dependencies:
      - repro-entry
      - rewrite-docs
  - id: commit-push
    content: 提交全部变更并推送到 GitHub origin/main
    status: completed
    dependencies:
      - rebuild-zip
      - acceptance
---


## 用户需求

为 ChatGPT（无先验上下文的 AI）生成一份完整的英文提示词文档，使其能够：

1. 读取交接包 `MLFlu_ChatGPT_Handoff_20261030.zip` 了解项目全貌（复现链、数据、脚本、权威报告）
2. 阅读论文 `reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md`（Moon et al., IEEE JBHI 2025）
3. 阅读 `HPC_GUIDE.md` 掌握 GPU 训练方法（SSH 密码免登录 Burgundy HPC）
4. **复现偏差分析**：诊断复现值 1.8652 与论文值 1.4355（+29.9%）的偏差来源，尝试通过超参调优/训练策略逼近至 5% 以内
5. **创新基准扩展**（发表级）：
   - 去归一化 MSE：将 z 空间 MSE 转换为 ILITOTAL 物理单位（人次数），直观展示实际预测误差
   - 分步长 MSE：分别展示 L24/L36/L48/L60 各步长独立 MSE（而非仅 4 步长均值），识别短/长期优势
   - PTE/PIE 逐模型逐步分析：按 Kramer & Shaman (2019) 标准（PTE <= 1 周 且 PIE <= 25%），对每个模型每个步长给出 PTE、PIE 及达标判断
   - 扩展模型组合：加入更多 ML 模型（决策树、DNN、CNN、RNN、LSTM、GRU 等），仅保留一个 Linear 基线（NLinear 或 DLinear 二选一），并探索 DeepSeek、Qwen 等 SOTA 开源 LLM（含/不含推理模式）

## 产品概述

生成一份结构化的英文提示词文档（`docs/CHATGPT_PROMPT.md`），包含项目背景、数据现状、任务指令、输出格式要求和诚实约束，使零上下文 AI 可直接执行。

## 核心功能

- 完整项目上下文注入（zip 引用、论文引用、HPC 指南引用）
- 当前数据快照（8 模型 MSE 排名、分步长 MSE、PTE/PIE 数据）
- 复现偏差分析任务指令（含论文 Table V 完整数据、消融数据、模型架构细节）
- 创新基准扩展任务指令（去归一化、分步长、PTE/PIE、扩展模型）
- 输出格式规范（Markdown 表格、Python 代码、报告结构）
- 七条硬约束逐字保留（诚实性要求）



## 技术栈

- 文档格式：Markdown（英文主导）
- 数据引用：CSV 文件路径（paper_tables/、results/v3_clean/analysis/peak_criteria/）
- Scaler 参数：JSON（data/scaler_miflu_author966.json）
- HPC 访问：SSH（sychan552@burgundy.hpc.cityu.edu.hk）
- 训练框架：PyTorch（现有 scripts/ 下训练脚本）

## 实现方案

### 总体策略

创建单个 Markdown 文件 `docs/CHATGPT_PROMPT.md`，内容为结构化英文提示词。文件分为 7 个主要段落，每段包含精确的数据引用和任务指令。不修改任何现有代码，纯文档产出。

### 关键技术决策

1. **数据快照内嵌**：将关键数值表（论文 Table V、我们的 TRACK_C 排名、PTE/PIE 聚合）直接嵌入提示词，避免 ChatGPT 需要额外解析 CSV 才能理解现状
2. **任务分层**：Part A（复现优化）为独立任务，Part B（创新基准）为独立任务，两者可并行或串行执行
3. **去归一化公式**：提供精确的 inverse transform 公式（x_physical = x_z * std + mean，std=9003.15, mean=9439.84），确保 ChatGPT 可直接计算
4. **PTE/PIE 标准**：明确引用 Kramer & Shaman (2019) 的阈值（PTE <= 1 周，PIE <= 25%），并提供现有逐格数据路径
5. **模型扩展清单**：提供具体的模型候选列表（ML 类 + LLM 类），标注哪些已有代码、哪些需新实现

### 实现注意

- **数据准确性**：所有嵌入数字必须与源 CSV 完全一致（MSE 1.8652、论文 1.4355、分步长值等）
- **诚实约束**：七条硬约束逐字保留，特别是"A/B 轨数字不可比"和"文本通路矛盾未决"
- **HPC 操作安全**：提示词中明确 HPC 操作需谨慎，训练前确认 checkpoint 备份
- **输出可验证**：每个任务的输出格式明确要求包含可验证的数字/表格

## 架构设计

纯文档产出，无代码架构变更。提示词文档结构：

```
docs/CHATGPT_PROMPT.md
├── Section 1: Role & Mission
├── Section 2: Attachments & Resources
├── Section 3: Project Background & Current State
│   ├── 3.1 Reproduction Summary
│   ├── 3.2 Current Benchmark Data (8 models)
│   ├── 3.3 Per-Horizon MSE Data
│   ├── 3.4 PTE/PIE Data
│   └── 3.5 Paper Table V (12 models, target values)
├── Section 4: Part A — Reproduction Gap Analysis & Optimization
├── Section 5: Part B — Innovation Benchmark Extension
│   ├── 5.1 Denormalized MSE
│   ├── 5.2 Per-Horizon MSE Breakdown
│   ├── 5.3 PTE/PIE Per-Model Per-Horizon Analysis
│   └── 5.4 Extended Model Comparison
├── Section 6: Output Format Requirements
└── Section 7: Honesty Constraints (7 hard rules)
```

## 目录结构

```
MLFlu/
└── docs/
    └── CHATGPT_PROMPT.md  # [NEW] 完整 ChatGPT 提示词文档（英文），约 400-600 行
```

## 关键数据结构

论文 Table V（目标值，12 模型）：
| L | MIFlu | GPT4TS | DLinear | PatchTST | TimesNet | FEDformer | Autoformer | Stationary | ETSformer | LightTS | Informer | Reformer |
|---|-------|--------|---------|----------|----------|-----------|------------|------------|-----------|---------|----------|----------|
| 24 | 1.542 | 2.063 | 2.215 | 1.319 | 2.317 | 3.228 | 3.483 | 2.294 | 2.527 | 8.313 | 5.764 | 4.400 |
| 36 | 1.422 | 1.868 | 1.963 | 1.430 | 1.972 | 2.679 | 3.103 | 1.825 | 2.615 | 6.631 | 4.755 | 4.783 |
| 48 | 1.414 | 1.790 | 2.130 | 1.553 | 2.238 | 2.622 | 2.669 | 2.010 | 2.359 | 7.299 | 4.763 | 4.832 |
| 60 | 1.364 | 1.979 | 2.368 | 1.470 | 2.027 | 2.857 | 2.770 | 2.178 | 2.487 | 7.283 | 5.264 | 4.882 |
| Avg | 1.4355 | 1.925 | 2.169 | 1.443 | 2.139 | 2.847 | 3.006 | 2.077 | 2.497 | 7.407 | 5.089 | 4.725 |

我们的 TRACK_C（8 模型，4L 均值 MSE）：
| Rank | Model | MSE | MAE | Side |
|------|-------|-----|-----|------|
| 1 | MIFlu | 1.8652 | 0.8842 | LLM |
| 2 | NLinear | 2.0495 | 0.9566 | non-LLM |
| 3 | DLinear | 2.3478 | 1.0884 | non-LLM |
| 4 | TimeCMA-LLM | 2.6700 | 1.0927 | LLM |
| 5 | PatchTST | 3.9205 | 1.3826 | non-LLM |
| 6 | iTransformer | 3.9847 | 1.3545 | non-LLM |
| 7 | Qwen-Time-LLM | 5.2196 | 1.5784 | LLM |
| 8 | CALF-LLM | 5.5153 | 1.6080 | LLM |

Scaler: ILITOTAL mean=9439.84, std=9003.15 (7 variables)

