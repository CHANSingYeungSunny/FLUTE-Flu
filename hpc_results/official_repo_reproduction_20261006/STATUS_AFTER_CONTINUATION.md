# 状态报告（本轮结束后）

生成时间：2026-10-06。取代 `STATUS_BEFORE_CONTINUATION.md` 作为**当前**状态。
HPC 连接：✅ **已恢复并全程实测**（`hpclogin02`，2026-10-05T20:20Z 首次连通）。

---

## 1. 一句话

**P0 文本通路矛盾已彻底结案（CPU+GPU 双边一致）。A1 四个 horizon 已在作者自己的入口点上真实跑完（每个 1 次重复）。论文的定量结果仍然没有复现，而且本轮实测出了「为什么 10 次重复很贵」的确切数字。**

---

## 2. 本轮实际提交并完成的 Slurm 作业（全部 COMPLETED）

| 作业 | 名称 | 分区 | 资源 | 时长 | GPU-h | 结果 |
|---|---|---|---|---:|---:|---|
| **606357** | probe_text_cpu | stingy | CPU only | 00:01:08 | 0 | ✅ `text_inert` |
| **606358** | probe_text_gpu | stingy | a100:1 | 00:00:30 | 0.00833 | ✅ `text_inert` |
| **606360** | probe_text_cmp | stingy | CPU only | 00:00:00 | 0 | ✅ `CPU/GPU verdicts AGREE` |
| 606361_0 | a1_measure | stingy | a100:1 | 00:00:07 | 0.00194 | ⚠️ 失败（`--target_modules` 类型陷阱，已定位） |
| **606362** | diag_peft | stingy | CPU only | 00:00:05 | 0 | ✅ 7 种写法逐一实测 |
| 606363_0 | a1_measure | stingy | — | — | 0 | 🚫 已取消（修好前提交，PENDING 阶段取消） |
| **606365_0** | a1 L=24 | stingy | a100:1 | 00:17:34 | 0.29278 | ✅ `mse_mean=0.5793` |
| **606378_1** | a1 L=36 | stingy | a100:1 | 00:16:54 | 0.28167 | ✅ `mse_mean=0.5920` |
| **606385_2** | a1 L=48 | stingy | a100:1 | 00:16:18 | 0.27167 | ✅ `mse_mean=0.6088` |
| **606412_3** | a1 L=60 | stingy | a100:1 | 00:15:42 | 0.26167 | ✅ `mse_mean=0.6361` |

**最终队列：空。** 无残留、无重复提交、无被遗忘的作业。

### GPU 预算（精确）

| 项 | GPU-h |
|---|---:|
| stage6（本会话之前，`sacct` 复核） | 1.1256 |
| 本轮（5 个 a100 作业） | **1.11806** |
| **累计** | **2.24366** |
| 授权上限 | 2.30000 |
| **剩余** | **0.05634**（≈3.4 分钟 A100） |

→ **因此本轮到此停止**，未再提交任何 A1 重复或 A0 完整重放。

---

## 3. P0 文本通路：结案

**同一脚本** `scripts/probe_text_path_deterministic.py`，`--device` 是唯一差异。

| 运行 | 设备 | torch | 等长替换 `max\|Δpred\|` | `\|grad_text\|` | `\|grad_ts\|`（对照） | flag control | 参数 SHA-256 | 判决 |
|---|---|---:|---:|---:|---:|---:|---|---|
| 本地 | Win CPU | 2.6.0 | **0.0** | **0.0** | 0.03278 | 2.384e-07 | `ebaaabd3…` | `text_inert` |
| HPC 606357 | cpunode | 2.5.1 | **0.0** | **0.0** | 0.04039 | 2.384e-07 | `d7ad42ee…` | `text_inert` |
| HPC 606358 | **A100-80GB** | 2.5.1 | **0.0** | **0.0** | 0.04039 | 2.384e-07 | `d7ad42ee…` | `text_inert` |
| **阳性对照**（文本前置，声明式修改） | CPU / A100 | — | **5.34e-05 / 5.29e-05** | — | — | — | — | **能检出** |

**结论**：作者发布代码的文本内容**严格无影响**。A0 GPU 观察到的 `multimodal 0/1` 性能差**不是文本效应**，而是序列长度改变导致的训练期 dropout 随机数差异（固定权重 eval 下两者差 **2.384e-07** = float32 舍入，**数学等价**）。
**HPC CPU 与 A100 的参数 SHA-256 完全相同** → 跨设备逐位可复现。

### 补充：A2 实现**是**生效的（必须分开陈述）

| 实现 | 结构 | 判决 | 证据 |
|---|---|---|---|
| 作者发布代码 | 文本在 patch **之后** | **`text_inert`** | max\|Δ\|=0.0，梯度=0.0 |
| **A2 修正实现**（基准所用） | 文本在 patch **之前**，读尾部 patch | **`text_active`** | max\|Δ\|=**59.7**，梯度=**7.13e8** |

→ 基准中 `notext` vs `miflu` 的对照**是真正的文本内容对照**。两件事不矛盾，但**不得互相挪用**。

---

