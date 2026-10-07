# Stage 5 / A2 结果报告（作者 966 行数据上的修正重构模型控制比较）

生成时间：2026-09-26 00:30 Asia/Hong_Kong（= 2026-09-25 16:30 UTC）。
授权来源：用户本轮明确授权（A2 共 36 次拟合 + 8 条基线 + 统一 Test 评分 + 核验 + 报告；累计上限 2 GPU-hours）。**本报告不代表导师已批准。**

配套产物：`hpc_results/stage5_a2/`（本地）／`/home/sychan552/stage5_a2_durable`（远端持久位置）。
补充表格：`recovery/stage5/results_tables_zh.md`（T1–T7）。执行与资源账本：`recovery/stage5/execution_ledger.md`。

---

## 0. 一句话结论

在作者 966 行数据、按冻结协议完成的受控比较中，**去掉文本通路的 `no-text` 变体在主指标 `average_MSE_4L` 上最好（1.922），修正重构版 MIFlu 次之（2.042），NLinear 几乎与 MIFlu 持平（2.050）**。也就是说，**在本次可核验的实验里，文本通路没有带来可确认的预测收益，反而略微变差**。本轮**没有**执行 A0（作者发布代码逐字重放），因此这不是对论文的严格复现判定，而是一个修正重构后的回顾性受控比较。

---

## 1. 实际完成情况

| 项 | 计划 | 实际 | 状态 |
|---|---:|---:|---|
| 学习模型独立拟合 | 36 | 36 | 全部成功，每 run 有验证选模证据与独立 checkpoint |
| 确定性基线评价 | 8 | 8 | 全部成功 |
| checkpoint 锁定 | 36 | 36 | 全部锁定（SHA-256 + 选模证据） |
| 统一 Test 评分 | 44 | 44 | 全部完成，单一评分代码路径 |
| 从工件独立重算主指标 | 44 | 44 | **PASS**，与评分表最大偏差 `4.44e-16` |
| 失败 / 重试 | — | 4 次失败 + 8 次空跑 + 2 次评分重跑 | 全部定位原因后同配置恢复，无删结果、无换种子 |
| A0 | 1 | 0 | **仍未执行（暂缓）** |
| GPU 消耗 | ≤ 2.0 GPU-h | **1.1536 GPU-h** | 剩余 0.8464 GPU-h |

---

## 2. 冻结协议（本轮实际执行值）

| 项 | 值 |
|---|---|
| 数据 | 作者 966 行快照，`national_illness_raw_paper_exact.csv`，SHA-256 `31ffc169…b87a`（运行时由 `verify_profile_hash()` 逐次校验） |
| 划分 | train / validation / Test = **676 / 97 / 193**，零基半开区间 `[0,676)`、`[676,773)`、`[773,966)` |
| T / L | T = 104；L ∈ {24, 36, 48, 60}，每个 L 独立训练 |
| seeds | 42 / 43 / 44，每 seed 重新初始化模型、优化器、调度器与最佳状态 |
| 窗口归属 | `--containment strict`：目标块 `[o+1, o+L]` 必须**完整**落在所属划分；跨界窗口剔除，不重新归属、不凑数 |
| 窗口数 | L=24 → 549/74/170；36 → 537/62/158；48 → 525/50/146；60 → 513/38/134（与冻结表逐项一致） |
| 缩放 | StandardScaler **仅**在 `train[0:676]` 上拟合，Test 从未参与 |
| 选模 | 每 (model, L, seed) 取**该 run 验证集七变量标准化 MSE 最低**的 epoch；训练全程不读 Test |
| 主指标 | `average_MSE_4L`：每 L 内先对 3 个 seed 求 Test MSE 均值，再对 4 个 L 等权平均；七变量、标准化空间、全部 lead、该 L 的**全部共同有效 Test origins** |
| 超参 | Adam、lr = 5e-4（**无学习率调度**）、wd = 0、betas (0.9, 0.999)、eps 1e-8、batch 16、**固定 20 epoch、无 early stopping**、reps = 1、fp32 |
| 架构 | K=6, Lp=24, S=2, lora_r=4；LoRA 73,728 参数；GPT-2 骨干冻结（仅 LoRA + 变体指定的前 k 层解冻） |

---

## 3. 主结果

