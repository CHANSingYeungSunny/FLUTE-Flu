# 计划：面向导师的流感预测评价图（适配 HPC，英文输出）

## 状态
已定案（FINAL）。代码干净、符合学术发表规范，输出全英文，无缓存机制、无内存防护代码、无 CJK 字体依赖。

**学术发表决策：** 为配合未来论文（essay / paper）投稿，所有图表面签、注解、CSV 列名与控制台输出均已定案为**全英文 + 国际标准数学符号（Δ、≈、•、─）**。所有 CJK 字体逻辑（SimHei / Microsoft YaHei / Noto Sans CJK SC、字体自检、降级）已全部移除——matplotlib 使用默认英文字体，可在任意 HPC Linux 环境下 100% 稳定渲染，绝无"豆腐块"乱码。

目标运行环境：学校 HPC（GPU）。**切勿在本机 GTX 1650（4GB 显存）上运行**（会 OOM）。

## 目标
`make_forecast_figure.py` 生成一张导师可见的图 + 一个 CSV：展示**精确的原始计数数值**（真值 vs 预测），并附一句判定结论（Accurate / Partially Accurate / Inaccurate）与解释性指标（COVID 第一波、H1N1 2009 对比）。指标仅作参考，非主结论。

## 硬性约束
1. **训练逻辑不变**——标准 `DataLoader` + 完整 GPU 训练，严格遵循原 MIFlu 论文方法论：**固定 20 个 epoch（经验性设定），无 early stopping / 无 patience / 无最优权重保存**（验证集 MSE 仅记录供参考，不参与任何终止或 checkpoint 决策）。`device = 'cuda' if torch.cuda.is_available() else 'cpu'`。
2. HPC 运行命令：`python make_forecast_figure.py`
3. 产出（三个文件，均位于 `data/`）：
   - `data/forecast_fig_national.png`（唯一导师可见图）
   - `data/forecast_values_national.csv`（列：epiweek, ground_truth, prediction, abs_err, rel_err, is_peak）
   - `data/forecast_run.log`（通过 Python 标准 `logging` 模块：训练进度 epoch/loss 同时镜像到控制台与本文件，外加最终数值报告与判定结论）
   - 控制台打印同样的数值报告与判定（英文）。
   - 禁止额外 png/pdf。

## 主图 `data/forecast_fig_national.png`
**Panel A（主体，≥60% 面积）— 预测放大窗**，epiweeks（约 201943–202014）：
 - x 轴为 epiweek（如 202006），绝不用 0–23 的周编号。
 - 绿线=真值、红线=预测、黑色细线=上下文（输入历史）。
 - `scipy.signal.find_peaks` 设 prominence/distance，最多标 3 个峰。
 - 每个峰旁标注精确千分位整数（运行时动态计算）。
 - 每对峰标注时间偏差 dt（周）+ 强度偏差 d%（如 "Timing accurate, magnitude underestimated by 13.4%"）。
 - 标题：动态英文判定，如 "Conclusion: Captured COVID Wave 1 peak timing accurately, magnitude underestimated -> Partially Accurate"。

**Panel B（数值表）**：峰周 + 关键周（epiweek | True | Pred | Abs Err | Rel Err%），峰行高亮。完整 24 周进 CSV，不上图。

**Panel C（参考指标框）**：指标（峰相对误差、峰周偏移、趋势斜率）仅以 "Reference" 身份出现，解释峰值成因（COVID 第一波；与 H1N1 2009 峰值量级对比——该数值从 CSV 的 2009 年窗口动态计算，绝硬编码 69068）与趋势含义。**MSE 不是主结论**。

## 数据（已确认）
- `data/national_illness_raw.csv`：1025 周，200201 → 202152。
- 选定预测窗口：epiweeks 约 201943 → 202014（覆盖 COVID 第一波 202005–202006，峰值约 108k–111k）。
- 参考峰值：H1N1 2009（从数据动态计算）、COVID 第一波 2020、Omicron 202152——全部运行时推导，无硬编码。

## 训练协议一致性说明（重要）
- 经核查整个项目（`train_miflu.py`、`train_baseline.py`、`train_regional_miflu.py`、`train_regional_baseline.py`、`make_forecast_figure.py`），**所有训练脚本均为固定 epoch、无 early stopping**，与原论文方法论及已生成的 `results_*.csv` 训练日志（`ep 20/20` 跑满）完全一致。（注：`train_national.py` 曾存在但偏离 Table IV 且从未运行，已于 2026-08-06 删除。）
- `miflu_model.py`、`textual_embedder.py` 为模型/嵌入定义文件，不含训练循环，无早停逻辑。
- 已生成的 `data/results_baseline.csv`、`data/results_miflu.csv` 及对应训练日志无需重训；其 ILITOTAL 的 +194%~+414% MSE 偏差方向已定位（ILITOTAL 本身 + 数据/切分口径层面系统性偏移），确切根因待 HPC 定量确认，与训练协议无关。
