# -*- coding: utf-8 -*-
import os, shutil, subprocess, sys
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

SRC = Path(r"C:\Users\Asus\Desktop\FYP code\_review_20261104\full\MIFlu_Reviewed_Project\01_最终报告")
OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v7")
OUT.mkdir(parents=True, exist_ok=True)
DOCS = ["ieee_manuscript_en", "ieee_manuscript_zh", "progress_report_en",
        "progress_report_zh", "report_internal_en", "report_internal_zh"]

def zh(run):
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

for name in DOCS:
    src = SRC / (name + ".docx")
    dst = OUT / (name + ".docx")
    shutil.copy2(src, dst)
    d = Document(dst)
    d.add_page_break()
    h = d.add_heading("V7 addendum — new 1120-cell common panel / V7 附录 — 新 1120 单元共同面板", level=1)
    for r in h.runs:
        r.font.size = Pt(13)

    def p(text, bold=False, size=9):
        par = d.add_paragraph()
        run = par.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            zh(run)
        return par

    p("Status: the national panel is complete at 1120/1120 cells; MIFlu seven-channel recovery is 40/40. "
      "Historical revision-9.2 numbers remain the old snapshot and are not overwritten.", False)
    p("状态：全国面板 1120/1120 完成；MIFlu 七通道恢复 40/40。旧 revision-9.2 数字仍是旧快照，未被覆盖。", False)
    p("New leading MSE (all-valid): MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782. "
      "Crop panel: 1.4994 / 1.6352 / 1.9027; the MIFlu crop mean 1.4994 reproduces the old 1.4995.", False)
    p("新 MSE（all-valid）：MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782；crop 1.4994 / 1.6352 / 1.9027，"
      "MIFlu crop 1.4994 重现旧值 1.4995。", False)
    p("Peak step passes (of 1680 per model): MIFlu 252 (15.0%), PatchTST 215 (12.8%), NLinear 57 (3.4%). "
      "The historical NLinear peak-champion claim is not reproduced; the old 16-unit table is a different population.", True)
    p("峰值 step passes（每模型 1680）：MIFlu 252（15.0%）、PatchTST 215（12.8%）、NLinear 57（3.4%）。"
      "旧「NLinear 峰值冠军」在新面板不成立；旧 16 单元表是不同总体。", True)
    p("Ablation is non-monotonic: K4 1.4989 best, K6 1.5457 (n=10), K2 1.5813, K8 1.6124, no_lora 1.6330, K12 1.7604 worst.", False)
    p("消融非单调：K4 1.4989 最佳，K6 1.5457（n=10），K2 1.5813，K8 1.6124，no_lora 1.6330，K12 1.7604 最差。", False)
    p("Regional Table VI: 51/53 valid; walk-forward only 473/1020 valid (329 non-finite, 218 missing), so walk-forward is partial. "
      "Paired Wilcoxon/Holm is exploratory (349/378 rejections; cells are not independent).", False)
    p("区域 Table VI：51/53 有效；walk-forward 仅 473/1020 有效（329 non-finite、218 missing），仍是部分。"
      "Paired Wilcoxon/Holm 属探索性（349/378 拒绝；cell 非独立）。", False)
    p("Do not claim full walk-forward, monotonic depth, or submission readiness. See v7/MESSAGE_TO_CHATGPT.md and SCIENTIFIC_AUDIT.md.", False)
    p("不得声称完整 walk-forward、单调深度或投稿就绪。详见 v7/MESSAGE_TO_CHATGPT.md 与 SCIENTIFIC_AUDIT.md。", False)

    table = d.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = ["Model", "MSE all-valid", "MSE crop", "Peak passes /1680"]
    for i, t in enumerate(hdr):
        c = table.rows[0].cells[i]
        c.text = t
    for row in [("MIFlu", "1.7944", "1.4994", "252 (15.0%)"),
                ("PatchTST", "1.9521", "1.6352", "215 (12.8%)"),
                ("NLinear", "2.0782", "1.9027", "57 (3.4%)")]:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = v
    d.save(dst)

NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
for name in DOCS:
    src = OUT / (name + ".docx"); dst = OUT / (name + ".pdf")
    if dst.exists(): dst.unlink()
    r = subprocess.run([NODE, CLI, "convert", "--input", str(src), "--output", str(dst)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(name, src.stat().st_size, dst.stat().st_size if dst.exists() else 0, r.returncode)
