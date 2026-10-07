# Stage 5 — 冻结协议与已记录决定（A2：作者 966 行数据的受控比较）

生成时间见 `hashes_stage5.json`。**决定来源：本次执行指令（CodeBuddy_MIFlu_Stage5_Execution_Prompt_ZH.md），不代表导师已批准。**

## 1. 数据、任务与比较对象

| 项 | 冻结值 |
|---|---|
| 数据 | 作者 966 行快照（`recovery/author_repo/dataset/illness/national_illness.csv`，完整 SHA-256 见 `hashes_stage5.json`） |
| 划分 | train / validation / Test = **676 / 97 / 193**；边界 676、773；零基半开区间 `[0,676)`、`[676,773)`、`[773,966)` |
| 历史结果 | `676/96/194` 结果保留，不覆盖；`project_1025` 默认行为不变（717/819） |
| T / L | T = 104；L ∈ {24, 36, 48, 60} |
| 变量 | 七个映射变量全部作为预测与主要评价对象 |
| 学习模型 | 修正重构版 MIFlu、`no_multi`（no-text 通路消融）、NLinear；每模型每 L 用冻结种子 42/43/44 各训练一次 = **36 个拟合任务** |
| 确定性基线 | Last Value、Seasonal Naive 各 4 个 L = **8 个评价任务**，不乘种子、不重复训练 |
| A2 合计 | 44 条记录（36 NEW_FIT + 8 NEW_EVAL） |
| A0 | 单独保留为 `BLOCKED`（`a0_diagnostic_record.csv`），不混入本轮预算 |

## 2. 窗口、缩放与指标

- 输入 `[o-103, o]`，目标 `[o+1, o+L]`；**目标必须完整位于所属划分**（见第 5 节 D-windows）。
- 缩放器只用训练行拟合（`train_end=676`）；缓存按数据 / 划分 / prompt / 模型 revision 区分。
- 主要指标：对每个模型、种子、L，在该 L 的**共同有效 origins、全部 L 个 lead、七变量**上计算训练集标准化空间的平均平方误差；先平均种子，再等权平均四个 L，得 `average_MSE_4L`。
- 补充 MAE、各 L 结果、每变量原单位误差、weighted ILI 单独结果。**不先平均种子预测再算误差**（那是集成模型）；原单位不同的变量不合并成未解释的总误差。

## 3. 选择规则与 Test 定位

- 每个模型 / L / 种子分别用**对应验证集七变量标准化 MSE** 选 checkpoint。
- `average_MSE_4L` 是跨任务报告指标，不用于选择某个 L 的训练 epoch。
- 不在每个 epoch 读取或评分 Test；不根据 Test 更换种子、超参、模型、窗口、prompt 或 split。
- 本轮不自动增加 train+validation 合并重训。
- 允许对**已暴露**的作者 Test 做协议冻结后的**回顾性评价**；它不因此恢复为"从未看过的独立测试集"。任何另行封存的新 holdout 不在本轮范围。

## 4. 已记录决定

| ID | 决定 | 状态 | 来源 |
|---|---|---|---|
| D-adapter | 应用 author-966 适配器 | 已完成 | Stage 4 |
| D-nlinear | 实现 NLinear + naive 薄运行器 | 已完成 | Stage 4 |
| D-split | 采用 676/97/193 | **已记录** | 本指令 §2.1 |
| D-target | `average_MSE_4L`（七变量 z 空间）为选择与报告指标 | **已记录** | 本指令 §2.2 |
| D-windows | 目标**完整包含**于划分（新增，见第 5 节） | **已记录（实现变更）** | 本指令 §2.2 |
| D-holdout | 仅对已暴露作者 Test 做一次性回顾性评价 | **已记录** | 本指令 §2.3 |
| D-compute | GPU 小时上限 + 队列 / 节点 + 并发上限 | **缺失（未授权）** | — |
| D-a0-env | A0 重放环境 | **缺失（未授权）** | — |

## 5. D-windows：窗口归属规则修正（本轮实际代码变更）

**发现**：三个运行器（`train_miflu.py`、`train_ablation.py`、`train_nlinear_966.py`）原按**目标起点**归属划分（`0 if ts < train_end else (1 if ts <= val_end else 2)`），与目标长度无关。因此在 L=60 时：

- 训练窗口的目标会跨进验证段（训练目标含验证行）；
- 验证窗口的目标会跨进 Test 段 —— 而这正是本轮选 checkpoint 的依据，构成实质 contamination。

**修正**：新增显式开关 `--containment {start,strict}`。

- `start`（默认）：保留历史行为，旧结果可比；
- `strict`（**A2 本轮使用**）：整个目标块必须落在所属划分内；跨界的窗口标为 `-1` 并剔除（不重新归属、不凑数）。

**核对结果**（`window_counts_verify.md`，CPU，三运行器一致）：

| L | train | val | test |
|---|---:|---:|---:|
| 24 | 549 | 74 | 170 |
| 36 | 537 | 62 | 158 |
| 48 | 525 | 50 | 146 |
| 60 | 513 | 38 | 134 |

与本指令 §2.2 表格**逐项一致**。修正前为 train=572、val=98（与 L 无关）、test=193−L。

## 6. 仍未解决（需导师 / 用户决定，不阻塞只读与静态工作）

见 `launch_decisions_stage5.md`：D-compute、D-a0-env；以及 `STATE.md` 中第 1、2、4、8、9 项科学决定。
