# A1 — 论文方法与数值复现判定：逐项证据表

生成时间：2026-09-26（Asia/Hong_Kong）。授权来源：用户本轮指令（完成原恢复计划中已授权、可独立执行的工作）。**不代表导师已批准。**

本文只做**证据判定**，不含任何新的 GPU 训练。四列含义：

| 列 | 含义 |
|---|---|
| **论文报告** | `MIFlu_paper.md` 中明确写出的内容（给出行号） |
| **仓库默认值** | 作者发布代码 `main_ILI_lora.py` argparse 的默认值（给出行号） |
| **发布代码实际行为** | 本轮**已执行**验证的行为（CPU 实测或字节级偏移分析），非静态推断 |
| **本项目 A2 实际** | A2 冻结协议下真正使用的值（`hashes_stage5_executed.json`） |

---

## 0. 判定摘要

| 结论 | 状态 |
|---|---|
| 论文是否给出了 epochs 与 learning rate | **否**。只写"set empirically (vary by base model)"（L298） |
| 发布代码默认值是否等于论文设置 | **否**。epochs 1、lr 1e-4，与项目 A2 的 20 / 5e-4 三者互不相同 |
| 发布代码是否应用 LoRA | **否**（`PEFT=0` 默认，L48；实测 100% 参数可训练） |
| 发布代码的 `freeze` 是否生效 | **否**（L58-61 只置 True 从不置 False；实测 82,705,944 / 82,705,944 可训练） |
| 发布代码的 Test 是否只覆盖 feature 0 | **是**（实测 `feat_id` 集合 = {0}） |
| 发布代码是否在训练中读 Test 并用 Test 选模型 | **是**（L211/225/264） |
| 论文的 token 顺序能否确定 | **否**，论文自身维度标注互相矛盾（L205 vs L219 vs L225） |
| A2 结果能否称为"复现论文" | **否**。A2 是修正重构；A0 诊断重放尚未跑 GPU |
| 论文 Table V 的 1.542/1.422/1.414/1.364 能否核对 | **是**，与 `MIFlu_paper.md` L318-324 逐项一致 |

---

## 1. 数据与变量

| 项 | 论文报告 | 仓库默认值 | 发布代码实际行为 | 本项目 A2 实际 |
|---|---|---|---|---|
| 数据来源 | National-Illness，"US 2002–2021"，七变量（L238） | `--data_path national_illness.csv`（L39） | 读到 966 行、列 `date,1,2,3,4,5,6,OT`（实测） | `paper_exact` 966 行，SHA-256 `31ffc169…b87a`，运行时逐次校验 |
| 七变量含义 | weighted ILI、unweighted ILI、age 0-4、age 5-24、ILITOTAL、providers、OT（L238） | 数字列名 `1..6,OT`，**无语义标签** | `target='OT'` 是第 7 列；语义靠 CSV 表头约定 | 语义化列名 + 冻结映射表（`author_966_profile.json`） |
| 划分比例 | 70:10:20（L238） | `Dataset_Custom` 整数规则（L257-259） | 实测 `num_train=676, num_vali=97, num_test=193`，borders `[0,572,669]/[676,773,966]` | **676/97/193**，与发布代码**完全一致** |
| 存储日期 | 2002–2021 | 直接用 CSV `date` 列 | 合成 7 天序列 2002-01-01…2020-06-30（Stage 2 已核） | 同上，未替换为流行病学周 |

**判定：划分一致。** A2 的 676/97/193 **不是**项目自创，而是与作者发布代码的整数规则逐项吻合。Stage 4 早期记录的"项目用 676/96/194"指的是旧 job 514859，不是本轮协议。

## 2. 输入 embedder 与切块

| 项 | 论文报告 | 仓库默认值 | 发布代码实际行为 | 本项目 A2 实际 |
|---|---|---|---|---|
| 输入 embedder 三层 | instance norm + patching + linear embedder（L178） | — | 实测 `in_layer = Linear(24→768)`；实例归一化在 forward 内（L109-112） | 同结构（`miflu_model.py`） |
| patch 长度 / stride | L_p=24, S=2（L301） | `--patch_size 24`、`--stride 2`（L72/79） | 一致 | Lp=24, S=2 |
| T（输入长度） | "previous 104 steps"（L508） | `--seq_len 104`（L50） | 一致 | T=104 |
| padding | 未说明 | `ReplicationPad1d((0, stride))`（L45） | 尾部补 1 个 stride，`patch_num` 再 +1（L46） | 同一约定 |
| DataEmbedding | 论文写的是 "linear embedder" | `from embed import DataEmbedding, DataEmbedding_wo_time`（L10） | **导入但从未使用**；真实投影是 `nn.Linear` | 不使用 |

## 3. 骨干、LoRA 与冻结

