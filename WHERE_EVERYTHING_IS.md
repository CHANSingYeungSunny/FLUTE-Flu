# 文件地图 —— 什么东西在哪里

> 一页纸回答："我要的东西在哪个文件？"　最后更新：2026-11-02

---

## §1 三份报告（全在 `01_最终报告/`）

| 报告 | 给谁看 | 页数 | 中文 | 英文 |
|------|--------|------|------|------|
| **内部技术报告**（最全） | 导师、接手的人 | 20 | `report_internal_zh.docx` / `.pdf` | `report_internal_en.docx` / `.pdf` |
| **FYP 进度报告**（简版） | 学校模板 | 5 | `progress_report_zh.docx` / `.pdf` | `progress_report_en.docx` / `.pdf` |
| **IEEE 论文稿**（投稿） | 期刊 | 6 | `ieee_manuscript_zh.docx` / `.pdf` | `ieee_manuscript_en.docx` / `.pdf` |

- 插图：`01_最终报告/figures/`
- 发给 ChatGPT：`01_最终报告/PROJECT_HANDOFF.zip` + `01_最终报告/chatgpt_prompt.md`
- 文件清单：`01_最终报告/MANIFEST.md`

**PDF 已签名、字体已嵌入，可直接发导师。**

---

## §2 数字（全在 `02_数字表格/`，都是 CSV）

| 我要查 | 打开这个 | 关键列 |
|--------|---------|--------|
| **复现 vs 论文对比** | `ESSAY_VS_REPRODUCTION_TABLE_V.csv` | `paper_mse` / `our_mse` / `delta_pct` |
| **所有模型准确率** | `BENCH_MSE_BY_MODEL_L.csv` | `mse_7var_z` |
| **排名（28 个模型）** | `BENCH_MSE_RANK_FULL.csv` | `mse_7var_z` |
| **峰值预测 PTE/PIE** | `BENCH_PTE_PIE_BY_STEP.csv` | `step` / `PTE_wk` / `PIE_pct` / `kramer_shaman_pass` |
| **谁通过 K&S 标准** | `BENCH_KS_CHAMPION_DETAIL.csv` | 通过情况 |
| **效率（参数量/耗时）** | `BENCH_EFFICIENCY.csv` | `params` / `wall_s` |
| **显著性检验** | `BENCH_PAIRED_TESTS.csv` | `p_value` |
| **按模型家族汇总** | `BENCH_MSE_BY_FAMILY.csv` | 家族平均 |
| **季节朴素基线** | `BENCH_SEASONAL_NAIVE.csv` | 基线 |
| **GPU 来源证据** | `BENCH_GPU_PROVENANCE.csv` | `gpu_name` / `partition` / `job_id` |

### ⚠️ 文件名带后缀的不要用

| 后缀 | 意思 | 用吗 |
|------|------|------|
| `.pre_evalwindow16` | 改评分方式**之前**的旧版 | ❌ |
| `.pre_miflu` | MIFlu 入表**之前**的旧版 | ❌ |
| `.post_evalwindow16` 等 | 中间实验分支 | ❌ |
| **没后缀的** | **最终版** | ✅ |

### 两个必须记住的事

1. **两套种子不能混着比**
   - **复现**：种子 2021–2030，10 次 → 对应论文 Table V
   - **对比**：种子 42/43/44，3 次 → 28 个模型互相比
   - 同一模型这两个数字不一样是正常的。

2. **MSE 和 PTE/PIE 是两回事**
   - MSE = 整条曲线平均差多少
   - PTE/PIE = 峰值那天有没有猜中
   - **MSE 冠军 ≠ 峰值冠军**，这是本文核心发现。

---

## §3 原始证据（`03_预测数据_证据/expanded_runs/`）

每次运行一个文件夹，命名：`<模型名>_L<跨度>_s<种子>/`
例：`miflu_L24_s42/` = MIFlu，预测 24 周，种子 42。