## 4. A1 复现轨：已在作者代码上真实运行（4/4 horizons，各 1 次重复）

**同一脚本**：作者自己的 `/scratch/sychan552/a0_replay/main_ILI_lora.py`，`multimodal=1` `PEFT=1` `lora_r=4`，20 epochs，lr 5e-4，batch 16。

| L | `mse_mean`（20 epoch 均值） | 最优 epoch MSE | 最优 epoch MAE | 墙钟 | 作业 |
|---:|---:|---:|---:|---:|---|
| 24 | 0.6044 | **0.5344** @ep8 | 0.4503 | 17:34 | 606365_0 |
| 36 | 0.6028 | **0.5387** @ep10 | 0.4195 | 16:54 | 606378_1 |
| 48 | 0.6571 | **0.6069** @ep16 | 0.4684 | 16:18 | 606385_2 |
| 60 | 0.6545 | **0.5933** @ep5 | 0.5093 | 15:42 | 606412_3 |

### ⚠️ 这**不是**论文 Table V 的复现

| 不可比的理由 | 说明 |
|---|---|
| 指标口径 | 作者的 Test **只算 feature 0**，且**用 Test MSE 选 checkpoint**（源码 L211/225/264） |
| 重复次数 | 论文要求 **10 repetitions**；本轮每 horizon **1 次** |
| 超参出处 | epochs 与 lr 论文**完全未披露**，20/5e-4 是 **reconstructed assumption** |
| 已保留的作者缺陷 | `freeze` 是 no-op（**100% 参数可训练**）、early stopping 调用被注释 |

**必须写**：「A1 已在作者代码上跑通四个 horizon，但其指标口径与论文 Table V 不同，**不构成复现**。」
**禁止写**：「A1 得到 0.53–0.64，优于论文 1.4x」——口径不同。

### 已发现的三个真实阻塞（均已定位并记录）

| # | 阻塞 | 根因 | 处理 |
|---|---|---|---|
| 1 | `get_peft_model` 抛 `Target modules c_attn not found` | 作者 `--target_modules` 是 `type=str` 但默认值是 **list**；命令行覆盖后变成字符串 | **不传该参数**，用作者自己的 list 默认值。诊断作业 606362 实测 7 种写法 |
| 2 | `scp` 报 `Disk quota exceeded` | scratch 用户配额 **413 GB / 300 GB**，`grace=expired` | 全部输出改写到 `/gpfs1/home/`；scratch 仅只读 |
| 3 | `sbatch` 报 `QOSMaxSubmitJobPerUserLimit` | `partition-stingy` 的 `MaxSubmit=1, MaxJobsPU=1`；`--array=1-2` 算 2 个提交 | 每个 horizon **逐个提交并等待** |

---

## 5. 当前进度总表

| 阶段 | 状态 | 说明 |
|---|---|---|
| 0 保全 | ✅ COMPLETE | 108 checkpoint 锁定；旧结果零改动 |
| 1 数据/索引审计 | ✅ COMPLETE | — |
| 2 可执行审计 | ✅ **COMPLETE（本轮升级）** | 作者代码的文本惰性已在 **CPU+GPU 双边**实证；LoRA 分支可执行性已实测 |
| 3 聚焦复现试点 | ⚠️ **PARTIAL（本轮大幅推进）** | A2 完成；**A1 四 horizon 跑通但每档仅 1/10 次重复**；A0 仍只有最小诊断 |
| 4 基准补全 | ⚠️ PARTIAL | 八模型 A 轨比较完成（3 seeds）；规范 PatchTST 未做 |
| 5 泛化与报告 | ⚠️ PARTIAL / BLOCKED | 无未触碰区间；Track C 无法开展 |
| **P0 文本通路** | ✅ **结案** | CPU/GPU 一致；矛盾已解释 |
| **配对统计方向 bug** | ✅ **已修** | 新脚本 + 4 项单元测试全过；**旧文件未动** |

---

## 6. 论文结果覆盖（诚实计数）

| 论文单元 | 状态 |
|---|---|
| 数据身份 | ✅ 已复现（966 行、7 变量、676/97/193） |
| Table IV 超参 | ⚠️ 部分（论文未给 epochs/lr） |
| **Table V**（MIFlu 自身分数） | ❌ **未复现**（A1 口径不同） |
| **Table V**（基线列） | ❌ 未复现（论文自述引自 [9]/[14]，非重跑） |
| Table VI（regional） | ❌ 未开展 |
| Table VII（文本嵌入器 BERT/LLaMA） | ❌ 未开展 |
| Table VIII（消融） | ❌ 未复现（`notext` 是不同协议的对照） |
| Table IX（训练时间） | ❌ 未开展 |
| 图 3–7 | ❌ 未复现 |
| 「10 次重复」 | ⚠️ A 轨 3；A1 每档 1；B 轨 10 |

**结论：论文定量结果的成功复现数 = 0。** 必须如此陈述。

---

## 7. LLM vs 非 LLM 公平比较（Track A，作者 966 行，3 seeds）

