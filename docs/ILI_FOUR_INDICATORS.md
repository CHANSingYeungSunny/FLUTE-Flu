# MIFlu ILI 四大评估指标 (Four Indicators)

本文件描述 MIFlu 在 **National ILITOTAL** 单目标上使用的四个补充评估指标与判定
阈值。这些指标由本项目脚本 `compute_miflu_indicators.py` 计算，作为 MIFlu 论文
MSE/MAE 主协议的**补充诊断**（supplementary，非论文原协议）。

目标序列：ILITOTAL（全国流感样病例就诊总计数），物理单位 = 患者人数。
输入通道 N=7（含 OT = num_patients（CDC 总就诊人次/分母，全量未缩放），推导与口径详见
`MIFlu_论文完整解析与答辩解答.md` §1 第 7 通道及附注）。

---

## 1. Peak Hit（峰值命中率）

- 定义：真实峰值中被预测峰值在 **±2 周** 内匹配到的比例。
- 计算：`hit_rate = n_hit / n_true_peaks`，其中 `n_true_peaks` 为真实峰值总数。
- 判定阈值：**≥ 0.75** 视为 accurate。

## 2. Timing（峰值时间误差）

- 定义：所有命中峰值对的平均绝对时间差 |Δt|（单位：周）。
- 计算：`mean_abs_delta_t = mean(|pred_peak_idx - true_peak_idx|)`。
- 判定阈值：**≤ 2.0 周** 视为 accurate。

## 3. Peak Intensity（峰值强度误差）

- 定义：命中峰值处预测值相对真实值的 **平均绝对相对误差 (%)**。
- 计算：`mean_peak_magnitude_rel_err = mean(|pred - true| / true * 100)`。
- 判定阈值：**≤ 20.0 %** 视为 accurate。

## 4. Direction（方向准确率）

- 定义：逐周（week-over-week）斜率符号一致的比例（剔除双边均为 0 的点）。
- 计算：`directional_accuracy = mean(sign(Δgt) == sign(Δpred))`。
- 判定阈值：**≥ 0.60** 视为 accurate。

---

## 阈值汇总

| Indicator       | Key (JSON)                       | Threshold | 方向   |
|-----------------|----------------------------------|-----------|--------|
| Peak Hit        | `peak_hit_rate`                  | ≥ 0.75    | 高越好 |
| Timing          | `mean_abs_delta_t`               | ≤ 2.0     | 低越好 |
| Peak Intensity  | `mean_peak_magnitude_rel_err`    | ≤ 20.0    | 低越好 |
| Direction       | `directional_accuracy`           | ≥ 0.60    | 高越好 |

---

## 输出物

- `results/ili/metrics/miflu_ili_peak_indicators.csv` — 逐峰值明细表
  （season, true/pred peak date, Δt, true/pred magnitude, rel-err%, status）。
- `results/ili/metrics/miflu_ili_peak_trend_summary.json` — 聚合指标 + `verdicts`
  块（`verdicts.{key}.value / threshold / verdict`）。
- `results/ili/metrics/miflu_verdict_table.md` — 人类可读 verdict 表（ASCII，无竖线歧义）。

`verdict` 取值：`accurate` / `not accurate`。

---

## 实现位置

- `scripts/compute_miflu_indicators.py` — 指标计算（纯 CPU：
  pandas / numpy / scipy / statsmodels）。
- 峰值检测：`scipy.signal.find_peaks`，`prominence=0.08*(max-min)`，`distance=8`。
- 季节标签：Jul–Jun 流感季（如 2018-01 → `2017-2018`）。
- 日期解析：epiweek（YYYYWW）→ `datetime.fromisocalendar(y, w, 1)`（ISO 周一起点）。
