# -*- coding: utf-8 -*-
"""Content of the IEEE-style manuscript (EN + ZH).

Single-column review draft, IEEE section order (I..IX).  Every number is the same
number as in the internal report: `dlv/data.py` asserts them.  Tables are numbered
by the renderer in Roman numerals, in order of appearance, so the text refers to
Table I..VIII and the order below must not change without updating the text.
"""
from __future__ import annotations

from . import data as D


def H1(en, zh):
    return ("h1", {"en": en, "zh": zh})


def H2(en, zh):
    return ("h2", {"en": en, "zh": zh})


def P(en, zh):
    return ("p", {"en": en, "zh": zh})


def LEAD(en, zh):
    return ("lead", {"en": en, "zh": zh})


def BUL(*pairs):
    return ("bul", {"en": [p[0] for p in pairs], "zh": [p[1] for p in pairs]})


def NUM(*pairs):
    return ("num", {"en": [p[0] for p in pairs], "zh": [p[1] for p in pairs]})


def T(key):
    return ("table", key)


PB = ("pb", None)


def FIG(name, note_en=None, note_zh=None):
    return ("fig", {"name": name, "note_en": note_en, "note_zh": note_zh})


def COLS(n):
    return ("cols", n)


TITLE_EN = ("Ranking by MSE Is Not Ranking for Deployment: A 28\u2011Model Reproduction and Benchmark "
            "of Influenza Forecasting")
TITLE_ZH = "以 MSE 排序不等于以部署为目标排序：流感预测的 28 模型复现与基准"

ABSTRACT_EN = (
    "Influenza forecasts exist to support decisions, but the literature ranks them by mean squared error. "
    "We report an independent reproduction of MIFlu (Moon et al., IEEE JBHI 2025) on the CDC national "
    "influenza series (966 weekly rows, 7 channels, bit-identical to the author's file) and a 28-model "
    "benchmark the original work does not contain: 13 conventional forecasters, four LLM-based "
    "forecasters (MIFlu and three published ones), and 11 frozen large-language-model encoders. The reproduction lands within "
    "4.5 % of the published four-horizon MSE mean (1.4995 against 1.4355) with a horizon-dependent sign: "
    "better at L=24 and L=36, worse at L=48 and L=60. On one common protocol (seeds 42/43/44; shared "
    "windows (W//16)*16 = 160/144/144/128) the accuracy champion is MIFlu (1.5574), ahead of PatchTST "
    "(1.6621) and NLinear (1.8716), and the spread across the roster is a factor of 3.6. On the "
    "epidemiological acceptance criterion of Kramer & Shaman (peak-timing error <= 1 week and "
    "peak-intensity error <= 25 % on ILITOTAL de-normalised to patient counts), NLinear and MIFlu each pass "
    "4 of 16 cells, but differently: NLinear passes all four step-0 cells with a peak-intensity error of "
    "3.2 %, while MIFlu's passes sit at 18.3-24.8 %, against the boundary. PatchTST passes none: its timing "
    "is the best in the study (mean 1.240 weeks) but its intensity error is 32.8 %. Accuracy and "
    "calibration are positively rank-correlated across all 28 arms (Spearman rho = +0.74), so MSE is a "
    "useful screen; but the frontier is ordered the other way round, and the pass indicator is negatively "
    "rank-correlated with MSE (rho = -0.43, p = 0.023). Parameter count does not resolve the choice: the "
    "slope of MSE against log10(parameters) is +0.1171 with R2 = 0.0223, the Pareto set is {NLinear, 2,520 "
    "parameters; PatchTST, 531,878 parameters}, and the 211x parameter cost buys an 11.2 % MSE difference "
    "that does not survive Holm correction over the 136 pairs (p = 0.117; with n = 12 no pair can). None of "
    "the 11 frozen encoders passes the "
    "criterion, and every one is worse than a decision tree. We argue that the acceptance criterion should "
    "be reported next to MSE, and that an MSE-sorted leaderboard can point a deployment decision the wrong "
    "way."
)
ABSTRACT_ZH = (
    "流感预测的存在是为了支持决策，但文献按均方误差给它们排名。本文报告对 MIFlu（Moon 等，IEEE JBHI 2025）"
    "在美国 CDC 全国流感序列（966 个每周行、7 个通道，与作者文件逐位相同）上的独立复现，以及原工作所没有的"
    "28 模型基准：16 个传统预测模型、MIFlu 本身、3 个已发表的基于 LLM 的预测器，以及 11 个冻结大语言模型编码器。"
    "复现落在已发表四跨度 MSE 均值的 4.5 % 以内（1.4995 对 1.4355），符号随跨度翻转：L=24 与 L=36 更好，"
    "L=48 与 L=60 更差。在统一协议下（种子 42/43/44；共享窗口 (W//16)*16 = 160/144/144/128），精度冠军是 MIFlu"
    "（1.5574），其后为 PatchTST（1.6621）与 NLinear（1.8716），全部模型的跨度为 3.6 倍。在 Kramer & Shaman 的"
    "流行病学接受判据下（反归一化为患者人数的 ILITOTAL 上，峰值时间误差 <= 1 周且峰值强度误差 <= 25 %），"
    "NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部四个步 0 单元，峰值强度误差为 3.2 %；"
    "MIFlu 的通过点为 18.3-24.8 %，贴着边界。PatchTST 一个都不通过：其时序最准（均值 1.240 周），"
    "但强度误差为 32.8 %。在全部 28 个模型上，精度与校准呈正秩相关（Spearman rho = +0.74），因此 MSE 是有用的"
    "筛选；但前沿的排序正好相反，且通过标记与 MSE 呈负秩相关（rho = -0.43，p = 0.023）。参数量无法解决这一选择："
    "MSE 对 log10(参数量) 的斜率为 +0.1171，R2 = 0.0223；帕累托集合为 {NLinear 2,520 参数；PatchTST 531,878 参数}；"
    "211 倍参数成本换来的 11.2 % MSE 差异在 136 对 Holm 校正后不显著（p = 0.117；n = 12 时没有任何一对能存活）。"
    "11 个冻结编码器无一通过判据，"
    "且每一个都差于决策树。我们主张：应把接受判据与 MSE 并列报告，而按 MSE 排序的榜单可能把部署决策引向"
    "错误方向。")

