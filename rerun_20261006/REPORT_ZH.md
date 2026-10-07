# 2026-10-06 独立重算报告：LLM vs 非 LLM 对比重跑

**本轮性质**：只读 + CPU 重算 + 新建审计文件。未启动任何训练，未改动任何旧数据、checkpoint、协议或报告。
**脚本**：`rerun_20261006/llm_vs_nonllm_recompute.py`（审计方自写，不 import 项目任何评分模块）
**产物**：`recomputed_A_average_mse_4L.csv`、`recomputed_B_average_mse_4L.csv`、`group_means.csv`、`paired_vs_nlinear.csv`、`recompute_summary.json`

---

## 1. 重算的忠实度：PASS

| 检查 | 结果 |
|---|---|
| A 轨从 116 个原始 `(pred, target)` NPZ 逐格重算 MSE | **116/116 与项目 `score_matrix.csv` 吻合** |
| 最大相对差 | **1.527e-07** ≈ float32 机器精度（1.19e-07） |
| B 轨从 320 行 seed 级表重新聚合 | 与 `model_ranking.csv` 逐项一致 |

结论：**已产出的数值本身可信**，本轮重跑不是要推翻它们，而是把「LLM vs 非 LLM」这一比较用审计方自己的代码从原始张量重建一遍，并核对分组口径。

---

## 2. 重跑结果：A 轨（作者 966 行数据，3 seeds × 4 horizons）

| 排名 | 模型 | 族 | average_MSE_4L | 12 格 sd |
|---:|---|---|---:|---:|
| — | notext（MIFlu 去文本） | 对照 | **1.922158** | 0.2069 |
| 1 | miflu | LLM | 2.041519 | 0.2838 |
| 2 | nlinear | non-LLM | 2.049550 | 0.0736 |
| — | seasonal_naive | 基线 | 2.268799 | — |
| 3 | dlinear | non-LLM | 2.347832 | 0.0895 |
| 4 | timecma_llm | LLM | 2.670009 | 0.1912 |
| 5 | patchtst | non-LLM | 3.920470 | 0.1400 |
| 6 | itransformer | non-LLM | 3.984699 | 0.1791 |
| 7 | qwen_time_llm | LLM | 5.219555 | 0.4840 |
| 8 | calf_llm | LLM | 5.515300 | 0.2371 |
| — | last_value_naive | 基线 | 7.165831 | — |

**分组均值**

| 口径 | LLM 组 | 非 LLM 组 | 差 |
|---|---:|---:|---:|
| **4 vs 4** | **3.861596**（miflu/timecma/qwen/calf） | **3.075638**（nlinear/dlinear/patchtst/itransformer） | **+0.785958** |
| 3 vs 5 | 4.468288（n=3，仅 `*_llm`） | 2.868814（n=5，含 miflu） | +1.599474 |

**配对差（12 个 (L, seed) 格）**

| 对比 | 均值差 | t | 谁更好 |
|---|---:|---:|---|
| miflu − nlinear | −0.0080 | −0.11 | **不可分** |
| notext − nlinear | −0.1274 | −2.28 | notext 更好 |
| notext − miflu | −0.1194 | −1.50 | 不显著 |
| timecma/qwen/calf − nlinear | +0.62 / +3.17 / +3.47 | +10.9 / +21.7 / +46.6 | 显著更差 |

---

## 3. 重跑结果：B 轨（July-2026 快照 1025 行，10 seeds × 4 horizons）

| 排名 | 模型 | 族 | average_MSE_4L |
|---:|---|---|---:|
| 1 | gpt2_miflu | LLM | **0.770872** |
| 2 | nlinear | non-LLM | 1.069767 |
| 3 | patchtst | non-LLM | 1.075951 |
| 4 | dlinear | non-LLM | 1.170933 |
| 5 | timecma_llm | LLM | 1.181449 |
| 6 | itransformer | non-LLM | 1.252982 |
| 7 | qwen_time_llm | LLM | 1.253096 |
| 8 | calf_llm | LLM | 1.764871 |

| 口径 | LLM 组 | 非 LLM 组 | 差 |
|---|---:|---:|---:|
| **4 vs 4** | **1.242572** | **1.142408** | **+0.100164** |
| 3 vs 5 | 1.399805 | 1.068101 | +0.331704 |

---

## 4. 必须如实报告的张力（两轨方向相反）

| | A 轨（作者 966） | B 轨（July 1025） |
|---|---|---|
| 组均值 | LLM 更差（+0.786） | LLM 更差（+0.100） |
| 组内第 1 名 | **notext（非 LLM 对照）** | **gpt2_miflu（LLM）** |
| MIFlu vs NLinear | 不可分（t=−0.11） | MIFlu 大幅领先（0.771 vs 1.070） |

