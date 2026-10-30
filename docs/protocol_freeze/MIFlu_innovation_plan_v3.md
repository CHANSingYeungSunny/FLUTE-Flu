# MIFlu 创新实验与评估计划 v3

```text
scientific_protocol_version = innov-v3.0
status                      = PREREGISTRATION (draft, internally validated)
supersedes                  = MIFlu_innovation_plan_v2.md (retained as immutable history)
```

本计划为 **v3 预注册**。本轮不下载权重、不实现/加载模型、不提交 Slurm 作业、不访问 Test 值、不生成结果图。

---

## 0. 与 v2 的关系

- v2（`innov-v2.0`）的全部证据保持**不可变历史**：runs、registries、冻结冠军 `nlinear`、
  一次性 Test 收据/清单/预测/指标/报告、选择与溯源审计、以及 2026-09-16 登录节点事故报告。
- v2 的 Test **已知**，不得被重新标注为"未触碰的 v3 holdout"。
- v3 使用独立根目录 `results/v3/` 与 `hpc_scripts/v3/`，不复用 v2 run ID、registry、
  Test 收据、frozen-winner 文件或最终报告。

## 1. 研究问题

在同一套公平、可复现的流感预测协议下，比较 **4 个代表性 Non-LLM 架构** 与
**4 个代表性 LLM-based 架构** 在预测精度、峰值预测、稳定性与计算效率上的差异。

主比较固定为 **4 vs 4**；两个廉价 naive 基线作为**参考下界**，不计入主架构；
LLM 负对照为**次级消融**，不是新增主候选。

## 2. 固定主候选集（8 个）

### Group A — Non-LLM

| model_key | display_name | fidelity | role |
|---|---|---|---|
| `nlinear` | NLinear | REFERENCE_FAITHFUL | 针对水平/分布漂移的归一化线性预测 |
| `dlinear` | DLinear | REFERENCE_FAITHFUL | 基于分解的线性预测 |
| `patchtst` | PatchTST-inspired | INSPIRED_SIMPLIFICATION | 基于 patch 的时序 Transformer |
| `itransformer` | iTransformer-aligned | REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS | 变量 token Transformer |

### Group B — LLM-based

| model_key | display_name | role |
|---|---|---|
| `gpt2_miflu` | MIFlu GPT-2 | 原始已发表 LLM/多模态基线 |
| `qwen_time_llm` | Qwen2.5-1.5B Time-LLM-inspired | patch reprogramming + Prompt-as-Prefix |
| `calf_llm` | CALF-inspired Cross-Modal LLM | 跨模态匹配 + 特征/输出对齐 |
| `timecma_llm` | TimeCMA-inspired LLM | 双分支时序/LLM 编码 + 跨模态对齐 |

候选冻结后**不得**再加入 Chronos、TimesFM、Moirai、LSTM、GRU、TimesNet、TimeMixer、
ModernTCN 等架构。若某个主模型不可行，**不得静默替换**——须报告确切阻塞并申请预注册修订。

## 3. 廉价参考基线（2 个）

```text
last_value_naive
seasonal_naive
```

- 不计入 4 个 Non-LLM 架构；不做大规模超参搜索；
- 使用相同 split、日期、horizon、聚合与指标；
- 提供下界健全性检查；
- **必须与 4-vs-4 主比较分开报告**。

## 4. 定向 LLM 负对照

次级、仅 validation 的对照，用于检验增益来源（语言知识 / 文本语义 / 仅参数与对齐机制）：

```text
zero_text
shuffled_text
llm_removed_or_alignment_only
```

预注册的有界设计：

```text
MIFlu GPT-2:                 zero_text, shuffled_text
Screening 后最佳 LLM 模型:    zero_text, shuffled_text, llm_removed_or_alignment_only

horizons = {24, 60}
seeds    = {42, 43, 44}
```

对照不是新的主候选；不得在观察到结果后扩展对照集。

## 5. 原始 GPT-2/MIFlu 数据与切分协议

v3 完全复用已验证的 GPT-2/MIFlu National-Illness 工作流，不引入外部数据、新 holdout、
`ili`/`wili` 目标、reduced-feature redesign 或 rolling-origin redesign。权威复用证据见
`results/v3/preregistration/original_data_reuse_manifest.json` 和
`results/v3/preregistration/split_equivalence_audit.json`。

```text
canonical data = data/raw/national_illness_raw.csv
target        = ILITOTAL
channels      = 7
rows          = 1025
train_end     = 717
val_end       = 819
test_end      = 1025
split         = target-start-week rule from the verified GPT-2/MIFlu manifest
scaler        = same StandardScaler metadata, train rows only
prompt stats  = train rows only
T             = 104
horizons      = {24,36,48,60}
formal seeds  = {42,43,44,45,46,47,48,49,50,51}
```

