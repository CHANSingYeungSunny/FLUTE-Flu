# HYPERPARAMETER PROVENANCE

日期：2026-10-06　　目的：解决「20 epochs / lr 5e-4 究竟是论文设置、作者实用设置，还是项目自定假设」这一长期冲突。

---

## 0. 结论（一句话）

**论文从未给出 epochs 与 learning rate 的数值。** 恢复计划与 CodeBuddy 执行提示词中「论文：20 epochs, lr 0.0005」的写法是**把项目自定假设误标成了论文值**。A2 实际执行的 20 ep / 5e-4 是 **reconstructed assumption**，**不得**归给原作者或论文。

---

## 1. 三方证据对照

| 参数 | **论文正文**（一手证据） | **作者发布代码默认值**（一手证据） | **项目 A2 实际执行** |
|---|---|---|---|
| training epochs | **未披露** | `--train_epochs` default **1**（`main_ILI_lora.py` L58） | **20**（固定，无早停） |
| learning rate | **未披露** | `--learning_rate` default **0.0001**（L55） | **0.0005** |
| optimizer | **未披露** | `optim.Adam`（入口脚本） | Adam |
| scheduler | **未披露** | `--lradj type1` + `--decay_fac 0.75`，**实测生效**（指数衰减，A1 日志 606378 出现 `Updating learning rate to 0.0001937…`）；`--cos 1` 才改走 CosineAnnealingLR | 无 scheduler |
| weight decay | **未披露** | 未显式设置 → 0 | 0 |
| batch size | **未披露** | `--batch_size` default **16**（L56） | 16 |
| dropout | **未披露** | `--dropout` default **0.2**（L69） | （沿用模型定义） |
| repetitions | **10**（明写） | `--itr` default **1**（L84） | A2 = **3 seeds** |
| backbone layers K | **6**（national，明写） | `--gpt_layers` default 6（L62） | 6 |
| LoRA rank r | **4**（明写） | `--lora_r` default 4（L46） | 4（**真实生效**） |
| LoRA target modules | "multi-head attention layer"（明写） | `["c_attn"]`（L47） | `c_attn` |
| patch length Lp | **24**（明写） | `--patch_size` default 24（L72） | 24 |
| stride S | **2**（明写） | `--stride` default 2（L79） | 2 |
| text embedder | **full GPT-2**（明写） | `--textmodel gpt2`（L64） | 同 |
| seq_len T | 104（Section 引文"previous 104 steps"） | `--seq_len` default 104（L50） | 104 |
| split | 70:10:20（明写） | `Dataset_Custom` 整数规则 | 676/97/193 |
| env | Python 3.9.18, PyTorch 2.1.0, RTX 3090（明写） | — | HPC A100 / 本地 Windows |

### 论文原文（PDF 抽取，`audit_20260930/paper_text.txt` L601-603）

> "We set the number of training epochs and the learning rate for MIFlu empirically because the hyperparameters vary depending on the base model."

对应 `MIFlu_paper.md` L298：

> "Training epochs and learning rate were set empirically (vary by base model)."

**该句是论文关于 epochs / lr 的全部内容 —— 没有任何数字。**

---

## 2. 「20 epochs / 5e-4」的错误来源（可定位）

恢复计划与执行提示词把它写成论文值：

| 文件 | 行 | 原文 | 判定 |
|---|---|---|---|
| `EE4080_MIFlu_Research_Recovery_Plan.md` | 161 | `\| Optimization \| Paper: 20 epochs, batch size 16, learning rate 0.0005; ...` | ❌ **错误标注**：标签写 "Paper:"，但论文未披露 |
| `CodeBuddy_MIFlu_Recovery_Prompt.md` | 63 | "Recover the national paper contract: ... **20 epochs**; batch 16; **learning rate 0.0005**; ten repetitions." | ❌ 把假设并入 "paper contract" |
| `CodeBuddy_MIFlu_Complete_Recovery_Plan_ZH.md` | 31 | "…LoRA rank 4 与可训练模块、**20 epochs**、batch 16、**学习率 0.0005**、十次重复…" | ❌ 同上 |
| `CodeBuddy_MIFlu_Current_Progress_Audit_Prompt.md` | 71 | **「历史记录对"20 epochs / 5e-4 是论文设置还是 A2 自定设置"存在冲突，必须解决」** | ✅ **本轮解决的正是这一项** |
| `CodeBuddy_Authorization_and_Final_Execution_ZH.md` | 31 | **「A2 的 20 epochs、5e-4 及 batch 16 不得归到原作者设置」** | ✅ 正确 |

