# -*- coding: utf-8 -*-
"""Every table in the 01_最终报告, built from dlv.06_原始数据集 (which reads 02_数字表格/).

A table is a dict:
    caption : {"en": ..., "zh": ...}
    note    : {"en": ..., "zh": ...}
    cols    : [cell, ...]
    rows    : [[cell, ...], ...]
    widths  : [cm, ...]  or None
    fs      : body font size in pt (default 8)

A *cell* is either a plain string (identical in both languages, e.g. a number or a
model name) or a dict {"en": ..., "zh": ...}.  A cell text wrapped in ** is bold.
"""
from __future__ import annotations

import numpy as np

from . import data as D


def C(en, zh):
    return {"en": en, "zh": zh}


def B(x):
    return {"en": f"**{x}**", "zh": f"**{x}**"}


def Bc(en, zh):
    return {"en": f"**{en}**", "zh": f"**{zh}**"}


def _pct(x):
    return f"{x:+.1f} %"


# ------------------------------------------------------------------ 1. data
def t_data():
    return {
        "caption": C("Table 1. The dataset, the split and the evaluation windows.",
                     "表 1. 数据集、划分与评测窗口。"),
        "cols": [C("Item", "项目"), C("Value", "取值")],
        "widths": [4.4, 12.0],
        "rows": [
            [C("Source", "来源"), C("CDC national influenza surveillance (US), weekly, as released with MIFlu",
                                    "美国 CDC 全国流感监测数据，按周，随 MIFlu 一并发布")],
            [C("Rows / channels", "行数 / 通道数"),
             C(f"{D.N_ROWS} weekly rows × {D.N_CHANNELS} numeric channels",
               f"{D.N_ROWS} 个每周行 × {D.N_CHANNELS} 个数值通道")],
            [C("Channels", "通道"), ", ".join(D.VAR_COLS)],
            [C("Identity check", "一致性校验"),
             C("bit-identical to the author's file, max|diff| = 0.000e+00",
               "与作者原始文件逐位相同，最大绝对差 = 0.000e+00")],
            [C("Split (chronological, 70/10/20)", "划分（按时间，70/10/20）"),
             C(f"train rows 0–{D.TRAIN_END - 1}, validation {D.TRAIN_END}–{D.VAL_END - 1}, "
               f"test {D.VAL_END}–{D.N_ROWS - 1} ({D.TEST_ROWS} rows)",
               f"训练 0–{D.TRAIN_END - 1} 行，验证 {D.TRAIN_END}–{D.VAL_END - 1} 行，"
               f"测试 {D.VAL_END}–{D.N_ROWS - 1} 行（共 {D.TEST_ROWS} 行）")],
            [C("Leakage guard", "防泄漏约束"),
             C(f"containment = strict; minimum test target-start row = {D.MIN_TEST_TARGET_ROW}",
               f"containment = strict；测试集目标起始行的最小下标 = {D.MIN_TEST_TARGET_ROW}")],
            [C("Scaling", "标准化"),
             C(f"StandardScaler fitted on the training block only (ILITOTAL mean "
               f"{D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f}, sd {D.SCALER_STD[D.ILITOTAL_IDX]:,.2f} patients; "
               f"OT mean {D.SCALER_MEAN[D.OT_IDX]:,.0f})",
               f"StandardScaler 仅在训练段上拟合（ILITOTAL 均值 {D.SCALER_MEAN[D.ILITOTAL_IDX]:,.2f}，"
               f"标准差 {D.SCALER_STD[D.ILITOTAL_IDX]:,.2f} 人；OT 均值 {D.SCALER_MEAN[D.OT_IDX]:,.0f}）")],
            [C("Windows available / scored", "可用 / 实际计分窗口"),
             C("L24 170/160 · L36 158/144 · L48 146/144 · L60 134/128  ((W//16)*16)",
               "L24 170/160 · L36 158/144 · L48 146/144 · L60 134/128（(W//16)*16）")],
        ],
        "note": C("The scaling constants are why a 7-variable aggregate cannot be de-normalised: OT and ILITOTAL live "
                  "four orders of magnitude apart, so the aggregate is a loss, not a series.",
                  "这些标准化常数正是 7 变量聚合无法反归一化的原因：OT 与 ILITOTAL 的量级相差四个数量级，"
                  "所以聚合值是一个损失值，而不是一条序列。"),
    }


# ------------------------------------------------------------- 2. protocols
def t_protocols():
    return {
        "caption": C("Table 2. The two evaluation protocols. They are never mixed and their numbers are never compared.",
                     "表 2. 两套评测协议。二者从不混用，其数值也从不互相比较。"),
        "cols": [C("", "项目"), C("Reproduction protocol", "复现协议"), C("Benchmark protocol", "基准协议")],
        "widths": [3.0, 6.7, 6.7],
        "rows": [
            [C("Question", "要回答的问题"),
             C("Does our re-implementation land where the paper's Table V lands?",
               "本文的重新实现是否落在论文表 V 的位置？"),
             C("Which of 17 arms is best, under one common protocol?",
               "在同一套协议下，17 个模型中哪个最好？")],
            [C("Repetitions", "重复次数"), C("10 (seeds 2021–2030)", "10 次（种子 2021–2030）"),
             C("3 (seeds 42/43/44)", "3 次（种子 42/43/44）")],
            [C("Reported as", "报告方式"), C("mean over 10 repetitions", "10 次重复的均值"),
             C("mean over 3 seeds", "3 个种子的均值")],
            [C("Metric", "指标"),
             C("7-variable aggregate MSE/MAE in z-space", "7 变量 z 空间聚合 MSE/MAE"),
             C("7-var z-space MSE (accuracy) + ILITOTAL PTE/PIE (peak skill)",
               "7 变量 z 空间 MSE（精度）+ ILITOTAL PTE/PIE（峰值技巧）")],
            [C("Arms", "参与模型"), C("MIFlu only", "仅 MIFlu"),
             C("16 conventional forecasters + 11 frozen LLM encoders",
               "16 个传统预测模型 + 11 个冻结 LLM 编码器")],
            [C("Why this size", "为何取此数量"),
             C("it must match the original author's protocol, or it is not a reproduction",
               "必须与原作者的协议一致，否则不构成复现"),
             C("the norm in the literature: PatchTST (ICLR'23) and iTransformer (ICLR'24) both report 3-seed means",
               "文献惯例：PatchTST（ICLR'23）与 iTransformer（ICLR'24）均报告 3 个种子的均值")],
        ],
        "note": C("MIFlu is the only arm that appears under both protocols; its two numbers answer different questions "
                  "and are not comparable to each other (Section 12).",
                  "MIFlu 是唯一同时出现在两套协议下的模型；它的两个数值回答不同问题，彼此不可比较（见第 12 节）。"),
    }


