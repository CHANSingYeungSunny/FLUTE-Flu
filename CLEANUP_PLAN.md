# CLEANUP_PLAN.md — 开源前清理清单（**待批准，尚未执行任何删除**）

> **状态：仅清单。** 本文件生成过程中**没有删除、移动或修改任何文件**。
> 所有条目需经你逐项批准后才可执行。建议先整体打包一份快照再动手。

## 0. 受保护目录（绝对不动）

| 路径 | 原因 |
|---|---|
| `scripts/` | 核心训练/评估代码（本轮重构目标，不是清理目标） |
| `hpc_scripts/` | 新建的投递脚本目录（PHASE 2.3 产物） |
| `data/raw/` | **原始输入数据**，删了不可恢复 |
| `hpc_results/journal_evidence/` | **最终期刊证据**，不可删 |
| `.codebuddy/memory/` | 跨会话工作记忆 |
| `.git/` | 版本历史 |

---

## A. 根目录散落脚本与临时文件（16 项）

你提到要清理的几类，**实测结果与描述有出入**（见 E 节）。以下均已逐文件读取开头确认用途。

### A-1 建议删除（10 项）—— 一次性探测/已被取代

| 文件 | 大小 | 用途判定 | 删除理由 |
|---|---|---|---|
| `_tmp_hpc2.sh` | 594 B | 一次性远端文件存在性探测（`ls`/`find`） | 一次性，已无用 |
| `_tmp_hpc3.sh` | 631 B | 一次性远端探测，打印 3 个**现已不存在**的脚本头部 | 引用目标已消失 |
| `_tmp_hpc4.sh` | 582 B | 一次性远端探测，grep + 查 `submit_ili_multihorizon.sh`；**引用了已不存在的 `PROJECT_STATE.md`** | 目标已消失、路径已失效 |
| `_tmp_mon.sh` | 518 B | 一次性作业监控快照（`squeue`+`sacct`+`tail`） | 单次快照，非守护进程 |
| `hpc_probe.sh` | 623 B | 一次性远端环境探测（torch/cuda 版本），硬编码 `sychan552` | 一次性；硬编码路径不宜开源 |
| `hpc_probe2.sh` | 221 B | 仅 3 行，打印 torch/cuda/cudnn 版本 | 已被 `hpc_probe.sh` 完全覆盖 |
| `check_anchor_env.sh` | 698 B | 为某一次 anchor 提交服务的提交前自检 | 一次性，服务于已结束的提交 |
| `auto_submit_l36_48_60.sh` | 1.06 KB | L=36/48/60 串行重投，但用的是**修复前的旧轮询逻辑**（sbatch 后只等"消失"，会误判并触发 `QOSMaxSubmitJobPerUserLimit`） | 已被 `auto_submit_l48_60.sh` 的修复版取代；其注释自述该 FIX 是从这次失败学到的 |
| `_tmp_pdftable.py` | 475 B | 一次性用 `pypdf` 从论文 PDF 抽取 TABLE IV | 一次性 |
| `_tmp_pdftable_out.txt` | 3.81 KB | 上一条的输出（论文 TABLE IV 超参摘录） | 超参已固化进 `MIFlu_paper.md`/`docs/` |

> `.gitignore` 已含 `_tmp_*` 与 `*.tmp`，A-1 中的临时脚本**本来就没进版本库**，删掉对开源包零影响。

### A-2 建议保留（6 项）—— 属复现流程或有长期价值

| 文件 | 大小 | 保留理由 | 建议处置 |
|---|---|---|---|
| `auto_submit_anchor.sh` | 1.55 KB | GPT4TS anchor probe 串行重投，含 QOS 修复逻辑 | 移入 `hpc_scripts/` |
| `auto_submit_diag.sh` | 2.66 KB | 三臂组件诊断扫描（no_multi/no_lora/full），对照 Table VIII | 移入 `hpc_scripts/` |
| `auto_submit_sens.sh` | 2.66 KB | 训练配方敏感性扫描（ep50/ep100/lr），论文附录可引用 | 移入 `hpc_scripts/` |
| `auto_submit_l48_60.sh` | 1.33 KB | L=48/60 重投，**带 APPEAR→DISAPPEAR 修复版** | 移入 `hpc_scripts/` |
| `hpc_gpu_check.sh` | 568 B | 通用集群工具（`sinfo` 查空闲 GPU + `squeue`），无副作用 | 移入 `hpc_scripts/` |
| `verify_forward.py` | 1.16 KB | 冒烟测试：验证 `MIFlu.forward` 返回 4 元组 + 一次 fwd/bwd | 移入 `tests/`（其 `sys.path` 已指向 `scripts/`） |

---

## B. 缓存与字节码

| 项 | 实测 | 处置 |
|---|---|---|
| `scripts/**/__pycache__/*.pyc` | 目录列表显示 `scripts/` 下有 **12 个 `.pyc`** | 删除（100% 可再生） |
| `.pytest_cache/`（7 个文件：`.gitignore`、`CACHEDIR.TAG`、`README.md`、`v/cache/lastfailed`、`nodeids`、`stepwise`） | 存在 | 删除（pytest 自动生成） |

> 注：`.gitignore` 第 7–8 行已正确排除 `__pycache__/` 与 `*.pyc`，但这些文件仍物理存在于工作区，开源打包时应清除。

---

## C. 陈旧备份目录

