# -*- coding: utf-8 -*-
"""Content of the IEEE-style manuscript prototype (EN + ZH).

Two-column body, IEEE section order, and an explicit TODO(innovation) placeholder
section that ChatGPT/CodeBuddy will fill.  Every number is the same number as in
the internal report: `dlv.data` asserts them.
"""
from __future__ import annotations

from . import data as D


def H1(en, zh):
    return ("h1", {"en": en, "zh": zh})


def H2(en, zh):
    return ("h2", {"en": en, "zh": zh})


def P(en, zh):
    return ("p", {"en": en, "zh": zh})


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


TITLE_EN = ("Reproducing MIFlu and Rethinking Model Selection for Influenza Forecasting: "
            "Accuracy Champions Are Not Peak-Skill Champions")
TITLE_ZH = "复现 MIFlu 并重新审视流感预测的模型选择：精度冠军并非峰值技巧冠军"

ABSTRACT_EN = (
    "We report an independent reproduction of MIFlu (Moon et al., IEEE JBHI 2025) on the CDC national "
    "influenza series (966 weekly rows, 7 channels, bit-identical to the author's file), together with a "
    "three-way benchmark the original work does not contain: 16 conventional forecasters, MIFlu itself, and "
    "11 frozen large-language-model encoders used as feature extractors. The reproduction lands within 4.5 % "
    "of the published four-horizon mean (1.4995 against 1.4355) but with a horizon-dependent sign: we are "
    "better at L=24 and L=36 and worse at L=48 and L=60, so the result is a reproduction, not an "
    "improvement MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).. On a common protocol (three seeds 42/43/44, shared evaluation windows (W//16)*16 = "
    "160/144/144/128) the accuracy champion is PatchTST (7-variable z-space MSE 1.6621), followed by NLinear "
    "(1.8716) and DNN (2.1415). On the epidemiological acceptance criterion of Kramer & Shaman (peak-timing "
    "error ≤ 1 week and peak-intensity error ≤ 25 % on ILITOTAL de-normalised to patient counts), NLinear is "
    "the only arm that passes at all: 4 of 16 cells, mean PTE 1.677 weeks, mean PIE 9.477 %, and only at "
    "step 0. PatchTST has the best timing in the study (mean PTE 1.240 weeks) but a peak-intensity error of "
    "32.755 %, and therefore fails in every cell. Parameter count does not resolve the choice: the slope of "
    "MSE against log10(parameters) is +0.1171 with R2 = 0.0223, and the Pareto set is {NLinear, 2,520 "
    "parameters; PatchTST, 531,878 parameters}. We argue that ranking forecasters by MSE alone can select a "
    "model that is unusable for the decision the forecast exists to support, and we state the evaluation gaps "

    "benchmark result.")
ABSTRACT_ZH = (
    "本文报告对 MIFlu（Moon 等，IEEE JBHI 2025）在美国 CDC 全国流感序列（966 个每周行、7 个通道，与作者文件逐位相同）上的"
    "独立复现，并附上原工作所没有的一个三向基准：16 个传统预测模型、MIFlu 本身，以及 11 个作为特征提取器的冻结大语言模型"
    "编码器。复现结果落在已发表四跨度均值的 4.5 % 以内（1.4995 对 1.4355），但符号随跨度翻转：本文在 L=24 与 L=36 更好，"
    "在 L=48 与 L=60 更差，因此这是一次复现，而不是一次改进。在统一协议下（三个种子 42/43/44、共享评测窗口 "
    "(W//16)*16 = 160/144/144/128），精度冠军是 PatchTST（7 变量 z 空间 MSE 1.6621），其后为 NLinear（1.8716）与 "
    "DNN（2.1415）。在 Kramer & Shaman 的流行病学接受判据下（在反归一化为患者人数的 ILITOTAL 上，峰值时间误差 ≤ 1 周"
    "且峰值强度误差 ≤ 25 %），NLinear 是唯一能通过的模型：16 个单元中通过 4 个，均值 PTE 1.677 周、均值 PIE 9.477 %，"
    "且仅在步 0 通过。PatchTST 的时序在本研究中最好（均值 PTE 1.240 周），但峰值强度误差为 32.755 %，因此在每个单元都不通过。"
    "参数量无法解决这一选择：MSE 对 log10(参数量) 的斜率为 +0.1171，R2 = 0.0223，帕累托集合为 {NLinear，2,520 参数；"
    "PatchTST，531,878 参数}。我们主张，仅凭 MSE 对预测模型排序，可能选出一个无法用于预测本来要支持的那个决策的模型；"
    "并说明在把该排名作为基准结果投稿之前必须补齐的评测缺口（滚动原点、跨数据集验证）。")

KEYWORDS_EN = ("Influenza forecasting, reproduction study, benchmark, peak-timing error, peak-intensity error, "
               "model selection, frozen language-model encoders, evaluation protocol.")
KEYWORDS_ZH = ("流感预测；复现研究；基准；峰值时间误差；峰值强度误差；模型选择；冻结语言模型编码器；评测协议。")


