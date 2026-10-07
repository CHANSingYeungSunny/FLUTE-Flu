# STATUS BEFORE CONTINUATION

生成时间：2026-10-06（本地 Windows 工作区）。
本轮性质：**只读核查 + CPU 重算 + 新建文件**。未删除、未覆盖、未修改任何旧 checkpoint / 预测 / 报告 / CSV。

---

## 0. 最高优先级：HPC 不可达（阻塞项，必须先读）

| 检查 | 命令 | 结果 |
|---|---|---|
| SSH 到 Burgundy | `ssh cityu` | ❌ `kex_exchange_identification: Connection closed by remote host` |
| SSH 到备用主机 | `ssh region-9.autodl.pro` | ❌ 同样被重置 |
| TCP 层 | `ssh -v` | 连接**能建立**，但在密钥交换阶段被远端关闭 |
| DNS | `Resolve-DnsName burgundy.hpc.cityu.edu.hk` | → `198.18.0.9`（保留网段，**非真实校园 IP**） |
| DNS 对照 | `Resolve-DnsName github.com` | → `198.18.0.31`（同一保留网段） |
| HTTPS | `curl https://github.com` | ✅ 200（走代理） |

**判定：本会话的网络被拦截层接管（整个 DNS 被改写进 198.18.0.0/15 保留段），SSH 在密钥交换阶段被远端直接关闭。这不是认证失败（未走到认证），也不是密钥问题。**

**后果（必须如实报告，不得假装已访问）：**

- ❌ **无法执行 `squeue -u $USER`** —— 当前队列状态**未知**，不是「无作业」
- ❌ **无法执行 `sacct`** —— 只能使用本地已捕获副本（见 §3）
- ❌ **无法 `sbatch` 提交任何作业**
- ❌ **无法在 GPU 上运行 text-path probe 的 GPU 半边**
- ❌ **无法完成 A1 的 10-seed 扩展训练**

**因此本轮的产出边界**：所有**不依赖 HPC 连接**的工作已实际执行完成（见 §5 交付物清单）；所有依赖 HPC 的工作已**准备好可直接提交的脚本**，但**没有提交**，也**不声称完成**。

**恢复 HPC 访问所需（需要用户操作）**：确认校园 VPN / SSH 网关是否已连接；或提供可用的跳板机。恢复后第一步应执行：

```bash
ssh cityu 'squeue -u $USER; sacct -S 2026-09-26 -X -o JobID,JobName,State,Elapsed,AllocTRES'
```

---

## 1. 工作区状态

| 项 | 值 |
|---|---|
| `pwd` | `C:\Users\Asus\Desktop\FYP code\MLFlu` |
| `git remote -v` | `origin https://github.com/CHANSingYeungSunny/FLUTE-Flu.git`（**项目自己的仓库**） |
| `git branch --show-current` | `recovery-stage4` |
| `git rev-parse HEAD` | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` |
| `git log -5 --oneline` | 只有 1 个 commit：`1f6563f FLUTE-Flu: MIFlu reproduction docs, scripts, figures (checkpoints excluded)` |

> ⚠️ 项目仓库**只有一个 commit**，没有历史可追溯。所有「何时做了什么」只能靠文件时间戳与 HPC 作业记录，不能靠 git history。

### 作者官方仓库（本地 checkout）

| 项 | 值 |
|---|---|
| 路径 | `recovery/author_repo/` |
| `git remote -v` | `origin https://github.com/Jmoon3108/MIFlu.git` ✅ **确为作者官方仓库** |
| `git rev-parse HEAD` | `6ed210150b8819313947cf607eb1821c87b1bee3` |
| commit 日期 | Fri Mar 21 15:24:23 2025 +0900（`Initial commit`） |
| 与恢复计划记录的候选版本 | ✅ **完全一致**（计划 §1 记录的 `6ed210150b8819313947cf607eb1821c87b1bee3`） |
| 是否为 partial clone | 是（`[blob:none]`，按需拉取 blob） |

### 数据文件身份（SHA-256 实测）

| 文件 | SHA-256 | 说明 |
|---|---|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | 作者仓库默认加载文件 |
| `recovery/author_repo/dataset/illness/national_illness_orig.csv` | `8594cecb98c6f2f9dc014eca11c4d5d1e38ad5ce6ed0592d4abe65b146fce395` | 作者另一份（966 行，数值与上者一致） |
| `data/raw/national_illness_raw_paper_exact.csv` | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | **A2/stage5/stage6 实际使用的 966 行文件**；前缀 `31ffc169…b87a` 与 stage6 报告记录一致 ✅ |
| `data/raw/national_illness_raw.csv` | （待测） | July-2026 1025 行快照，**Track B 专用，禁止与 A 轨混用** |

