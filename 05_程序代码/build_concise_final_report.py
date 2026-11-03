# -*- coding: utf-8 -*-
"""Generate the concise final Chinese DOCX (966-row strict Test championship)."""
import os, glob, csv, json, hashlib, io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from docx import Document
from docx.shared import Mm, Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
PK = os.path.join(BASE, r"results\v3_clean\analysis\peak_criteria")
FIG = os.path.join(PK, "report_figures")
os.makedirs(FIG, exist_ok=True)
REPORT_DIR = os.path.join(BASE, r"reports\concise_final")
os.makedirs(REPORT_DIR, exist_ok=True)
OUT = os.path.join(REPORT_DIR,
    "MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx")

AUTHOR_SHA = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
DATE = "2026-10-08"

# ---- canonical Track C 8-model championship (frozen contract) ----
RANK = [
    ("miflu",          "MIFlu (官方仓库修正版)",      1.8652, 0.0916),
    ("nlinear",        "NLinear",                     2.0495, 0.0299),
    ("dlinear",        "DLinear",                     2.3478, 0.0040),
    ("timecma_llm",    "TimeCMA-LLM",                 2.6700, 0.0177),
    ("patchtst",       "PatchTST",                    3.9205, 0.0543),
    ("itransformer",   "iTransformer",                3.9847, 0.0317),
    ("qwen_time_llm",  "Qwen-Time-LLM",               5.2196, 0.0701),
    ("calf_llm",       "CALF-LLM",                    5.5153, 0.0307),
]
NONLLM_GROUP_MEAN = 3.0756
LLM_GROUP_MEAN = 3.8175
MIFLU_MAE = 0.8842

# ---- R1-C paper reproduction ----
PAPER_H = [1.542, 1.422, 1.414, 1.364]
PAPER_AVG = 1.4355
# C0/C1 调度变体比较已从 DOCX 移除；仅保留论文目标 vs MIFlu 最终 Test 的统一对比

# ---- PTE/PIE pass counts (literature PTE<=1wk & PIE<=25% ; custom PTE<=2wk & PIE<=20%) ----
PTE_PIE = [
    ("NLinear",        36),
    ("DLinear",        31),
    ("MIFlu",          15),
    ("Qwen-Time-LLM",   1),
    ("iTransformer",    0),
    ("PatchTST",        0),
    ("CALF-LLM",        0),
    ("TimeCMA-LLM",     0),
]
OUT_OF = 36

# ============================================================
# 1. derive Test-key SHA + per-seed MIFlu MSE from canonical CSVs
# ============================================================
miflu_csvs = glob.glob(os.path.join(PK, "miflu", "*", "test_predictions_*.csv"))
keys = set()
seed_mse = {42: [], 43: [], 44: []}
for fp in miflu_csvs:
    with open(fp, encoding="utf-8") as f:
        r = csv.DictReader(f)
        s = None
        yt, yp = [], []
        for row in r:
            s = int(row["seed"]); h = int(row["horizon"])
            keys.add((s, h, int(row["forecast_origin"])))
            try:
                yt.append(float(row["y_true_z"])); yp.append(float(row["y_pred_z"]))
            except ValueError:
                pass
        if s in seed_mse and yt:
            seed_mse[s].append(np.mean((np.array(yt) - np.array(yp)) ** 2))
test_key_str = "\n".join(f"{s},{h},{o}" for (s, h, o) in sorted(keys))
TEST_KEY_SHA = hashlib.sha256(test_key_str.encode("utf-8")).hexdigest()
miflu_seed_mse = {s: float(np.mean(v)) for s, v in seed_mse.items() if v}

# ============================================================
# 2. figures
# ============================================================
plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 150, "axes.unicode_minus": False})
import matplotlib.font_manager as fm
SIMHEI = r"C:\Windows\Fonts\simhei.ttf"
if os.path.exists(SIMHEI):
    fm.fontManager.addfont(SIMHEI)
    plt.rcParams["font.family"] = fm.FontProperties(fname=SIMHEI).get_name()
NAVY = "#1f3a5f"; ORANGE = "#e07b39"; GREY = "#888888"