| 文件 | 用途 | 能删吗 |
|------|------|--------|
| `pred_*.npz` | 预测值 + 真值（**唯一能重新推导数字的来源**） | ❌ **绝对不能删** |
| `manifest_*.json` | 运行记录（GPU、分区、作业号、耗时） | ❌ |
| `results_*.csv` / `metrics.csv` | 该次运行的指标 | ⭕ 可重建 |
| `ckpt/` | 模型权重 | ⭕ 可重训 |

### 哪些是复现、哪些是对比

| 种子 | 用途 |
|------|------|
| `s2021` ~ `s2030` | **复现**论文 Table V |
| `s42` / `s43` / `s44` | **28 模型对比** |

---

## §4 详细文档（`04_详细说明文档/`）

| 文件 | 什么时候看 |
|------|-----------|
| `LEDGER.md` | **总账本**，所有已确认数字和决定 |
| `HANDOFF_20261102.md` | 接手时先读（完整状态） |
| `GAP_PLANS_20261102.md` | 3 个未完成缺口 + 成本（A100 小时） |
| `BUG_POSTMORTEM_20261102.md` | 踩过的 8 个坑 + 7 个误判 |
| `GLOSSARY.md` | 名词看不懂时查 |
| `METHODOLOGY_METRICS_AND_SPLIT.md` | 方法、指标、数据划分定义 |
| `BENCHMARK_MODEL_ROSTER.md` | 28 个模型分别是什么 |
| `LLM_ARMS.md` | 11 个 LLM 编码器细节 |
| `AUTHOR_REPO_FIDELITY.md` | 与作者原代码逐行对比 |
| `HPC_RUNBOOK.md` | 怎么在集群上跑 |
| `agent/` | 给 AI 助手看的任务书 |

---

## §5 集群（HPC）

| 项目 | 值 |
|------|-----|
| 主机 | `burgundy.hpc.cityu.edu.hk`（SSH 别名 `cityu`） |
| 根目录 | `/gpfs1/home/sychan552/stage5_a2_durable`（简称 `$R`） |
| 队列 | `$R/code/queue/master_queue.tsv` |
| 驱动作业 | **722968**（`tiny` 分区，5 天） |
| 查作业 | `sacct -X -S <日期> -u sychan552`（**不要用 `squeue`**） |

> **改名只动了本地仓库，`$R` 上一个字节没变**，跑着的作业不受影响。

---

## §6 四个核心问题的答案

| # | 问题 | 答案 | 数据 |
|---|------|------|------|
| 1 | 复现成功了吗？ | **基本成功**：4 跨度平均 **1.4995**，论文 1.4355，**差 +4.5%**，2 好 2 差 | `ESSAY_VS_REPRODUCTION_TABLE_V.csv` |
| 2 | 谁最准？ | **MIFlu 1.5574**；PatchTST 1.6621；NLinear 1.8716；DNN 2.1415 | `BENCH_MSE_RANK_FULL.csv` |
| 3 | 该部署哪个？ | **MIFlu**（最准）或 **NLinear**（0.3% 参数量、峰值也准） | `BENCH_EFFICIENCY.csv` |
| 4 | LLM 有用吗？ | **没用**。最好 Hunyuan-1.8B = 4.7374（比 MIFlu 差 3 倍），**无一通过 K&S** | `BENCH_MSE_BY_MODEL_L.csv` |

**一句话**：论文结论成立（LLM 多模态有效），但**最值得部署的不是最准的** —— 这就是本文多出的贡献。

---

## §7 还没做完的

| 项目 | 状态 | 成本 |
|------|------|------|
| Table VI 区域预测 | 集群排队中 | ~7.7 A100 小时 |
| Table IX 区域训练时间 | 等 Table VI | 0 |
| 滚动起点评估 | 有代码未跑 | 155–360 A100 小时 |
| 跨数据集（WHO FluNet） | 未开始 | ~10 A100 小时 |

详见 `04_详细说明文档/GAP_PLANS_20261102.md`。