### 3.1 主指标 `average_MSE_4L`（七变量标准化 MSE，越低越好）

| 排名 | 模型 | average_MSE_4L | 平均 MAE_4L |
|---:|---|---:|---:|
| 1 | **no-text（w/o multimodality）** | **1.922158** | 0.9352 |
| 2 | MIFlu（修正重构，文本通路开启） | 2.041519 | 0.9485 |
| 3 | NLinear | 2.049550 | 0.9566 |
| 4 | Seasonal Naive（确定性基线） | 2.268799 | 0.9612 |
| 5 | Last Value（确定性基线） | 7.165831 | 1.8172 |

### 3.2 分 L 的七变量标准化 MSE（3 seeds 均值 ± 样本标准差）

| 模型 | L=24 | L=36 | L=48 | L=60 |
|---|---:|---:|---:|---:|
| MIFlu | 2.4439 ± 0.0753 | 1.9360 ± 0.1754 | **1.7677** ± 0.1202 | 2.0184 ± 0.1390 |
| no-text | **1.9796** ± 0.1490 | **1.8268** ± 0.1673 | 1.7901 ± 0.0382 | 2.0921 ± 0.3094 |
| NLinear | 2.1008 ± 0.0374 | 2.0277 ± 0.0261 | 2.0033 ± 0.0292 | **2.0664** ± 0.1364 |
| Seasonal Naive | 2.5638 | 2.2655 | 2.1425 | 2.1035 |
| Last Value | 6.2133 | 7.7138 | 7.8513 | 6.8849 |

### 3.3 逐 (model, L, seed) 的 Test MSE 与选它的验证值

见 `results_tables_zh.md` 表 T2。36 个 run 全部有 `best_val_mse_7var_z`、checkpoint 路径/字节数/mtime/完整 SHA-256（`CHECKPOINT_LOCK.csv`）。

### 3.4 分变量（七变量标准化空间 Test MSE，3 seeds 与 4 个 L 的平均）

| 模型 | WILI | UILI | AGE 0-4 | AGE 5-24 | ILITOTAL | PROVIDERS | OT |
|---|---:|---:|---:|---:|---:|---:|---:|
| MIFlu | 0.9071 | 1.2216 | 3.3760 | 2.8882 | 3.8988 | 0.9330 | 1.0660 |
| no-text | 0.8663 | 1.1669 | 3.1802 | 2.6900 | 3.6089 | 0.8852 | 1.0576 |
| NLinear | 0.8797 | 1.1589 | 3.4018 | 2.9553 | 4.0310 | 0.7892 | 1.1310 |
| Seasonal Naive | 1.1421 | 1.4034 | 3.8435 | 3.1387 | 4.6036 | 0.6910 | 1.0593 |
| Last Value | 4.4589 | 5.3660 | 11.6592 | 10.6995 | 15.4758 | 0.9658 | 1.5355 |

误差最大的两个变量是 **AGE 0-4** 与 **AGE 5-24**（z 空间 MSE 2.7–3.4），远高于 ILI 比例类变量（0.87–1.22）。这也是 `average_MSE_4L` 数值看起来较大的主要原因。

### 3.5 原单位误差（逐变量分别报告，不合并不同单位）

| 模型 | %WEIGHTED ILI | %UNWEIGHTED ILI | AGE 0-4（人次） | AGE 5-24（人次） | ILITOTAL（人次） | PROVIDERS（家） | OT（人次） |
|---|---:|---:|---:|---:|---:|---:|---:|
| MIFlu | 0.748 | 0.815 | 2672 | 4628 | 11584 | 400 | 201740 |
| no-text | 0.737 | 0.809 | 2673 | 4579 | 11409 | 385 | 197392 |
| NLinear | 0.754 | 0.806 | 2678 | 4742 | 11717 | 377 | 215208 |
| Seasonal Naive | 0.779 | 0.802 | 2762 | 4467 | 11947 | 379 | 217869 |
| Last Value | 1.926 | 1.970 | 5436 | 9709 | 25808 | 378 | 221433 |

单位互不相同，**不得**把这些列加总成一个"总误差"。

### 3.6 weighted ILI（通道 0）与 ILITOTAL（通道 4）单独结果