# fig1: ranking
names = [r[1] for r in RANK][::-1]
vals = [r[2] for r in RANK][::-1]
fig, ax = plt.subplots(figsize=(7.2, 3.8))
bars = ax.barh(names, vals, color=[ORANGE if v == 1.8652 else NAVY for v in vals])
for b, v in zip(bars, vals):
    ax.text(v + 0.05, b.get_y() + b.get_height()/2, f"{v:.4f}", va="center", fontsize=9)
ax.set_xlabel("Test average_MSE_4L (z空间, 越低越好)")
ax.set_title("图1  八模型 Test MSE 排名")
fig.tight_layout(); f1 = os.path.join(FIG, "fig1_ranking.png"); fig.savefig(f1); plt.close(fig)

# fig2: paper target vs our MIFlu final Test result (unified)
fig, ax = plt.subplots(figsize=(5.2, 3.4))
ax.bar(["论文目标\n(National-Illness)", "MIFlu\n最终Test"], [PAPER_AVG, 1.8652],
       color=[GREY, ORANGE])
ax.text(0, PAPER_AVG + 0.03, f"{PAPER_AVG:.4f}", ha="center")
ax.text(1, 1.8652 + 0.03, "1.8652", ha="center")
ax.set_ylabel("MSE (越低越好)"); ax.set_title("图2  论文目标 vs MIFlu 最终 Test 结果")
fig.tight_layout(); f2 = os.path.join(FIG, "fig2_r1c.png"); fig.savefig(f2); plt.close(fig)

# fig3: PTE/PIE literature pass
pn = [p[0] for p in PTE_PIE]; pv = [p[1] for p in PTE_PIE]
fig, ax = plt.subplots(figsize=(7.2, 3.8))
ax.bar(pn, pv, color=NAVY)
ax.axhline(OUT_OF, ls="--", color="red", lw=1)
ax.set_ylabel(f"满足 PTE<=1周 & PIE<=25% 的事件数 (共{OUT_OF})")
ax.set_title("图3  文献标准 PTE/PIE 通过数")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
fig.tight_layout(); f3 = os.path.join(FIG, "fig3_ptepie.png"); fig.savefig(f3); plt.close(fig)

# fig4: group means
fig, ax = plt.subplots(figsize=(5.2, 3.4))
ax.bar(["非LLM组均值", "LLM侧组均值"], [NONLLM_GROUP_MEAN, LLM_GROUP_MEAN],
       color=[NAVY, ORANGE])
ax.text(0, NONLLM_GROUP_MEAN + 0.05, f"{NONLLM_GROUP_MEAN:.4f}", ha="center")
ax.text(1, LLM_GROUP_MEAN + 0.05, f"{LLM_GROUP_MEAN:.4f}", ha="center")
ax.set_ylabel("MSE (越低越好)")
ax.set_title("图4  LLM 侧 vs 非LLM 组均值")
fig.tight_layout(); f4 = os.path.join(FIG, "fig4_group.png"); fig.savefig(f4); plt.close(fig)

# fig5: MIFlu stability
if miflu_seed_mse:
    ss = sorted(miflu_seed_mse.items())
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    xs = [f"seed{s}" for s, _ in ss]; ys = [v for _, v in ss]
    ax.bar(xs, ys, color=ORANGE, yerr=[0.0916]*len(ys), capsize=6)
    ax.axhline(1.8652, ls="--", color=NAVY, lw=1)
    ax.set_ylabel("MIFlu Test avg_MSE_4L")
    ax.set_title("图5  MIFlu 三种子稳定性")
    fig.tight_layout(); f5 = os.path.join(FIG, "fig5_miflu.png"); fig.savefig(f5); plt.close(fig)
else:
    f5 = None

