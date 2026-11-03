import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_progress.py'
c = open(p, 'r', encoding='utf-8').read()

print(f'Before: {len(c)} chars')

# Find blocks() and expand it with comprehensive content
start = c.find('def blocks(')
prefix = c[:start]

NEW = r'''def blocks(lang=None):
    """FYP Progress Report — comprehensive semester report following school template.
    Contains ALL progress done this semester."""
    b = []

    # ── PART A ──
    b.append(H1("PART A", "PART A"))
    b.append(P(
        "Name of Student: _________________________  Student ID: _________________\n"
        "Programme-Major: _________________________\n"
        "Project Code and Title: __________________  Reproducing MIFlu and Benchmarking\n"
        "    Influenza Forecasting with Frozen LLM Encoders\n"
        "Name of Supervisor: _______________________  Name of Assessor: ____________\n"
        "Number of meetings with supervisor / assessor: __________\n"
        "Average number of hours spent weekly: ______ hours/week",
        "学生姓名：_________________________  学号：_______________\n"
        "专业：_________________________\n"
        "项目编号与标题：__________________  复现 MIFlu 并以冻结 LLM 编码器基准评估流感预测\n"
        "导师姓名：_______________________  评阅人姓名：____________\n"
        "与导师/评阅人会面次数：________\n"
        "每周平均投入时间：______ 小时/周"))

    # ── PART B ──
    b.append(H1("PART B", "PART B"))

    # 1. Project objectives
    b.append(H2("1. Project objectives", "1. 项目目标"))
    b.append(P(
        "**Problem statement.** Influenza forecasting directly affects public-health resource allocation. "
        "Moon et al. (IEEE JBHI 2025) proposed MIFlu, a multimodal model combining GPT-2 time-series encoding "
        "with text embeddings, reporting the best accuracy on CDC national influenza data. However, the paper "
        "benchmarks only against two simple baselines, uses a single random seed, and selects the model checkpoint "
        "on the test set (data leakage). A public-health team therefore cannot answer: **is MIFlu actually the "
        "best model to deploy?**",
        "**问题陈述。** 流感预测直接影响公共卫生资源分配。Moon et al.（IEEE JBHI 2025）提出 MIFlu，一个多模态模型"
        "（GPT-2 时间序列编码 + 文本嵌入），在 CDC 全国流感数据上报告了最佳精度。但该论文仅与两个简单基线比较，"
        "仅用单一随机种子，且在测试集上选择模型检查点（数据泄漏）。因此公共卫生团队无法回答：**MIFlu 是不是"
        "最该部署的模型？**"))
    b.append(P("**Objectives:**", "**目标：**"))
    b.append(NUM(
        ("**Reproduce MIFlu's Table V** with a rigorous protocol (10 seeds, validation-based checkpoint selection, "
         "7-variable aggregate MSE) and quantify the gap against the paper's reported numbers.",
         "用严格协议**复现 MIFlu 的 Table V**（10 种子、验证集选检查点、7 变量聚合 MSE），量化与论文的差距。"),
        ("**Benchmark 28 forecasting models** (16 conventional + MIFlu + 3 LLM-based + 11 frozen LLM encoders) "
         "on the same data, using both accuracy (MSE/MAE) and peak-forecasting skill (PTE/PIE, Kramer & Shaman).",
         "在同一数据上**基准评估 28 个预测模型**（16 常规 + MIFlu + 3 基于 LLM + 11 冻结 LLM 编码器），"
         "同时用精度（MSE/MAE）和峰值预测技能（PTE/PIE，Kramer & Shaman 判据）。"),
        ("**Determine which model a public-health team should deploy**, and identify whether large language "
         "models improve epidemiological forecasting.",
         "**确定公共卫生团队应部署哪个模型**，并判断大语言模型是否改善流行病学预测。")))

    # 2. Planning chart
    b.append(H2("2. Original project planning chart", "2. 原始项目规划图"))
    b.append(P("Timeline (Sep 2026 – Dec 2026):", "时间线（2026 年 9 月 – 12 月）："))
    b.append(BUL(
        ("**Sep 2026 (Weeks 1-4):** Data acquisition & verification (966-week CDC dataset, byte-level check). "
         "Milestone: dataset confirmed identical.", 
         "**2026 年 9 月（第 1-4 周）：** 数据获取与验证（966 周 CDC 数据集，逐字节校验）。里程碑：数据集确认一致。"),
        ("**Oct 2026 (Weeks 5-8):** MIFlu code reconstruction (17 fidelity fixes), reproduction runs "
         "(10 seeds × 4 horizons). Milestone: Table V reproduced.",
         "**2026 年 10 月（第 5-8 周）：** MIFlu 代码重建（17 项保真修复），复现实验（10 种子 × 4 跨度）。"
         "里程碑：Table V 复现完成。"),
        ("**Nov 2026 (Weeks 9-12):** Benchmark runs (28 models × 3 seeds × 4 horizons), LLM encoder benchmark, "
         "Table VIII ablation (60/60), analysis, progress report. Milestone: benchmark complete.",
         "**2026 年 11 月（第 9-12 周）：** 基准实验（28 模型 × 3 种子 × 4 跨度）、LLM 编码器基准、"
         "Table VIII 消融（60/60）、分析、进度报告。里程碑：基准完成。"),
        ("**Dec 2026 (Weeks 13-16):** Innovation experiments, paper writing, submission.",
         "**2026 年 12 月（第 13-16 周）：** 创新实验、论文撰写、投稿。")))

    # 3. Background study
    b.append(H2("3. Background study", "3. 背景研究"))
    b.append(P(
        "**Technical background.** Influenza forecasting has evolved from statistical models (ARIMA, Prophet) "
        "to deep learning (LSTM, Transformer) and recently to large language models (LLMs). MIFlu represents "
        "the LLM approach: it fine-tunes GPT-2 with LoRA adapters on CDC national influenza data (966 weeks × "
        "7 variables) and reports the best accuracy. However, its comparison set is limited and its evaluation "
        "protocol has issues (test-set checkpoint selection, single seed).",
        "**技术背景。** 流感预测从统计模型（ARIMA、Prophet）发展到深度学习（LSTM、Transformer），再到最近的"
        "大语言模型（LLM）。MIFlu 代表 LLM 方法：用 LoRA 适配器在 CDC 全国流感数据（966 周 × 7 变量）上微调 "
        "GPT-2，报告了最佳精度。但其比较集有限，评测协议存在问题（测试集选检查点、单种子）。"))
    b.append(P(
        "**Contemporary and societal context.** Post-COVID, governments worldwide invested in AI-based epidemic "
        "forecasting. The WHO and CDC use forecasting to allocate vaccines and antivirals. However, a 2024 review "
        "in *Nature Medicine* noted that most AI forecasting papers compare only against weak baselines and lack "
        "reproducibility. Our study addresses both: a rigorous reproduction (with data-leakage fixes) and a "
        "28-model benchmark — directly answering whether LLMs actually help public-health forecasting.",
        "**当代与社会背景。** 新冠疫情后，各国政府投资 AI 流感预测。WHO 和 CDC 用预测分配疫苗和抗病毒药物。"
        "但 2024 年 *Nature Medicine* 综述指出，多数 AI 预测论文仅与弱基线比较且缺乏可复现性。本研究同时解决"
        "这两个问题：严格复现（修复数据泄漏）+ 28 模型基准——直接回答 LLM 是否真的帮助公共卫生预测。"))

    # 4. Methodology
    b.append(H2("4. Methodology", "4. 方法"))
    b.append(P(
        "We adopt a two-part design: (1) a faithful reproduction of MIFlu's Table V with rigorous fixes, and "
        "(2) a controlled benchmark of 28 models. The table below compares our settings against the original.",
        "我们采用两部分设计：(1) 严格修复后的 MIFlu Table V 忠实复现；(2) 28 模型受控基准。下表对比我们的设置与原论文。"))
    b.append(T("repro_params"))
    b.append(P(
        "**Key definitions.** Horizon L = future weeks predicted (input always T = 104 weeks; L=24 means predict "
        "24 weeks ahead). Step s = which predicted week (step 0 = 1 week ahead). PTE (Peak Timing Error) = "
        "|predicted peak week − observed peak week| [Kramer & Shaman 2019, PLoS Comput Biol 15(2):e1006742] "
        "**[to verify]**. PIE (Peak Intensity Error) = |predicted − observed peak| / observed × 100% [same] "
        "**[to verify]**. K&S criterion: PTE ≤ 1 wk AND PIE ≤ 25% [same] **[to verify]**. "
        "Eval windows: (W//16)*16 = 160/144/144/128 — NOT a journal requirement, side effect of drop_last=True.",
        "**关键定义。** 跨度 L = 预测未来周数（输入始终 T = 104 周；L=24 = 预测 24 周）。步长 s = 第几个预测周"
        "（step 0 = 提前 1 周）。PTE（峰值时间误差）= |预测峰值周 − 观测峰值周| [Kramer & Shaman 2019, "
        "PLoS Comput Biol 15(2):e1006742] **[to verify]**。PIE（峰值强度误差）= |预测 − 观测峰值| / 观测 × 100% "
        "[同上] **[to verify]**。K&S 判据：PTE ≤ 1 周 且 PIE ≤ 25% [同上] **[to verify]**。"
        "评测窗口：(W//16)*16 = 160/144/144/128——非期刊要求，drop_last=True 的副作用。"))
    b.append(P(
        "**Why two deliberate deviations?** (1) The original code selects the best epoch on the TEST set — "
        "this is data leakage. Top-tier journals prohibit this. We use the VALIDATION set. (2) The original "
        "code's test loader covers only 1 of 7 variables (a bug); Table V requires 7-variable aggregate MSE. "
        "We fix both.",
        "**为什么两处故意偏离？** (1) 原代码在测试集上选最优 epoch——这是数据泄漏。顶刊禁止此做法。我们改用验证集。"
        "(2) 原代码的 test loader 只覆盖 7 个变量中的 1 个（bug）；Table V 要求 7 变量聚合 MSE。两者均已修复。"))

    # 6. Progress — ALL work done this semester
    b.append(H2("6. Progress", "6. 进度"))
    b.append(P(
        "**All work completed this semester:**", "**本学期已完成的全部工作：**"))
    b.append(BUL(
        ("**Data acquisition & verification:** 966-week CDC dataset verified bit-identical to the author's "
         "file (SHA-256, max|diff| = 0). Split 676/97/193 confirmed.",
         "**数据获取与验证：** 966 周 CDC 数据集与作者文件逐字节相同（SHA-256，最大差 0）。切分 676/97/193 确认。"),
        ("**MIFlu code reconstruction:** 17 fidelity fixes identified and applied (RevIN formula, LayerNorm, "
         "3 dropouts, drop_last, single-variable batch, seed, epsilon, etc.).",
         "**MIFlu 代码重建：** 识别并修复 17 项保真差异（RevIN 公式、LayerNorm、3 个 dropout、drop_last、"
         "单变量 batch、seed、epsilon 等）。"),
        ("**Reproduction runs:** 40 cells (10 seeds × 4 horizons), all verified against per-seed oracle "
         "(|Δ| ≤ 1e-5).",
         "**复现实验：** 40 格（10 种子 × 4 跨度），全部通过逐种子 oracle 验证（|Δ| ≤ 1e-5）。"),
        ("**Benchmark runs:** 28 models × 3 seeds × 4 horizons = 336 cells, all on A100-SXM4-80GB.",
         "**基准实验：** 28 模型 × 3 种子 × 4 跨度 = 336 格，全部在 A100-SXM4-80GB 上。"),
        ("**LLM encoder benchmark:** 11 frozen encoders × 12 cells = 132 cells, MSE/PTE/PIE aggregated.",
         "**LLM 编码器基准：** 11 个冻结编码器 × 12 格 = 132 格，MSE/PTE/PIE 已聚合。"),
        ("**Table VIII ablation:** 60/60 complete (K2/K4/K8/K12 depth ladder + no_lora).",
         "**Table VIII 消融：** 60/60 完成（K2/K4/K8/K12 深度阶梯 + no_lora）。"),
        ("**Analysis pipeline:** MSE/MAE, PTE/PIE, K&S criterion, Pareto frontier, paired significance tests.",
         "**分析流水线：** MSE/MAE、PTE/PIE、K&S 判据、Pareto 前沿、配对显著性检验。"),
        ("**Document generation:** 6 reports (DOCX+PDF, EN+ZH) auto-generated from CSV data with assertions.",
         "**文档生成：** 6 份报告（DOCX+PDF，中英）从 CSV 数据自动生成，含断言验证。")))

    b.append(P(
        "**Table V reproduction results** (7-variable aggregate MSE, 10-seed mean):",
        "**Table V 复现结果**（7 变量聚合 MSE，10 种子均值）："))
    b.append(T("reproduction"))
    b.append(P(
        "The paper reports MSE 1.542/1.422/1.414/1.364 (mean 1.4355). We achieve 1.3045/1.3561/1.6543/1.6829 "
        "(mean 1.4995), reproducing within +4.5% with a sign crossover 2-2 (better at L24/L36, worse at L48/L60). "
        "MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), "
        "L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).",
        "论文报告 MSE 1.542/1.422/1.414/1.364（均值 1.4355）。我们得到 1.3045/1.3561/1.6543/1.6829（均值 1.4995），"
        "复现误差 +4.5%，符号交叉 2-2（L24/L36 更好，L48/L60 更差）。MAE：L24 0.7482 vs 0.726（+3.1%），"
        "L36 0.7712 vs 0.779（-1.0%），L48 0.8381 vs 0.757（+10.7%），L60 0.8596 vs 0.719（+19.6%）；均值 0.8043 vs 0.7452（+7.9%）。"))

    b.append(P("**Benchmark results** (28 models, 3 seeds):", "**基准结果**（28 模型，3 种子）："))
    b.append(T("benchmark"))
    b.append(T("ks_grid"))

    b.append(P(
        "**Core finding: the MSE champion is NOT the peak-forecast champion.** MIFlu has the best MSE (1.5574) "
        "but NLinear has the best peak forecasting (K&S 4/16 passes, PTE 1.677 wk, PIE 9.477%). This means "
        "model choice depends on what public health needs: overall accuracy (MIFlu) vs peak timing/calibration "
        "(NLinear). Pareto frontier: {NLinear 2,520 params; PatchTST 531,878 params} — 211× params for 11.2% "
        "lower MSE. All 11 frozen LLM encoders perform poorly (MSE 4.73-5.20), none passes K&S.",
        "**核心发现：MSE 冠军不是峰值预测冠军。** MIFlu MSE 最优（1.5574），但 NLinear 峰值预测最佳（K&S 4/16 通过，"
        "PTE 1.677 周，PIE 9.477%）。这意味着模型选择取决于公共卫生需求：整体精度（MIFlu）还是峰值时间/校准（NLinear）。"
        "Pareto 前沿：{NLinear 2,520 参数；PatchTST 531,878 参数}——211 倍参数换 11.2% 更低 MSE。"
        "全部 11 个冻结 LLM 编码器表现差（MSE 4.73-5.20），无一通过 K&S。"))

    b.append(P(
        "**Problems encountered:** (1) Original code had 5 documented bugs (test-set checkpoint selection, "
        "single-variable test loader, no-op freeze, etc.) — all identified and fixed. (2) K&S threshold is "
        "attributed to Kramer & Shaman (2019) but needs verification against the original PDF. (3) Initial "
        "evaluation used incorrect windows; corrected to (W//16)*16 rule. (4) Chinese encoding corruption "
        "twice during document generation; fixed with UTF-8 enforcement.",
        "**遇到的问题：** (1) 原代码有 5 个已记录 bug（测试集选检查点、单变量 test loader、空操作 freeze 等）"
        "——已全部识别并修复。(2) K&S 阈值归因于 Kramer & Shaman (2019) 但需对照原文核实。(3) 初期评测用了错误窗口；"
        "已修正为 (W//16)*16 规则。(4) 文档生成时两次中文编码损坏；已用 UTF-8 强制修复。"))

    # 7. Summary table
    b.append(H2("7. Summary of objectives addressed and results achieved to date",
                "7. 目标完成与成果总结"))
    b.append(T("obj"))

    # 8. Work schedule
    b.append(H2("8. Work schedule and expected results for the next one to two months",
                "8. 未来 1-2 个月的工作计划与预期成果"))
    b.append(BUL(
        ("**Innovation experiments (Nov-Dec 2026):** Evaluate three candidate contributions: "
         "(a) calibration-aware model selection (0 GPU-h), (b) hybrid predictor (20-60 GPU-h), "
         "(c) frozen-encoder selection guidance (0 GPU-h). Expected: one publishable innovation claim.",
         "**创新实验（2026 年 11-12 月）：** 评估三个候选贡献：(a) 校准感知模型选择（0 GPU 时），"
         "(b) 混合预测器（20-60 GPU 时），(c) 冻结编码器选型指南（0 GPU 时）。预期：一个可发表的创新主张。"),
        ("**Rolling-origin evaluation (if budget allows):** 5-fold cross-validation, 155-360 A100-hours.",
         "**滚动原点评测（如预算允许）：** 5 折交叉验证，155-360 A100 机时。"),
        ("**Paper writing (Dec 2026):** Complete IEEE JBHI manuscript with all results, figures, and tables. "
         "Target: submission by end of December 2026.",
         "**论文撰写（2026 年 12 月）：** 完成 IEEE JBHI 稿件，含全部结果、图表。目标：12 月底投稿。")))

    b.append(P("Date: _____________    Signature of student: _____________",
               "日期：_____________    学生签名：_____________"))
    return b
'''

c = prefix + NEW
open(p, 'w', encoding='utf-8', newline='').write(c)
print(f'After: {len(c)} chars')

try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
