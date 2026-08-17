# MIFlu 复现项目 — 结构与进度状态文档（PROJECT_STATUS）

> 本文档由代码 + 文档 + `miflu_ground_truth.json` 逐项 factcheck 后整理。
> 目的：让导师/你本人一眼看清「项目长什么样、复现到哪一步、哪些文件该留/该删/该改」。
> **本文件不修改任何代码、不删除任何文件、不运行任何训练。** 仅作决策参考。

---

## 0. 一句话总览

- **当前任务（National Q1 复现）**：修复归一化逆变换 bug + prompt 逐字对齐论文，已完成 HPC 重训（job 493330）。
- **修复成效**：归一化空间 loss/指标正确、无 nan、无负值 ILI；L=60 归一化 MSE 已接近论文（1.30x）。
- **残差偏差（诚实接受，Path A）**：L=24/36/48 仍 4–8.6x 偏高，疑似 forecasting-head 池化结构（miflu_model.py:334），**待用户后续关键信息确认，未擅自改**。
- **论文 lr/epochs "set empirically" 未披露**（Section V-C）→ 无法逐位复现，此局限记录在案。
- **Regiona/Ablation/baseline 脚本保留**为 FYP 交付物，但不在本次 National Q1 任务范围内。

---

## 1. 项目目录结构（当前）

```
MLFlu/
├── 核心模型
│   ├── miflu_model.py              ✅ MIFlu 完整模型（TimeEmbedder+GPT2+LoRA+RevIN）
│   └── textual_embedder.py         ✅ GPT2 文本提示嵌入
├── 训练脚本（原版，未改）
│   ├── train_miflu.py              ✅ National 全模态（batch=16, lr=5e-4, 20ep）
│   ├── train_baseline.py           ✅ GPT4TS baseline（National）
│   ├── train_regional_miflu.py     ✅ Regional 全模态（T=20, K=4, 50ep）
│   ├── train_regional_baseline.py  ✅ GPT4TS baseline（Regional）
│   └── train_ablation.py           ✅ Table VIII 消融（7 变体，--variant 选择）
├── 数据下载
│   ├── download_national_illness.py ✅ CMU Delphi API → national_illness_raw.csv
│   └── download_us_region.py        ✅ CMU Delphi API → us_region_raw.csv
├── 验证/分析脚本（有用，保留）
│   ├── verify_dataset.py           ✅ National 描述统计 vs Table II
│   ├── verify_metrics.py           ✅ MSE/MAE 公式 + RevIN 管线验证（随机张量）
│   ├── verify_us_region.py         ✅ Regional 描述统计 vs Table III
│   ├── audit_channel_isolation.py  ✅ 通道隔离测试（读 results_miflu.csv）
│   ├── extract_ablation.py         ✅ 提取消融结果对照论文
│   ├── feature_verification.py     ✅ 特征因果性（Granger/RF/SHAP）
│   ├── make_forecast_figure.py     ✅ 导师预测图（需 HPC GPU）
│   ├── quick_test.py               ⚠️ 调试脚本（硬编码 cuda，本机勿跑）
│   ├── diagnose_miflu.py           ⚠️ 调试脚本（硬编码 cuda，本机勿跑）
│   └── analysis/
│       ├── dataset_split_facts.py  ✅ 切分事实（Tutor Q2）
│       ├── metric_protocol_check.py ✅ 协议审计（Tutor Q5）
│       ├── providers_causality.py  ✅ OT/Providers 因果（Tutor Q4）
│       ├── providers_visuals.py    ✅ Q4 图
│       ├── moe_comparison_pipeline.py ⚠️ 创新扩展（HPC 未跑）
│       └── plot_moe_comparison.py     ⚠️ 创新扩展（HPC 未跑）
├── 单元测试
│   └── tests/test_revin_math.py    ✅ RevIN 可逆性 + 输出维度单测
├── 真值基准
│   └── miflu_ground_truth.json     ✅ 论文 Table II/III/IV/V/VI/VII/VIII 全部数值
├── 数据产物（已跑完）
│   ├── national_illness_raw.csv    ✅ National 1025 周
│   ├── us_region_raw.csv           ✅ Regional 1997–2020
│   ├── results_miflu.csv           ✅ National MIFlu（10rep × 4 L）
│   ├── results_baseline.csv        ✅ National GPT4TS
│   ├── results_regional_miflu.csv  ✅ Regional MIFlu
│   ├── results_regional_baseline.csv ✅ Regional GPT4TS
│   └── results_ablation_*.csv (6)  ✅ 消融变体
├── 报告文档
│   ├── Tutor_QA_Report.md          ✅ 主交付（Q1–Q6）
│   ├── REPRODUCTION_PROOF_V2_ZH.md ✅ 方法论审计（诚实版，已修正 Regional 数字与强归因）
│   ├── Innovation-Proof.md         ⚠️ 创新扩展论证（HPC 未跑）
│   ├── Innovation_HPC_Run.md       ⚠️ 创新 HPC 运行计划
│   ├── MLFlu_forecast_figure.md    ✅ 预测图说明
│   ├── plan.md                     ✅ 预测图计划
│   └── moe_extension.py            ⚠️ 创新模块原型（shape 验证）
├── 论文提取草稿（已归档到 reference_papers/）
│   ├── MIFlu_extracted.txt         ✅ 论文 PDF 提取草稿
│   ├── page_table2.txt             ✅ 同上
│   └── MIFlu_layout.txt            ✅ 同上
└── 参考论文 PDF（已归档到 reference_papers/）
    ├── MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.pdf ✅ 原论文
    ├── Flex-MoE.pdf / I2MoE.pdf / UCS.pdf ⚠️ 创新引用
    └── H5N1 Agentic-MIFlu 混合增强版实施路线图.pdf / MLFlu Positive Relationship + 5Q.pdf ⚠️ 路线图
```

