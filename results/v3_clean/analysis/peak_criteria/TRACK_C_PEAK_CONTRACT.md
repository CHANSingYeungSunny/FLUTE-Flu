# Track C 峰值分析合同（Peak Contract）

*本文件定义 Track C 八模型 PTE/PIE 的计算合同。所有数值来自冻结的 Test 预测，
未重新训练、未修改预测。*

## 1. 主峰目标变量

- **ILITOTAL**（feature index 4），即全国流感样病例就诊量的代理指标，物理单位为**病例数（patient counts）**。
- 选择依据：MIFlu 论文、作者数据变量定义、Track C 目标 schema、以及历史导师疑问意图，
  均指向 ILITOTAL 作为主流感活动量目标。**不对 7 个无关变量做单一合并峰值。**
- 仅 ILITOTAL 进入 PTE/PIE；其余 6 个变量为辅助特征。

## 2. 物理单位与反缩放

- 所有 8 模型在同一 z 空间评分；PTE/PIE 必须回到物理单位（PIE 是相对误差，z 空间会除到错误分母）。
- 反变换：`physical = z * 9003.15234375 + 9439.841796875`（来自 `scaler_train_only.json`，
  **仅在 Train 行 [0,676) 拟合**）。往返误差 2.9e-11（精确可逆）。

## 3. 日期映射与季节定义

- 数据集周频，起始 2002-01-01。`date(row) = 2002-01-01 + 7*row 天`。
- 流感季为**年度周期**。真实季节峰必须相隔较远：取 `MIN_SEP_WEEKS = 40`（保守年度下界；
  30 周曾把离群小峰误计为季节峰，导致每单元 ~5.5 个峰）。
- Track C Test 行 773–965 → **2016-10-25 → 2020-06-30**（不覆盖 2021 高 ILI 异常）。

## 4. 峰值检测

- 贪心选峰：反复取序列最大值，然后掩蔽其 ±`MIN_SEP_WEEKS//2` 邻域；候选必须超过**幅度地板**。
- 幅度地板 = 序列**均值**（中位数会把 18k 水平的离群小峰算作季节峰，使峰数虚高）。
- 每个 (model, L, seed) 单元独立检测。

## 5. 峰匹配方法

- 对每个真实峰，在 ±`MATCH_TOL_WEEKS = 2` 周内找最近的、未使用的预测峰。
- 匹配成功但仅满足一项判据 → `MatchedNotHit`；两项都满足 → `Hit`；
  真实峰无匹配 → `Missed`；预测峰无对应真实峰 → `FalsePeak`。

## 6. 聚合方式

- **种子聚合**：每模型 3 种子 × 4 horizon = 12 单元，共 **36 个真实峰**。
- **horizon 处理**：每个 horizon 独立评分，再跨 horizon 池化（不跨 horizon 合并 MSE）。
- **判定按峰（per peak），不按均值**：均值会掩盖一个 2 周错位的峰被另一个 0 周错位的峰抵消，
  不符合 Kramer & Shaman 的判定约定。

## 7. 判定阈值——文献标准 vs 项目自定义（必须分离）

### 文献标准（LITERATURE，直接引自 Kramer & Shaman 2019, PLOS Comput Biol,
DOI 10.1371/journal.pcbi.1006742；与 CDC "Predict the Influenza Season Challenge" 同口径）

- **PTE ≤ 1 周**
- **PIE ≤ 25 %**
- 两条件**同时满足**才记为一次峰值命中（HIT）。

### 项目自定义工程门槛（PROJECT_CUSTOM_ENGINEERING_CRITERIA，非 MIFlu 论文）

- **PTE ≤ 2 周**（相对文献 1 周放宽）
- **PIE ≤ 20 %**（相对文献 25 % 收紧）
- 明确标注为自定义，不可表述为论文标准。

> 不得把 PTE≤2 / PIE≤20 或任何"Peak Hit Rate ≥ 0.75"描述为 MIFlu 论文标准。
> MIFlu 原论文（IEEE JBHI 2025）中不存在这些阈值定义（历史报告已订正）。

## 8. 缺失 / 边界情况

- `Missed`：真实峰无预测匹配（计为未命中，计入分母）。
- `FalsePeak`：预测峰无真实对应（不计为真实峰，仅作诊断）。
- 单元缺失（预测文件不存在）→ 跳过，不计入。
