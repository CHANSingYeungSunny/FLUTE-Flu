---
name: align-lora-llm4ts-recipe
overview: 对齐 MIFlu 所 follow 的 LLM4TS [36] LoRA 训练配方（alpha=r×8、AdamW、小 lr、epochs≈15），验证 no_multi（无文本有 LoRA）能否从 2.40 降到论文 1.647 附近，定位 LoRA 配置是否为复现差距主因。
todos:
  - id: align-lora-alpha
    content: 修改 miflu_model.py LoRA alpha 默认 4→32(scaling=8)，同步 LoRALinear 签名
    status: completed
  - id: align-optimizer
    content: 改 train_ablation.py 用 AdamW，lr=1.8e-5，epochs=15，加 lora_alpha 配置
    status: completed
    dependencies:
      - align-lora-alpha
  - id: probe-no-multi
    content: 上传 HPC 跑 no_multi paper 窗口 L=24 网格(alpha 32/64 × lr 1.8e-5/5e-5, 各2rep)
    status: in_progress
    dependencies:
      - align-optimizer
  - id: verify-lora-cause
    content: 分析 no_multi MSE 是否接近论文 1.647，确认 LoRA 配方为主因
    status: pending
    dependencies:
      - probe-no-multi
  - id: extend-full
    content: 若验证通过，扩到 full 变体 paper 窗口 10 reps 复测，目标接近 1.436
    status: pending
    dependencies:
      - verify-lora-cause
---

## 用户需求

基于前期论文审查与 LLM4TS [36] 源码调研，将 MIFlu 的 LoRA 训练配方对齐到 LLM4TS（arXiv:2308.08469）已披露配置，以验证"LoRA 配置错误"是否为复现差距（full 1.928 vs 论文 1.436，no_multi 2.40 vs 论文 1.647）的主因。

## 产品概述

无 UI。属于模型训练逻辑层的配置对齐与消融验证：修改 LoRA 的 alpha/scaling、优化器（Adam→AdamW）、学习率与训练轮数，使其贴近 LLM4TS [36] 的实证配方，并在 HPC 上用控制变量法跑 no_multi（无文本有 LoRA）探针，确认 LoRA 增益是否从负优化转为正向。

## 核心功能

- 将 LoRA alpha 从 4 调整为 32（scaling=alpha/r=8，匹配 [36] 的有效缩放；r 保持论文规定的 4）
- 优化器由 Adam 改为 AdamW，学习率降到 LLM4TS DFT 量级（~1.8e-5），训练轮数对齐 15
- 在 paper 窗口（行 20-985）跑 no_multi（w/o multimodality，无文本有 LoRA）小网格探针：alpha∈{32,64} × lr∈{1.8e-5,5e-5}，各 2 reps，目标 MSE 接近论文 1.647
- 若 no_multi 显著下降，确认 LoRA 配方为主因，再扩展到 full 变体 + 10 reps 复测
- 保留已修复的 LoRA Q/K/V 独立实现，不回退

## 技术栈

- 现有项目：Python + PyTorch + 手写 LoRALinear（miflu_model.py），HPC（CityUHK Burgundy, stingy 分区）训练
- 不引入 PEFT 库依赖（保持手写 LoRALinear，仅修正 scaling 以匹配 [36] 的 alpha/r 语义）
- 仅修改 scripts/miflu_model.py（alpha 默认值）、scripts/train_ablation.py（CONFIG 与 optimizer）

## 实现方案

### 关键依据（LLM4TS [36] 已披露配置）

- models/LLM4TS.py：peft target_modules=["c_attn"]，fan_in_fan_out=True，用 peft LoraConfig
- ETTh1_full/LLM4TS.json：peft_params_r=8, lora_alpha=64（scaling=8）, dropout=0, AdamW, SFT lr=7.9e-5(5ep), DFT lr=1.8e-5(15ep)
- 两阶段 lp_ft：Stage1 冻结主干只训 output；Stage2 解冻 input_layer + 仅 lora。MIFlu 论文 no_lora 明确训 PE+LN，故我们保持"训 PE+LN+LoRA"结构（与 MIFlu 文本一致），仅对齐 LoRA 缩放/优化器/lr/epochs

### 关键决策

1. **alpha 修正**：论文 r=4（override [36] 的 8），但 alpha 论文未披露。按 [36] 的 scaling=alpha/r=8 推算，r=4 时应 alpha=32（scaling=8）；同时探针试 alpha=64（scaling=16）看是否更好。我们当前 alpha=4（scaling=1）是 LoRA 几乎无效的主因。
2. **优化器/学习率**：[36] 用 AdamW + 小 lr（DFT 1.8e-5）。我们当前 Adam + 5e-4 过大导致 LoRA 过冲为负优化。改用 AdamW，主 lr 降到 1.8e-5~5e-5。
3. **epochs**：对齐 [36] DFT=15（我们 20 接近，保持 15~20）。
4. **先 no_multi 隔离验证**：no_multi 无文本，排除文本融合干扰，纯测 LoRA 配方是否有效。若 no_multi 从 2.40 降到 ~1.647，证明 LoRA 是主因。

### 实现注意

- 修改 apply_lora_to_gpt2_attention 的 alpha 默认值（L74）与 LoRALinear（L43）初始化签名保持一致
- train_ablation.py L208 的 Adam 改为 AdamW；CONFIG 增加 lora_alpha、调整 learning_rate/epochs
- 复用现有 --lora-lr 双 param group 机制（L74, L193-206），让 LoRA 与 base（PE/LN）可分别设 lr
- 所有本地修改须重传 HPC 后重跑（HPC_GUIDE §6）
- stingy 分区直接提交，不加 exclude/nodelist

## 架构设计

LoRA 路径：GPT2 c_attn(frozen) → +LoRA delta(scaling=alpha/r) 到 Q/K/V → causal attention → 输出。修改仅影响 LoRA 的 scaling 因子与优化器配置，不改变 concat/PE/丢弃文本 token 的数据流。

## 目录结构

```
scripts/
├── miflu_model.py      # [MODIFY] L74 apply_lora 默认 alpha=32（原4）；L43 LoRALinear alpha 默认同步；保持 Q/K/V 独立
└── train_ablation.py   # [MODIFY] L32 CONFIG: learning_rate→1.8e-5, epochs→15, 增 lora_alpha=32; L208 Adam→AdamW; 复用 --lora-lr
```

## 关键代码结构

- apply_lora_to_gpt2_attention(block, r=4, alpha=32.0)  # scaling=alpha/r=8，匹配 [36]
- LoRALinear(in_features, out_features, r=4, alpha=32.0)  # delta=(x@A^T@B^T)*(alpha/r)