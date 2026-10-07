# SCORING CORRECTION NOTE

日期：2026-10-06　　性质：**只追加更正，不覆盖任何旧文件**。

---

## 1. 被更正的对象

`hpc_results/stage6/scoring/paired_stats.py`（由作业 587385 的评分流程写出 `paired_stats.txt`）。

该文件在表头自述：

```
  negative mean means A is better; n_win = cells where A beats B
```

**但计数器在相反的条件下自增。** 即：它打印的 `n_win` 统计的是 **A 输掉** 的格数。

---

## 2. 实测差异

| 行（原文） | 文件中的 `n_win` | 正确值 | 关系 |
|---|---:|---:|---|
| `miflu - nlinear`  mean=−0.0080 t=−0.11 | 5/12 | **7/12** | 12 − 5 = 7 ✅ |
| `notext - nlinear` mean=−0.1274 t=−2.28 | 1/12 | **11/12** | 12 − 1 = 11 ✅ |
| `notext - miflu`   mean=−0.1194 t=−1.50 | 5/12 | **7/12** | 12 − 5 = 7 ✅ |
| `miflu - dlinear`  mean=−0.3063 t=−3.36 | 3/12 | **9/12** | 12 − 3 = 9 ✅ |

**在全部行上，正确值 = 12 − 文件值**，与「计数条件取反」的假设完全一致（无例外，故不是随机误差）。

---

## 3. 影响范围（重要：只影响叙述，不影响数值）

| 项目 | 是否受影响 |
|---|---|
| 每格 MSE / MAE | ❌ 不受影响 —— 与独立重算吻合至 1.5e-07 |
| 每模型 `average_MSE_4L` | ❌ 不受影响 |
| 排名 | ❌ 不受影响 |
| 均值差 `mean` | ❌ 不受影响 |
| t 统计量 | ❌ 不受影响 |
| **胜场计数 `n_win`** | ✅ **受影响（方向取反）** |
| **引用该计数的叙述** | ✅ **受影响** |

### 具体污染的报告

`recovery/stage6/results_report_zh.md` **§0** 写：

> 「MIFlu 与 NLinear 这两个模型在 12 个配对格上完全不可分（t = −0.11，**5/12 胜**）」

**应为「7/12 胜」。**

而**同一份报告 §4.3** 写：

> 「no-text 优于 NLinear（t=−2.28，**11/12**）」

**是正确的**。即同一份报告在两处使用了互相矛盾的计数，其中 §0 采用了被反掉的那个。

> 注意：`paired_stats.txt` 中 `notext - nlinear` 写的是 `1/12`，而报告 §4.3 写的是 `11/12` —— 报告作者在一处修正了、在另一处没有。

---

## 4. 本轮的处理

1. **未修改** `paired_stats.py`、**未修改** `paired_stats.txt`、**未修改** `results_report_zh.md`（遵守「不覆盖旧结果」规则）。
2. 新建 `scripts/paired_stats_corrected.py`：修正计数方向，并加入 **4 项 unit test**（见下）。
3. 输出 `paired_stats_corrected.csv` / `paired_stats_corrected.md`（基于独立 scorer 的 `indep_scorer_cells.csv`）。

### Electron unit tests（`python scripts/paired_stats_corrected.py --self-test`）

| 用例 | 构造 | 期望 | 结果 |
|---|---|---|---|
| 1 | A 每格严格更低 | A wins all cells | ✅ PASS（4/4） |
| 2 | A 每格严格更高 | A wins zero cells | ✅ PASS（0/4） |
| 3 | 混合 `[-0.4,+0.6,-0.2,+0.1,-3.0,0.0]` | 手算 A=3, B=2, tie=1, mean=−0.483333 | ✅ PASS |
| 4 | **回归守卫**：真实 `miflu−nlinear` 的 12 个格差 | 正确=7；旧式反计数=5 | ✅ PASS |

同时断言不变式 `wins_A + wins_B + ties == n_cells`，对每个真实配对都成立。

---

## 5. 更正后的配对表（摘要）

| A | B | mean diff | t | **A wins** | B wins | ties |
|---|---|---:|---:|---:|---:|---:|
| miflu | nlinear | −0.0080 | −0.11 | **7** | 5 | 0 |
| notext | nlinear | −0.1274 | −2.28 | **11** | 1 | 0 |
| notext | miflu | −0.1194 | −1.50 | **7** | 5 | 0 |
| miflu | dlinear | −0.3063 | −3.36 | **9** | 3 | 0 |
| dlinear | nlinear | +0.2983 | +8.51 | 0 | 12 | 0 |
| timecma_llm | nlinear | +0.6205 | +10.94 | 0 | 12 | 0 |
| patchtst | nlinear | +1.8709 | +39.16 | 0 | 12 | 0 |
| itransformer | nlinear | +1.9351 | +31.47 | 0 | 12 | 0 |
| qwen_time_llm | nlinear | +3.1700 | +21.66 | 0 | 12 | 0 |
| calf_llm | nlinear | +3.4658 | +46.63 | 0 | 12 | 0 |

---

## 6. 需要在正式报告中如何表述

**改为**：「MIFlu 在 12 个配对格中 **7 格**优于 NLinear，但配对差均值仅 −0.0080（t = −0.11），**统计上不可分**；且胜负随预测长度翻转（L=24 三格全负，L=36/48/60 多数为正）。」

**不要**再用「5/12 胜」。

---

## 7. 证据路径

| 项 | 路径 |
|---|---|
| 修正后脚本（含 unit test） | `scripts/paired_stats_corrected.py` |
| 独立 scorer 的逐格数据 | `indep_scorer_cells.csv` |
| 修正后配对表 | `paired_stats_corrected.csv` / `.md` |
| **有 bug 的原文件（未被修改）** | `hpc_results/stage6/scoring/paired_stats.py` / `paired_stats.txt` |
| 被污染的报告段落 | `recovery/stage6/results_report_zh.md` §0（§4.3 正确） |