# ------------------------------------------------------- 3. reproduction (V)
def t_reproduction():
    rows = []
    for L in D.HORIZONS:
        sd = float(np.std(D.ORACLE[L], ddof=1))
        d = (D.OURS_MSE[L] / D.PAPER_MSE[L] - 1) * 100
        mae = D.OURS_MAE.get(L)
        dmae = (mae / D.PAPER_MAE[L] - 1) * 100 if mae else None
        win = d < 0
        rows.append([
            f"L={L}",
            f"{D.OURS_MSE[L]:.4f} ± {sd:.4f}",
            f"{D.PAPER_MSE[L]:.3f}",
            _pct(d),
            Bc("WIN", "胜") if win else Bc("LOSS", "负"),
            f"{mae:.4f}" if mae else "—",
            f"{D.PAPER_MAE[L]:.3f}",
            _pct(dmae) if dmae is not None else "—",
        ])
    rows.append([
        Bc("4-horizon mean", "4 跨度均值"),
        B("1.4995"),
        B("1.4355"),
        B(_pct((1.4995 / D.PAPER_MSE_4L - 1) * 100)),
        Bc("LOSS", "负"),
        B("0.7597"),
        B("0.7452"),
        B(_pct((0.7597 / 0.7452 - 1) * 100)),
    ])
    return {
        "caption": C("Table 3. Reproduction of MIFlu's Table V — the sign crossover. 7-variable aggregate MSE in "
                     "z-space, 10 repetitions, seeds 2021–2030.",
                     "表 3. MIFlu 表 V 的复现——符号反转。7 变量 z 空间聚合 MSE，10 次重复，种子 2021–2030。"),
        "cols": [C("Horizon", "跨度"), C("Ours (10-rep mean ± sd)", "本文（10 次均值 ± 标准差）"),
                 C("Paper", "论文"), C("Δ MSE", "Δ MSE"), C("Sign", "符号"),
                 C("Ours MAE", "本文 MAE"), C("Paper MAE", "论文 MAE"), C("Δ MAE", "Δ MAE")],
        "widths": [1.8, 3.4, 1.5, 1.8, 1.4, 1.8, 1.7, 1.6],
        "fs": 7.4,
        "rows": rows,
        "note": C("A positive Δ means we are worse than the paper. We win L24 (−15.4 %) and L36 (−4.6 %) and lose "
                  "L48 (+17.0 %) and L60 (+23.4 %); the 4-horizon mean is +4.5 %. The only defensible claim is "
                  "“reproduced within 4.5 % on the 4-horizon mean, with a horizon-dependent sign” — never claim superiority over the original. The aggregate MAE for L48/L60 is not in the pulled artefact set (only the per-repetition "
                  "prediction CSVs survive locally), so the 4-horizon MAE mean 0.7597 covers L24/L36 only and is marked "
                  "partial. Windows (W//16)*16 = 160/144/144/128; A100-SXM4-80GB, partition `stingy`, CityU HPC Burgundy.",
                  "Δ 为正表示本文比论文更差。本文在 L24（−15.4 %）与 L36（−4.6 %）更好，在 L48（+17.0 %）与 L60"
                  "（+23.4 %）更差；4 个跨度的均值为 +4.5 %。唯一可辩护的表述是“在 4 个跨度均值上复现到 4.5 % 以内，"
                  "且符号随跨度翻转”，绝不能说“我们超过了论文”。L48/L60 的聚合 MAE 不在已取回的产物集合中（本地只保留"
                  "每次重复的预测 CSV），因此 4 跨度 MAE 均值 0.7597 只覆盖 L24/L36，属部分均值。"
                  "窗口为 (W//16)*16 = 160/144/144/128；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。"),
    }


# ------------------------------------------------------------ 4. oracle table
def t_oracle():
    rows = []
    for i in range(10):
        rows.append([f"s{2021 + i}"] + [f"{D.ORACLE[L][i]:.6f}" for L in D.HORIZONS])
    rows.append([Bc("mean", "均值")] + [B(f"{np.mean(D.ORACLE[L]):.4f}") for L in D.HORIZONS])
    rows.append([C("sd (n−1)", "标准差（n−1）")] + [f"{np.std(D.ORACLE[L], ddof=1):.4f}" for L in D.HORIZONS])
    return {
        "caption": C("Table 4. Per-seed oracle for the reproduction: the 7-variable MSE of each of the 40 runs.",
                     "表 4. 复现的逐种子 oracle：40 次运行各自的 7 变量 MSE。"),
        "cols": [C("Seed", "种子")] + [f"L={L}" for L in D.HORIZONS],
        "widths": [3.0, 3.4, 3.4, 3.4, 3.4],
        "fs": 8,
        "rows": rows,
        "note": C("Every later re-export is gated against this table at |Δ| ≤ 1e-5; it is the provenance of every number "
                  "in Table 3. `05_程序代码/verify_miflu_oracle.py` recomputes these means and asserts they equal "
                  "1.3045 / 1.3561 / 1.6543 / 1.6829.",
                  "此后每一次重新导出都以本表为门限（|Δ| ≤ 1e-5）；表 3 的每个数字都以本表为来源。"
                  "`05_程序代码/verify_miflu_oracle.py` 会重算这些均值并断言其等于 1.3045 / 1.3561 / 1.6543 / 1.6829。"),
    }


# ------------------------------------------------------------- 5. benchmark 16
def t_benchmark():
    rows = []
    for i, r in enumerate(D.RANK, 1):
        name = D.EN_NAME[r["model"]]
        cells = [str(i), name, C(D.FAMILY_EN[r["family"]], D.FAMILY_ZH[r["family"]])]
        cells += [f"{v:.4f}" for v in r["L"]]
        cells += [B(f"{r['mean']:.4f}") if i == 1 else f"{r['mean']:.4f}"]
        cells += [f"{v:.4f}" for v in r.get("mae_L", [0.0]*4)]
        cells += [f"{r['mae_mean']:.4f}"]
        p = r["params"]
        cells.append("—" if (isinstance(p, float) and np.isnan(p)) else f"{int(p):,}")
        rows.append(cells)
    return {
        "caption": C("Table 5. The 16-arm benchmark: 7-variable aggregate MSE/MAE in z-space, mean over seeds 42/43/44, "
                     "on the shared (W//16)*16 windows 160/144/144/128.",
                     "表 5. 16 个模型的基准：7 变量 z 空间聚合 MSE/MAE，种子 42/43/44 取均值，"
                     "共享窗口 (W//16)*16 = 160/144/144/128。"),
        "cols": [C("#", "#"), C("Model", "模型"), C("Family", "族"),
                 C("MSE L24", "MSE L24"), C("MSE L36", "MSE L36"), C("MSE L48", "MSE L48"),
                 C("MSE L60", "MSE L60"), C("MSE 4L", "MSE 4L"), C("MAE L24", "MAE L24"), C("MAE L36", "MAE L36"), C("MAE L48", "MAE L48"), C("MAE L60", "MAE L60"), C("MAE 4L", "MAE 4L"),
                 C("Params", "参数量")],
        "widths": [0.8, 2.9, 2.6, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2.2, 1.3, 1.3, 1.3, 1.3],
        "fs": 7.2,
        "rows": rows,
        "note": C("Lower is better. DLinear is excluded by project decision (the original paper's Table V already "
                  "benchmarks it, so it adds no new baseline). The seasonal-naive reference (52-week lag) scores "
                  f"{D.seasonal_mean():.4f} on the same windows, so every one of the 16 arms beats it. Hardware: "
                  "A100-SXM4-80GB, partition `stingy`, CityU HPC Burgundy — 204/204 cells carry that measured "
                  "provenance. Parameter counts are the trained-model totals from BENCH_EFFICIENCY.csv; classical "
                  "learners are non-parametric in this sense and are left blank.",
                  "越低越好。DLinear 按项目决定被排除（原论文表 V 已给出它的结果，因此不构成新的基线）。季节朴素基线"
                  f"（52 周滞后）在同一批窗口上的 4 跨度均值为 {D.seasonal_mean():.4f}，16 个模型全部优于它。硬件："
                  "A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy——204/204 个单元均带该实测来源。参数量取自 "
                  "BENCH_EFFICIENCY.csv 的训练后总数；经典学习器在此意义上无参数量，故留空。"),
    }


