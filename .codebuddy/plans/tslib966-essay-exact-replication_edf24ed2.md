---
name: tslib966-essay-exact-replication
overview: 在 HPC 上用 TSLib 原版 national_illness.csv（966 行，即论文实际所用数据）跑全部 4 个 horizon（L=24/36/48/60）× 10 reps，产出与论文 Table V 逐档对照的最终复现表，作为"与论文一模一样"的收尾证据。全程隔离目录，不触碰主目录与本地训练逻辑。
todos:
  - id: build-exact-data
    content: 下载官方 TSLib csv，文本级转换注入真实 epiweek，校验 966 行、数值零改动与 split 边界
    status: completed
  - id: submit-exact-run
    content: 建 HPC 隔离目录 Chattime_paper_exact，提交全量 SLURM 作业（四档 L×10 reps+出图）
    status: completed
    dependencies:
      - build-exact-data
  - id: collect-results
    content: 分段轮询至完成，回收结果 CSV、预测 CSV、图与日志到 hpc_results/paper_exact/
    status: completed
    dependencies:
      - submit-exact-run
  - id: write-verdict
    content: 撰写 REPLICATION_VERDICT.md：Table V 三方对照、OT 说明、复现状态清单、通俗现状总结
    status: completed
    dependencies:
      - collect-results
  - id: update-memory
    content: 更新 MEMORY.md 与当日记忆，固化论文精确复现终跑结论
    status: completed
    dependencies:
      - write-verdict
---

## 用户需求

1. **现状通俗说明**：用户表示“完全不知道现在进展到哪了”，需要一份通俗、清晰的现状说明：哪些部分已核验与论文一致、还剩哪一项差异、这次要做什么、预期得到什么。
2. **OT 变量确认**：确认论文中 OT 变量的实际含义，以及我们使用的 OT 是否与论文一致（此项核查已完成，结论将写入报告：语义完全一致，仅少量周因官方数据回溯修订而数值不同）。
3. **论文精确复现终跑**：把唯一剩余的差异（数据文件）替换为官方基准数据集的逐字节数据，按论文协议在隔离环境完整重跑全部四档预测长度（各 10 次重复），训练后自动生成评估图。
4. **复现判定**：给出“是否完美复现论文”的明确结论，含逐项一致性清单（架构、超参、协议、OT、数据、训练配方）与论文结果表的数值对照。

## 产品概述

一次“论文精确复现”终跑加一份结论报告：在隔离环境用官方数据完整重跑论文协议，产出与论文结果表直接可比的对照数据（全通道 MSE/MAE，含均值与波动范围）、四档预测明细与物理尺度评估图，并以清单形式逐项判定复现状态，同时用通俗语言总结当前全局进展。

## 核心功能

- 官方数据集下载、格式转换与逐值校验（行数、七列数值零改动、真实周历注入、训练/验证/测试边界核验）
- 隔离环境全量训练与自动出图（不触碰既有主结果与主协议）
- 结果回收与论文结果表三方对照（论文精确版 / 论文原值 / 现有全量数据版）
- OT 变量定义与一致性说明
- 复现状态判定清单与通俗现状总结

## 技术栈

- **复用现有管线（零训练逻辑改动）**：`scripts/train_miflu.py`、`miflu_model.py`、`textual_embedder.py`、`make_miflu_evaluation_figure.py`（HPC 主目录已是 2026-08-28 升级版，含 `_phys` 导出，已验证可运行）
- **数据源**：官方 TSLib `national_illness.csv`（966 行），下载地址（本日已验证可用）：`https://huggingface.co/datasets/thuml/Time-Series-Library/resolve/main/illness/national_illness.csv`
- **算力**：CityUHK Burgundy HPC，`stingy` 分区 + `gpu:a100:1` + `--time=04:00:00`，单作业顺序跑全量（预计 ~110–120 分钟，含充足余量）
- **本地**：Windows PowerShell + OpenSSH/scp

## 实现方案（数据替换 + 隔离终跑）

### 已核验的关键事实（本方案的基础）

1. **OT 变量（用户问题 2 的答案）**：论文 Table X 仅称 "'OT' feature for long-term forecasting task"（无公式，paper:502-505）；官方 TSLib csv 的 OT 列 ≡ `ILITOTAL / (%UNWEIGHTED ILI / 100)` = **总就诊人次（分母）**。本地验证：我们的 OT 与该公式**相对误差 0.0%**；与官方 csv OT 列在重叠 966 周中 **889 周逐位相同**，77 周差异纯属 CDC 回溯修订（我们是更新的 CDC 下载）。**结论：同一 OT 变量。**
2. **数据对齐**：TSLib 官方 966 行 ≡ 我们 raw 的行 20–985（锚点：最大 ILITOTAL 111,361 在 TSLib 行 905 = 本地行 925；偏移 +20 全程成立；913/966 周 ILITOTAL 逐位相同）。其真实周历跨度 = epiweek 200240→202113，恰与论文自述 "between 2002 and 2021"（paper:238）吻合。
3. **为什么官方 csv 是“论文数据”**：论文 Table V 基线数字直接取自 [9]（GPT4TS/TSLib 同数据集运行），MIFlu 自报结果与之同表比较；论文对数据集的描述（2002–2021）与该 csv 的真实周历一致。同时保留我们 8-17 的全量 1025 行结果作为“作者可能用新 CDC 下载”的替代情景，**两套都报告**。
4. **为何此前 control966 不算"exact"**：它截的是行 0–965（保留头部 20 周、切掉 2021 年 39 周），与官方 966 行相差 20 周平移；本次改为行 20–985 的官方逐字节数据。

