---
name: MIFlu_DualTrack_Experiments_no_text_ln_gated_inject
overview: 为论文"双轨"核心叙事补跑两个缺失实验：no_text_ln（证明移除 text LayerNorm 后失去"统计捷径"、MSE 退化）与 gated_inject（证明 ModalityAligner 门控注入 + 前2层部分解冻成功激活跨模态注意力、MSE 低于 baseline）。需在 miflu_model.py 实现 ModalityAligner 并打通 use_text_ln/gated_inject/unfreeze_first_k 开关，在 train_ablation.py 登记两个变体并透传参数，随后生成两个 gpu_a100 分区 sbatch 作业并提交（当前 519289/519290 占 2/4 槽，留 2 槽正好并行）。
todos:
  - id: patch-miflu-model
    content: 在 miflu_model.py 新增 ModalityAligner、use_text_ln/gated_inject/unfreeze_first_k 开关并改 forward 分支
    status: completed
  - id: wire-train-ablation
    content: 在 train_ablation.py 注册 no_text_ln/gated_inject 变体并透传新参数至 MIFlu 与 argparse
    status: completed
    dependencies:
      - patch-miflu-model
  - id: local-smoke
    content: 本地构造两个新变体跑一次小前向，确认形状与开关生效、import 无误
    status: completed
    dependencies:
      - wire-train-ablation
  - id: make-submit-scripts
    content: 创建 submit_journal_job3.sh(no_text_ln) 与 submit_journal_job4.sh(gated_inject)，gpu_a100 分区
    status: completed
    dependencies:
      - patch-miflu-model
  - id: upload-and-submit
    content: scp 重传 miflu_model.py/train_ablation.py/两 submit 脚本至 HPC，提交两作业
    status: completed
    dependencies:
      - local-smoke
      - make-submit-scripts
  - id: verify-queue
    content: squeue 确认两作业进入 R 或 PD，回报 Job ID 与状态
    status: completed
    dependencies:
      - upload-and-submit
---

## 用户需求

为期刊证据链补齐论文"双轨"叙事中最核心的两个实验，立即在 Burgundy `gpu_a100` 分区（当前 519289/519290 占 2 槽，剩 2 槽可并行）提交两个新作业：

- **实验 3 `no_text_ln`（Track 1 统计捷径证明）**：标准 MIFlu 架构、LoRA 开启，但**显式关闭 text LayerNorm**。预期 MSE 从 ~1.81 退化到 ~2.28，证明文本并非经 Attention 起作用，而是经 LN 统计捷径。10 reps × 20 epochs × 1025 行全窗。
- **实验 4 `gated_inject`（Track 2 第三条路架构）**：MIFlu 架构注入提出的 **`ModalityAligner`（Gated Injection，门控交叉注意力对齐）** 于 forecasting LLM 之前，剩余层加 LoRA，**前 2 个 GPT2 层完全解冻**。预期激活跨模态注意力并将 MSE 降到 baseline 之下。10 reps × 20 epochs × 1025 行全窗。

## 交付内容

1. `miflu_model.py`：新增 `use_text_ln` / `gated_inject` / `unfreeze_first_k` 开关与 `ModalityAligner` 模块。
2. `train_ablation.py`：注册 `no_text_ln`、`gated_inject` 两个变体并透传新开关。
3. `scripts/submit_journal_job3.sh`（`no_text_ln`）、`scripts/submit_journal_job4.sh`（`gated_inject`），`gpu_a100` 分区。
4. 重传改动文件至 HPC、提交两作业、回报 Job ID 与 R/PD 状态。

## 技术栈

- Python 3.9 + PyTorch 2.5.1 (CUDA 11.8)，Slurm `sbatch` 投递至 Burgundy `gpu_a100` 分区（`--gres=gpu:a100:1 --time=04:00:00`，QOS 允许每用户 4 作业，当前剩 2 槽）。
- 改动严格沿既有 `miflu_model.py` / `train_ablation.py` 架构，不引入新依赖。

## 实现方案