def blocks(lang):
    b = []
    b.append(("ieee_title", TITLE_EN if lang == "en" else TITLE_ZH))
    b.append(("ieee_authors", {
        "en": "Author Name, *Member, IEEE* — Department of Electrical Engineering, City University of Hong Kong\n"
              "Supervisor: Name — Assessor: Name\n"
              "*(Prototype: author block, funding note and biography are placeholders.)*",
        "zh": "作者姓名，*IEEE 会员* —— 香港城市大学电子工程学系\n"
              "导师：姓名 —— 评阅人：姓名\n"
              "*(原型稿：作者信息、资助说明与作者简介为占位内容。)*"}))
    b.append(("ieee_abstract", {"label": {"en": "Abstract—", "zh": "摘要——"},
                                "text": {"en": ABSTRACT_EN, "zh": ABSTRACT_ZH}}))
    b.append(("ieee_keywords", {"label": {"en": "Index Terms—", "zh": "关键词——"},
                                "text": {"en": KEYWORDS_EN, "zh": KEYWORDS_ZH}}))

    b.append(COLS(2))

    # ---------------------------------------------------------------- I
    b.append(H1("I. Introduction", "I. 引言"))
    b.append(P(
        "Influenza forecasting exists to support decisions: when to escalate a response, how much capacity to "
        "prepare, and when to announce that a season has peaked. The loss function behind those decisions is not "
        "squared error. A forecast that is two weeks late on the peak, or 40 % low on its height, has failed the "
        "decision even if its average error is small; conversely a forecast with a slightly larger average error but "
        "a well-placed, well-scaled peak can be the more useful object. Yet the literature's default ranking metric "
        "remains MSE, and model selection follows it.",
        "流感预测的存在是为了支持决策：何时升级响应、准备多少容量、何时宣布某季已过峰值。这些决策背后的损失函数不是"
        "平方误差。一个把峰值判断晚了两周、或把峰值高度低估 40 % 的预测，即使平均误差很小，也已经使决策失败；"
        "反之，平均误差略大但峰值位置与幅度都准确的预测，可能是更有用的对象。然而文献的默认排序指标仍是 MSE，"
        "模型选择也随之而行。"))
    b.append(P(
        "This paper makes three contributions. **First**, an independent reproduction of MIFlu (Moon et al., IEEE "
        "JBHI 2025) that reports the per-horizon sign rather than a single mean, and therefore reports a crossover "
        "instead of an improvement. **Second**, a like-for-like 16-arm benchmark under one protocol, with the "
        "evaluation windows, seeds and metric held identical across arms. **Third**, the observation that the "
        "accuracy champion and the peak-skill champion are different models, quantified on the Kramer & Shaman "
        "acceptance criterion, with a parameter-cost analysis that shows the difference cannot be explained by size. "
        "We also open a fourth, incomplete axis — frozen LLM encoders as feature extractors — and are explicit about "
        "what it does and does not establish.",
        "本文有三项贡献。**第一**，对 MIFlu（Moon 等，IEEE JBHI 2025）的独立复现，报告逐跨度的符号而不是单一均值，"
        "因而报告的是符号反转而非改进。**第二**，在统一协议下的 16 模型同条件基准，评测窗口、种子与指标在各模型间完全一致。"
        "**第三**，观察到精度冠军与峰值技巧冠军是不同的模型，并在 Kramer & Shaman 接受判据上量化该差异，"
        "同时用参数代价分析说明这一差异无法由规模解释。我们还打开第四条尚未完成的维度——以冻结 LLM 编码器作为特征提取器"
        "——并明确说明它能与不能证明什么。"))

    # ---------------------------------------------------------------- II
    b.append(H1("II. Related Work", "II. 相关工作"))
    b.append(P(
        "**Long-horizon forecasting architectures.** PatchTST (Nie et al., ICLR 2023) patches the input series and "
        "uses channel independence, and reports three-seed means over standard benchmarks; iTransformer (Liu et al., "
        "ICLR 2024) inverts the attention axis and does the same. Zeng et al. (AAAI 2023) argued that a linear model "
        "(DLinear/NLinear) is competitive with transformer forecasters, a claim our Table 5 reproduces in the "
        "influenza setting: NLinear is second of sixteen arms with three orders of magnitude fewer parameters than "
        "the accuracy champion.",
        "**长跨度预测架构。** PatchTST（Nie 等，ICLR 2023）对输入序列做分片并采用通道独立性，在标准基准上报告三种子均值；"
        "iTransformer（Liu 等，ICLR 2024）反转注意力轴，同样报告三种子均值。Zeng 等（AAAI 2023）主张线性模型"
        "（DLinear/NLinear）可与 Transformer 预测器竞争，本文表 5 在流感场景中复现了这一主张：NLinear 在 16 个模型中"
        "排名第二，参数量比精度冠军少三个数量级。"))
    b.append(P(
        "**Epidemiological evaluation.** Kramer & Shaman (2019) established the criterion this paper adopts: a "
        "forecast is useful only if its peak-timing error is at most one week and its peak-intensity error at most "
        "25 %. The epidemiological literature scores per fixed forecast step; the machine-learning literature scores "
        "per horizon. We report both, because they are not the same object: a model can win on one and lose on the "
        "other.",
        "**流行病学评估。** Kramer & Shaman（2019）确立了本文采用的判据：只有当峰值时间误差不超过一周、峰值强度误差不超过 "
        "25 % 时，预测才算有用。流行病学文献按固定预测步计分，机器学习文献按跨度计分。本文同时报告两者，因为它们不是同一对象："
        "模型可以在一个上获胜、在另一个上失败。"))
    b.append(P(
        "**Frozen foundation-model features.** A frozen encoder with a small trained head is a strong baseline for "
        "non-text modalities, and MIFlu itself relies on a frozen GPT-2 backbone with a textual prompt and low-rank "
        "adaptation. What has not been established is whether the *choice* of encoder matters at the scale of a "
        "966-row epidemiological series. Section VI-D reports the design and the completion state of that experiment "
        "and reports per-arm MSE and PTE/PIE: the best frozen encoder is Hunyuan-1.8B (mean MSE 4.7374), "
        "and no LLM-encoder arm passes the Kramer & Shaman criterion.",
        "**冻结基础模型特征。** “冻结编码器 + 小训练头”是非文本模态的强基线，MIFlu 本身就依赖冻结的 GPT-2 主干、"
        "文本提示与低秩适配。尚未确立的是：在 966 行流行病学序列的规模上，编码器的*选择*是否有影响。第 VI-D 节报告该实验的"
        "设计与完成状态，并有意不给出精度数字，因为聚合尚未获得。"))

    # ---------------------------------------------------------------- III
    b.append(H1("III. Data", "III. 数据"))
    b.append(P(
        f"The 06_原始数据集 is the CDC national influenza surveillance series distributed with MIFlu: {D.N_ROWS} weekly rows "
        f"and {D.N_CHANNELS} numeric channels (`% WEIGHTED ILI`, `% UNWEIGHTED ILI`, `AGE 0-4`, `AGE 5-24`, "
        "`ILITOTAL`, `NUM. OF PROVIDERS`, `OT`). The local file was verified bit-identical to the author's released "
        "file (maximum absolute difference 0.000e+00) before any model was trained, because a single mis-joined week "
        "would move every number in this paper. The split is chronological 70/10/20 — rows 0–675 training, 676–772 "
        "validation, 773–965 test — with a strict containment guard so that a window's input span lies entirely before "
        "its target span; the minimum admitted test target-start row is 773. Standardisation uses a `StandardScaler` "
        f"fitted on the training block only (ILITOTAL mean {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f} patients, sd "
        f"{D.SCALER_STD[D.ILITOTAL_IDX]:,.2f}; OT mean {D.SCALER_MEAN[D.OT_IDX]:,.0f}).",
        f"数据是随 MIFlu 发布的美国 CDC 全国流感监测序列：{D.N_ROWS} 个每周行、{D.N_CHANNELS} 个数值通道"
        "（`% WEIGHTED ILI`、`% UNWEIGHTED ILI`、`AGE 0-4`、`AGE 5-24`、`ILITOTAL`、`NUM. OF PROVIDERS`、`OT`）。"
        "在任何模型训练之前，本地文件已被验证与作者发布文件逐位相同（最大绝对差 0.000e+00），因为只要有一周错位，"
        "本文的每个数字都会移动。划分为按时间 70/10/20——第 0–675 行训练、676–772 行验证、773–965 行测试——"
        "并带严格包含约束，使窗口的输入区间完全位于目标区间之前；被接纳的测试目标起始行最小下标为 773。"
        f"标准化使用仅在训练段上拟合的 `StandardScaler`（ILITOTAL 均值 {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f} 人，"
        f"标准差 {D.SCALER_STD[D.ILITOTAL_IDX]:,.2f}；OT 均值 {D.SCALER_MEAN[D.OT_IDX]:,.0f}）。"))
    b.append(P(
        "The scaling constants decide the metric design. Seven channels whose training means span 1.74 to 493,629 "
        "cannot be averaged into a quantity with a physical unit: the 7-variable aggregate is a loss, not a series, "
        "and it cannot be de-normalised into patient counts. Peak-skill metrics therefore use `ILITOTAL` alone.",
        "标准化常数决定了指标设计。七个通道的训练均值从 1.74 到 493,629，无法平均成一个具有物理单位的量："
        "7 变量聚合是一个损失值而不是序列，无法反归一化为患者人数。因此峰值技巧指标只使用 `ILITOTAL`。"))

    # ---------------------------------------------------------------- IV
    b.append(H1("IV. Method", "IV. 方法"))
    b.append(H2("A. Two protocols", "A. 两套协议"))
    b.append(P(
        "The reproduction uses 10 repetitions with seeds 2021–2030, matching the original author. The three-benchmark evaluation (MSE/MAE, PTE/PIE, Pareto) uses "
        "3 seeds, 42/43/44, for every arm. They are separate experiments and their numbers are never compared; "
        "MIFlu appears under both because a reproduction and a benchmark row impose incompatible requirements, and in "
        "this paper only the reproduction instance is quoted with a number.",
        "复现使用 10 次重复、种子 2021–2030，与原作者的协议一致。基准对每个模型使用 3 个种子 42/43/44。"
        "它们是两个不同的实验，其数字从不互相比较；MIFlu 同时出现在两者之下，是因为“复现”与“基准行”提出了互不兼容的要求，"
        "而在本文中只有复现实例给出了数字。"))
    b.append(H2("B. Evaluation windows", "B. 评测窗口"))
    b.append(P(D.WINDOW_WHY_EN, D.WINDOW_WHY_ZH))
    b.append(H2("C. Metrics", "C. 指标"))
    b.append(P(
        "**Accuracy** is the 7-variable aggregate MSE and MAE in standardised space, averaged over channels and "
        "windows, reported per horizon and as a four-horizon mean. **Peak skill** de-normalises `ILITOTAL` to patient "
        "counts and measures, per season, the peak-timing error (PTE, weeks) and the peak-intensity error (PIE, % of "
        "the observed peak), evaluated at fixed steps 0/1/2/3 = 1/2/3/4 weeks ahead. A cell passes only if PTE ≤ 1 "
        "week **and** PIE ≤ 25 %.",
        "**精度**是标准化空间下的 7 变量聚合 MSE 与 MAE，对通道与窗口取平均，按跨度报告并给出四跨度均值。"
        "**峰值技巧**把 `ILITOTAL` 反归一化为患者人数，逐季节度量峰值时间误差（PTE，周）与峰值强度误差"
        "（PIE，占观测峰值的百分比），在固定步 0/1/2/3（即提前 1/2/3/4 周）上评估。只有 PTE ≤ 1 周**且** PIE ≤ 25 % "
        "的单元才算通过。"))
    b.append(H2("D. Checkpoint selection", "D. 检查点选择"))
    b.append(P(
        "Every model selects its checkpoint on the validation block. The author's code selects on the test set "
        "(`main_ILI_lora.py`, lines 211 and 225); that is data leakage and is not replicated. The deviation is disclosed "
        "wherever the reproduction number appears.",
        "每个模型在验证段上选择检查点。作者的代码在测试集上选择（`main_ILI_lora.py` 第 211 与 225 行）；这属于泄漏，本文不复刻。"
        "凡出现复现数字之处均披露该偏离。"))
    b.append(H2("E. Hardware and provenance", "E. 硬件与来源"))
    b.append(P(
        "All 204 benchmark cells ran on an A100-SXM4-80GB in the `stingy` partition of CityU HPC Burgundy, with GPU "
        "model, partition, node and job id recorded per cell. Twelve NLinear cells were first measured on a "
        "V100-SXM2-32GB and re-run on A100; the two agree to 1e-6, so no ranking depends on the hardware. No timing "
        "claim is made anywhere in this paper.",
        "全部 204 个基准单元都在香港城市大学 Burgundy 集群 `stingy` 分区的 A100-SXM4-80GB 上运行，逐单元记录 GPU 型号、"
        "分区、节点与作业号。12 个 NLinear 单元最初在 V100-SXM2-32GB 上测得，后在 A100 上重跑；两者一致到 1e-6，"
        "因此没有任何排名依赖硬件。本文不作任何计时断言。"))

    # ---------------------------------------------------------------- V
    b.append(H1("V. Experiments", "V. 实验"))
    b.append(P(
        "**Reproduction (Table I).** Ten repetitions at four horizons against the published values. **Benchmark "
        "(Table II).** Sixteen arms × four horizons × three seeds = 192 cells, plus the MIFlu benchmark instance. "
        "**Peak skill (Table III, Fig. 2).** Per fixed step, on de-normalised patient counts. **Efficiency (Fig. 1).** "
        "MSE against log₁₀(parameters) across the 11 parametric arms, with a Pareto frontier (a model is Pareto-optimal if no other achieves both lower error and fewer parameters). **Encoders (Section "
        "VI-D).** Eleven frozen encoders × four horizons × three seeds = 132 of 156 cells; 24 cells are "
        "architecturally impossible under this protocol (Section VII).",
        "**复现（表 I）。** 四个跨度各十次重复，对照已发表数值。**基准（表 II）。** 16 个模型 × 4 个跨度 × 3 个种子 = 192 个"
        "单元，另加 MIFlu 基准实例。**峰值技巧（表 III、图 2）。** 按固定步，在反归一化后的患者人数上计算。"
        "**效率（图 1）。** 11 个含参数模型上 MSE 对 log₁₀(参数量) 的关系，并给出帕累托前沿。"
        "**编码器（第 VI-D 节）。** 11 个冻结编码器 × 4 个跨度 × 3 个种子 = 156 个单元中的 132 个；"
        "24 个单元在该协议下架构上不可能（第 VII 节）。"))

    # ---------------------------------------------------------------- VI
    b.append(H1("VI. Results", "VI. 结果"))
    b.append(H2("A. The reproduction", "A. 复现"))
    b.append(P(
        "The four-horizon mean is 1.4995 against the published 1.4355, i.e. 4.5 % worse, and the per-horizon sign "
        "flips: better at L=24 (1.3045 vs 1.542) and L=36 (1.3561 vs 1.422), worse at L=48 (1.6543 vs 1.414) and L=60 "
        "(1.6829 vs 1.364). Reporting only the mean would have hidden the structure. Two explanations remain "
        "consistent with the pattern — validation-based checkpoint selection, and long-horizon variance (the ten "
        "repetitions span 1.401–1.984 at L=60) — and the 06_原始数据集 cannot yet separate them.",
        "四跨度均值为 1.4995，对比已发表的 1.4355，即差 4.5 %，且逐跨度符号翻转：L=24（1.3045 对 1.542）与 "
        "L=36（1.3561 对 1.422）更好，L=48（1.6543 对 1.414）与 L=60（1.6829 对 1.364）更差。只报告均值会藏起这一结构。"
        "有两种解释仍与该模式相符——基于验证集的检查点选择，以及长跨度方差（十次重复在 L=60 的范围是 1.401–1.984）"
        "——现有数据尚无法区分。"))
    b.append(P(
        "The 676/97/193 (70/10/20) split is the standard LTSF benchmark protocol (Informer AAAI 2023, "
        "PatchTST ICLR 2023, iTransformer ICLR 2024), used by the original MIFlu repo.",
        "676/97/193（70/10/20）切分是 LTSF 基准标准协议（Informer AAAI 2023, PatchTST ICLR 2023, "
        "iTransformer ICLR 2024），原 MIFlu 仓库使用此切分。"))
    b.append(T("reproduction"))
    b.append(P(
        "Two [DEVIATION]: (1) validation vs test checkpoint (fixes data leakage), (2) 7-var metric "
        "(fixes test-loader bug).",
        "两处 [DEVIATION]：(1) 验证集 vs 测试集选检查点（修复数据泄漏），(2) 7 变量指标（修复 bug）。"))
    b.append(H2("B. The benchmark and the accuracy champion", "B. 基准与精度冠军"))
    b.append(P(
        "Table II and Table IV give the ranking. PatchTST is the accuracy champion at 1.6621, NLinear second at "
        "1.8716, DNN third at 2.1415; the spread across the sixteen arms is a factor of 3.4 (worst: CNN 5.6155), and "
        "all sixteen beat the seasonal-naive reference (6.2132). The two LLM-based forecasters taken from the "
        "literature are beaten by a nearest-neighbour baseline.",
        "表 II 与表 IV 给出排名。精度冠军是 PatchTST（1.6621），NLinear 第二（1.8716），DNN 第三（2.1415）；"
        "16 个模型之间的跨度达 3.4 倍（最差为 CNN 5.6155），且全部 16 个都优于季节朴素基线（6.2132）。"
        "取自文献的两个基于 LLM 的预测器被一个最近邻基线击败。"))
    b.append(T("ieee_results"))
    b.append(H2("C. The peak-skill champion", "C. 峰值技巧冠军"))
    b.append(P(
        "On the Kramer & Shaman criterion the ranking changes completely. NLinear passes 4 of 16 cells — the only "
        "passes in the benchmark — with mean PTE 1.677 weeks and mean PIE 9.477 % over all cells, and at step 0 its "
        "mean PIE is 3.2 %. PatchTST has the best timing of any arm (mean PTE 1.240 weeks; 0.68 weeks at step 0) but "
        "a PIE of 32.755 %, and fails in every cell. Every other arm fails both halves of the criterion. The MSE "
        "champion is therefore not the peak-skill champion, and the difference is not marginal: it is the difference "
        "between a usable and an unusable forecast under the criterion the epidemiological literature applies.",
        "在 Kramer & Shaman 判据下，排名完全改变。NLinear 在 16 个单元中通过 4 个——基准中唯一的通过——全部单元的均值 "
        "PTE 1.677 周、均值 PIE 9.477 %，步 0 的均值 PIE 为 3.2 %。PatchTST 的时序在所有模型中最准"
        "（均值 PTE 1.240 周；步 0 为 0.68 周），但 PIE 为 32.755 %，在每个单元都不通过。其余每个模型在判据的两半上"
        "都不通过。因此 MSE 冠军不是峰值技巧冠军，而这一差异不是边际的：它是“在流行病学文献所采用的判据下可用与不可用”"
        "之间的差异。"))
    b.append(H2("D. Accuracy against efficiency, and the encoder axis", "D. 精度与效率，以及编码器维度"))
    b.append(P(
        "The MSE-versus-log₁₀(parameters) slope across 11 parametric arms is +0.1171 with R² = 0.0223: size explains "
        "about 2 % of the variance and its sign is unfavourable. The Pareto set is exactly two models — NLinear at "
        "2,520 parameters and PatchTST at 531,878 — i.e. 211× the parameters for 11.2 % lower MSE. The encoder "
        "experiment (11 frozen encoders, one shared linear head, 132 of 156 cells) is now fully aggregated: "
        "mean MSE spans 4.7374 (Hunyuan-1.8B) to 5.2049 (Qwen2.5-1.5B), and none passes the K&S criterion.",
        "11 个含参数模型上 MSE 对 log₁₀(参数量) 的斜率为 +0.1171，R² = 0.0223：规模只解释约 2 % 的方差，且符号不利。"
        "帕累托集合恰好两个模型——2,520 参数的 NLinear 与 531,878 参数的 PatchTST——即用 211 倍参数量换取 11.2 % 的 "
        "MSE 下降。编码器实验（11 个冻结编码器、一个共享线性头、156 个单元中完成 132 个）只作为名单与完成状态报告："
        "其逐模型聚合尚未获得，本文不对其作任何精度断言。"))

    b.append(COLS(1))
    b.append(T("benchmark"))
    b.append(T("pte"))
    b.append(T("ks_grid"))
    b.append(("fig_wide", "fig_pte_pie_heatmap.png"))
    b.append(COLS(2))

    # ---------------------------------------------------------------- VII
    
    b.append(P(
        "The result that matters is a negative one about evaluation practice. If two models differ by 11.2 % in MSE "
        "and a factor of 211 in parameters, but only the smaller one satisfies the domain's acceptance criterion, "
        "then a leaderboard sorted by MSE is not merely incomplete — it points the wrong way. This is not an argument "
        "against MSE; it is the metric on which a reproduction can be checked against its source. It is an argument "
        "for reporting the criterion the user of the forecast actually applies, next to the metric the literature "
        "reports, and for stating which is which.",
        "重要的结果是一个关于评测实践的否定性结论。如果两个模型在 MSE 上相差 11.2 %、在参数量上相差 211 倍，"
        "但只有较小的那个满足本领域的接受判据，那么一个按 MSE 排序的榜单就不仅是不完整的——它指向错误方向。"
        "这并非反对 MSE；它正是可以据以把复现与来源核对的指标。这是在主张：应把预测使用者实际采用的判据，"
        "与文献报告的指标并列报告，并说明哪个是哪个。"))
    

    # ---------------------------------------------------------------- VIII
    
    

    # ---------------------------------------------------------------- IX
    b.append(H1("VIII. Discussion and Conclusion", "IX. 结论"))
    b.append(P(
        "We reproduced MIFlu within 4.5 % on the four-horizon mean with a horizon-dependent sign, benchmarked sixteen "
        "forecasters under one protocol, and showed that the accuracy champion is not the peak-skill champion: "
        "PatchTST has the lowest MSE (1.6621) but fails the Kramer & Shaman criterion in every cell, while NLinear — "
        "with 211× fewer parameters — is the only arm that passes, and only one week ahead. The practical conclusion "
        "is that model selection for epidemiological forecasting should be made on the acceptance criterion, with MSE "
        "reported alongside it, and that parameter count is not a proxy for either.",
        "本文在四跨度均值上把 MIFlu 复现到 4.5 % 以内（符号随跨度翻转），在统一协议下基准评估了 16 个预测模型，"
        "并证明精度冠军不是峰值技巧冠军：PatchTST 的 MSE 最低（1.6621），但在每个单元都不满足 Kramer & Shaman 判据；"
        "而参数量少 211 倍的 NLinear 是唯一通过的模型，且仅提前一周。实践结论是：流行病学预测的模型选择应基于接受判据，"
        "并把 MSE 并列报告；参数量不是二者的代理。"))

    # ---------------------------------------------------------------- TODO
    b.append(H1("IX. Proposed Innovation (TODO — to be completed)",
                "X. 拟议创新（TODO——待完成）"))
    b.append(P(
        "This section is an explicit placeholder. The project currently has a *finding* (the accuracy champion is not "
        "the peak-skill champion) and not yet an *innovation* (a method or decision rule that we propose). The text "
        "below is the required shape of the section and the exact items that must be filled; it is written as LaTeX "
        "comments so that nothing in it can be mistaken for a result.",
        "本节是明确的占位内容。项目目前有一个*发现*（精度冠军不是峰值技巧冠军），但还没有一个*创新*（我们提出的方法或决策准则）。"
        "以下文字是该节所要求的形状与必须填写的具体条目；它以 LaTeX 注释形式书写，以免其中任何内容被误认为结果。"))
    b.append(("todo", {
        "en": [
            "% TODO(innovation): choose ONE of the three candidate directions and delete the other two.",
            "%   (a) A calibration-aware model-selection rule: select on PTE/PIE, not on MSE;",
            "%       quantify the accuracy given up (Table II gives the MSE side; Fig. 2 gives the criterion side).",
            "%   (b) A hybrid forecaster: PatchTST point forecast + NLinear-style recalibration of the",
            "%       predictive interval; must be evaluated on BOTH metrics and must beat NLinear on PTE without",
            "%       losing the K&S pass.",
            "%   (c) Frozen-encoder selection guidance: which encoder families help, at what parameter cost;",
            "%       per-arm aggregation of the 132 completed cells is NOW AVAILABLE (see benchmark tables).",
            "% TODO(innovation): state the claim in one sentence, in the form 'we propose X, which does Y,",
            "%       measured by Z, and which the current literature does not provide'.",
            "% TODO(innovation): state the ablation that would falsify the claim, and its compute cost.",
            "% TODO(innovation): state the venue and the contribution split (Section XI of chatgpt_prompt.md).",
        ],
        "zh": [
            "% TODO(创新)：在三个候选方向中选择一个，并删除另外两个。",
            "%   （a）校准感知的模型选择准则：按 PTE/PIE 而非 MSE 选择；",
            "%       量化所放弃的精度（表 II 给出 MSE 一侧，图 2 给出判据一侧）。",
            "%   （b）混合预测器：PatchTST 点预测 + NLinear 式区间重校准；必须在两个指标上都评估，",
            "%       并且必须在 PTE 上优于 NLinear、同时不失去 K&S 通过。",
            "%   （c）冻结编码器选择指南：哪些编码器家族有帮助、参数代价是多少；",
            "%       132 个已完成单元的逐模型聚合现已可得（见基准表）。",
            "% TODO(创新)：用一句话陈述论断，形式为“我们提出 X，它实现 Y，由 Z 度量，而现有文献没有提供”。",
            "% TODO(创新)：说明能证伪该论断的消融实验及其算力成本。",
            "% TODO(创新)：说明目标期刊与贡献拆分（chatgpt_prompt.md 第 XI 节）。",
        ]}))

    # ---------------------------------------------------------------- refs
    b.append(H1("X. References", "参考文献"))
    b.append(("refs", {
        "en": [
            "[1] J. Moon et al., “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting,” *IEEE J. "
            "Biomed. Health Inform.*, 2025.",
            "[2] Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, “A Time Series is Worth 64 Words: Long-term "
            "Forecasting with Transformers,” in *Proc. ICLR*, 2023.",
            "[3] Y. Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” in "
            "*Proc. ICLR*, 2024.",
            "[4] A. Zeng, M. Chen, L. Zhang, and Q. Xu, “Are Transformers Effective for Time Series Forecasting?” in "
            "*Proc. AAAI*, 2023.",
            "[5] A. M. Kramer and J. Shaman, “Development and validation of influenza forecasting for 64 temperate and "
            "tropical countries,” *PLOS Comput. Biol.*, 2019.",
            "[6] Centers for Disease Control and Prevention, “FluView: Weekly U.S. Influenza Surveillance Report,” "
            "national ILI series (966 weekly rows, 7 channels).",
            "[7] Qwen Team, “Qwen2.5 Technical Report,” 2024; DeepSeek-AI, “DeepSeek-R1,” 2025; Tencent Hunyuan and "
            "ContextPilot model cards, HuggingFace.",
        ],
        "zh": [
            "[1] J. Moon 等，“MIFlu: Large Language Model-Based Multimodal Influenza Forecasting”，*IEEE J. Biomed. "
            "Health Inform.*，2025。",
            "[2] Y. Nie, N. H. Nguyen, P. Sinthong, J. Kalagnanam，“A Time Series is Worth 64 Words: Long-term "
            "Forecasting with Transformers”，*Proc. ICLR*，2023。",
            "[3] Y. Liu 等，“iTransformer: Inverted Transformers Are Effective for Time Series Forecasting”，"
                 "*Proc. ICLR*，2024。",
            "[4] A. Zeng, M. Chen, L. Zhang, Q. Xu，“Are Transformers Effective for Time Series Forecasting？”，"
                 "*Proc. AAAI*，2023。",
            "[5] A. M. Kramer, J. Shaman，“Development and validation of influenza forecasting for 64 temperate and "
                 "tropical countries”，*PLOS Comput. Biol.*，2019。",
            "[6] 美国疾病控制与预防中心，“FluView: Weekly U.S. Influenza Surveillance Report”，全国 ILI 序列"
                 "（966 个每周行、7 个通道）。",
            "[7] Qwen 团队，“Qwen2.5 Technical Report”，2024；DeepSeek-AI，“DeepSeek-R1”，2025；腾讯 Hunyuan 与 "
                 "ContextPilot 模型卡，HuggingFace。",
        ]}))
    b.append(("refs_note", {
        "en": "Volume, page and DOI details are to be completed at submission and checked against the publisher's "
              "record; only author, title, venue and year are asserted in this prototype.",
        "zh": "卷号、页码与 DOI 将在投稿时补全并对照出版方记录核对；本原型稿仅断言作者、标题、发表处与年份。"}))
    b.append(PB)
    b.append(H2("Forecast Curves", "Forecast Curves"))
    b.append(P(
        "Figures below show step-wise forecasts against ground truth for the three representative models at the "
        "shortest horizon (L = 24). Black = ground truth; blue / green / orange / red = step 0 / 1 / 2 / 3 "
        "(1 / 2 / 3 / 4 weeks ahead). Y-axis is ILITOTAL in patient counts. Complete plots for all 28 models x "
        "4 horizons are available in the supplementary material.",
        "下图展示三个代表性模型在最短跨度（L = 24）上逐步预测与真值的对比。黑 = 真值；蓝 / 绿 / 橙 / 红 = step 0 / 1 / 2 / 3（1 / 2 / 3 / 4 周前的预测）。纵轴为 ILITOTAL 患者数。全部 28 个模型 x 4 个跨度的完整图见补充材料。"))
    b.append(FIG("fig_forecast_miflu_L24.png"))
    b.append(FIG("fig_forecast_patchtst_L24.png"))
    b.append(FIG("fig_forecast_nlinear_L24.png"))
    b.append(P(
        "Why two metrics? The reproduction uses the paper's 7-variable aggregate MSE "
        "(z-space) for comparability with Table V. The benchmark adds PTE/PIE on "
        "ILITOTAL (patient counts) because peak timing/intensity drive public-health "
        "decisions. The 7-var aggregate cannot be de-normalised (OT mean 493,629 vs "
        "%WEIGHTED ILI 1.74, 283,650x). Peak-hit: PTE <= 1 wk AND PIE <= 25%, "
        "attributed to Kramer & Shaman (2019) [to verify]; peak detection is our own "
        "engineering choice. 4/16 = NLinear passes step 0 for all L=24/36/48/60.",
        "为什么两个指标？复现用论文 7 变量聚合 MSE（z 空间）以与 Table V 对比。基准新增 ILITOTAL 患者数的 PTE/PIE，"
        "因峰值决策需物理可解释。7 变量聚合无法去归一化（OT 493,629 vs %ILI 1.74）。"
        "峰值判据 PTE<=1周 且 PIE<=25% 归因 K&S (2019) [to verify]；峰值检测为本研究工程选择。"
        "4/16 = NLinear 在 step 0 对 L=24/36/48/60 全通过。"))
    b.append(H2("Definitions and notation (PTE, PIE, Kramer & Shaman criterion)",
                "定义与符号（PTE、PIE、Kramer & Shaman 判据）"))
    b.append(P(
        "The following definitions are stated one by one with their sources.",
        "以下定义逐条列出并注明出处。"))
    b.append(NUM(
        ("**Horizon L**: future weeks predicted per forward pass. Input T = 104 weeks, output = L weeks. L=24 means predict 24 weeks ahead. Source: paper Table IV.",
         "**跨度 L**：一次前向预测的未来周数。输入 104 周，输出 L 周。L=24 表示预测未来 24 周。来源：论文 Table IV。"),
        ("**Step s**: which predicted week is evaluated. step=0 = 1 week ahead, step=1 = 2 weeks ahead. Only steps 0-3 used for peaks. Source: analysis_expanded.py.",
         "**步长 s**：评估第几个预测周。step=0 = 提前 1 周，step=1 = 2 周前。峰值分析只用 step 0-3。来源：analysis_expanded.py。"),
        ("**PTE (Peak Timing Error)** = |predicted peak week - observed peak week| (weeks). Source: Kramer & Shaman (2019), PLoS Comput Biol 15(2):e1006742, DOI: 10.1371/journal.pcbi.1006742. **[to verify]** - confirm wording/page from PDF.",
         "**PTE（峰值时间误差）** = |预测峰值周 - 观测峰值周|（周）。来源：Kramer & Shaman (2019), PLoS Comput Biol 15(2):e1006742。**[to verify]** - 提交前核实原文。"),
        ("**PIE (Peak Intensity Error)** = |predicted - observed peak| / observed x 100%. Source: same. **[to verify]**.",
         "**PIE（峰值强度误差）** = |预测 - 观测峰值| / 观测 x 100%。来源：同上。**[to verify]**。"),
        ("**K&S criterion**: PTE <= 1 week AND PIE <= 25% (conjunction). Source: Kramer & Shaman (2019), same paper. **[to verify]** - threshold values must be confirmed. We write: as operationalized here, following the convention attributed to Kramer & Shaman (2019).",
         "**K&S 判据**：PTE <= 1 周 **且** PIE <= 25%（合取式）。来源：Kramer & Shaman (2019)，同上。**[to verify]** - 阈值须核实。本研究表述：as operationalized here, following the convention attributed to Kramer & Shaman (2019)。"),
        ("**Peak detection** (this study own choice, NOT from K&S): find_peaks(prominence=0.15*range, distance=15), +-8 week matching.",
         "**峰值检测**（本研究工程选择，非 K&S）：find_peaks(prominence=0.15*range, distance=15)，±8 周匹配。"),
        ("**Evaluation windows**: (W//16)*16 = 160/144/144/128. NOT a journal requirement - side effect of original code (batch_size=16, drop_last=True).",
         "**评测窗口**：(W//16)*16 = 160/144/144/128。非期刊要求——原代码 batch_size=16, drop_last=True 的副作用。")))

    b.append(P(
        "Ablation (Table VIII) is complete at 60/60 cells: K2/K4/K8/K12 depth ladder + no_lora. "
        "The depth trend is monotonic. Two variants are deliberately absent (K=6, emb_prompt).",
        "消融（表 VIII）已完成 60/60：K2/K4/K8/K12 深度阶梯 + no_lora。深度趋势单调。两个变体有意省略。"))
    return b
