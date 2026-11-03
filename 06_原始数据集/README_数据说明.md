# 06_原始数据集/ 里面是什么

**这是最原始的输入数据——所有结论都建立在它上面。**

## raw/ —— 真实数据（966 周 × 7 个指标）

| 文件 | 是什么 |
|------|--------|
| `national_illness_author_repo_966.csv` | **主数据**，和原论文用的完全一致（逐字节相同） |
| `national_illness_raw.csv` | 原始下载版（未处理） |
| `national_illness_raw_paper_exact.csv` | 论文精确版 |
| `us_region_raw.csv` | 美国分区域数据 |
| `COLUMN_MAP_national_illness.csv` | 列名对照表 |

## 7 个指标（列）是什么

| 列号 | 名称 | 意思 |
|------|------|------|
| 0 | % WEIGHTED ILI | 加权流感样病例百分比 |
| 1 | % UNWEIGHTED ILI | 未加权流感样病例百分比 |
| 2 | AGE 0-4 | 0-4 岁病例数 |
| 3 | AGE 5-24 | 5-24 岁病例数 |
| 4 | **ILITOTAL** | **流感样病例总数**（峰值预测看这个） |
| 5 | NUM. OF PROVIDERS | 上报的医疗机构数 |
| 6 | OT | 门诊总量 |

## 两个 JSON 文件（代码要用，别删）

| 文件 | 用途 |
|------|------|
| `scaler_miflu_author966.json` | 归一化参数（把数据压到标准尺度） |
| `scaler_miflu_national.json` | 同上，全国版 |

**归一化是什么**：把不同量级的指标（百分比 vs 数万病例数）都转到同一个尺度，
让模型能公平比较。JSON 里存的就是转换用的均值和标准差。

---

## 名词解释（你问的）

- **raw** = 原始数据（没加工过的）
- **ili** = Influenza-Like Illness，流感样病例（原本有个空文件夹，已挪走）
- **legacy** = 遗留的旧版本（已挪到 `99_旧文件存档/`）