weighted ILI 在 z 空间的 Test MSE 全部落在 0.87–1.22（表 3.4 第 1 列）；ILITOTAL 落在 3.61–4.03。ILITOTAL 的相关系数（`pcc_ili`，通道 4）见 `results_tables_zh.md` 表 T1：三个学习模型在 0.66–0.80 之间，Last Value 在 −0.07–0.11 之间（几乎无相关），Seasonal Naive 在 0.62–0.72 之间。

---

## 4. 结果解读（含不能下的结论）

### 4.1 文本通路（消融）：MIFlu vs no-text

- `no_multi` 变体的冻结定义是 **移除文本嵌入输入**（`use_text=False, use_lora=True, use_text_ln=True, gated_inject=False, unfreeze_first_k=0`），即"去掉整个多模态通路、保留 LoRA"。这是本轮规定的通路消融。
- **按 seed 配对、同一 L 的配对差（`MIFlu − no-text`，正值 = MIFlu 更差）**：平均 **+0.1194**，标准差 0.2748；分 L 为 L24 **+0.4643**、L36 +0.1092、L48 −0.0224、L60 −0.0737。12 个 (L, seed) 格中 MIFlu 更差的只有 7 个 —— **符号在 L 之间翻转**。
- 可以说的：在 `average_MSE_4L` 这个预先指定的报告指标上，no-text 更好（1.922 vs 2.042，相对 +6.2%）；差异主要由 L=24 拉大，长预测步（L=48/60）上两者实际上互有胜负、差距在种子波动量级内。
- **不能说的**：不能宣称"文本通路在统计上确定有害"。配对差的标准差（0.275）与均值（0.119）同量级，只有 3 个 seed，符号在 L 间翻转，**不显著 ≠ 等效**，也不应把"未显著"写成"无差异"。

### 4.2 系统比较：MIFlu vs NLinear

- 配对差平均 **−0.0080**（标准差 0.2640），分 L：L24 +0.3431、L36 −0.0917、L48 −0.2355、L60 −0.0480；12 格中 MIFlu 更好 5 格。
- 结论只能是：**在本协议下 MIFlu 与一个线性基线 NLinear 无法区分**。差距比单个 L 上 3-seed 的标准差小一个数量级。

### 4.3 三个种子的作用

三个 seed 只描述**优化随机性**（初始化、批序、LoRA 噪声），**不是时间泛化不确定性**，也不构成"重复实验"。单个 L 上 3-seed 的 Test MSE 标准差为 0.026–0.309（`results_tables_zh.md` 表 T7）；`notext` 在 L=60 的种子间跨度最大（1.749 – 2.350）。任何模型间差异若小于这个量级，都不应被解读为模型能力差异。

### 4.4 与论文数值的关系（谨慎表述）

论文 Table V 报告的 `MSE_All` 为 1.542 / 1.422 / 1.414 / 1.364（4 个 L），等权平均 **1.4355**。本轮 MIFlu 为 2.4439 / 1.9360 / 1.7677 / 2.0184，等权平均 **2.0415**，约为论文值的 **1.42×**。这明显好于本项目此前在 1025 行论文窗上的 1.7–2.6× 差距（`hpc_results/paper_exact/REPLICATION_VERDICT.md`），改进主要来自本轮的两点：改用作者 966 行快照本身，以及 `strict` 窗口归属（修掉了 L=60 时验证目标越界进入 Test 的实质缺陷）。

**但点估计接近不等于严格复现。** 本轮是**修正重构**（不是作者发布代码的逐字重放，A0 未执行），seeds 只有 3 个而论文用 10 reps，且本轮 Test 是回顾性暴露的旧 Test。因此**不得**据此宣称已复现论文，也不得宣称已推翻论文。

---

## 5. Test 隔离与协议执行情况

