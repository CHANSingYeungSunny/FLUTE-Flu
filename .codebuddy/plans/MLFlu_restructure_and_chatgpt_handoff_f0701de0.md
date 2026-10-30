---
name: MLFlu_restructure_and_chatgpt_handoff
overview: 把史山式 MLFlu 项目重构为零基础可读、可发表的结构（双语文档导航层 + 根目录物理归档，不改动任何数据/结果/证据），并构建"文本+代码+数据"双语交接 zip 供无上下文的 ChatGPT 完整接手（先优化现有 8 模型基准、再扩模型、再创新），最后将重构与 zip 一并 commit+push。
todos:
  - id: paper-repo-docs
    content: 编写论文解读与作者仓库解读双语文档（docs/01_paper/）
    status: completed
  - id: audit-movable
    content: 用 [subagent:code-explorer] 核查根目录散落文件引用关系，确定安全归档清单
    status: completed
  - id: docs-layer
    content: 创建零基础文档层：START_HERE、GLOSSARY、DIRECTORY_MAP、EVIDENCE_INDEX、PROJECT_STATUS、ROADMAP
    status: completed
    dependencies:
      - paper-repo-docs
  - id: reorg
    content: git mv 根目录散落文件至 docs/ 与 archive/，重写 README 并修正文本引用
    status: completed
    dependencies:
      - audit-movable
      - docs-layer
  - id: docx-to-md
    content: 用 [skill:docx] 提取权威 DOCX 为 Markdown 并核对数字一致
    status: completed
    dependencies:
      - docs-layer
  - id: handoff-script
    content: 编写 build_handoff_zip.py：按清单组装 00_HANDOFF 至 07_docs 双语交接包
    status: completed
    dependencies:
      - reorg
      - docx-to-md
  - id: build-verify-zip
    content: 构建 zip，校验体积、可解压、结构与硬约束完整、SHA 链一致
    status: completed
    dependencies:
      - handoff-script
  - id: commit-push
    content: git 提交重构与 zip（zip 入库），push origin main 并输出开场 prompt
    status: completed
    dependencies:
      - build-verify-zip
---

## 产品概述

将 MLFlu（IEEE JBHI 2025 MIFlu 流感预测论文复现 + 4非LLM/4LLM 基准对比）从"史山式"结构重构为零基础可读、可发表的项目，并产出供无上下文 ChatGPT 完整接手的双语交接包。

## 核心功能

1. **论文解读文档**：高层设计（文本嵌入器/时序嵌入器/预测LLM 三模块）、预测工作流、作者包结构、数据切分（National-Illness 70:10:20=676/97/193）、指标与超参、Table V 结果。
2. **作者仓库解读文档**：github.com/Jmoon3108/MIFlu 结构映射（main_ILI_lora.py 入口、models/GPT4TS_lora.py=LoRA 核心、data_provider、utils、dataset/illness + text_emb 预计算嵌入），论文章节↔代码对照表。
3. **项目重构（文档层 + 目录物理归档）**：新建 START_HERE、术语表、目录地图、证据索引、状态与路线图；根目录约 40 个散落规划/提示词文件移入 docs/ 与 archive/。**严禁改动任何数据、结果、脚本与哈希证据**。
4. **ChatGPT 交接 zip（文本+代码+数据，双语）**：总交接书 + 论文/仓库解读 + 966行数据 + 12 个预测 CSV + 基准结果 + 复现/审计证据 + 全部脚本 + 文档层；含给 ChatGPT 的分阶段任务书（先优化现有基准→扩模型→创新）。

## 必须固化的硬约束（写入所有新文档）

- A轨(966行/3种子/2.0415) 与 B轨(1025行/10种子/0.7709) 数字绝不可比；论文 1.4355 是第三种口径。
- 文本通路机制矛盾**未决**：GPU 梯度非零 vs CPU 效应为零，两侧证据相反，不得宣称有效或无效。
- 禁止出现"自定义通过"；PTE/PIE 仅用文献标准 PTE≤1周 & PIE≤25%。
- 论文复现统一为：1.4355 ↔ 1.8652（+29.9%，PARTIAL_REPRODUCTION）；不提 C0/C1。
- 权威报告 = reports/concise_final/..._精简终版.docx（SHA 见 CURRENT_OFFICIAL_REPORT.txt）。
- 正式数据 = 作者 966 行 national_illness.csv（SHA 2a96dfed…）；1025 行快照不同 vintage 不可混用；date 列为合成标签。
- MSE≠准确率：MSE 冠军 MIFlu(1.8652)，峰值冠军 NLinear(36/36)，分开报告。

## 技术栈

- 文档生成：Markdown（双语：英文正文 + 关键裁决/约束中英对照）
- DOCX→Markdown：python-docx 1.2.0 提取正文与表格（环境无 LibreOffice/pandoc）
- 压缩：Python zipfile（可控清单与体积校验）；校验：hashlib SHA-256
- 归档：git mv（保留历史）；全仓引用修正用 ripgrep 定位

## 实现要点

- **零影响原则**：results\(3811)、hpc_results\(729)、hpc_scripts\(703)、scripts\、tests\、data\、recovery\、slurm\、audit_20260930\、rerun_20261006\ 全部原位不动（900+ 脚本硬编码相对路径 + 哈希证据引用）。仅重构根目录散落文件。
- **重构后验证**：比对文件数与关键 SHA（2a96dfed…、DOCX SHA）不变；git status 仅 rename/add 无 delete。
- **zip 体积控制**：含 83MB 预测 CSV，预计 60–120MB；构建后校验 <100MB（GitHub 单文件上限），超限分卷并在交接书说明。
- **交接书必含**：7 条硬约束、canonical 数字表、给 ChatGPT 的 Phase A/B/C 任务书、zip 阅读指南、开场 prompt。
- **git**：.gitignore 增 handoff/staging/；zip 本身入库；两笔提交后 push origin main（禁止 force）。

## 目录结构（新增/移动）

```
MLFlu/
├── START_HERE.md            # [NEW] 10分钟零基础入口
├── README.md                # [MODIFY] 重写为导航入口
├── CURRENT_OFFICIAL_REPORT.txt  # 保留
├── docs/
│   ├── 01_paper/PAPER_EXPLAINED.md          # [NEW] 论文解读
│   ├── 01_paper/AUTHOR_REPO_EXPLAINED.md    # [NEW] 作者仓库解读
│   ├── GLOSSARY.md / DIRECTORY_MAP.md / EVIDENCE_INDEX.md  # [NEW]
│   ├── PROJECT_STATUS.md / ROADMAP.md       # [NEW]
│   └── paper_and_analysis/  planning/       # [MOVE] 根目录分析与规划文档
├── archive/prompts/  planning_docx/         # [MOVE] 提示词与历史 docx
├── handoff/
│   ├── build_handoff_zip.py    # [NEW] 交接包构建脚本
│   └── MLFlu_ChatGPT_Handoff_*.zip  # [NEW] 交付物
└── (results/ hpc_results/ scripts/ data/ recovery/ 等原位保留)
```

### SubAgent

- **code-explorer**
- 用途：重构前全仓梳理根目录 40 个散落文件的引用关系与 scripts/tests 中的路径依赖，确认可安全移动的清单
- 预期产出：可移动文件清单 + 需修正的文本引用位置列表

### Skill

- **docx**
- 用途：从 reports/concise_final/..._精简终版.docx 提取正文与表格生成 Markdown 版纳入交接包
- 预期产出：04_benchmark/REPORT_精简终版.md（内容与 DOCX 一致）