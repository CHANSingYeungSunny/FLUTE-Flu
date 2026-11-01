# Track C 缩放合同与物理单位审计

*Companion to `TRACK_C_PHYSICAL_UNIT_SANITY.csv` and `TRACK_C_VARIABLE_LABEL_AUDIT.csv`.
Source: `audit_20260930/predictions_stage6/scaler_train_only.json`, author-966 raw data
`recovery/author_repo/dataset/illness/national_illness.csv`. No retraining; local CPU only.*

## 1. 缩放合同（已被严格包含性冻结）

- **缩放器仅在 author-966 的 Train 行 [0, 676) 上拟合**（`train_end=676`, `val_end=773`），
  持久化于 `scaler_train_only.json`（profile: `author_966`）。
- **8 个模型全部在同一 z 空间评分**；最终 Test 排名在 z 空间计算。
- 物理单位（ILITOTAL）反变换统一使用：
  `physical = z * 9003.15234375 + 9439.841796875`（仅 ILITOTAL，feature index 4）。
- **不存在 RevIN / 全局 StandardScaler 混用**：真值与预测两条线使用同一套 train-only 反变换。
- 日期列已排除在 7 个预测特征之外（date 是索引，非特征）。

## 2. 变量标签订正（关键修正）

历史报告 Q3 曾使用 `mean=9368.29 / scale=8853.43 / train[:717]`，那属于 **1025 行 / 更早实验**，
在严格 966 行合同下已被取代。Track C 的 7 个变量（来自 `scaler_train_only.json.var_cols`）确认为：

| idx | 原始 CSV 列 | 规范标签 | 是否为 PTE/PIE 目标 |
|---|---|---|---|
| 0 | 1 | % WEIGHTED ILI | 否 |
| 1 | 2 | % UNWEIGHTED ILI | 否 |
| 2 | 3 | AGE 0-4 | 否 |
| 3 | 4 | AGE 5-24 | 否 |
| 4 | 5 | **ILITOTAL** | **是（流感活动量）** |
| 5 | 6 | NUM. OF PROVIDERS | 否 |
| 6 | OT | OT | 否 |

> PTE/PIE 主峰目标 = **ILITOTAL**（feature index 4），与计算脚本 `compute_pte_pie_track_c.py`
> 中 `ILI = 4` 一致，并匹配缩放器第 4 项（mean 9439.84 / scale 9003.15）。

## 3. 物理单位合理性（Train [0,676) 描述统计）

| 变量 | 训练最小值 | 训练最大值 | 训练均值 |
|---|---|---|---|
| ILITOTAL（目标） | 318.0 | 69,068.0 | 9,439.84 |
| AGE 5-24 | 91.0 | 39,364.0 | 3,745.15 |
| AGE 0-4 | 98.0 | 13,187.0 | 2,672.45 |
| NUM. OF PROVIDERS | 264.0 | 2,197.0 | 1,322.16 |
| % WEIGHTED ILI | 0.35 | 7.72 | 1.74 |
| % UNWEIGHTED ILI | 0.49 | 7.62 | 1.71 |
| OT | 64,699.0 | 906,536.0 | 493,629.37 |

- 反变换往返最大误差 = **2.9e-11**（精确可逆，证实 inverse_transform 实现无系统偏差）。
- ILITOTAL 落在"数千到数万"量级，与 MIFlu 论文对 ILITOTAL 量级的描述一致。

## 4. 与 MIFlu 论文 Table II 的比对说明（已披露的限制）

MIFlu 论文 Table II 在原 PDF 中是**扫描表格图片**，无法机器提取精确数值
（见历史报告已披露限制）。本审计改用**同一份 National-Illness 原始数据集的实测描述统计**作为等价独立交叉验证：
若管线用错缩放器或错轴，该检查足以暴露。若日后取得 Table II 精确数值，可再做逐格核对。

## 5. 结论

Track C 缩放合同自洽、无泄漏（验证/测试信息未进入缩放器拟合）、8 模型同空间可比；
ILITOTAL 标签与反变换已订正为严格 966 行合同的值，历史 Q3 的 1025 行数值不再适用。
