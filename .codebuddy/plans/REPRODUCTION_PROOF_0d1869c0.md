---
name: REPRODUCTION_PROOF
overview: 生成 REPRODUCTION_PROOF.md：基于本地 CSV/训练日志与 miflu_ground_truth.json 的逐项逐行比对，按用户给定的 Markdown 结构输出，但所有占位数值以实际提取值为准（绝对透明，不虚构）。覆盖文件映射、Pre-COVID Smoking Gun、National/Regional 主表、消融完整性，并关联 Agentic-MIFlu 创新点。
todos:
  - id: build-file-mapping
    content: 建立论文表格与本地 CSV/日志映射清单，标注文件名差异与 Pre-COVID 缺失项
    status: completed
  - id: compute-metrics
    content: 用脚本计算各 CSV 的 10 次重复均值并提取训练日志 Pre-COVID MSE，记录行索引
    status: completed
    dependencies:
      - build-file-mapping
  - id: verify-pdf
    content: 用 [skill:pdf] 抽取 PDF 表 V/VI/VIII 核对 JSON 真值一致性
    status: completed
    dependencies:
      - build-file-mapping
  - id: generate-report
    content: 按模板生成透明标注差异与创新关联的 REPRODUCTION_PROOF.md
    status: completed
    dependencies:
      - compute-metrics
      - verify-pdf
---

## ⚠️ 2026-08-17 CORRECTION — CDC-revision attribution RETRACTED

This plan's original Gap-Attribution (below, line 39 & 65) listed **"CDC 2024→2026 回溯修订"**
as a cause of the National MSE/MAE gap. That attribution is now **retracted** as contradicted
by `docs/scaler_convention_supplement.md`:

- The local raw data (`data/raw/national_illness_raw.csv`) covers `epiweek 200201 … 202152`
  only — **no 2024+ weeks exist**. The "2024→2026" in the old hypothesis referred to our
  *download date*, not to newer surveillance data. CDC ILINet national 2002–2021 is final/stable.
- The "~5% Table-II drift" claim (line 66) relied on `data/verification_report.txt`, which has
  since been **deleted** (obsolete, sourced from the now-purged `MIFlu_Complete_Extraction.md`).
  It can no longer be cited as evidence.
- The only honest, verifiable explanation of the absolute-number gap is the **StandardScaler
  train-only vs pooled-fit convention difference** (explains most of the MSE gap; ~4% of paper,
  but MAE still ~17% off). CDC-vintage is **moot**, not a primary explanation.

**Corrected attribution:** National MSE/MAE gap → (1) primary: StandardScaler fit-convention
difference (train-only vs pooled); (2) residual MAE (~17%): undisclosed paper scaler convention
and/or architecture/hyperparameter differences; (3) CDC 2024→2026 revision: **ruled out / moot**,
do not attribute any gap to it.

## 用户需求

扮演"极其严苛的学术论文复现审计员"，遍历项目目录，将 `miflu_ground_truth.json`、PDF 论文表格与本地生成的 `.csv` 结果文件及训练日志逐行比对，生成名为 `REPRODUCTION_PROOF.md` 的证明文档。

## 产品概述

一份面向导师展示"方法论复现"的证据文档。遵循四大原则：绝对透明（不隐藏任何数值差异）、证据驱动（引用本地文件名/JSON 键值/CSV 行索引）、创新关联（将局限性映射到 Flex-MoE / I2MoE / UCS 创新点）、关键验证（Pre-COVID 基准 + 消融完整性）。

## 核心功能

