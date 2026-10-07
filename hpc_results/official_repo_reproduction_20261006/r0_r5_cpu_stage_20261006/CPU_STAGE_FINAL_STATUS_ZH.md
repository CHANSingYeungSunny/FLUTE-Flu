# CPU 阶段最终状态报告（中文）

生成时间：2026-10-06。**本轮为纯 CPU/轻量阶段，未提交任何 GPU 作业。**

---

## 1. 新的 append-only 输出目录

```
hpc_results/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/
```

---

## 2. 论文身份与三源交叉核对

| 来源 | SHA-256 | 角色 |
|---|---|---|
| **PDF** | `7735a4388145dd2aced536417f7a4f50dafe21ed0d4fca64baa2b20f2e27885c` | 原始存档（12 页） |
| **Markdown（新）** | `6488a76b564d0b587ec01902848371d054b00bf2b941e289b2cd5d2483e39edd` | 主要结构化来源（466 行，27 个标题，**含全部 10 个表**） |
| 旧 `MIFlu_paper.md` | — | 已废弃（缺 Table IV，且无任何表值） |

### ⚠️ 结构性发现

**PDF 的表格数值全部是图片**：`find_tables()` 在 12 页上均返回 **0 个表**；`1.542`、`1.422`、`1.364`、`1.4355`、`0.74525` 在文本层出现次数**均为 0**。因此所有表值必须**读渲染图**。

### 三源核对结果

| 项 | PDF 图像 | 新 Markdown | 旧转录 | 判决 |
|---|---|---|---|---|
| **Table V**（8 个 MIFlu 值） | ✅ | ✅ | ✅ | **三源一致 → `MARKDOWN_PDF_CROSS_VERIFIED`** |
| **Table VIII**（消融 14 值） | ✅ | ✅ | ✅ | 交叉验证一致 |
| **Table IV 超参数** | ✅ **唯一来源** | ❌ 明确声明不可提取 | ❌ 完全缺失 | **`PDF_VISUALLY_VERIFIED`（单源）** |
| Table II / III 描述统计 | ❌ 未渲染 | ❌ 声明不可提取 | ❌ 缺失 | **`UNREADABLE`** |

### ⚠️ Table IV 更正了一条此前的错误结论

**PDF 第 7 页图像**读出 Table IV 的设置块：

| 设置 | National ILI |
|---|---|
| L | 24, 36, 48, 60 |
| **Epochs** | **20** |
| **Batch size** | **16** |
| **Learning rate** | **0.0005** |
| T | 104 |

**此前几轮断定「论文未披露 epochs 与 lr」，并把项目的 20/5e-4 定为无出处的 `RECONSTRUCTED_ASSUMPTION` —— 这是错的。** 出处就是 Table IV。原因：新 Markdown 明说该表不可提取、只给了模型名；旧转录完全省略了 Table IV。

**更正后的分类**：epochs / batch / lr / T = **`PAPER_EXPLICIT`（经 Table IV）**。
**仍然真正 `UNRECOVERED` 的**：optimizer、scheduler、seed 列表、checkpoint 选择规则、pooling 轴。

---

## 3. 论文编号核对结果

**预期的 II、IV、V、VI、VII、VIII、IX、X 与 Figures 3、5、6、7 全部正确**，并额外发现：

| 项 | 说明 |
|---|---|
| **Table I** | 输入文本提示模板（p4）——简报未列 |
| **Table III** | US-Region 描述统计（p6 引用、p5 印刷）——简报未列 |
| 图引用格式 | 用 `Fig. N`，字面 "Figure" 出现 **0** 次 |
| 全国划分 | **70:10:20**（与代码的 676/97/193 一致） |
| 区域划分 | **50:10:40**（简报未察；仅适用于 US-Region） |

**未读取的论文单元**：Table II、Table III 的全部数值（PDF 第 5 页从未渲染）。

---

## 4. 论文结果清点

| 类别 | 数量 |
|---|---:|
| 表格 | **10**（I–X） |
| 图 | **7**（Fig. 1–7） |
| 已清点的定量单元格 | **301** |
| 其中 `IMAGE_MANUALLY_VERIFIED` | **299** |
| 其中 `UNREADABLE` | **2** |
| **作者自产结果**（Table V 的 MIFlu 列 8 格 + Table VI 的 MIFlu 列 + Table VII/VIII/IX） | 作者自产 |
| **引用基线结果**（Table V 的 11 个基线列共 88 格等） | **`CITED_BASELINE_RESULT`** —— 论文自述取自 [9]/[14] |