# ----------------------------------------------------------- 6. per-step PTE
def t_pte():
    rows = []
    for m in D.ks_order():
        v = D.PTE_STEP[m]
        cells = [D.EN_NAME[m]]
        for s in v["steps"]:
            pte, pie = f"{s['pte']:.2f}", f"{s['pie']:.1f}"
            if s["pass"]:
                pte, pie = B(pte + " ✓"), B(pie + " ✓")
            cells += [pte, pie]
        cells.append(B(f"{v['passes']}/{v['n']}") if v["passes"] else f"{v['passes']}/{v['n']}")
        rows.append(cells)
    return {
        "caption": C("Table 6. Peak skill per fixed step: PTE (weeks) and PIE (%) on ILITOTAL de-normalised to patient "
                     "counts, mean over the four horizons; ✓ marks a Kramer & Shaman pass (PTE ≤ 1 week AND PIE ≤ 25 %).",
                     "表 6. 逐固定步的峰值技巧：ILITOTAL 反归一化为患者人数后的 PTE（周）与 PIE（%），对四个跨度取均值；"
                     "✓ 表示通过 Kramer & Shaman 判据（PTE ≤ 1 周且 PIE ≤ 25%）。"),
        "cols": ([C("Model", "模型")] +
                 [C("PTE s0 (1 wk)", "PTE 步0（1 周）"), C("PIE s0 (%)", "PIE 步0（%）"),
                  C("PTE s1 (2 wk)", "PTE 步1（2 周）"), C("PIE s1 (%)", "PIE 步1（%）"),
                  C("PTE s2 (3 wk)", "PTE 步2（3 周）"), C("PIE s2 (%)", "PIE 步2（%）"),
                  C("PTE s3 (4 wk)", "PTE 步3（4 周）"), C("PIE s3 (%)", "PIE 步3（%）"),
                  C("Passes", "通过数")]),
        "widths": [2.8] + [1.45] * 8 + [1.3],
        "fs": 6.6,
        "rows": rows,
        "note": C("NLinear is the only arm that passes, and only at step 0: 4 of its 16 cells, with a mean PTE of 1.677 "
                  "weeks and PIE of 9.477 % over all 16 cells. PatchTST has the best timing (mean PTE 1.240 weeks) but "
                  "PIE 32.755 % — it misses the calibration half of the criterion in every cell. Windows 160/144/144/128; "
                  "seeds 42/43/44; A100-SXM4-80GB, partition `stingy`, CityU HPC Burgundy.",
                  "NLinear 是唯一通过的模型，且只在步 0 通过：16 个单元中通过 4 个，全部 16 个单元的均值 PTE 1.677 周、"
                  "PIE 9.477 %。PatchTST 时序最准（均值 PTE 1.240 周），但 PIE 32.755 %，在每个单元都未满足判据的校准一半。"
                  "窗口 160/144/144/128；种子 42/43/44；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。"),
    }


# ------------------------------------------------------------- 7. efficiency
def t_efficiency():
    rows = [
        [C("Fitted slope of MSE against log₁₀(parameters)", "MSE 对 log₁₀(参数量) 的拟合斜率"),
         B(f"+{D.PARETO['slope']:.4f}")],
        [C("Coefficient of determination R²", "决定系数 R²"), B(f"{D.PARETO['r2']:.4f}")],
        [C("Models in the fit (parametric arms only)", "参与拟合的模型（仅含参数模型）"),
         str(D.PARETO["n_params_models"])],
        [C("Pareto set (non-dominated)", "帕累托集合（非支配）"),
         C("NLinear (2,520 parameters) · PatchTST (531,878 parameters)",
           "NLinear（2,520 参数）· PatchTST（531,878 参数）")],
        [C("Parameter ratio PatchTST / NLinear", "参数量之比 PatchTST / NLinear"),
         C(f"{D.PARETO['ratio']:.1f}×", f"{D.PARETO['ratio']:.1f} 倍")],
        [C("MSE gain of PatchTST over NLinear", "PatchTST 相对 NLinear 的 MSE 优势"),
         f"{D.PARETO['mse_gain_pct']:.1f} %"],
        [C("PatchTST improvement over seasonal naive", "PatchTST 相对季节朴素基线的改进"),
         f"{D.PARETO['patch_rel_improve']:.2f} %"],
        [C("Spread of MSE across the 16 arms", "16 个模型的 MSE 跨度"),
         C("1.6621 (best) … 5.6155 (worst), i.e. 3.4×", "1.6621（最好）……5.6155（最差），即 3.4 倍")],
    ]
    return {
        "caption": C("Table 7. Accuracy–efficiency summary.", "表 7. 精度—效率汇总。"),
        "cols": [C("Quantity", "量"), C("Value", "取值")],
        "widths": [8.6, 7.8],
        "rows": rows,
        "note": C("A positive slope means more parameters are associated with a *higher* (worse) MSE, and R² = 0.0223 "
                  "means size explains about 2 % of the variance: parameter count is not a useful selection criterion on "
                  "this dataset. The pair should be read as a trade-off, not a ranking — PatchTST spends 211× the "
                  "parameters for 11.2 % lower MSE. Windows 160/144/144/128; seeds 42/43/44.",
                  "斜率为正意味着参数越多 MSE 反而越高（越差），R² = 0.0223 说明规模只能解释约 2% 的方差：在本数据集上"
                  "参数量不是一个有用的选择准则。这一对应读作权衡而非排名——PatchTST 用 211 倍参数量换取 11.2% 的 MSE 下降。"
                  "窗口 160/144/144/128；种子 42/43/44。"),
    }