所有八个主模型、两个 naive baseline 与 bounded controls 使用同一文件、同一 target、
同一 split、同一 scaler、同一 prompt-statistics 规则、同一窗口构造和同一 evaluation pipeline。
已完成的外部数据/new holdout 调查保留为 `SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY`，
不属于 active v3 workflow，也不形成实现 blocker。

## 7. 协议冻结项

```text
目标与输入            : ILITOTAL 目标，7 通道输入
look-back T           : 104
horizons L            : {24, 36, 48, 60}（每个 horizon 独立训练与评分，不跨 lead time 合并）
seed 集               : Screening {42,43,44}；Full Validation {42..51}
scaler                : 仅 train 拟合
prompt statistics     : 仅 train 计算
optimizer / 搜索预算   : 各候选预注册且公开报告
early stopping        : 仅监控 validation MSE，patience = 7
checkpoint            : 保存并恢复最低 validation MSE 的 checkpoint
主数值口径             : z 空间 MSE 与 MAE（PRIMARY）
补充数值口径           : 物理量纲 MSE 与 MAE
峰值指标               : PTE、PIE
唯一文献峰值判据        : PTE <= 1 周 AND PIE <= 25%
多重比较校正           : Holm
execution Gate        : Phase 1 仅在本计划获得授权后开启；v2 Test 保持历史证据，不作 v3 输入
```

本计划不包含任何未预注册的搜索、预算自适应或自动架构扩展阶段；候选集、预算和
选择规则在观察结果前固定。

## 8. Fixed-step 契约（steps 0–3）

### 8.1 step → 周提前量映射（显式，不假定）

仓库中 `innovation.metrics.aggregate_fixed_step` 的文档串明确规定：

> 保留 `step == step` 的行后，每个点具有 **(step + 1) 周的固定提前量**。

因此本计划显式冻结：

| step | 固定提前量 | lead_time_label | 角色 |
|---|---|---|---|
| 0 | 1 周 | `1-week ahead` | **primary endpoint** |
| 1 | 2 周 | `2-week ahead` | mandatory supplementary |
| 2 | 3 周 | `3-week ahead` | mandatory supplementary |
| 3 | 4 周 | `4-week ahead` | mandatory supplementary |

### 8.2 规则

- 该 fixed-step 规则对 **8 个主架构 + last-value naive + seasonal naive + 每个预注册负对照**
  完全一致。
- **严禁跨 step 平均预测或指标**；不得把多个 step 合并成一条预测。
- 每个 step 是独立预测任务，必须保留各自的目标日期、预测、指标行与报告身份。
- 冠军规则**只使用 step 0**（预注册主终点）；steps 1–3 用于评估 lead-time 稳健性。
  **不得**通过挑选最好看的 step 来选冠军。
- 加入 steps 1–3 **不得**放大主假设族或允许事后挑选。

### 8.3 每个 step 产物必须记录

```text
model_key, horizon, seed, split, step, lead_time_label,
date_start, date_end, row_count, prediction_file,
checkpoint_sha256, source_snapshot_sha256
```

路径约定：

```text
predictions/validation_step{0,1,2,3}_predictions.csv
metrics/validation_step{0,1,2,3}_metrics.json
```

（本 v3 纠正不定义新的 holdout 路径；仅保留原始 GPT-2/MIFlu validation/test 路径。）

每个 step 指标文件必须包含：z 空间 MSE/MAE（主）、物理量纲 MSE/MAE（补充）、PTE、PIE、
唯一文献判据、日期范围与行数、聚合策略名、checkpoint 与来源溯源。

### 8.4 日期窗口与可比性

- 同 horizon 同 step 的跨模型比较**必须**使用相同目标日期与相同行数；
  若覆盖不同，则取共同交集并披露减少量。
- 不得因为评估窗口不同而把更长 horizon 或更晚 step 的更低误差解释为"更好"。

## 9. 统一出图契约

权威来源与其内容哈希（出图前必须比对，哈希不符即视为契约被破坏）：

```text
docs/FIGURE_STYLE_GUIDE.md
  SHA-256 = 4e2ee958bb1561e41155e735c8b2bdd6a2c6ee2270e66e06568077c6de070741

results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png   （版式与视觉语言参考）
  SHA-256 = 06d8622152ef2bf00017278fb6925283445e8c604d7973a6d35a4798b1399d70

scripts/v3/figure_style.py                                （唯一共享绘图模块）
```
- 全 v3 使用**同一套**绘图系统，统一画布、DPI、字体层级、线宽、配色、
  模型视觉身份、step 与 horizon 编码、panel 标签、日期格式、命名与 caption 结构。
