---
name: enhanced-forecast-figure
overview: 增强 make_forecast_figure.py，生成一张导师可用的、带 epiweek 时间轴、COVID 阴影标注、峰值说明和自解释面板的预测 vs 真值综合图。同时在 CPU 模式下跑出最终结果。
todos:
  - id: extract-epiweek-info
    content: 在窗口选择后提取 epiweek 信息：计算 wi_e（原始df中的窗口起始行）、提取上下文和预测区间的 epiweek 列表，并定位 COVID/H1N1 的df行索引区间
    status: completed
  - id: enhance-csv-output
    content: 修改 CSV 输出：在 `forecast_values_national.csv` 中新增 epiweek 列，格式为 step, epiweek, ground_truth_ILITOTAL, prediction_ILITOTAL, abs_error
    status: completed
    dependencies:
      - extract-epiweek-info
  - id: rewrite-plot-panel-a
    content: 重写面板一（历史全景）：全历史 ILITOTAL 曲线、COVID 红色阴影 (202001-202152)、H1N1 橙色阴影 (200915-200952)、训练/验证/测试分割虚线、选中预测窗口绿色高亮框
    status: completed
    dependencies:
      - extract-epiweek-info
  - id: rewrite-plot-panel-b
    content: "重写面板二（预测放大）：epiweek x轴旋转标签、输入上下文黑色实线、真值绿色圆点连线、预测红色虚线方块、forecast start 灰色分隔线。用 scipy.signal.find_peaks 检测真值/预测峰值：真值峰值画蓝色★、预测峰值画红色●，峰值处 annotate 具体数值（如 'W202006: 108,307'）；计算并标注时间偏差(差几周)与强度偏差(差多少)"
    status: completed
    dependencies:
      - extract-epiweek-info
  - id: rewrite-plot-panel-cd
    content: 重写面板三（数值表与解释）：24行精确数字表含 epiweek 列且峰值行高亮；解释性文字框用人话列出具体偏差（真值峰值 vs 预测峰值的周偏差/强度偏差%）、峰值命名（COVID Wave 1 等）、量级对比（vs H1N1 2009）、模型行为描述；底部趋势解释区用箭头+文字说明峰值业务原因（如'进入冬季 ILI 显著上升，符合流感爆发特征'）。同时在控制台打印同样的数值对比报告。保存 peak_analysis_plot.png 与 .pdf
    status: completed
    dependencies:
      - enhance-csv-output
      - rewrite-plot-panel-b
  - id: cpu-run-and-verify
    content: 用 CPU 模式运行脚本生成最终图：`$env:MIFLU_DEVICE="cpu"; python make_forecast_figure.py`，验证 `data/forecast_fig_national.png` 和 `data/forecast_values_national.csv` 输出正确
    status: completed
    dependencies:
      - rewrite-plot-panel-cd
---

## 用户需求

导师原话要求："can you give me the photo/graph that have exact number of prediction and ground truth? also include the indicator to explain the reason behind it."

需要生成一张**能说服导师的综合图**，包含：

- 精确的预测数值与真值对比
- 解释性标注（COVID-19 期间双峰位置、H1N1 参考峰值）
- epiweek 时间轴而非泛化的"Week"编号

## 产品概述

增强 `make_forecast_figure.py` 绘图部分，输出一张**三面板综合诊断图**：历史全景 + 预测放大 + 精确数字表与解释文字。不改训练逻辑，纯 CPU 运行。

## 核心功能

- **面板一（历史全景）**：2002-2021 全历史 ILITOTAL 曲线，COVID/H1N1 高亮阴影，训练/验证/测试分割线，选中预测窗口框选
- **面板二（预测放大）**：epiweek x轴，输入上下文 + 真值 + 预测三条线，峰值箭头标注，COVID 期间标记
- **面板三（数值与解释）**：24周精确数字表（新增 epiweek 列），解释性指标文字框（峰值命名、量级对比、模型捕捉情况）
- CSV 输出新增 epiweek 列

## 技术栈

- Python 3.9 + Matplotlib（GridSpec 多面板布局）
- 复用现有 torch/numpy/pandas 栈，不引入新依赖
- 纯 CPU 模式（`MIFLU_DEVICE=cpu`）

## 实现方案

### 修改范围

**仅修改 `make_forecast_figure.py` 第 56-161 行**，具体为：

1. 第 56-61 行（窗口选择后）：新增 epiweek 信息提取
2. 第 126-133 行（CSV 输出）：新增 epiweek 列
3. 第 135-161 行（绘图）：完全重写为三面板 GridSpec 布局

训练逻辑（第 1-55、63-125 行）完全不改。

### 三面板布局设计

```
┌─────────────────────────────────────────┐
│ Panel A (top 35%): Historical Overview  │
│ Full ILITOTAL 2002-2021, shaded regions │
│ for COVID & H1N1, split markers, window │
│ highlight box                           │
├──────────────────────┬──────────────────┤
│ Panel B (mid 35%):   │ Panel C:         │
│ Forecast Detail      │ Indicator Text   │
│ - epiweek x-axis     │ - Peak naming    │
│ - context + truth    │ - Magnitude      │
│   + prediction       │   comparison     │
│ - peak arrows        │ - Model behavior │
│                      │   explanation    │
├──────────────────────┴──────────────────┤
│ Panel D (bottom 30%): Exact Numbers     │
│ Table (step, epiweek, truth, pred, err) │
│ with COVID-peak rows highlighted        │
└─────────────────────────────────────────┘
```

### 关键实现细节

**epiweek 索引追踪**：在窗口选择后，从 `df['epiweek']` 提取对应的 epiweek 列表：

- `ctx_epiweeks = df['epiweek'].iloc[wi_e + T - 40 : wi_e + T].values`（上下文最后40周的epiweek）
- `fc_epiweeks = df['epiweek'].iloc[wi_e + T : wi_e + T + L].values`（预测24周的epiweek）
其中 `wi_e` 是窗口在原始 `df` 中的起始行索引，需从测试集内 `wi` 回推：`wi_e = np.where(split == 2)[0][wi]`

**COVID/H1N1 阴影区间**：

- H1N1: epiweek 200915-200952（约2009年4月-12月）
- COVID: epiweek 202001-202152（2020年1月-2021年底）
- 使用 `ax.axvspan()` 在历史曲线上绘制半透明色块

**峰值自动检测**：扫描预测窗口24周内的 ILITOTAL 真值，对超过阈值（如均值的2倍或绝对值>80k）的周次标注箭头。

**解释性文字**：

- "COVID-19 Wave 1 (Jan-Mar 2020): ILITOTAL surged from ~20k to 111,361 at epiweek 202006"
- "Model captures the rapid ascent but underestimates peak magnitude by X%"
- "H1N1 2009 reference: peak 69,068 at epiweek 200942"
- "Split: Train 70% (2002-2016), Val 10% (2016-2018), Test 20% (2018-2021)"

### 性能考量

- 绘图部分纯 CPU/内存操作，不计入训练时间
- 全历史数据 1025 点 x 1 折线，Matplotlib 秒级完成渲染
- 图尺寸 ~18x14 inches @ 120 DPI，文件大小 ~500KB-1MB
- 首次运行（含 GPT2 下载 + 训练）：约 15-35 分钟
- 后续运行（GPT2 已缓存）：约 10-25 分钟

### 向后兼容

- CSV 列新增 epiweek，但保留原有列，旧解析脚本不受影响
- MIFLU_DEVICE 环境变量机制保留
- 所有现有训练参数不变