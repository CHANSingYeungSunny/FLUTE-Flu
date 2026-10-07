---
name: MIFlu_JBHI_Finalization
overview: "Finish the 4 remaining \"0→100\" journal-readiness tasks for the MIFlu IEEE JBHI submission that the audit flagged as TODO/INCOMPLETE: (A) add the missing \"Timing=0.5 = peak timing error, not lead time\" ELI5 section to Advisor_Questions_Resolution_Report.md; (B) write an attention-heatmap generator, pull a gated_inject checkpoint from HPC, and produce fig_attention_heatmap.png; (C) scp the HPC journal_evidence/ (gated_inject + core4_table) to local results/ili/ so the clean 4-variant Table VIII and artifacts are local; (D) execute the local cleanup enumerated in CLEANUP_PLAN.md (remove stray temp scripts, __pycache__, backup dir) while preserving core files. The 4/4 HPC ablations and parameter-audit gate are already complete; no retraining required."
todos:
  - id: audit-checklist
    content: 输出 0-100 完成度审计清单（Markdown 表格，含 DONE/TODO 与证据）
    status: completed
  - id: advisor-timing
    content: 在 Advisor_Questions_Resolution_Report.md 补充 Timing=0.5 ELI5 章节（引用 Tutor_QA_Draft:66-94）
    status: completed
  - id: hpc-pull
    content: scp 拉取 HPC journal_evidence/gated_inject 与 core4_table 到本地 results/ili/ 并校验
    status: completed
  - id: fig2-heatmap
    content: 编写并执行 scripts/make_attention_heatmap.py 生成 results/ili/figures/fig_attention_heatmap.png（本地无 torch 则 HPC 兜底）
    status: completed
    dependencies:
      - hpc-pull
  - id: local-cleanup
    content: 按 CLEANUP_PLAN.md 执行本地清理：dry-run 后删除临时脚本/__pycache__/备份目录，保留核心文件
    status: completed
---

## 用户需求概述

