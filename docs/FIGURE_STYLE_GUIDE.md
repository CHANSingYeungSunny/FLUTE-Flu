# MIFlu 出图规范 (Figure Style Guide)

本规范定义 MIFlu 复现 ChatTime 评估协议时两张出版级图与 verdict 表的样式。
目标：与 ChatTime 的 `make_ili_evaluation_figure.py` 视觉与信息密度一致，
便于并排对比。

---

## 图 1 — 连续预测曲线 (Hero figure)

- 文件：`results/ili/figures/fig_miflu_eval_continuous.png`
- 尺寸：**7 in × 4.2 in**，DPI **300**。
- 内容：
  - 横轴：时间（epiweek → 日期，ISO 周一起点）。
  - 蓝色虚线：Ground Truth (ILITOTAL)；红色实线：MIFlu Prediction (ILITOTAL)。
  - 蓝色倒三角：真实峰值；红色正三角：预测峰值。
  - 背景按流感相位着色（Baseline / Ramp-up / Peak / Decay）。
  - 右上角注释框：4 指标数值（Peak Hit / Timing / Peak Intensity / Direction）。
- 标题示例：`MIFlu Full-Test Continuous Curve with Peaks & Phases (N=7, OT=num_patients)`。

## 图 2 — 诊断图 (Diagnostics, 2-panel)

- 文件：`results/ili/figures/fig_miflu_eval_diagnostics.png`
- 尺寸：**13 in × 4.2 in**（1×2 子图），DPI **300**。
- 左 panel — Rolling Directional Accuracy：
  - 13 周滚动窗口的方向符号匹配概率；含 chance=0.5 参考线与 overall 均值线。
- 右 panel — Per-Season Peak Timing & Magnitude Error：
  - 每个流感季两根柱：`|Δt|` 周数（蓝）与 magnitude rel-err %（橙）。

---

## Verdict 表规范

- 文件：`results/ili/metrics/miflu_verdict_table.md`（同时产出可对照的 JSON）。
- 表格为**真实 Markdown 表格**（竖线分隔），但单元格内 **不含竖线 / 希腊字母**，
  避免渲染歧义。
- 列：`Indicator | Value | Threshold | Verdict`。
- 行：Peak Hit / Timing / Peak Intensity / Direction。
- `Verdict` 取值：`accurate` / `NOT accurate`（大写以醒目）。

| Indicator | Value | Threshold | Verdict |
|---|---|---|---|
| Peak Hit | 0.xxx | 0.75 | accurate / NOT accurate |
| Timing | x.xx | 2.00 | accurate / NOT accurate |
| Peak Intensity | xx.x | 20.00 | accurate / NOT accurate |
| Direction | 0.xx | 0.60 | accurate / NOT accurate |

---

## 配色（与 ChatTime 一致）

- Ground Truth：`#1f77b4`（蓝）；Prediction：`#d62728`（红）。
- 相位底色：`Baseline #e8e8e8 / Ramp-up #fde0dd / Peak #f9c0bb / Decay #d9d2e9`。
- 方向图：`#2ca02c`（绿）；overall 线：`#d62728`（红点线）。

---

## 通用 matplotlib 设置

- `font.size=9`，`axes.titlesize=10/11`，`legend.fontsize=8`，`xtick/ytick.labelsize=8`。
- `figure.dpi=100` 用于屏幕预览；`savefig(dpi=300)` 用于出版。
- 后端：`Agg`（无显示环境，如 HPC / 本地 CPU）。

---

## 实现位置

- `scripts/make_miflu_evaluation_figure.py` — 纯 CPU 出图（matplotlib / pandas / numpy）。
- 输入依赖：`results/ili/miflu_fulltest_walkforward.csv` +
  `results/ili/metrics/miflu_ili_peak_indicators.csv` +
  `results/ili/metrics/miflu_ili_peak_trend_summary.json`。