KEYWORDS_EN = ("Influenza forecasting, reproduction study, benchmark, peak-timing error, peak-intensity error, "
               "evaluation protocol, model selection, frozen language-model encoders.")
KEYWORDS_ZH = ("流感预测；复现研究；基准；峰值时间误差；峰值强度误差；评测协议；模型选择；冻结语言模型编码器。")


def blocks(lang):
    b = []
    b.append(("ieee_title", TITLE_EN if lang == "en" else TITLE_ZH))
    b.append(("ieee_authors", {
        "en": "Author Name, *Member, IEEE* — Department of Electrical Engineering, City University of Hong Kong\n"
              "Supervisor: Prof. Katie Chan — Assessor: Name\n"
              "*(Draft: author block and funding note are placeholders.)*",
        "zh": "作者姓名，*IEEE 会员* —— 香港城市大学电子工程学系\n"
              "导师：Prof. Katie Chan —— 评阅人：姓名\n"
              "*(草稿：作者信息与资助说明为占位内容。)*"}))
    b.append(("ieee_abstract", {"label": {"en": "Abstract—", "zh": "摘要——"},
                                "text": {"en": ABSTRACT_EN, "zh": ABSTRACT_ZH}}))
    b.append(("ieee_keywords", {"label": {"en": "Index Terms—", "zh": "关键词——"},
                                "text": {"en": KEYWORDS_EN, "zh": KEYWORDS_ZH}}))

    # Single-column review draft: the result tables have 10 columns and cannot be
    # legible inside a two-column measure; the two-column IEEEtran layout is
    # restored at submission, once the tables are re-typeset in LaTeX.

    # ---------------------------------------------------------------- I
    b.append(H1("I. Introduction", "I. 引言"))
    b.append(P(
        "Influenza forecasting exists to support decisions: when to escalate a response, how much capacity "
        "to prepare, and when to announce that a season has peaked. The loss behind those decisions is not "
        "squared error. A forecast that is two weeks late on the peak, or 40 % low on its height, has failed "
        "the decision even if its average error is small; conversely, a forecast with a slightly larger "
        "average error but a well-placed, well-scaled peak can be the more useful object. Yet the "
        "literature's default ranking metric remains MSE, and model selection follows it.",
        "流感预测的存在是为了支持决策：何时升级响应、准备多少容量、何时宣布某季已过峰值。这些决策背后的损失不是"
        "平方误差。一个把峰值判断晚了两周、或把峰值高度低估 40 % 的预测，即使平均误差很小，也已经使决策失败；"
        "反之，平均误差略大但峰值位置与幅度都准确的预测，可能是更有用的对象。然而文献的默认排序指标仍是 MSE，"
        "模型选择也随之而行。"))
    b.append(P(
        "This paper tests that default on its own terms. We reproduce MIFlu (Moon et al., IEEE JBHI 2025), "
        "the current multimodal state of the art on CDC national influenza data, after removing the data "
        "leakage in its checkpoint selection; we place it in a 28-model benchmark under one set of windows "
        "and seeds; and we score every arm twice — once on the metric the literature reports (MSE) and once "
        "on the criterion public health applies (the Kramer & Shaman peak criterion). The two scorings do "
        "not agree, and the disagreement is systematic rather than marginal.",
        "本文按该默认标准本身来检验它。我们复现 MIFlu（Moon 等，IEEE JBHI 2025）——CDC 全国流感数据上当前的"
        "多模态最先进方法——并移除其检查点选择中的数据泄漏；把它放进同一窗口与种子下的 28 模型基准；"
        "然后对每个模型计分两次：一次用文献报告的指标（MSE），一次用公共卫生采用的判据（Kramer & Shaman 峰值判据）。"
        "两种计分并不一致，而且这种不一致是系统性的，不是边际的。"))
    b.append(P(
        "**Contributions.** (1) A leak-free reproduction of MIFlu that reports the per-horizon sign rather "
        "than a single mean, and therefore reports a crossover instead of an improvement. (2) A 28-arm "
        "benchmark under one protocol — 13 conventional forecasters, 4 LLM-based (MIFlu and 3 published), "
        "forecasters, and 11 frozen LLM encoders — with windows, seeds, metric and checkpoint rule held "
        "identical. (3) The finding that the deployment ordering is not the accuracy ordering: the frontier "
        "is inverted on peak calibration, and the acceptance verdict is negatively rank-correlated with MSE. "
        "(4) A parameter-cost and significance analysis showing that the 211x cost of the accuracy "
        "runner-up buys a difference this benchmark cannot resolve.",
        "**贡献。** (1) 对 MIFlu 的无泄漏复现，报告逐跨度符号而非单一均值，因而报告的是符号交叉而不是改进。"
        "(2) 统一协议下的 28 模型基准——16 个传统预测模型、MIFlu、3 个已发表的基于 LLM 的预测器、11 个冻结 LLM "
        "编码器——窗口、种子、指标与检查点规则完全一致。(3) 发现部署排序不是精度排序：前沿在峰值校准上反转，"
        "且接受判定与 MSE 呈负秩相关。(4) 参数成本与显著性分析，说明精度亚军 211 倍的成本换来的差异在本基准下"
        "无法分辨。"))

    # ---------------------------------------------------------------- II
    b.append(H1("II. Related Work", "II. 相关工作"))
    b.append(P(
        "**Long-horizon forecasting architectures.** PatchTST (Nie et al., ICLR 2023) patches the input "
        "series and uses channel independence, and reports three-seed means over standard benchmarks; "
        "iTransformer (Liu et al., ICLR 2024) inverts the attention axis and does the same. Zeng et al. "
        "(AAAI 2023) argued that a linear model is competitive with transformer forecasters, a claim our "
        "benchmark reproduces in the influenza setting: NLinear is third of 28 arms with three orders of "
        "magnitude fewer parameters than the accuracy champion.",
        "**长跨度预测架构。** PatchTST（Nie 等，ICLR 2023）对输入序列做分片并采用通道独立性，在标准基准上报告"
        "三种子均值；iTransformer（Liu 等，ICLR 2024）反转注意力轴，同样如此。Zeng 等（AAAI 2023）主张线性模型"
        "可与 Transformer 预测器竞争，本文基准在流感场景中复现了这一主张：NLinear 在 28 个模型中排第三，"
        "参数量比精度冠军少三个数量级。"))
    b.append(P(
        "**Epidemiological evaluation.** Kramer & Shaman (2019) established the criterion this paper adopts: "
        "a forecast is useful only if its peak-timing error is at most one week and its peak-intensity error "
        "at most 25 %. The epidemiological literature scores per fixed forecast step; the machine-learning "
        "literature scores per horizon. We report both, because they are not the same object: a model can win "
        "on one and lose on the other.",
        "**流行病学评估。** Kramer & Shaman（2019）确立了本文采用的判据：只有当峰值时间误差不超过一周、"
        "峰值强度误差不超过 25 % 时，预测才算有用。流行病学文献按固定预测步计分，机器学习文献按跨度计分。"
        "本文同时报告两者，因为它们不是同一对象：模型可以在一个上获胜、在另一个上失败。"))
    b.append(P(
        "**Frozen foundation-model features.** A frozen encoder with a small trained head is a strong "
        "baseline for non-text modalities, and MIFlu itself relies on a frozen GPT-2 backbone with a textual "
        "prompt and low-rank adaptation. Whether the *choice* of encoder matters at the scale of a 966-row "
        "epidemiological series has not been established. Section VI-F reports that experiment: eleven "
        "encoders, one shared linear head, and a negative result.",
        "**冻结基础模型特征。** “冻结编码器 + 小训练头”是非文本模态的强基线，MIFlu 本身就依赖冻结的 GPT-2 主干、"
        "文本提示与低秩适配。尚未确立的是：在 966 行流行病学序列的规模上，编码器的*选择*是否有影响。"
        "第 VI-F 节报告该实验：十一个编码器、一个共享线性头，以及一个负面结果。"))
    b.append(P(
        "**Reproduction and benchmark studies.** Reproduction work is increasingly recognised as a "
        "contribution in its own right, because a benchmark is only as useful as its protocol. Our "
        "contribution is of that kind: we do not propose a new architecture, we make the existing comparison "
        "honest and then measure what the honest comparison says.",
        "**复现与基准研究。** 复现工作正日益被视为独立的贡献，因为基准的价值不会超过其协议。本文的贡献属于"
        "这一类：我们不提出新架构，而是让现有比较变得诚实，然后测量这个诚实的比较说了什么。"))

    # ---------------------------------------------------------------- III
    b.append(H1("III. Data", "III. 数据"))
    b.append(P(
        f"The data are the CDC national influenza surveillance series distributed with MIFlu: {D.N_ROWS} "
        f"weekly rows and {D.N_CHANNELS} numeric channels (`% WEIGHTED ILI`, `% UNWEIGHTED ILI`, `AGE 0-4`, "
        "`AGE 5-24`, `ILITOTAL`, `NUM. OF PROVIDERS`, `OT`). The local file was verified bit-identical to "
        "the author's released file (maximum absolute difference 0.000e+00) before any model was trained, "
        "because a single mis-joined week would move every number in this paper. The split is chronological "
        "70/10/20 — rows 0-675 training, 676-772 validation, 773-965 test — with a strict containment guard "
        "so that a window's input span lies entirely before its target span; the minimum admitted test "
        "target-start row is 773. Standardisation uses a StandardScaler fitted on the training block only "
        f"(ILITOTAL mean {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f} patients, sd "
        f"{D.SCALER_STD[D.ILITOTAL_IDX]:,.2f}; OT mean {D.SCALER_MEAN[D.OT_IDX]:,.0f}).",
        f"数据是随 MIFlu 发布的美国 CDC 全国流感监测序列：{D.N_ROWS} 个每周行、{D.N_CHANNELS} 个数值通道"
        "（`% WEIGHTED ILI`、`% UNWEIGHTED ILI`、`AGE 0-4`、`AGE 5-24`、`ILITOTAL`、`NUM. OF PROVIDERS`、`OT`）。"
        "在任何模型训练之前，本地文件已被验证与作者发布文件逐位相同（最大绝对差 0.000e+00），因为只要有一周错位，"
        "本文的每个数字都会移动。划分为按时间 70/10/20——第 0-675 行训练、676-772 行验证、773-965 行测试——"
        "并带严格包含约束，使窗口的输入区间完全位于目标区间之前；被接纳的测试目标起始行最小下标为 773。"
        f"标准化使用仅在训练段上拟合的 StandardScaler（ILITOTAL 均值 {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f} 人，"
        f"标准差 {D.SCALER_STD[D.ILITOTAL_IDX]:,.2f}；OT 均值 {D.SCALER_MEAN[D.OT_IDX]:,.0f}）。"))
    b.append(P(
        "The scaling constants decide the metric design. Seven channels whose training means span 1.74 to "
        "493,629 cannot be averaged into a quantity with a physical unit: the 7-variable aggregate is a "
        "loss, not a series, and it cannot be de-normalised into patient counts. Peak-skill metrics therefore "
        "use `ILITOTAL` alone.",
        "标准化常数决定了指标设计。七个通道的训练均值从 1.74 到 493,629，无法平均成一个具有物理单位的量："
        "7 变量聚合是一个损失值而不是序列，无法反归一化为患者人数。因此峰值技巧指标只使用 `ILITOTAL`。"))

    # ---------------------------------------------------------------- IV
    b.append(H1("IV. Method", "IV. 方法"))
    b.append(H2("A. Two protocols", "A. 两套协议"))
    b.append(P(
        "The reproduction uses 10 repetitions with seeds 2021-2030, matching the original author, and "
        "validation-selected checkpoints. The benchmark uses 3 seeds, 42/43/44, for every arm, and the same "
        "checkpoint rule. They are separate experiments and their numbers are never compared; MIFlu appears "
        "under both because a reproduction and a benchmark row impose incompatible requirements, and only the "
        "reproduction instance is quoted as a reproduction.",
        "复现使用 10 次重复、种子 2021-2030，与原作者的协议一致，并使用验证集选择的检查点。基准对每个模型使用 "
        "3 个种子 42/43/44，以及相同的检查点规则。它们是两个不同的实验，其数字从不互相比较；MIFlu 同时出现在"
        "两者之下，是因为“复现”与“基准行”提出了互不兼容的要求，而只有复现实例被作为复现引用。"))
    b.append(H2("B. Evaluation windows", "B. 评测窗口"))
    b.append(P(D.WINDOW_WHY_EN, D.WINDOW_WHY_ZH))
    b.append(H2("C. Metrics", "C. 指标"))
    b.append(P(
        "**Accuracy** is the 7-variable aggregate MSE and MAE in standardised space, averaged over channels "
        "and windows, reported per horizon and as a four-horizon mean. **Peak skill** de-normalises "
        "`ILITOTAL` to patient counts and measures, per season, the peak-timing error (PTE, weeks) and the "
        "peak-intensity error (PIE, % of the observed peak), at fixed steps 0/1/2/3 = 1/2/3/4 weeks ahead. A "
        "cell passes only if PTE <= 1 week **and** PIE <= 25 %. The thresholds are attributed to Kramer & "
        "Shaman (2019) and are marked [to verify] against the original text; peak detection "
        "(find_peaks(prominence = 0.15 x range, distance = 15), ±8-week matching) is this study's "
        "engineering choice, not part of the published criterion.",
        "**精度**是标准化空间下的 7 变量聚合 MSE 与 MAE，对通道与窗口取平均，按跨度报告并给出四跨度均值。"
        "**峰值技巧**把 `ILITOTAL` 反归一化为患者人数，逐季节度量峰值时间误差（PTE，周）与峰值强度误差"
        "（PIE，占观测峰值的百分比），在固定步 0/1/2/3（即提前 1/2/3/4 周）上评估。只有 PTE <= 1 周**且** "
        "PIE <= 25 % 的单元才算通过。阈值归因于 Kramer & Shaman（2019），并标注 [to verify] 待与原文核对；"
        "峰值检测（find_peaks(prominence = 0.15 x range, distance = 15)，±8 周匹配）是本研究的工程选择，"
        "不是已发表判据的一部分。"))
    b.append(H2("D. Checkpoint selection", "D. 检查点选择"))
    b.append(P(
        "Every model selects its checkpoint on the validation block. The author's code selects on the test "
        "set (`main_ILI_lora.py`, lines 211 and 225); that is data leakage and is not replicated. The "
        "deviation is disclosed wherever a reproduction number appears.",
        "每个模型在验证段上选择检查点。作者的代码在测试集上选择（`main_ILI_lora.py` 第 211 与 225 行）；"
        "这属于泄漏，本文不复刻。凡出现复现数字之处均披露该偏离。"))
    b.append(H2("E. Statistics", "E. 统计"))
    b.append(P(
        f"Paired comparisons use exact sign-flip tests on the 12 matched (horizon x seed) cells, with "
        f"Holm-Bonferroni correction over all {D.N_PAIRS} pairs of the 17 non-encoder arms (MIFlu and the 11 "
        f"encoders are outside this family), a bootstrap 95 % CI (10,000 "
        f"resamples), and Cohen's d. All arms share the same three seeds, which is what makes the 12 cells "
        f"matched; with n = 12 the smallest attainable p is 2/2¹² ≈ 0.00049, and we state that floor rather "
        f"than hide it. {D.N_RAW_SIG} of {D.N_PAIRS} pairs are significant before correction; after proper Holm "
        f"none survives, because the smallest attainable adjusted p is {D.HOLM_MIN:.3f}.",
        f"配对比较在 12 个配对（跨度 x 种子）单元上使用精确符号翻转检验，对全部 {D.N_PAIRS} 对模型做 "
        f"Holm-Bonferroni 校正，并给出 bootstrap 95 % 置信区间（10,000 次重采样）与 Cohen's d。所有模型共享"
        f"同三个种子，这正是 12 个单元可以配对的原因；n = 12 时最小可达 p 为 2/2¹² ≈ 0.00049，我们如实说明"
        f"该下限而不隐藏。{D.N_PAIRS} 对中有 {D.N_RAW_SIG} 对在校正前显著；正确 Holm 校正后无一存活，因为最小可达"
        f"校正 p 为 {D.HOLM_MIN:.3f}。"))
    b.append(H2("F. Hardware and provenance", "F. 硬件与来源"))
    b.append(P(
        "The 204 cells of the 17 arms (13 conventional, 3 published LLM-based, and DLinear) ran on an "
        "A100-SXM4-80GB in the `stingy` partition of "
        "CityU HPC Burgundy, with GPU model, partition, node and job id recorded per cell; the MIFlu and "
        "encoder cells ran on the same partition with per-cell manifests on the cluster. Twelve NLinear "
        "cells were first measured on a V100-SXM2-32GB and re-run on A100; the two agree to 1e-6, so no "
        "ranking depends on the hardware. No timing claim is made anywhere in this paper.",
        "17 个传统模型的 204 个单元在香港城市大学 Burgundy 集群 `stingy` 分区的 A100-SXM4-80GB 上运行，"
        "逐单元记录 GPU 型号、分区、节点与作业号；MIFlu 与编码器单元在同一分区运行，并在集群上留有逐单元清单。"
        "12 个 NLinear 单元最初在 V100-SXM2-32GB 上测得，后在 A100 上重跑；两者一致到 1e-6，因此没有任何排名"
        "依赖硬件。本文不作任何计时断言。"))

    # ---------------------------------------------------------------- V
    b.append(H1("V. Experiments", "V. 实验"))
    b.append(P(
        "Four analyses are reported, in this order. **Reproduction (Table I):** ten repetitions at four "
        "horizons against the published values. **Accuracy (Table II):** 28 arms x four horizons x three "
        "seeds, ranked by the four-horizon mean. **Peak skill (Tables III-IV):** the Kramer & Shaman "
        "criterion, per fixed step, on de-normalised patient counts. **Efficiency and significance (Tables "
        "V-VI):** a Pareto frontier and a log-parameter regression, then Holm-corrected paired tests. A "
        "fifth axis — frozen LLM encoders (Table VII) — and the ablation ladder (Table VIII) complete the "
        "matrix; the ladder is in progress and is reported as a design, not as a result.",
        "本文按以下顺序报告四项分析。**复现（表 I）：** 四个跨度各十次重复，对照已发表数值。"
        "**精度（表 II）：** 28 个模型 x 4 个跨度 x 3 个种子，按四跨度均值排序。**峰值技巧（表 III-IV）：** "
        "Kramer & Shaman 判据，按固定步，在反归一化后的患者人数上计算。**效率与显著性（表 V-VI）：** "
        "帕累托前沿与对数参数回归，然后是 Holm 校正配对检验。第五条轴——冻结 LLM 编码器（表 VII）——与消融阶梯"
        "（表 VIII）补全矩阵；阶梯仍在进行中，作为设计而非结果报告。"))

    # ---------------------------------------------------------------- VI
    b.append(H1("VI. Results", "VI. 结果"))
    b.append(H2("A. The reproduction", "A. 复现"))
    b.append(P(
        "The four-horizon mean is 1.4995 against the published 1.4355, i.e. 4.5 % worse, and the per-horizon "
        "sign flips: better at L=24 (1.3045 vs 1.542) and L=36 (1.3561 vs 1.422), worse at L=48 (1.6543 vs "
        "1.414) and L=60 (1.6829 vs 1.364). The MAE side behaves the same way (0.8043 against 0.7452, "
        "+7.9 %). Reporting only the mean would have hidden the structure. Two explanations remain "
        "consistent with the pattern — validation-based checkpoint selection, and long-horizon variance (the "
        "ten repetitions span 1.401-1.984 at L=60) — and the data cannot yet separate them.",
        "四跨度均值为 1.4995，对比已发表的 1.4355，即差 4.5 %，且逐跨度符号翻转：L=24（1.3045 对 1.542）与 "
        "L=36（1.3561 对 1.422）更好，L=48（1.6543 对 1.414）与 L=60（1.6829 对 1.364）更差。MAE 一侧同样"
        "（0.8043 对 0.7452，+7.9 %）。只报告均值会藏起这一结构。有两种解释仍与该模式相符——基于验证集的"
        "检查点选择，以及长跨度方差（十次重复在 L=60 的范围是 1.401-1.984）——现有数据尚无法区分。"))
    b.append(T("reproduction"))
    b.append(P(
        "**Takeaway.** The reproduction is a reproduction, not an improvement: 4.5 % on the four-horizon "
        "mean, with a sign that depends on the horizon. The two disclosed deviations mean the per-horizon "
        "wins cannot be claimed as superiority over the original.",
        "**要点。** 这是一次复现，不是改进：四跨度均值差 4.5 %，且符号依赖跨度。两处已披露的偏离意味着"
        "逐跨度的胜出不能主张为“优于原论文”。"))
    b.append(H2("B. Accuracy: the 28-arm ranking", "B. 精度：28 模型排名"))
    b.append(P(
        "MIFlu is the accuracy champion at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716); the "
        "spread across all 28 arms is 1.5574 to 5.6155, a factor of 3.6, and all 28 beat the seasonal-naive "
        f"reference ({D.seasonal_mean():.4f}). The two published LLM-based forecasters are beaten by a "
        "nearest-neighbour baseline (KNN 3.7854 against Qwen-Time 5.2557 and CALF 5.5785). A linear model "
        "with 2,520 parameters is third of 28, ahead of every transformer except PatchTST.",
        f"MIFlu 是精度冠军，1.5574，其后是 PatchTST（1.6621）与 NLinear（1.8716）；28 个模型的跨度为 1.5574 到 "
        f"5.6155，即 3.6 倍，且全部 28 个都优于季节朴素基线（{D.seasonal_mean():.4f}）。两个已发表的基于 LLM 的"
        "预测器被最近邻基线击败（KNN 3.7854 对 Qwen-Time 5.2557、CALF 5.5785）。一个 2,520 参数的线性模型在 "
        "28 个模型中排第三，除 PatchTST 外领先所有 Transformer。"))
    b.append(T("benchmark"))
    b.append(P(
        "**Takeaway.** Accuracy alone does not identify a deployable model. The top three are within 20 % of "
        "each other in MSE, and the ranking says which model fits this test set best, not which supports the "
        "decision the forecast exists for.",
        "**要点。** 仅凭精度无法确定可部署的模型。前三名的 MSE 彼此相差在 20 % 以内，而排名说明的是哪个模型"
        "最拟合这个测试集，而不是哪个支持预测本来要服务的决策。"))
    b.append(H2("C. Peak skill: the deployment ordering", "C. 峰值技巧：部署排序"))
    b.append(P(
        f"On the Kramer & Shaman criterion the ranking changes. NLinear and MIFlu each pass 4 of 16 cells, "
        f"but differently: NLinear passes all four step-0 cells with a peak-intensity error of "
        f"{D.KS['nlinear']['step0_pie']:.1f} %, while MIFlu's four passes sit at PIE 18.3-24.8 %, against "
        f"the 25 % boundary, and it misses L=48 at step 0 (PTE 1.22 weeks). PatchTST passes none: its timing "
        f"is the best in the study (mean PTE {D.KS['patchtst']['mean_pte']:.2f} weeks) but its PIE is "
        f"{D.KS['patchtst']['mean_pie']:.1f} %, so it fails the calibration half in every cell. Every other "
        f"arm fails both halves.",
        f"在 Kramer & Shaman 判据下，排名发生变化。NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部"
        f"四个步 0 单元，峰值强度误差为 {D.KS['nlinear']['step0_pie']:.1f} %；MIFlu 的四个通过点为 PIE "
        f"18.3-24.8 %，贴着 25 % 边界，且在 L=48 步 0 失败（PTE 1.22 周）。PatchTST 一个都不通过：其时序是"
        f"本研究最准的（均值 PTE {D.KS['patchtst']['mean_pte']:.2f} 周），但 PIE 为 "
        f"{D.KS['patchtst']['mean_pie']:.1f} %，在每个单元都未满足校准一半。其余每个模型在两半上都不通过。"))
    b.append(T("pte"))
    b.append(T("ks_grid"))
    b.append(P(
        f"**Takeaway (Finding 1).** The deployment ordering is not the accuracy ordering. Across all 28 arms "
        f"better MSE does go with better calibration (Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f} against mean "
        f"PIE), so MSE is a useful screen; but among the three lowest-MSE arms the calibration order is "
        f"inverted at both ends — NLinear (3rd) {D.KS['nlinear']['mean_pie']:.1f} %, MIFlu (1st) "
        f"{D.KS['miflu']['mean_pie']:.1f} %, PatchTST (2nd) {D.KS['patchtst']['mean_pie']:.1f} % — and the "
        f"pass indicator is negatively rank-correlated with MSE (ρ = {D.DECOUPLE['rho_pass']:.2f}, "
        f"p = {D.DECOUPLE['p_pass']:.3f}). The MSE runner-up passes nothing; the third-best passes every "
        f"horizon one week ahead.",
        f"**要点（发现 1）。** 部署排序不是精度排序。在全部 28 个模型上，MSE 更好确实伴随校准更好"
        f"（对均值 PIE 的 Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f}），因此 MSE 是有用的筛选；但在 MSE 最低的"
        f"三个模型中，校准排序完全反转——NLinear（第 3）{D.KS['nlinear']['mean_pie']:.1f} %、"
        f"MIFlu（第 1）{D.KS['miflu']['mean_pie']:.1f} %、PatchTST（第 2）"
        f"{D.KS['patchtst']['mean_pie']:.1f} %——且通过标记与 MSE 呈负秩相关"
        f"（ρ = {D.DECOUPLE['rho_pass']:.2f}，p = {D.DECOUPLE['p_pass']:.3f}）。MSE 第二名一个都不通过；"
        f"第三名通过每个跨度的提前一周。"))
    b.append(H2("D. Accuracy against efficiency", "D. 精度与效率"))
    b.append(P(
        f"The slope of MSE against log10(parameters) across the 11 parametric arms is "
        f"+{D.PARETO['slope']:.4f} with R² = {D.PARETO['r2']:.4f}: size explains about 2 % of the variance "
        f"and its sign is unfavourable. The Pareto set is exactly two models — NLinear at 2,520 parameters "
        f"and PatchTST at 531,878 — i.e. {D.PARETO['ratio']:.0f}x the parameters for "
        f"{D.PARETO['mse_gain_pct']:.1f} % lower MSE. Whether that is a good trade depends on the "
        f"deployment, and on whether the deployment needs peak skill: if it does, the 11.2 % advantage buys "
        f"a model that fails the criterion outright.",
        f"在 11 个含参数模型上，MSE 对 log10(参数量) 的斜率为 +{D.PARETO['slope']:.4f}，R² = "
        f"{D.PARETO['r2']:.4f}：规模只解释约 2 % 的方差，且符号不利。帕累托集合恰好两个模型——2,520 参数的 "
        f"NLinear 与 531,878 参数的 PatchTST——即 {D.PARETO['ratio']:.0f} 倍参数量换取 "
        f"{D.PARETO['mse_gain_pct']:.1f} % 的 MSE 下降。这笔交易是否划算取决于部署场景，也取决于部署是否需要"
        f"峰值技巧：若需要，那 11.2 % 的优势换来的却是一个完全不能满足判据的模型。"))
    b.append(T("efficiency"))
    b.append(H2("E. Statistical significance", "E. 统计显著性"))
    b.append(P(
        f"The pair the Pareto argument needs is NLinear vs PatchTST: mean Δ MSE +0.2095 in PatchTST's "
        f"favour, NLinear lower in only {int(D.PAIR.wins_a)} of 12 cells, raw p = "
        f"{float(D.PAIR.p_raw):.4f}, and **p(Holm) = {float(D.PAIR.p_holm):.3f}** after correction over all "
        f"{D.N_PAIRS} pairs; d = {float(D.PAIR.effect_d):.2f}. That pair is the {D.PAIR_RANK}th smallest of "
        f"the {D.N_PAIRS} p-values, so a table sorted by significance would omit it — which is why Table VI "
        f"prints it first and the six most significant pairs below it.",
        f"帕累托论证所需的那一对是 NLinear 对 PatchTST：平均 Δ MSE 为 +0.2095（对 PatchTST 有利），"
        f"NLinear 只在 12 个单元中的 {int(D.PAIR.wins_a)} 个更低，原始 p = {float(D.PAIR.p_raw):.4f}，"
        f"而在全部 {D.N_PAIRS} 对上校正后 **p(Holm) = {float(D.PAIR.p_holm):.3f}**；"
        f"d = {float(D.PAIR.effect_d):.2f}。这一对在 {D.N_PAIRS} 个 p 值中排第 {D.PAIR_RANK} 小，"
        f"因此按显著性排序的表会省略它——这正是表 VI 把它放在第一行、把六个最显著的对放在下面的原因。"))
    b.append(T("paired"))
    b.append(P(
        f"**Takeaway (Finding 2).** The 211x cost buys an 11.2 % MSE difference that this benchmark cannot "
        f"resolve at n = 12. This is a failure to reject equality, not a proof of equivalence "
        f"(d = {float(D.PAIR.effect_d):.2f}; PatchTST is lower in {12 - int(D.PAIR.wins_a)} of 12 cells). "
        f"The defensible conclusion is “no accuracy advantage is established for the 211x cost”.",
        f"**要点（发现 2）。** 211 倍成本换来的 11.2 % MSE 差异，在本基准的 n = 12 下无法分辨。这是“未能拒绝"
        f"相等”，不是“证明相等”（d = {float(D.PAIR.effect_d):.2f}；PatchTST 在 12 个单元中的 "
        f"{12 - int(D.PAIR.wins_a)} 个更低）。可辩护的结论是“未能为 211 倍成本确立精度优势”。"))
    b.append(H2("F. Frozen LLM encoders", "F. 冻结 LLM 编码器"))
    b.append(P(
        f"Eleven encoders (Qwen2.5-1.5B; DeepSeek-R1-Distill-Qwen at 1.5B, 7B, 14B and 32B; "
        f"DeepSeek-R1-Distill-Llama-8B; Hunyuan-1.8B/4B/7B; ContextPilot-8B/14B) were each frozen and "
        f"paired with one shared linear head, trained channel-independently: 132 of 156 cells. The best is "
        f"Hunyuan-1.8B at {D.ENC['best_mse']:.4f} and the worst Qwen2.5-1.5B at {D.ENC['worst_mse']:.4f}, "
        f"i.e. {D.ENC['ratio_best']:.2f}x to {D.ENC['ratio_worst']:.2f}x the MSE of MIFlu. Every one is "
        f"worse than a decision tree (4.3198), and none passes the Kramer & Shaman criterion in any cell. "
        f"The ordering inside the family is not a monotone function of size.",
        f"十一个编码器（Qwen2.5-1.5B；DeepSeek-R1-Distill-Qwen 的 1.5B、7B、14B、32B；"
        f"DeepSeek-R1-Distill-Llama-8B；Hunyuan-1.8B/4B/7B；ContextPilot-8B/14B）各自冻结，并接同一个共享"
        f"线性头、按通道独立训练：156 个单元中完成 132 个。最好是 Hunyuan-1.8B，{D.ENC['best_mse']:.4f}；"
        f"最差是 Qwen2.5-1.5B，{D.ENC['worst_mse']:.4f}，即 MIFlu 的 {D.ENC['ratio_best']:.2f} 至 "
        f"{D.ENC['ratio_worst']:.2f} 倍。每一个都差于决策树（4.3198），且没有任何一个在任何单元通过 "
        f"Kramer & Shaman 判据。家族内部的排序不是规模的单调函数。"))
    b.append(T("llm"))
    b.append(P(
        "**Takeaway (Finding 3).** The protocol was designed to give the idea its best chance — frozen "
        "features, a linear read-out, channel independence — and it still fails. This does not prove that an "
        "encoder can never help, but a claimed gain from frozen language features on this task owes both a "
        "mechanism and a control.",
        "**要点（发现 3）。** 协议被设计成给该想法最好的机会——冻结特征、线性读出、通道独立——而它仍然失败。"
        "这不能证明编码器永远不可能有帮助，但任何声称在本任务上从冻结语言特征获得增益的主张，都需要给出"
        "机制与对照。"))
    b.append(H2("G. The ablation ladder", "G. 消融阶梯"))
    b.append(P(
        "The ladder asks where MIFlu's accuracy comes from: the LoRA adaptation, or the depth of the GPT-2 "
        "stack. It is five variants (no LoRA; K = 2, 4, 8, 12 layers) at four horizons and three seeds — 60 "
        "cells — compared against the full K=6 arm already in Table II. One result is established and it is "
        "negative about the text branch: the text tokens sit behind the causal mask and the head reads only "
        "the time patches, so `--no-text` is bit-identical to the full arm (asserted by "
        "`tests_archive/test_miflu_ablations.py`), which means a text ablation is a structural verification, not an "
        "effect. At the snapshot this draft is built from, 27 of the 60 cells for the remaining variants were "
        "complete, so no depth trend is claimed. The ladder is reported as a design and a status, not as a "
        "result.",
        "阶梯要问 MIFlu 的精度从何而来：LoRA 适配，还是 GPT-2 堆叠的深度。它是五个变体（去掉 LoRA；"
        "K = 2、4、8、12 层）在 4 个跨度与 3 个种子上共 60 个单元，与表 II 中已有的完整 K=6 臂比较。"
        "有一项结果已经确立，而且是关于文本分支的负面结论：文本 token 位于因果掩码之后、输出头只读时间分片，"
        "因此 `--no-text` 与完整臂逐位相同（由 `tests_archive/test_miflu_ablations.py` 断言），这意味着文本消融是"
        "结构验证，不是效应。在本草稿所依据的快照中，其余变体的 60 个单元里完成 27 个，因此不声明任何深度趋势。"
        "阶梯作为设计与状态报告，不作为结果。"))
    b.append(T("ablation"))

    # ---------------------------------------------------------------- VII
    b.append(H1("VII. Threats to Validity", "VII. 效度威胁"))
    b.append(P(
        "**Single dataset.** All results come from one 966-row national series in one country. Nothing here "
        "establishes cross-dataset or cross-region generality, and the regional and rolling-origin "
        "evaluations that would test it are not yet run.",
        "**单一数据集。** 所有结果都来自一个国家的一条 966 行全国序列。本文不能确立跨数据集或跨区域的普适性，"
        "而本可检验它的区域评测与滚动原点评测尚未运行。"))
    b.append(P(
        "**Resolution of the tests.** With n = 12 matched cells the smallest attainable p is 2/2¹² ≈ 0.00049, "
        "and a non-significant result is a failure to reject, not evidence of equivalence. We therefore "
        "phrase the Pareto conclusion as “no advantage established”, not “no advantage”.",
        "**检验的分辨率。** 在 n = 12 个配对单元下，最小可达 p 为 2/2¹² ≈ 0.00049；不显著的结果是“未能拒绝”，"
        "而不是“相等的证据”。因此我们把帕累托结论表述为“未能确立优势”，而不是“没有优势”。"))
    b.append(P(
        "**Criterion attribution.** The 1-week / 25 % thresholds are attributed to Kramer & Shaman (2019) "
        "but are marked [to verify] against the original text, and the peak detector is our own engineering "
        "choice. A different detector would move PTE/PIE, though it would not move the MSE ranking.",
        "**判据归属。** 1 周 / 25 % 阈值归因于 Kramer & Shaman（2019），但标注 [to verify] 待与原文核对；"
        "峰值检测器是我们自己的工程选择。不同的检测器会改变 PTE/PIE，但不会改变 MSE 排名。"))
    b.append(P(
        "**Scope of the encoder axis.** The experiment tests frozen features with a linear read-out. It does "
        "not test generation, prompting or fine-tuning, and its negative result must not be read as a claim "
        "about LLM forecasters in general — MIFlu, which is fine-tuned, is the accuracy champion.",
        "**编码器维度的范围。** 该实验测试的是冻结特征加线性读出，不测试生成、提示或微调；其负面结果不可"
        "读作关于 LLM 预测器的一般性主张——经过微调的 MIFlu 恰恰是精度冠军。"))
    b.append(P(
        "**Incomplete ablation.** The depth and LoRA questions are open until the 60 cells are aggregated. "
        "The manuscript reports the ladder's design and its completion count, and claims no trend.",
        "**消融未完成。** 在 60 个单元聚合之前，深度与 LoRA 的问题仍未回答。本文报告阶梯的设计与完成数，"
        "不声明任何趋势。"))
    b.append(P(
        "**The reproduction's two deviations.** Validation-based checkpoint selection and the 7-variable "
        "metric are necessary for a leak-free, table-comparable result, but they mean the per-horizon wins "
        "are not a like-for-like claim of superiority.",
        "**复现的两处偏离。** 基于验证集的检查点选择与 7 变量指标是无泄漏、可与表 V 比较的结果所必需的，"
        "但它们意味着逐跨度的胜出不是同条件的“优于”主张。"))

    # ---------------------------------------------------------------- VIII
    b.append(H1("VIII. Conclusion", "VIII. 结论"))
    b.append(P(
        "We reproduced MIFlu within 4.5 % on the four-horizon MSE mean with a horizon-dependent sign, "
        "benchmarked 28 forecasters under one protocol, and showed that the deployment ordering is not the "
        "accuracy ordering: the accuracy champion is not the calibration champion, the MSE runner-up passes "
        "no cell of the epidemiological criterion, and the model that passes every horizon one week ahead "
        "has 2,520 parameters against the runner-up's 531,878 and is the cheaper member of the Pareto "
        "frontier. "
        "Parameter count is not a proxy for accuracy (slope +0.1171, R² 0.0223), and the 211x cost buys a "
        "difference this benchmark cannot resolve (p(Holm) = 0.117; no pair survives the 136-pair correction). "
        "Eleven frozen LLM encoders fail "
        "outright. The practical conclusion is that model selection for epidemiological forecasting should "
        "be made on the acceptance criterion, with MSE reported alongside it, and that a leaderboard sorted "
        "by MSE alone can point a deployment decision the wrong way.",
        "本文在四跨度 MSE 均值上把 MIFlu 复现到 4.5 % 以内（符号随跨度翻转），在统一协议下基准评估了 28 个"
        "预测模型，并证明部署排序不是精度排序：精度冠军不是校准冠军；MSE 亚军不通过任何一格流行病学判据；"
        "而每个跨度都提前一周通过的那个模型，参数量比亚军少 211 倍，并且是帕累托前沿中更便宜的一员。"
        "参数量不是精度的代理（斜率 +0.1171，R² 0.0223），而 211 倍成本换来的差异在本基准下无法分辨"
        "（p(Holm) = 0.117；136 对校正后无一存活）。十一个冻结 LLM 编码器则直接失败。实践结论是：流行病学预测的"
        "模型选择应基于"
        "接受判据，并把 MSE 并列报告；仅按 MSE 排序的榜单可能把部署决策引向错误方向。"))

    # ---------------------------------------------------------------- IX
    b.append(H1("IX. References", "IX. 参考文献"))
    b.append(("refs", {
        "en": [
            "[1] J. Moon et al., “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting,” *IEEE J. "
            "Biomed. Health Inform.*, 2025, doi: 10.1109/JBHI.2025.3561214.",
            "[2] Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, “A Time Series is Worth 64 Words: "
            "Long-term Forecasting with Transformers,” in *Proc. ICLR*, 2023, arXiv:2211.14730.",
            "[3] Y. Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series "
            "Forecasting,” in *Proc. ICLR*, 2024.",
            "[4] A. Zeng, M. Chen, L. Zhang, and Q. Xu, “Are Transformers Effective for Time Series "
            "Forecasting?” in *Proc. AAAI*, 2023.",
            "[5] A. M. Kramer and J. Shaman, “Development and validation of influenza forecasting for 64 "
            "temperate and tropical countries,” *PLOS Comput. Biol.*, vol. 15, no. 2, e1006742, 2019, "
            "doi: 10.1371/journal.pcbi.1006742.",
            "[6] Centers for Disease Control and Prevention, “FluView: Weekly U.S. Influenza Surveillance "
            "Report,” national ILI series (966 weekly rows, 7 channels).",
            "[7] Qwen Team, “Qwen2.5 Technical Report,” 2024; DeepSeek-AI, “DeepSeek-R1,” 2025; Tencent "
            "Hunyuan and ContextPilot model cards, HuggingFace.",
        ],
        "zh": [
            "[1] J. Moon 等，“MIFlu: Large Language Model-Based Multimodal Influenza Forecasting”，*IEEE J. "
            "Biomed. Health Inform.*，2025，doi: 10.1109/JBHI.2025.3561214。",
            "[2] Y. Nie, N. H. Nguyen, P. Sinthong, J. Kalagnanam，“A Time Series is Worth 64 Words: Long-term "
            "Forecasting with Transformers”，*Proc. ICLR*，2023，arXiv:2211.14730。",
            "[3] Y. Liu 等，“iTransformer: Inverted Transformers Are Effective for Time Series Forecasting”，"
                 "*Proc. ICLR*，2024。",
            "[4] A. Zeng, M. Chen, L. Zhang, Q. Xu，“Are Transformers Effective for Time Series Forecasting?”，"
                 "*Proc. AAAI*，2023。",
            "[5] A. M. Kramer, J. Shaman，“Development and validation of influenza forecasting for 64 temperate "
                 "and tropical countries”，*PLOS Comput. Biol.*，第 15 卷第 2 期，e1006742，2019，"
                 "doi: 10.1371/journal.pcbi.1006742。",
            "[6] 美国疾病控制与预防中心，“FluView: Weekly U.S. Influenza Surveillance Report”，全国 ILI 序列"
                 "（966 个每周行、7 个通道）。",
            "[7] Qwen 团队，“Qwen2.5 Technical Report”，2024；DeepSeek-AI，“DeepSeek-R1”，2025；腾讯 Hunyuan "
                 "与 ContextPilot 模型卡，HuggingFace。",
        ]}))
    b.append(("refs_note", {
        "en": "Volume, page and DOI details are to be completed at submission and checked against the publisher's "
              "record; author, title, venue and year are asserted in this draft.",
        "zh": "卷号、页码与 DOI 将在投稿时补全并对照出版方记录核对；本草稿断言作者、标题、发表处与年份。"}))

    # ---------------------------------------------------------------- appendix
    b.append(PB)
    b.append(H1("Appendix A. Forecast panels", "附录 A. 预测曲线"))
    b.append(P(
        "The panels below show step-wise forecasts against ground truth for three representative arms at the "
        "shortest horizon (L = 24). Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks "
        "ahead; the y-axis is ILITOTAL in patient counts. Complete panels for all 28 arms x 4 horizons are "
        "available in the supplementary material.",
        "下图展示三个代表性模型在最短跨度（L = 24）上逐步预测与真值的对比。黑 = 真值；每步 0/1/2/3"
        "（提前 1/2/3/4 周）一条预测线；纵轴为 ILITOTAL 患者数。全部 28 个模型 x 4 个跨度的完整图见补充材料。"))
    b.append(FIG("fig_forecast_miflu_L24.png"))
    b.append(FIG("fig_forecast_patchtst_L24.png"))
    b.append(FIG("fig_forecast_nlinear_L24.png"))
    return b
