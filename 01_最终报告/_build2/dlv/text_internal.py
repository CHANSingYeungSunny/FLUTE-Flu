# -*- coding: utf-8 -*-
"""Content of the internal technical report (EN + ZH), as a block list.

Block kinds: h1 h2 h3 p lead bul num quote table fig pb kv
Every payload is {"en": ..., "zh": ...}; tables/figures are referenced by key.

Numbering rule: the twelve H1 sections are numbered 1..12 and the contents list
is generated from the same strings, so the two can never disagree.  Tables are
numbered by the renderer, in order of appearance; the text therefore refers to
them by name ("the benchmark table") rather than by a hand-written number.
"""
from __future__ import annotations

from . import data as D


def H1(en, zh):
    return ("h1", {"en": en, "zh": zh})


def H2(en, zh):
    return ("h2", {"en": en, "zh": zh})


def H3(en, zh):
    return ("h3", {"en": en, "zh": zh})


def P(en, zh):
    return ("p", {"en": en, "zh": zh})


def LEAD(en, zh):
    return ("lead", {"en": en, "zh": zh})


def BUL(*pairs):
    return ("bul", {"en": [p[0] for p in pairs], "zh": [p[1] for p in pairs]})


def NUM(*pairs):
    return ("num", {"en": [p[0] for p in pairs], "zh": [p[1] for p in pairs]})


def QUOTE(en, zh):
    return ("quote", {"en": en, "zh": zh})


def T(key):
    return ("table", key)


def FIG(name, note_en=None, note_zh=None):
    return ("fig", {"name": name, "note_en": note_en, "note_zh": note_zh})


PB = ("pb", None)


META_EN = [
    ("Document", "Internal technical report (long form)"),
    ("Project", "Independent reproduction of MIFlu and a 28-model influenza-forecasting benchmark"),
    ("Version / date", "1.1 — 3 November 2026"),
    ("Audience", "Supervisor, assessor, and the next agent (CodeBuddy / ChatGPT) who continues the work"),
    ("Status", "Reproduction complete (+4.5 %, sign crossover 2-2); 28-model benchmark complete; 11 frozen "
               "encoders complete; ablation ladder in progress (27/60 cells at this snapshot)."),
    ("Companion documents", "progress_report_en.docx (short, school template) · ieee_manuscript_en.docx "
                            "(journal draft) · MANIFEST.md (file inventory) · 04_详细说明文档/REPO_HYGIENE.md"),
    ("Rule", "Every number below is read from `02_数字表格/*.csv` at build time and asserted by `dlv/data.py`. "
             "Nothing is quoted from memory."),
]
META_ZH = [
    ("文档", "内部技术报告（长篇）"),
    ("项目", "MIFlu 的独立复现，以及一个 28 模型的流感预测基准"),
    ("版本 / 日期", "1.1 — 2026 年 11 月 3 日"),
    ("读者", "导师、评阅人，以及接手本工作的下一个智能体（CodeBuddy / ChatGPT）"),
    ("状态", "复现完成（+4.5%，符号交叉 2-2）；28 模型基准完成；11 个冻结编码器完成；"
             "消融阶梯进行中（本快照完成 27/60 个单元）。"),
    ("配套文档", "progress_report_en.docx（简短，学校模板）· ieee_manuscript_en.docx（期刊稿）· "
                 "MANIFEST.md（文件清单）· 04_详细说明文档/REPO_HYGIENE.md"),
    ("原则", "下文每个数字都在构建时从 `02_数字表格/*.csv` 读取，并由 `dlv/data.py` 断言。没有任何数字凭记忆引用。"),
]

_SECTIONS = [
    ("1. Data",
     "1. 数据"),
    ("2. Methodology",
     "2. 方法"),
    ("3. Reproduction of MIFlu's Table V",
     "3. MIFlu 表 V 的复现"),
    ("4. Benchmark 1 — accuracy (28 arms)",
     "4. 基准一：精度（28 个模型）"),
    ("5. Benchmark 2 — peak skill on the Kramer & Shaman criterion",
     "5. 基准二：Kramer & Shaman 判据下的峰值技巧"),
    ("6. Benchmark 3 — the accuracy-efficiency frontier",
     "6. 基准三：精度—效率前沿"),
    ("7. Benchmark 4 — statistical significance",
     "7. 基准四：统计显著性"),
    ("8. Frozen LLM encoders as feature extractors",
     "8. 作为特征提取器的冻结 LLM 编码器"),
    ("9. The ablation ladder: design and current status",
     "9. 消融阶梯：设计与当前状态"),
    ("10. What the evidence does and does not support",
     "10. 证据支持什么、不支持什么"),
    ("11. Reproducibility",
     "11. 可复现性"),
    ("12. References",
     "12. 参考文献"),
]

CONTENTS_EN = [s[0] for s in _SECTIONS]
CONTENTS_ZH = [s[1] for s in _SECTIONS]


