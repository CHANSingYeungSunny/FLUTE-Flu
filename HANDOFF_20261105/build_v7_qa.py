# -*- coding: utf-8 -*-
import shutil, subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

src = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\report_internal_qa_zh.docx")
out = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v7\report_internal_qa_zh_v7.docx")
out.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, out)
d = Document(out)
d.add_page_break()
d.add_heading("V7 更新索引（2026-11-06）— Q01–Q25 需修改的答案", level=1)

def p(t, b=False):
    par = d.add_paragraph()
    r = par.add_run(t); r.bold = b; r.font.size = Pt(9)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

p("本索引不删除、不改写原 25 题；下列题目在新 1120 面板下需要替换旧结论，保留原题号与引用。", True)
p("1. 峰值相关题：旧答案称 NLinear 为 K&S 冠军（4/16）。新面板 step-level passes：MIFlu 252/1680（15.0%）、PatchTST 215/1680（12.8%）、NLinear 57/1680（3.4%）；旧 16 单元表与新 1680 step rows 不是同一总体。应改为 MIFlu/PatchTST 领先、NLinear 不再复现冠军。")
p("2. MSE 排名题：新 all-valid 为 MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782；crop 为 1.4994/1.6352/1.9027。旧 1.4995/1.6621/1.8716 属旧快照，不能与新面板混写。")
p("3. 消融题：60 格 + K6 参考显示非单调：K4 1.4989 最佳、K6 1.5457（n=10）、K2 1.5813、K8 1.6124、no_lora 1.6330、K12 1.7604。删除任何单调深度趋势说法。")
p("4. rolling-origin / 外部效度题：walk-forward 仅 473/1020 有效（329 non-finite、218 missing），Table VI 51/53；只能写 partial，不能写完成或泛化验证。")
p("5. 统计题：378 对 Wilcoxon + Holm 为探索性（349/378 拒绝，最小校正 p 约 6.9e-10）；cell 共享同一序列与重叠目标，不是独立样本，不得称确认性显著。")
p("6. 复现题：MIFlu crop 1.4994 与旧 1.4995 一致；新 all-valid 1.7944 是不同 panel，不得冒充旧复现。")
p("完整证据见 v7/V7_SCIENTIFIC_ADDENDUM.md、final/SCIENTIFIC_AUDIT.md、final/PEAK_BY_STEP.csv。")
d.save(out)

NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
pdf = out.with_suffix(".pdf")
if pdf.exists():
    pdf.unlink()
r = subprocess.run([NODE, CLI, "convert", "--input", str(out), "--output", str(pdf)],
                   capture_output=True, text=True, errors="replace")
print(out.stat().st_size, pdf.stat().st_size if pdf.exists() else 0, r.returncode)
