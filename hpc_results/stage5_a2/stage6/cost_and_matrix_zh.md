# 八模型比较：矩阵、复用判定与实测成本

生成时间：2026-09-26（Asia/Hong_Kong）。
**状态：代码、矩阵、派发、锁定、评分、独立重算全部就绪并通过 CPU 校验；仅缺新增计算额度，因此未提交任何 GPU 作业。**

---

## 1. 八个模型 + 标签（不变更已冻结的架构标签）

| 组 | 模型 | 实现来源 | 忠实度标签（必须随结果一起报告） |
|---|---|---|---|
| 非 LLM | NLinear | `innovation/backbones/dlinear.py::NLinear` | 重实现（Zeng et al., AAAI 2023） |
| 非 LLM | DLinear | `innovation/backbones/dlinear.py::DLinear` | 重实现（Zeng et al., AAAI 2023） |
| 非 LLM | PatchTST-inspired | `innovation/backbones/patchtst.py` | **PatchTST-INSPIRED**：监督训练、无 RevIN、无自监督预训练、容量缩减（d_model=64 / 2 层）。**不是规范 PatchTST** |
| 非 LLM | iTransformer | `innovation/backbones/itransformer.py` | 重实现（Liu et al., ICLR 2024） |
| LLM | GPT-2 MIFlu | `scripts/miflu_model.py`（修正重构） | 修正重构：文本通路真实生效、验证集选模、七变量联合、`strict` 窗口 |
| LLM | Qwen Time-LLM | `innovation/backbones/llm_inspired.py::QwenTimeLLM` | **Time-LLM-INSPIRED**：冻结 Qwen2.5-1.5B、patch 原型重编程、Prompt-as-Prefix |
| LLM | CALF | `...::CALFInspired` | **CALF-INSPIRED**：冻结 GPT-2、并行时序/文本双分支、两个对齐损失 |
| LLM | TimeCMA | `...::TimeCMAInspired` | **TimeCMA-INSPIRED**：冻结 GPT-2、检索对齐、last-token 分支 |
| 机制消融 | no-text（`no_multi`） | `scripts/train_ablation.py` | **不计入八个模型**；它是机制消融，仍含预测 LLM |
| 基线 | Last Value / Seasonal Naive | `scripts/train_naive_966.py` | 确定性，各 4 个 L |

**规范 PatchTST 未包含。** 若要声称规范 PatchTST，需另行实现并单独计成本（`patchtst.py` 的 `architecture_report()` 已把三条偏离逐条列出）。

## 2. 统一协议（与 A2 完全一致）

| 项 | 值 |
|---|---|
| 数据 | `author_966`，完整 SHA-256 `31ffc169…b87a`，运行时逐次校验 |
| 划分 | 676 / 97 / 193，零基半开区间 |
| T / L | T=104；L ∈ {24,36,48,60}，各自独立训练 |
| seeds | 42 / 43 / 44，每 seed 重新初始化模型/优化器/调度器/最佳状态 |
| 窗口 | `--containment strict`，目标块完整落在所属划分；**不重新归属、不凑数** |
| 窗口数 | 549/74/170、537/62/158、525/50/146、513/38/134 |
| 缩放 | StandardScaler 仅拟合 `train[0:676)` |
| 选模 | 每 (模型, L, seed) 用**该 run 验证集七变量标准化 MSE** 选 checkpoint |
| 超参 | Adam lr=5e-4、batch 16、固定 20 epoch、无 scheduler、无 early stopping、fp32 |
| Test 隔离 | 全部拟合 `DEFER_TEST=1`；96 个 checkpoint 锁定后才统一评分 |
| 主指标 | `average_MSE_4L`：seed 内平均 → 4 个 L 等权平均，七变量标准化 MSE |
| 评分入口 | **单一** `scripts/score_test_stage5.py --stage6`（与 A2 同一份指标代码） |
| 独立重算 | `recovery/stage6/recompute_eight.py`（不导入任何模型代码） |

**协议同一性已执行证明**（job 586942）：

```
train_backbone_966 reuses the SAME objects: True True True
  (build_windows / load_and_normalize / eval_mse 与 A2 是同一对象)
L=24: train=549 val=74 test=170
L=36: train=537 val=62 test=158
L=48: train=525 val=50 test=146
L=60: train=513 val=38 test=134
```

即新运行器**直接 import** A2 的数据准备与窗口代码，不重新实现，因此协议一致性是构造性的，不是承诺。

## 3. 复用判定