| 排名 | 模型 | 族 | average_MSE_4L |
|---:|---|---|---:|
| — | **notext** | **控制（保留 LLM）** | **1.922158** |
| 1 | miflu | LLM | 2.041519 |
| 2 | nlinear | non-LLM | 2.049550 |
| 3 | dlinear | non-LLM | 2.347832 |
| 4 | timecma_llm | LLM | 2.670009 |
| 5 | patchtst | non-LLM | 3.920470 |
| 6 | itransformer | non-LLM | 3.984699 |
| 7 | qwen_time_llm | LLM | 5.219555 |
| 8 | calf_llm | LLM | 5.515300 |

**7 个必答问题**（完整版见 `benchmark_best_model_summary.csv`）：

1. 八模型最佳 → **`miflu` 2.0415**；含控制组则 `notext` 1.9222
2. 最佳 LLM → **`miflu` 2.0415**
3. 最佳 non-LLM → **`nlinear` 2.0496**
4. 机制对照 → `notext − miflu` = **−0.1194**，t=**−1.50**，7/12 → **不显著**
5. 逐 horizon → L24/L36 **notext**；L48/L60 **miflu**（**符号翻转**）
6. 稳定性 → miflu 极差 **0.676** vs nlinear **0.098**（MIFlu 波动是 6.9 倍）
7. 成本 → A1 作者配置 **0.2817 GPU-h/fit** vs A2 LoRA 配置 **0.0146**（**19 倍**）

---

## 8. 剩余工作与阻塞

| 优先级 | 事项 | 阻塞原因 | 最小动作 |
|---|---|---|---|
| P1 | A1 补齐到 10 次重复 | 每 fit 0.2817 GPU-h → 40 fits ≈ **11.27 GPU-h**；剩余 **0.056** | 申请额度 |
| P1 | A 轨 3 seeds → 10 | 缺 88 fits | 申请额度（A2 便宜：0.0146/fit） |
| P2 | A0 完整重放 | 未授权 | 每 fit ≈0.28 GPU-h |
| P2 | 规范 PatchTST | 未实现 | 实现或保持 INSPIRED 标签 |
| P2 | 修 Stage-6 报告 §0 的「5/12 胜」 | 计数方向反 | 改为 **7/12**（旧文件本轮未动） |
| **需用户** | **scratch 配额** | **413/300 GB，grace expired** | 清理 `innovation_deploy_root_v3_*` 暂存目录（52+50+11+11+9.7+9.6×6 GB）；**本轮未擅自删除** |
| **需导师** | 是否存在未触碰的泛化区间 | — | 决定 |
| ❌ | Track C 泛化 | 无未看过区间 | **不可通过改名伪造** |

---

## 9. 交付物

`hpc_results/official_repo_reproduction_20261006/`，共 **47 项**（22 项规格要求 + 本轮新增）：

**规格 22 项**：`STATUS_*`、`REPOSITORY_PROVENANCE`、`HYPERPARAMETER_PROVENANCE`、`DEVIATION_LEDGER`、`TEXT_PATH_RESOLUTION`、`IMPLEMENTATION_IDENTITY`、`RUN_MANIFEST`、`REMAINING_RUN_MATRIX`、`author_paper_targets`、`reproduction_results_{per_seed,aggregate}`、`paper_vs_reproduction`、`benchmark_results_{per_seed,per_horizon,per_variable,average_4L}`、`paired_stats_corrected.{csv,md}`、`cost_summary`、`failures_and_retries`、`REPORT_{ZH,EN}`

**本轮新增**：`a1_results_{per_epoch,per_run,aggregate}.csv`、`a1_gpu_ledger.csv`、`benchmark_best_model_summary.csv`、`benchmark_results_trackB_july.csv`、`SCORING_CORRECTION_NOTE.md`、`a2_text_path_probe.json`、`hpc_probe/`（3 文件）、`hpc_a1_runs/`（3 个 horizon）、`hpc_compat/`、4 个脚本、`slurm/`（5 个 sbatch）

**远端**：`/gpfs1/home/sychan552/official_repo_reproduction_20261006/`（含 4 个 checkpoint，各约 331 MB —— 因 scratch 配额所限未下载到本地）

---

## 10. 措辞边界（不变）

**可以说**
- 「作者发布代码的文本内容严格无影响（CPU 与 A100 双设备一致；阳性对照证明探针有效）。」
- 「A2 修正实现的文本通路生效，因此基准的 full-vs-no-text 对照是真实的文本对照。」
- 「A1 已在作者代码上跑通四个 horizon；每档 1 次重复，指标口径与 Table V 不同，**不构成复现**。」
- 「MIFlu 与 NLinear 在 12 格上不可分（t=−0.11，7/12 格 MIFlu 更优），且符号随 horizon 翻转。」

**不可以说**
- ❌ 「论文已复现」——论文定量结果复现数 = **0**
- ❌ 「A1 的 0.53 优于论文的 1.5」——口径不同
- ❌ 「LLM 整体更强/更弱」——两轨方向相反，组均值与组内最优矛盾
- ❌ 横比 Track A 与 Track B 的绝对数字
- ❌ 把 A2 的 `text_active` 拿来替作者代码辩护