| 项 | 论文报告 | 仓库默认值 | 发布代码实际行为（实测） | 本项目 A2 实际 |
|---|---|---|---|---|
| 骨干层数 K | K=6（国别）（L299） | `--gpt_layers 6`（L62） | 实测 `llmmodel.h` 保留 **6 / 12** 个 GPT2Block | K=6 |
| 骨干 | GPT-2 | `--backbone gpt2`（L63） | `GPT2Model.from_pretrained('gpt2')`（L51） | 同 |
| LoRA rank | r=4（L300） | `--lora_r 4`（L46） | 值存在但 **`PEFT=0`（L48）→ L74-90 分支从不执行**；实测 `llmmodel` 是裸 `GPT2Model` | LoRA r=4 真实生效，73,728 参数 |
| LoRA 目标模块 | "only the multi-head attention layer"（L214） | `--target_modules ["c_attn"]`（L47） | 因 PEFT=0 而无效 | `c_attn`（W_Q/W_K/W_V） |
| 冻结策略 | "only PE and layer-normalization typically fine-tuned"（L214） | `--freeze 1`（L77） | **实测无效**：L58-61 只对含 `'ln'`/`'wpe'` 的名字置 `requires_grad=True`，**从不置 False**；结果 **82,705,944 / 82,705,944 = 100% 可训练**（含 wte+wpe 的 39,383,808） | GPT-2 冻结，仅 LoRA + 变体指定层解冻；trainable 1,030,056 |
| 文本编码器 | "full GPT2"（L303） | `--textmodel gpt2`（L64） | `text_emb_label_0507_{L}.txt`，四个 L 的文件**都存在**（实测 6.2 MB/个，shape (317,768)） | 同族文本编码器 |

## 4. 文本通路的 token 顺序 —— 本表最关键的一行

| 环节 | 论文 | 发布代码 | 本项目 A2 |
|---|---|---|---|
| 拼接顺序 | **无法确定**：L205 写 `R^{(len(token)+num(patches))×D}`（文本在前），L219 写 `R^{(num(patches)+len(token))×D}`（文本在后）—— 同一篇论文自相矛盾 | `cat((时间片, 文本))`（L139），即**文本在后** | 文本在前，时间片在后（`ModalityAligner`） |
| 截断 | L222 散文："the **token portion is discarded**"（丢弃文本）；L225 公式：`h_forecast[len(token):]` 被移除后剩 `num(patches)` 行 | `outputs[:, :self.patch_num, :]`（L145），即**丢弃文本、保留时间片** | 保留时间片 |
| 是否自洽 | **否**。若按 L205（文本在前）解释 L225 的下标，`len(token):` 切的是文本，剩 `num(patches)` 行成立但与 L219 的维度式冲突；若按 L219（时间在前）解释，则 L225 的下标切到了时间片，剩 `len(token)` 行，与宣称的 `num(patches)` 行不符 | 与 L222 的**散文意图**一致 | — |

**已执行的结构性结论（CPU 字节偏移 + 因果掩码分析）：**

发布代码的执行顺序是 `cat(5566) → llmmodel(5746) → truncate(5835)`，即先拼接、再过 LLM、最后截断。保留下来的 `patch_num` 个位置在序列中**全部位于文本 token 之前**；GPT-2 的因果注意力使靠前位置**不能**看到靠后位置。因此：

> **文本 token 在被读取之前，其输出就被丢弃；文本通路在发布实现中无法影响任何被读出的量。**
> 这不是"注意力恰好没用到"，而是"文本的输出根本没进入读出路径"。

同时这也说明：发布代码的截断**符合论文散文的意图**（丢弃 token portion），所以不能简单说"代码写错了"。真正的问题是**论文的公式无法确定 token 顺序**，而两种可能的顺序中，至少"时间在前"这一种在因果注意力下必然使文本失效。

> **A1 判定：论文的 token 顺序无法从论文确定（维度标注自相矛盾）；在"时间片在前"这一顺序下，文本通路按构造失效。要使文本真正生效，文本必须排在时间片之前。**

## 5. 训练与选模

| 项 | 论文报告 | 仓库默认值 | 发布代码实际行为 | 本项目 A2 实际 |
|---|---|---|---|---|
| epochs | **未给出**，只写"set empirically"（L298） | `--train_epochs 1`（L58） | 跑 1 个 epoch | 固定 20（无 early stopping） |
| learning rate | **未给出**（L298） | `--learning_rate 0.0001`（L55） | 1e-4 | 5e-4 |
| batch size | 未给出 | `--batch_size 16`（L56） | 16 | 16 |
| optimizer / scheduler | 未给出 | Adam（L159）+ `CosineAnnealingLR(T_max=10)`（L172），但仅当 `--cos 1`（默认 0） | 默认无 scheduler；`adjust_learning_rate` 仅 type1 分支（L234） | Adam，**无 scheduler**（已核实三个运行器均无） |
| 重复次数 | **10 repetitions**（L306） | `--itr 1`（L84） | 1 | 3 seeds（42/43/44） |
| 选模依据 | 未明确说明 | **用 Test MSE 选**（L211 `test(...)` 每 epoch；L225 `if mse_temp < min_mse`；L264 保存该 `model_state`） | Test 参与选模 | **只用验证集七变量标准化 MSE** |
| early stopping | 未提及 | 实例化但**调用被注释**（L235-236） | 不生效 | 禁用，固定 20 epoch |
| checkpoint | 未提及 | `checkpoints/<setting>/checkpoint.pth` | 保存 Test 最优权重 | 每 (model,L,seed) 独立 per-seed 文件 + SHA-256 锁定 |

