# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v7")
OUT.mkdir(parents=True, exist_ok=True)
doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Inches(0.8)
    s.left_margin = s.right_margin = Inches(0.9)
style = doc.styles["Normal"]; style.font.name = "Microsoft YaHei"; style.font.size = Pt(10)

def set_zh(run, size=10, bold=False):
    run.font.name = "Microsoft YaHei"; run.font.size = Pt(size); run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

def h(t, l=1):
    p = doc.add_heading(t, level=l)
    for r in p.runs: set_zh(r, 14 if l == 1 else 11, True)

def p(t, size=10, bold=False):
    par = doc.add_paragraph(); r = par.add_run(t); set_zh(r, size, bold); return par

def table(head, rows, cap):
    p(cap, 9, True)
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"
    for i, x in enumerate(head):
        c = t.rows[0].cells[i]; c.text = str(x)
        for r in c.paragraphs[0].runs: set_zh(r, 8, True)
    for row in rows:
        cs = t.add_row().cells
        for i, x in enumerate(row): cs[i].text = str(x)
    doc.add_paragraph()

p("MIFlu 与 27 个流感预测实现的共同十种子重评（V7 中文技术报告）", 15, True).alignment = WD_ALIGN_PARAGRAPH.CENTER
p("CHAN Sing Yeung｜香港城市大学电子工程学系｜2026-11-06｜草稿，非投稿就绪", 8).alignment = WD_ALIGN_PARAGRAPH.CENTER

h("摘要")
p("我们在 966 周全国 ILI 序列上，用同一协议（T=104，L=24/36/48/60，seeds 2021–2030，28 个实现）完成 1,120 个单元。由于旧 MIFlu 导出只有 ILITOTAL，我们从检查点恢复七通道预测，并在 all-valid 与历史 crop 两个相同目标总体面板上重算。all-valid 的领先 MSE 为 MIFlu 1.7944、PatchTST 1.9521、NLinear 2.0782；crop 为 1.4994/1.6352/1.9027，MIFlu crop 重现旧值 1.4995。峰值结论改变：MIFlu 252/1680（15.0%）、PatchTST 215/1680（12.8%）、NLinear 57/1680（3.4%）。60 格深度/LoRA 阶梯非单调：K4 最佳 1.4989，K12 最差 1.7604。区域 Table VI 51/53 有效；walk-forward 仅 473/1020 有效。新面板与旧快照分开报告。")

h("1. 数据与协议")
p("数据为 966 行、七通道，按 676/97/193 切分（边界 0/676/773/966），T=104，L=24/36/48/60，strict containment，seeds 2021–2030。28 个实现 = 13 个传统模型 + 4 个 LLM 预测器 + 11 个冻结语言编码器加共享线性读出。名义 28×4×10=1,120 个单元；确定性拟合按有效重复数单列。")

h("2. 评分面板")
p("all-valid 使用全部有效测试窗口（170/158/146/134）；crop 使用前 (W//16)×16 个窗口（160/144/144/128），即历史 complete-batch 规则。MSE/MAE 为七通道 z-space 均值；峰值用 ILITOTAL 患者数，按 train-fit scaler 反归一化。峰检测 find_peaks(prominence=0.15×range, distance=15)，±8 周一对一匹配，PTE≤1 周且 PIE≤25% 记为通过。")

h("3. 结果")
table(["模型", "MSE all-valid", "MSE crop", "MAE all-valid"],
      [["MIFlu", "1.7944", "1.4994", "0.8529"],
       ["PatchTST", "1.9521", "1.6352", "0.9244"],
       ["NLinear", "2.0782", "1.9027", "0.9652"],
       ["DNN", "2.2802", "2.1173", "1.0401"],
       ["TimeCMA", "2.6255", "2.5765", "1.0879"]],
      "表 1. 两个共同面板的领先平均误差（28 模型，十种子，四跨度）。")
p("两个面板的领先顺序一致：MIFlu < PatchTST < NLinear。crop 面板 MIFlu 1.4994 与旧 1.4995 一致，验证七通道恢复；all-valid 提高所有误差但不改变前三名。")

table(["模型", "平均 PTE（周）", "平均 PIE（%）", "通过 / 1680"],
      [["PatchTST", "0.707", "34.41", "215（12.8%）"],
       ["MIFlu", "0.964", "30.09", "252（15.0%）"],
       ["NLinear", "2.013", "42.35", "57（3.4%）"],
       ["DNN", "1.690", "51.54", "0"]],
      "表 2. step-level Kramer–Shaman 结果（每模型 10 seeds × 168 leads）。")
p("事件级检测与幅度分离：iTransformer 检测 99.1% 但 PIE 71.2%；MIFlu 98.8% 且 PIE 30.4%；PatchTST 97.6% 且 PIE 34.6%；NLinear 92.6% 且 PIE 40.6%。旧「NLinear 峰值冠军」在新面板不成立；旧 16 单元表与新 1680 step rows 不是同一总体。")

table(["变体", "单元", "平均 MSE"],
      [["K4", "12", "1.4989"], ["K6 参考", "10", "1.5457"],
       ["K2", "12", "1.5813"], ["K8", "12", "1.6124"],
       ["no_lora", "12", "1.6330"], ["K12", "12", "1.7604"]],
      "表 3. 深度/LoRA 阶梯，七通道 z-space MSE。")
p("深度非单调：K4 最佳，K12 最差；不得再声称单调深度趋势。")

h("4. 外部效度与统计")
p("区域 Table VI：53 个输出全部有效（L13/s2030 与 L15/s2026 已补跑）；为 10 变量区域聚合，不可与七通道全国均值混算。Walk-forward：1,020 个目录中 802 个在从原始 NPZ 直接重算后有效，218 个无 NPZ；仍不是完整 WF。")
p("统计：378 对 Wilcoxon + Holm，349/378 拒绝，最小校正 p≈6.9e-10；按 seed 的 cluster bootstrap 有 359/378 的 95% CI 排除 0。但同一 seed 内 L 与目标重叠，仍是探索性，不是确认性推断。")

h("5. 限制")
p("单一全国序列；四个跨度复用观测；十种子不是十个独立流行季；CDC 发布日历/vintage 未重建，峰值是回顾性；11 个编码器只测冻结特征+线性读出；未运行 Chronos/TimesFM 等数值基础模型；未做资源测量；区域与 walk-forward 不完整。本文是 v7 草稿，不是投稿就绪版本。")

h("6. 结论")
p("在完整 1,120 单元共同面板上，MIFlu 七通道 MSE 最低，PatchTST 平均峰值时间最好，MIFlu step-level 峰值通过最多；旧 NLinear 峰值冠军不复现；深度非单调。新面板与冻结的旧快照分开保留。")

src = OUT / "V7_INTERNAL_ZH.docx"; doc.save(src)
NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
pdf = src.with_suffix(".pdf")
if pdf.exists(): pdf.unlink()
r = subprocess.run([NODE, CLI, "convert", "--input", str(src), "--output", str(pdf)],
                   capture_output=True, text=True, errors="replace")
print(src.stat().st_size, pdf.stat().st_size if pdf.exists() else 0, r.returncode)
