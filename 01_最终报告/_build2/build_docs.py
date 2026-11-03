# -*- coding: utf-8 -*-
"""Build all six 01_最终报告 (DOCX) from the measured artefacts.

Run from the repo root:  python deliverables/_build2/build_docs.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.shared import Cm, Pt, RGBColor       # noqa: E402

from dlv import data as D          # noqa: E402  (asserts the headline facts on import)
from dlv import tables as TB       # noqa: E402
from dlv.render import Doc, add_rich, HEAD_FONT, MUTED  # noqa: E402
from dlv import text_internal, text_progress, text_ieee  # noqa: E402

OUT = os.path.join(D.ROOT, "01_最终报告")


def render(doc, blocks):
    for kind, payload in blocks:
        if kind == "h1":
            doc.h(1, payload[doc.lang])
        elif kind == "h2":
            doc.h(2, payload[doc.lang])
        elif kind == "h3":
            doc.h(3, payload[doc.lang])
        elif kind == "p":
            doc.p(payload[doc.lang])
        elif kind == "lead":
            doc.p(payload[doc.lang], size=11.2, italic=True, color=doc.accent)
        elif kind == "bul":
            doc.bullets(payload[doc.lang])
        elif kind == "num":
            doc.bullets(payload[doc.lang], numbered=True)
        elif kind == "quote":
            doc.quote(payload[doc.lang])
        elif kind == "table":
            doc.table(TB.ALL[payload]())
        elif kind == "fig":
            doc.figure(payload["name"])
        elif kind == "pb":
            doc.page_break()
        elif kind == "kv":
            doc.kv(payload)
        elif kind == "cols":
            doc.set_columns(payload)
        elif kind == "fig_wide":
            doc.figure(payload, width_cm=17.5)
        elif kind == "ieee_title":
            ia(doc, payload)
        elif kind == "ieee_authors":
            iauthors(doc, payload[doc.lang])
        elif kind == "ieee_abstract":
            iabstract(doc, payload)
        elif kind == "ieee_keywords":
            ikeywords(doc, payload)
        elif kind == "todo":
            itodo(doc, payload[doc.lang])
        elif kind == "refs":
            for line in payload[doc.lang]:
                par = doc.doc.add_paragraph()
                par.paragraph_format.left_indent = Cm(0.55)
                par.paragraph_format.first_line_indent = Cm(-0.55)
                par.paragraph_format.space_after = Pt(3)
                add_rich(par, line, doc.lang, 8.2)
        elif kind == "refs_note":
            doc.p(payload[doc.lang], size=7.8, italic=True, color=MUTED)
        else:  # pragma: no cover
            raise ValueError(kind)


# ---------------------------------------------------------------- IEEE pieces
def ia(doc, text):
    par = doc.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(6)
    par.paragraph_format.space_after = Pt(8)
    add_rich(par, text, doc.lang, 20, bold=True, color=RGBColor(0, 0, 0),
             ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])


def iauthors(doc, text):
    par = doc.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(10)
    for i, line in enumerate(text.split("\n")):
        if i:
            par.add_run().add_break()
        add_rich(par, line, doc.lang, 9.5, italic=(i > 0),
                 ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])


def iabstract(doc, payload):
    par = doc.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(6)
    par.paragraph_format.left_indent = Cm(0.4)
    par.paragraph_format.right_indent = Cm(0.4)
    add_rich(par, payload["label"][doc.lang], doc.lang, 8.6, bold=True,
             ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])
    add_rich(par, payload["text"][doc.lang], doc.lang, 8.6,
             ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])


def ikeywords(doc, payload):
    par = doc.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_after = Pt(12)
    par.paragraph_format.left_indent = Cm(0.4)
    par.paragraph_format.right_indent = Cm(0.4)
    add_rich(par, payload["label"][doc.lang], doc.lang, 8.6, bold=True, italic=True,
             ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])
    add_rich(par, payload["text"][doc.lang], doc.lang, 8.6, italic=True,
             ascii_font="Times New Roman", ea_font=HEAD_FONT["zh"])


def itodo(doc, lines):
    for line in lines:
        par = doc.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(1)
        par.paragraph_format.left_indent = Cm(0.3)
        add_rich(par, "`" + line + "`", doc.lang, 7.4)


def build_internal(lang):
    d = Doc(lang, font_size=10.5, margin_cm=2.1,
            footer_left=("MLFlu — internal technical report" if lang == "en"
                         else "MIFlu 内部技术报告"))
    meta = text_internal.META_EN if lang == "en" else text_internal.META_ZH
    d.title("Reproducing MIFlu and Benchmarking Influenza Forecasting" if lang == "en"
            else "复现 MIFlu 并基准评估流感预测",
            sub=("Internal technical report — reproduction, 16-arm benchmark, peak skill, and 11 frozen LLM encoders"
                 if lang == "en" else
                 "内部技术报告——复现、16 模型基准、峰值技巧与 11 个冻结 LLM 编码器"),
            kicker=("FINAL-YEAR PROJECT · CITY UNIVERSITY OF HONG KONG · DEPARTMENT OF ELECTRICAL ENGINEERING"
                    if lang == "en" else "毕业设计 · 香港城市大学 · 电子工程学系"))
    d.kv(meta)
    d.p("")
    d.h(2, "Contents" if lang == "en" else "目录")
    items = text_internal.CONTENTS_EN if lang == "en" else text_internal.CONTENTS_ZH
    d.plain_list(items)
    d.page_break()
    render(d, text_internal.blocks())
    path = os.path.join(OUT, f"report_internal_{lang}.docx")
    d.save(path)
    return path


def build_progress(lang):
    d = Doc(lang, font_size=10.5, margin_cm=2.2,
            footer_left=("FYP progress report" if lang == "en" else "FYP 进度报告"))
    head = ("CITY UNIVERSITY OF HONG KONG" if lang == "en" else "香港城市大学")
    dept = ("Department of Electrical Engineering" if lang == "en" else "电子工程学系")
    d.title(head + " — " + ("Progress Report" if lang == "en" else "进度报告"),
            sub=dept + ("   ·   FYP Progress Report, Semester A 2026/27"
                        if lang == "en" else "   ·   毕业设计进度报告，2026/27 学年 A 学期"),
            kicker=("SUBMISSION: FYP InfoNet, by 11:59 pm 20 November 2026"
                    if lang == "en" else "提交：FYP InfoNet，2026 年 11 月 20 日 23:59 前"))
    d.kv([("Project title" if lang == "en" else "项目题目",
           text_progress.TITLE_EN if lang == "en" else text_progress.TITLE_ZH),
          ("Report date" if lang == "en" else "报告日期",
           "2 November 2026" if lang == "en" else "2026 年 11 月 2 日")])
    render(d, text_progress.blocks(lang))
    path = os.path.join(OUT, f"progress_report_{lang}.docx")
    d.save(path)
    return path


def build_ieee(lang):
    d = Doc(lang, font_size=9.0, margin_cm=1.6, serif=True, footer_left="",
            h_sizes=[12, 9.8, 9.4, 9.0])
    render(d, text_ieee.blocks(lang))
    path = os.path.join(OUT, f"ieee_manuscript_{lang}.docx")
    d.save(path)
    return path


def main():
    made = []
    for fn in (build_internal, build_progress, build_ieee):
        for lang in ("en", "zh"):
            p = fn(lang)
            made.append(p)
            print(f"{os.path.getsize(p):>9,}  {os.path.basename(p)}")
    return made


if __name__ == "__main__":
    main()