- 全部 36 个学习模型拟合在 `DEFER_TEST=1` 下运行：训练末尾的 Test 评价与预测导出被显式跳过，日志逐 run 可见 `DEFER_TEST=1 - Test NOT evaluated`。
- checkpoint 锁定文件 `CHECKPOINT_LOCK.json` 写于 **2026-09-25T16:13:29Z**，记录 36/36 个拟合的完整 SHA-256 与选模证据；**任何 Test 推理都在此之后**（同一作业内严格先后：step 1 锁定 → step 2 推理 → step 3 重算），且第一次锁定的副本另存为 `CHECKPOINT_LOCK_first_20260925T161329Z.json`。
- 统一评分由单一入口 `scripts/score_test_stage5.py` 完成，36 个 checkpoint + 8 条基线走同一套指标代码。
- 独立重算：`scripts/recompute_from_artifacts.py` **不导入任何训练/评分模型代码**，只读预测 NPZ、Test origin 清单与训练集 scaler，从零重算主指标，并逐格与评分表比对（最大偏差 `4.44e-16`），同时强制检查 44 个工件齐备、每个 Test 目标块完整落在 `[773, 966)`、每个 L 的 Test origin 数等于冻结值。该脚本已用合成数据做过正/负向自测（`recovery/stage5/_selftest_recompute.py`，故意篡改一个预测后正确报错退出）。
- **工件可重算性**：每个 (model, L, seed) 一个 NPZ，含 `pred`、`target`（标准化空间）、`target_start_row`、`L`、`seed`、`var_cols`、`train_mean`、`train_std`、`profile`、`containment`、`space`；另有 `test_manifest.csv`（6688 行，逐 origin 记录 origin 行号、目标首末行、origin/首/末目标的 epiweek 与 release_date、lead 数）与 `scaler_train_only.json`。

### 5.1 协议偏离与异常（完整披露，不隐藏）
1. **窗口归属规则被修正（D-windows）**。三个运行器原本按"目标起点"归属划分，与目标长度无关；L=60 时训练目标会进入验证段、**验证目标会进入 Test 段**，而验证 MSE 正是选 checkpoint 的依据 —— 这构成实质 contamination。本轮新增 `--containment strict` 并全程使用，旧行为保留为默认值以便旧结果可比。这是本轮最重要的协议修正。
2. **基线 Test 数值的产生时序与协议字面顺序不同**。8 条基线的 Test 指标在 job 585836（2026-09-25 15:19 UTC）产生，**早于** no-text seed 43/44 的拟合（15:30–15:32 UTC），因此不满足"36 个 checkpoint 全部锁定后才统一评价 8 条基线"的字面顺序。但是：当时已锁定的 24 个学习拟合全部是纯验证选模，且**系统内不存在任何学习模型的 Test 数值**（全部 `DEFER_TEST=1`），所以基线 Test 数值在事实上不可能影响任何选择。统一评分作业 585883 在完整锁定之后**从零重算了全部 8 条基线**，数值与 585836 逐位相同，因此**报告中采用的基线数值出自完整锁定之后**。
3. **no-text 的 8 个拟合是接管后补做的**。上一轮中 4 个 L 的 seed 42 训练成功但因 `DEFER_TEST` 下对 `None` 求均值触发 `TypeError` 而退出 1；随后的 4 个作业显示 COMPLETED 却是**空跑** —— resume 判据以 `(L, rep)` 为键且读取了本运行器从不写入的列 `test_mse_all`，在 `DEFER_TEST=1` 下把每个已有行都判为"已完成"，seed 43/44 被静默跳过。修复后（判据改为 `(L, rep, seed)` + 对应 per-seed checkpoint 是否存在）只补做了缺失的 8 个拟合（jobs 585865/585874/585875/585876），**seed 42 原样复用**（同一 checkpoint、同一 SHA-256），其余 28 个已完成拟合一个都没有重跑。
4. **评分作业 585878 失败**。checkpoint 锁定已成功，随后 `predict_nlinear` 抛 `AttributeError: 'NLinear' object has no attribute 'device'`（NLinear 是裸 `nn.Linear` 子类，没有 `.device`；MIFlu 有）。最小修复（显式传入 device）后以 585883 重跑，**指标代码路径未变**。
5. **被同配置重跑取代的作业**。miflu L=24 / L=36 曾由 585555 / 585581 完成，随后由 585794 / 585798 以完全相同配置重跑（前一 dispatcher 中断后重启），导出文件被后一次覆盖。只有后一次的工件进入报告与锁定清单。相关成本已全额计入预算。
6. **`best_epoch` 证据缺口**。MIFlu 的每个 run 有完整逐 epoch 日志，`best_epoch` 可查。NLinear 只在 `metrics.csv` 记录 `best_val`，从不记录 `best_epoch`。no-text 的逐 epoch 轨迹写在 `horizon_L*/rep_01/metrics.csv`，但每个 seed 会覆盖前一个 seed，且作业封装用 `tail -40` 截断了每个 seed 的输出（20 个 epoch 只剩 3 行），因此 **notext 与 nlinear 的 `best_epoch` 未能留证**。选模型真正使用的量是 `best_val`，它对 36 个 run 全部齐备并已锁定；缺口只在辅助信息，不影响结论。曾尝试从 stdout 恢复，但因上述截断会错误归属 seed，已**丢弃**该结果而不发布。
7. **A0 未执行**。作者发布代码（`main_ILI_lora.py`）的逐字重放本轮仍为 `BLOCKED`，见 `a0_diagnostic_record.csv`。
8. **本轮不是新的独立泛化 Test**。作者 Test 早已暴露，本轮只做协议冻结后的回顾性评价；没有任何另行封存的新 holdout 被打开。
9. **未运行任何本地登录节点计算**。登录节点只做 `sbatch` 提交、`squeue`/`sacct` 轮询与小文件读取。