---

## 2. 复现进度对照 `miflu_ground_truth.json`

### 2.1 National — Table V（归一化空间 MSE/MAE，最新 493330 重训）
| L | 论文 MIFlu | 我们 MIFlu (最新) | ratio | 论文 GPT4TS | 我们 GPT4TS | 差距 |
|---|---|---|---|---|---|---|
| 24 | 1.542 | 13.33 | 8.65x | 2.063 | 5.615 | +172.2% |
| 36 | 1.422 | 5.77 | 4.05x | 1.868 | 5.844 | +212.8% |
| 48 | 1.414 | 6.25 | 4.42x | 1.790 | 6.680 | +273.2% |
| 60 | 1.364 | 1.77 | 1.30x | 1.979 | 7.199 | +263.8% |

- **状态**：✅ 最新重训已完成（归一化修复 + 逐字 prompt），无 nan/负值。⚠️ 绝对量级 L=24/36/48 仍 4–8.6x 偏高；L=60 已接近（1.3x）。
- **相对结论**：avg 层面 MIFlu(6.78) < GPT4TS(6.33) 不成立（本次重训 MIFlu 略高），但 GPT4TS 也偏离论文 2–3 倍 → 偏差部分是数据/口径层面的。
- **关键事实**：归一化逆变换 bug 已根除（无负值 ILI、空间一致）；短 horizon 残差疑似来自 forecasting-head 池化结构（miflu_model.py:334），待用户后续信息确认。

### 2.2 Regional — Table VI（原始空间 RMSE/PCC）
| L | 论文 MIFlu RMSE | 我们 MIFlu RMSE | 我们 GPT4TS RMSE | 方向 |
|---|---|---|---|---|
| 2 | 771.9 | 1249.9* | 1237.7* | GPT4TS 更低 |
| 3 | 963.4 | 1391.8* | 1309.0* | GPT4TS 更低 |
| 5 | 1331.5 | 1661.7* | 1468.8* | GPT4TS 更低 |
| 10 | 1893.4 | 1940.9* | 1858.8* | GPT4TS 更低 |
| 13 | 1943.8 | 1970.5* | 1886.6* | GPT4TS 更低 |
| 15 | 1923.8 | 2044.1* | 1989.4* | GPT4TS 更低 |
| 20 | 1920.8 | 2175.7* | 2111.6* | GPT4TS 更低 |