> **重要**：Table V 只有 **MIFlu 那一列**是作者自产；其余 11 列是**引用值**。复现它们属 `NOT_APPLICABLE`。

---

## 5. R1-B 复现实现

### 5.1 训练器**已建成**

| 文件 | 内容 |
|---|---|
| `r1b/r1b_model.py` | 继承作者 `models.GPT4TS_lora.GPT4TS`，实现 **B-2**（文本前置 + 读取其后的 patch）与 **B-4**（有效冻结） |
| `r1b/r1b_train.py` | 实现 **B-1**（七通道）、**B-3**（PEFT=1）、**B-5**（验证集选模）、**B-6**（保存预测）、**B-7**（Table IV 配置） |

**作者源码树未被修改**：`git diff --stat` 仅显示 1 个 `.pyc`（import 时重新生成），**0 插入 0 删除**。

### 5.2 作者入口点的改动（全部为**声明式偏离**）

| # | 改动 | 类别 | 实测效果 |
|---|---|---|---|
| **B-1** | 七通道多变量窗口 | 论文要求 | 输出形状 → **(B, L, 7)** |
| **B-2** | 文本前置、读取其后的 patch 位置 | **修复发布代码缺陷** | `max\|Δ\|` **0.000e+00 → 5.88e-02**；`\|grad_text\|` **0 → 1.04e-03**；判决 **`text_inert` → `text_active`** |
| **B-3** | `PEFT=1` | 论文要求 | 本地无 peft，**待 HPC 验证**；注意**不得**传 `--target_modules` |
| **B-4** | 有效冻结 | **修复发布代码缺陷** | 可训练 **100% → 1.93%**（1,599,768 / 82,705,944） |
| **B-5** | 验证集选模 | 评估洁净性 | 训练期不读 Test |
| **B-6** | 保存预测与真值 | 评估洁净性 | NPZ schema 与已审计评分器一致 |
| **B-7** | 声明式训练配置 | **`PAPER_EXPLICIT`（Table IV）** | epochs 20 / lr 5e-4 / batch 16 |

### 5.3 CPU/静态验收

**30 项中 27 项通过，0 项失败，3 项待 HPC**：
- ✅ 24 项 PASS
- ✅ 2 项 PASS（已接线）
- ✅ 1 项 PASS（资产级）
- ⏳ 3 项 `NOT_YET_RUN`：LoRA 模块存在性、LoRA 参数可训练性（本地无 peft）、checkpoint 重载

### 5.4 就绪判决

# `NOT_READY_CONTRACT_UNRESOLVED`

**不是工程失败。** 阻塞是三项契约未决（pooling 轴、checkpoint 规则、optimizer/scheduler），其中 **pooling 轴永久不可恢复**。

**下一步（不需要 GPU）**：提交一个 **CPU-only HPC 作业**跑完 T19/T20/T29，然后重新签发判决。

---

## 6. 历史 4-vs-4 项目

**确切模型集（经核实，与预期一致）**：

| 侧 | 模型字符串 |
|---|---|
| **LLM（4）** | `gpt2_miflu` · `qwen_time_llm` · `calf_llm` · `timecma_llm` |
| **非 LLM（4）** | `nlinear` · `dlinear` · `patchtst` · `itransformer` |

**历史 MIFlu 的实现与角色**：

| 项 | 值 |
|---|---|
| 路径 | `scripts/miflu_model.py`，类 `MIFlu` |
| 适配器 | `scripts/innovation/backbones/gpt2_miflu_adapter.py`（`GPT2MifluAdapter`，名 `gpt2_miflu`） |
| 身份 | **项目自研的从零重实现，不是作者的 `GPT4TS_lora.py`** |
| as-run 快照 | 与 `results/innovation/source_snapshot/` 逐字节一致 |

**已识别的阶段（严格分开）**：A `early_ili_july2026` · B `innovation_v2_screening` · **C `wave1_validation_v3clean`（历史 4-vs-4 排名）** · **D `final_test_holdout_v3clean`（一次性 Test）** · E `a2_author966_stage5/stage6`（克隆后）。

**一个关键的验证反转**：`gpt2_miflu` 在 Wave-1 验证排名**第 1（0.771）**，却在一次性 Test 上**输给 `nlinear`（3.0505 vs 2.7389）**。替换必须**两个阶段都评**。

---

## 7. 直接替换兼容性判决

# `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED`

| 阶段 | 判决 |
|---|---|
| C Wave-1 验证排名 | `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` |
| D 最终 Test/Holdout | `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` |
| author-966 A2/stage-6 轨 | `INCOMPATIBLE_WITHOUT_NEW_CONTROLLED_EXPERIMENT` |