| 模型 | 拟用拟合数 | 复用 | 依据 |
|---|---:|---:|---|
| MIFlu | 12 | **全部复用 A2** | 同一 `train_miflu.py`、同一 profile/strict/epochs/batch/seeds、同一 per-seed 验证选模 checkpoint、同一 `DEFER_TEST=1` 门。A2 的 12 个 checkpoint 已锁定并已归档（SHA-256 已记录） |
| NLinear | 12 | **全部复用 A2** | 同一 `train_nlinear_966.py` 与同一协议；A2 已锁定 12 个 per-seed checkpoint |
| no-text（消融） | 12 | **全部复用 A2** | 同一 `train_ablation.py`、`--variant no_multi`、同一协议 |
| DLinear | 12 | 新拟合 | 运行器已就绪 |
| PatchTST-inspired | 12 | 新拟合 | 同上 |
| iTransformer | 12 | 新拟合 | 同上 |
| CALF | 12 | 新拟合 | 同上，GPT-2 骨干本地缓存 |
| TimeCMA | 12 | 新拟合 | 同上，GPT-2 骨干本地缓存 |
| Qwen Time-LLM | 12 | 新拟合 | 同上，Qwen2.5-1.5B 本地快照 |
| 基线 | 8 | **全部复用 A2** | 确定性，A2 已评分且被独立重算验证 |

**最终配置拟合总数 = 96**（8 模型 × 4 L × 3 seed）。
**新拟合 = 72**（6 模型 × 12）。
**复用 = 24 学习拟合 + 8 基线 = 32。**

复用无回退风险：若任一 A2 checkpoint 的 SHA-256 与 `CHECKPOINT_LOCK.json` 不符，锁定步骤会 fail-closed 而不是静默重跑。

## 4. 实测成本（非外推）

**成本来源**：B 轨（1,025 行）`/home/sychan552/innovation_durable/screening/*/resource_usage.json` 中每个 run 的 `train_seconds`，共 8 个模型 × 4 个 L × 10 seeds = 320 个已完成 run 的真实计时。

**成本基础有效性已验证**（job 587011，CPU-only）：本轮六个新骨干的**可训练参数量与 B 轨逐项完全一致**，说明实现未变，因此 B 轨计时可直接用作成本依据。

| 模型 | L=24 | L=36 | L=48 | L=60 | 均值 s/fit | ×12 拟合 | GPU-h |
|---|---:|---:|---:|---:|---:|---:|---:|
| DLinear | 5.5 | 5.6 | 5.9 | 5.8 | 5.70 | 68.4 s | 0.0190 |
| PatchTST-insp | 8.1 | 8.0 | 8.9 | 8.5 | 8.38 | 100.5 s | 0.0279 |
| iTransformer | 8.2 | 8.2 | 8.5 | 9.0 | 8.48 | 101.7 s | 0.0282 |
| CALF | 20.1 | 20.4 | 20.0 | 20.2 | 20.18 | 242.1 s | 0.0673 |
| TimeCMA | 16.5 | 15.2 | 14.8 | 14.4 | 15.23 | 182.7 s | 0.0508 |
| **Qwen Time-LLM** | 319.2 | 353.7 | 323.5 | 358.3 | **338.68** | **4064.2 s** | **1.1289** |
| **合计（72 次新拟合）** | | | | | | **4759.6 s** | **1.3221** |

**交叉验证**：B 轨 `gpt2_miflu` 均值 147.3 s/fit；A2 实测 MIFlu 约 156 s/seed（469 s / 3 seeds）。两者同量级，说明该计时口径可用。

**修正与附加开销**：

| 项 | 量 | 依据 |
|---|---:|---|
| author_966 训练窗更少 | ×0.96 | 549 vs 572（L24）、513 vs 536（L60） |
| 骨干/资产加载 | +120 s | Qwen 4 个作业 × ~30 s（每 (骨干, L) 一个进程，内含 3 个 seed）；实测 CPU 加载 Qwen 1.5B 需 16 s，GPU 更快。GPT-2 三个模型可忽略 |
| 窗口构建 + 验证 | ×1.15 | 窗口构建在 CPU 上每次 ~3 s；B 轨 `train_seconds` 是否含每 epoch 验证未在元数据中标注，故加余量 |
| 统一评分（96 学习 + 8 基线） | +150 s | A2 评分 44 条记录实测 49 s（含 5 GB 哈希）；104 条且含 Qwen 推理 |
| 锁定（96 个 SHA-256） | +60 s | A2 锁定 36 个（5.0 GB）实测约 20 s；本轮 checkpoint 显著更小（冻结骨干不落盘） |
| 失败/重试余量 | ×1.15 | A2 实测失败率约 20%（主要为代码缺陷）；本轮代码已预检，风险更低 |

**合计估算 = 1.3221 × 0.96 × 1.15 + 0.33 ≈ 1.79 → 取整申请 1.8 GPU-h**，派发器内置停止规则（`BUDGET_GPU_H`，默认 1.8），在提交每个作业前检查已用量，超限即停并记录剩余矩阵。

**A0 的 GPU 需求（分开申请）**：