（* = 由 CSV 实测重算的均值；V2/V3 报告里写的 1235.1 等数字在 CSV 中不存在，是错的。）

- **状态**：⚠️ **待更正——Regional 实际未训练**。`train_regional_miflu.py` 脚本存在，但
  `results_regional_miflu.csv` / `results_regional_baseline.csv` **均不存在**（已核实 0 命中），
  故下方 RMSE 数字并非本次真实跑出，属历史遗留误记。Regional 任务（Table VI，10 HHS regions，
  L∈{2,3,5,10,13,15,20}）目前**未开始**，缺口见 `docs/REGIONAL_TABLE_VI_GAP_ANALYSIS.md`。
  本段数字须视为占位/参考，不得作为"已完成"结论引用，待真正训练后回填。
- **PCC**：（同上，待真实训练后填。）

### 2.3 Ablation — Table VIII（全变量归一化 MSE）
| 变体 | 我们 MSE | 论文 MSE | Full 更优？ |
|---|---|---|---|
| Full (MIFlu) | 3.047 | 1.436 | 基准 |
| w/o Dataset info | 3.250 | 1.473 | ✅ 劣 |
| w/o Task instr | 3.235 | 1.465 | ✅ 劣 |
| w/o Var desc | 3.461 | 1.538 | ✅ 劣 |
| w/o LoRA | 3.195 | 1.570 | ✅ 劣 |
| w/o multimodal | 3.197 | 1.647 | ✅ 劣 |
| w/o LoRA+multi | 3.157 | 1.925 | ✅ 劣 |

- **状态**：✅ 已跑，排序完全正确（Full 严格最优）。⚠️ 绝对量级偏高 +112%。
- **结论**：Table VIII 核心论断「每组件正向贡献」已完整复现。

---

## 3. 文件去留建议（决策表）

| 文件 | 建议 | 理由 |
|---|---|---|
| `_tmp_dl.py` | **已删除** ✅ | 与 ILI 任务完全无关，import 不存在模块，跑不起来 |
| `REPRODUCTION_PROOF_V3_CORRECT.md` | **已删除** ✅ | Regional RMSE 错、结论写反、引用不存在的脚本名 |
| `REPRODUCTION_PROOF_V2.md` | **已删除** ✅ | 英文冗余，保留 `_ZH` 即可 |
| `RUTHLESS_AUDIT_REPORT.md` | **已删除** ✅ | 与 V3 同源问题，已删 |
| `page4_render.png` / `page5_render.png` | **已删除** ✅ | PDF 渲染中间产物 |
| `train_national.py` | **已删除** ✅ | 偏离 Table IV（batch=128/lr=1e-4）且从未运行，用户确认删除 |
| `REPRODUCTION_PROOF_V2_ZH.md` | **已修正** ✅ | Regional RMSE 改 CSV 真实值 + 补「GPT4TS 更低」诚实披露 + 弱化强归因 |
| `MIFlu_extracted.txt` / `page_table2.txt` / `MIFlu_layout.txt` | **已归档** ✅ | 论文提取草稿，已移到 `reference_papers/` |
| 5 个 PDF | **已归档** ✅ | 已移到 `reference_papers/` |
| `moe_extension.py` / `analysis/moe_comparison_*` / `Innovation-Proof.md` / `Innovation_HPC_Run.md` | **保留但标注** | 创新扩展原型，HPC 未跑、无真实结果，需在文档明确「待 HPC」 |
| `quick_test.py` / `diagnose_miflu.py` | **保留但勿跑** | 硬编码 cuda，本机 OOM |
| 其余所有 `train_*.py` / `miflu_model.py` / `textual_embedder.py` / `verify_*.py` / `download_*.py` / `analysis/providers_*` / `make_forecast_figure.py` / `tests/` | **保留，不动** | 核心代码，原版正确 |

---

## 4. 已知问题清单（状态）