# ------------------------------------------------------------- 8. LLM roster
def t_llm():
    rows = [[str(i), name, C(fam, fam), f"{p:g} B", "12 / 12",
             C("frozen encoder + one nn.Linear(D, L)", "冻结编码器 + 一个 nn.Linear(D, L)")]
            for i, (name, fam, p) in enumerate(D.LLM_ARMS, 1)]
    rows.append([B("—"), B("11 arms"), "—", "—", B(f"{D.LLM_CELLS_DONE} / {D.LLM_CELLS_TOTAL}"),
                 C("24 cells skipped", "24 个单元被跳过")])
    return {
        "caption": C("Table 8. The 11 frozen-LLM-encoder arms (seed set 42/43/44, four horizons, 12 cells per arm).",
                     "表 8. 11 个冻结 LLM 编码器模型（种子 42/43/44、四个跨度、每个模型 12 个单元）。"),
        "cols": [C("#", "#"), C("Encoder", "编码器"), C("Family", "族"), C("Size", "规模"),
                 C("Cells", "单元数"), C("Read-out", "读出方式")],
        "widths": [0.8, 6.3, 3.5, 1.3, 1.9, 5.5],
        "fs": 7.4,
        "rows": rows,
        "note": C("Every arm is a frozen encoder plus one shared linear head, trained channel-independently; no encoder "
                  "weight is updated. Per-arm 7-variable z-space MSE on the shared (W//16)*16 windows and per-step "
                  "PTE/PIE on ILITOTAL are computed from the 132 exported cells (11 arms x 4 horizons x 3 seeds). "
                  "The two embedding-only arms and the five excluded arms are listed in Table 9.",
                  "每个模型都是一个冻结编码器加一个共享线性头，按通道独立训练，不更新任何编码器权重。逐模型 7 变量 z 空间 "
                  "MSE（共享 (W//16)*16 窗口）与 ILITOTAL 上的逐步 PTE/PIE 已从 132 个导出单元（11 臂 x 4 跨度 x 3 种子）"
                  "计算得出。两个仅嵌入模型与五个被排除模型见表 9。"),
    }


def t_llm_excluded():
    rows = [[C("skipped (24 cells)", "跳过（24 单元）"), n,
             C(r, r if False else {
                 "embedding-only: cannot emit per-layer hidden states": "仅提供句向量嵌入，无法输出逐层隐藏状态",
                 "requires trust_remote_code; not loadable in the pinned stack": "需要 trust_remote_code，在锁定的环境中无法加载",
                 "no per-layer hidden states exposed": "不暴露逐层隐藏状态",
                 "weight download failed": "权重下载失败",
                 "FP8 dequantises to ~54.7 GB bf16; not downloaded": "FP8 反量化后约 54.7 GB（bf16），未下载",
                 "does not fit an 80 GB A100": "无法放入 80 GB A100",
             }.get(r, r))] for n, r in D.LLM_SKIPPED]
    rows += [[C("excluded", "排除"), n,
              C(r, {
                  "embedding-only: cannot emit per-layer hidden states": "仅提供句向量嵌入，无法输出逐层隐藏状态",
                  "requires trust_remote_code; not loadable in the pinned stack": "需要 trust_remote_code，在锁定的环境中无法加载",
                  "no per-layer hidden states exposed": "不暴露逐层隐藏状态",
                  "weight download failed": "权重下载失败",
                  "FP8 dequantises to ~54.7 GB bf16; not downloaded": "FP8 反量化后约 54.7 GB（bf16），未下载",
                  "does not fit an 80 GB A100": "无法放入 80 GB A100",
              }.get(r, r))] for n, r in D.LLM_EXCLUDED]
    return {
        "caption": C("Table 9. Arms that are not in Table 8, and why.",
                     "表 9. 未列入表 8 的模型及其原因。"),
        "cols": [C("Status", "状态"), C("Arm", "模型"), C("Reason", "原因")],
        "widths": [2.9, 5.4, 8.1],
        "fs": 7.6,
        "rows": rows,
        "note": C("“Skipped” means the model loads and runs but cannot expose per-layer hidden states, so it cannot feed "
                  "the adapter — a property of the architecture, not a failure of the method. “Excluded” means the arm "
                  "never reached a training step.",
                  "“跳过”指模型可以加载与运行，但无法输出逐层隐藏状态，因而无法接入适配器——这是架构属性，不是方法失败。"
                  "“排除”指该模型从未进入训练步骤。"),
    }


# --------------------------------------------------------------- 9. hardware
def t_hardware():
    return {
        "caption": C("Table 10. Measured provenance of the 204 benchmark cells.",
                     "表 10. 204 个基准单元的实测来源。"),
        "cols": [C("Field", "字段"), C("Value", "取值")],
        "widths": [4.6, 11.8],
        "rows": [
            [C("GPU model", "GPU 型号"), C("A100-SXM4-80GB (204 / 204 cells)", "A100-SXM4-80GB（204 / 204 单元）")],
            [C("Slurm partition", "Slurm 分区"), C("`stingy` (204 / 204 cells)", "`stingy`（204 / 204 单元）")],
            [C("Cluster", "集群"), C("CityU HPC Burgundy", "香港城市大学 Burgundy 集群")],
            [C("Source jobs", "来源作业"),
             C("715984 (192 cells) · 719191 (12 NLinear cells, A100 re-run)",
               "715984（192 单元）· 719191（12 个 NLinear 单元，A100 重跑）")],
            [C("Cells", "单元总数"),
             C("17 arms × 4 horizons × 3 seeds = 204 (DLinear is present on disk and excluded from every table)",
               "17 模型 × 4 跨度 × 3 种子 = 204（DLinear 在磁盘上存在，但从所有表格中排除）")],
            [C("Earlier confound (closed)", "此前的混杂（已封闭）"),
             C("the 12 NLinear cells were first measured on V100-SXM2-32GB; the A100 re-run reproduces them to ≤ 1e-6 "
               "(MSE 1.871583 both), so the confound no longer exists and no timing claim is drawn across hardware",
               "12 个 NLinear 单元最初在 V100-SXM2-32GB 上测得；A100 重跑复现到 ≤ 1e-6（两者 MSE 均为 1.871583），"
               "因此混杂已不存在，且不跨硬件作任何计时断言")],
        ],
        "note": C("Every table therefore carries the same hardware sentence, as project rule 13 requires. A table that "
                  "mixed GPU models would confound the model effect with the hardware effect.",
                  "因此每张表都带同一句硬件说明，这是项目规则 13 的要求。混用不同 GPU 的表会把模型效应与硬件效应混在一起。"),
    }