作为 IEEE JBHI 投稿的资深架构师与一作，对 `C:\Users\Asus\Desktop\FYP code\MLFlu\` 进行「0→100」全面审计 + 自动补齐缺失任务，确保项目达到顶会投稿 100% 就绪。

## PHASE 1 完成度审计清单（[Item] / [Status] / [Evidence/Action]）

| # | Item | Status | Evidence / Action |
| --- | --- | --- | --- |
| 1 | 双轨指标（表 V 用 z-space，图/补充用物理单位） | DONE | `train_ablation.evaluate()` 同时返回 z-space 与 `mse_ili_phys`；`results/ili/figures/fig_miflu_eval_continuous_L24.png` 已存在且为物理单位 |
| 2 | 完整 1025 行窗口（train_end=717, val_end=819） | DONE | `configs.assert_full_window`/`derive_split` 断言；HPC 日志确认 `Data: 1025 total \ | Train=717 \ | Val=102` |
| 3 | 仅 4 核心变体（full/no_lora/no_text_ln/gated_inject） | DONE | `configs.CORE_VARIANTS`；`core4_table/journal_table_viii.csv` 仅含 4 行（HPC 遗留目录不影响干净表） |
| 4 | `CLEANUP_PLAN.md` 存在并列出散落文件 | DONE | 本地 `CLEANUP_PLAN.md`（8.59KB）存在 |
| 5 | 散落文件实际删除 | TODO | 本地仍有 `_tmp_*.sh`、`auto_submit_*.sh`、`hpc_*.sh`、`__pycache__`(12 .pyc)、`_mlflu_wt_backup_20260830/` 等，需按 CLEANUP_PLAN 删除 |
| 6 | `scripts/configs.py` 被全部 5 个训练脚本 import | DONE | 6 处 import（train_ablation/baseline/miflu/regional_* + miflu_model） |
| 7 | `set_seed()` 在所有训练脚本开头调用 | DONE | 5 个训练脚本均含 `set_seed(CONFIG["seed"])` 调用 |
| 8 | 数据泄漏证明：scaler 仅对 `[:717]` 拟合 | DONE | `scaler_utils.fit_from_train` 用 `data[:train_end].mean/std`；`_self_check` 断言 `train_end==717, val_end==819`（注意：非 sklearn `.fit()`，勿误改） |
| 9 | `REPRODUCIBILITY.md` 含环境/数据/CLI | DONE | 本地 `REPRODUCIBILITY.md`（11.78KB）存在 |
| 10 | Advisor 报告回答 5 问（ELI5） | DONE | `Advisor_Questions_Resolution_Report.md` 含 Q1–Q5 ELI5 |
| 11 | Advisor 报告明确解释 "Timing=0.5" | TODO | 报告缺此章节；源材料在 `docs/Tutor_QA_Draft_2026-08-17.md:66-94`（说明 0.5 周为峰值时间误差/半周偏移，非 lead time） |
| 12 | 产物树按 `variant/reps_1_to_10/rep_N/` 结构 | DONE | HPC `journal_evidence/gated_inject/reps_1_to_10/rep_01..10/checkpoints/best_model.pt` 确认 |
| 13 | 聚合出干净 4 变体 Table VIII | DONE | HPC `journal_evidence/core4_table/journal_table_viii.csv`（已排除遗留目录） |
| 14 | 图1：物理单位评估图（真实 CDC 日期 X 轴） | DONE | `results/ili/figures/fig_miflu_eval_continuous_L24.png` 存在；`make_miflu_evaluation_figure.py`+`cdc_calendar.py` 生成 |
| 15 | 图2：gated_inject 跨模态注意力热力图 | TODO | 无 `fig_attention_heatmap.png` 及无生成脚本；`ModalityAligner.cross_attn` 当前丢弃权重（`aligned, _ = ...`） |
| 16 | HPC 结果已 scp 回本地 `results/ili/` | TODO | 本地 `results/ili/` 仅有 figures/metrics，`journal_evidence/` 与 `core4_table/` 缺失 |


## 核心待执行项（TODO）

A. 本地清理（删除散落文件/**pycache**/备份目录）
B. Advisor 报告补充 Timing=0.5 章节
C. 从 HPC 拉取 `journal_evidence/gated_inject` 与 `core4_table` 到本地
D. 编写并运行脚本生成图2 注意力热力图

## 技术栈与既有约定

- 项目语言：Python（PyTorch + pandas）。HPC 环境：`sychan552@burgundy.hpc.cityu.edu.hk`，工作目录 `/scratch/sychan552/CHATTIME/Chattime`（非 MLFLU、非 /gpfs1/home）。
- 既有模式：所有超参集中在 `scripts/configs.py`；`set_seed()` 在脚本开头；`evaluate()` 双轨返回；`scaler_utils.fit_from_train` 仅用 `data[:train_end]` 拟合（已正确，勿改）。
- 图1 生成范式：`make_miflu_evaluation_figure.py` + `cdc_calendar.py`（真实日期反归一化），图2 复用同套物理单位/绘图风格。

## 实施方案（关键决策）

### B. Advisor 报告补充 Timing=0.5（低风险，纯文档）

- 在 `Advisor_Questions_Resolution_Report.md` 追加 Q6（或并入 Q3 之后）ELI5 章节，结构严格遵循 `Problem → Scientific Reason → Fix → Status`。
- 内容要点（取自 `docs/Tutor_QA_Draft_2026-08-17.md:66-94`）：`Timing=0.5 周` = 4 个真实流感峰中命中 2 个、其平均时间偏差 |Δt| 为半周（早/晚约 3.5 天），是**峰值时间误差（半周偏移）**，**绝非 lead time（提前量）**；且绝不以孤立数字出现，须附 `based on 2/4 matched peaks`，零匹配报 `unmatched` 而非 0.0。

### C. HPC 数据回拉（scp）

- `scp -r sychan552@burgundy.hpc.cityu.edu.hk:/scratch/sychan552/CHATTIME/Chattime/hpc_results/journal_evidence/gated_inject results/ili/journal_evidence/`
- `scp -r .../hpc_results/journal_evidence/core4_table results/ili/core4_table`
- 校验 `results/ili/core4_table/journal_table_viii.csv` 存在（4 变体干净表）。

### D. 图2 注意力热力图（需 checkpoint，本地优先/HPC 兜底）

- 新建 `scripts/make_attention_heatmap.py`：
- 用 `NATIONAL_CONFIG` 实例化 `ForecastingLLM(gated_inject=True)`，从 `results/ili/journal_evidence/gated_inject/reps_1_to_10/rep_01/checkpoints/best_model.pt` 载入 `state_dict`。
- 对 `modality_aligner.cross_attn` 注册 forward hook 捕获注意力权重（`query=time-patches, key/value=text-tokens`）。
- 取一个样本窗口做前向，跨 head 平均，绘制 `time-patch × text-token` 跨模态注意力热力图，输出 `results/ili/figures/fig_attention_heatmap.png`。
- 复用图1 的字体/配色风格，标注 cross-modal activation。
- 执行策略：先本地 `python scripts/make_attention_heatmap.py`；若本地无 torch，则在 HPC 用 `sbatch` 短任务（或用其已配 conda env `mlflu_hpc`）生成后 scp 回本地。

### A. 本地清理（安全删除）

- 删除：`_tmp_hpc*.sh`、`_tmp_mon.sh`、`_tmp_pdftable.*`、`auto_submit_*.sh`、`hpc_*.sh`、`check_anchor_env.sh`、`hpc_probe*.sh`、`verify_forward.py`、全部 `__pycache__`（.pyc）、`_mlflu_wt_backup_20260830/`。
- 保留：`scripts/`、`data/`、`docs/`、`hpc_results/`、`results/`、`*.md`、`configs.py`、已生成图表与报告。
- 先 `dry-run` 列出待删清单，确认无误后再执行（必要时用 `move` 至 `_trash/` 暂存更安全）。

## 性能与可靠性

- 热力图只需单次前向（单窗口），开销极小；跨 head 平均降维，避免大图。
- scp 仅拉 `gated_inject`（10 个 rep 的 checkpoint，每个 ~数百 MB）与 `core4_table`（小），带宽可控；先验证远端路径存在再拉。
- 清理前 dry-run，避免误删核心文件（blast-radius 控制）。