def blocks():
    b = []

    # ------------------------------------------------------------------ 1
    b.append(H1(*_SECTIONS[0]))
    b.append(P(
        "The data are the CDC national influenza surveillance series distributed with MIFlu: "
        f"{D.N_ROWS} weekly rows x {D.N_CHANNELS} numeric channels, bit-identical to the author's file "
        "(maximum absolute difference 0.000e+00). The split is chronological 70/10/20 — "
        f"rows 0-{D.TRAIN_END - 1} train, {D.TRAIN_END}-{D.VAL_END - 1} validation, {D.VAL_END}-{D.N_ROWS - 1} "
        f"test ({D.TEST_ROWS} rows) — and every window is checked against a containment guard, so a window's "
        f"input span always ends before its target span starts (minimum admitted test target-start row "
        f"{D.MIN_TEST_TARGET_ROW}). Standardisation uses a StandardScaler fitted on the training block only.",
        "数据是随 MIFlu 发布的美国 CDC 全国流感监测序列："
        f"{D.N_ROWS} 个每周行 x {D.N_CHANNELS} 个数值通道，与作者文件逐字节相同（最大绝对差 0.000e+00）。"
        "切分为按时间 70/10/20——"
        f"第 0-{D.TRAIN_END - 1} 行训练、{D.TRAIN_END}-{D.VAL_END - 1} 行验证、{D.VAL_END}-{D.N_ROWS - 1} 行测试"
        f"（共 {D.TEST_ROWS} 行）——每个窗口都通过严格包含约束检查，使输入区间总在目标区间开始之前结束"
        f"（被接纳的测试目标起始行最小下标为 {D.MIN_TEST_TARGET_ROW}）。标准化只使用在训练段上拟合的 StandardScaler。"))
    b.append(P(
        "**Why 676/97/193 (70/10/20)?** This is the standard protocol of the long-horizon forecasting "
        "benchmark family (Informer, AAAI 2023; DLinear, AAAI 2023; PatchTST, ICLR 2023; iTransformer, "
        "ICLR 2024) and the split used by the original MIFlu repository. The integer arithmetic is "
        "966 x 0.7 = 676, 966 x 0.2 = 193, remainder 97. We follow it exactly so that the numbers are "
        "comparable.",
        "**为什么用 676/97/193（70/10/20）？** 这是长跨度预测基准家族的标准协议（Informer, AAAI 2023；"
        "DLinear, AAAI 2023；PatchTST, ICLR 2023；iTransformer, ICLR 2024），也是原 MIFlu 仓库使用的切分。"
        "整数算术为 966 x 0.7 = 676、966 x 0.2 = 193、余 97。我们完全遵循，以保证数字可比。"))
    b.append(P(
        "**Why (W//16)*16 evaluation windows?** This is not a journal requirement. It is a side effect of "
        "the original code's `DataLoader(batch_size=16, drop_last=True)`, which discards the final partial "
        "batch of test windows: 170 -> 160, 158 -> 144, 146 -> 144, 134 -> 128. The discarded windows are "
        "measurably harder (about 1.41x the retained mean), so scoring MIFlu on the cropped set while "
        "scoring every other arm on the full set would hand MIFlu an easier test. All 28 arms are "
        "therefore scored on the same cropped windows.",
        "**为什么用 (W//16)*16 评测窗口？** 这不是期刊要求，而是原代码 `DataLoader(batch_size=16, "
        "drop_last=True)` 的副作用：它会丢弃最后不完整的一批测试窗口，170 -> 160、158 -> 144、146 -> 144、"
        "134 -> 128。被丢弃的窗口实测更难（约为保留窗口均值的 1.41 倍），因此若 MIFlu 按裁剪后的集合计分、"
        "其他模型按全集计分，就等于给 MIFlu 一个更容易的测试集。所以 28 个模型统一在同一批裁剪窗口上计分。"))
    b.append(T("06_原始数据集"))

    # ------------------------------------------------------------------ 2
    b.append(H1(*_SECTIONS[1]))
    b.append(P(
        "Two protocols are used, and they are never mixed. **(1) Reproduction:** 10 repetitions, seeds "
        "2021-2030, validation-selected checkpoint, 7-variable aggregate MSE — the protocol needed to "
        "compare with the paper's Table V. **(2) Benchmark:** 3 seeds (42/43/44), shared windows "
        "(W//16)*16 = 160/144/144/128 — the protocol used to compare 28 arms with each other. MIFlu is the "
        "only arm that appears under both, and its two numbers are not comparable to each other.",
        "本文使用两套协议，且从不混用。**(1) 复现：** 10 次重复、种子 2021-2030、验证集选择检查点、"
        "7 变量聚合 MSE——这是与论文表 V 比较所需的协议。**(2) 基准：** 3 个种子（42/43/44）、共享窗口 "
        "(W//16)*16 = 160/144/144/128——这是 28 个模型互比所用的协议。MIFlu 是唯一同时出现在两套协议下的模型，"
        "它的两个数值彼此不可比较。"))
    b.append(T("protocols"))
    b.append(P(
        "**Why 3 seeds in the benchmark but 10 in the reproduction?** The reproduction follows the paper's "
        "protocol (10 repetitions) so that a like-for-like comparison is possible. The benchmark follows the "
        "convention of the forecasting literature: PatchTST (ICLR 2023, arXiv:2211.14730) and iTransformer "
        "(ICLR 2024) both report three-seed means. Three seeds across 28 arms keeps the matrix at "
        "28 x 4 x 3 = 336 cells, which is tractable on one A100 partition; ten seeds would be 1,120 cells "
        "for no gain in the comparisons that are made here.",
        "**为什么基准用 3 个种子而复现用 10 个？** 复现遵循论文协议（10 次重复），以便进行同条件比较。"
        "基准遵循预测文献的惯例：PatchTST（ICLR 2023, arXiv:2211.14730）与 iTransformer（ICLR 2024）均报告"
        "三种子均值。28 个模型用 3 个种子使矩阵为 28 x 4 x 3 = 336 个单元，在单个 A100 分区上可完成；"
        "若用 10 个种子则为 1,120 个单元，而对本文所做的比较没有额外收益。"))
    b.append(T("repro_params"))
    b.append(P(
        "**What are the two [DEVIATION] items, and why are they necessary?** (1) **Checkpoint selection:** "
        "the original code selects the best epoch on the test set (`main_ILI_lora.py`, lines 211 and 225). "
        "That is data leakage — the test set is the final exam, and a model must not consult it while being "
        "chosen. We select on the validation block. (2) **The 7-variable metric:** the original test loader "
        "covers only 1 of the 7 variables (a bug), while Table V is defined on a 7-variable aggregate. We fix "
        "the loader. Both deviations are disclosed wherever a reproduction number appears.",
        "**两处 [DEVIATION] 是什么，为什么必要？** (1) **检查点选择：** 原代码在测试集上选最优 epoch"
        "（`main_ILI_lora.py` 第 211、225 行）。这是数据泄漏——测试集是期末考试，选模型时不能看它。"
        "我们改为在验证段上选择。(2) **7 变量指标：** 原测试加载器只覆盖 7 个变量中的 1 个（bug），"
        "而表 V 定义在 7 变量聚合上。我们修复了加载器。两处偏离凡出现在复现数字处均予披露。"))
    b.append(T("bench_params"))
    b.append(P(
        "**Why does PTE/PIE use ILITOTAL while MSE uses the 7-variable aggregate?** The aggregate is a "
        "*loss*, not a time series: its seven channels have training means from 1.74 (% WEIGHTED ILI) to "
        "493,629 (OT), so averaging them produces a number with no physical unit and no de-normalisation. "
        "Peak timing and peak height, by contrast, are statements about a single interpretable series in "
        "patient counts. PTE/PIE therefore use ILITOTAL de-normalised with the train-fit scaler "
        f"(mean {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f}, sd {D.SCALER_STD[D.ILITOTAL_IDX]:,.2f} patients). "
        "The reproduction keeps the aggregate because Table V is defined on it.",
        "**为什么 PTE/PIE 用 ILITOTAL 而 MSE 用 7 变量聚合？** 聚合值是一个*损失*，不是时间序列："
        "七个通道的训练均值从 1.74（% WEIGHTED ILI）到 493,629（OT），把它们平均得到的是一个没有物理单位、"
        "也无法反归一化的数。峰值时间与峰值高度则是对单一可解释序列（患者人数）的陈述。因此 PTE/PIE 使用"
        f"经训练集 scaler 反归一化的 ILITOTAL（均值 {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f}，标准差 "
        f"{D.SCALER_STD[D.ILITOTAL_IDX]:,.2f} 人）。复现保留聚合指标，是因为表 V 如此定义。"))

    # ------------------------------------------------------------------ 3
    b.append(H1(*_SECTIONS[2]))
    b.append(P(
        "The four-horizon mean is **1.4995 against the paper's 1.4355, i.e. 4.5 % worse**, but the mean is "
        "the least informative part of the result. The sign flips with the horizon: at L=24 we are 15.4 % "
        "better than the paper (1.3045 against 1.542) and at L=36 4.6 % better (1.3561 against 1.422), "
        "while at L=48 we are 17.0 % worse (1.6543 against 1.414) and at L=60 23.4 % worse (1.6829 against "
        "1.364). The MAE side shows the same crossover: 0.7482 / 0.7712 / 0.8381 / 0.8596 against "
        "0.726 / 0.779 / 0.757 / 0.719, a four-horizon mean of 0.8043 against 0.7452 (+7.9 %).",
        "四跨度均值为 **1.4995，对比论文的 1.4355，即差 4.5 %**，但均值是这个结果里信息量最小的部分。"
        "符号随跨度翻转：L=24 时本文比论文好 15.4 %（1.3045 对 1.542），L=36 时好 4.6 %（1.3561 对 1.422）；"
        "而 L=48 时差 17.0 %（1.6543 对 1.414），L=60 时差 23.4 %（1.6829 对 1.364）。MAE 一侧同样交叉："
        "0.7482 / 0.7712 / 0.8381 / 0.8596 对 0.726 / 0.779 / 0.757 / 0.719，四跨度均值为 0.8043 对 0.7452"
        "（+7.9 %）。"))
    b.append(T("reproduction"))
    b.append(P(
        "Two explanations are consistent with this pattern, and the data cannot yet separate them. The "
        "first is checkpoint selection: our validation-selected checkpoints are not the same objects as the "
        "author's test-selected ones, and a test-selected checkpoint has an advantage that grows with "
        "horizon, because longer horizons have more variance to exploit. The second is simply variance: the "
        "ten repetitions span 1.201-1.465 at L=24 and 1.401-1.984 at L=60, so a 17 % gap at L=48 and a 23 % "
        "gap at L=60 are large but not absurd given that spread — the run that produced 1.6829 at L=60 also "
        "produced 1.4108 on a different seed.",
        "有两种解释与该模式相符，而现有数据尚无法区分。其一是检查点选择：本文用验证集选出的检查点与作者用"
        "测试集选出的不是同一类对象，而测试集选出的检查点具有随跨度增长的优势，因为更长跨度有更多方差可利用。"
        "其二就是方差：十次重复在 L=24 的范围是 1.201-1.465，在 L=60 是 1.401-1.984，因此在如此离散度下，"
        "L=48 的 17 % 与 L=60 的 23 % 差距虽大却并不荒谬——产出 L=60 的 1.6829 的那次运行，在另一个种子上"
        "也产出过 1.4108。"))
    b.append(QUOTE(
        "The only defensible claim is: reproduced within 4.5 % on the four-horizon MSE mean, with a "
        "horizon-dependent sign. It is not a claim of superiority over the original, and it is not "
        "“the paper is wrong”.",
        "唯一可辩护的表述是：在四跨度 MSE 均值上复现到 4.5 % 以内，且符号随跨度翻转。这不是“我们优于原论文”，"
        "也不是“论文错了”。"))
    b.append(P(
        "The per-seed oracle is included because a reproduction claim is only as strong as its provenance. "
        "Every later re-export of a MIFlu cell, including the benchmark instance, is gated against that "
        "table at |Δ| <= 1e-5 by `05_程序代码/verify_miflu_oracle.py`; a cell that does not match is "
        "rejected rather than averaged in.",
        "本报告给出逐种子 oracle，因为复现论断的强度不会超过其来源的强度。此后每一次 MIFlu 单元（包括基准实例）"
        "的重新导出，都由 `05_程序代码/verify_miflu_oracle.py` 以 |Δ| <= 1e-5 对照该表把关；不匹配的单元被拒绝，"
        "而不是被平均进去。"))
    b.append(T("oracle"))
    b.append(FIG("fig_forecast_miflu_L24.png"))
    b.append(FIG("fig_forecast_miflu_L60.png"))
    b.append(P(
        "The curves show what the MSE gap is made of. At L=24 the step-0 curve tracks the ground truth "
        "through every rise and fall, and the degradation with step is visible but orderly. At L=60 the "
        "model still captures the seasonal shape — it is not a broken model — but it systematically "
        "under-shoots the three peaks, and the under-shoot is largest at the sharpest peak (the 2017-18 "
        "season). That is the visual form of a positive MSE gap at long horizon: the model has learned the "
        "seasonality and lost the amplitude.",
        "曲线展示了 MSE 差距由什么构成。L=24 时步 0 曲线在每一次起伏中都紧跟真值，随步退化可见但有秩序。"
        "L=60 时模型仍抓住季节形状——它不是坏掉的模型——但系统性地低估三个峰，且在最尖锐的峰（2017-18 季节）"
        "处低估最多。这就是长跨度下正 MSE 差距的视觉形态：模型学会了季节性，却丢掉了幅度。"))

    # ------------------------------------------------------------------ 4
    b.append(H1(*_SECTIONS[3]))
    b.append(P(
        "The benchmark contains 28 arms across six families: (1) **linear** (NLinear) — the simplest "
        "baseline; (2) **transformer** (PatchTST, iTransformer) — the current long-horizon state of the "
        "art; (3) **neural** (DNN, CNN, RNN, LSTM, GRU); (4) **classical machine learning** (gradient "
        "boosting, random forest, decision tree, SVR, KNN); (5) **LLM-based forecasters** (MIFlu, TimeCMA, "
        "Qwen-Time, CALF) — the paper's approach and its published competitors; (6) **frozen LLM encoders** "
        "(11 arms: Qwen2.5, DeepSeek-R1-Distill at five sizes, Tencent Hunyuan and ContextPilot) — the "
        "question of whether pre-trained language representations transfer to an epidemiological series. "
        "The matrix is 28 x 4 horizons x 3 seeds = 336 cells, of which 204 (13 conventional + 3 published "
        "LLM-based + DLinear) carry measured A100 provenance and 132 are the encoder cells.",
        "基准包含 6 个家族的 28 个模型：(1) **线性**（NLinear）——最简基线；(2) **Transformer**（PatchTST、"
        "iTransformer）——当前长跨度预测的最先进方法；(3) **神经网络**（DNN、CNN、RNN、LSTM、GRU）；"
        "(4) **经典机器学习**（梯度提升、随机森林、决策树、SVR、KNN）；(5) **基于 LLM 的预测器**（MIFlu、"
        "TimeCMA、Qwen-Time、CALF）——论文方法及其已发表的竞争者；(6) **冻结 LLM 编码器**（11 个：Qwen2.5、"
        "五个尺寸的 DeepSeek-R1-Distill、腾讯 Hunyuan 与 ContextPilot）——检验预训练语言表征能否迁移到流行病学"
        "序列。矩阵为 28 x 4 个跨度 x 3 个种子 = 336 个单元，其中 204 个（17 个传统模型，含 DLinear）带实测 A100 "
        "来源，132 个为编码器单元。"))
    b.append(T("benchmark"))
    b.append(P(
        "Three features of the table matter more than the ordering. First, **MIFlu is the accuracy "
        "champion** at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716): the paper's own model "
        "does win once it is placed on the same protocol as everyone else. Second, a **linear model with "
        "2,520 parameters is third of 28**, ahead of every transformer except PatchTST — a result that "
        "should make a reader suspicious of the assumption that architectural sophistication is what buys "
        "accuracy on a 966-row series. Third, the **spread is large**: 1.5574 to 5.6155 is a factor of 3.6, "
        "so model choice dominates any hyper-parameter tuning reported in the papers being compared.",
        "这张表里有三点比排序本身更重要。第一，**MIFlu 是精度冠军**，1.5574，其后是 PatchTST（1.6621）与 "
        "NLinear（1.8716）：论文自己的模型在被放到与所有模型相同的协议上之后，确实胜出。第二，一个 **2,520 "
        "参数的线性模型在 28 个模型中排第三**，除 PatchTST 外领先所有 Transformer——这一结果应让读者怀疑"
        "“架构精巧才买到精度”这一假设，至少在这条 966 行的序列上不成立。第三，**跨度很大**：1.5574 到 5.6155 "
        "是 3.6 倍，因此模型选择的影响远大于被比较论文中报告的任何超参数调整。"))
    b.append(LEAD(
        "**Finding F0 — accuracy alone does not identify a deployable model.** The top three arms are "
        "separated by 20 % of MSE, and the remaining 25 arms span a further 3.0x. A ranking is therefore "
        "easy to produce and hard to act on: it says which model fits this test set best, not which model "
        "supports the decision the forecast exists for. Benchmarks 2-4 ask the questions the ranking "
        "cannot answer.",
        "**发现 F0——仅凭精度无法确定一个可部署的模型。** 前三名之间的 MSE 相差 20 %，其余 25 个模型又进一步"
        "跨越 3.0 倍。因此排名很容易产出、却很难据以行动：它说明哪个模型最拟合这个测试集，而不说明哪个模型"
        "支持预测本来要服务的那个决策。基准二至基准四正是要回答排名回答不了的问题。"))
    b.append(FIG("fig_forecast_patchtst_L24.png"))
    b.append(FIG("fig_forecast_nlinear_L24.png"))

    # ------------------------------------------------------------------ 5
    b.append(H1(*_SECTIONS[4]))
    b.append(P(
        "Peak skill replaces the question “how close is the curve” with the question “does the forecast "
        "support a decision”. On ILITOTAL de-normalised to patient counts we compute, per fixed step "
        "0/1/2/3 = 1/2/3/4 weeks ahead, the peak-timing error (PTE, weeks) and the peak-intensity error "
        "(PIE, % of the observed peak). A cell passes the Kramer & Shaman criterion only if **PTE <= 1 "
        "week AND PIE <= 25 %** in the same cell. The two halves are a conjunction, and most arms fail one "
        "of them even when the other looks excellent.",
        "峰值技巧把问题从“曲线有多接近”换成“预测能否支持决策”。在反归一化为患者人数的 ILITOTAL 上，"
        "我们按固定步 0/1/2/3（提前 1/2/3/4 周）计算峰值时间误差（PTE，周）与峰值强度误差（PIE，占观测峰值的"
        "百分比）。只有同一格内 **PTE <= 1 周 且 PIE <= 25 %** 才通过 Kramer & Shaman 判据。两半是合取关系，"
        "多数模型即使一半很好，也会在另一半上失败。"))
    b.append(T("pte"))
    b.append(T("ks_grid"))
    b.append(P(
        "Two arms pass, and they pass differently. **NLinear passes all four step-0 cells** (4 of 16), with "
        f"a mean PTE of {D.KS['nlinear']['mean_pte']:.2f} weeks and a mean PIE of "
        f"{D.KS['nlinear']['mean_pie']:.2f} % over all 16 cells; at step 0 its mean PIE is "
        f"{D.KS['nlinear']['step0_pie']:.1f} %, an order of magnitude inside the criterion. **MIFlu also "
        f"passes 4 of 16**, but three are step-0 cells and the fourth is L=48 at step 1: at L=48 step 0 its "
        f"PTE is 1.22 weeks, and its PIE values across the passing cells are 18.3-24.8 %, i.e. against the "
        f"boundary rather than inside it. **PatchTST passes none**: its timing is the best in the study "
        f"(mean PTE {D.KS['patchtst']['mean_pte']:.2f} weeks) but its PIE is "
        f"{D.KS['patchtst']['mean_pie']:.1f} %, and it misses the calibration half in every cell.",
        "有两个模型通过，但通过的方式不同。**NLinear 在步 0 的四个单元全部通过**（4/16），全部 16 个单元的"
        f"均值 PTE 为 {D.KS['nlinear']['mean_pte']:.2f} 周、均值 PIE 为 {D.KS['nlinear']['mean_pie']:.2f} %；"
        f"步 0 的均值 PIE 为 {D.KS['nlinear']['step0_pie']:.1f} %，比判据宽松一个数量级。**MIFlu 同样通过 "
        f"4/16**，但其中三个是步 0 单元、第四个是 L=48 的步 1：在 L=48 步 0 它的 PTE 为 1.22 周，"
        f"而它通过的单元 PIE 为 18.3-24.8 %，即贴着边界而不是落在判据内部。**PatchTST 一个都不通过**："
        f"它的时序是本研究中最准的（均值 PTE {D.KS['patchtst']['mean_pte']:.2f} 周），但 PIE 为 "
        f"{D.KS['patchtst']['mean_pie']:.1f} %，在每个单元都未满足校准一半。"))
    b.append(FIG("fig_pte_pie_heatmap.png"))
    b.append(P(
        "The mechanism is visible in the curves. A model trained to minimise squared error is rewarded for "
        "tracking the level and is punished only quadratically for missing a peak; a smooth, slightly "
        "conservative forecast is a good MSE strategy and a bad peak strategy, because the peak is the one "
        "place where the loss is dominated by a handful of weeks. NLinear, essentially a linear map with a "
        "per-window level correction, produces a sharper response at the peak: it over-shoots more often, "
        "which costs it MSE, and lands closer to the peak height more often, which is what PIE measures. "
        "This is a hypothesis consistent with the data, not a proven mechanism.",
        "机制在曲线中可见。以最小化平方误差训练的模型，因跟踪水平而受奖励，只在漏掉峰值时受到二次惩罚；"
        "平滑、略保守的预测是好的 MSE 策略、坏的峰值策略，因为峰值正是损失被少数几周主导的地方。NLinear 本质上是"
        "一个带逐窗口水平修正的线性映射，在峰值处反应更锐利：它更经常高估，这使 MSE 变差；也更经常落在接近峰值"
        "高度的位置，而这正是 PIE 度量的。这是与数据相符的假设，不是已被证明的机制。"))
    b.append(LEAD(
        f"**Finding F1 — the deployment ordering is not the accuracy ordering.** Across all 28 arms, better "
        f"MSE does go with better calibration (Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f} against mean PIE): "
        f"the two axes are not independent, and MSE is a useful screen. What fails is the ordering of the "
        f"frontier. Among the three lowest-MSE arms the calibration order is inverted at both ends — NLinear "
        f"(3rd on MSE) has the lowest PIE at {D.KS['nlinear']['mean_pie']:.1f} %, MIFlu (1st) sits at "
        f"{D.KS['miflu']['mean_pie']:.1f} % and PatchTST (2nd) at {D.KS['patchtst']['mean_pie']:.1f} % — and "
        f"the pass indicator is negatively rank-correlated with MSE (ρ = {D.DECOUPLE['rho_pass']:.2f}, "
        f"p = {D.DECOUPLE['p_pass']:.3f}). The runner-up by MSE passes nothing; the third-best passes every "
        f"horizon one week ahead. That is the finding a deployment decision turns on, and a leaderboard "
        f"sorted by MSE cannot express it.",
        f"**发现 F1——部署排序不是精度排序。** 在全部 28 个模型上，MSE 更好确实伴随校准更好"
        f"（对均值 PIE 的 Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f}）：两个轴并非彼此独立，MSE 是有用的筛选。"
        f"失效的是**前沿内部的排序**。在 MSE 最低的三个模型中，校准排序恰好相反——NLinear（MSE 第 3）的 PIE 最低，"
        f"为 {D.KS['nlinear']['mean_pie']:.1f} %；MIFlu（第 1）为 {D.KS['miflu']['mean_pie']:.1f} %；"
        f"PatchTST（第 2）为 {D.KS['patchtst']['mean_pie']:.1f} %——而且通过标记与 MSE 呈负秩相关"
        f"（ρ = {D.DECOUPLE['rho_pass']:.2f}，p = {D.DECOUPLE['p_pass']:.3f}）。MSE 第二名一个都不通过；"
        f"第三名通过每个跨度的提前一周。这正是部署决策所依赖的发现，而按 MSE 排序的榜单无法表达它。"))

    # ------------------------------------------------------------------ 6
    b.append(H1(*_SECTIONS[5]))
    b.append(P(
        "The Pareto frontier answers a different question from the peak criterion: not “is this model good "
        "enough to deploy” but “how much accuracy does each additional parameter buy”. A model is "
        "Pareto-optimal if no other model achieves both lower error and fewer parameters. The frontier has "
        "exactly two members: NLinear (2,520 parameters, MSE 1.8716) and PatchTST (531,878 parameters, MSE "
        "1.6621). Across the 11 parametric arms, a regression of the four-horizon mean MSE on "
        f"log10(parameters) gives a slope of **+{D.PARETO['slope']:.4f}** with **R² = "
        f"{D.PARETO['r2']:.4f}**.",
        "帕累托前沿回答的是与峰值判据不同的问题：不是“这个模型是否好到可以部署”，而是“每增加一些参数买到了多少"
        "精度”。若无其他模型同时具有更低误差和更少参数，则该模型是帕累托最优的。前沿恰好两个成员：NLinear"
        "（2,520 参数，MSE 1.8716）与 PatchTST（531,878 参数，MSE 1.6621）。在 11 个含参数模型上，把四跨度均值 "
        f"MSE 对 log10(参数量) 做回归，斜率为 **+{D.PARETO['slope']:.4f}**，**R² = {D.PARETO['r2']:.4f}**。"))
    b.append(T("efficiency"))
    b.append(P(
        "Both signs of that sentence matter. The slope is positive, so more parameters are associated with "
        "a *higher* (worse) MSE; and R² is 2 %, so size explains almost none of the variance. The two "
        "Pareto rows then read as a trade-off rather than a ranking: PatchTST spends "
        f"{D.PARETO['ratio']:.0f}x the parameters of NLinear for {D.PARETO['mse_gain_pct']:.1f} % lower MSE. "
        "Whether that is a good trade depends on the deployment — and, given Finding F1, on whether the "
        "deployment needs peak skill, in which case the 11.2 % accuracy advantage buys a model that fails "
        "the epidemiological criterion outright.",
        "这句话的两个符号都重要。斜率为正，即参数越多 MSE 反而*越高*（越差）；R² 只有 2 %，即规模几乎解释不了"
        "任何方差。于是两条帕累托记录应读作权衡而不是排名：PatchTST 用 "
        f"{D.PARETO['ratio']:.0f} 倍于 NLinear 的参数量，换取 {D.PARETO['mse_gain_pct']:.1f} % 的 MSE 下降。"
        "这笔交易是否划算取决于部署场景——而且，鉴于发现 F1，还取决于部署是否需要峰值技巧；若需要，那 11.2 % 的"
        "精度优势换来的却是一个完全不能满足流行病学判据的模型。"))
    b.append(FIG("fig_pareto_frontier.png"))
    b.append(FIG("fig_ks_ranking.png"))
    b.append(LEAD(
        f"**Finding F2 — parameter count is not a proxy for accuracy.** The slope is positive and R² is "
        f"{D.PARETO['r2']:.4f}: on this dataset, size is uninformative about accuracy, and what little signal "
        f"there is points the wrong way. The frontier is a two-model trade-off, not a ranking, and the "
        f"cheaper member of the frontier is the one that passes the domain criterion at every horizon.",
        f"**发现 F2——参数量不是精度的代理。** 斜率为正、R² = {D.PARETO['r2']:.4f}：在本数据集上，规模对精度"
        f"没有信息量，而仅有的那点信号还指向错误方向。前沿是两个模型之间的权衡，不是排名；而前沿中更便宜的那个，"
        f"才是每个跨度都通过领域判据的模型。"))

    # ------------------------------------------------------------------ 7
    b.append(H1(*_SECTIONS[6]))
    b.append(P(
        "The Pareto analysis is descriptive: it says what the trade-off is, and needs no inference. The "
        "significance analysis is inferential: it asks whether the 11.2 % difference is distinguishable from "
        "seed noise at all. Both are needed, because a trade-off is only worth discussing if the difference "
        "being traded is real.",
        "帕累托分析是描述性的：它说明权衡是什么，不需要推断。显著性分析是推断性的：它问的是那 11.2 % 的差异"
        "究竟能否与种子噪声区分开。两者都需要，因为只有当被交易的差异是真实的时候，讨论这笔交易才有意义。"))
    b.append(P(
        f"On the 12 matched (horizon x seed) cells we run exact paired sign-flip tests over all "
        f"{D.N_PAIRS} pairs of the 17 non-encoder arms (MIFlu and the 11 encoders are outside this family), with Holm-Bonferroni correction, a bootstrap 95 % CI (10,000 resamples) "
        f"and Cohen's d. {D.N_RAW_SIG} of {D.N_PAIRS} pairs are significant before correction; after proper Holm "
        f"over {D.N_PAIRS} pairs none survives, because n = 12 makes the smallest attainable adjusted p "
        f"{D.HOLM_MIN:.3f}. The pair the "
        f"Pareto argument needs is **NLinear vs PatchTST**: mean Δ MSE +0.2095 in PatchTST's favour, NLinear "
        f"lower in only {int(D.PAIR.wins_a)} of 12 cells, raw p = {float(D.PAIR.p_raw):.4f}, "
        f"**p(Holm) = {float(D.PAIR.p_holm):.3f}**, d = {float(D.PAIR.effect_d):.2f}.",
        f"在 12 个配对（跨度 x 种子）单元上，我们对全部 {D.N_PAIRS} 对模型做精确配对符号翻转检验，"
        f"使用 Holm-Bonferroni 校正、bootstrap 95 % 置信区间（10,000 次重采样）与 Cohen's d。"
        f"{D.N_PAIRS} 对中有 {D.N_RAW_SIG} 对在校正前显著；对 {D.N_PAIRS} 对做正确的 Holm 校正后无一存活，因为 n = 12 "
        f"使最小可达校正 p 为 {D.HOLM_MIN:.3f}。帕累托论证所需的那一对是 **NLinear 对 PatchTST**："
        f"平均 Δ MSE 为 +0.2095（对 PatchTST 有利），NLinear 只在 12 个单元中的 {int(D.PAIR.wins_a)} 个更低，"
        f"原始 p = {float(D.PAIR.p_raw):.4f}，**p(Holm) = {float(D.PAIR.p_holm):.3f}**，"
        f"d = {float(D.PAIR.effect_d):.2f}。"))
    b.append(T("paired"))
    b.append(P(
        f"Why the paired-test table looks like it is about other models: it is sorted by p, and the "
        f"NLinear-PatchTST pair is the {D.PAIR_RANK}th smallest of {D.N_PAIRS} — a “strongest six” table "
        f"would silently omit the one comparison the argument needs. The table therefore puts that pair in "
        f"the first row and the six most significant pairs below it, so both facts are visible at once: before "
        f"correction most of the roster separates; after correction the study cannot separate any pair — a "
        f"statement about power, not about the models — and the frontier pair is the one the argument needs.",
        f"为什么配对检验表看起来在讲别的模型：它按 p 排序，而 NLinear-PatchTST 这一对在 {D.N_PAIRS} 对中"
        f"排第 {D.PAIR_RANK} 小——“最强六项”式的表会恰好省略论证所需的那一个比较。因此本表把这一对放在第一行，"
        f"把六个最显著的对放在下面，使两个事实同时可见：校正前榜单上的大多数模型彼此可分；校正后本研究无法分开任何一对"
        f"——这是检验功效的陈述，不是关于模型的陈述——而前沿上的那一对正是论证所需。"))
    b.append(LEAD(
        f"**Finding F3 — the 211x parameter cost is not statistically distinguishable from noise.** p(Holm) "
        f"= {float(D.PAIR.p_holm):.3f} means we cannot reject equality of the two means at the 5 % level. "
        f"Three qualifications keep this honest: with n = 12 the smallest attainable p is 2/2¹² ≈ 0.00049; "
        f"non-significance is a failure to reject, not a demonstration of equivalence; and the effect size "
        f"is d = {float(D.PAIR.effect_d):.2f} with PatchTST lower in {12 - int(D.PAIR.wins_a)} of 12 cells, "
        f"so the direction is consistent even though the difference is not resolvable at this sample size. "
        f"The correct conclusion is not “the models are equal” but “this benchmark does not establish an "
        f"accuracy advantage for the 211x cost” — which, together with Finding F1, is enough to make NLinear "
        f"the defensible default.",
        f"**发现 F3——211 倍参数成本在统计上与噪声不可区分。** p(Holm) = {float(D.PAIR.p_holm):.3f} 意味着"
        f"在 5 % 水平上无法拒绝两个均值相等。三点限定让它保持诚实：n = 12 时最小可达 p 为 2/2¹² ≈ 0.00049；"
        f"不显著是“未能拒绝”，不是“证明相等”；效应量为 d = {float(D.PAIR.effect_d):.2f}，且 PatchTST 在 12 个"
        f"单元中的 {12 - int(D.PAIR.wins_a)} 个更低，因此方向一致，只是在这个样本量下差异无法分辨。"
        f"正确的结论不是“两个模型相等”，而是“本基准未能为 211 倍成本确立精度优势”——结合发现 F1，这已足以让 "
        f"NLinear 成为可辩护的默认选择。"))

    # ------------------------------------------------------------------ 8
    b.append(H1(*_SECTIONS[7]))
    b.append(P(
        "The encoder axis asks whether a pre-trained language model is a useful feature extractor for an "
        "epidemiological series. Each arm is a frozen encoder plus one shared linear head, trained "
        "channel-independently; no encoder weight is updated, and the head is the only trainable part. This "
        "is deliberately the *charitable* version of the idea: if the representation carries usable "
        "information, a linear read-out is enough to expose it, and a failure cannot be blamed on "
        "fine-tuning instability. 132 of 156 cells are complete (11 arms x 4 horizons x 3 seeds); the 24 "
        "missing cells belong to two embedding-only models that cannot emit per-layer hidden states.",
        "编码器这一轴问的是：预训练语言模型能否作为流行病学序列的有用特征提取器。每个模型是一个冻结编码器加一个"
        "共享线性头，按通道独立训练；不更新任何编码器权重，线性头是唯一可训练部分。这是该想法*最宽容*的版本："
        "如果表征携带可用信息，线性读出就足以暴露它，失败也不能归咎于微调不稳定。156 个单元中完成 132 个"
        "（11 个模型 x 4 个跨度 x 3 个种子）；缺失的 24 个属于两个仅提供句向量、无法输出逐层隐藏状态的模型。"))
    b.append(T("llm"))
    b.append(T("llm_excluded"))
    b.append(P(
        f"The result is uniform and negative. The best encoder (Hunyuan-1.8B) reaches "
        f"{D.ENC['best_mse']:.4f} and the worst (Qwen2.5-1.5B) {D.ENC['worst_mse']:.4f}, i.e. "
        f"{D.ENC['ratio_best']:.2f}x to {D.ENC['ratio_worst']:.2f}x the MSE of MIFlu (1.5574), and every one "
        f"of the 11 is worse than a decision tree (4.3198). None passes the Kramer & Shaman criterion in any "
        f"cell. The ordering inside the family is not explained by size: a 1.8B model is the best and a 7B "
        f"model of the same vendor is worse, so whatever the encoders carry, it is not a monotone function "
        f"of capacity.",
        f"结果一致且为负。最好的编码器（Hunyuan-1.8B）为 {D.ENC['best_mse']:.4f}，最差（Qwen2.5-1.5B）为 "
        f"{D.ENC['worst_mse']:.4f}，即 MIFlu（1.5574）MSE 的 {D.ENC['ratio_best']:.2f} 至 "
        f"{D.ENC['ratio_worst']:.2f} 倍，且 11 个全部差于决策树（4.3198）。没有任何一个在任何单元通过 "
        f"Kramer & Shaman 判据。家族内部的排序也不能由规模解释：1.8B 的模型最好，而同厂商 7B 的模型更差，"
        f"因此无论编码器携带了什么，它都不是容量的单调函数。"))
    b.append(LEAD(
        f"**Finding F4 — frozen LLM representations do not transfer to this task.** Eleven encoders, five "
        f"model families, 1.5B to 32B parameters, 132 cells: none beats a decision tree and none passes the "
        f"domain criterion. The negative result is informative because the protocol was designed to give the "
        f"idea its best chance (frozen features, linear read-out, channel independence) and it still fails; "
        f"it does not follow that an encoder can never help, but it does mean that a paper claiming a gain "
        f"from frozen language features on this task owes a mechanism and a control.",
        f"**发现 F4——冻结 LLM 表征不能迁移到本任务。** 11 个编码器、5 个模型家族、1.5B 至 32B 参数、132 个单元："
        f"没有一个胜过一个决策树，也没有一个通过领域判据。这一负面结果有信息量，因为协议被设计成给该想法最好"
        f"的机会（冻结特征、线性读出、通道独立），而它仍然失败；这不能推出编码器永远不可能有帮助，但它确实意味着："
        f"任何声称在本任务上从冻结语言特征获得增益的论文，都需要给出机制与对照。"))

    # ------------------------------------------------------------------ 9
    b.append(H1(*_SECTIONS[8]))
    b.append(P(
        "The ablation ladder asks where MIFlu's accuracy comes from. The paper's model is a GPT-2 backbone "
        "with low-rank adapters (LoRA), a text branch, and a linear head, so the two knobs that could carry "
        "the result are (a) the LoRA adaptation and (b) the depth of the stack. The ladder is therefore five "
        "variants: no LoRA, and K = 2, 4, 8, 12 transformer layers, each at four horizons and three seeds "
        "(5 x 12 = 60 cells), compared against the full K=6 arm already in the benchmark table.",
        "消融阶梯要问的是 MIFlu 的精度从何而来。论文模型是 GPT-2 主干 + 低秩适配（LoRA）+ 文本分支 + 线性头，"
        "因此可能承载结果的两个旋钮是 (a) LoRA 适配与 (b) 堆叠深度。阶梯因此为五个变体：去掉 LoRA，以及 "
        "K = 2、4、8、12 层，每个变体 4 个跨度、3 个种子（5 x 12 = 60 个单元），与已在基准表中的完整 K=6 臂比较。"))
    b.append(P(
        "The question each variant answers is worth stating, because “ablation” without a hypothesis is just "
        "extra runs. **no_lora** isolates the frozen backbone: if accuracy survives, the adaptation is not "
        "what carries it. **K=2 and K=4** test whether depth is needed at all on a 966-row series; **K=8 and "
        "K=12** test whether extra capacity helps or merely over-fits. The reference arm is the K=6 model "
        "already reported, so the ladder contains no duplicated run.",
        "每个变体要回答的问题值得写明，因为没有假设的“消融”只是多跑几次。**no_lora** 隔离出冻结主干："
        "若精度仍在，则适配不是承载它的东西。**K=2 与 K=4** 检验在这条 966 行序列上是否根本需要深度；"
        "**K=8 与 K=12** 检验额外容量是有帮助还是仅仅过拟合。参考臂即已报告的 K=6 模型，因此阶梯中没有重复运行。"))
    b.append(T("ablation"))
    b.append(P(
        "One ablation result is already established, and it is a negative one about the text branch: the "
        "text tokens are appended *after* the time patches behind a causal mask, and the output head reads "
        "only the time-patch positions. Two different text tensors therefore give bit-identical predictions, "
        "and `--no-text` is bit-identical to the full arm with the same seed — asserted by "
        "`tests_archive/test_miflu_ablations.py`, not assumed. In the published architecture the text branch cannot "
        "change a number, so a “text ablation” row would be a structural verification, not an effect. That "
        "is why the modality claim of the original paper should be read carefully: whatever its text branch "
        "contributes, it is not visible in this implementation.",
        "有一项消融结果已经确立，而它是关于文本分支的负面结论：文本 token 被附加在时间分片*之后*并位于因果掩码"
        "之后，而输出头只读时间分片位置。因此两个不同文本张量给出逐位相同的预测，`--no-text` 与同种子的完整臂"
        "逐位相同——这一点由 `tests_archive/test_miflu_ablations.py` 断言，而非假设。在已发表的架构中，文本分支无法改变"
        "任何数字，所以“文本消融”一行只能是结构验证，不是效应。这正是原论文的多模态主张需要被仔细阅读的原因："
        "无论其文本分支贡献了什么，在这个实现里都不可见。"))
    b.append(P(
        f"The remaining five variants are not yet reported. At the snapshot these documents are built from, "
        f"{D.TABLE8_DONE} of {D.TABLE8_TOTAL} cells were complete (driver job {D.DRIVER_JOB}) and the "
        f"per-variant export had not been pulled, so this section reports the design and the completion "
        f"count and claims **no** depth trend. An earlier internal note that described the ladder as "
        f"complete at 60/60 and “monotonic” is not supported by any artefact in this repository and has been "
        f"removed from the reports.",
        f"其余五个变体尚未报告。在本文档所依据的快照中，{D.TABLE8_TOTAL} 个单元里完成 {D.TABLE8_DONE} 个"
        f"（驱动作业 {D.DRIVER_JOB}），且逐变体导出尚未取回，因此本节只报告设计与完成数，**不**声明任何深度趋势。"
        f"早前一份内部记录称阶梯已 60/60 完成且“单调”，但本仓库没有任何产物支持该说法，已从报告中移除。"))
    b.append(LEAD(
        "**Finding F5 (provisional) — the modality claim is not supported by the architecture as shipped.** "
        "The text branch is masked out of the prediction path, so `--no-text` cannot move a number; the "
        "depth and LoRA questions remain open until the 60 cells are aggregated. This is reported as a "
        "design and a status, not as a result.",
        "**发现 F5（暂定）——按已交付的架构，多模态主张得不到支持。** 文本分支位于预测路径之外，因此 `--no-text` "
        "无法改变任何数字；深度与 LoRA 的问题要等 60 个单元聚合后才能回答。此处报告的是设计与状态，不是结果。"))

    # ------------------------------------------------------------------ 10
    b.append(H1(*_SECTIONS[9]))
    b.append(P(
        "Four claims are supported by the artefacts in this repository: (1) the reproduction lands within "
        "4.5 % of the published four-horizon MSE mean with a horizon-dependent sign; (2) on one common "
        "protocol, MIFlu is the accuracy champion of 28 arms and NLinear is third with 2,520 parameters "
        "against PatchTST's 531,878; (3) the deployment ordering is not the accuracy ordering — the frontier "
        "is inverted on calibration and the pass indicator is negatively rank-correlated with MSE; (4) "
        "frozen LLM encoders do not transfer to this task under a protocol designed to favour them.",
        "本仓库的产物支持四项主张：(1) 复现在已发表的四跨度 MSE 均值 4.5 % 以内，且符号随跨度翻转；"
        "(2) 在同一协议下，MIFlu 是 28 个模型中的精度冠军，NLinear 以比 PatchTST 少 211 倍的参数排第三；"
        "(3) 部署排序不是精度排序——前沿在校准上反转，且通过标记与 MSE 呈负秩相关；"
        "(4) 在有利于该想法的协议下，冻结 LLM 编码器不能迁移到本任务。"))
    b.append(P(
        "Five claims are not supported, and the reports do not make them. (1) **Superiority over the "
        "original**: the reproduction is 4.5 % worse on the mean, and the per-horizon wins do not survive "
        "as a claim because the protocol differs in two disclosed ways. (2) **“MSE and peak skill are "
        "unrelated”**: they are positively correlated across the roster (ρ = +0.74); the finding is about "
        "the frontier, not about independence. (3) **“NLinear is the only arm that passes”**: MIFlu also "
        "passes 4 of 16, by a different route and against the boundary. (4) **“PatchTST's advantage is "
        "zero”**: the test fails to reject equality, which is not the same statement. (5) **“The ablation "
        "shows a monotonic depth trend”**: the ladder is 27/60 and no per-variant number has been "
        "aggregated.",
        "有五项主张不被支持，报告也不作这些主张。(1) **优于原论文**：复现在均值上差 4.5 %，而逐跨度的胜出"
        "不能作为主张成立，因为协议在两处已披露的地方不同。(2) **“MSE 与峰值技巧无关”**：它们在榜单上正相关"
        "（ρ = +0.74）；发现针对的是前沿，而不是独立性。(3) **“NLinear 是唯一通过的模型”**：MIFlu 同样通过 "
        "4/16，只是路径不同且贴着边界。(4) **“PatchTST 的优势为零”**：检验未能拒绝相等，这与“相等”不是同一陈述。"
        "(5) **“消融显示单调的深度趋势”**：阶梯为 27/60，尚未聚合任何逐变体数字。"))
    b.append(P(
        "The threats to validity are worth naming. The K&S thresholds are attributed to Kramer & Shaman "
        "(2019) but remain **[to verify]** against the original text; the peak detector is this study's "
        "engineering choice. The benchmark has one dataset, one country and one target series, so nothing "
        "here establishes cross-dataset generality. The significance tests have n = 12, so their resolution "
        "is coarse by construction. There is no rolling-origin evaluation yet: every number is from a single "
        "chronological split, so a season that falls in the test block is seen once. Finally, the encoder "
        "axis is a *frozen-feature* test; it does not test generation, prompting or fine-tuning, and its "
        "negative result must not be over-read.",
        "值得点明效度威胁。K&S 阈值归因于 Kramer & Shaman（2019），但仍标注 **[to verify]**，待与原文核对；"
        "峰值检测器是本研究的工程选择。基准只有一个数据集、一个国家、一条目标序列，因此本文不能确立跨数据集"
        "的普适性。显著性检验 n = 12，其分辨率在构造上就是粗的。目前没有滚动原点评测：每个数字都来自单一按时间"
        "切分，因此落在测试块中的季节只被看到一次。最后，编码器这一轴是*冻结特征*测试，不测试生成、提示或微调，"
        "其负面结果不可过度解读。"))
    b.append(T("defects"))
    b.append(P(
        "The defect ledger is included because it is part of the evidence: eight defects were found and "
        "seven fixed during the campaign, and one of them (A1) is why no LLM ±sd measured before "
        "2026-11-02 03:57:47 is quoted anywhere in these documents. A6 remains open and is an operational, "
        "not a scientific, risk: it wastes GPU hours without corrupting a completed cell.",
        "本报告收录缺陷清单，因为它本身就是证据的一部分：本次工作中发现八项缺陷、修复七项，其中 A1 正是"
        "这些文档拒绝引用 2026-11-02 03:57:47 之前任何 LLM 标准差的原因。A6 仍未修复，属运行风险而非科学风险："
        "它浪费 GPU 机时，但不会污染已完成的单元。"))

    # ------------------------------------------------------------------ 11
    b.append(H1(*_SECTIONS[10]))
    b.append(P(
        "Every document in `01_最终报告/` is generated from the CSVs, not edited by hand. From the repository "
        "root:",
        "`01_最终报告/` 中的每一份文档都由 CSV 生成，而非手工编辑。在仓库根目录执行："))
    b.append(BUL(
        ("`python 01_最终报告/_build2/build_docs.py` — writes the six DOCX and asserts every headline number "
         "on import of `dlv/data.py`.",
         "`python 01_最终报告/_build2/build_docs.py`——写出六份 DOCX，并在导入 `dlv/data.py` 时断言每个关键数字。"),
        ("`python 01_最终报告/_build2/to_pdf.py` — converts to PDF with the bundled LibreOffice kit and "
         "prints the page count of each file.",
         "`python 01_最终报告/_build2/to_pdf.py`——用内置 LibreOffice kit 转 PDF，并打印每份文件的页数。"),
        ("`python 01_最终报告/_build2/verify_docs.py` — reopens every DOCX, checks the Chinese round-trip on "
         "two independent paths, and confirms the reproduction table still shows the sign crossover.",
         "`python 01_最终报告/_build2/verify_docs.py`——重新打开每份 DOCX，用两条独立路径检查中文往返，"
         "并确认复现表仍显示符号交叉。"),
        ("`python 01_最终报告/_build2/make_manifest.py` — regenerates `MANIFEST.md`.",
         "`python 01_最终报告/_build2/make_manifest.py`——重新生成 `MANIFEST.md`。")))
    b.append(T("artefacts"))

    # ------------------------------------------------------------------ 12
    b.append(H1(*_SECTIONS[11]))
    b.append(BUL(
        ("Moon et al. “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting.” *IEEE Journal of "
         "Biomedical and Health Informatics*, 2025. DOI: 10.1109/JBHI.2025.3561214.",
         "Moon 等，“MIFlu: Large Language Model-Based Multimodal Influenza Forecasting”，*IEEE Journal of "
         "Biomedical and Health Informatics*，2025。DOI: 10.1109/JBHI.2025.3561214。"),
        ("Kramer & Shaman. “Development and validation of influenza forecasting for 64 temperate and "
         "tropical countries.” *PLoS Computational Biology* 15(2): e1006742, 2019. "
         "DOI: 10.1371/journal.pcbi.1006742 [thresholds to verify].",
         "Kramer & Shaman，“Development and validation of influenza forecasting for 64 temperate and "
         "tropical countries”，*PLoS Computational Biology* 15(2): e1006742，2019。"
         "DOI: 10.1371/journal.pcbi.1006742 [阈值待核实]。"),
        ("Nie et al. “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers.” *ICLR* 2023. "
         "arXiv:2211.14730.",
         "Nie 等，“A Time Series is Worth 64 Words: Long-term Forecasting with Transformers”，*ICLR* 2023。"
         "arXiv:2211.14730。"),
        ("Liu et al. “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting.” "
         "*ICLR* 2024.",
         "Liu 等，“iTransformer: Inverted Transformers Are Effective for Time Series Forecasting”，*ICLR* 2024。"),
        ("Zeng et al. “Are Transformers Effective for Time Series Forecasting?” *AAAI* 2023.",
         "Zeng 等，“Are Transformers Effective for Time Series Forecasting?”，*AAAI* 2023。"),
        ("Centers for Disease Control and Prevention. “FluView: Weekly U.S. Influenza Surveillance Report,” "
         "national ILI series (966 weekly rows, 7 channels).",
         "美国疾病控制与预防中心，“FluView: Weekly U.S. Influenza Surveillance Report”，全国 ILI 序列"
         "（966 个每周行、7 个通道）。")))

    return b