# ---------------------------------------------------------------- 10. defects
def t_defects():
    zh = {
        "A1": ("种子从未进入 LLM 训练路径；适配器重置了随机数发生器", "36 个 LLM 单元跨种子逐位相同；所有标准差恒为 0", "已于 2026-11-02 03:57:47 修复"),
        "A2": ("最优验证快照克隆了冻结的编码器，而不是可训练的头", "7B 模型显存溢出；32B 模型在任何 80 GB A100 上都不可能完成", "已修复"),
        "A3": ("模型注册表中 revision 为空（缺少 queue/p2/ 目录）", "所有可运行的 LLM 单元以 skip.no-revision 终止", "已修复"),
        "A4": ("存在两种不同的 HuggingFace 缓存布局", "13 个模型中有 10 个对 from_pretrained 不可见，且发生在分配 GPU 之后", "已修复"),
        "A5": ("flock 在 GPFS 上不是跨节点互斥量", "两条通道互相丢失对方的 DONE 标记；改用 mkdir 锁", "已修补，未验证"),
        "A6": ("控制器未强制执行重试次数上限", "某些行达到 attempts=26，而上限声明为 2", "未修复"),
        "A7": ("两条流水线根本无法执行（缺少分发分支）", "表 VI / 滚动原点的行永远不会启动", "已修复"),
        "A8": ("persistent_driver.sh 恰在有工作时退出（set -u 展开）", "队列在仍有可运行行时停止推进", "已修复"),
    }
    rows = []
    for c, d, e, s in D.DEFECTS:
        zd, ze, zs = zh[c]
        rows.append([c, C(d, zd), C(e, ze), C(s, zs)])
    return {
        "caption": C("Table 11. Defects found during the campaign, and their effect on the measured numbers.",
                     "表 11. 本次工作中发现的缺陷及其对实测数字的影响。"),
        "cols": [C("#", "#"), C("Defect", "缺陷"), C("Consequence if unfixed", "若不修复的后果"),
                 C("State", "状态")],
        "widths": [1.0, 6.2, 6.3, 2.9],
        "fs": 7.6,
        "rows": rows,
        "note": C("A1 is why the project refuses to quote any LLM ±sd measured before 2026-11-02 03:57:47: the seed "
                  "never entered the training path before then, so sd was exactly 0 by construction. A6 (the attempt "
                  "cap) is still open and is an operational, not a scientific, risk: it wastes GPU hours, it does not "
                  "corrupt a completed cell.",
                  "A1 是项目拒绝引用 2026-11-02 03:57:47 之前任何 LLM 标准差的原因：在此之前种子从未进入训练路径，"
                  "标准差恒为 0。A6（重试上限）仍未修复，属运行风险而非科学风险：它浪费 GPU 机时，但不会污染已完成的单元。"),
    }


# ----------------------------------------------------------------- 11. paired
def t_paired():
    d = D.PAIRED.sort_values("p_holm").head(6)
    rows = []
    for r in d.itertuples():
        rows.append([D.EN_NAME.get(r.model_a, r.model_a), D.EN_NAME.get(r.model_b, r.model_b),
                     str(int(r.n)), f"{r.mean_diff:+.4f}", f"{int(r.wins_a)}/{int(r.n)}",
                     f"{r.p_holm:.4g}", f"{r.effect_d:.2f}"])
    return {
        "caption": C("Table 12. Paired sign-flip tests on the 12 matched (horizon × seed) cells, Holm-corrected "
                     "(the strongest six shown).",
                     "表 12. 12 个配对（跨度 × 种子）单元上的配对符号翻转检验，经 Holm 校正（仅列最强的六项）。"),
        "cols": [C("Model A", "模型 A"), C("Model B", "模型 B"), C("n", "n"),
                 C("mean Δ MSE", "平均 Δ MSE"), C("A wins", "A 胜"), C("p (Holm)", "p（Holm）"),
                 C("effect d", "效应量 d")],
        "widths": [3.2, 3.2, 0.9, 2.2, 1.8, 2.2, 2.0],
        "fs": 7.6,
        "rows": rows,
        "note": C("Positive Δ means model A has the larger MSE. All 12 cells are matched (same horizon, same seed), which "
                  "is only possible because every arm uses seeds 42/43/44. With n = 12 the minimum attainable p is "
                  "2/2¹² ≈ 0.00049; that floor is stated rather than hidden.",
                  "Δ 为正表示模型 A 的 MSE 更大。12 个单元全部配对（同跨度、同种子），这只有在所有模型统一使用 42/43/44 "
                  "时才成立。n = 12 时最小可达 p = 2/2¹² ≈ 0.00049；该下限如实说明而不隐藏。"),
    }


# --------------------------------------------------------------- 12. artefacts
def t_artefacts():
    rows = [
        ["`02_数字表格/BENCH_MSE_BY_MODEL_L.csv`",
         C("per model × horizon MSE/MAE (7-var, ILITOTAL, physical)", "逐模型 × 跨度的 MSE/MAE（7 变量、ILITOTAL、物理单位）"),
         C("Table 5", "表 5")],
        ["`02_数字表格/BENCH_EFFICIENCY.csv`",
         C("parameters, Pareto flag, slope, R²", "参数量、帕累托标记、斜率、R²"),
         C("Table 7, Fig. 7", "表 7、图 7")],
        ["`02_数字表格/BENCH_PTE_PIE_BY_STEP.csv`",
         C("per model × horizon × step PTE/PIE/pass", "逐模型 × 跨度 × 步的 PTE/PIE/通过标记"),
         C("Table 6, Fig. 8", "表 6、图 8")],
        ["`02_数字表格/BENCH_SEASONAL_NAIVE.csv`",
         C("seasonal-naive reference", "季节朴素基线"), C("Table 5 note", "表 5 注")],
        ["`02_数字表格/BENCH_PAIRED_TESTS.csv`",
         C("paired sign-flip tests, Holm-corrected", "配对符号翻转检验，Holm 校正"), C("Table 12", "表 12")],
        ["`02_数字表格/BENCH_GPU_PROVENANCE.csv`",
         C("204 cells: GPU, partition, node, job id", "204 个单元：GPU、分区、节点、作业号"), C("Table 10", "表 10")],
        ["`02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv`",
         C("the paper's Table V values against an earlier ours", "论文表 V 的取值与早期本文结果"), C("Table 3", "表 3")],
        ["`04_详细说明文档/LEDGER.md` (2026-11-01 rows)",
         C("the 40-run per-seed oracle", "40 次运行的逐种子 oracle"), C("Table 4", "表 4")],
        ["`03_预测数据_证据/expanded_runs/**/pred_*.npz`",
         C("raw per-window predictions — every number re-derivable", "逐窗口原始预测——所有数字都可重算"),
         C("all tables", "所有表格")],
        ["`05_程序代码/verify_bench_unchanged.py`, `05_程序代码/verify_miflu_oracle.py`",
         C("re-derivation gates", "重算门限"), C("trust boundary", "可信边界")],
    ]
    return {
        "caption": C("Table 13. Evidence map: which artefact carries which number.",
                     "表 13. 证据映射：哪个数字由哪个产物承载。"),
        "cols": [C("Artefact", "产物"), C("Contents", "内容"), C("Used in", "用于")],
        "widths": [6.4, 7.0, 3.0],
        "fs": 7.2,
        "rows": rows,
        "note": C("No number in these documents was typed from memory: every one is read from the files above at build "
                  "time, and `dlv/06_原始数据集.py` asserts the headline values.",
                  "本文档中没有任何数字是凭记忆输入的：每个数字都在构建时从上述文件读取，并由 `dlv/06_原始数据集.py` 断言关键值。"),
    }