**A1 判定：论文的 epochs / lr / batch / optimizer / scheduler 均未给出。** 因此"20 epoch、lr 5e-4"是**项目假设**，不是论文值；发布代码的"1 epoch、lr 1e-4"也不是论文值。三者互不相同，A1 必须把它们并列为三种状态，不能把任何一种说成"作者实用配置"。

## 6. 评价口径

| 项 | 论文 | 发布代码 | 本项目 A2 |
|---|---|---|---|
| Test 覆盖面 | 声称七变量国别结果 | **只测 feature 0**（实测 `feat_id={0}`；`__len__` 对 test 不乘 `enc_in`，L312-316） | 七变量全部 |
| 样本组织 | 未说明 | 逐特征**单变量样本**（`seq_x` 取单列，L305-306），train/val 覆盖 7 个特征但从不联合 | 联合七变量 |
| 指标 | MSE/MAE（Table V）；Fig.7 用 ILITOTAL | 单特征 MSE/MAE | 七变量标准化 MSE/MAE 为主，ILITOTAL 单列 |
| 重复聚合 | 10 次平均 | `itr=1` | 3 seed 平均后再对 4 个 L 等权平均 |

## 7. 论文数值核对（Table V，国别，MIFlu 列）

| L | 论文 MSE | 论文 MAE | 本项目核对 |
|---:|---:|---:|---|
| 24 | **1.542** | **0.726** | 与 `MIFlu_paper.md` L318-319 一致 |
| 36 | **1.422** | **0.779** | 与 L320-321 一致 |
| 48 | **1.414** | **0.757** | 与 L322-323 一致 |
| 60 | **1.364** | **0.719** | 与 L324 一致 |
| 等权平均 | **1.4355** | 0.7453 | 由上表算出 |

A2 实测 MIFlu：2.4439 / 1.9360 / 1.7677 / 2.0184，等权平均 **2.0415**，约为论文值的 **1.42×**。

**必须同时声明的三点：**
1. A2 用 3 seeds，论文用 10 repetitions，聚合口径不同。
2. A2 是**修正重构**（文本通路真实生效、验证集选模、七变量联合、`strict` 窗口），**不是**作者发布代码的重放（A0）。
3. 因此 1.42× 的差距**既不能**判定为"已复现"，也**不能**判定为"已推翻"。A0 的作用正是把这个差距分解为"实现差异"与"作者实际跑的配置未知"两部分。

## 8. 无法核验的具体原因（A1 的诚实边界）

| 待核验项 | 为什么无法核验 |
|---|---|
| 作者实际使用的 epochs / lr | 论文明写"set empirically"且不给值；仓库默认 1 / 1e-4 与项目 20 / 5e-4 都无法被证实为作者实用值 |
| token 顺序 | 论文 L205 与 L219 的维度标注互相矛盾，L225 的下标与两者都不自洽 |
| 完整 prompt 原文 | `text_emb.ipynb` 用占位 prompt（"Text from users"），缓存文件名与 loader 期望不一致（Stage 2 已核） |
| 文本嵌入的生成参数 | 分词器、模型 revision、max_len、生成设置均未随仓库提供；本轮只验证了文件存在且 shape=(317,768) |
| Table V 其余 12 个模型 | 论文 §V.C 明写基线结果**引自既往文献**，仓库不含其代码，无法在本协议下重算 |
| 10 次重复的方差 | 未提供每次重复的数值，只有 10 次均值 |

## 9. A1 结论

**允许的表述：**
- 发布代码在 2025-03 的 commit `6ed2101` 上，与论文的**部分**描述一致（K=6、r=4、Lp=24、S=2、T=104、70:10:20 且整数规则给出 676/97/193），与论文的另**部分**明确冲突（LoRA 未启用、冻结无效、Test 只覆盖 feature 0、用 Test 选模）。
- 论文的 token 顺序标注自相矛盾；在"时间片在前"的顺序下文本通路按构造失效。
- A2 的 676/97/193 与作者发布代码一致；A2 的 MIFlu 主指标为论文 Table V 均值的 1.42×。

**不允许的表述：**
- 不允许说"已复现论文"或"已推翻论文"。
- 不允许把 20 epoch / lr 5e-4 说成论文配置。
- 不允许把 A2 与旧 1,025 行结果拼成同一排名。
- 不允许把"发布代码的文本通路失效"推广为"论文的文本通路失效"—— 论文公式无法确定顺序，因此只能说在已知的两种顺序之一下必然失效。