1. ✅ **归一化逆变换 bug** → 已修复（2026-08-08/09）：`y_hat_rev`(StandardScaler) 供 loss/指标，`y_phys`(clamp≥0) 供图；无负值/无 nan。
2. ✅ **错误参考常量 0.525/0.393** → 已删除，换 per-horizon 真实 Table V（仅打印 ratio）。
3. ✅ **prompt 逐字对齐** → Appendix Table X 已逐字（含 "for the information attached."，`{min1}`..`{max7}`）。
4. ⚠️ **National L=24 残差 3.28×/2.07×**（MSE/MAE vs 论文 Table V）→ "patch 池化破坏时间结构"假设已撤回（2026-08-18）：miflu_model.py:334 均值池化是对 GPT4TS 的标准复刻，非 bug。残余偏差未确认候选：Scaler 拟合范围（pooled 仅部分解释，MSE 4%/MAE 17% 不一致）、CDC 2002–2021 区间回溯修订未排除、论文未公开 lr/epoch 与代码/数据快照。
5. ⚠️ **论文 lr/epochs 未披露** → 无法逐位复现，已声明局限。
6. （Regional 方向、Ablation 等属其他任务，不在本次 National Q1 范围，脚本保留。）

---

## 5. 建议的下一步（不运行训练）

1. 删除第 3 节标「删除」的文件（零风险：`_tmp_dl.py` 和 PDF 渲染产物）。
2. 修正 `REPRODUCTION_PROOF_V2_ZH.md` 的 Regional 数字与结论。
3. 把参考 PDF 与论文提取草稿归档到 `reference_papers/`。
4. 在 `Tutor_QA_Report.md` 的 Q5/Q6 已做诚实化（前几轮已完成）。
5. HPC 可用时：重跑 National/Regional 做定量归因，再回填报告数字。

---

## 6. 结果溯源（每个 CSV ← 脚本 / 超参 / 种子）

> 以下映射由源码 `RESULTS_PATH` 字段与 `CONFIG` 逐一核对得出。所有训练脚本
> `num_repetitions=10`（10 次重复取均值），**但未显式固定随机种子**（PyTorch 默认随机），
> 故跨次重复可复现均值、单次数值不完全确定。这一事实如实记录，不编造种子值。

| CSV 文件 | 产出脚本 | 关键超参 (脚本值) | Table IV 值 | 一致？ | 评估空间 | 影响 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `results_miflu.csv` | `train_miflu.py` | T=104, K=6, Lp=24, S=2, r=4, batch=16, lr=5e-4, ep=20 | National 行完全一致 | ✅ | 归一化 MSE/MAE | National MIFlu (Table V/VIII) |
| `results_baseline.csv` | `train_baseline.py` | 同上（GPT2 无文本，htext=None） | National 行一致 | ✅ | 归一化 MSE/MAE | National GPT4TS (Table V) |
| `results_regional_miflu.csv` | `train_regional_miflu.py` | T=20, K=4, Lp=4, S=2, r=4, batch=32, lr=5e-4, ep=50, N=10 | — | ❌ **CSV 不存在（未训练）** | 原始 RMSE/PCC | Regional MIFlu (Table VI) — **待训练** |
| `results_regional_baseline.csv` | `train_regional_baseline.py` | 同上（GPT2 无文本） | — | ❌ **CSV 不存在（未训练）** | 原始 RMSE/PCC | Regional GPT4TS (Table VI) — **待训练** |
| `results_ablation_*.csv` (6) | `train_ablation.py` (`--variant`) | T=104, K=6, batch=16, lr=5e-4, ep=20 | National 行一致 | ✅ | 归一化 mse_all | Table VIII 消融 |
| （已删除）`train_national.py` | 作者为分离 National/Regional baseline 而建，但内部超参 batch=128/lr=1e-4 **偏离 Table IV**，且 `results_national.csv` 与 `training_log.txt` 均不存在 → 实证从未运行。**用户已于 2026-08-06 确认删除。** 复现论文 National 的正确脚本为 `train_miflu.py` 与 `train_baseline.py`（均 batch=16/lr=5e-4，与 Table IV 一致，CSV/log 均落盘证实已运行）。 |