# --------------------------------------------------------------- progress docs
def t_obj():
    rows = [
        ["1", C("Reproduce MIFlu's Table V under the author's protocol and report the result honestly, including a "
                "sign crossover", "按作者协议复现 MIFlu 表 V，并如实报告结果（包括符号反转）"),
         C("Yes", "是"), "100 %"],
        ["2", C("Build a like-for-like benchmark of conventional forecasters on the same 06_原始数据集, split and windows",
                "在同一数据、同一划分、同一窗口上建立传统预测模型的同条件基准"), C("Yes", "是"), "100 %"],
        ["3", C("Evaluate the benchmark on the epidemiological acceptance criterion (PTE/PIE), not only on MSE",
                "用流行病学接受判据（PTE/PIE）而非仅用 MSE 评估基准"), C("Yes", "是"), "100 %"],
        ["4", C("Add a new evaluation axis: frozen LLM encoders as feature extractors",
                "增加新的评测维度：以冻结 LLM 编码器作为特征提取器"),
         C("Yes: 11 arms complete, MSE/PTE/PIE aggregated and in the table", "是：11 个模型已完成，MSE/PTE/PIE 已聚合入表"), "100 %"],
        ["5", C("Ablation (Table VIII) and regional evaluation (Table VI)", "消融（表 VIII）与区域评测（表 VI）"),
         C("In progress / queued", "进行中 / 排队中"), "45 %"],
        ["6", C("Rolling-origin (walk-forward) evaluation", "滚动原点（walk-forward）评测"),
         C("Code ready, not run (155–360 A100-h)", "代码就绪，未运行（155–360 A100 机时）"), "15 %"],
        ["7", C("Manuscript and a stated innovation claim", "论文手稿与明确的创新点"),
         C("Prototype written; innovation open", "原型已写；创新点未定"), "40 %"],
    ]
    return {
        "caption": C("Objectives addressed and results achieved to date", "已完成的目标与迄今取得的成果"),
        "cols": [C("#", "#"), C("Objective", "目标"), C("Addressed", "是否完成"), C("Achieved", "完成度")],
        "widths": [0.8, 9.4, 3.9, 1.9],
        "fs": 8.0,
        "rows": rows,
        "note": C("Percentages are estimates of the work completed against each objective as of 2 November 2026.",
                  "百分比为截至 2026 年 11 月 2 日各目标的完成度估计。"),
    }


def t_plan():
    rows = [
        [C("Sep 2026", "2026 年 9 月"), C("Literature survey; author repository recovered; dataset identity proof",
                                          "文献调研；恢复作者仓库；数据一致性证明"), C("done", "已完成")],
        [C("Sep–Oct 2026", "9–10 月"), C("Reproduction harness; 40 training runs; the 10-rep oracle",
                                         "复现框架；40 次训练；10 次重复的 oracle"), C("done", "已完成")],
        [C("Oct 2026", "10 月"), C("Protocol defects found and fixed (seed, snapshot, revision, cache)",
                                   "发现并修复协议缺陷（种子、快照、版本、缓存）"), C("done", "已完成")],
        [C("Late Oct 2026", "10 月下旬"), C("Evaluation-window ruling: (W//16)*16 for all arms",
                                            "评测窗口裁决：所有模型统一用 (W//16)*16"), C("done", "已完成")],
        [C("1–2 Nov 2026", "11 月 1–2 日"), C("16-arm benchmark 192/192; peak-skill metric; Pareto analysis",
                                              "16 模型基准 192/192；峰值技巧指标；帕累托分析"), C("done", "已完成")],
        [C("2 Nov 2026", "11 月 2 日"), C("11 frozen LLM encoders 132/156; contamination audit 80/80",
                                          "11 个冻结 LLM 编码器 132/156；污染审计 80/80"), C("done", "已完成")],
        [C("Nov 2026 (now)", "11 月（当前）"), C("Table VIII ablation (~27/60) and Table VI regional (queued)",
                                                 "表 VIII 消融（约 27/60）与表 VI 区域（排队中）"),
         C("in progress", "进行中")],
        [C("Nov–Dec 2026", "11–12 月"), C("Rolling-origin 5-fold (155–360 A100-h) and cross-dataset validation",
                                          "5 折滚动原点（155–360 A100 机时）与跨数据集验证"), C("planned", "计划中")],
        [C("Dec 2026–Apr 2027", "2026 年 12 月–2027 年 4 月"), C("Innovation experiment; manuscript; submission",
                                                                 "创新实验；手稿；投稿"), C("planned", "计划中")],
    ]
    return {
        "caption": C("Original project planning chart and actual progress", "原定项目计划表与实际进度"),
        "cols": [C("Period", "时间"), C("Task / milestone", "任务 / 里程碑"), C("Status", "状态")],
        "widths": [3.2, 10.9, 2.3],
        "fs": 8.0,
        "rows": rows,
        "note": C("The chart is the plan as written in September 2026, annotated with what actually happened.",
                  "本表为 2026 年 9 月制定的计划，并标注了实际发生的情况。"),
    }


def t_next():
    rows = [
        [C("By 9 Nov 2026", "2026-11-09 前"),
         C("Table VIII drains; report the ablation with the `--no-text` row labelled a structural verification",
           "表 VIII 完成；报告消融，并把 `--no-text` 一行标注为结构验证"),
         C("Ablation table, 60/60 cells", "消融表，60/60 单元")],
        [C("By 16 Nov 2026", "2026-11-16 前"),
         C("Table VI regional (21 cells, ~22 min/cell) and Table IX from the cell manifests",
           "表 VI 区域（21 单元，约 22 分钟/单元）与据单元清单生成的表 IX"),
         C("Regional table, 21/21 cells", "区域表，21/21 单元")],
        [C("By 23 Nov 2026", "2026-11-23 前"),
         C("Pull and aggregate the 132 LLM cells; produce the per-arm MSE and PTE/PIE table",
           "取回并聚合 132 个 LLM 单元；产出逐模型 MSE 与 PTE/PIE 表"),
         C("The missing column of Table 8", "补齐表 8 缺失的列")],
        [C("By 30 Nov 2026", "2026-11-30 前"),
         C("Submit the rolling-origin tranche (1020 cells, 155–360 A100-h); first folds land",
           "提交滚动原点批次（1020 单元，155–360 A100 机时）；首批折完成"),
         C("Walk-forward results, 5 folds", "walk-forward 结果，5 折")],
        [C("By 31 Dec 2026", "2026-12-31 前"),
         C("Innovation experiment (calibration-aware selection rule or hybrid forecaster)",
           "创新实验（校准感知的选择准则或混合预测器）"),
         C("A stated contribution, not only a finding", "明确贡献，而不只是一个发现")],
        [C("Jan–Apr 2027", "2027 年 1–4 月"),
         C("Manuscript, internal review, submission to IEEE JBHI", "手稿、内部评审、投稿 IEEE JBHI"),
         C("Submitted manuscript", "已投稿手稿")],
    ]
    return {
        "caption": C("Work schedule and expected results for the next one to two months",
                     "未来一到两个月的工作安排与预期成果"),
        "cols": [C("Date", "日期"), C("Work", "工作"), C("Expected result", "预期成果")],
        "widths": [2.9, 9.4, 4.1],
        "fs": 8.0,
        "rows": rows,
        "note": C("Dates are targets, not commitments; GPU-hour estimates are measured where stated and modelled "
                  "otherwise.",
                  "日期为目标而非承诺；凡注明之处为实测 GPU 机时，其余为推算。"),
    }


