---
name: MLFlu_paper交叉参考与scaler_convention勘误
overview: 将交叉参考唯一来源统一为 MIFlu_paper.md（确认其为完整 PDF 转换），勘误 scaler_convention_supplement.md 两处错误结论，并订正仍残留旧协议/旧提取文件引用的文档。
todos:
  - id: confirm-paper-md
    content: 确认 MIFlu_paper.md 为完整 PDF 转换（Tables V/VI/VII/VIII 逐字），作为唯一交叉参考源
    status: completed
  - id: sweep-stale-refs
    content: Use [subagent:code-explorer] 扫描全项目残留的 MIFlu_Complete_Extraction.md 引用及旧提取文件推导结论，输出清单
    status: completed
    dependencies:
      - confirm-paper-md
  - id: fix-scaler-doc
    content: 勘误 docs/scaler_convention_supplement.md：修正 pooled-fit 线性缩放数学错误与 CDC 过度结论，重定性为未确认部分解释
    status: completed
    dependencies:
      - sweep-stale-refs
  - id: fix-obstacle-doc
    content: 订正 MIFlu 复现障碍分析.md：L4/L32/L53/L66-75 改回权威协议（L=24/36/48/60 四档），统一 OT 口径，标注旧表
    status: completed
    dependencies:
      - sweep-stale-refs
  - id: fix-plan-doc
    content: 在 .codebuddy/plans/MLFlu文档精简与文件清理_3e491920.md L31/L65 加注现统一指向 MIFlu_paper.md
    status: completed
    dependencies:
      - confirm-paper-md
  - id: fix-remote-state
    content: SSH 只读确认远端 PROJECT_STATE.md 含旧提取文件引用后改指向 MIFlu_paper.md
    status: completed
    dependencies:
      - confirm-paper-md
  - id: option3-cdc-check
    content: 并行核查 ILITOTAL 数据源/定义是否与论文一致，将 CDC 区间内回溯修订列为未排除候选（Option 3）
    status: completed
    dependencies:
      - fix-scaler-doc
---

## 用户需求

1. **确认 `MIFlu_paper.md` 性质**：确认为论文 PDF 的直接 markdown 完整转换（非摘要/提炼）。已核实：含完整 Abstract、I–VII 全章节、Tables V/VI/VII/VIII 逐字内容（MIFlu_paper.md L314-412）、IEEE JBHI 2025 头版信息，确为完整转换，是安全权威的交叉参考源。
2. **统一交叉参考约定**：在 MEMORY.md、`MIFlu 复现障碍分析.md`、`.codebuddy/plans/MLFlu文档精简与文件清理_3e491920.md`、远端 `PROJECT_STATE.md` 全部明确指向 `MIFlu_paper.md`，并清剿来自已删 `MIFlu_Complete_Extraction.md` 的其他残留结论（已知 instance-norm 声称已撤回，需扫描有无其他）。
3. **勘误 `docs/scaler_convention_supplement.md`**（用户最新聚焦）：

- 解释 codebuddy 如何做 pooled-fit 重缩放：1.609/0.847 来自 train-only 实测 5.056/1.500 的**代数重缩放**（MSE×(σ_train/σ_pooled)²、MAE×(σ_train/σ_pooled)），**未重新训练**（脚本 `_diag_baseline_check.py` L40/L67-69）。
- 修正错误 A：「仿射压缩大误差更狠、MSE 缩快 MAE 慢」是**数学错误**——StandardScaler 线性缩放对各误差均匀，不存在压缩大误差更狠。
- 修正错误 B：「CDC-vintage ruled out / moot」是**过度结论**——仅排除 2024+ 增量周，未排除 2002–2021 span 内 CDC 回溯修订。
- 将 pooled-fit 重新定性为「**未确认的部分解释**（MSE 4% / MAE 17% 不一致，非确认根因）」，train-only 仍为主结果，pooled 仅作带 caveat 的辅助对比。
- 并行推进 Option 3（核查 ILITOTAL 数据源/定义是否与论文一致，CDC 区间回溯修订未排除）。

## 技术栈

