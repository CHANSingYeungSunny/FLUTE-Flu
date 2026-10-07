# REPORT_ZH — 官方仓库复现与 LLM vs 非 LLM 公平比较（2026-10-06）

目录：`hpc_results/official_repo_reproduction_20261006/`
本轮性质：**只读核查 + 本地 CPU 重算 + 新建文件**。未删除/覆盖任何旧 checkpoint、预测、报告、CSV。**未提交任何 HPC 作业**（原因见 §0）。

---

## §0 执行边界

**HPC 已连通并全程实测**（`hpclogin02`，2026-10-05T20:20Z 首次连通；登录需 `-o PreferredAuthentications=publickey`，因为 `~/.ssh/config` 把 publickey 排除在 `PreferredAuthentications` 之外）。

**本轮实际提交并完成的作业（全部 COMPLETED，队列最终为空）**：

| 作业 | 内容 | 资源 | 时长 | GPU-h |
|---|---|---|---:|---:|
| 606357 | text-path probe CPU 半边 | CPU only | 00:01:08 | 0 |
| 606358 | text-path probe **A100** 半边 | a100:1 | 00:00:30 | 0.00833 |
| 606360 | CPU/GPU 探针对照 | CPU only | 00:00:00 | 0 |
| 606361_0 | A1 尝试（失败，`--target_modules` 类型陷阱） | a100:1 | 00:00:07 | 0.00194 |
| 606362 | PEFT/LoRA 诊断（7 种写法实测） | CPU only | 00:00:05 | 0 |
| **606365_0** | **A1 L=24** | a100:1 | 00:17:34 | 0.29278 |
| **606378_1** | **A1 L=36** | a100:1 | 00:16:54 | 0.28167 |
| **606385_2** | **A1 L=48** | a100:1 | 00:16:18 | 0.27167 |
| **606412_3** | **A1 L=60** | a100:1 | 00:15:42 | 0.26167 |

**GPU 预算**：stage6 已用 1.1256 + 本轮 1.11806 = **2.24366 / 2.3**，剩余 **0.05634**（≈3.4 分钟 A100）→ 本轮在此停止。

**本轮遇到的三个真实阻塞（均已定位并记录于 `DEVIATION_LEDGER.md` D-10~D-12）**：
1. 作者 `--target_modules` 是 `type=str` 但默认值是 list → 命令行覆盖后 LoRA 直接崩溃；
2. **scratch 用户配额超额**（413 GB / 300 GB，`grace=expired`）→ 所有写入改到 `/gpfs1/home/`；
3. `partition-stingy` 的 `MaxSubmit=1, MaxJobsPU=1` → 每个 horizon 逐个提交并等待。

---

## §A 执行摘要

| 问题 | 答案 |
|---|---|
| **论文是否成功复现？** | ❌ **未成功。** 论文 Table V–IX 与图 3–7 的定量结果**均未复现**。本轮已在作者代码上真实跑通 A1 四个 horizon，但**口径不同，不构成复现**。 |
| **最佳 overall 模型** | Track A（作者 966 行）：**`notext` 1.9222**（控制组）；八个核心模型中 **`miflu` 2.0415** |
| **最佳 LLM 模型** | Track A：**`miflu` 2.0415** ／ Track B：**`gpt2_miflu` 0.7709**（全表第 1） |
| **最佳 non-LLM 模型** | Track A & B 均为 **`nlinear`**（2.0496 ／ 1.0698） |
| **matched full vs no-text** | `notext − miflu` = **−0.1194**，t = **−1.50**，7/12 格 notext 更优 → **未达显著**，**不能宣称「去掉文本更好」** |
| **文本通路结论** | ✅ **已解决（CPU+A100 双边）**：发布实现文本 **严格无影响**（max\|Δpred\|=0，梯度=0）；**A2 实现则 `text_active`**（max\|Δpred\|=59.7）——基准的 full-vs-no-text 对照确实有效 |

**三个必须同时说出口的事实**：