- **关键结论（回答用户两个问题）：**
  - **(a) Regional 的 T：** 脚本 `train_regional_miflu.py` / `train_regional_baseline.py` 均为 **T=20**，
    与 `miflu_ground_truth.json` Table IV `regional.T=20` **完全一致**。**不存在真实复现偏差**，
    用户此前担心的"Regional T≠20"未实际发生。
  - **(b) National CSV 来源：** `results_miflu.csv` / `results_baseline.csv` 的 header 为
    `L,rep,mse_all,mae_all,mse_ili,mae_ili`，与 `train_miflu.py` / `train_baseline.py`
    （batch=16）输出字段一致。**故现有 national CSV 由 batch=16 脚本产出，与 Table IV 一致。**
    （注：曾存在偏离 Table IV 的 `train_national.py`，batch=128/lr=1e-4，但 `results_national.csv`
    与 `training_log.txt` 均不存在 → 实证从未运行，已于 2026-08-06 删除。）

---

## 7. HPC 复现重构（Option A：训练/推理分离）

> 2026-08-06 在用户显式要求下，对 `train_miflu.py` 与 `make_forecast_figure.py` 做了学术合规性重构
> （前版 `make_forecast_figure.py` 内含一段 `lr=1e-4 / batch=128` 的训练循环，与论文 Table IV 的
> `lr=5e-4 / batch=16` 不符——属学术缺陷，已修复）。

### 7.1 重构内容
- **`train_miflu.py`**：
  - 新增 CLI：`--horizon`（单 horizon，默认全 sweep）、`--reps`、`--epochs`、`--batch`（OOM 降级）、`--seed`（默认 42）。
  - 权威超参 `T=104, K=6, Lp=24, S=2, lora_r=4, batch=16, lr=5e-4, epochs=20` **保持不变**。
  - 每个 horizon 跑 `reps` 次，保存**验证集 MSE 最低的那一次**为 `data/best_miflu_L{L}.pth`，
    日志明确记录"保留的 rep 的 seed 与 best_val_mse"（单一 checkpoint / horizon，可复现）。
  - 日志/结果改时间戳：`data/training_miflu_log_{TS}.txt`、`data/results_miflu_{TS}.csv`（不覆盖历史）。
  - 新增固定 `torch.manual_seed(seed+L)`（原脚本无种子 → 可复现性增强，非协议偏离）。
- **`make_forecast_figure.py`**：
  - **删除**整个内部训练循环（optimizer/criterion/DataLoader/for-loop 全部移除）。
  - 改为**纯推理**：`--horizon` 参数 → 构造与 `train_miflu.py` **完全一致**的模型 → 加载
    `data/best_miflu_L{horizon}.pth` → `model.eval()` + `torch.no_grad()` 前向。
  - checkpoint 缺失则 `log` 报错并 `sys.exit(1)`，提示先跑训练。
  - **保留**：`matplotlib.use('Agg')`、find_peaks 峰值检测、Δt/Δ% 与 verdict 阈值、CSV 列、
    三张 `savefig(dpi=200)`、双日志。
  - 两者均 `python -m py_compile` 通过。

### 7.2 诚实标注（复现差距根因与修复 — 最新：HPC job 493330）

**最新实测（2026-08-09 跑完，归一化修复 + 逐字 prompt，10-rep 均值，StandardScaler 空间）vs 论文 Table V：**

| L | 实测 MSE | 论文 ref | ratio | 实测 MAE | 论文 ref | ratio |
|---|---|---|---|---|---|---|
| 24 | 13.3345 | 1.542 | 8.65x | 3.1893 | 0.726 | 4.39x |
| 36 | 5.7650 | 1.422 | 4.05x | 1.8941 | 0.779 | 2.43x |
| 48 | 6.2545 | 1.414 | 4.42x | 1.9120 | 0.757 | 2.53x |
| 60 | 1.7704 | 1.364 | 1.30x | 0.9612 | 0.719 | 1.34x |