---

## 2. 本地修改（`git status --short`）

工作区有大量未提交修改（约 60+ 项），性质分类：

| 类别 | 例子 | 风险 |
|---|---|---|
| 被删除的旧产物 | `D HPC_GUIDE.md`、`D data/results_miflu_20260814_204437.csv`、`D results/ili/figures/q4_*.png` | 已 staged 删除，**非本轮所为** |
| 被修改的图表 | `M results/ili/figures/fig_miflu_eval_*_L*.png` | 旧的重新生成 |
| 被修改的指标 | `M results/ili/metrics/*.csv` | 旧的重新计算 |
| 被修改的文档 | `M PROJECT_STATUS.md`、`M README.md`、`M MIFlu_论文完整解析与答辩解答.md` | 旧的编辑 |
| 被修改的代码 | `M scripts/miflu_model.py`、`M scripts/diagnose_miflu.py`、`M scripts/compute_miflu_indicators.py` | ⚠️ **注意**：`scripts/miflu_model.py` 有未提交修改，任何新训练必须锁定实际使用的版本 |

**本轮未做任何新的修改或删除。** 完整 diff 见 `git diff` / `git diff --cached`。

---

## 3. HPC 作业状态（本地已捕获副本，非实时）

来源：`audit_20260930/sacct_jobs.psv`（951 行，捕获于 **2026-09-30 16:37**，**距本轮已 6 天，可能已过期**）。

### 3.1 已完成（有产物且通过完整性校验）

| 阶段 | 内容 | 数量 | 证据 |
|---|---|---:|---|
| Stage 5 (A2) | 3 模型 × 4 L × 3 seeds 学习拟合 | **36** | `hpc_results/stage5_a2/scoring/predictions/*.npz`（36 个 pred_miflu/nlinear/notext） |
| Stage 5 (A2) | 确定性基线评估 | **8** | 同上（4× last_value + 4× seasonal_naive） |
| Stage 5 (A2) | 统一 Test 评分 | **44** | `hpc_results/stage5_a2/scoring/score_matrix.csv` |
| Stage 6 | 新增六骨干 × 4 L × 3 seeds | **72** | `run_ledger.csv` 全部 `exit=0`；`audit_20260930/predictions_stage6/*.npz` |
| Stage 6 | 统一 Test 评分 | **116** | `hpc_results/stage6/scoring/score_matrix.csv` |
| Stage 6 | A0 GPU 最小诊断 | **2**（MODE=0/1） | `hpc_results/stage6/a0_gpu/a0_587091.out`、`a0_587068.out` |
| — | checkpoint 锁定 | **108** | `hpc_results/stage6/scoring/CHECKPOINT_LOCK.csv` |

**Stage 6 台账核对**：`run_ledger.csv` 75 行 = 72 个唯一 `(model, L, seed)` 格 + 3 个 DLinear-L48 重试；全部 `exit=0`。

### 3.2 失败 / 重试（全部已定位，均为良性）

| 作业 | 状态 | 原因 | 影响 |
|---|---|---|---|
| 587048 / 587054 / 587059 | FAILED | A0 依次：import blocker / `--checkpoints` 目录不存在 / `itr` 越界 | 无产物损伤，已同配置恢复 |
| 587068 | FAILED（旧包装） | 作者代码返回 `rc=1`，旧包装脚本直接判 FAILED | **产物有效**（跑了完整 82 秒重放） |
| 587373 | FAILED | `build_lock_stage5.py` 相对路径解析到错误阶段 | 未开始评分，无损伤 |
| 587385 | exit 3 | 收尾断言期望计数过时（104 vs 116） | **评分矩阵完整写出**，无损伤 |
| 587243 | CANCELLED | 被 `90731875` 取代（该 ID 在本集群不存在） | 无产物依赖 |

### 3.3 缺失 / 未提交

| 项 | 状态 |
|---|---|
| A0 **完整**逐字重放（论文级配置，4 L × 3 seeds） | ❌ **未执行**（仅最小诊断） |
| A1 论文配置复现（4 L × 10 seeds = 40 fits） | ❌ **未执行**（A2 用的是 20ep/5e-4 的项目假设，非论文配置） |
| A 轨种子从 3 扩到 10 | ❌ **未执行** |
| 2×2 text/LoRA 矩阵（160 fits） | ❌ **未授权、未执行** |
| 规范 PatchTST（canonical） | ❌ 未执行（现为 inspired 实现） |
| regional / few-shot / 表 VI / 表 VII / 表 IX | ❌ 未开展 |
| Track C 独立泛化 | ❌ **BLOCKED**（不存在未看过区间） |
| **text-path CPU/GPU 同脚本对照 probe** | ❌ **未执行 → 本轮已写好脚本，待 HPC 恢复后提交** |