## 5.2 2026-09-26 补充：外部证据如何改变本报告的解读

本报告的 A2 数值本身未变，但以下两条**已执行**的外部证据改变了对它的解读，必须一并阅读。

### (a) A0 证明：作者发布代码的文本通路输出恒等为零

A0 的 CPU 可执行诊断（job 587002，0 GPU-hours，`recovery/a0/`）在作者发布代码上实测得到：

| 检验 | 结果 |
|---|---|
| 真实文本 vs 打乱文本的输出最大差异 | **恰为 `0.000e+00`** |
| 损失对文本嵌入的梯度范数 | **恰为 `0.000e+00`** |
| 机制 | 文本拼在时间片**之后**（源码偏移 5566）→ 过 GPT-2（5746）→ 截断 `[:, :patch_num]`（5835）。因果注意力下靠前位置看不到靠后位置，文本输出在被读出前已丢弃 |

同时实测：骨干只保留 **6 / 12** 层；**LoRA 从未应用**（`PEFT=0`）；`freeze` **无效**，**82,705,944 / 82,705,944 = 100% 参数可训练**；前向是**逐特征**的 `(8,104,1)→(8,24,1)`，从不联合七变量；**Test 只覆盖 feature 0**（`feat_id=[0]`，`drop_last` 后 170→160）；划分 `676/97/193` **与 A2 完全一致**。

**这意味着**：本报告 §3 中 MIFlu（2.042）优于 no-text（1.922）的结果，衡量的是**修正重构后**的通路差异；它**不能**被解读为对论文所述机制的验证或否证，因为论文的 token 顺序标注自相矛盾（见 `recovery/a1/a1_evidence_table_zh.md` §4），而发布实现在任一"时间在前"的顺序下都使文本失效。

### (b) 早前基线曝光的措辞需要收紧

`supervisor_brief_zh.md` 曾写"锁定后重算一致只验证数值，不可断言提前曝光不可能影响研究选择"。按本轮更严格的表述，应改为：

> 8 条基线的 Test 数值在 no-text 后两个种子拟合**之前**产生，不符合协议的**字面顺序**。已核实：当时系统内**不存在任何学习模型的 Test 数值**（全部 `DEFER_TEST=1`），因此基线数值在**机制上**不可能进入任何 checkpoint 选择路径；统一评分作业在完整锁定后从零重算并逐位相同，报告采用的基线值出自完整锁定之后。**但"机制上不可能影响选模"不等于"研究者的后续判断未受任何影响"**：本轮新增的模型范围、报告口径与结论取舍都是在基线数值可见之后作出的，这一事实予以记录，不作因果断言。

### (c) 本轮新增 GPU 使用

Stage 6 / A0 阶段（归档、审计、六骨干自检、A0 可执行诊断）**全部使用 `stingy` 的 CPU-only 作业**（`AllocTRES` 中无 `gres/gpu`），新增 GPU 消耗 **0.0000 GPU-hours**。A2 账本仍为 **1.1536 / 2.0**。

---

## 6. 本轮不能支持的结论（明确边界）

