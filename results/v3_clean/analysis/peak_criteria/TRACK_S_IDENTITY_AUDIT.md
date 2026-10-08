# Track S 身份审计（Identity Audit）

*审核"Track S"标签在项目中的每一次出现，确定其含义，并给出最终报告的处理决策。*

## 1. 搜索结果：项目内存在两种互不相干的 "S-track"

| 含义 | 出现位置 | 是否结果轨道 |
|---|---|---|
| **停止准则敏感性补充实验**（patience=5 早停） | `scripts/s1_*.py`、`S1_EARLYSTOP_PROTOCOL.md`、`s1_earlystop.sbatch`、`s1_batch_driver.sh`（作业名 `s1es`） | 是（补充方法） |
| **存储基础设施轨道**（checkpoint 存储 S0–S5） | `STORAGE_TRACK_S0_S1.md`、`storage_guard.py`、`HPC_STORAGE_READY_VERDICT.md` | 否（基础设施，陈旧标签） |
| A/B/C 实验轨道分离 | `TRACK_SEPARATION_RULES.md`（此处 "track" 指实验轨道，非 Track S） | 上下文，非 Track S |

> 因此"Track S"在本项目中**没有单一稳定含义**，这正是必须审计的原因。
> 与最终报告结论相关的只有第一种（停止准则补充实验）。

## 2. 与最终报告相关的 "Track S" 定义

- 数据集：**author-966（与 Track C 完全相同）**。
- 代码路径：`s1_earlystop_train.py`（由 Track C 训练脚本打补丁生成，仅加入 patience 早停）。
- 结果目录：`s1_earlystop_20261008/`（独立于 Track C 的 `r1_v2_verification_20261007/`）。
- 结果：12 次拟合全部 rc 0；11/12 与 Track C 冠军结果**完全相同到 6 位小数**；
  仅 L60/seed43 因早停在 epoch 3 局部谷回滚而 +0.144（见 `S1_EARLYSTOP_PROTOCOL.md` §7）。

## 3. 判定

- 与最终报告结论相关的 Track S = **TRACK_S_IS_SENSITIVITY_AND_SUPPLEMENTARY**。
- 存储 "S-track"（S0–S5）= **TRACK_S_IS_STALE_LABEL**（基础设施，不应出现在最终报告正文）。
- "track separation" 中的 track = 实验轨道 A/B/C，**不是 Track S**。

## 4. 结论

停止准则补充实验（Track S）在科学上**不独立于 Track C**：它使用相同数据、相同模型、
相同评分，仅改变停止规则，且结论是该规则**不改变冠军排名**。因此：
- 它**不是**第四个主要结果轨道；
- 必须归入**补充方法 / 限制**章节，而非主结论；
- 存储 "S-track" 标签与结果无关，最终报告不得引用。

> 详见 `TRACK_S_FINAL_REPORT_DECISION.md` 与 `TRACK_S_REFERENCE_MAP.csv`。
