# -*- coding: utf-8 -*-
"""Content of the FYP progress report, following Requirements_ProjectProgressReport_2627A.

The school template has PART A (identity) and PART B sections 1, 2, 3, 4, 6, 7, 8
(there is no section 5 in the template).  The numbering below is identical to the
template so a reader can check compliance line by line.  PART A and PART B are
emitted by build_docs.py; this module starts at section 1.
"""
from __future__ import annotations

from . import data as D

TITLE_EN = "Reproducing MIFlu and Benchmarking Influenza Forecasting with Frozen LLM Encoders"
TITLE_ZH = "复现 MIFlu 并以冻结 LLM 编码器基准评估流感预测"


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


PART_A_EN = [
    ("Name of Student", "________________________________"),
    ("Student ID", "________________________________"),
    ("Programme-Major", "BEng (Hons) Electrical Engineering / ______________"),
    ("Project Code and Title", "________  " + TITLE_EN),
    ("Name of Supervisor", "Prof. Katie CHAN"),
    ("Name of Assessor", "________________________________"),
    ("Number of meetings with supervisor / assessor", "______ / ______"),
    ("Average number of hours spent on the project weekly", "________ hours/week"),
    ("Report date", "3 November 2026"),
]
PART_A_ZH = [
    ("学生姓名", "________________________________"),
    ("学生编号", "________________________________"),
    ("课程—主修", "电机工程工学士 / ______________"),
    ("项目编号与题目", "________  " + TITLE_ZH),
    ("导师姓名", "Prof. Katie CHAN"),
    ("评阅人姓名", "________________________________"),
    ("与导师 / 评阅人会面次数", "______ / ______"),
    ("每周平均投入时数", "________ 小时/周"),
    ("报告日期", "2026 年 11 月 3 日"),
]