### 1. `miflu_model.py` — `ModalityAligner`（新增类）

门控交叉注意力对齐：以时间 patches 为 query、文本为 key/value 做 cross-attention，得到与 `htime` 同形的对齐特征，再用一个可学习标量 gate（sigmoid）按比例注入，最后 LayerNorm：
`aligned = CrossAttn(query=htime, key=htext, value=htext); g = sigmoid(gate); hfuse = ln(htime + g * aligned)`
仅当 `gated_inject=True` 时实例化并走此分支。

### 2. `ForecastingLLM` / `MIFlu` 新增参数

`ForecastingLLM.__init__(..., use_text_ln=True, gated_inject=False, unfreeze_first_k=0)`：

- `use_text_ln=False` → `self.text_ln = nn.Identity()`（移除归一化，复现"去捷径"退化）。
- `unfreeze_first_k=k` → 前 k 个 block 全部 `param.requires_grad=True`（部分解冻）；其余层维持原"冻结 + ln_1/ln_2 可训 + MHA LoRA"。
- `MIFlu.__init__` 透传上述三参数给 `ForecastingLLM`。

### 3. `ForecastingLLM.forward` 分支

- `gated_inject`：先 `hfuse = self.modality_aligner(htime, htext)`（无文本前缀），之后 positional encoding + blocks 同原逻辑；`hforecast = hidden[:, :self.total_patches, :]`（取完整序列，因无文本前缀）。
- 默认：维持现有 `htext = self.text_ln(htext); hfuse = cat([htext, htime])` 与取尾部 `total_patches`。
- `MIFlu.forward` 不需改（开关由 `__init__` 状态决定）。

### 4. `train_ablation.py` 接线

- `variants` 字典新增：
- `"no_text_ln": {"use_text": True, "use_lora": True, "use_text_ln": False, "prompt_fn": build_prompt, "name": "w/o text LayerNorm"}`
- `"gated_inject": {"use_text": True, "use_lora": True, "gated_inject": True, "unfreeze_first_k": 2, "prompt_fn": build_prompt, "name": "ModalityAligner (gated)"}`
- `train_L(...)` 与 `export_prediction_csv(...)` 增加同名形参并透传至两次 `MIFlu(...)` 构造。
- `--variant` 的 `choices` 增加 `no_text_ln`、`gated_inject`，日志打印新开关。

### 5. 提交脚本与 HPC 同步

- 两个 `submit_*.sh`：`#SBATCH --partition=gpu_a100 --gres=gpu:a100:1 --time=04:00:00`，分别跑 `python scripts/train_ablation.py --variant no_text_ln|gated_inject --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 --export-dir hpc_results/journal_evidence/<v>/reps_1_to_10`。
- **关键**：HPC 不自动同步；改完本地 `miflu_model.py`/`train_ablation.py`/两脚本后必须 `scp` 重传，且作业在启动时刻只读代码，不影响在跑的 519289/519290。
- 并发写 `data/scaler_miflu_national.json` 无害（由 raw train 确定性拟合，内容一致）。

## 关键代码结构

```python
class ModalityAligner(nn.Module):
    def __init__(self, D=768, n_heads=8):
        # cross-attn (time query, text kv) + learnable scalar gate + LayerNorm
    def forward(self, htime, htext) -> torch.Tensor:  # (B, total_patches, D)

# ForecastingLLM.__init__ 新增:
#   use_text_ln: bool = True
#   gated_inject: bool = False
#   unfreeze_first_k: int = 0
# MIFlu.__init__ 新增并透传: use_text_ln, gated_inject, unfreeze_first_k
```

## 验证

- 本地自测：`python -c "import miflu_model"` 与构造 `MIFlu(gated_inject=True, unfreeze_first_k=2)` / `MIFlu(use_text_ln=False)` 跑一次小前向，确认形状与开关生效。
- HPC：提交后 `squeue -u sychan552` 确认两作业 R 或 PD；待其落盘后 `aggregate_journal_tables.py` 汇总（与 519289/519290 同目录结构，互不污染）。