### 3.4 GPU 消耗（独立计算，来自本地捕获的 sacct）

| 类别 | GPU-hours |
|---|---:|
| Stage 6 COMPLETED 作业 | 1.0500 |
| Stage 6 FAILED 作业 | 0.0756 |
| **Stage 6 合计** | **1.1256** |
| Stage 5 超额但已计费 | 0.4400 |
| 不计入（job 586949 `diaggen-visual`，另一项工作） | — |

Stage 6 授权上限 2.3 GPU-h，**剩余约 1.17 GPU-h 未花**。

---

## 4. 产物完整性校验（本轮实测）

| 校验 | 方法 | 结果 |
|---|---|---|
| Stage 6 预测张量 | 从 116 个 NPZ 重新计算 MSE，与 `score_matrix.csv` 逐格比对 | ✅ **116/116 吻合**，最大相对差 `1.527e-07`（float32 精度下限） |
| Stage 5 预测张量 | 同上，44 格 | ✅ 吻合 |
| Stage 5/6 复用一致性 | `miflu`/`nlinear`/`notext` 在两阶段数值完全相同 | ✅ 证明为复用而非重跑，与叙述一致 |
| B 轨 seed 级表 | 从 320 行重新聚合 | ✅ 与 `model_ranking.csv` 一致 |
| 数据 hash | SHA-256 实测 vs 报告记录 | ✅ `31ffc169…b87a` 匹配 |
| 作者仓库 commit | `rev-parse HEAD` vs 计划记录 | ✅ 匹配 |
| 作者源码树是否被改动 | probe 实测 `author_source_dirty_files = []` | ✅ **零源码修改**（仅 `.pyc` 重新生成） |
| 文本通路 P0 | 等长替换 max\|Δpred\| = 0 + 阳性对照 3.55e-05 | ✅ **CPU 侧定论 `text_inert`** |

---

## 5. 本轮实际交付（不依赖 HPC 的部分）

| # | 交付物 | 状态 |
|---|---|---|
| 1 | `STATUS_BEFORE_CONTINUATION.md` | ✅ 本文件 |
| 2 | `REPOSITORY_PROVENANCE.md` | ✅ |
| 3 | `HYPERPARAMETER_PROVENANCE.md` | ✅ |
| 4 | `DEVIATION_LEDGER.md` | ✅ |
| 5 | `TEXT_PATH_RESOLUTION.md` | ⚠️ **PENDING-HPC**（CPU 半边已本地执行，GPU 半边待提交） |
| 6 | `IMPLEMENTATION_IDENTITY.md` | ✅ |
| 7 | `RUN_MANIFEST.csv` | ✅ |
| 8 | `REMAINING_RUN_MATRIX.csv` | ✅ |
| 9 | `author_paper_targets.csv` | ✅ |
| 10–11 | `reproduction_results_per_seed.csv` / `_aggregate.csv` | ✅（3 seeds，明确标注） |
| 12 | `paper_vs_reproduction.csv` | ✅ |
| 13–16 | `benchmark_results_*.csv` | ✅（独立 scorer 重算） |
| 17 | `paired_stats_corrected.csv` / `.md` | ✅（胜场方向已修复 + unit test） |
| 18 | `cost_summary.csv` | ✅ |
| 19 | `failures_and_retries.csv` | ✅ |
| 20–21 | `REPORT_ZH.md` / `REPORT_EN.md` | ✅ |
| 22 | Slurm 脚本 / probe / 独立 scorer | ✅（已写，**未提交**） |

---

## 6. 下一步最小可执行动作（按顺序）

1. **【需要用户】** 恢复 HPC 网络访问（VPN / 跳板机）。
2. **【HPC 恢复后第一条命令】** `ssh cityu 'squeue -u $USER; sacct -S 2026-09-26 -X'` —— 确认是否有残留作业。
3. **【HPC】** 提交 text-path 对照 probe：`sbatch slurm/probe_text_path_cpu.sbatch` + `sbatch slurm/probe_text_path_gpu.sbatch`（**同一脚本、同一 checkpoint**）→ 解决 P0 矛盾。
4. **【HPC】** 提交 A1 复现 array（预算内最大不重复 run）。
5. **【本地】** 每有结果落地即用 `scripts/score_predictions_independent.py` 独立评分。

**不得**在 HPC 恢复前声称任何训练、评估或复现已完成。