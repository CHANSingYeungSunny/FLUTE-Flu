# REPOSITORY PROVENANCE

日期：2026-10-06

---

## 1. 项目仓库

| 项 | 值 |
|---|---|
| `pwd` | `C:\Users\Asus\Desktop\FYP code\MLFlu` |
| `git remote -v` | `origin https://github.com/CHANSingYeungSunny/FLUTE-Flu.git` |
| `git branch --show-current` | `recovery-stage4` |
| `git rev-parse HEAD` | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` |
| commit 数 | **1**（`FLUTE-Flu: MIFlu reproduction docs, scripts, figures (checkpoints excluded)`） |
| 工作区状态 | 约 60+ 项未提交修改（详见 §4） |

> ⚠️ **单 commit 仓库**：无法用 git history 追溯实验时序。所有时序判断必须依赖文件时间戳、HPC 作业记录（sacct/ledger）与日志，不能依赖 git。

---

## 2. 作者官方仓库（复现对象）

| 项 | 值 | 判定 |
|---|---|---|
| 路径 | `recovery/author_repo/` | — |
| `git remote -v` | `origin https://github.com/Jmoon3108/MIFlu.git` | ✅ **确为作者官方仓库**（非 fork、非镜像） |
| `git rev-parse HEAD` | `6ed210150b8819313947cf607eb1821c87b1bee3` | — |
| commit 元数据 | `Fri Mar 21 15:24:23 2025 +0900`，`Initial commit` | — |
| 与恢复计划记录的候选版本 | `6ed210150b8819313947cf607eb1821c87b1bee3` | ✅ **完全一致** |
| clone 类型 | partial（`blob:none`） | ⚠️ 按需拉取 blob；若网络中断，部分文件可能缺失 |
| 已知缺陷 | `embed.py` 缺失（仅剩 `__pycache__/embed.cpython-39.pyc`） | 已在 `recovery/a0/a0_compat.py` 记录重建 |

### 本地是否改动过作者树

`recovery/a0/a0_cpu_audit.sh` 与本轮 probe 均声明：**作者源码树逐字节未改**，兼容层放在独立 `sys.path` 目录。

**本轮实测核验**（写入 `text_path_probe_cpu_local.json`）：

| 字段 | 值 |
|---|---|
| `author_commit` | `6ed210150b8819313947cf607eb1821c87b1bee3` |
| `author_source_dirty_files` | **`[]` — 源码树零修改** ✅ |
| `author_commit_dirty_files` | `["models/__pycache__/GPT4TS_lora.cpython-39.pyc"]`（仅 `.pyc`，由 import 自动重新生成，非源码改动） |
| `author_model_sha256` | `6ef9108eea3c068badb7f8a60efba9717b4e7fe969b46365ac7c26da560c6365` |

**结论：作者源码树逐字节未改**，兼容层全部位于独立 `sys.path` 目录。

### HPC 上的作者 checkout（2026-10-06 联网实测）

| 项 | 值 |
|---|---|
| 路径 | `/scratch/sychan552/a0_replay` |
| `git rev-parse HEAD` | `6ed210150b8819313947cf607eb1821c87b1bee3` ✅ 与本地和计划记录一致 |
| `git status --porcelain`（排除 `.pyc`） | 仅 `?? results/` —— A0/A1 运行时作者代码自己写 summary CSV 所需的**输出目录**，非源码 |
| `git diff --stat` | 9 files changed, **0 insertions, 0 deletions** → 全部是二进制 `.pyc`，**无源码改动** |
| A1 运行时二次核验 | `provenance.txt` 记录 `author_source_modified=1 non-pyc entries`，经查即为上述 `results/` 目录 |

---

## 3. 数据身份

| 文件 | 行数 | SHA-256 | 用途 | 允许与谁比较 |
|---|---:|---|---|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | 966 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | 作者仓库**默认加载**文件 | 仅 Track A |
| `recovery/author_repo/dataset/illness/national_illness_orig.csv` | 966 | `8594cecb98c6f2f9dc014eca11c4d5d1e38ad5ce6ed0592d4abe65b146fce395` | 作者另一份（数值与上者一致） | 仅 Track A |
| `data/raw/national_illness_raw_paper_exact.csv` | 966 | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | **A2 / stage5 / stage6 实际使用** | 仅 Track A |
| `data/raw/national_illness_raw.csv` | 1025 | 待测 | July-2026 快照 | **仅 Track B** |

**轨道隔离规则（强约束）**：
- Track A（966 行）与 Track B（1025 行）的绝对 MSE **禁止同表排名、禁止求平均、禁止互相填空**。
- A 轨 3 seeds / B 轨 10 seeds，**口径不同**。
- `31ffc169…b87a` 前缀与 `recovery/stage6/results_report_zh.md` §2 记录一致 ✅（本轮实测复核）。

---

## 4. 工作区未提交修改（摘要）

| 类别 | 代表文件 | 风险 |
|---|---|---|
| staged 删除 | `D HPC_GUIDE.md`、`D data/results_miflu_20260814_204437.csv`、`D results/ili/figures/q4_*.png` | 早期清理，**非本轮** |
| 重新生成的图 | `M results/ili/figures/fig_miflu_eval_*.png` | 与旧版并存于历史 |
| 重新计算的指标 | `M results/ili/metrics/*.csv` | 同上 |
| **代码修改** | `M scripts/miflu_model.py`、`M scripts/diagnose_miflu.py`、`M scripts/quick_test.py`、`M scripts/compute_miflu_indicators.py` | ⚠️ **任何新训练必须锁定实际使用的代码版本**；仅靠 git commit 无法识别 |

> ⚠️ 因为仓库只有一个 commit，`scripts/miflu_model.py` 的未提交修改**无法通过 git 复原到「训练时的版本」**。这是本项目的**可复现性缺口**，必须在报告中声明。

---

## 5. 复现边界声明

**已确认为一手证据的**：
- 作者仓库 URL 与 commit ✅
- 三份数据文件的 SHA-256 ✅
- 论文 PDF 文本抽取（`audit_20260930/paper_text.txt`）✅

**不能确认的**：
- 作者**实际运行**时用的是仓库默认值还是覆盖值（仓库无 CI、无 launch 脚本、无 README 命令）
- 论文 Table V 的 MIFlu 列是否也含引用成分（论文只说明**基线列**引自 [9]/[14]）
- 文档中「20 epochs / lr 5e-4 = 论文设置」的说法**无出处**（见 `HYPERPARAMETER_PROVENANCE.md`）

**结论**：仓库身份**完全可核验**；**论文实验配置不可核验**。任何「已复现论文」的主张都必须跨过后者这道坎。