- 纯文档/Markdown 勘误与交叉参考统一，无代码逻辑改动、无模型重训、无 PDF 删除。
- 远端文件（`PROJECT_STATE.md`）经 HPC 节点 `hpclogin02`（`$HOME/scratch/CHATTIME/Chattime/`）只读确认后修改。

## 实施方案

### 关键结论（已探查确认）

- `MIFlu_paper.md` 为完整 PDF 转换（Tables V/VI/VII/VIII 逐字存在），可作唯一交叉参考。
- `docs/scaler_convention_supplement.md` 存在两处需勘误的结论：
- 错误 A：L34-36 的「affine rescale contracts large errors more」→ 线性缩放均匀，数学错误。
- 错误 B：L41/L52/L71-77/L83 的「CDC-vintage ruled out/moot」→ 仅排除 2024+ 周，未排除 2002–2021 区间内回溯修订。
- L44-53/L80-88 把 pooled-fit 写成「解释大部分 MSE gap」→ 应降为「未确认部分解释（MSE 4%/MAE 17% 不一致）」。
- `MIFlu 复现障碍分析.md`：L3 交叉参考已正确（指向 MIFlu_paper.md），但 L4/L32/L53/L66-75 仍把 L=52 walk-forward 当「当前主结论」，与 MEMORY.md 权威协议（L∈{24,36,48,60} 四档独立、L=52 已废弃隔离）矛盾，需订正为与权威协议一致；L59-62 旧表数字（13.33/5.77/6.25/1.77）系非法负值 bug 时代产物，与当前 5.056 不符，需标注或替换；L93 残留「OT=num_patients/100」与 L95 自纠的「全量未缩放」前后矛盾，需统一。
- `.codebuddy/plans/MLFlu文档精简与文件清理_3e491920.md`：L31/L65 仍提 `MIFlu_Complete_Extraction.md` 为当时唯一交叉参考，加注「现统一指向 MIFlu_paper.md」。

### 实施注意

- 严格遵守协议变更硬规则：仅**订正文档**使其与现存权威协议（L∈{24,36,48,60} 四档独立）一致，不发起任何协议变更。
- 不删除任何 PDF，不重训模型。
- 远端 `PROJECT_STATE.md` 需先 SSH 只读确认内容含旧提取文件引用后再改。
- pooled-fit 重缩放的数学说明须准确：设训练集标准差 σ_t、全序列标准差 σ_p，则同一组预测误差 e 在两者空间下满足 e'=e·(σ_t/σ_p)，MSE'=MSE·(σ_t/σ_p)²、MAE'=MAE·(σ_t/σ_p)，对所有误差点**同一比例**，无非线性压缩。

## 目录结构与待修改文件

```
MLFlu/
├── docs/
│   └── scaler_convention_supplement.md   # [MODIFY] 勘误 pooled-fit 数学解释 + CDC 结论，重定性为未确认部分解释
├── MIFlu 复现障碍分析.md                  # [MODIFY] L4/L32/L53/L66-75 订正为权威协议（L=24/36/48/60 四档）；L59-62 旧表标注；L93 与 L95 OT 口径统一
├── .codebuddy/
│   ├── memory/
│   │   └── MEMORY.md                       # [VERIFY] L45-46 已正确，确认无旧提取文件残留引用
│   └── plans/
│       └── MLFlu文档精简与文件清理_3e491920.md  # [MODIFY] L31/L65 加注现统一指向 MIFlu_paper.md
└── (远端) $HOME/scratch/CHATTIME/Chattime/PROJECT_STATE.md  # [VERIFY+MODIFY] SSH 确认后改指向 MIFlu_paper.md
```

# Agent Extensions

<section>

## Agent Extensions

- **SubAgent**: code-explorer
- Purpose: 跨文件扫描 `MIFlu_Complete_Extraction.md` 残留引用，以及「instance-norm」「OT=num_patients/100」「pooled explains」等来自旧提取文件或错误推导的结论，确保全部清剿。
- Expected outcome: 输出所有仍引用已删提取文件或与其相关的未验证结论的文件与行号清单，供勘误步骤逐条处理。
</section>