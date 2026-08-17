---
name: national_miflu_drop_pcc_rmse_table
overview: 明确本次为 National ILI 复现（L=24/36/48/60，MSE/MAE 为论文章节指标）。修改 train_miflu.py 的最终报告表：PCC 与 RMSE 不再输出到主结果表/日志表头，但 evaluate() 仍照常计算（保留诊断能力，不破坏下游 best-rep 选择逻辑）。
todos:
  - id: trim-output-cols
    content: 修改 train_miflu.py 移除 RMSE/PCC 输出列（4 处：all_rows、agg、rename、日志表）
    status: completed
  - id: compile-check
    content: 本地 py_compile 校验 train_miflu.py 语法
    status: completed
    dependencies:
      - trim-output-cols
  - id: upload-hpc
    content: 上传修正后脚本至 HPC CHATTIME/Chattime/scripts/
    status: completed
    dependencies:
      - compile-check
  - id: verify-report
    content: 确认最终 CSV 表头仅 MSE/MAE 且日志表仅打印 L/MSE/MAE
    status: completed
    dependencies:
      - upload-hpc
---

## 用户需求

确认当前复现任务为论文 **National ILI 预测**（L=24/36/48/60，K=6/Lp=24/S=2，70:10:20 切分），并修正最终报告口径。

## 产品概述

修正 `scripts/train_miflu.py` 的最终结果输出，使 National 复现的主报告严格对齐论文 National 表（仅 MSE / MAE），移除误混入的 RMSE / PCC 列，避免与 Regional 指标混淆。

## 核心功能

- 最终汇总 CSV（`results_miflu_paper_protocol_table_*.csv`）表头仅保留 `Horizon`、`MSE_ILI_mean/std`、`MAE_ILI_mean/std`，删除 `RMSE_ILI_*` 与 `PCC_ILI_*` 列。
- 终端日志的最终结果表仅打印 `L / MSE / MAE` 三列，删除 `RMSE` 与 `PCC` 列。
- per-rep 原始 CSV（`RESULTS_PATH`）仅写入 `mse_ili` 与 `mae_ili`，不再写入 `rmse_ili` 与 `pcc_ili`。
- `evaluate()` 内部仍照常计算并返回 PCC（及预测序列），本次仅停用其输出，保留底层计算逻辑与函数签名，避免牵动 `train_L` 与 NaN-rep 判定等既有引用。

## 技术栈

- 语言：Python 3.9（与 HPC `mlflu_hpc` 环境一致）
- 依赖：numpy、pandas、torch、transformers（仅沿用现有，无新增）
- 目标文件：`scripts/train_miflu.py`（本地权威副本，上传至 HPC `CHATTIME/Chattime/scripts/`）

## 实现方案

采用**最小切面修改**策略：仅剪除 PCC/RMSE 在「输出层」（per-rep 行、聚合表、CSV 表头、日志表格）的呈现，保留 `evaluate()` 的计算与返回结构。原因：

1. PCC 计算逻辑本身无害，保留它可继续作为诊断信息（例如 NaN-rep 判定已依赖 `test_pcc_ili` 有限性检查，行 215），且改动返回值会级联影响 `train_L` 返回字典与 `all_rows` 多处引用，收益不抵风险。
2. 论文 National 表（MIFlu_Complete_Extraction.md 第 226–314 行）仅用 MSE/MAE，移除 RMSE/PCC 列即完成口径对齐，无需改训练或评估数学。

性能与可靠性：本次为纯输出层裁剪，无新增计算开销；`evaluate()` 仍执行 `np.corrcoef`（O(n) 轻量），不影响训练热路径。改动范围小、向后兼容，不触碰 best-val 选择、checkpoint 导出、切分逻辑。

## 实现要点（执行细节）

- 复用现有 `all_rows` / `summary` / `result_table` 构建模式，仅删除对应键，不引入新变量或分支。
- `rmse_ili` 在行 359 是 `np.sqrt(mse_ili)` 的派生值，直接删除该行即可，无需保留中间量。
- 日志表头（行 412）与逐行打印（行 417–420）同步删列，保持表头与数据列数一致，防止格式错位。
- 保留 `evaluate()` 返回值中的 `pcc_ili`（行 173）及 `train_L` 中 `test_pcc_ili` 字段（行 219、228），确保 NaN-rep 有限性检查（行 215）继续生效。

## 架构设计

本次为单文件输出层修正，不涉及架构变更。数据流维持：
`evaluate()` 计算指标 → `train_L` 收集返回 → `main()` 汇总 `all_rows` → 聚合 `summary` → 写出 CSV + 日志表。
仅在 `main()` 汇总与打印环节裁剪列，上游计算链不变。

## 目录结构

```
scripts/
└── train_miflu.py   # [MODIFY] 裁剪最终报告中的 RMSE/PCC 列。
                      # 修改点：(1) 行 357-360 all_rows.append 删除 rmse_ili/pcc_ili；
                      # (2) 行 393-397 summary.agg 删除 rmse/pcc 聚合；
                      # (3) 行 399-404 rename 删除 RMSE_ILI_*/PCC_ILI_* 映射；
                      # (4) 行 412-420 日志表头与逐行打印仅保留 L/MSE/MAE。
                      # 不动 evaluate()、train_L 返回结构、best-val、导出逻辑。
```