### 执行步骤

1. **数据构建（本地）**：下载官方 csv → **文本级转换**（仅改表头：`%UNWEIGHTED ILI`→`% UNWEIGHTED ILI` 加空格、前插 `epiweek` 列 = 本地 raw 行 20–985 的 epiweek；数据行逐行前插 epiweek 值，**7 列数值字符串逐字节不变**）→ 校验：行数 966、pandas 双读 7 列数值完全相等、epiweek 首=200240 末=202113、split 边界（代码动态计算）train[0,676) val[676,772) **test[772,966) ≈ epiweek 201737→202113**（含 2020 春 COVID 峰 111,361；不含 2021 反弹峰 202152）。官方原始下载留存于 `hpc_results/paper_exact/` 作证据。
2. **HPC 隔离终跑**：新建 `/home/sychan552/scratch/CHATTIME/Chattime_paper_exact/`（scripts 从主目录 HPC 侧 `cp`，不重新上传），上传转换后数据 → 提交单个 SLURM 作业：`python scripts/train_miflu.py --reps 10 --epochs 20 --batch 16 --seed 42`（与 8-17 论文协议命令逐字相同，不传 `--horizon` 即全量 L∈{24,36,48,60}）→ 训练后循环调用 `make_miflu_evaluation_figure.py --pred_csv ... --L {L}` 出图。
3. **回收与对照**：`grep 'DONE'` 提取各 L × 10 reps 全通道指标（**论文可比口径 = test_mse(All)/test_mae(All)**，全 7 通道、StandardScaler 空间、stride-1 不聚合；MSE_ILI/PCC 仅作参考）；scp 回收结果 CSV、4 个 7 列预测 CSV、图、日志到本地 `hpc_results/paper_exact/`。
4. **结论报告**：`REPLICATION_VERDICT.md`，含 Table V 三方对照表（论文精确终跑 vs 论文原值 vs 全量 1025 行）、OT 定义与一致性说明、复现状态清单、通俗现状总结。

### 关键决策与理由

- **文本级转换而非 pandas 重写**：杜绝浮点再序列化改写字符串，保证“逐字节”承诺可验证。
- **单作业全量而非 4 作业**：4 档 × ~26–29 分钟 ≈ 110–120 分钟，4h 上限内余量充足；且规避同节点多作业并发（2026-08-06 NaN 事故）。回退方案：若意外超时被杀，按日志/CSV 判断已完成档，逐 L 补交。
- **不触发协议变更规则**：主协议（Phase-1 全量数据）与主目录产物**零改动**，本次为隔离对照实验（同 control966 模式），不要求三处文档同步；最终以哪套作为“主复现结果”留给用户决定。

## 实施注意事项

- 主目录零写入：作业前后 `ls -la` 时间戳比对（control966 已两度验证该隔离模式安全）。
- Windows→HPC 陷阱：scp 多远程文件用通配符；上传 `.sh` 后 `sed -i 's/\r$//'`；ssh 轮询 sleep ≤240s（长 sleep 会被本地超时杀掉）。
- 指标口径防错：与论文比较只用全通道 `(All)` 数字；勿用 MSE_ILI（会重复之前 3–5× 的高估错误）。
- 预期结果锚点：control966（错位窗口）已得 L=24 MSE_All=1.379±0.223（论文 1.542 的 0.89×）；论文精确版预期落在同量级，最终以实跑为准。

## 目录结构

```
本地 MLFlu/
├── scripts/
│   └── _tmp_paper_exact_convert.py          # [NEW·临时] 官方 csv 文本级转换+校验（用后删）
├── hpc_results/
│   └── paper_exact/                          # [NEW] 终跑产物与证据目录
│       ├── tslib_national_illness_official.csv   # [NEW] 官方原始下载（字节级证据留存）
│       ├── results_miflu_paper_protocol_*.csv    # [回收] 10-rep 原始/汇总结果
│       ├── predictions_miflu_L{24,36,48,60}_paper_protocol.csv  # [回收] 7 列预测明细（含 _phys）
│       ├── fig_miflu_eval_*_L{24,36,48,60}.png   # [回收] 物理尺度评估图
│       ├── training_miflu_log_*.txt               # [回收] 训练日志（指标提取源）
│       └── REPLICATION_VERDICT.md                 # [NEW] 复现结论报告（核心交付物）

HPC /home/sychan552/scratch/CHATTIME/
├── Chattime_paper_exact/                     # [NEW] 隔离运行目录
│   ├── scripts/
│   │   ├── train_miflu.py                    # [COPY·HPC侧] 主目录 2026-08-28 版（含 _phys 导出）
│   │   ├── miflu_model.py / textual_embedder.py            # [COPY·HPC侧] 同上
│   │   ├── make_miflu_evaluation_figure.py   # [COPY·HPC侧] 训练后出图
│   │   └── submit_paper_exact.sh              # [NEW] SLURM 作业（全量扫描 + 逐 L 出图）
│   ├── data/raw/national_illness_raw.csv     # [NEW] 转换后官方数据（966 行，数值零改动）
│   ├── logs/ · checkpoints/ · results/ili/figures/
└── Chattime/                                 # 主目录：本次零写入（时间戳核验）
```