1. **组均值显示 LLM 更差，但组内最优在两轨相反**：A 轨组内第 1 是 `notext`（非 LLM 对照），B 轨组内第 1 是 `gpt2_miflu`（LLM）。**只报其一是选择性报告。**
2. **MIFlu 与 NLinear 不可分**（t = −0.11），且**胜负随预测长度翻转**（L=24 三格全负，L=36/48/60 多数为正）。
3. **Track A 与 Track B 的绝对数字禁止对比**（数据、种子数、Test 窗内容全不同）。

---

## §B 当前仓库身份

| 项 | 值 | 判定 |
|---|---|---|
| 项目仓库 remote | `CHANSingYeungSunny/FLUTE-Flu.git` | — |
| 项目 commit | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51`（**仅 1 个 commit**） | ⚠️ 无 git history 可追溯实验时序 |
| 分支 | `recovery-stage4` | — |
| 作者仓库 remote | `Jmoon3108/MIFlu.git` | ✅ **确为作者官方仓库** |
| 作者 commit | `6ed210150b8819313947cf607eb1821c87b1bee3`（2025-03-21） | ✅ 与恢复计划记录**完全一致** |
| 作者树是否被本地改动 | 兼容层放独立 `sys.path`，**作者源码逐字节未改** | ✅ |
| 数据 SHA-256（A 轨实际使用） | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | ✅ 与前序记录一致 |
| 数据 SHA-256（作者默认加载） | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | — |

**可复现性缺口**：`scripts/miflu_model.py` 等有**未提交修改**，且仓库只有一个 commit → **无法通过 git 复原训练时的代码版本**。已声明。

---

## §C 论文目标 vs 实际结果

### 论文目标（Table V）

| L | MSE | MAE |
|---:|---:|---:|
| 24 | 1.542 | 0.726 |
| 36 | 1.422 | 0.779 |
| 48 | 1.414 | 0.757 |
| 60 | 1.364 | 0.719 |
| 均值 | 1.4355 | 0.74525 |

> **重要限定**：论文 §V-C 明写「national 与 regional 的对比基线结果取自**[9]**与**[14]**」。即 Table V 的**基线列是引用值，不是重跑**。MIFlu 自身列是否含引用成分，论文未说明。

### 我方（Track A，作者 966 行，z 空间，**3 seeds**）

| L | 我方 MSE | 论文 MSE | 绝对差 | 比值 |
|---:|---:|---:|---:|---:|
| 24 | 2.4439 | 1.542 | +0.902 | 1.58× |
| 36 | 1.9360 | 1.422 | +0.514 | 1.36× |
| 48 | 1.7677 | 1.414 | +0.354 | 1.25× |
| 60 | 2.0184 | 1.364 | +0.654 | 1.48× |
| 均值 | **2.0415** | 1.4355 | +0.606 | **1.42×** |

### ⚠️ 这个表**不是**复现证据

| 不可比的理由 | 说明 |
|---|---|
| 超参未披露 | 论文只说 "set empirically"，**无 epochs / lr 数值**（见 §D） |
| 种子数 | 我方 **3**，论文 **10 repetitions** |
| 缩放口径 | 论文自身的 scaler 约定未披露 |
| 文本通路 | 论文的 token 顺序在论文内部**自相矛盾**（L205/L219/L225），我方用声明式修正 |

**必须写**：「我方 2.0415 与论文 1.4355 口径不同，**不构成复现**。」
**禁止写**：「我们复现了论文的 1.4355」或任何暗示数值接近即成功的表述。

### 3 seeds vs 10 seeds 状态（分开陈述）

| 轨 | seeds | 状态 |
|---|---|---|
| Track A（作者 966） | **3**（42/43/44） | ✅ 完成，仅 12 格/模型 |
| Track A 扩展到 10 | 10 | ❌ **未执行**；缺 88 个 fit（A2 配置 0.0146 h/fit ≈ 1.29 GPU-h） |
| **A1 轨（作者代码）** | **1/10** | ⚠️ **4/4 horizons 已跑**（2026-10-06，作业 606365/606378/606385/606412），每档 1 次重复；配齐 10 次需 ≈11.27 GPU-h |
| Track B（July 1025） | **10**（42–51） | ✅ 完成（历史轨道） |

---

## §D A0 / A1 / A2 的区别（禁止混淆）

| ### A1 已实际运行（2026-10-06，作者自己的入口点）

**配置**：作者 `main_ILI_lora.py`，`multimodal=1` `PEFT=1` `lora_r=4`，20 epochs，lr 5e-4，batch 16，`itr=1`。

| L | `mse_mean` | 最优 epoch MSE | 最优 epoch MAE | 墙钟 | 作业 |
|---:|---:|---:|---:|---:|---|
| 24 | 0.6044 | **0.5344** @ep8 | 0.4503 | 17:34 | 606365_0 |
| 36 | 0.6028 | **0.5387** @ep10 | 0.4195 | 16:54 | 606378_1 |
| 48 | 0.6571 | **0.6069** @ep16 | 0.4684 | 16:18 | 606385_2 |
| 60 | 0.6545 | **0.5933** @ep5 | 0.5093 | 15:42 | 606412_3 |

> ⚠️ **这不是 Table V 的复现。** 作者的 Test **只算 feature 0** 且**用 Test MSE 选 checkpoint**；论文要求 **10 次重复**，本轮每档 **1 次**；epochs/lr 论文**未披露**。这些数字与论文 1.542/1.422/1.414/1.364 **口径不同，不可比较**。

| | **A0** 发布代码逐字重放 | **A1** 论文配置重建 | **A2** 修正公平基准 |
|---|---|---|---|
| 代码 | 作者原样 | 作者原样 + 论文设置 | 修正重构 |
| 目的 | 记录发布代码**实际行为** | 论文数值复现主轨 | 公平比较 |
| 超参 | 作者默认（1 ep / 1e-4） | 20 ep / 5e-4（**reconstructed**） | 20 ep / 5e-4 |
| 文本通路 | 原样（惰性） | 原样 | 声明式修正（文本前置） |
| LoRA | **从不应用** | 应用 | 应用 |
| 冻结 | **no-op（100% 可训练）** | 依变体 | 生效 |
| checkpoint 选择 | **用 Test 选**（泄漏） | 同 A0 | validation-only |
| Test 变量 | **仅 feature 0** | 同 A0 | 全部 7 个 |
| 完成度 | ⚠️ **仅最小诊断**（1 epoch, itr=1, L=24） | ⚠️ **4/4 horizons 已跑，每档 1/10 次重复**（2026-10-06） | ✅ 108 fits + 116 评分 |

**硬性规则**：
- A0 的成品**不得**称为干净 holdout，**不得**称为论文复现成功。
- A2 **不是**「未修改的论文复现」，必须始终带「修正重构」标签。
- 三者**不得合并排名或求平均**。

### 已实测的作者代码缺陷（一手证据）

| 缺陷 | 证据 |
|---|---|
| Test 只覆盖 `feat_id=[0]` | 实测 `test=[0]`；`drop_last` 后 170→160 |
| 每 epoch 读 Test 并用 Test MSE 选 checkpoint | 源码 L211/225/264；本轮再次核对确认 |
| early stopping 调用被注释 | L235-236 |
| `PEFT=0` 默认 → **LoRA 从未应用** | 实测 `llmmodel` 为裸 `GPT2Model` |
| `freeze` 是 no-op | 实测 **82,705,944 / 82,705,944 = 100% 可训练** |
| 文本通路惰性 | 见 §E |

---

## §E 文本通路结论（P0 已解决）

### 判定：`text_inert` —— 发布实现的文本 CONTENT 严格无影响

| 判据 | 实测 |
|---|---|
| **等长不同内容文本替换** `max\|Δpred\|` | **0.000000e+00**（严格零） |
| 文本 embedding 梯度范数 | **0.0**（严格零） |
| 时序 embedding 梯度范数（对照） | **0.032782**（非零 → 证明测量链路正常） |
| 预测头实际读取的位置 | **42** = `patch_num`；文本位于 [42, 358]，**不在读取范围内** |
| dropout 状态 | 全部 `training=False` |
| **阳性对照**（文本前置的声明式修复） | `max\|Δpred\|` = **3.55e-05** → **探针确实能检测文本影响** |

### 之前的「CPU/GPU 矛盾」是什么

A0 GPU 证据比较的是 `--multimodal 0` vs `1`，**这同时改变了序列长度（42 → 359）**，因此改变了训练期的 dropout 随机数消耗 → 换了整条优化轨迹。**这不是文本效应。**

**本轮新增的实证**（固定权重、eval、关 dropout）：

| 对比 | 序列长度 | `max\|Δpred\|` | 解读 |
|---|---|---|---|
| `multimodal=0` vs `1` | 42 vs 359 | **2.38e-07** | ≈ float32 舍入 → **数学等价** |
| 等长不同内容文本 | 359 vs 359 | **0.000e+00** | 严格零 |

这与静态因果掩码分析完全一致：被保留的 42 个 patch 位置全在文本**之前**，因果注意力使其**无法**看到文本。

**结论**：**Stage-2 的 CPU 判定是对的，A0 的 GPU 判定是误读。** 该项应从「未决矛盾」结案。
**GPU 半边已在 HPC A100 上完成**（作业 606358，0.00833 GPU-h），对照作业 **606360 输出 `CPU/GPU verdicts AGREE`**。三方（本地 CPU / HPC CPU / HPC A100）判决一致，且 **HPC CPU 与 A100 的参数 SHA-256 完全相同**（`d7ad42ee…`）→ 跨设备逐位可复现。

### E.2 补充：**A2 实现是 `text_active`（必须与作者代码分开陈述）**

上面的判决只针对**作者发布代码**。但**基准比较用的是 A2**，所以单独验证了 A2（`probe_a2_text_path.py`，真实训练 checkpoint）：

| 实现 | 文本通路结构 | 判决 | 等长替换 `max\|Δpred\|` | 文本梯度 |
|---|---|---|---:|---:|
| **作者发布代码** `GPT4TS_lora.py` | 文本在 patch **之后**（因果注意力不可达） | **`text_inert`** | **0.0** | **0.0** |
| **A2 修正实现** `miflu_model.py` | 文本在 patch **之前**，读**尾部** patch（L376/L407） | **`text_active`** | **59.6875** | **7.13e+08** |

（A2 探针的 L=24 与 L=60 两个 prompt 长度完全相同，1552 字符 → `(1,369,768)`，因此是天然的**等长不同内容**对照；`missing=12` 的键是 GPT-2 因果掩码 **buffer**，确定性常量、不可训练，所以加载的确实是训练后权重。）

**结论**：基准中 `notext` vs `miflu` 的对照**是真正的文本内容对照**。两件事不矛盾，但**不得互相挪用**——不得用 A2 的 `text_active` 替作者代码辩护，也不得用作者的 `text_inert` 否定 A2 的机制实验。

---

## §F LLM vs 非 LLM 公平比较

### F.1 Track A（作者 966 行，z 空间，3 seeds × 4 horizons）

| 排名 | 模型 | 族 | 身份 | average_MSE_4L |
|---:|---|---|---|---:|
| — | **notext** | **控制（保留 LLM）** | reconstructed ablation | **1.922158** |
| 1 | miflu | LLM | 修正重构 | 2.041519 |
| 2 | nlinear | non-LLM | **canonical** | 2.049550 |
| — | seasonal_naive | 基线 | deterministic | 2.268799 |
| 3 | dlinear | non-LLM | 自研重实现 | 2.347832 |
| 4 | timecma_llm | LLM | TimeCMA-**INSPIRED** | 2.670009 |
| 5 | patchtst | non-LLM | PatchTST-**INSPIRED** | 3.920470 |
| 6 | itransformer | non-LLM | 自研重实现 | 3.984699 |
| 7 | qwen_time_llm | LLM | Time-LLM-**INSPIRED** | 5.219555 |
| 8 | calf_llm | LLM | CALF-**INSPIRED** | 5.515300 |
| — | last_value_naive | 基线 | deterministic | 7.165831 |

**组均值（补充信息，非主结论）**

| 口径 | LLM 组 | non-LLM 组 | 差 |
|---|---:|---:|---:|
| **4 vs 4** | **3.861596** | **3.075638** | +0.785958 |
| 3 vs 5 | 4.468288（n=3） | 2.868814（n=5） | +1.599474 |

> `notext` **不计入任一组**：它仍保留 GPT-2 预测骨干与 LoRA。

### F.2 主结论（基于具体模型、预先声明的比较）

| 比较 | 均值差 | t | 胜场 | 判定 |
|---|---:|---:|---|---|
| **miflu − nlinear** | −0.0080 | −0.11 | **7/12** | **不可分** |
| **notext − miflu**（机制） | −0.1194 | −1.50 | 7/12 | **不显著** → 不能宣称去掉文本更好 |
| notext − nlinear | −0.1274 | −2.28 | 11/12 | notext 更优 |
| dlinear − nlinear | +0.2983 | +8.51 | 0/12 | 显著更差 |
| timecma_llm − nlinear | +0.6205 | +10.94 | 0/12 | 显著更差 |
| patchtst − nlinear | +1.8709 | +39.16 | 0/12 | 显著更差 |
| itransformer − nlinear | +1.9351 | +31.47 | 0/12 | 显著更差 |
| qwen_time_llm − nlinear | +3.1700 | +21.66 | 0/12 | 显著更差 |
| calf_llm − nlinear | +3.4658 | +46.63 | 0/12 | 显著更差 |

> ⚠️ 胜场数已修正。原 `paired_stats.txt` 的 `n_win` **方向取反**（`miflu−nlinear` 原写 5/12，实为 7/12）。详见 `SCORING_CORRECTION_NOTE.md`。**均值差与 t 值不受影响。**

### F.3 逐预测长度优胜者（符号翻转）

| L | 最佳 overall | 最佳 LLM | 最佳 non-LLM | notext |
|---:|---|---|---|---:|
| 24 | **notext** 1.9796 | miflu 2.4439 | **nlinear** 2.1008 | 1.9796 |
| 36 | **notext** 1.8268 | **miflu** 1.9360 | nlinear 2.0277 | 1.8268 |
| 48 | **miflu** 1.7677 | **miflu** 1.7677 | nlinear 2.0033 | 1.7901 |
| 60 | **miflu** 2.0184 | **miflu** 2.0184 | nlinear 2.0664 | 2.0921 |

**L=24 时 NLinear 明显优于 MIFlu（2.1008 vs 2.4439），L=36/48/60 时 MIFlu 领先。单一 L 的胜负不能外推。**

### F.4 稳定性

| 模型 | L24 | L36 | L48 | L60 | 极差 |
|---|---:|---:|---:|---:|---:|
| notext | 1.9796 | 1.8268 | 1.7901 | 2.0921 | 0.302 |
| **miflu** | 2.4439 | 1.9360 | 1.7677 | 2.0184 | **0.676** |
| **nlinear** | 2.1008 | 2.0277 | 2.0033 | 2.0664 | **0.098** |
| dlinear | 2.2850 | 2.2780 | 2.3558 | 2.4726 | 0.195 |

**MIFlu 的跨 L 波动是 NLinear 的 6.9 倍**（12 格样本 SD：0.2838 vs 0.0736）。**NLinear 稳定性显著更高。**

### F.5 成本

| 项 | 值 |
|---|---|
| 测量到的单次拟合成本 | **0.0125 GPU-h**（20 epochs；1.05 GPU-h / 72 fits） |
| Stage 6 已用 | 1.0500 GPU-h（+0.0756 失败） |
| Stage 6 授权上限 | 2.3 GPU-h，**剩余 1.1744** |
| A1 8 fits（array） | ≈ 0.10 GPU-h |
| A 轨扩展至 10 seeds | ≈ 1.84 GPU-h（**超出剩余额度**） |
| 本轮（10-06）HPC 消耗 | **0.0**（未提交任何作业） |

### F.6 Track B（July-2026 1025 行，10 seeds）— 仅历史轨道

| 排名 | 模型 | 族 | average_MSE_4L |
|---:|---|---|---:|
| 1 | **gpt2_miflu** | LLM | **0.770872** |
| 2 | nlinear | non-LLM | 1.069767 |
| 3 | patchtst | non-LLM | 1.075951 |
| 4 | dlinear | non-LLM | 1.170933 |
| 5 | timecma_llm | LLM | 1.181449 |
| 6 | itransformer | non-LLM | 1.252982 |
| 7 | qwen_time_llm | LLM | 1.253096 |
| 8 | calf_llm | LLM | 1.764871 |

组均值 4v4：LLM **1.242572** vs non-LLM **1.142408**（+0.100164）。

**张力**：组均值说 LLM 更差，**组内第 1 名却是 LLM**。两轨方向相反（A 轨组内第 1 是 notext）。

---

## §G 与旧结果比较（三条轨道必须分开）

| | **Track A**（本次主轨） | **Track B**（历史） | **旧 8-17 / 514859**（更早） |
|---|---|---|---|
| 数据 | 作者 966 行 | July-2026 **1025 行** | 966 / 1025 混用 |
| 划分 | 676/97/193 | 不同 | 676/**96/194** |
| seeds | 3 | 10 | 10 reps |
| 选模 | validation-only | validation | **无验证选模** |
| 通道 | 全 7 变量 | 全 7 变量 | **仅 ILI 单通道** |
| 主值（L=24） | 2.4439 | 0.7324（gpt2_miflu） | 2.593 / 2.238 / 1.379 |

**硬性规则**：
- **绝对 MSE 禁止横向比较。** A 轨 2.0415 与 B 轨 0.7709 相差 2.6 倍**纯属口径差异**（不同数据、不同 scaler 拟合、不同 Test 窗内容）。
- 旧结果只能作为「数据支线地标」，**不得进入任何排名或均值**。
- 旧 Test 已暴露 → 标为 **retrospective**。

---

## §H Limitations（必须随每个结论一起报告）

| 类别 | 内容 |
|---|---|
| **未恢复的超参** | epochs 与 lr **论文完全未披露**。20 ep / 5e-4 是 **reconstructed assumption**，**不是**论文值，**不是**作者实用值（作者默认 1 ep / 1e-4）。 |
| **上游文档错误** | 恢复计划 L161 与 Recovery Prompt L63 把 20/5e-4 标为 "Paper:"，**无出处**。已在本轮纠正。 |
| **实现身份** | 八个模型中仅 **NLinear 是 canonical**。PatchTST 是 **INSPIRED**（非 canonical），CALF/TimeCMA/Qwen 均为 **INSPIRED/adaptation**。换用官方仓库**不会**使它们成为「官方正确实现」。 |
| **`notext` 不是 non-LLM** | 它保留 GPT-2 预测骨干与 LoRA。任何把它计入 non-LLM 组的做法都会污染组均值。 |
| **已暴露的 Test** | 全部 Test 结果均为 **retrospective**。 |
| **剩余 seeds** | Track A 仅 3 seeds，论文要求 10。缺 88 个 fit。 |
| **配额** | Stage 6 剩 **1.1744 GPU-h**；扩展至 10 seeds 需 ≈1.84 GPU-h → **超额**。 |
| **无真正 untouched holdout** | **不存在未看过的区间**；**不得**把旧区间改名冒充 holdout。Track C 无法开展。 |
| **A0 未完整重放** | 只有 1 epoch / itr=1 / L=24 的最小诊断。 |
| **A1 重复次数不足** | 四档各 **1/10** 次重复。配齐 40 fits 需 **11.27 GPU-h**（实测 0.2817/fit），剩余额度仅 **0.056**。 |
| **区域 / few-shot / 表 VI / 表 VII / 表 IX** | **完全未开展**，必须显式声明为「未做」而非从分母中删除。 |
| **git 可追溯性** | 项目仓库仅 1 个 commit，`scripts/miflu_model.py` 有未提交修改 → **训练时代码版本无法复原**。 |
| **scratch 配额超额** | `mmlsquota`：**413 GB / 300 GB**，`grace=expired`。`/gpfs1/scratch` 写入间歇失败；本轮全部输出改到 `/gpfs1/home/`。占用大户 `innovation_deploy_root_v3_*`（52+50+11+11+9.7+9.6×6 GB）**未被本轮删除**，需用户决定。 |
| **group 解释边界** | 4 个/4 个固定实现**不是随机样本**，组均值**不得**解读为对 LLM / non-LLM 家族的统计推断。 |

---

## §I 本轮交付物清单（22 项）

| # | 文件 | 状态 |
|---|---|---|
| 1 | `STATUS_BEFORE_CONTINUATION.md` | ✅ |
| 2 | `REPOSITORY_PROVENANCE.md` | ✅ |
| 3 | `HYPERPARAMETER_PROVENANCE.md` | ✅ |
| 4 | `DEVIATION_LEDGER.md` | ✅ |
| 5 | `TEXT_PATH_RESOLUTION.md` | ✅（CPU 侧定论；GPU 复核 PENDING） |
| 6 | `IMPLEMENTATION_IDENTITY.md` | ✅ |
| 7 | `RUN_MANIFEST.csv` | ✅ 118 行 |
| 8 | `REMAINING_RUN_MATRIX.csv` | ✅ 51 行 |
| 9 | `author_paper_targets.csv` | ✅ |
| 10–11 | `reproduction_results_per_seed.csv` / `_aggregate.csv` | ✅ 116 / 11 行 |
| 12 | `paper_vs_reproduction.csv` | ✅（含 «不构成复现» 说明） |
| 13–16 | `benchmark_results_{per_seed,per_horizon,per_variable,average_4L}.csv` | ✅ |
| 17 | `paired_stats_corrected.csv` / `.md` + `SCORING_CORRECTION_NOTE.md` | ✅（4 项单元测试全过） |
| 18 | `cost_summary.csv` | ✅ |
| 19 | `failures_and_retries.csv` | ✅ |
| 20–21 | `REPORT_ZH.md` / `REPORT_EN.md` | ✅ |
| 22 | `scripts/probe_text_path_deterministic.py`、`scripts/score_predictions_independent.py`、`scripts/paired_stats_corrected.py`、`slurm/*.sbatch`、`slurm/submit_all.sh` | ✅ **已写好，未提交** |

附：`indep_scorer_*.csv/json`、`text_path_probe_cpu_local*.json`、`build_deliverables.py`

---

## §J 下一步最小可执行动作

1. **【需要用户】** 恢复 HPC 网络（VPN / 跳板机）。
2. **【HPC 第一条命令】** `ssh cityu 'squeue -u $USER; sacct -S 2026-09-26 -X'` → 确认无残留作业，**不要重复提交相同 run**。
3. **【HPC】** `bash slurm/submit_all.sh` → 依次提交 CPU probe → GPU probe → 对比；A1 array 默认注释掉，需预算确认。
4. **【本地】** 每有结果落地即 `python scripts/score_predictions_independent.py` 独立评分 + `scripts/paired_stats_corrected.py` 配对统计。
5. **【需导师决定】** ① 是否有真正未触碰的泛化区间 ② 是否授权 A0 完整重放 ③ 是否授权 A 轨扩展至 10 seeds（≈1.84 GPU-h，超额）

**在 HPC 恢复前，不得声称任何训练、评估或复现已完成。**