**组均值与组内最优给出相反印象。**只报组均值 = 暗示 LLM 更弱；只报组内最优 = 暗示 LLM 更强。两者都是选择性报告。
**两轨数字绝不可直接横比**：数据不同、种子数不同（3 vs 10）、Test 窗内容不同，A 轨 2.0415 与 B 轨 0.7709 相差 2.6 倍纯属口径差异。

---

## 5. 本轮新发现：项目 `paired_stats.txt` 的胜场计数是反的

`hpc_results/stage6/scoring/paired_stats.txt` 的 `n_win` 列自述为「cells where A beats B」，实际统计的是 **A 输** 的格数：

| 行 | 文件中写 | 我重算 |
|---|---|---|
| `miflu - nlinear` | mean=−0.0080, t=−0.11, **A better in 5/12** | miflu 胜 **7/12** |
| `notext - nlinear` | mean=−0.1274, t=−2.28, **A better in 1/12** | notext 胜 **11/12** |
| `miflu - dlinear` | mean=−0.3063, t=−3.36, **A better in 3/12** | miflu 胜 **9/12** |

**均值差与 t 值全部正确，只有胜场计数反了。**

- 影响：`recovery/stage6/results_report_zh.md` **§0 引用「5/12 胜」**（来自该列），而**同报告 §4.3 又写「11/12」**（正确值）。同一份报告内自相矛盾。
- 定性：**报告层计数错误，不是数值错误**，不改动任何 MSE、均值、t 值或排名。
- 建议：修 `paired_stats.py` 的计数方向，或在报告中改述为「miflu 在 12 格中 7 格优于 NLinear」。

逐格明细（miflu vs nlinear）：

| L | seed | miflu | nlinear | 差 | 胜者 |
|---:|---:|---:|---:|---:|---|
| 24 | 42 | 2.4695 | 2.0857 | +0.3837 | nlinear |
| 24 | 43 | 2.5031 | 2.1434 | +0.3598 | nlinear |
| 24 | 44 | 2.3592 | 2.0734 | +0.2858 | nlinear |
| 36 | 42 | 1.8422 | 2.0423 | −0.2001 | miflu |
| 36 | 43 | 1.8275 | 1.9976 | −0.1701 | miflu |
| 36 | 44 | 2.1383 | 2.0431 | +0.0952 | nlinear |
| 48 | 42 | 1.7091 | 2.0278 | −0.3188 | miflu |
| 48 | 43 | 1.6881 | 1.9710 | −0.2829 | miflu |
| 48 | 44 | 1.9060 | 2.0109 | −0.1050 | miflu |
| 60 | 42 | 2.1728 | 1.9846 | +0.1882 | nlinear |
| 60 | 43 | 1.9032 | 2.2238 | −0.3206 | miflu |
| 60 | 44 | 1.9793 | 1.9908 | −0.0115 | miflu |

**符号随 L 翻转**：L=24 全部输给 NLinear；L=36/48/60 多数赢。**单一 L 上的胜负不能外推**，这也解释了为什么 12 格平均后「不可分」。

---

## 6. 措辞边界

**可以说**
- 「在作者 966 行数据、z 空间、3 种子协议下，四 LLM 实现组均值 3.8616 劣于四非 LLM 组均值 3.0756（差 +0.786）。」
- 「在 July-2026 快照、10 种子协议下，四 LLM 组均值 1.2426 劣于四非 LLM 组均值 1.1424（差 +0.100），但组内最优者为 LLM 模型 gpt2_miflu（0.7709）。」
- 「MIFlu 与 NLinear 在 12 个配对上不可分（t=−0.11，7/12 格 MIFlu 更优）。」
- 「该比较是**两个预先指定的固定实现集合**的描述性对比，4 个/4 个实现不是随机样本。」

**不可以说**
- ❌ 「LLM 模型整体更强」或「整体更弱」——两轨方向不一致，且组均值与组内最优互相矛盾。
- ❌ 「我们复现了论文的 1.4355」——A 轨 2.0415 是不同度量口径。
- ❌ 「文本通路对 MIFlu 有增益」——A0 GPU 与 Stage 2 CPU 的重放结论相反，矛盾未解（P0）。
- ❌ 直接横比 A 轨与 B 轨的任何数字。

---

## 7. 证据路径

| 类别 | 路径 |
|---|---|
| 本轮重算脚本 | `rerun_20261006/llm_vs_nonllm_recompute.py` |
| 本轮产物 | `rerun_20261006/*.csv`、`recompute_summary.json` |
| A0 GPU 逐字重放证据 | `results/stage6/a0_gpu/`、`hpc_results/stage6/` |
| A 轨原始预测张量 | `audit_20260930/predictions_stage6/*.npz`（116）、`hpc_results/stage5_a2/scoring/predictions/*.npz`（44） |
| B 轨 seed 级表 | `results/v3_clean/analysis/primary_seed_level.csv`（320 行） |
| 项目评分表（被核对对象） | `hpc_results/stage6/scoring/score_matrix.csv` |
| 胜场计数错误的文件 | `hpc_results/stage6/scoring/paired_stats.txt` |