- 文件映射与存在性检查：解析 JSON 全部表格 ID，在 `data/` 下核对对应 CSV/日志，缺失项明确标记（Pre-COVID 无独立 CSV，仅存于训练日志 `preCOVID_mse` 字段）。
- 数值比对与关键验证：提取各 CSV 中 10 次重复均值，与 JSON 真值对比，计算绝对误差与相对误差；完成 Pre-COVID 基准验证（证明无分布偏移下代码正确性）与消融实验完整性验证（Full 模型 MSE 严格最小）。
- 主表差异核对：National Table V（L=24/36/48/60 MSE）、Regional Table VI（L=2..20 PCC/RMSE）、Ablation Table VIII 各变体。
- 差异归因与创新关联：将显著 Gap（>5%）归因于 **StandardScaler 训练集-only vs 全局(pooled)拟合约定差异**（主因，见 `docs/scaler_convention_supplement.md`）、L=36 静态 Prompt 语义错配、区域噪声/模态缺失、黑盒融合不可解释，并映射到 Step 1.1（Condition-Aware Prompting / UCS）、Step 1.3（Flex-MoE Lite Missing Modality Bank）、Step 2.1（I2MoE Lite）。**CDC 2024→2026 数据回溯修订已于 2026-08-17 撤回**（本地数据仅覆盖 200201–202152，无 2024+ 周次，vintage 假设不成立），不再作为 Gap 归因。
- 生成 `REPRODUCTION_PROOF.md`：严格按给定 Markdown 结构（Executive Summary / File-to-Table Mapping / Detailed Numerical Verification 3.1-3.4 / Gap Attribution 4.1-4.3 / Conclusion）填充实际提取数值，保留双层框架（方法论复现成功 + 数值差异透明归因），不虚构"完美"。

## 技术栈与方法论

本文档生成任务以数据核对与 Markdown 撰写为主，无软件工程实现。核心是比较方法论与取值规范，需保证可复现与可追溯。

### 数据来源与解析

- 真值库：`miflu_ground_truth.json`（已声明"All values verified against PDF tables"），作为审计基线。
- 本地结果：`data/results_miflu.csv`（National Full，注意文件名非模板预期的 `results_national_miflu.csv`）、`data/results_regional_miflu.csv`、`data/results_baseline.csv`、`data/results_regional_baseline.csv`、6 个消融变体 `results_ablation_no_*.csv`（无 `results_ablation_full.csv`，Full 即 `results_miflu.csv`）。
- Pre-COVID：无独立 CSV，从 `data/training_*_log.txt` 每行的 `preCOVID_mse=...` 字段按 rep 提取（如 `training_baseline_log.txt`）。

### 指标计算规范

- 每个 (Horizon L, rep) 取 CSV 中 `mse_all`/`mae_all`（National）或 `rmse`/`pcc`（Regional）列，对同 L 下 10 个 rep 求算术均值作为"Our"值。
- CSV 行索引约定：`row_idx = 1(表头) + 块序号*10 + rep`（L 顺序 24→36→48→60 或 2→3→5→10→13→15→20），用于证据引用。
- 误差公式：Absolute Gap = Our − Paper；Relative Gap = (Our − Paper) / Paper。正值表示劣于论文。

### 关键验证逻辑

- Pre-COVID 基准：baseline（GPT4TS 等价）全 40 reps 的 `preCOVID_mse` 均值 ≈1.16，对比论文 GPT4TS ~2.06，证明无分布偏移下优于基线，排除代码错误。
- 消融完整性：Full 模型全 L 全 rep 的 `mse_all` 均值必须严格小于所有变体（实测 Full≈3.047 < 其余变体），验证各组件正向贡献。

### 实现注意

- 透明原则：National MSE 与论文差距远超 5%（实测 +56%~+156%），必须如实标注正值 Gap，归因于"评估空间缩放差异（StandardScaler 训练集-only vs 全局拟合约定）+ 静态 Prompt 与多峰数据语义错配"，不得改写为"完美复现"。**注意：原草稿中的"CDC 2024→2026 回溯修订"归因已撤回（见顶部 CORRECTION）；本地数据无 2024+ 周次，vintage 假设不成立，`data/verification_report.txt` 亦已删除、不可引用。**
- ~~`data/verification_report.txt` 已确认 Table II 全量统计匹配（15/21 within tolerance）并明确归因 CDC 修订~~ —— **该文件已删除（2026-08-17），且其所依赖的 `MIFlu_Complete_Extraction.md` 已被证明含编造内容；此条证据作废，不得再引用。**
- 文件体积小（CSV 10-40 行），计算无性能负担；建议用一次性 Python（pandas）脚本精确汇总，避免手工误差。

## Agent Extensions

### Skill

- **pdf**
- Purpose: 抽取 PDF 论文中 Table V（National）、Table VI（Regional）、Table VIII（Ablation）的数值，与 `miflu_ground_truth.json` 真值做交叉核对，确认审计基线准确无误。
- Expected outcome: 确认 JSON 真值表与 PDF 原始表格一致（或记录任何偏差），为报告中的"证据驱动"原则提供 PDF 侧背书。