### `_mlflu_wt_backup_20260830/`（15 个文件）
| 内容 | 判定 |
|---|---|
| `SHA256_MANIFEST.txt`（1.8 KB，15 行哈希） | 清单本身 |
| `.codebuddy/memory/2026-08-18.md`（13.52 KB） | 与当前同名文件大小一致，疑似相同 |
| `.codebuddy/memory/MEMORY.md`（7.25 KB） | 当前 `MEMORY.md` 已是 **8.1 KB**，已被取代 |
| 其余 8 `.png` + 4 `.csv` | 旧版图表/结果，已被 `results/ili/` 与 `hpc_results/` 下更新产物取代 |

**建议**：整体删除，或先移到仓库外冷存储再删。**删前建议核对 `SHA256_MANIFEST.txt`**，确认其中没有唯一留存的文件。

---

## D. 非最终期刊证据的旧产物

### D-1 `data/`（除 `raw/` 与 scaler 外）
| 文件 | 判定 | 建议 |
|---|---|---|
| `data/raw/national_illness_raw.csv` | **原始输入** | 🔒 **保留（受保护）** |
| `data/scaler_miflu_national.json` | `mean_`/`scale_` 落盘，逆变换与审计依赖 | 🔒 **保留** |
| `predictions_miflu_L{24,36,48,60}_paper_protocol.csv` | 旧版预测导出（新布局将输出到 `hpc_results/...`） | ⚠️ 待你确认后删除（可再生） |
| `q4_causality_summary.csv` | 旧分析产物 | ⚠️ 待确认 |
| `results_miflu_20260814_204437.csv` | 带时间戳的旧结果快照 | 删除（可再生） |
| `training_miflu_log_20260816_173454.txt`<br>`training_miflu_log_20260828_215025.txt` | 旧训练日志 | 删除 |
| `data/ili/` | 子目录，需进一步甄别 | ⚠️ 待确认 |

### D-2 `checkpoints/`（5 项）
`best_miflu_L{24,36,48,52,60}.pth` —— 主流程旧检查点。
⚠️ **高风险**：模型权重，删了需重训才能恢复。建议**保留或移到仓库外冷存储**，不要随开源包发布（体积大）。

### D-3 `results/ili/`（30 文件：14 png / 7 csv / 5 json / 4 md）
最终图表与结果。建议**保留**（这是图表证据），但需甄别其中是否有被 `hpc_results/journal_evidence/figures/` 取代的旧版。

### D-4 其它目录
`analysis/`、`archive/`、`docs/`、`tests/`、`reference_papers/` —— 需逐个甄别后决定；`docs/` 含论文笔记与审计文档，倾向保留。

---

## E. 与任务描述不符的实测事实（重要，请知悉）

| 你的描述 | 实测结果 |
|---|---|
| "stray `.sh`/`.ps` 文件，尤其 watchdog 脚本" | **`.ps` 文件 0 个**；**`*.ps1` 仅 1 个**（在 `scripts/` 下）；**`watchdog*` 文件 0 个**（全项目任意大小写、任意扩展名搜索均无命中）。故"watchdog 后台任务脚本"这一类**不存在**。 |
| "old HPC submit scripts not in `hpc_scripts/`" | **`hpc_scripts/` 目录不存在**；14 个 `.sh` 全部位于 `scripts/` 下。PHASE 2.3 会新建该目录并把它们移入。 |
| `__pycache__` | 存在（12 个 `.pyc`），见 B 节。 |

---

## F. 汇总

| 分类 | 建议删除 | 建议保留/待确认 |
|---|---|---|
| A 根目录散落 | 10 | 6 |
| B 缓存 | 12 `.pyc` + 7 `.pytest_cache` | 0 |
| C 陈旧备份 | 15（整目录） | 0（建议先核对 manifest） |
| D 旧产物 | 若干（可再生 CSV/日志/预测） | `checkpoints/`（⚠️高风险）、`results/ili/` |

---

## G. 拟执行命令（**未执行，待批准**）

```bash
# 0) 先打包快照（强烈建议）
cd "C:/Users/Asus/Desktop/FYP code"
tar -czf MLFlu_before_cleanup_$(date +%Y%m%d).tar.gz MLFlu/

cd "C:/Users/Asus/Desktop/FYP code/MLFlu"

# A-1 根目录一次性脚本
rm -f _tmp_hpc2.sh _tmp_hpc3.sh _tmp_hpc4.sh _tmp_mon.sh \
      hpc_probe.sh hpc_probe2.sh check_anchor_env.sh \
      auto_submit_l36_48_60.sh _tmp_pdftable.py _tmp_pdftable_out.txt

# B 缓存
rm -rf .pytest_cache
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -name "*.pyc" -delete

# C 陈旧备份（删前请核对 SHA256_MANIFEST.txt）
rm -rf _mlflu_wt_backup_20260830/

# D-1 可再生旧产物（data/ 下，不含 raw/ 与 scaler）
rm -f data/results_miflu_*.csv data/training_miflu_log_*.txt
# ⚠️ 以下四项待你确认后再删：
# rm -f data/predictions_miflu_L*_paper_protocol.csv data/q4_causality_summary.csv

# 移动保留项到规范位置（非删除）
mkdir -p hpc_scripts tests
mv auto_submit_anchor.sh auto_submit_diag.sh auto_submit_sens.sh \
   auto_submit_l48_60.sh hpc_gpu_check.sh hpc_scripts/
mv verify_forward.py tests/
```

> 批准方式：告诉我「执行 A-1+B+C」「全部执行」或「只执行某几项」，我再动手。
> 在得到明确批准前，磁盘上不会有任何文件被删除。
