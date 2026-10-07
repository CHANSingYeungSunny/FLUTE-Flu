---
name: 文本路径_bug_审查与修复
overview: 对照 MIFlu 论文 Section III/IV（尤其 IV-A 文本 embedder、IV-C 融合与 h_fuse 丢弃逻辑），审查我们文本路径实现，定位为何文本组件仅贡献 +3.4% 增益（论文 +18.4%），并给出可执行的修复验证方案。
todos:
  - id: read-paper-text
    content: 精读 MIFlu_paper.md Section IV-A/IV-C/Table X/Fig 1，逐条列出文本融合的论文规范
    status: completed
  - id: audit-text-ln
    content: 核对 text_ln 是否为论文所有；若论文无，移除 miflu_model.py 中 text_ln 定义与调用
    status: completed
    dependencies:
      - read-paper-text
  - id: audit-pe-prompt
    content: 核对位置编码拼接方案与 prompt 模板/统计口径/OT 是否与论文一致，修复不符项
    status: completed
    dependencies:
      - read-paper-text
  - id: run-notext-ablation
    content: 在 paper 窗口重跑 w/o LoRA（仅文本）ablation 10 reps，目标 MSE≈1.570
    status: in_progress
    dependencies:
      - audit-text-ln
      - audit-pe-prompt
  - id: summarize
    content: 汇总文本路径修复结论与增益提升幅度，更新 memory
    status: pending
    dependencies:
      - run-notext-ablation
---

## 用户需求

对照论文 MIFlu_paper.md 审查文本路径（textual_embedder.py + miflu_model.py 融合逻辑），定位为什么"仅文本（w/o LoRA）"变体在我们的实现里只带来 +3.4% 增益（MSE 1.909 vs 基线 1.976），而论文 Table VIII 中该变体带来 +18.4% 增益（1.570 vs 1.925）。目标是找出文本路径中的实现 bug 并予以修复，使文本组件在 paper 窗口（行 20-985）上复现论文量级的增益。

## 核心功能

- 逐字核对论文 Section IV-A / IV-C / 附录 Table X 对文本嵌入与融合的描述
- 审查代码：text_ln 额外归一化、位置编码拼接方案、prompt 模板与统计口径、OT 第 7 变量、文本 token 数
- 修复确认的 bug，并在 paper 窗口重跑 w/o LoRA（仅文本）ablation（10 reps）验证文本增益接近论文 1.570

## 视觉/功能效果

无 UI 改动，属于模型逻辑层审查与修复；最终通过 HPC 上的 ablation 数值（MSE/MAE）验证文本组件增益是否达到论文水平。

## 技术栈

- 现有项目：Python + PyTorch + transformers（GPT2），HPC（CityUHK Burgundy, stingy 分区 A100）训练
- 仅修改现有 `scripts/textual_embedder.py`、`scripts/miflu_model.py`、`scripts/train_miflu.py`、`scripts/train_ablation.py`，不引入新依赖

## 实现方案

### 关键审查结论（已对照论文确认）

1. **候选 A（text_ln 额外归一化，最可能主因）**：论文 L170-174 仅将文本 embedder 的 `last_hidden_state`（已含 GPT2 内部 ln_f）与 `h_time` concat，**未提及任何额外 LayerNorm 把文本缩放到时序尺度**。我们的 `miflu_model.py:267-270` 定义可训练 `text_ln = nn.LayerNorm(D)` 并在 L304 调用，会把文本语义幅度压成单位方差，可能抹掉文本承载的统计/领域信息，导致文本信号退化为近似噪声，符合"+3.4% 弱增益"。需移除或与论文逐字核对；若论文无此步，应删除 `text_ln` 及调用，让 h_text 直接 concat。
2. **候选 B（位置编码冲突）**：文本 367 token 占位置 0..366（GPT2 语言位置），时序 patch 占 367+。论文 IV-C 仅说 PE 加到 h_fuse，未明确文本是否复用 wpe 0..366。需核对 Fig 1 右半确认；若论文文本用独立/偏移段而我们复用 0..366，则文本位置先验干扰融合。
3. **候选 C（prompt 统计口径）**：`compute_prompt_stats` 用 `train_df[col].min()/max()` 填模板，论文 Table X 用 `<min(X_train)>`/`<max(X_train)>`。需确认 `train_df` 子集与论文训练集切分一致（我们 70/10/20 vs 论文）。
4. **候选 D（OT 第 7 变量）**：OT 是我们自定义（=num_patients），论文未给公式；prompt 第 (7) 描述若与论文不符会削弱文本增益。
5. **候选 E（文本 token 数）**：`prompt_cache.shape[1]=367`，需核对论文实际模板 token 数是否一致。

### 执行策略

- 先做**只读核对**：精读 MIFlu_paper.md Section IV-A、IV-C、附录 Table X、Fig 1 描述，逐条比对代码，确定哪些是我们自行添加（论文无）、哪些与论文不符。
- 按"移除论文没有的操作（text_ln）→ 核对位置编码 → 核对 prompt 口径 → 核对 OT"优先级修复。
- 每修一项即跑 **w/o LoRA（仅文本）ablation（paper 窗口，10 reps）**，目标 MSE≈1.570；用控制变量法定位主因，避免一次性改多处无法归因。
- 文本 embedder 改 CPU 跑、LoRA 已修为 Q/K/V 独立均保留，不回退。

### 性能与可靠性

- ablation 单 L=24 约 12 分钟（单 rep）或 ~30 分钟（10 reps）；用 `--horizon 24 --reps 10` 控制成本
- 复用现有 `train_ablation.py` 的 `no_lora` 变体（use_text=True, use_lora=False），仅换 `--window paper`
- 不改动 GPT4TS 基线（已 +2.7% 复现），保证窗口正确性锚点不变

## 实现注意

- 修改 `miflu_model.py` 时保持 `ForecastingLLM.forward` 的 concat/PE/丢弃文本 token 结构（与论文 L202-225 一致），只调整 text_ln 与位置编码细节
- 所有改动需同步上传 HPC 后重跑（HPC_GUIDE §6：本地改须重传）
- stingy 分区直接用，不加 exclude/nodelist（之前误加导致调度黑洞）

## 架构设计

文本路径：TextualInputEmbedder(GPT2 frozen) → h_text → [可选 text_ln] → concat[h_text||h_time] → +PE → GPT2 K层(+LoRA) → 丢弃文本 token → output_projection
修改仅发生在 `[可选 text_ln]` 与 PE 段，不改变整体数据流。

## 目录结构（将修改/新建）

```
scripts/
├── miflu_model.py          # [MODIFY] 审查/移除 text_ln(L267-270,304)；核对位置编码(L308-311)；forward 丢弃逻辑(L331-333) 保持
├── textual_embedder.py     # [MODIFY] PROMPT_TEMPLATE_7 逐字核对；compute_prompt_stats 口径；VAR_COLS/OT 处理
├── train_miflu.py          # [CHECK] 调用 text_ln 处；train_df 来源（70/10/20 切分）
└── train_ablation.py       # [REUSE] no_lora 变体跑 paper 窗口复测
MIFlu_paper.md              # [READ] Section IV-A/IV-C/Table X/Fig 1 逐字核对依据
```

## 关键代码结构（待核对）

- `miflu_model.py` 中 `text_ln` 定义与调用（是否论文所有）
- `textual_embedder.py` 中 `compute_prompt_stats` 返回的 min/max 子集是否与论文训练集一致