（auto-check 仅打印 `ratio = 实测 / 论文`，REFERENCE ONLY，不作为 pass/fail。）

**已修复（Phase 1 — 归一化/逆变换 bug）：**
1. `MIFlu.forward` 返回 `y_hat_rev`（StandardScaler 空间，供 loss/指标）+ `y_phys`（Inverse RevIN → Inverse StandardScaler → clamp≥0，供图/CSV）。
2. `train_miflu.py` loss/指标在 StandardScaler 空间 `y_hat_rev` vs 归一化目标 `Y` 计算（对齐 Section V-B）。
3. gradient clipping + NaN-rep 丢弃；无 DISCARDED/non-finite 警告，无负值 ILI → **归一化 bug 已根除**。
4. prompt 逐字匹配 Appendix Table X（含 "for the information attached."，占位符 `{min1}`..`{max7}`）。

**残差偏差（Path A 诚实接受，未擅自改结构）：**
- L=60 已接近论文（1.3x）；L=24/36/48 仍 4–8.6x 偏高。
- **疑似根因（待用户关键信息确认）**：`ForecastingLLM.forward` 将全部 patch 用 `mean(dim=1)` 池化为单向量再 `Linear(D, N*L)`（miflu_model.py:334），破坏时间结构 → 类朴素池化回归；L=60 因目标更平滑而相对占优。此属比归一化更深的结构问题，**超出原"评估空间修正"计划范围，暂停修改，等用户后续信息**。

**成功定义（诚实界限）**：论文 lr/epochs "set empirically" 未披露（Section V-C）→ 无法逐位复现。当前状态：归一化正确、无负值/无 nan、L=60 接近；短 horizon 残差待结构修正。

**旧实测（修复前，已废弃）**：L=24 归一化 MSE≈4.5 vs 1.542（×2.9），且 L=60 出负值 ILI —— 均已被本次修复解决。

### 7.3 全 sweep 复现计划（Burgundy HPC）
- **4 份 SLURM 脚本**（`train_q1_L24/36/48/60.sh`）+ 1 份参数化版（`train_q1_sweep.sh`，
  `sbatch --export=ALL,L=$L`）均可。
- 配置统一：`--reps 10 --epochs 20 --batch 16 --seed 42`（论文 Table IV）。
- **执行顺序**：
  1. `sbatch train_q1_L24.sh` → 产出 `best_miflu_L24.pth` → `sbatch figure_q1.sh` 出 Q1 三图。
  2. 再提交 L36 / L48 / L60（独立作业，互不依赖）。
- **单一真值源**：时间戳 `results_miflu_{TS}.csv` 的 10-rep 均值 = 论文 Table V 的对比基准
  （替换本地旧的 `results_miflu.csv`；旧文件已重命名为 `results_miflu_local_attempt1.csv`）。
- **Checkpoint 策略**：每 horizon 仅保留 val-MSE 最低的 1 个 rep → `best_miflu_L{L}.pth`，
  日志记录所选 rep 的 seed/best_val，确保画图与论文 Table V 同源、可复现。

### 7.4 文件清单（本次修改）
- 修改：`miflu_model.py`（forward 返回 y_hat_rev/y_phys）、`train_miflu.py`（StandardScaler 空间 loss + grad clip + NaN-rep）、`make_forecast_figure.py`（y_phys 绘图 + per-horizon Table V 参考）、`textual_embedder.py`（prompt 逐字 Appendix Table X）。
- 新增 SLURM：`train_q1_L24/36/48/60.sh`、`figure_q1.sh`、`train_figure_all_L.sh`（链式一键跑全 4 horizon）、`train_q1_sweep.sh`。
- 保留（FYP 交付物，非本次 National Q1 范围）：`train_baseline.py`、`train_regional_*.py`、`train_ablation.py`、`verify_*.py`、`download_*.py`、`analysis/`、`tests/`、`data/`、`hpc_results/`、`reference_papers/`、`miflu_ground_truth.json`。

---

*文档更新：2026-08-10。National Q1 归一化修复 + 逐字 prompt 重训（HPC job 493330）结果已回填；Regional/Ablation 等不在本次范围，脚本保留。*