| 作业 | 内容 | 估算 |
|---|---|---:|
| A0-1 | 发布代码逐字重放，`pred_len=24`、`itr=1`、**发布默认** `train_epochs=1`、`lr=1e-4`、`multimodal=0` | ~0.25 GPU-h |
| A0-2 | 同上但 `multimodal=1`，用于数值确认文本不改变 Test 指标 | ~0.25 GPU-h |
| **合计** | | **~0.50 GPU-h** |

A0 每次 epoch 的成本高于 A2 的 MIFlu：发布代码对 3,843 个**单特征**样本训练（240 步/epoch）、序列长 42+317=359、且对 82.7 M 参数**全量微调**。文本梯度归零与文本替换零差异**已在 CPU 上证明**，因此 A0-2 的价值仅在于给出端到端的 Test feature-0 数值；若额度紧张，可只跑 A0-1。

## 5. 一次性新增额度请求

| 分支 | 拟提交作业数 | 拟合数 | 申请 GPU-h | 若不批准的后果 |
|---|---:|---:|---:|---|
| A0 最小诊断 | 2 | 2（各 1 epoch） | **0.5** | A0 停留在 CPU 诊断；已可给出全部结构性结论，但拿不到发布代码的 Test feature-0 数值 |
| 八模型比较 | 24 | 72 | **1.8** | 无法产出八模型统一比较；DLinear/PatchTST/iTransformer/CALF/TimeCMA/Qwen 六个模型在作者 966 行数据上没有任何结果 |
| **合计** | **26** | **74** | **2.3** | |

**可分开批准。** 若只批准 1.0 GPU-h：派发器按 `dlinear → patchtst → itransformer → calf_llm → timecma_llm → qwen_time_llm` 顺序执行，五个便宜模型合计仅 **0.193 GPU-h**，可在任何额度下完成；Qwen 单独占 1.13 GPU-h，是唯一的大块。

**已明确排除、未列入请求的项目**（原计划的全计算/扩展选项，需另行决定）：
- 2×2 文本/LoRA 完整矩阵（160 拟合）
- 十次重复（论文口径）替代三 seed
- 规范 PatchTST 实现
- 区域 / 小样本研究
- 引入新的骨干或数据集

## 6. 资源与依赖

| 项 | 值 |
|---|---|
| 分区 / 资源 | `stingy`，`--gres=gpu:a100:1`，`--mem=24G`（评分 32G），walltime 1 h；QOS 允许 1 运行 + 1 排队 |
| 环境 | `/home/sychan552/.conda/envs/mlflu_hpc/bin/python`（py3.9 / torch 2.5.1 / transformers 4.57.6） |
| GPT-2 | `/home/sychan552/.cache/huggingface/hub/models--gpt2`（`607a30d7…`） |
| Qwen2.5-1.5B | `/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/8faed761d45a263340a0528343f099c05c9a4323`，`local_files_only=True`，`trust_remote_code=False`（job 587011 已实测解析到该 revision） |
| 峰值显存 | Qwen 骨干 fp32 常驻约 3.1 GB + 激活；A2 的 MIFlu 实测峰值 1.43 GB。Qwen 为本轮最大单点，A100-80GB 余量充足，但**未实测**，属估算 |
| 存储 | 冻结骨干不落盘（key 集合写入 `.frozen_keys.json` sidecar）→ 72 个 checkpoint 预计 < 2 GB；scratch 余量充足（776 T 可用） |
| 网络 | 不需要。`TRANSFORMERS_OFFLINE=1`、`HF_HUB_OFFLINE=1` |

## 7. 提交方式（额度批准后）

```bash
# A0
sbatch recovery/a0/a0_gpu_minimal.sh          # 需先补该脚本，见下

# 八模型（自带停止规则与执行锁）
tmux new -d -s s6 'bash recovery/stage6/dispatch.sh --run'
# 结束后自动释放 results/stage6/logs/EXEC_LOCK

# 96 个 checkpoint 全部存在并锁定后
sbatch recovery/stage6/score_all.sh
```

`dispatch.sh` 在未加 `--run` 时只打印计划并退出，**不会误提交**（已在 job 中实测：`dispatch.sh is armed but NOT running`）。所有 Stage 脚本 `bash -n` 语法通过（`syntax_fail=0`）。

## 8. 统计与表述约束（提交前即固定）

- 三个 seed 只描述**优化随机性**，不是独立流感季，不构成重复实验。
- 不做时间区块不确定性分析：Test 仅 193 周、轨迹重叠、且含疫情期非平稳性，证据不足以支撑；只给描述性结论。
- **LLM vs 非 LLM 是两组各 4 个事先指定实现的描述性比较，不是"所有 LLM"的随机样本**，不得写成统计结论。
- 不把 B 轨（1,025 行）旧结果与本轮 A2/八模型数值拼成同一排名。
- A2 已锁定的原始结果继续保存，八模型输出写到 `results/stage6/`，**不覆盖**。