**结论**：这是**计划文档层的标注错误**。论文与作者代码都没有支持 20/5e-4。数值本身也可能巧合合理，但**巧合不等于出处**。

---

## 3. A1 的 minimum reconstruction（预先声明，不做 accuracy hunting）

由于 epochs / lr **UNRECOVERED**，A1 必须声明单一重建方案。**以下为本轮预先声明的选择，理由基于可核验证据，且不得因结果不接近论文而更改：**

| 参数 | A1 采用值 | 状态 | 选择依据 |
|---|---|---|---|
| epochs | **20** | **reconstructed assumption** | 沿用 A2 值以保持 A1/A2 可比；论文未披露 |
| learning rate | **5e-4** | **reconstructed assumption** | 同上；作者默认 1e-4 亦无证据支持为实用值 |
| optimizer | Adam | reconstructed assumption | 发布代码使用 Adam；论文未披露 |
| scheduler | 无 | reconstructed assumption | 论文未披露；发布 `lradj=type1` 在默认路径不生效 |
| batch size | 16 | released default | 发布代码默认 16，且与 A2 一致 |
| seed 列表 | 42–51（10 个） | declared | 论文只写"10 repetitions"，未给 seed；本项目声明自己的 seed 列表 |
| checkpoint rule | validation-only 选模 | corrected | 发布代码用 Test 选模（缺陷，见 DEVIATION_LEDGER D-03） |

**明确禁止**：试多组 epochs/lr 然后挑最接近论文 1.4355 的一组。任何此类行为必须记为 accuracy hunting 并作废。

**单一替代方案（若必须对照作者默认值）**：另跑一组 `--train_epochs 1 --learning_rate 1e-4`（= 发布代码默认值）作为**独立的 A0 完整重放配置**，与 A1 并列报告，**不混入 A1 的均值**。

---

## 4. 论文目标的正确读取（避免口径混淆）

| 项 | 值 | 来源 |
|---|---|---|
| L=24 MSE / MAE | 1.542 / 0.726 | Table V |
| L=36 | 1.422 / 0.779 | Table V |
| L=48 | 1.414 / 0.757 | Table V |
| L=60 | 1.364 / 0.719 | Table V |
| 四档算术均值 | 1.4355 / 0.74525 | 由 Table V 计算 |
| 论文自己的舍入表述 | 1.436 / 0.745 | Table VIII |

**重要限定**：论文 §V-C 明写：

> "Results for the national and regional ILI forecasting models are taken from **[9]** and **[14]**, respectively."

即 Table V 的**对比基线**列（GPT4TS / DLinear / PatchTST / …）是**引用自文献 [9]/[14]，不是重跑**。**MIFlu 自身那一列是否也含引用成分，论文没有说明清楚**。任何「复现 Table V」的主张都必须先声明这一点。

---

## 5. 对未来运行的约束

1. A1 的配置必须带 `HYPERPARAMETER_PROVENANCE` 标签：`paper_disclosed` / `released_default` / `reconstructed`。
2. 任何报告表格中含 reconstructed 参数的单元格，必须加注 `†`。
3. 不得再出现「Paper: 20 epochs, lr 0.0005」这类写法。
4. `author_paper_targets.csv` 只放论文值；复现值另表（`reproduction_results_*.csv`），两表**不得合并**。

---

## 6. 证据路径

| 类别 | 路径 |
|---|---|
| 论文 PDF 文本抽取 | `audit_20260930/paper_text.txt` L601-603 |
| 论文 markdown | `MIFlu_paper.md` L290-306 |
| 作者 argparse 默认值 | `recovery/author_repo/main_ILI_lora.py` L34–L85 |
| A1 逐项证据表（前序工作） | `recovery/a1/a1_evidence_table_zh.md` |
| 错误标注的源头 | `EE4080_MIFlu_Research_Recovery_Plan.md` L161；`CodeBuddy_MIFlu_Recovery_Prompt.md` L63 |
| A2 实际执行值 | `recovery/stage5/hashes_stage5_executed.json`、`recovery/stage5/results_report_zh.md` §2 |