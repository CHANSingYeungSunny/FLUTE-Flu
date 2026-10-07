---
name: verify-pe-position-candidate-b
overview: 基于 paper 窗口实测（full=1.928, no_lora=1.815, GPT4TS=1.976），文本增益仅 +8.1%（论文 +18.4%），且 LoRA 负优化。验证候选 B：文本 token 占 PE 0..366 把时序推到 367+，破坏 GPT2 时序位置先验，导致文本增益偏小。改 PE 拼接让文本用零/独立 PE、时序从 0 开始，重跑 no_lora 看是否→1.570。
todos:
  - id: fix-pe-separation
    content: 修改 miflu_model.py ForecastingLLM.forward：文本零 PE，时序从位置 0 起，保持因果 concat
    status: completed
  - id: upload-and-submit
    content: 重传 HPC 并提交 no_lora paper L=24（2-3 reps）消融 job
    status: completed
    dependencies:
      - fix-pe-separation
  - id: verify-candidate-b
    content: 查日志确认 no_lora MSE 是否从 1.815 降至 ~1.570，判定候选 B 是否主因
    status: completed
    dependencies:
      - upload-and-submit
  - id: next-step-or-summarize
    content: 若有效则更新 memory 结论；若无效则转查文本 embedder 表示质量
    status: completed
    dependencies:
      - verify-candidate-b
---

## 用户需求

针对 MIFlu 在 paper 窗口（行 20-985）的文本路径复现差距，验证"候选 B（PE 位置冲突）"是否为文本增益偏小（仅 +8.1%，论文 +18.4%）的主因，并予以修复。

## 核心功能

- 修改 `miflu_model.py` 的 `ForecastingLLM.forward`，让文本 token 不挤占 GPT2 的位置编码 0..366 段：文本 token 使用零 PE（或独立高位段），时序 patch 从位置 0 开始，保持"文本在前、时序在后"的因果注意力顺序不变。
- 在 paper 窗口重跑 `no_lora`（仅文本、无 LoRA）变体 L=24（2-3 reps），验证 MSE 是否从当前 1.815 降至接近论文 1.570。
- 若验证有效，确认 PE 冲突是文本增益偏小主因；若无效，转向核查文本 embedder 表示质量（文本语义/LN 间接机制）。
- 保留已修复的 LoRA Q/K/V 独立实现，不回退（full 变体后续仍使用）。

## 视觉/功能效果

无 UI 改动，属模型逻辑层的位置编码修正与消融验证；通过 HPC 上的 ablation 数值（MSE/MAE）确认 PE 修正是否提升文本组件增益至论文量级。

## 技术栈

- 现有项目：Python + PyTorch + transformers（GPT2），HPC（CityUHK Burgundy, stingy 分区 A40）训练
- 仅修改 `scripts/miflu_model.py` 的 `ForecastingLLM.forward` 位置编码段；不引入新依赖、不改变数据流结构

## 实现方案

### 关键依据（已查 paper 窗口实测 CSV）

- `full_paper_L24`: MSE_All=1.928；`no_lora_paper_L24`: MSE_All=1.815；`no_lora_multi_paper`: ≈1.976（GPT4TS 锚点）
- 同窗口对照：no_lora(1.815) vs GPT4TS(1.976) = 文本 +8.1%（论文 +18.4%，差距约一半）；full(1.928) vs no_lora(1.815) = LoRA 负优化 -6.2%（论文 LoRA 正 +8.5%）
- 前序 (Z) 诊断：frozen attention 下 time→text=1% → 文本不进 attention，增益仅来自 PE/LN 训练间接影响
- 候选 B 机制：文本 367 token 占 PE 0..366，时序从 367 开始，GPT2 wpe[367+] 预训练未充分见过 → 时序注意力位置先验被打乱，同时解释"文本增益偏小"与"LoRA 负优化"。论文 w/o LoRA=1.570 < GPT4TS 1.925，暗示论文文本不破坏时序 PE。

### 关键决策

1. **PE 分离（候选 B 修复）**：文本 token 加零 PE（不含语言位置先验），时序 token 用 `wpe[0..T_patch-1]`（从 0 开始）。Causal mask 保持文本在前，时序仍可 attend 文本，仅位置编码不冲突。这是对论文"文本不破坏时序 PE"最合理对齐，且最小改动。
2. **不回退 LoRA**：已修复的 Q/K/V 独立 LoRA 保留（alpha=32 等已对齐 [36]），本次只动 PE 段，full 后续仍用。
3. **控制变量验证**：仅改 PE 后重跑 no_lora（有文本无 LoRA）paper L=24，对比修改前 1.815。若降至 ~1.570 则确认候选 B 为主因；若仍 ~1.815 则文本增益偏小另有因（文本表示质量），转查 textual_embedder。
4. **复用现有提交链路**：沿用 `scripts/submit_ablation.sh`（已支持 `--lora-alpha`/`--lora-lr`、已去掉 nodelist），通过 `ABL_VAR=no_lora ABL_WIN=paper ABL_L=24` 提交。

### 性能与可靠性

- L=24 单 rep ≈ 2.5 min（A40），2-3 reps ≈ 6-8 min，成本极低；QOS 限制一次 1 job，串行提交即可。
- 修改仅影响 PE 加法，不改变 concat/attention/丢弃文本 token 结构，blast radius 小。
- 所有本地修改须重传 HPC 后重跑（HPC_GUIDE §6：本地改须重传）；stingy 分区直接提交，不加 exclude/nodelist。

## 实现注意

- `ForecastingLLM.forward` 当前 L325-339：`htext_aligned = self.text_ln(htext)` → `hfuse = cat([htext_aligned, htime])` → `positions = arange(total_len)` → `hfuse += wpe(positions)`。
- 改为：文本段 `pos_embeds_text = zeros_like(htext_aligned)`（或 `wpe` 高位独立段）；时序段 `pos_embeds_time = self.wpe(arange(htime.shape[1]))`；分别加到各自段再 concat。
- 保持 `htext` 在序列前（causal 允许时序 attend 文本），仅 PE 不挤占 0..366。
- `text_ln` 保留（已确认论文无此步但当前作为幅度对齐，本次不回退以免引入新变量；若 PE 修正后 no_lora 仍差，再单独评估 text_ln）。
- 同步更新日志/诊断打印（若有）避免误导。

## 架构设计

文本路径：TextualInputEmbedder(GPT2 frozen) → h_text → text_ln → [零 PE] → concat[text‖time] → [时序 PE 从 0] → GPT2 K层(+LoRA) → 丢弃文本 token → output_projection。
修改仅发生在"文本/时序 PE 分配"段，不改变整体数据流与注意力因果结构。

## 目录结构

```
scripts/
└── miflu_model.py          # [MODIFY] ForecastingLLM.forward L325-339：文本零 PE，时序从 0 起；保持 concat/因果/丢弃逻辑
（其余文件 train_ablation.py / textual_embedder.py / submit_ablation.sh 复用，不修改）
```

## 关键代码结构（待修改）

- `ForecastingLLM.forward` 中 PE 段：
- 原：`positions = torch.arange(total_len, ...); hfuse = hfuse + self.wpe(positions)`
- 新：`time_pe = self.wpe(torch.arange(htime.shape[1], device=...)); hfuse = torch.cat([htext_aligned, htime + time_pe], dim=1)`（文本段不加 wpe）