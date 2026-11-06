# 01_最终报告/figures/ — 报告用图（全部英文）

**所有图都已生成为英文**，可直接插入英文版报告（内部技术报告 / FYP 进度报告 / IEEE 稿件）。

---

## 一、模型预测对比（3 面板）

| 文件 | 内容 |
|------|------|
| `fig_forecast_L24.png` | MIFlu / NLinear / PatchTST 在 **L=24 周**的预测 vs 真值 |
| `fig_forecast_L36.png` | 同上，**L=36 周** |
| `fig_forecast_L48.png` | 同上，**L=48 周** |
| `fig_forecast_L60.png` | 同上，**L=60 周** |

每个面板：黑线 = 真值，彩色虚线 = 模型预测。左上角标注该模型的 **PTE/PIE** 和 **K&S 是否通过**。

## 二、单模型逐 step 图（高质量版）

| 文件 | 内容 |
|------|------|
| `fig_forecast_miflu_L24.png` | **MIFlu** L=24，4 个 step 各一条曲线 |
| `fig_forecast_miflu_L60.png` | **MIFlu** L=60 |
| `fig_forecast_nlinear_L24.png` | **NLinear** L=24 |
| `fig_forecast_nlinear_L60.png` | **NLinear** L=60 |
| `fig_forecast_patchtst_L24.png` | **PatchTST** L=24 |
| `fig_forecast_patchtst_L60.png` | **PatchTST** L=60 |

**这些图是最高质量的**，适合放在报告正文：
- y 轴 = **实际患者数**（已去归一化）
- x 轴 = **真实日期**（2016-10 到 2020-02）
- 4 条虚线 = step 0/1/2/3（1/2/3/4 周前的预测）
- 图例含每步的 **PTE（周）和 PIE（%）**

## 三、总览图

| 文件 | 内容 |
|------|------|
| `fig_forecast_all_horizons.png` | 4 个跨度放一起看（2×2 大图） |
| `fig_all_models_ranking.png` | **28 个模型**按 MSE 排名（含家族着色） |
| `fig_llm_encoders_vs_baseline.png` | **11 个 LLM 编码器** vs 最佳常规模型 |
| `fig_pareto_frontier.png` | 准确率 vs 参数量（性价比） |
| `fig_pte_pie_heatmap.png` | 峰值预测 PTE/PIE 热力图 |

---

## 怎么读这些图

- **黑线**永远是真值（Ground Truth）
- **彩色线**是模型预测，颜色越接近黑线越好
- **PTE** = 峰值日期误差（周），越小越好，≤1 周算好
- **PIE** = 峰值强度误差（%），越小越好，≤25% 算好
- **K&S PASS** = 该模型通过 Kramer & Shaman (2019) 标准（PTE≤1 且 PIE≤25%）

## 图的生成方式

图由 `05_程序代码/` 中的脚本从 `03_预测数据_证据/expanded_runs/` 的预测数据生成。
数据来源和指标定义见 `WHERE_EVERYTHING_IS.md`。


## 四维汇报专用参数图

fig_pareto_presentation.png 由 presentation/build_pareto_figure.py 从 BENCH_EFFICIENCY.csv 的 11 个非空参数量模型重画。所有点均保留，仅标注 NLinear 和 PatchTST 以便投影阅读；MIFlu 与编码器不在该子集。横轴为对数参数量，纵轴为平均 MSE，参数量不能替代实测运行时间。内部报告仍保留原完整标签版本。