- 唯一共享模块：`scripts/v3/figure_style.py`；各出图脚本必须调用它。
- 同一模型在任何图中颜色**永不改变**；不依赖颜色单通道（颜色 + 线型 + 标记）。
- 所有图**仅从已保存的预测/指标/资源/checkpoint 清单生成**，不得为画图重新推理。
- 每张图必须有 `.provenance.json` sidecar，并进入自动 QA Gate。

## 10. 各阶段与作业量

```text
Phase 0  预注册与可行性       （无下载、无 Slurm）
Phase 1  Pilot               8 主模型 x L=24 x seed=42 = 8 次 A100 pilot，预算上界 7 GPU-h
Phase 2  Screening           8 x {24,60} x {42,43,44} = 48 次正式 validation，预算上界 42 GPU-h
         + 2 个 naive 基线的匹配单元（不计入主架构）
Phase 3  Full Validation     首选 8 x 4 horizons x 10 seeds = 320 次，预算上界 280 GPU-h
                             预算不足时的预注册降级：4 finalists x 4 x 10 = 160 次，预算上界 140 GPU-h
Phase 4  Negative controls   预注册有界子集
Phase 5  Validation 选择 → best_non_llm / best_llm / best_overall
Phase 6  停止在 Phase 1 授权前；不创建新 holdout 或 final-Test receipt
```

预算上界按每次 Non-LLM 0.25 GPU-h、每次 LLM 1.5 GPU-h、每次 naive 0.02 GPU-h
估算，并额外加入 30% 的启动、失败重试和 `stingy` 队列等待余量。固定 steps 0–3
使预测与指标产物按每次 run 约 48 MB 计；preferred full validation 的两份 durable
副本、Qwen 权重和环境缓存合计约 34 GB。`stingy` 每用户至多 1 个运行作业、1 个
pending 作业，因此 full-320 的实际串行墙钟约 15.2 天，fallback-160 约 7.6 天；
这些是资源规划上界，不是已执行结果。

## 11. 选择规则（对所有候选一致）

1. 每次 run 只接受最低 validation MSE 的 checkpoint；
2. 同一 horizon 内向冻结参考归一化；
3. 四个 horizon 等权平均；
4. 预注册的文献峰值下限；
5. primary score 差异 < 1% 时，依次用 validation MAE、峰值表现、可训练参数、训练时间决胜；
6. 除非有统计支持，否则只称 **observed best**。

## 12. 报告与审计

- 报告总参数、可训练参数、权重体积、训练墙钟、GPU-hours、峰值显存、推理延迟、
  validation 评估次数、失败与重试作业数。
- 两种互补比较：
  **A. 相同 per-run 协议下的精度**；
  **B. 相同累计 GPU-hour 与 validation 评估预算下的最佳 validation 结果**。
- 不计算跨时间步的累计曲线分数；仅报告预注册的逐步指标。
- 不得给 LLM 模型无限调参而 Non-LLM 只用默认。

## 13. HPC 红线（永久）

登录节点（`hpclogin01` / `hpclogin02` / `burgundy.hpc.cityu.edu.hk`）**禁止**执行：
训练、推理、评估、批量预测、模型构建、为计算加载 checkpoint、Torch/CUDA 计算、
大数据处理、`nohup python ... &`、后台模型进程、`screen`/`tmux` 模型计算、
直接跑模型代码的循环。

登录节点仅允许：`sbatch` 提交；`squeue`/`sacct`/轻量轮询；`scp`/`sftp`/`ls`/`cat` 小文件操作；
小 JSON/CSV 检视与哈希；只轮询并提交的队列安全控制器（不得 import Torch、构建模型、
加载 checkpoint 或读取大数据）。

所有计算作业遵循 `HPC_GUIDE.md`：`partition=stingy`、`gres=gpu:a100:1`、
`time <= 04:00:00`。禁止裸 `--gres=gpu:1`，禁止夸大资源申请。

## 14. 修订政策

任何对数据、切分、scaler、prompt statistics、架构身份、指标、阈值、早停、
候选集或预算的修改，必须**停止并申请预注册修订**，不得在观察到结果后执行。

## Protocol correction closure

- Approved canonical figure template: `results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png`; the original `scripts/q1_step_sweep.py` format remains authoritative.
- CDC/Delphi/NHSN, external-data acquisition, new-holdout, `ili`/`wili`, reduced-feature, and rolling-origin proposals are superseded history, not active v3 requirements.
- MIFlu GPT-2 remains `LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE`; its verified workflow is the protocol baseline.
- Qwen access and TimeCMA license review remain asset/code authorization blockers, not data-holdout blockers.
- Fixed steps remain 0, 1, 2, 3 with step 0 primary and steps 1-3 mandatory supplementary; steps are never averaged.