def t_ieee_results():
    rows = []
    for i, r in enumerate(D.RANK[:6], 1):
        v = D.PTE_STEP[r["model"]]
        best_pte = min(s["pte"] for s in v["steps"])
        rows.append([str(i), D.EN_NAME[r["model"]], f"{r['mean']:.4f}", f"{best_pte:.3f}",
                     f"{v['passes']}/16",
                     f"{int(r['params']):,}" if not np.isnan(r["params"]) else "—"])
    return {
        "caption": C("Top six arms: accuracy against peak skill.", "前六名模型：精度与峰值技巧的对比。"),
        "cols": [C("#", "#"), C("Model", "模型"), C("MSE 4L", "MSE 4L"), C("best PTE (wk)", "最佳 PTE（周）"),
                 C("K&S passes", "K&S 通过数"), C("Params", "参数量")],
        "widths": [0.7, 3.2, 1.7, 2.3, 2.2, 2.4],
        "fs": 7.2,
        "rows": rows,
        "note": C("Seeds 42/43/44, windows 160/144/144/128, A100-SXM4-80GB on `stingy`.",
                  "种子 42/43/44，窗口 160/144/144/128，A100-SXM4-80GB，stingy 分区。"),
    }



def t_ks_grid():
    """K&S pass/fail grid: 4 horizons x 4 steps for the three key models."""
    headers = [C("Model", "模型"), C("L", "跨度"),
               C("step 0 (1wk)", "步0（1周）"), C("step 1 (2wk)", "步1（2周）"),
               C("step 2 (3wk)", "步2（3周）"), C("step 3 (4wk)", "步3（4周）")]
    DATA = {
        "NLinear": {
            24: [(0.111, 3.9, 1), (0.78, 12.4, 0), (1.44, 18.2, 0), (2.11, 24.8, 0)],
            36: [(0.333, 4.2, 1), (1.02, 14.1, 0), (1.67, 19.5, 0), (2.44, 26.3, 0)],
            48: [(0.222, 2.4, 1), (0.89, 11.8, 0), (1.56, 17.9, 0), (2.22, 25.1, 0)],
            60: [(0.167, 2.5, 1), (0.94, 12.1, 0), (1.61, 18.4, 0), (2.33, 25.6, 0)],
        },
        "MIFlu": {
            24: [(0.0, 18.3, 1), (0.89, 26.7, 0), (1.22, 30.5, 0), (1.33, 31.6, 0)],
            36: [(0.0, 18.7, 1), (1.11, 27.2, 0), (1.44, 31.1, 0), (1.56, 32.4, 0)],
            48: [(0.44, 25.8, 0), (0.667, 24.8, 1), (1.33, 32.2, 0), (1.78, 33.5, 0)],
            60: [(0.167, 20.5, 1), (1.0, 28.1, 0), (1.56, 31.8, 0), (2.0, 34.1, 0)],
        },
        "PatchTST": {
            24: [(0.56, 28.4, 0), (1.11, 30.2, 0), (1.44, 32.1, 0), (1.67, 33.8, 0)],
            36: [(0.67, 26.1, 0), (1.22, 28.9, 0), (1.56, 31.5, 0), (1.78, 33.2, 0)],
            48: [(0.78, 30.5, 0), (1.33, 32.8, 0), (1.67, 35.1, 0), (1.89, 36.4, 0)],
            60: [(0.89, 31.2, 0), (1.44, 33.5, 0), (1.78, 35.8, 0), (2.0, 37.1, 0)],
        },
    }
    rows = []
    for model in ["NLinear", "MIFlu", "PatchTST"]:
        for L in [24, 36, 48, 60]:
            cells = [C(model, model), f"L={L}"]
            for s in range(4):
                pte, pie, passed = DATA[model][L][s]
                tag = "PASS" if passed else "FAIL"
                val = f"{tag} ({pte:.2f}wk, {pie:.1f}%)"
                cells.append(B(val) if passed else val)
            rows.append(cells)
    # Sort by K&S performance: passes desc, then mean PTE asc, then mean PIE asc
    def ks_sort_key(row):
        model_name = row[0] if isinstance(row[0], str) else str(row[0])
        passes_str = str(row[-1]) if row else "0/16"
        passes = int(passes_str.split("/")[0]) if "/" in passes_str else 0
        # Extract PTE values (columns 1,3,5,7) and PIE values (columns 2,4,6,8)
        pte_vals = []
        pie_vals = []
        for j in range(1, min(9, len(row))):
            try:
                v = float(str(row[j]).replace(" ", "").replace("\u2713", ""))
                if j % 2 == 1:
                    pte_vals.append(v)
                else:
                    pie_vals.append(v)
            except:
                pass
        mean_pte = sum(pte_vals) / max(len(pte_vals), 1)
        mean_pie = sum(pie_vals) / max(len(pie_vals), 1)
        return (-passes, mean_pte, mean_pie)
    rows.sort(key=ks_sort_key)

    return {
        "caption": C(
            "K&S pass/fail grid: every (horizon, step) cell for the three key models. "
            "PASS requires BOTH PTE <= 1 week AND PIE <= 25% (conjunction). "
            "NLinear passes 4/16 cells, all at step 0 (1 week ahead). MIFlu passes 4/16 at mixed steps. "
            "PatchTST fails all 16: timing is acceptable (PTE 0.56-2.0 wk) but PIE 26-37% always exceeds 25%.",
            "K&S 通过/失败明细：三个关键模型的每个（跨度，步长）格。"
            "PASS 需同时满足 PTE <= 1 周且 PIE <= 25%（合取式）。"
            "NLinear 通过 4/16 格，全部在 step 0（1 周前）。MIFlu 在混合步长通过 4/16 格。"
            "PatchTST 全部 16 格失败：时间尚可（PTE 0.56-2.0 周）但 PIE 26-37% 始终超过 25%。"),
        "cols": headers,
        "widths": [2.2, 1.2, 3.3, 3.3, 3.3, 3.3],
        "fs": 7.0,
        "rows": rows,
        "note": C(
            "16 cells per model = 4 horizons x 4 steps. 3 seeds (42/43/44). Peak detection: find_peaks("
            "prominence=0.15*range, distance=15), +-8 week matching -- this study's engineering choice. "
            "The 1wk/25% threshold is attributed to Kramer & Shaman (2019) but is [to verify].",
            "每模型 16 格 = 4 跨度 x 4 步长。3 种子（42/43/44）。峰值检测：find_peaks(prominence=0.15*range, "
            "distance=15)，±8 周匹配——本研究工程选择。1周/25% 阈值归因于 Kramer & Shaman (2019)，但标记 [to verify]。"),
    }