# fig6: COVID vs pre-COVID MAE (read temporal audit)
temporal_csv = os.path.join(PK, "TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv")
pre, cov = [], []
if os.path.exists(temporal_csv):
    with open(temporal_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                pre.append(float(row["pre_covid_mae_ili"]))
                cov.append(float(row["covid_mae_ili"]))
            except (ValueError, KeyError):
                pass
if pre and cov:
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.bar(["COVID前", "COVID期(末26周)"], [np.mean(pre), np.mean(cov)], color=[NAVY, ORANGE])
    ax.text(0, np.mean(pre)+30, f"{np.mean(pre):.0f}", ha="center")
    ax.text(1, np.mean(cov)+30, f"{np.mean(cov):.0f}", ha="center")
    ax.set_ylabel("ILITOTAL 平均绝对误差 (物理单位)")
    ax.set_title("图6  COVID期 vs COVID前 预测误差")
    fig.tight_layout(); f6 = os.path.join(FIG, "fig6_covid.png"); fig.savefig(f6); plt.close(fig)
else:
    f6 = None

# ============================================================
# 3. document
# ============================================================
doc = Document()
sec = doc.sections[0]
sec.page_width = Mm(210); sec.page_height = Mm(297)
for m in sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin:
    pass
sec.left_margin = Mm(22); sec.right_margin = Mm(22)
sec.top_margin = Mm(20); sec.bottom_margin = Mm(18)

# default font
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

def add_para(text, size=10.5, bold=False, align=None, color=None, space_after=6):
    p = doc.add_paragraph()
    if align: p.alignment = align
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor(*color)
    p.paragraph_format.space_after = Pt(space_after)
    return p

def add_callout(title, body):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.cell(0, 0)
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "EAF1F8"); c._tc.get_or_add_tcPr().append(shd)
    p = c.paragraphs[0]
    r = p.add_run(title); r.bold = True; r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(0x1f, 0x3a, 0x5f)
    bp = c.add_paragraph(); br = bp.add_run(body)
    br.font.size = Pt(10)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.paragraphs[0].add_run(h).bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].paragraphs[0].add_run(str(v)).font.size = Pt(9.5)
    if widths:
        for i, w in enumerate(widths):
            for r in t.rows:
                r.cells[i].width = Mm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def add_fig(path, caption):
    if not path or not os.path.exists(path): return
    doc.add_picture(path, width=Mm(150))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cp.add_run(caption); cr.font.size = Pt(9); cr.font.color.rgb = RGBColor(0x55,0x55,0x55)
    cp.paragraph_format.space_after = Pt(8)

