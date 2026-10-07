# MIFlu ILI 评估指标 (PTE / PIE)

> **2026-09 更新（重要）**：本文件原描述"四大指标"（Peak Hit / Timing /
> Peak Intensity / Direction）。现已精简为**两项**：
> **PTE（Peak Timing Error，峰值时间误差）** 与 **PIE（Peak Intensity Error，峰值强度误差）**。
>
> - `peak_hit_rate`（峰值命中率）与 `directional_accuracy`（方向准确率）已**彻底移除**——
>   不再计算、不再判定、不再出现在任何图形或表格中。
> - 训练端的**"双闸门"早停机制**（val_loss 下降 **且** peak_hit_rate 过阈才保存 checkpoint）
>   依赖命中率，已随之移除；早停现为纯 `val_loss + patience`（见 `scripts/early_stopping.py`）。
> - 文件名保留 `ILI_FOUR_INDICATORS.md` 仅为不破坏既有链接，内容已改为两项。

本文件描述 MIFlu 在 **National ILITOTAL** 单目标上使用的两个补充评估指标与判定
阈值。这些指标由本项目脚本 `compute_miflu_indicators.py` 计算，作为 MIFlu 论文
MSE/MAE 主协议的**补充诊断**（supplementary，非论文原协议）。

目标序列：ILITOTAL（全国流感样病例就诊总计数），物理单位 = 患者人数。
输入通道 N=7（含 OT = num_patients（CDC 总就诊人次/分母，全量未缩放），推导与口径详见
`MIFlu_论文完整解析与答辩解答.md` §1 第 7 通道及附注）。

---

## 1. PTE — Peak Timing Error（峰值时间误差）

- 定义：真实峰值与其匹配预测峰值之间的**平均绝对时间差 |Δt|**（单位：周）。
- 计算：`peak_timing_error_weeks = mean(|pred_peak_idx - true_peak_idx|)`，
  **仅在匹配峰值上计算**（`status == "Hit"`，匹配窗口 ±2 周）。
- 判定阈值：**≤ 2.0 周** 视为 accurate。

> ⚠️ **这是误差，不是提前期（lead time）**。 Advisor Q1c：曾有人把 0.5 读作
> "提前 0.5 周"，其真实含义是"匹配峰值平均差半周"。提前期由 `step` 列给出
> （step h = 第 h+1 周提前）。旧键名 `mean_abs_delta_t` 作为弃用别名保留以兼容
> 既有 JSON/CSV 消费者。

## 2. PIE — Peak Intensity Error（峰值强度误差）

- 定义：匹配峰值处预测值相对真实值的**平均绝对相对误差 (%)**。
- 计算：`mean_peak_magnitude_rel_err = mean(|pred - true| / true * 100)`，
  **仅在匹配峰值上计算**。
- 判定阈值：**≤ 20.0 %** 视为 accurate。

---

## 样本量限定语（必须与 PTE/PIE 同显）

PTE 与 PIE **只在匹配峰值上有定义**。因此它们必须始终与匹配峰值计数一同展示：

- `peak_hit_count`：形如 `"3/5"` 的字符串（匹配数 / 真实峰值总数）
- `n_hit`、`n_missed`

图中写作，例如：`PTE = 1.5 wk (based on 2/3 matched peaks)`。

**该计数是样本量限定语，不是被报告的指标**——峰值命中"率"（比值）已移除。
不标样本量会让读者无法判断该均值取自 5 个峰还是 1 个峰，审稿时易被质疑。

边界约定（不可破坏）：

- 零匹配时，PTE/PIE 报 `null`（显示 unmatched），**绝不报 0.0**；
- 未匹配的真实峰值记为 `Missed`（一次 miss），**绝不记为 Timing = 0**。

---

## 阈值汇总

| Indicator | Key (JSON) | Threshold | 方向 |
|---|---|---|---|
| PTE — Peak Timing Error | `peak_timing_error_weeks` | ≤ 2.0 周 | 低越好 |
| PIE — Peak Intensity Error | `mean_peak_magnitude_rel_err` | ≤ 20.0 % | 低越好 |

已移除：~~Peak Hit `peak_hit_rate` ≥ 0.75~~、~~Direction `directional_accuracy` ≥ 0.60~~

---

## 输出物

- `results/ili/metrics/miflu_ili_peak_indicators.csv` — 逐峰值明细表
  （season, true/pred peak date, Δt, true/pred magnitude, rel-err%, status）。
- `results/ili/metrics/miflu_ili_peak_trend_summary.json` — 聚合指标 + `verdicts`
  块（`verdicts.{key}.value / threshold / verdict`），另含 STL 趋势强度
  （beta/zeta，属趋势强度诊断，与已删的 Direction 是不同概念，故保留）。
- `results/ili/metrics/miflu_verdict_table*.md` — 人类可读 verdict 表（ASCII，无竖线歧义）。

`verdict` 取值：`accurate` / `not accurate`。

---

## 实现位置

- `scripts/compute_miflu_indicators.py` — 指标计算（纯 CPU：pandas / numpy / scipy / statsmodels）。
- 峰值检测：`scipy.signal.find_peaks`，`prominence=0.08*(max-min)`，`distance=8`。
- 季节标签：Jul–Jun 流感季（如 2018-01 → `2017-2018`）。
- 日期解析：epiweek（YYYYWW）→ `datetime.fromisocalendar(y, w, 1)`（ISO 周一起点）。
- 早停：`scripts/early_stopping.py` 现为纯 `val_loss + patience`（双闸门已移除）。