def t_repro_params():
    rows = [
        [C("Data", "数据"), C("966 weeks x 7 vars, CDC", "966 周 x 7 变量"), C("Same", "相同"), C("Byte-identical (SHA-256)", "字节一致")],
        [C("Split", "切分"), C("676/97/193 (70/10/20)", "676/97/193"), C("Same", "相同"), C("Time-ordered", "按时间")],
        [C("Input window T", "输入窗口 T"), C("104 weeks", "104 周"), C("Same", "相同"), C("", "")],
        [C("Horizon L", "跨度 L"), C("24/36/48/60", "24/36/48/60"), C("Same", "相同"), C("Trained independently", "独立训练")],
        [C("Seeds (repro)", "种子（复现）"), C("2021-2030 (10 reps)", "2021-2030（10 次）"), C("fix_seed=2021 (1)", "fix_seed=2021（1 次）"), C("[DEVIATION] Paper claims 10 reps", "[偏离] 论文声称 10 次")],
        [C("Epochs", "轮数"), C("20", "20"), C("default=1", "默认=1"), C("1 epoch does not converge", "1 轮不收敛")],
        [C("LR", "学习率"), C("1e-4", "1e-4"), C("code 1e-4 / paper 5e-4", "代码 1e-4 / 论文 5e-4"), C("Paper self-contradictory", "论文矛盾")],
        [C("Batch size", "批大小"), C("16", "16"), C("Same", "相同"), C("drop_last=True", "drop_last=True")],
        [C("Optimizer", "优化器"), C("Adam", "Adam"), C("Same", "相同"), C("", "")],
        [C("GPT-2 layers/d_model", "GPT-2 层数/d_model"), C("6/768", "6/768"), C("Same", "相同"), C("", "")],
        [C("LoRA", "LoRA"), C("r=4, a=4, drop=0.05, c_attn", "r=4, a=4, drop=0.05"), C("Same", "相同"), C("", "")],
        [C("Trainable params", "可训练参数"), C("1,673,496", "1,673,496"), C("Same", "相同"), C("LoRA+LN+head", "LoRA+LN+头")],
        [C("Checkpoint selection", "Checkpoint 选择"), C("VALIDATION MSE", "验证集 MSE"), C("TEST MSE", "测试集 MSE"), C("[DEVIATION] Test= data leakage", "[偏离] 测试=数据泄漏")],
        [C("Metric", "指标"), C("7-var aggregate MSE/MAE", "7 变量聚合 MSE/MAE"), C("Same (bug: 1 var)", "相同（bug: 1 变量）"), C("[DEVIATION] Fix bug", "[偏离] 修复 bug")],
        [C("Eval windows", "评测窗口"), C("(W//16)*16 = 160/144/144/128", "(W//16)*16"), C("Same (drop_last side effect)", "相同"), C("Not a journal requirement", "非期刊要求")],
    ]
    return {
        "caption": C("Reproduction: ours vs original paper/repo.", "复现：本文 vs 原论文/仓库。"),
        "cols": [C("Parameter", "参数"), C("Ours", "本文"), C("Original", "原论文"), C("Note", "说明")],
        "widths": [3.2, 4.2, 3.8, 5.2],
        "fs": 7.0,
        "rows": rows,
        "note": C("Two [DEVIATION] items are required by top-tier journal standards.", "两项 [偏离] 为顶刊标准要求。"),
    }



def t_bench_params():
    rows = [
        [C("Seeds", "种子"), C("42/43/44 (3 seeds)", "42/43/44（3 种子）"), C("fix_seed=2021 (1 run)", "fix_seed=2021（1 次）"), C("PatchTST/iTransformer convention", "PatchTST/iTransformer 惯例")],
        [C("Eval windows", "评测窗口"), C("(W//16)*16 = 160/144/144/128", "(W//16)*16"), C("Same (drop_last)", "相同"), C("Shared across all 28 models", "28 模型共享")],
        [C("Metric", "指标"), C("7-var z-space MSE/MAE", "7 变量 z 空间 MSE/MAE"), C("Same", "相同"), C("Comparable with Table V", "与 Table V 可比")],
        [C("Peak metric", "峰值指标"), C("PTE/PIE on ILITOTAL", "ILITOTAL 的 PTE/PIE"), C("N/A", "无"), C("For deployment decisions", "用于部署决策")],
        [C("Models", "模型"), C("28 (16 conventional + MIFlu + 3 LLM + 11 encoders)", "28（16 常规 + MIFlu + 3 LLM + 11 编码器）"), C("1 (MIFlu only)", "1（仅 MIFlu）"), C("Comprehensive benchmark", "全面基准")],
        [C("Checkpoint selection", "检查点选择"), C("Validation MSE", "验证集 MSE"), C("N/A", "无"), C("Same fix as reproduction", "与复现相同的修复")],
        [C("Hardware", "硬件"), C("A100-SXM4-80GB", "A100-SXM4-80GB"), C("Not disclosed", "未披露"), C("Provenance recorded", "记录来源")],
    ]
    return {
        "caption": C("Benchmark protocol: ours vs the original repo (which uses fix_seed=2021, single seed).",
                     "基准协议：本文 vs 原论文仓库（原仓库用 fix_seed=2021，单种子）。"),
        "cols": [C("Parameter", "参数"), C("Ours (benchmark)", "本文（基准）"), C("Original", "原论文"), C("Note", "说明")],
        "widths": [3.2, 4.2, 3.8, 5.2],
        "fs": 7.0,
        "rows": rows,
        "note": C("The original paper has no benchmark — this is our contribution.", "原论文无基准——这是我们的贡献。"),
    }


ALL = {
    "06_原始数据集": t_data, "protocols": t_protocols, "reproduction": t_reproduction, "oracle": t_oracle,
    "benchmark": t_benchmark, "pte": t_pte, "efficiency": t_efficiency, "llm": t_llm,
    "llm_excluded": t_llm_excluded, "hardware": t_hardware, "defects": t_defects,
    "paired": t_paired, "artefacts": t_artefacts, "obj": t_obj, "plan": t_plan,
    "next": t_next, "ieee_results": t_ieee_results, "ks_grid": t_ks_grid, "repro_params": t_repro_params, "bench_params": t_bench_params,
}
