---
name: Q6_attention_claim_correction
overview: 修正 Q6 中对"38.6% 文本注意力"的误读：改为如实表述"原版架构平均文本注意力仅 0.526× 机会水平（低于随机），文本被稀疏定点使用；'文本确实参与预测'的硬证据来自 no_multi 功能消融，而非注意力质量"。新增订正说明原论文"多模态注意力是关键机制"未被注意力模式支持，且真正高路由的 ModalityAligner 不在原论文中。同步回写 .docx 并验证双格式一致；并按已批准的"1. yes"补跑 6 个缺失权重文件的变体于 HPC。
todos:
  - id: correct-q6-md
    content: 修正 .md 中 Q6 对 38.6% 的误读表述与证据表
    status: completed
  - id: regen-docx-parity
    content: 由 .md 重生成 .docx 并运行 parity 校验
    status: completed
    dependencies:
      - correct-q6-md
  - id: update-changelog
    content: 在变更日志追加 Q6 修正条目
    status: completed
    dependencies:
      - correct-q6-md
  - id: inspect-hpc-patterns
    content: 读取 HPC_GUIDE 与训练脚本确定 6 个缺失变体
    status: completed
  - id: submit-missing-hpc
    content: 提交 6 个缺失变体的 HPC 训练作业
    status: completed
    dependencies:
      - inspect-hpc-patterns
  - id: verify-hpc-checkpoints
    content: 确认 6 个 HPC 作业产出 checkpoints 与 summary.csv
    status: completed
    dependencies:
      - submit-missing-hpc
---

## 用户需求

1. 复核 Q6 报告中"原版架构 38.6% 注意力落在文本上"是否受 modality aligner 污染（用户记忆 text→time 占比 < 0.001）。
2. 补跑 6 个缺失权重文件的实验变体（no_multi、no_lora_multi、Q4 四配方），以补齐顶刊证据链。

## 产品概述

修订导师五大疑问回复报告（Q6 节），纠正一处误读的数字表述，并补齐 HPC 上缺失的模型权重产物，确保 .md / .docx 双格式一致、证据完整可提交。

## 核心功能

- 澄清 38.6% 来源：确认来自基础 full 模型（gated_inject=False），未被 modality aligner 污染；但重新判读为"平均文本注意力 0.526× 机会水平（低于随机），文本被稀疏定点使用"，修正原"文本被大量使用"的误读。
- 修正 Q6 证据表、判读、订正条款、建议与验证表，新增【订正4】说明"多模态注意力是关键机制"未被注意力模式支持（用户直觉部分成立，但"说谎/无法复现"仍不可证）。
- 由 .md 单一源重新生成 .docx，校验双格式一致（PARITY: OK）。
- 更新变更日志。
- 在 HPC stingy 分区提交 6 个缺失变体的训练作业，补齐 checkpoints 权重文件。

## 技术栈

- Python 3（项目现有），stdlib 生成 docx（`scripts/md_to_docx.py`，无外部依赖）
- Slurm HPC（stingy 分区 / A100），训练入口 `train_ablation.py` 与 Q4 配方定义
- 单一源管线：`.md` → `md_to_docx.py` → `.docx` → `verify_report_parity.py`（只读校验）

## 实现方法

- **Q6 修正（仅改报告表述，不动数据脚本）**：`q6_text_attention_audit.py` 与 CSV 数据均正确，误读在报告文字。修正要点：
- `full_L24` 配置为 `gated_inject=False`、目录 `full_H24` → 属于基础模型，**与 modality aligner 无关**，污染担忧不成立。
- 但 `observed_text_mass=0.3858` vs `chance_text_mass=0.7347` → `mass_ratio_vs_chance=0.5256`（<1，低于随机因果基线）。故"文本被大量使用"是误读；真实信号是**峰值 34×**（稀疏定点使用）。
- 用户记忆的 `<0.001` 对应 modality aligner 的 `observed_text_mass=0.00271`（恰好均匀，1.000×），与基础模型 38.6% 是两套不同统计量，不矛盾。
- 文本"确实参与预测"的**唯一硬证据**是 `no_multi` 功能消融（ΔMSE +0.705, p=0.011），而非注意力质量。
- **HPC 补跑**：复用既有 `submit_*.sh` 模板与 `train_ablation.py` 配方定义，构造 6 个变体提交脚本，沿用 `--mem=16G`（此前默认 1024MB 曾 OOM）与 stingy/A100。

## 实现注意

- 严格保持 `.md` 为唯一可编辑源，`.docx` 永远由脚本再生，杜绝双份漂移。
- 重跑 `verify_report_parity.py` 确认 PARITY: OK（502 单元）后再交付。
- HPC 作业从 checkpoint 输出头自动推断 horizon，避免 L 错配（此前 full/ 误取 L=60）。
- 日志复用现有 logger，不写敏感信息；HPC 作业状态以 `sacct`/`squeue` 轮询确认。

## 架构设计

- 文档管线：`.md`（single source）→ `md_to_docx.py` → `.docx` → `verify_report_parity.py`（只读校验一致性）。
- HPC 训练：`train_ablation.py` 接收变体标志 → 产出 `checkpoints/<variant>/` 权重与 `results/ili/metrics/*summary.csv`。
- 二者解耦：文档修正不依赖 HPC，可并行推进。

## 目录结构

```
project-root/
├── MIFlu_导师五大疑问_回复报告.md          # [MODIFY] Q6 节（第335-461行）：修正证据表(368-373)、判读1(377)、新增【订正4】(436后)、建议1(442)、验证表#1(453)
├── MIFlu_导师五大疑问_回复报告.docx        # [REGEN] 由 md_to_docx.py 从 .md 重新生成，保持双格式一致
├── CHANGELOG_2026-09-02_导师报告更新.md   # [MODIFY] 追加 Q6 修正条目（38.6% 误读说明 + 订正4）
├── scripts/
│   ├── md_to_docx.py                       # [REUSE] 由 .md 生成 .docx（stdlib）
│   └── verify_report_parity.py             # [REUSE] 只读校验 .md/.docx 一致（PARITY: OK 期望 502 单元）
├── hpc_scripts/
│   └── submit_missing_*.sh                 # [NEW] 6 个缺失变体的 Slurm 提交脚本（no_multi / no_lora_multi / 4 个 Q4 配方）
└── checkpoints/
    └── <variant>/reps_1_to_10/rep_01/checkpoints/  # [NEW] HPC 作业产出的权重文件
```