- **不能**说"已复现论文"或"已推翻论文"。A0 未执行，本轮是修正重构。
- **不能**把本轮任何数值与旧 1,025 行项目结果放进同一排名。旧结果（job 514859 的 2.238、control966 的 1.379、8-17 的 2.593/3.341/3.237/3.559）用的是 `676/96/194` 划分、10 reps、固定 20 epoch、无验证选模、且只保存了 ILI 单通道预测，与本轮 `676/97/193` + 3 seeds + 验证选模 + `strict` 窗口不同源。旧结果仅作"数据支线地标"，本报告未使用。
- **不能**把 3 个 seed 的波动当作时间泛化不确定性或重复实验。
- **不能**说"文本无效应被移除"。本轮只证明：在本协议、本数据、3 seeds 下，文本通路没有可确认的预测收益。文本敏感性预检（preflight job 584886：替换文本后输出变化 ≈1.6e-3）只证明**文本能影响输出**，不证明文本**提升性能**；这两件事在本轮被分别确认。
- **不能**把 `MIFlu ≈ NLinear` 写成"等效"。只能说在本协议下无法区分。
- **不能**声称 Test 隔离完美无瑕。旧实验（`--containment start`）确实存在验证目标越界进入 Test 的实质泄漏；本轮已修正并可核验，但历史结论中依赖旧窗口规则的任何"旧 Test 不受污染"推论都必须撤回。

---

## 7. 证据与交付物清单

| 内容 | 路径 |
|---|---|
| 本地完整产物（123 个文件，含逐条 SHA-256 清单） | `hpc_results/stage5_a2/` |
| 远端持久位置 | `/home/sychan552/stage5_a2_durable/` |
| 远端 scratch（有 10 天宽限） | `/scratch/sychan552/a2_stage5/results/stage5/` |
| 36 个锁定 checkpoint（含完整 SHA-256） | `hpc_results/stage5_a2/scoring/CHECKPOINT_LOCK.{json,csv}` |
| 统一 Test 评分表（44 行） | `hpc_results/stage5_a2/scoring/score_matrix.csv` |
| 独立重算表 | `hpc_results/stage5_a2/scoring/recomputed_*.csv` |
| 逐 (model, L, seed) 预测与真值张量（44 个 NPZ） | `hpc_results/stage5_a2/scoring/predictions/` |
| Test origin 清单（6688 行，含 epiweek / release_date） | `hpc_results/stage5_a2/scoring/predictions/test_manifest.csv` |
| 训练集 scaler（仅 `[0,676)` 拟合） | `hpc_results/stage5_a2/scoring/predictions/scaler_train_only.json` |
| 每 run 验证选模证据（metrics.csv / 逐 epoch 日志） | `hpc_results/stage5_a2/per_run/` |
| 作业 stdout / 派发日志 / GPU 账本 | `hpc_results/stage5_a2/logs/` |
| 实际执行的代码 + SHA-256 | `hpc_results/stage5_a2/code/` |
| 实际执行代码哈希台账 | `recovery/stage5/hashes_stage5_executed.json` |
| 补充表格 T1–T7 | `recovery/stage5/results_tables_zh.md` |
| 执行与资源账本 | `recovery/stage5/execution_ledger.md` |
| 冻结协议 | `recovery/stage5/frozen_protocol_stage5.md` |

**持久性说明**：5.0 GB 的 checkpoint 未复制到 home（配额 100 GiB，scratch 有 10 天宽限），但其完整 SHA-256 已锁定在 `CHECKPOINT_LOCK.json`，可据此校验唯一性。若需长期保留 checkpoint，应另行申请复制。

---

## 8. 建议的下一步（需用户/导师决定，本轮不自动执行）

1. **A0**：执行作者发布代码的逐字重放，才能对"我们的重构 vs 作者实现"给出可核验的对比。这是当前唯一真正未做的溯源支线。
2. **扩大 seed 数**：若要把 MIFlu / no-text / NLinear 的差异做成结论，当前 3 个 seed 不够（配对差 sd ≈ 0.26–0.27，而模型间差距 0.008–0.119）。需要预先固定统计方案，而不是反复尝试直到显著。
3. **真正的独立 holdout**：本轮 Test 已暴露，若要支撑"泛化"主张，必须另行声明并封存一个从未看过的未来区间。
4. **A2 之外的模型**：本轮只含 MIFlu / no-text / NLinear 三者，不构成对论文全部模型的复现判断。