**根因**：数据契约不兼容 —— 历史轨是 **July-2026 1025 行 / 717-102-206**，R1-B 是 **作者 966 行 / 676-97-193**。**作者数据的 MIFlu 指标不得直接插入 1025 行的排名。**

**其余七个模型**：**无需重训**（最终 Test 的 `test_predictions.csv` 本地齐备），仅需**用同一个评分器重新聚合**。

被替换的那次运行必须标注：

> **official-repository-based MIFlu transferred to the historical comparison contract**

**绝不能称作"论文复现"。**

---

## 8. 哪些可保持不变 / 需重算 / 需重训

| 模型 | 角色 | 保持 | 重算 | 重训 |
|---|---|---|---|---|
| `gpt2_miflu` | **替换** | — | ✅ | **✅ 在历史 1025 行契约上** |
| `qwen_time_llm` | 固定 | ✅ | ❌ | ❌ |
| `calf_llm` | 固定 | ✅ | ❌ | ❌ |
| `timecma_llm` | 固定 | ✅ | ❌ | ❌ |
| `nlinear` | 固定 | ✅ | ❌ | ❌ |
| `dlinear` | 固定 | ✅ | ❌ | ❌ |
| `patchtst` | 固定 | ✅ | ❌ | ❌ |
| `itransformer` | 固定 | ✅ | ❌ | ❌ |

---

## 9. Seasonal Naive 泄漏影响

**项目里有两套 seasonal naive 实现，只有一套泄漏。**

| | **安全版** | **泄漏版** |
|---|---|---|
| 文件 | `results/v3_clean/.../clean_metrics.py` | `scripts/train_naive_966.py` |
| 公式 | `src=(T-1)+(k+1)-52`，**有钳制** | `ref = ts + s - 52`，**无上界钳制** |
| L=60 读未来？ | **否** | **是** |

**泄漏位置**：`s ≥ 52` 时 `ref = ts+s-52 ≥ ts`，即 L=60 的 **8 个 lead** 读到预测窗内的真实目标行。文件内 `assert ref < ts+s` 对任何正滞后恒真，**不检查 origin**。

### 精确影响

| 阶段 | 是否受影响 |
|---|---|
| **C/D 历史 4-vs-4** | **❌ 不受影响**（用的是安全版） |
| **E author-966 A2/stage-5/6** | **✅ 受影响，仅 L=60** |
| F1（冻结） | 已修正 |

| 轨 | L24 | L36 | L48 | **L60** | 四档均值 |
|---|---:|---:|---:|---:|---:|
| C/D 安全（历史） | 0.71934 | 0.73240 | 0.74603 | **0.88491** | 0.77067 |
| E 泄漏 | 2.5638 | 2.2655 | 2.1425 | **2.1035** | 2.26880 |
| E 修正后 | 2.5638 | 2.2655 | 2.1425 | **1.9174** | **2.22229** |

**对排名无影响**（仍是第 5/5），但任何引用 author-966 L=60 值或四档均值的表述**必须更新**。

> **结论：受控 MIFlu 替换不会继承这个泄漏缺陷。**

---

## 10. 未来需要的 GPU 授权

| 项目 | 状态 |
|---|---|
| 核心 R1-B 试点 | ❌ **未批准**（需新的复现专用授权） |
| 10 次重复扩展 | ❌ 未批准 |
| 论文级 Tier-2 实验 | ❌ 未批准 |
| 历史替换实验（40 fits on 1025-row） | ❌ 未批准 |
| **F1 封存的 0.35 GPU-h** | 🔒 **不得使用** |
| **旧的 0.05639 GPU-h** | 🔒 **不得使用** |

---

## 11. 确认

- ✅ **未提交任何 GPU 作业**：我名下最新作业仍是 **607691**（F1 的 Phase 3c）；队列空
- ✅ **F2 未启动**，且已取消
- ✅ **F1 保持冻结**：29/29 产物逐字节不变
- ✅ **未使用任何封存额度**
- ✅ **未修改或删除任何文件**：66/66 既有交付物逐字节不变；5 棵历史结果树文件数不变；**19 个 `innovation_deploy_root_v3_*` 仍为 19 个**；**作者源码树零改动**（仅一个重新生成的 `.pyc`）；git 状态 179 ?? / 49 M / 9 D 未变
- ✅ **原始中文 DOCX 报告未被改动**

**未完成部分（如实标注，未伪装为已完成）**：Table II/III 的全部数值（需渲染 PDF 第 5 页）；R1-B 的 3 项 HPC 门；论文级 Tier-2/Tier-3 实验；历史替换实验；新版 DOCX（前置条件未满足）。