def blocks(lang=None):
    b = []

    # 1. Project objectives
    b.append(H2("1. Project objectives", "1. 项目目标"))
    b.append(P(
        "**Problem statement.** Influenza forecasting directly affects public-health resource allocation: "
        "when to escalate a response, how much capacity to prepare, and when to announce that a season has "
        "peaked. Moon et al. (IEEE JBHI 2025) proposed MIFlu, a multimodal model that pairs a GPT-2 "
        "time-series encoder with text embeddings, and reported the best accuracy on CDC national influenza "
        "data. The paper, however, compares against two simple baselines, reports a single random seed, and "
        "selects its checkpoint on the test set — data leakage. A public-health team therefore cannot answer "
        "the question that matters: **is MIFlu the model we should deploy, and would we know if it were not?**",
        "**问题陈述。** 流感预测直接影响公共卫生资源分配：何时升级响应、准备多少床位与疫苗、何时宣布某季已过峰值。"
        "Moon 等（IEEE JBHI 2025）提出 MIFlu——一个把 GPT-2 时间序列编码器与文本嵌入结合的多模态模型——"
        "并在 CDC 全国流感数据上报告了最佳精度。但该论文只与两个简单基线比较、只报告单一随机种子，"
        "且在测试集上选择检查点——这是数据泄漏。因此公共卫生团队无法回答真正重要的问题："
        "**MIFlu 是不是我们该部署的模型？如果不是，我们能否知道？**"))
    b.append(P("**Objectives.**", "**目标。**"))
    b.append(NUM(
        ("**Reproduce MIFlu's Table V** under a rigorous protocol (10 seeds, validation-based checkpoint "
         "selection, 7-variable aggregate MSE) and quantify the gap against the published numbers, "
         "including its sign at each horizon.",
         "用严格协议**复现 MIFlu 的表 V**（10 个种子、验证集选择检查点、7 变量聚合 MSE），量化与已发表数值的"
         "差距，包括每个跨度上的符号。"),
        ("**Benchmark 28 forecasting models** (13 conventional + 4 LLM-based, MIFlu and 3 published, + "
         "11 frozen LLM encoders) on one protocol, scored on accuracy (MSE/MAE) and on peak-forecasting "
         "skill (PTE/PIE under the Kramer & Shaman criterion).",
         "在同一协议上**基准评估 28 个预测模型**（13 个传统模型 + 4 个基于 LLM 的预测器（MIFlu 与 3 个已发表）+ "
         "11 个冻结 LLM 编码器），同时用精度（MSE/MAE）与峰值预测技巧（Kramer & Shaman 判据下的 PTE/PIE）计分。"),
        ("**Determine which model a public-health team should deploy**, and test empirically whether large "
         "language models improve epidemiological forecasting at all.",
         "**确定公共卫生团队应部署哪个模型**，并用实验检验大语言模型是否真的改善流行病学预测。")))
    b.append(P(
        "**Scope.** The project is an empirical evaluation, not a new architecture. Its contribution is the "
        "measurement: a leak-free protocol, a 28-arm matrix under one set of windows and seeds, and an "
        "evaluation that separates accuracy from deployment value. No new loss function or prompt mechanism "
        "is proposed, and none is needed for the claims that are made.",
        "**范围。** 本项目是实证评估，不是新架构。其贡献在于测量：无泄漏的协议、在同一窗口与种子下的 28 模型矩阵，"
        "以及把精度与部署价值分开的评估。本文不提出新的损失函数或提示机制，所主张的结论也不需要它们。"))

    # 2. Planning chart
    b.append(H2("2. Original project planning chart", "2. 原始项目规划图"))
    b.append(BUL(
        ("**Sep 2026 (Weeks 1-4):** data acquisition and verification (966-week CDC series, byte-level "
         "check). Milestone: dataset confirmed identical — **done**.",
         "**2026 年 9 月（第 1-4 周）：** 数据获取与验证（966 周 CDC 序列，逐字节校验）。里程碑：数据集确认一致"
         "——**已完成**。"),
        ("**Oct 2026 (Weeks 5-8):** MIFlu code reconstruction, reproduction runs (10 seeds x 4 horizons). "
         "Milestone: Table V reproduced with a disclosed sign crossover — **done**.",
         "**2026 年 10 月（第 5-8 周）：** MIFlu 代码重建、复现实验（10 个种子 x 4 个跨度）。"
         "里程碑：表 V 复现完成，并披露符号交叉——**已完成**。"),
        ("**Nov 2026 (Weeks 9-12):** 28-model benchmark and frozen-encoder axis; ablation ladder queued; "
         "progress report and presentation. Milestone: benchmark complete — **benchmark done, ablation "
         "27/60 and running**.",
         "**2026 年 11 月（第 9-12 周）：** 28 模型基准与冻结编码器维度；消融阶梯排队；进度报告与汇报。"
         "里程碑：基准完成——**基准已完成，消融 27/60 运行中**。"),
        ("**Dec 2026 - Apr 2027:** regional evaluation, rolling-origin evaluation, manuscript, submission. "
         "Milestone: submitted manuscript — **planned**.",
         "**2026 年 12 月–2027 年 4 月：** 区域评测、滚动原点评测、手稿、投稿。里程碑：已投稿手稿——**计划中**。")))
    b.append(P(
        "The one schedule slip is the ablation ladder: it was planned for early November and is 27/60 at "
        "this report. It is a compute-queue delay, not a design change; the regional evaluation is gated "
        "behind it and has moved to late November.",
        "唯一的进度滑移是消融阶梯：原计划 11 月初完成，本报告时为 27/60。这是算力排队延迟，不是设计变更；"
        "区域评测排在其后，已移至 11 月下旬。"))

    # 3. Background study
    b.append(H2("3. Background study", "3. 背景研究"))
    b.append(P(
        "**Technical background.** Influenza forecasting has moved from statistical models (ARIMA, Prophet) "
        "to deep learning (LSTM, Transformer) and recently to large language models. MIFlu represents the "
        "last group: it fine-tunes a GPT-2 backbone with LoRA adapters on the CDC series and reports the best "
        "aggregate accuracy. Its comparison set is thin and its protocol has two problems — test-set "
        "checkpoint selection and a single seed — which is exactly the space in which an independent "
        "reproduction and a wider benchmark become useful.",
        "**技术背景。** 流感预测已从统计模型（ARIMA、Prophet）发展到深度学习（LSTM、Transformer），"
        "再到最近的大语言模型。MIFlu 属于最后一类：用 LoRA 适配器在 CDC 序列上微调 GPT-2 主干，并报告最佳"
        "聚合精度。它的比较集很薄，协议有两个问题——测试集选检查点与单一种子——而这正是独立复现与更广基准"
        "能发挥作用的空间。"))
    b.append(P(
        "**Contemporary and societal context.** After COVID-19, governments invested heavily in AI-based "
        "epidemic forecasting, and agencies such as the WHO and CDC use forecasts to allocate vaccines and "
        "antivirals. A forecast is useful to those decisions only if its peak is placed and scaled correctly: "
        "a curve that is two weeks late on the peak, or 40 % low on its height, fails the decision even when "
        "its average error is small. Yet the literature ranks models by MSE. That gap between the metric and "
        "the decision is the problem this project measures.",
        "**当代与社会背景。** 新冠疫情后，各国政府大量投资 AI 疫情预测，WHO 与 CDC 等机构用预测分配疫苗与抗病毒"
        "药物。只有当峰值的位置与幅度都正确时，预测才对这类决策有用：一条把峰值判断晚两周、或把峰值高度低估 "
        "40 % 的曲线，即使平均误差很小，也已经使决策失败。然而文献仍按 MSE 给模型排名。指标与决策之间的这道鸿沟，"
        "正是本项目要测量的对象。"))
    b.append(P(
        "**Gap identified.** Three things are missing from the current literature: (1) a reproduction of "
        "MIFlu that removes the test-set checkpoint leak; (2) a benchmark wide enough that the linear and "
        "classical baselines are represented; (3) an evaluation on the criterion public health actually "
        "applies, next to the criterion the literature reports. This project supplies all three.",
        "**识别的空白。** 现有文献缺三样东西：(1) 一个移除测试集检查点泄漏的 MIFlu 复现；"
        "(2) 一个宽到足以包含线性与经典基线的基准；(3) 在公共卫生真正使用的判据上、与文献报告的判据并列的评估。"
        "本项目三者兼备。"))

    # 4. Methodology
    b.append(H2("4. Methodology", "4. 方法"))
    b.append(P(
        "**Design.** Two protocols, never mixed. The reproduction protocol (10 seeds, 2021-2030; "
        "validation-selected checkpoint; 7-variable aggregate MSE) exists to compare with the paper's "
        "Table V. The benchmark protocol (3 seeds 42/43/44; shared windows (W//16)*16 = 160/144/144/128; "
        "one metric) exists to compare 28 models with each other. MIFlu is the only arm under both, and its "
        "two numbers are not comparable.",
        "**设计。** 两套协议，从不混用。复现协议（10 个种子 2021-2030；验证集选择检查点；7 变量聚合 MSE）"
        "用于与论文表 V 比较。基准协议（3 个种子 42/43/44；共享窗口 (W//16)*16 = 160/144/144/128；同一指标）"
        "用于 28 个模型互比。MIFlu 是唯一同时出现在两套协议下的模型，其两个数值不可比较。"))
    b.append(T("repro_params"))
    b.append(P(
        "**Two deliberate deviations.** (1) *Checkpoint selection*: the original code selects the best epoch "
        "on the test set (`main_ILI_lora.py`, lines 211 and 225), which is data leakage; we select on "
        "validation. (2) *The 7-variable metric*: the original test loader covers only 1 of 7 variables (a "
        "bug), while Table V is defined on the 7-variable aggregate; we fix the loader. Both are disclosed "
        "wherever a reproduction number appears.",
        "**两处故意偏离。** (1) *检查点选择*：原代码在测试集上选最优 epoch（`main_ILI_lora.py` 第 211、225 行），"
        "这是数据泄漏；我们改用验证集。(2) *7 变量指标*：原测试加载器只覆盖 7 个变量中的 1 个（bug），"
        "而表 V 定义在 7 变量聚合上；我们修复加载器。两处偏离凡出现复现数字处均予披露。"))
    b.append(P(
        "**Metrics and definitions.** Horizon L = weeks predicted ahead (input window T = 104 weeks). "
        "Step s = which predicted week is scored (step 0 = one week ahead). PTE (peak timing error) = "
        "|predicted peak week - observed peak week| in weeks; PIE (peak intensity error) = |predicted - "
        "observed peak| / observed peak x 100 %. A cell passes the Kramer & Shaman criterion only if "
        "PTE <= 1 week **and** PIE <= 25 %; the thresholds are attributed to Kramer & Shaman (2019) and are "
        "marked [to verify] against the original text. The peak detector "
        "(find_peaks(prominence = 0.15 x range, distance = 15), ±8-week matching) is this project's "
        "engineering choice, not part of the published criterion. PTE/PIE use ILITOTAL de-normalised to "
        "patient counts, because the 7-variable aggregate is a loss, not a series, and cannot be "
        "de-normalised.",
        "**指标与定义。** 跨度 L = 预测未来周数（输入窗口 T = 104 周）。步 s = 计分第几个预测周（步 0 = 提前一周）。"
        "PTE（峰值时间误差）= |预测峰值周 - 观测峰值周|（周）；PIE（峰值强度误差）= |预测 - 观测峰值| / 观测峰值 "
        "x 100 %。只有 PTE <= 1 周**且** PIE <= 25 % 时该格才通过 Kramer & Shaman 判据；阈值归因于 "
        "Kramer & Shaman（2019），并标注 [to verify] 待与原文核对。峰值检测器"
        "（find_peaks(prominence = 0.15 x range, distance = 15)，±8 周匹配）是本项目的工程选择，不是已发表判据的"
        "一部分。PTE/PIE 使用反归一化为患者人数的 ILITOTAL，因为 7 变量聚合是损失值而不是序列，无法反归一化。"))
    b.append(P(
        "**Design impact in a broader context.** The evaluation is deliberately split into two questions that "
        "a deployment actually faces: *how accurate is the curve* (MSE) and *can the forecast support a "
        "decision* (PTE/PIE). Keeping them separate matters because they can rank models differently; a "
        "single leaderboard that collapses them would hide the choice. The benchmark is also built to be "
        "re-runnable: every cell records its GPU, partition, node and job id, so a public-health team can "
        "audit the numbers rather than trust them. That is a small contribution to reproducibility in a "
        "field where published forecasting results are rarely re-derived.",
        "**更广背景下的设计影响。** 评估被有意拆成部署真正面对的两个问题：*曲线有多准*（MSE）与*预测能否支持决策*"
        "（PTE/PIE）。把它们分开很重要，因为它们可能给出不同的排序；把二者合并成单一榜单会隐藏这个选择。"
        "基准也被设计为可重跑：每个单元记录 GPU、分区、节点与作业号，因此公共卫生团队可以审计这些数字，"
        "而不是只能相信它们。在一个已发表预测结果很少被重新推导的领域里，这是对可复现性的一点贡献。"))

    # 6. Progress
    b.append(H2("6. Progress", "6. 进度"))
    b.append(P("**Work completed this semester.**", "**本学期已完成的工作。**"))
    b.append(BUL(
        ("**Data verification:** 966-week CDC series confirmed bit-identical to the author's file "
         "(SHA-256, max|diff| = 0); split 676/97/193 and the containment guard verified.",
         "**数据验证：** 966 周 CDC 序列与作者文件逐字节相同（SHA-256，最大差 0）；切分 676/97/193 与包含约束"
         "已验证。"),
        ("**Code reconstruction:** 17 fidelity fixes (RevIN, LayerNorm, three dropouts, drop_last, "
         "single-variable batch, seed, epsilon, and others), each recorded in the deviation ledger.",
         "**代码重建：** 17 项保真修复（RevIN、LayerNorm、三个 dropout、drop_last、单变量 batch、seed、epsilon 等），"
         "每项都记录在偏离清单中。"),
        ("**Reproduction:** 40 runs (10 seeds x 4 horizons), every cell gated against the per-seed oracle "
         "at |Δ| <= 1e-5.",
         "**复现：** 40 次运行（10 个种子 x 4 个跨度），每个单元都以 |Δ| <= 1e-5 对照逐种子 oracle。"),
        ("**Benchmark:** 28 models x 4 horizons x 3 seeds = 336 cells; 204 of them (the 17 conventional "
         "arms) carry recorded per-cell A100 provenance, and the 132 encoder cells ran on the same "
         "partition with per-cell manifests on the cluster.",
         "**基准：** 28 个模型 x 4 个跨度 x 3 个种子 = 336 个单元；其中 204 个（17 个传统模型）带逐单元 A100 "
         "来源记录，132 个编码器单元在同一分区运行并留有逐单元清单。"),
        ("**Encoder axis:** 11 frozen encoders x 12 cells = 132 cells, MSE and PTE/PIE aggregated.",
         "**编码器维度：** 11 个冻结编码器 x 12 个单元 = 132 个单元，MSE 与 PTE/PIE 已聚合。"),
        ("**Analysis:** MSE/MAE, PTE/PIE, the Kramer & Shaman criterion, a Pareto frontier, a log-parameter "
         "regression, and 136 Holm-corrected paired tests.",
         "**分析：** MSE/MAE、PTE/PIE、Kramer & Shaman 判据、帕累托前沿、对数参数回归，以及 136 对 "
         "Holm 校正配对检验。"),
        ("**Ablation ladder:** designed, implemented behind flags, 27/60 cells complete at this report.",
         "**消融阶梯：** 已设计、以开关实现，本报告时完成 27/60 个单元。"),
        ("**Documentation:** six reports (DOCX + PDF, EN + ZH) generated from the CSVs with assertions.",
         "**文档：** 六份报告（DOCX + PDF，中英）由 CSV 生成并带断言。")))
    b.append(P(
        "**Reproduction result** (7-variable aggregate MSE, 10-seed mean):",
        "**复现结果**（7 变量聚合 MSE，10 种子均值）："))
    b.append(T("reproduction"))
    b.append(P(
        "The paper reports 1.542 / 1.422 / 1.414 / 1.364 (mean 1.4355). We obtain 1.3045 / 1.3561 / 1.6543 / "
        "1.6829 (mean 1.4995), i.e. 4.5 % worse on the mean, with a sign crossover 2-2: better at L=24 and "
        "L=36, worse at L=48 and L=60. The MAE side behaves the same way (0.8043 against 0.7452, +7.9 %).",
        "论文报告 1.542 / 1.422 / 1.414 / 1.364（均值 1.4355）。我们得到 1.3045 / 1.3561 / 1.6543 / 1.6829"
        "（均值 1.4995），即均值上差 4.5 %，符号交叉 2-2：L=24 与 L=36 更好，L=48 与 L=60 更差。"
        "MAE 一侧同样（0.8043 对 0.7452，+7.9 %）。"))
    b.append(LEAD(
        "**Conclusion (reproduction).** The reproduction is within 4.5 % on the four-horizon mean, with a "
        "horizon-dependent sign — a reproduction, not an improvement. Reporting only the mean would have "
        "hidden the structure, and the two disclosed deviations (validation checkpoint, 7-variable metric) "
        "mean the per-horizon wins cannot be claimed as superiority.",
        "**结论（复现）。** 复现在四跨度均值上落在 4.5 % 以内，符号随跨度翻转——这是复现，不是改进。"
        "只报告均值会藏起这一结构；而两处已披露的偏离（验证集检查点、7 变量指标）意味着逐跨度的胜出不能"
        "主张为“优于原论文”。"))

    b.append(P(
        "**Benchmark result** (28 arms, 3 seeds, shared windows):",
        "**基准结果**（28 个模型，3 个种子，共享窗口）："))
    b.append(T("benchmark"))
    b.append(P(
        "MIFlu is the accuracy champion at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716); the "
        "spread across all 28 arms is 1.5574 to 5.6155, a factor of 3.6. The published LLM-based "
        "competitors are beaten by a nearest-neighbour baseline (KNN 3.7854 vs Qwen-Time 5.2557 and "
        "CALF 5.5785), and the 11 frozen encoders occupy the 4.74-5.20 band.",
        "MIFlu 是精度冠军，1.5574，其后是 PatchTST（1.6621）与 NLinear（1.8716）；28 个模型的跨度为 1.5574 到 "
        "5.6155，即 3.6 倍。已发表的基于 LLM 的竞争者被最近邻基线击败（KNN 3.7854 对 Qwen-Time 5.2557、"
        "CALF 5.5785），11 个冻结编码器则位于 4.74-5.20 区间。"))
    b.append(LEAD(
        "**Finding F0 — accuracy alone does not identify a deployable model.** The ranking is easy to "
        "produce and hard to act on: it says which model fits this test set best, not which model supports "
        "the decision the forecast exists for. The next three analyses ask the questions the ranking cannot "
        "answer.",
        "**发现 F0——仅凭精度无法确定可部署的模型。** 排名很容易产出、却很难据以行动：它说明哪个模型最拟合"
        "这个测试集，而不说明哪个模型支持预测本来要服务的决策。接下来的三项分析正是要回答排名回答不了的问题。"))

    b.append(P(
        "**Peak-skill result** (PTE/PIE, Kramer & Shaman criterion; the grid shows the three named arms "
        "cell by cell):",
        "**峰值技巧结果**（PTE/PIE，Kramer & Shaman 判据；下表逐格展示三个具名模型）："))
    b.append(T("ks_grid"))
    b.append(P(
        f"NLinear and MIFlu each pass 4 of 16 cells, but differently: NLinear passes all four step-0 cells "
        f"with a PIE of {D.KS['nlinear']['step0_pie']:.1f} %, while MIFlu's four passes sit at PIE "
        f"18.3-24.8 %, against the 25 % boundary, and it misses L=48 at step 0. PatchTST passes none: its "
        f"timing is the best in the study (mean PTE {D.KS['patchtst']['mean_pte']:.2f} weeks) but its PIE is "
        f"{D.KS['patchtst']['mean_pie']:.1f} %.",
        f"NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部四个步 0 单元，PIE 为 "
        f"{D.KS['nlinear']['step0_pie']:.1f} %；MIFlu 的四个通过点 PIE 为 18.3-24.8 %，贴着 25 % 边界，"
        f"且在 L=48 步 0 失败。PatchTST 一个都不通过：它的时序是本研究最准的（均值 PTE "
        f"{D.KS['patchtst']['mean_pte']:.2f} 周），但 PIE 为 {D.KS['patchtst']['mean_pie']:.1f} %。"))
    b.append(LEAD(
        f"**Finding F1 — the deployment ordering is not the accuracy ordering.** Across all 28 arms, better "
        f"MSE does go with better calibration (Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f} against mean PIE), "
        f"so MSE is a useful screen; but the frontier is ordered the other way round. Among the three "
        f"lowest-MSE arms the calibration order is inverted at both ends (NLinear "
        f"{D.KS['nlinear']['mean_pie']:.1f} %, MIFlu {D.KS['miflu']['mean_pie']:.1f} %, PatchTST "
        f"{D.KS['patchtst']['mean_pie']:.1f} %), and the pass indicator is negatively rank-correlated with "
        f"MSE (ρ = {D.DECOUPLE['rho_pass']:.2f}, p = {D.DECOUPLE['p_pass']:.3f}). The runner-up by MSE "
        f"passes nothing; the third-best passes every horizon one week ahead.",
        f"**发现 F1——部署排序不是精度排序。** 在全部 28 个模型上，MSE 更好确实伴随校准更好（对均值 PIE 的 "
        f"Spearman ρ = +{D.DECOUPLE['rho_pie']:.2f}），所以 MSE 是有用的筛选；但前沿的排序正好相反。"
        f"MSE 最低的三个模型中，校准排序完全反转（NLinear {D.KS['nlinear']['mean_pie']:.1f} %、"
        f"MIFlu {D.KS['miflu']['mean_pie']:.1f} %、PatchTST {D.KS['patchtst']['mean_pie']:.1f} %），"
        f"且通过标记与 MSE 呈负秩相关（ρ = {D.DECOUPLE['rho_pass']:.2f}，p = {D.DECOUPLE['p_pass']:.3f}）。"
        f"MSE 第二名一个都不通过；第三名通过每个跨度的提前一周。"))
    b.append(FIG("fig_ks_ranking.png"))

    b.append(P(
        "**Efficiency and significance.** Across the 11 parametric arms, MSE against log10(parameters) has "
        f"slope +{D.PARETO['slope']:.4f} and R² = {D.PARETO['r2']:.4f}: size explains about 2 % of the "
        f"variance and its sign is unfavourable. The Pareto set is exactly {{NLinear, 2,520 parameters; "
        f"PatchTST, 531,878 parameters}}, i.e. {D.PARETO['ratio']:.0f}x the parameters for "
        f"{D.PARETO['mse_gain_pct']:.1f} % lower MSE. On the 12 matched cells of the 17 non-encoder arms, {D.N_RAW_SIG} of "
        f"{D.N_PAIRS} pairs are significant before correction; after proper Holm none survives (smallest "
        f"attainable adjusted p {D.HOLM_MIN:.3f}), and the NLinear-PatchTST pair has p(Holm) = "
        f"{float(D.PAIR.p_holm):.3f}.",
        f"**效率与显著性。** 在 11 个含参数模型上，MSE 对 log10(参数量) 的斜率为 +{D.PARETO['slope']:.4f}、"
        f"R² = {D.PARETO['r2']:.4f}：规模只解释约 2 % 的方差，且符号不利。帕累托集合恰好 {{NLinear 2,520 参数；"
        f"PatchTST 531,878 参数}}，即 {D.PARETO['ratio']:.0f} 倍参数换取 {D.PARETO['mse_gain_pct']:.1f} % 的 "
        f"MSE 下降。在 12 个配对单元上，{D.N_PAIRS} 对中有 {D.N_RAW_SIG} 对在校正前显著；正确 Holm 校正后无一存活"
        f"（最小可达校正 p 为 {D.HOLM_MIN:.3f}），NLinear-PatchTST 的 p(Holm) = {float(D.PAIR.p_holm):.3f}。"))
    b.append(T("paired"))
    b.append(LEAD(
        f"**Finding F2 (efficiency).** Parameter count is not a proxy for accuracy: the slope is positive "
        f"and R² is {D.PARETO['r2']:.4f}. The frontier is a two-model trade-off, not a ranking.",
        f"**发现 F2（效率）。** 参数量不是精度的代理：斜率为正、R² 只有 {D.PARETO['r2']:.4f}。前沿是两个模型"
        f"之间的权衡，不是排名。"))
    b.append(LEAD(
        f"**Finding F3 (significance).** The 211x cost buys an 11.2 % MSE difference that this benchmark "
        f"cannot resolve at n = 12. This is a failure to reject equality, not a proof of equivalence "
        f"(d = {float(D.PAIR.effect_d):.2f}; PatchTST is lower in {12 - int(D.PAIR.wins_a)} of 12 cells), so "
        f"the defensible conclusion is “no accuracy advantage is established for the 211x cost”, which "
        f"together with F1 makes NLinear the defensible default.",
        f"**发现 F3（显著性）。** 211 倍成本换来的 11.2 % MSE 差异，在本基准的 n = 12 下无法分辨。这是"
        f"“未能拒绝相等”，不是“证明相等”（d = {float(D.PAIR.effect_d):.2f}；PatchTST 在 12 个单元中的 "
        f"{12 - int(D.PAIR.wins_a)} 个更低），因此可辩护的结论是“未能为 211 倍成本确立精度优势”，结合 F1，"
        f"这使 NLinear 成为可辩护的默认选择。"))
    b.append(FIG("fig_pareto_frontier.png"))

    b.append(P(
        "**Frozen LLM encoders.** Eleven encoders (Qwen2.5-1.5B, five DeepSeek-R1-Distill sizes, "
        "Hunyuan-1.8B/4B/7B, ContextPilot-8B/14B), each frozen with one shared linear head, 132 of 156 "
        f"cells. The best is Hunyuan-1.8B at {D.ENC['best_mse']:.4f} and the worst Qwen2.5-1.5B at "
        f"{D.ENC['worst_mse']:.4f}, i.e. {D.ENC['ratio_best']:.2f}x to {D.ENC['ratio_worst']:.2f}x the MSE "
        f"of MIFlu; every one is worse than a decision tree, and none passes the Kramer & Shaman criterion "
        f"in any cell.",
        "**冻结 LLM 编码器。** 11 个编码器（Qwen2.5-1.5B、五个尺寸的 DeepSeek-R1-Distill、"
        "Hunyuan-1.8B/4B/7B、ContextPilot-8B/14B），每个冻结后接一个共享线性头，156 个单元中完成 132 个。"
        f"最好的是 Hunyuan-1.8B，{D.ENC['best_mse']:.4f}；最差的是 Qwen2.5-1.5B，{D.ENC['worst_mse']:.4f}，"
        f"即 MIFlu 的 {D.ENC['ratio_best']:.2f} 至 {D.ENC['ratio_worst']:.2f} 倍；每一个都差于决策树，"
        "且没有任何一个在任何单元通过 Kramer & Shaman 判据。"))
    b.append(LEAD(
        "**Finding F4 — frozen LLM representations do not transfer to this task.** The protocol was built "
        "to give the idea its best chance (frozen features, linear read-out, channel independence) and it "
        "still fails. This does not prove that an encoder can never help, but it does mean that a claim of "
        "gain from frozen language features on this task owes a mechanism and a control.",
        "**发现 F4——冻结 LLM 表征不能迁移到本任务。** 协议被设计成给该想法最好的机会（冻结特征、线性读出、"
        "通道独立），而它仍然失败。这不能证明编码器永远不可能有帮助，但它确实意味着：任何声称在本任务上从"
        "冻结语言特征获得增益的主张，都需要给出机制与对照。"))

    b.append(P(
        "**Ablation ladder (Table VIII in the project plan).** Five variants — no LoRA, and K = 2, 4, 8, 12 "
        "layers — at four horizons and three seeds (60 cells), compared against the full K=6 arm already in "
        "the benchmark table. The ladder answers where MIFlu's accuracy comes from: the LoRA adaptation or "
        "the depth of the stack. At this report 27 of 60 cells are complete, so no depth trend is claimed. "
        "One result is already established: the text tokens sit behind the causal mask and the head reads "
        "only the time patches, so `--no-text` is bit-identical to the full arm — a structural verification "
        "(asserted by `tests_archive/test_miflu_ablations.py`), not an ablation effect.",
        "**消融阶梯（项目计划中的表 VIII）。** 五个变体——去掉 LoRA，以及 K = 2、4、8、12 层——在 4 个跨度与 "
        "3 个种子上共 60 个单元，与已在基准表中的完整 K=6 臂比较。阶梯回答 MIFlu 的精度从何而来：LoRA 适配，"
        "还是堆叠深度。本报告时 60 个单元中完成 27 个，因此不声明任何深度趋势。有一项结果已经确立："
        "文本 token 位于因果掩码之后、输出头只读时间分片，因此 `--no-text` 与完整臂逐位相同——这是结构验证"
        "（由 `tests_archive/test_miflu_ablations.py` 断言），不是消融效应。"))
    b.append(LEAD(
        "**Finding F5 (provisional).** The text branch is masked out of the prediction path, so the "
        "multimodal claim is not supported by the architecture as shipped; the depth and LoRA questions "
        "remain open until the 60 cells are aggregated. This is reported as a design and a status, not as a "
        "result.",
        "**发现 F5（暂定）。** 文本分支位于预测路径之外，因此按已交付的架构，多模态主张得不到支持；"
        "深度与 LoRA 的问题要等 60 个单元聚合后才能回答。此处报告的是设计与状态，不是结果。"))

    b.append(P(
        "**Problems encountered.** (1) The original code selects its checkpoint on the test set and scores "
        "only 1 of 7 variables in the test loader; both were identified and fixed, and are disclosed as "
        "deviations. (2) The evaluation-window rule is a side effect of `drop_last=True`; adopting it for "
        "all arms was necessary to avoid handing MIFlu an easier test. (3) Eight engineering defects were "
        "found in the training pipeline (seed not reaching the LLM path, snapshot cloning the frozen "
        "encoder, two cache layouts, a non-atomic lock); seven are fixed and one remains open as an "
        "operational risk. (4) The ablation ladder has slipped from early November to late November because "
        "of queue contention on the shared A100 partition.",
        "**遇到的问题。** (1) 原代码在测试集上选检查点，且测试加载器只对 7 个变量中的 1 个计分；两者均已识别"
        "并修复，并作为偏离披露。(2) 评测窗口规则是 `drop_last=True` 的副作用；为所有模型统一采用它是必要的，"
        "否则就等于给 MIFlu 一个更容易的测试。(3) 训练流水线中发现八项工程缺陷（种子未进入 LLM 路径、快照克隆了"
        "冻结编码器、两种缓存布局、非原子锁）；七项已修复，一项作为运行风险仍未解决。(4) 消融阶梯因共享 A100 "
        "分区排队从 11 月初滑至 11 月下旬。"))

    # 7. Summary
    b.append(H2("7. Summary of objectives addressed and results achieved to date",
                "7. 目标完成与成果总结"))
    b.append(T("obj"))

    # 8. Schedule
    b.append(PB)
    b.append(H2("8. Work schedule and expected results for the next one to two months",
                "8. 未来 1-2 个月的工作计划与预期成果"))
    b.append(T("next"))
    b.append(P(
        "**Risks and mitigation.** (1) *Queue contention* on the shared A100 partition is the reason the "
        "ablation slipped; the ladder is submitted as one 60-cell job so it cannot be starved cell by cell. "
        "(2) *Criterion attribution*: the 1-week / 25 % thresholds are marked [to verify] and will be checked "
        "against the Kramer & Shaman text before submission; the peak detector is stated as our own choice, "
        "so a reader can separate the criterion from the implementation. (3) *Single dataset*: the regional "
        "and rolling-origin evaluations are the mitigation, and if they do not finish in time the paper will "
        "state the limitation rather than generalise. (4) *Scope*: if the ablation or Table VI is still "
        "incomplete at submission, the manuscript reports them as design and status, exactly as this report "
        "does — no trend, no fabricated number.",
        "**风险与应对。** (1) 共享 A100 分区的*排队竞争*是消融滑期的原因；阶梯以单个 60 单元作业提交，"
        "因此不会被逐单元饿死。(2) *判据归属*：1 周 / 25 % 阈值标注 [to verify]，投稿前会对照 Kramer & Shaman "
        "原文核对；峰值检测器明确声明为本研究的选择，使读者能把判据与实现分开。(3) *单一数据集*：区域评测与"
        "滚动原点评测就是应对措施；若来不及完成，论文将陈述这一局限，而不是外推。(4) *范围*：若投稿时消融或"
        "表 VI 仍未完成，手稿将像本报告一样只报告设计与状态——不写趋势，不编数字。"))
    b.append(P(
        "The manuscript draft is already written against these results (IEEE structure, EN and ZH; a "
        "single-column review draft until submission); "
        "the remaining work is to fold in the ablation ladder, the regional table and, if the budget allows, "
        "the rolling-origin evaluation. The submission target is IEEE JBHI, with a CCF-B venue as the "
        "alternative if the rolling-origin results arrive in time.",
        "手稿草稿已按这些结果写好（IEEE 结构，中英两版；投稿前为单栏评审稿）；剩余工作是把消融阶梯、区域表以及（若预算允许）"
        "滚动原点评测并入。投稿目标为 IEEE JBHI；若滚动原点结果及时到位，则以 CCF-B 会议为备选。"))
    b.append(P("Date: _____________    Signature of student: _____________",
               "日期：_____________    学生签名：_____________"))

    return b
