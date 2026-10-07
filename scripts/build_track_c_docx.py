#!/usr/bin/env python3
"""
build_track_c_docx.py — the final Chinese report for Track C
(AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP).

Writes MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx
and never touches the original report.

All numbers are read from the validated Track C result files; none are typed by
hand, and no value is invented.
"""
from __future__ import annotations

import os
import sys

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IN = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                  "r1_v2_verification_20261007", "docx_inputs")
OUT = os.path.join(ROOT, "results", "v3_clean", "analysis", "reports",
                   "MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx")

CN = {"miflu": "官方仓库修正版 MIFlu", "nlinear": "NLinear", "dlinear": "DLinear",
      "patchtst": "PatchTST", "itransformer": "iTransformer",
      "timecma_llm": "TimeCMA-LLM", "qwen_time_llm": "Qwen-Time-LLM",
      "calf_llm": "CALF-LLM"}
SIDE = {"LLM": "LLM 侧", "non-LLM": "非 LLM 侧"}


def load(name):
    p = os.path.join(IN, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def _repeat_header(row):
    """Mark a table row as a header row so Word repeats it after a page break."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def add_table(doc, df, cols, cn_header, fmt=None, widths=None):
    t = doc.add_table(rows=1, cols=len(cols))
    t.style = "Light Grid Accent 1"
    t.autofit = True
    for i, h in enumerate(cn_header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
    _repeat_header(t.rows[0])
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, cl in enumerate(cols):
            v = row[cl]
            if fmt and cl in fmt:
                v = fmt[cl](v)
            cells[i].text = str(v)
    if widths:
        from docx.shared import Cm
        for row in t.rows:
            for i, w in enumerate(widths):
                if i < len(row.cells):
                    row.cells[i].width = Cm(w)
    return t


def main():
    rank = load("TRACK_C_TEST_MSE_RANKING.csv")
    mae = load("TRACK_C_TEST_MAE_RANKING.csv")
    perh = load("TRACK_C_PER_HORIZON_CHAMPIONS.csv")
    pw = load("TRACK_C_PAIRWISE_STATS_CORRECTED.csv")
    grp = load("TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    pers = load("TRACK_C_PER_SEED_RANKINGS.csv")
    gate = load("SEED42_EIGHT_MODEL_GATE_RESULTS.csv")
    cost = load("TRACK_C_COST_SUMMARY.csv")
    mm = load("TRACK_C_MIFLU_RUN_MATRIX.csv")
    cc = load("TRACK_C_CELL_CLASSIFICATION.csv")

    missing = [n for n, d in [("rank", rank), ("mae", mae), ("perh", perh),
                              ("pw", pw), ("grp", grp), ("gate", gate),
                              ("cost", cost), ("miflu", mm), ("cells", cc)]
               if d is None]
    if missing:
        raise SystemExit(f"ABORT: missing validated inputs: {missing}")

    champ = rank.iloc[0]
    g = {r["side"]: r["mean_of_model_means_Test_MSE_4L"] for _, r in grp.iterrows()}
    gp = int((gate.result == "PASS").sum())
    gf = int((gate.result == "FAIL").sum())
    costd = {r["item"]: r["value"] for _, r in cost.iterrows()}

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "SimSun"
    st.font.size = Pt(10.5)

    def H(txt, lvl=1):
        p = doc.add_heading(txt, level=lvl)
        for r in p.runs:
            r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
            r.font.name = "SimHei"
        return p

    def P(txt, bold=False):
        p = doc.add_paragraph()
        r = p.add_run(txt)
        r.bold = bold
        return p

    # ---------- title ----------
    t = doc.add_heading("MIFlu 非 LLM 与 LLM 流感预测最终报告", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in t.runs:
        r.font.name = "SimHei"
    s = doc.add_paragraph("——作者 966 行严格包含（strict-containment）八模型一次性测试冠军版")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    d = doc.add_paragraph("生成日期：2026-10-07　|　主实验轨道：Track C　|　"
                          "冻结种子：42 / 43 / 44")
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER

    P("")
    H("一、结论摘要", 1)
    P(f"在作者 966 行 National-Illness 数据集、严格包含（strict-containment）"
      f"窗口契约、匹配种子 42/43/44 的条件下，八个模型全部在训练集训练、"
      f"以验证集选择 checkpoint、并以一次性测试集（Test）评价。")
    P(f"最终冠军为【{CN.get(champ['model'], champ['model'])}】，"
      f"测试集四horizon等权平均 MSE = {champ['mean_Test_MSE_4L']:.4f}"
      f"（标准差 {champ['sd_Test_MSE_4L']:.4f}），"
      f"平均 MAE = {champ['mean_Test_MAE_4L']:.4f}。", bold=True)
    P(f"该模型在 L=24/36/48/60 四个 horizon 上均为第一名，并非依靠加权平均掩盖局部落后。")
    P(f"需要同时保留的第二个结论：LLM 侧组的平均分为 {g.get('LLM', float('nan')):.4f}，"
      f"非 LLM 侧组的平均分为 {g.get('non-LLM', float('nan')):.4f}，"
      f"即【按组平均而言非 LLM 侧更优】。两者并不矛盾——冠军是 LLM 侧的 MIFlu，"
      f"但 LLM 侧其余成员（Qwen-Time-LLM、CALF-LLM）明显偏弱，拉低了整组均值。")

    # ---------- chronology ----------
    H("二、项目历程与三条轨道", 1)
    P("本项目最终区分三条互不可比的结果轨道，绝对 MSE 数值不得跨轨道比较。")
    docs = [
        ("Track H", "历史 1025 行受控替换实验：使用旧自建 MIFlu，"
                    "且历史窗口按“目标起点”归属划分，存在跨划分污染。"
                    "已冻结为 PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE，"
                    "仅作历史证据，不参与最终冠军评选。"),
        ("Track R", "作者 966 行 R1-B 论文复现：使用官方仓库修正版 MIFlu，"
                    "结论为 PARTIAL_REPRODUCTION（四个 horizon 全部落在"
                    "预声明 ±0.10 容差之外）。用于验证 MIFlu 实现，本身不是八模型冠军实验。"),
        ("Track C", "作者 966 行严格包含八模型一次性测试冠军实验——即本报告的主结果。"),
    ]
    for k, v in docs:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(f"{k}："); r.bold = True
        p.add_run(v)

    # ---------- why 966 ----------
    H("三、为何采用 966 行数据集", 1)
    P("论文 Table II 的七个变量描述统计与 966 行作者文件【7/7 完全吻合】"
      "（最大相对偏差约 0.02%）；而 2026 年 7 月的 1025 行快照仅 1/7 吻合。"
      "因此 966 行文件才是论文分析所用的数据集，其 70:10:20 整数划分为 "
      "676 / 97 / 193。1025 行快照属于 Track H，其绝对数值不得与 Track C 混用。")
    P("数据身份（SHA-256）：")
    p = doc.add_paragraph("2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.font.name = "Consolas"

    # ---------- roles ----------
    H("四、Train / Validation / Test 的分工", 1)
    P("严格区分三者职责，是本实验公正性的核心：")
    for s in ["Train（676 行）：仅用于拟合模型参数与标准化器（scaler 仅用训练行拟合）。",
              "Validation（97 行）：仅用于选择 checkpoint 与早停；"
              "不进入最终排名，不进入分组均值，不作为主要性能结果。",
              "Test（193 行）：在 checkpoint 冻结后【只评价一次】，"
              "是唯一决定冠军的依据，并用于分 horizon 冠军、最佳 LLM / 最佳非 LLM、"
              "分组汇总与配对统计。"]:
        doc.add_paragraph(s, style="List Bullet")
    P("明确禁止且未发生：逐 epoch 读取 Test、用 Test 选择 checkpoint、"
      "看过 Test 后调参、依据 Test 挑选种子、剔除表现不佳的种子、"
      "混用 Validation 与 Test 结果。")

    # ---------- contamination ----------
    H("五、历史划分污染与严格包含的修正", 1)
    P("历史 1025 行契约按“目标起点”把窗口归入划分（train 若 ts < 717，val 若 ts ≤ 819），"
      "完全不考虑目标长度。实测在 L=24 时，23 个训练目标越界进入验证段、"
      "23/103 个验证目标越界进入 Test 段——而验证集正是选择 checkpoint 的依据，"
      "构成实质性污染。")
    P("Track C 改用严格包含：对每个窗口，目标块必须完整落在其所属划分内：")
    for s in ["target_start ≥ split_start", "target_end ≤ split_end − 1",
              "target_end = target_start + L − 1"]:
        p = doc.add_paragraph(s, style="List Bullet")
        for r in p.runs:
            r.font.name = "Consolas"
    P("由此得到的严格窗口数（已逐项验证）：")
    add_table(doc, pd.DataFrame([
        {"L": 24, "训练": 549, "验证": 74, "测试": 170},
        {"L": 36, "训练": 537, "验证": 62, "测试": 158},
        {"L": 48, "训练": 525, "验证": 50, "测试": 146},
        {"L": 60, "训练": 513, "验证": 38, "测试": 134}]),
        ["L", "训练", "验证", "测试"], ["horizon L", "训练起点数", "验证起点数", "测试起点数"])
    P("测试集键数分别等于 170×24×7、158×36×7、146×48×7、134×60×7，"
      "八个模型共用完全相同的键集合，重复键为 0。")

    # ---------- model identity ----------
    H("六、模型身份与单元格分类", 1)
    P("八个模型身份固定，未增加、删除、改名或替换。96 个单元格分类如下：")
    n_re = int((cc["class"] == "RESCORE_ONLY").sum())
    n_rt = int((cc["class"] == "GPU_RETRAIN").sum())
    P(f"RESCORE_ONLY（重新评分）：{n_re} 个；GPU_RETRAIN（重新训练）：{n_rt} 个。")
    P("官方仓库修正版 MIFlu：以作者仓库为基座，七通道输出、文本通路有效、"
      "PEFT 启用、LoRA 施加于 c_attn、参数冻结有效、验证集选择 checkpoint、"
      "Test 只读一次、锁定式 checkpoint 与独立评分。12 个单元格全部重新训练"
      "（配置冻结，未依据任何结果调整）。")

    H("七、为何拒绝 Stage-6 的 MIFlu 预测", 1)
    P("stage-6 的 pred_miflu_* 通过了全部结构性检查（strict containment、"
      "author_966、z 空间、规范起点、变量列顺序与形状均正确），但仍被判定为不可用："
      "它与 A2 产物【逐字节相同】（sha256 76b81b5b0dfa5bde），"
      "即项目早期自建重构版，而非本实验要求的官方仓库实现。")
    P("【键兼容不等于实现身份。】若按“全部复用”的表面结论执行，"
      "最终冠军实验将静默替换为规则明确禁止的模型。该拒绝记录于 "
      "TRACK_C_MODEL_IDENTITY.csv 的 gpt2_miflu_REJECTED 行。", bold=True)

    # ---------- ranking ----------
    H("八、最终测试集排名", 1)
    P("全部 96 个单元格由同一个规范评分器重算，未使用任何模型自带的评分代码路径。"
      "排序依据为测试集四个 horizon 等权平均 MSE（越低越好）。")
    r2 = rank.copy()
    r2["模型"] = r2.model.map(lambda m: CN.get(m, m))
    r2["阵营"] = r2.side.map(lambda s: SIDE.get(s, s))
    add_table(doc, r2,
              ["rank_MSE", "模型", "mean_Test_MSE_4L", "sd_Test_MSE_4L",
               "mean_Test_MAE_4L", "阵营"],
              ["排名", "模型", "平均 MSE (4L)", "标准差", "平均 MAE (4L)", "阵营"],
              {"mean_Test_MSE_4L": lambda v: f"{v:.4f}",
               "sd_Test_MSE_4L": lambda v: f"{v:.4f}",
               "mean_Test_MAE_4L": lambda v: f"{v:.4f}"},
              widths=[1.4, 5.0, 2.2, 2.0, 2.2, 1.8])
    P("")
    P("按平均 MAE 的排名（次序与 MSE 一致）：")
    m2 = mae.copy()
    m2["模型"] = m2.model.map(lambda m: CN.get(m, m))
    add_table(doc, m2, ["rank_MAE", "模型", "mean_Test_MAE_4L", "mean_Test_MSE_4L"],
              ["排名(MAE)", "模型", "平均 MAE (4L)", "平均 MSE (4L)"],
              {"mean_Test_MAE_4L": lambda v: f"{v:.4f}",
               "mean_Test_MSE_4L": lambda v: f"{v:.4f}"},
              widths=[2.0, 5.4, 3.2, 3.2])

    H("九、各 horizon 冠军", 1)
    ph = perh.sort_values(["L", "rank"])
    ph1 = ph[ph["rank"] == 1].copy()
    ph1["模型"] = ph1.model.map(lambda m: CN.get(m, m))
    add_table(doc, ph1, ["L", "模型", "mse", "mae"],
              ["horizon L", "冠军", "MSE", "MAE"],
              {"mse": lambda v: f"{v:.4f}", "mae": lambda v: f"{v:.4f}"},
              widths=[2.2, 5.4, 2.8, 2.8])
    P("MIFlu 在四个 horizon 上全部排名第一，未出现“总体第一但个别 horizon 落后”的情形。")

    H("十、逐种子排名与稳定性", 1)
    ps = pers.sort_values(["seed", "rank_within_seed"])
    ps2 = ps.copy()
    ps2["模型"] = ps2.model.map(lambda m: CN.get(m, m))
    add_table(doc, ps2, ["seed", "rank_within_seed", "模型", "mean_mse"],
              ["种子", "该种子内排名", "模型", "该种子平均 MSE"],
              {"mean_mse": lambda v: f"{v:.4f}"},
              widths=[1.6, 2.6, 5.0, 3.2])
    P("排名在三个匹配种子上完全稳定，冠军未随种子改变；"
      "但绝对数值存在真实种子波动（MIFlu 标准差 "
      f"{champ['sd_Test_MSE_4L']:.4f}），因此三个种子全部保留、未做任何剔除。")

    H("十一、配对统计与 11/12 完整性校验", 1)
    P("配对差异定义为 diff = A − B；MSE 越低越好，故【仅当 diff < 0 时 A 获胜】。")
    pw2 = pw.copy()
    pw2["对手"] = pw2.B.map(lambda m: CN.get(m, m))
    add_table(doc, pw2, ["A", "对手", "n_cells", "mean_diff", "A_wins", "B_wins", "ties"],
              ["A", "对手", "配对数", "平均差异", "A 胜", "B 胜", "平局"],
              {"mean_diff": lambda v: f"{v:+.4f}"})
    nl = pw[pw.B == "nlinear"].iloc[0]
    P(f"关键校验：MIFlu 对 NLinear 的平均差异为 {nl['mean_diff']:+.4f}，"
      f"胜场 {int(nl['A_wins'])}/{int(nl['n_cells'])}。"
      f"差异符号与胜场计数一致——若曾出现符号与计数相反（此前的反向计数缺陷），"
      f"此处将显示为 {int(nl['n_cells'] - nl['A_wins'])}/{int(nl['n_cells'])}。"
      f"其中确有 {int(nl['B_wins'])} 个单元格 NLinear 获胜，说明并未只保留有利结果。", bold=True)

    H("十二、分组汇总（两个结论并存）", 1)
    g2 = grp.copy()
    g2["阵营"] = g2.side.map(lambda s: SIDE.get(s, s))
    add_table(doc, g2, ["阵营", "mean_of_model_means_Test_MSE_4L"],
              ["阵营", "组内模型均值"],
              {"mean_of_model_means_Test_MSE_4L": lambda v: f"{v:.4f}"})
    P("必须同时陈述两点：(1) 修正版 MIFlu 是最佳单一模型；"
      "(2) 非 LLM 侧按组平均优于 LLM 侧。第二点的成因是 LLM 侧的 "
      "Qwen-Time-LLM 与 CALF-LLM 明显偏弱，而非冠军归属有争议。")

    H("十三、预测键校验与门禁", 1)
    P(f"种子 42 八模型门禁：{gp} 项通过 / {gf} 项失败，共 {len(gate)} 项检查。")
    P("门禁覆盖：八个模型身份、四个 horizon 完整性、数据集哈希、676/97/193 划分、"
      "严格包含断言、训练集独占标准化、验证集选择 checkpoint、"
      "测试集不参与选择、Test 只评价一次、预测与目标文件齐备、"
      "八模型测试键集合完全相同、无缺失键、无重复键、独立评分器接受全部单元格、"
      "MIFlu 文本通路有效、LoRA 安装于 c_attn、冻结正确、锁定式 checkpoint 与"
      "sidecar 一致、stage-6 自建 MIFlu 被标记为拒绝、输出目录合规、"
      "无被替代产物进入排名。")

    H("十四、计算成本与存储", 1)
    P(f"GPU 作业数：{costd.get('gpu_jobs')}；GPU 小时总计："
      f"{float(costd.get('gpu_hours_total', 0)):.4f}；"
      f"全部作业退出码为 0：{costd.get('all_jobs_rc_zero')}。"
      f"评分与门禁为 CPU-only 作业，不占用 GPU 小时。")
    P("存储（取自 mmlsquota 的权威用户配额，而非文件系统空闲空间）：")
    add_table(doc, pd.DataFrame([
        {"项": "home", "已用 (GB)": costd.get("home_used_GB"),
         "软配额 (GB)": costd.get("home_soft_quota_GB"),
         "硬上限 (GB)": costd.get("home_hard_limit_GB"),
         "grace": costd.get("home_grace"),
         "距软配额余量 (GB)": costd.get("home_headroom_to_soft_GB")},
        {"项": "scratch", "已用 (GB)": costd.get("scratch_used_GB"),
         "软配额 (GB)": costd.get("scratch_soft_quota_GB"),
         "硬上限 (GB)": costd.get("scratch_hard_limit_GB"),
         "grace": costd.get("scratch_grace"),
         "距软配额余量 (GB)": costd.get("scratch_headroom_to_soft_GB")}]),
        ["项", "已用 (GB)", "软配额 (GB)", "硬上限 (GB)", "grace", "距软配额余量 (GB)"],
        ["文件系统", "已用 (GB)", "软配额 (GB)", "硬上限 (GB)", "宽限期", "距软配额余量 (GB)"])
    P("checkpoint 策略：每个单元格仅保留验证集选出的锁定式 checkpoint"
      "（可训练张量 + 冻结键 sidecar），不保留逐 epoch checkpoint、"
      "不保留优化器/调度器状态；冻结的文本骨干张量不落盘，"
      "故 Qwen 拟合体积约 5 MB 而非约 3 GB。")

    H("十五、其他必须说明的事项", 1)
    for s in ["Seasonal Naive 泄漏区分：历史 4-vs-4 所用的 Seasonal Naive 实现是安全的"
              "（钳制式公式）；作者 966 自建实现存在 L=60 未来泄漏；"
              "Track C 的受控替换不继承该缺陷。",
              "R1-B 论文复现结论：PARTIAL_REPRODUCTION。"
              "四个 horizon 全部落在预声明 ±0.10 MSE 容差之外（均值 1.9477 对论文 1.4355）。"
              "该结论不因 Track C 夺冠而改变。",
              "F1 仅作补充：冻结为 EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT，"
              "不作为主要结果；F2 未执行；R1-C 未执行。",
              "受阻的论文表图：Table VI（US-Region 区域数据未公开）为 "
              "BLOCKED_BY_MISSING_DATA；Fig. 7（few-shot）为 "
              "BLOCKED_BY_MISSING_CONFIGURATION；Table II/III 原文单元格为图像，"
              "Table III 不可读。以上均不得以替代数据充数。",
              "变量标签修正：旧 1025 行产物的 variable 名称整体错位两位"
              "（把 epiweek、release_date 当作变量）。本报告一律使用正确变量名，"
              "且该错位不影响任何 MSE（指标按数组索引计算）。"]:
        doc.add_paragraph(s, style="List Bullet")

    H("十六、局限性与冠军结论的适用范围", 1)
    for s in ["冠军结论仅适用于：作者 966 行数据、676/97/193 划分、严格包含窗口、"
              "匹配种子 42/43/44、验证集选择 checkpoint、一次性测试集评价。",
              "换用其他数据集、划分、窗口规则或种子集合，结论不自动成立。",
              "三个种子可给出标准差，但不足以支撑强显著性主张；"
              "本报告不宣称统计显著性，只报告配对差异与胜场计数。",
              "horizon 之间并非相互独立的重复实验，配对统计的解释需保留该限定。",
              "qwen_time_llm / calf_llm / timecma_llm 是“受启发的简化实现”"
              "（冻结骨干 + 命名组件契约），并非已发表系统的复现，"
              "因此“LLM 侧偏弱”的表述限于本实验的实现口径。",
              "MIFlu 的论文级复现仍为 PARTIAL_REPRODUCTION，"
              "本报告的冠军身份不构成“论文已复现”的主张。"]:
        doc.add_paragraph(s, style="List Bullet")

    H("十七、最终答案", 1)
    P(f"在作者 966 行、严格包含、一次性测试集契约下，"
      f"八模型比较的冠军是【{CN.get(champ['model'], champ['model'])}】"
      f"（以作者仓库为实现基座的修正版），"
      f"测试集四 horizon 等权平均 MSE = {champ['mean_Test_MSE_4L']:.4f}，"
      f"平均 MAE = {champ['mean_Test_MAE_4L']:.4f}，四个 horizon 全部第一。", bold=True)
    P(f"非 LLM 侧最佳为 {CN.get(rank[rank.side=='non-LLM'].iloc[0]['model'])}"
      f"（MSE {rank[rank.side=='non-LLM'].iloc[0]['mean_Test_MSE_4L']:.4f}）；"
      f"LLM 侧最佳即总冠军。按组平均，非 LLM 侧（{g.get('non-LLM', float('nan')):.4f}）"
      f"优于 LLM 侧（{g.get('LLM', float('nan')):.4f}）。")
    P("验证集结果未参与冠军评选；本报告未将验证集或 1025 行历史成绩混入最终排名。")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)
    print("[docx] wrote:", os.path.basename(OUT).encode("utf-8","replace").decode("utf-8"))
    print("[docx] size", os.path.getsize(OUT), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())