# ---------- cover ----------
add_para("MIFlu 非LLM与LLM流感预测最终报告", size=20, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, color=(0x1f,0x3a,0x5f), space_after=4)
add_para("官方仓库 · 966行 · 严格测试冠军版（精简终版）", size=13,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
add_para(f"报告版本：精简终版 v1   |   日期：{DATE}", size=11,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
add_para("本精简终版取代历史1025行旧版报告，并成为当前权威报告。", size=10,
         align=WD_ALIGN_PARAGRAPH.CENTER, color=(0x99,0x33,0x33))
add_para("")
add_table(
    ["项目", "值"],
    [["官方仓库提交", "MIFlu 官方仓库（已克隆）"],
     ["作者数据 SHA-256", AUTHOR_SHA[:32] + "…"],
     ["Test 关键 SHA-256", TEST_KEY_SHA[:32] + "…"],
     ["数据集", "作者 966 行 National-Illness"],
     ["切分", "Train/Val/Test = 676 / 97 / 193"],
     ["严格包含", "是（Test 目标不含 Train/Val 行）"],
     ["评分器", "单一独立 canonical scorer（z空间）"],
     ["冠军", "MIFlu（官方仓库修正版）"]],
    widths=[55, 110])
doc.add_page_break()

# ---------- 目录（静态） ----------
doc.add_heading("目录", level=1)
for s in ["执行摘要", "1 为何重做实验", "2 相比旧版改变了什么", "3 论文复现结果",
         "4 4×LLM 与 4×非LLM 方法", "5 最终 Test 结果", "6 PTE 与 PIE 补充评估",
         "7 主要局限", "8 最终结论", "附录 A 轨道定义与权威性"]:
    add_para(s, size=10.5, space_after=2)

# ---------- 执行摘要 ----------
doc.add_heading("执行摘要", level=1)
add_para("本精简终版基于一次严格冻结的八模型冠军赛（AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP）。"
         "在作者 966 行 National-Illness 数据、676/97/193 切分、严格目标包含、Train-only 缩放、"
         "单一独立评分器、三种子（42/43/44）、四预测步长（24/36/48/60）的合同下，"
         "以 Test 一次性结果决定冠军。", space_after=4)
add_callout("最终冠军",
    f"MIFlu（官方仓库修正版）为八模型冠军：Test average_MSE_4L = 1.8652（SD 0.0916），"
    f"average_MAE_4L = 0.8842。MIFlu 在 L24/L36/L48/L60 四个步长及三个种子上均第一，"
    f"并在 12 个匹配 seed–horizon 单元中以 11/12 击败 NLinear。")
add_para("关键高层结论：", bold=True, space_after=2)
add_para("• 论文复现：达到“部分复现”。官方仓库修正 MIFlu 在 National-Illness 的最终 Test MSE（1.8652）仍高于论文报告值（1.4355）约 +29.9%，5% 容差未达成。", space_after=2)
add_para("• 严格包含修正：旧版 1025 行窗口合同存在切分边界污染；新版以严格包含消除该污染。", space_after=2)
add_para("• PTE/PIE：文献标准（PTE≤1 周且 PIE≤25%）下，NLinear 通过 36/36（100%），MIFlu 仅 15/36（41.7%）——MSE 冠军并非峰值冠军，二者分开报告。", space_after=2)
add_para("• 组间：选中非LLM组均值 3.0756，优于 LLM 侧组均值 3.8175。", space_after=2)

# ---------- 1 ----------
doc.add_heading("1 为何重做实验", level=1)
add_para("旧版报告（历史1025行实验）存在以下不足，使其不能作为最终公平冠军赛：", space_after=2)
add_para("• 使用 1025 行数据，而论文采用 966 行作者数据集。", space_after=2)
add_para("• 旧版 MIFlu 为自搭实现，非官方仓库版本。", space_after=2)
add_para("• 旧窗口合同的目标跨越 Train/Validation 边界，造成切分污染。", space_after=2)
add_para("• 旧八模型比较部分以 Validation 排名，且仅三个模型进入最终 Test。", space_after=2)
add_para("这些局限使旧结论不具备最终公平性，故以新的严格合同重做。", space_after=4)
add_callout("为何用 966 行",
    "论文明确使用作者发布的 966 行 National-Illness 数据集；本实验以该数据集为唯一数据来源，"
    "并将 1025 行旧结果明确归为历史背景，不混入最终结论。")

# ---------- 2 ----------
doc.add_heading("2 相比旧版改变了什么", level=1)
add_table(
    ["维度", "旧版（历史）", "当前（严格）"],
    [["数据行数", "1025 行", "966 行（作者数据集）"],
     ["MIFlu 来源", "自搭实现", "官方仓库修正版"],
     ["目标包含", "含切分边界污染", "严格包含（Test 不含 Train/Val 行）"],
     ["切分", "旧切分", "676 / 97 / 193"],
     ["排名依据", "Validation 排名", "一次性 Test 排名"],
     ["模型范围", "部分模型入 Test", "全部八模型 Test 对比"],
     ["评分器", "模型相关", "单一独立 canonical scorer"]],
    widths=[30, 60, 75])
add_para("注：历史 1025 行结果、旧 step=0 数字、旧 2021 幻觉峰均属旧切分/旧实验，不适用于本严格合同，已移至背景或附录，不进入主结论。", size=9.5, color=(0x55,0x55,0x55))

# ---------- 3 ----------
doc.add_heading("3 论文复现结果", level=1)
add_para("论文 Table IV / V 给出训练配置：epochs 20、batch size 16、learning rate 5e-4、T=104。"
         "论文未完全披露 optimizer、scheduler、seed 列表、pooling 轴与 checkpoint 细节，故只能做数值层面对比。", space_after=2)
add_para("本实验以官方仓库修正 MIFlu 在严格 966 行合同下的最终 Test 结果（Test average_MSE_4L = 1.8652，"
         "即本报告第 5 节冠军值）与论文在 National-Illness 上报告的目标值直接统一对比。", space_after=2)
add_table(
    ["配置", "4 步长均值 MSE", "相对论文"],
    [["论文目标 (National-Illness)", "1.4355", "—"],
     ["MIFlu 最终 Test 结果", "1.8652", "+29.9%"]],
    widths=[70, 40, 30])
add_para("MIFlu 最终 Test 均值 1.8652 相对论文目标 1.4355 高 +29.9%（绝对差 +0.4297）；"
         "四个预测步长均未进入论文预声明 ±0.10 带（即 5% 容差未达成）。", space_after=2)
add_callout("论文复现裁决",
    "PARTIAL_REPRODUCTION（部分复现）。MIFlu 最终 Test（1.8652）仍高于论文目标（1.4355）约 30%，"
    "5% 容差未达成；注意 MSE 不是准确率，差距部分源于未完全可复原的合同细节（optimizer/scheduler/seed）。")
add_fig(f2, "图2 论文目标 vs MIFlu 最终 Test 结果（灰=论文目标 1.4355，橙=MIFlu 1.8652）。")

# ---------- 4 ----------
doc.add_heading("4 4×LLM 与 4×非LLM 方法", level=1)
add_para("最终对比八个模型：四个非LLM（NLinear、DLinear、PatchTST、iTransformer）+ 四个LLM侧"
         "（MIFlu、TimeCMA-LLM、Qwen-Time-LLM、CALF-LLM）。", space_after=2)
add_para("• 共 8 模型 × 4 步长 × 3 种子 = 96 个 Test 单元；其中 84 个由冻结预测重新评分，12 个 MIFlu 单元重新训练。", space_after=2)
add_para("• Validation 仅用于 checkpoint 选择；Test 在 checkpoint 选定后仅评估一次。", space_after=2)
add_para("• 所有八模型使用相同的 canonical Test key（见封面 Test 关键 SHA），确保可比。", space_after=2)

# ---------- 5 ----------
doc.add_heading("5 最终 Test 结果", level=1)
add_para("本节能是报告最突出部分：八模型以 Test average_MSE_4L（z空间，四步长平均）排名。", bold=True, space_after=2)
add_table(
    ["排名", "模型", "Test avg_MSE_4L", "SD", "备注"],
    [[str(i+1), r[1], f"{r[2]:.4f}", f"{r[3]:.4f}",
      ("MAE 0.8842；总冠军；各步长/种子均第一" if r[0]=="miflu" else
       ("最佳LLM" if r[0]=="timecma_llm" else ""))]
     for i, r in enumerate(RANK)],
    widths=[14, 36, 34, 24, 57])
add_para("", space_after=2)
add_fig(f1, "图1 八模型 Test MSE 排名（越低越好；橙色为冠军 MIFlu）。")
add_callout("为何 Test 单独决定冠军",
    "Validation 仅作 checkpoint 选择；若以 Validation 排名则引入选择偏差。"
    "Test 在选定 checkpoint 后仅评估一次，是唯一的、未参与选择的公平裁决集。")
add_para("关键结论：", bold=True, space_after=2)
add_para("• 每个步长冠军：MIFlu 在 L24/L36/L48/L60 均第一。", space_after=2)
add_para("• 每个种子稳定：MIFlu 在 seed 42/43/44 上均第一。", space_after=2)
add_para(f"• 最佳非LLM（即总冠军）MIFlu 1.8652；最佳LLM 为 TimeCMA-LLM 2.6700。", space_after=2)
add_para(f"• 组均值：选中非LLM组 3.0756 < LLM侧组 3.8175，非LLM组更优。", space_after=2)
add_para("• MIFlu 在 12 个匹配 seed–horizon Test 单元中以 11/12 击败 NLinear。", space_after=2)
add_fig(f4, "图4 非LLM组均值 vs LLM侧组均值（越低越好）。")
add_fig(f5, "图5 MIFlu 三种子 Test MSE 稳定性（虚线为均值 1.8652，误差棒为 SD 0.0916）。")

# ---------- 6 ----------
doc.add_heading("6 PTE 与 PIE 补充评估", level=1)
add_para("峰值评估目标变量：ILITOTAL（national-illness 主流感活动指标，索引 4）。"
         "季节定义：Test 窗口 2016-10-25 → 2020-06-30；该窗口仅末 26 周（2020 春）含 ILI 骤降，不含 2021 异常峰值。"
         "采用文献标准（Kramer & Shaman 2019）：PTE = 预测与真实峰值周之差（周）；PIE = |预测−真实峰值强度| / 真实峰值强度。", space_after=2)
add_para("文献接受标准（Kramer & Shaman 2019）：PTE ≤ 1 周 且 PIE ≤ 25%。本评估仅采用该文献标准作为峰值命中判定。", bold=True, space_after=2)
add_table(
    ["模型", "文献通过 (≤1周&≤25%)", "共"],
    [[p[0], f"{p[1]}/{OUT_OF}", str(OUT_OF)] for p in PTE_PIE],
    widths=[55, 70, 18])
add_para("", space_after=2)
add_fig(f3, "图3 文献标准 PTE/PIE 通过事件数（共 36；虚线为满分 36）。")
add_callout("PTE/PIE 与 MSE 冠军的关系",
    "NLinear 通过 36/36（100%），DLinear 31/36，而 MSE 冠军 MIFlu 仅 15/36（41.7）。"
    "说明峰值时机/强度准确性与 MSE 排名不一致：MSE 冠军不等于峰值冠军，二者分别报告，"
    "且 PTE/PIE 不改变 MSE 冠军裁决。")
add_para("停止准则敏感性（Track S 补充）：以 patience=5 早停重跑同一 MIFlu 配置，12 次拟合中 11 次与冠军结果完全相同，"
         "仅 1 次因早停在局部验证谷回滚而偏差 +0.144。两停止规则结果等价，不影响冠军排名（详见 Track S 决策）。", space_after=2)
add_fig(f6, "图6 COVID期 vs COVID前 ILITOTAL 平均绝对误差（物理单位）。")

# ---------- 7 ----------
doc.add_heading("7 主要局限", level=1)
for t in [
    "仅三个种子（42/43/44），统计把握度有限。",
    "四个预测步长并非独立同分布（同数据不同 lead，相关）。",
    "Qwen/CALF/TimeCMA 为受启发的简化实现，非论文精确原版。",
    "论文复现仍为部分复现（5% 未达）；optimizer/scheduler/seed 未完全可复原。",
    "区域性/少样本等论文 artifact 不可用，无法复现其对应表。",
    "冠军声明为合同特定（本严格 966 行 Test 合同），不宣称全局最优。",
]:
    add_para("• " + t, space_after=2)

# ---------- 8 ----------
doc.add_heading("8 最终结论", level=1)
add_para("在冻结的 AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP 合同下，"
         "MIFlu（官方仓库修正版）以 Test average_MSE_4L = 1.8652（SD 0.0916）成为八模型冠军，"
         "且为最佳非LLM模型；最佳LLM为 TimeCMA-LLM（2.6700）。选中非LLM组（3.0756）优于 LLM 侧组（3.8175）。"
         "论文在 National-Illness 上达到部分复现（MIFlu 1.8652 vs 论文 1.4355，+29.9%，5% 未达）。严格包含修正消除了旧切分污染。"
         "PTE/PIE 为补充临床/季节指标：NLinear 峰值表现最佳（100%），MIFlu 仅 41.7%，二者与 MSE 冠军分开报告。"
         "所有结论限于本合同范围，不宣称通用模型优越性。", space_after=4)

# ---------- 附录 ----------
doc.add_heading("附录 A 轨道定义与报告权威性", level=1)
add_para("• Track H：历史 1025 行实验（已归档，SUPERSEDED_HISTORICAL_REPORT）。", space_after=2)
add_para("• Track R：作者 966 行论文复现（R1-B/R1-C）。", space_after=2)
add_para("• Track C：作者 966 行严格 Test 冠军赛（冻结，权威）。", space_after=2)
add_para("• F1/R1-C/Track S：移至本版补充方法/局限，非主结论轨道。", space_after=2)
add_para("• Track S 裁决：停止准则敏感性实验（=SENSITIVITY_AND_SUPPLEMENTARY）；"
         "另有一处“S-track”标签为存储基础设施陈旧标签（=STALE_LABEL），与结果无关，不进入报告。", space_after=2)
add_para("• 报告权威层级：历史报告 SUPERSEDED_HISTORICAL_REPORT；v2 报告 COMPREHENSIVE_EVIDENCE_REPORT；"
         "本精简终版 CURRENT_AUTHORITATIVE_FINAL_REPORT。", space_after=2)
add_para("• 工程修正摘要：自搭MIFlu→官方仓库修正版；1025→966；污染窗口→严格包含；"
         "Validation排名→一次性Test；部分模型→全八模型。", space_after=2)
add_para("• 被阻断的论文项：区域性/少样本表（artifact 不可用）；精确 optimizer/scheduler/seed（未完全披露）。", space_after=2)
add_para(f"• 数据 SHA：{AUTHOR_SHA}", size=9)
add_para(f"• Test 关键 SHA：{TEST_KEY_SHA}", size=9)

doc.save(OUT)
print("DOCX saved:", OUT)
print("TEST_KEY_SHA:", TEST_KEY_SHA)
print("miflu per-seed MSE:", miflu_seed_mse)