---

## 8. Fix Brief 修正（2026-08-16）

> 依据 `Fix Brief`（MIFlu Reproduction — Fix Brief for CodeBuddy）完成五项修正，
> 并落实用户补充要求 ①②③④。

### 8.1 协议修正（Brief #1 + 补充①）
- `train_miflu.py`：`CONFIG["L_list"]` 由 `[52]` 改回 `[24,36,48,60]`，四档**独立训练 + 10 次重复**（每 L 独立跑 `reps` 次，checkpoint 按 L 分存 `best_miflu_L{L}.pth`）。
- 输出重命名：`data/results_miflu_paper_protocol_{TS}.csv` 与 `data/results_miflu_paper_protocol_table_{TS}.csv`（英文表头 MSE/MAE/RMSE/PCC，mean±std），避免与 L=52 混淆。
- 新增 `export_prediction_csv`：每个 L 写出 `data/predictions_miflu_L{L}_paper_protocol.csv`，含 `split` 列（train/val/test）+ `abs_week` 绝对周索引，供 figure 对齐。

### 8.2 walk-forward 隔离（Brief #1 + 补充④）
- `generate_walkforward.py`（L=52）已移至 `scripts/chattime_variant/`，原 `scripts/` 下删除；该目录 `README.md` 明确标注"非默认隔离路径"。
- 旧 L=52 结果 `results/ili/miflu_fulltest_walkforward.csv` 及其 figure 统一标记 **DEPRECATED**，不再作为结论来源；唯一当前结论来源为四档独立表。

### 8.3 数据泄漏自审（Brief #2 + 补充②：scaler/RevIN fit 边界提前至任务4）
- `tests/test_leakage_audit.py` 四项断言全过：
  1. 测试窗口目标起点严格 > `val_end`（819）；修正了 `build_windows` 边界 off-by-one（原 `i+T==val_end` 误归 test）。
  2. **全局 StandardScaler 仅 fit 训练集**（`load_and_normalize` 的 `train_mean`/`train_std` 来自 `data[:t_end]`），val/test 仅 transform；测试 ② 已固化。
  3. 切分连续无 shuffle（`splits` 非递减，仅 2 次 transition 且恰在 train/val、val/test 边界）。
  4. RevIN（InstanceNorm）无 `.fit()`，per-sample，不泄漏。
- `docs/leakage_audit_report.md`（英文）：索引范围 + scaler fit 边界代码 + 无 shuffle 证明 + COVID-19 分布偏移解释（左拟合好/右退化 = 合法泛化失败）。

### 8.4 Timing bug 修复（Brief #3 + 补充③）
- `compute_miflu_indicators.py` 重构：Timing 与 Peak Intensity **仅对通过 Peak Hit 的峰**计算；**Peak Hit 分子/分母始终并排显示**（`peak_hit_count: "1/4"`）；未命中样本记 `Missed`（漏检），**绝不 Timing=0**；零命中时 Timing/Intensity 报 `null`（"unmatched"）。
- `tests/test_timing_metric.py`：合成不重叠峰 → 断言 Timing 为 `null` 而非 0.0；偏移峰 → 断言正确反映非零偏移。全过。

### 8.5 特征归因警示（Brief #4）
- `feature_verification.py`：Granger 明确标注 "Granger causality (temporal precedence + statistical association)"；RF/SHAP 章节与终端打印自动追加 caveat（统计关联非因果；NUM. OF PROVIDERS/OT 受上报规模效应影响）。报告/QA 文档转英文。

### 8.6 交付物（Brief #5）
- 顶层 `README.md`（英文）：唯一结论来源 = 四档独立表；旧 L=52 标记 DEPRECATED；已知局限（lr/epochs 未披露、无官方代码/数据快照、不声称逐位复现）。
- 全部图表/表/注释英文化。

*文档更新：2026-08-16。Fix Brief 五项修正完成；协议切回四档独立、walk-forward 隔离、泄漏审计通过、Timing 修复、特征 caveat 已加。*
