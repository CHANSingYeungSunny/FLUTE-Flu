# -*- coding: utf-8 -*-
"""DOCX rendering kit: styles, bilingual block renderer, tables, figures, footer.

All text is UTF-8; every CJK run gets an explicit w:eastAsia font, because a
latin font name alone does not establish glyph availability (see the office-docx
skill).  No document text is produced here -- content lives in dlv/text_*.py.
"""
from __future__ import annotations

import json
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import data as D

FIGDIR = D.FIG
CAPTIONS = json.load(open(os.path.join(FIGDIR, "figure_captions.json"), encoding="utf-8"))

BODY_FONT = {"en": "Calibri", "zh": "SimSun"}
HEAD_FONT = {"en": "Calibri", "zh": "Microsoft YaHei"}
MONO_FONT = "Consolas"

INK = RGBColor(0x1F, 0x2A, 0x37)
ACCENT = RGBColor(0x1F, 0x3B, 0x63)
MUTED = RGBColor(0x5A, 0x63, 0x70)


# --------------------------------------------------------------------- helpers
def _set_run_font(run, ascii_font, ea_font, size=None, bold=None, italic=None,
                  color=None, mono=False):
    run.font.name = MONO_FONT if mono else ascii_font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), MONO_FONT if mono else ascii_font)
    rfonts.set(qn("w:hAnsi"), MONO_FONT if mono else ascii_font)
    rfonts.set(qn("w:eastAsia"), ea_font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


_CLOSERS = set(" \t,.;:)]}\u2019\"'")


def _is_cjk(ch):
    if not ch:
        return False
    o = ord(ch)
    return (0x3000 <= o <= 0x303F or 0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF
            or 0xFF00 <= o <= 0xFF65)


def _tokens(text):
    """Split into ('plain'|'bold'|'code'|'italic', text) pieces.

    A single asterisk is only an *italic* delimiter when it opens after
    whitespace, a CJK character, or the start of the text, and closes before
    whitespace, punctuation or a CJK character.  That rule keeps every occurrence
    of the window expression `(W//16)*16` untouched, in both languages.
    """
    out, buf, i, n = [], [], 0, len(text)

    def flush():
        if buf:
            out.append(("plain", "".join(buf)))
            buf.clear()

    while i < n:
        if text.startswith("**", i):
            j = text.find("**", i + 2)
            if j > i + 2:
                flush()
                out.append(("bold", text[i + 2:j]))
                i = j + 2
                continue
        if text[i] == "`":
            j = text.find("`", i + 1)
            if j > i + 1:
                flush()
                out.append(("code", text[i + 1:j]))
                i = j + 1
                continue
        if (text[i] == "*" and (i == 0 or text[i - 1].isspace() or _is_cjk(text[i - 1]))
                and i + 1 < n and not text[i + 1].isspace()):
            j = i + 1
            while j < n:
                if text[j] == "*" and not text[j - 1].isspace():
                    nxt = text[j + 1] if j + 1 < n else ""
                    if nxt == "" or nxt in _CLOSERS or _is_cjk(nxt):
                        break
                j += 1
            if j < n and j > i + 1:
                flush()
                out.append(("italic", text[i + 1:j]))
                i = j + 1
                continue
        buf.append(text[i])
        i += 1
    flush()
    return out


def add_rich(par, text, lang, size=10.5, bold=False, italic=False, color=INK,
             ascii_font=None, ea_font=None):
    """Add text with **bold**, `code` and *italic* markup."""
    ascii_font = ascii_font or BODY_FONT["en"]
    ea_font = ea_font or BODY_FONT["zh"]
    for kind, part in _tokens(text):
        if kind == "bold":
            r = par.add_run(part)
            _set_run_font(r, ascii_font, ea_font, size, True, italic, color)
        elif kind == "code":
            r = par.add_run(part)
            _set_run_font(r, MONO_FONT, ea_font, size - 0.5, bold, italic, color, mono=True)
        elif kind == "italic":
            r = par.add_run(part)
            _set_run_font(r, ascii_font, ea_font, size, bold, True, color)
        else:
            r = par.add_run(part)
            _set_run_font(r, ascii_font, ea_font, size, bold, italic, color)
    return par


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_split_row(row):
    """Keep a row's cells on one page (Word breaks rows mid-cell by default)."""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def keep_with_next(par):
    par.paragraph_format.keep_with_next = True


def _footer_field(par, lang):
    def fld(instr):
        r = par.add_run()
        b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin")
        i = OxmlElement("w:instrText"); i.set(qn("xml:space"), "preserve"); i.text = instr
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end")
        r._r.append(b); r._r.append(i); r._r.append(e)
        _set_run_font(r, BODY_FONT["en"], BODY_FONT["zh"], 8, color=MUTED)

    r = par.add_run("Page " if lang == "en" else "第 ")
    _set_run_font(r, BODY_FONT["en"], BODY_FONT["zh"], 8, color=MUTED)
    fld(" PAGE ")
    r = par.add_run(" of " if lang == "en" else " 页，共 ")
    _set_run_font(r, BODY_FONT["en"], BODY_FONT["zh"], 8, color=MUTED)
    fld(" NUMPAGES ")
    if lang == "zh":
        r = par.add_run(" 页")
        _set_run_font(r, BODY_FONT["en"], BODY_FONT["zh"], 8, color=MUTED)


# ------------------------------------------------------------------ document
def _roman(n):
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
            (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


_CAP_NUM = re.compile(r"^(?:Table|表)\s*[0-9]+[a-zA-Z]?\.\s*", re.U)


class Doc:
    def __init__(self, lang, *, font_size=10.5, margin_cm=2.1, serif=False,
                 footer_left="", landscape=False, h_sizes=None, table_roman=False):
        self.lang = lang
        self.table_counter = 0
        self.table_roman = table_roman
        self.doc = Document()
        self.font_size = font_size
        self.accent = ACCENT
        d = self.doc
        sec = d.sections[0]
        if landscape:
            from docx.enum.section import WD_ORIENT
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
        else:
            sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(margin_cm)
        sec.top_margin = Cm(2.0)
        sec.bottom_margin = Cm(1.9)
        self.usable_cm = 21.0 - 2 * margin_cm
        self.margin_cm = margin_cm
        self.top_margin_cm = 2.0
        self.bottom_margin_cm = 1.9

        normal = d.styles["Normal"]
        normal.font.size = Pt(font_size)
        normal.font.name = BODY_FONT["en"]
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT["zh"])
        normal.paragraph_format.space_after = Pt(5)
        normal.paragraph_format.line_spacing = 1.14
        sizes = h_sizes or [17, 13, 11.5, 10.5]
        self.h_sizes = sizes
        for i, (sz, col) in enumerate([(sizes[0], ACCENT), (sizes[1], ACCENT),
                                       (sizes[2], INK), (sizes[3], INK)], start=1):
            st = d.styles[f"Heading {i}"]
            st.font.size = Pt(sz)
            st.font.bold = True
            st.font.color.rgb = col
            st.font.name = HEAD_FONT["en"]
            st.element.rPr.rFonts.set(qn("w:eastAsia"), HEAD_FONT["zh"])
            st.paragraph_format.space_before = Pt(12 if i <= 2 else 9)
            st.paragraph_format.space_after = Pt(4)
            st.paragraph_format.keep_with_next = True

        # footer
        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if footer_left:
            r = fp.add_run(footer_left + "   ·   ")
            _set_run_font(r, BODY_FONT["en"], BODY_FONT["zh"], 8, color=MUTED)
        _footer_field(fp, lang)

    # ---------------------------------------------------------------- pieces
    def title(self, text, sub=None, kicker=None):
        if kicker:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            add_rich(p, kicker, self.lang, 9, bold=True, color=MUTED,
                     ascii_font=HEAD_FONT["en"], ea_font=HEAD_FONT["zh"])
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.space_before = Pt(2)
        add_rich(p, text, self.lang, 22, bold=True, color=ACCENT,
                 ascii_font=HEAD_FONT["en"], ea_font=HEAD_FONT["zh"])
        if sub:
            p2 = self.doc.add_paragraph()
            p2.paragraph_format.space_after = Pt(10)
            add_rich(p2, sub, self.lang, 11.5, italic=True, color=MUTED)

    def h(self, level, text):
        p = self.doc.add_heading(level=level)
        add_rich(p, text, self.lang, self.h_sizes[level - 1],
                 bold=True, color=self.accent if level <= 2 else INK,
                 ascii_font=HEAD_FONT["en"], ea_font=HEAD_FONT["zh"])
        return p

    def p(self, text, size=None, italic=False, color=INK, align=None, space_after=None, bold=False):
        par = self.doc.add_paragraph()
        if align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if space_after is not None:
            par.paragraph_format.space_after = Pt(space_after)
        add_rich(par, text, self.lang, size or self.font_size, italic=italic, bold=bold, color=color)
        return par

    def bullets(self, items, numbered=False, size=None):
        for i, it in enumerate(items, 1):
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Cm(0.65)
            par.paragraph_format.first_line_indent = Cm(-0.45)
            par.paragraph_format.space_after = Pt(3)
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            mark = f"{i}. " if numbered else "•  "
            add_rich(par, mark + it, self.lang, size or self.font_size)

    def plain_list(self, items, size=9.6):
        for it in items:
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Cm(0.9)
            par.paragraph_format.space_after = Pt(1.5)
            add_rich(par, it, self.lang, size)

    def quote(self, text):
        par = self.doc.add_paragraph()
        par.paragraph_format.left_indent = Cm(0.7)
        par.paragraph_format.right_indent = Cm(0.7)
        par.paragraph_format.space_before = Pt(4)
        par.paragraph_format.space_after = Pt(7)
        add_rich(par, text, self.lang, self.font_size - 0.5, italic=True, color=MUTED)
        pPr = par._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        left = OxmlElement("w:left")
        left.set(qn("w:val"), "single"); left.set(qn("w:sz"), "18")
        left.set(qn("w:space"), "8"); left.set(qn("w:color"), "8FA6C4")
        bdr.append(left)
        pPr.append(bdr)

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def set_columns(self, n, space=300):
        """Insert a continuous section break and give the following section n columns."""
        sec = self.doc.add_section(WD_SECTION.CONTINUOUS)
        sec.left_margin = sec.right_margin = Cm(self.margin_cm)
        sec.top_margin = Cm(self.top_margin_cm)
        sec.bottom_margin = Cm(self.bottom_margin_cm)
        sectPr = sec._sectPr
        cols = sectPr.find(qn("w:cols"))
        if cols is None:
            cols = OxmlElement("w:cols")
            sectPr.append(cols)
        cols.set(qn("w:num"), str(n))
        cols.set(qn("w:space"), str(space))
        cols.set(qn("w:equalWidth"), "1")
        self._ncols = n
        self.usable_cm = (21.0 - 2 * self.margin_cm - (0.35 if n == 2 else 0)) / (2 if n == 2 else 1)
        # footer must keep following the same layout
        sec.footer.is_linked_to_previous = True
        return sec

    def kv(self, pairs, widths=(4.2, 12.2), fs=8.5):
        t = self.doc.add_table(rows=0, cols=2)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for k, v in pairs:
            row = t.add_row()
            for cell, txt, bold in ((row.cells[0], k, True), (row.cells[1], v, False)):
                cell.width = Cm(widths[0] if bold else widths[1])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                par = cell.paragraphs[0]
                par.paragraph_format.space_after = Pt(1)
                add_rich(par, txt, self.lang, fs, bold=bold)
            shade(row.cells[0], "EEF2F8")
        return t

    # ---------------------------------------------------------------- table
    def table(self, t, number_label=None):
        self.table_counter += 1
        cap = t["caption"][self.lang]
        # Captions may carry a stale hand-written number; the document numbers its
        # own tables, so the number is stripped and re-applied here.
        cap = _CAP_NUM.sub("", cap)
        if number_label is None:
            n = self.table_counter
            if self.lang == "zh":
                number_label = f"表 {n}"
            elif self.table_roman:
                number_label = f"TABLE {_roman(n)}"
            else:
                number_label = f"Table {n}"
        cap = f"{number_label}. {cap}"
        note = t["note"][self.lang]
        cols = t["cols"]
        rows = t["rows"]
        fs = t.get("fs", 8)
        widths = t.get("widths")
        if widths and abs(sum(widths) - self.usable_cm) > 0.6:
            k = self.usable_cm / sum(widths)
            widths = [w * k for w in widths]

        cp = self.doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(8)
        cp.paragraph_format.space_after = Pt(3)
        keep_with_next(cp)
        add_rich(cp, cap, self.lang, 8.6, bold=True, color=ACCENT,
                 ascii_font=HEAD_FONT["en"], ea_font=HEAD_FONT["zh"])

        tb = self.doc.add_table(rows=1, cols=len(cols))
        tb.style = "Table Grid"
        tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tb.autofit = False
        if widths:
            # LibreOffice lays a fixed table out from w:tblGrid, not from the
            # individual w:tcW cells, so the grid must carry the widths too.
            for j, w in enumerate(widths):
                tb.columns[j].width = Cm(w)

        hdr = tb.rows[0]
        repeat_header(hdr)
        no_split_row(hdr)
        for j, c in enumerate(cols):
            cell = hdr.cells[j]
            if widths:
                cell.width = Cm(widths[j])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            par = cell.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.space_before = Pt(1)
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_rich(par, c[self.lang] if isinstance(c, dict) else c, self.lang, fs,
                     bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                     ascii_font=HEAD_FONT["en"], ea_font=HEAD_FONT["zh"])
            shade(cell, "1F3B63")

        for i, row in enumerate(rows):
            tr = tb.add_row()
            no_split_row(tr)
            for j, val in enumerate(row):
                cell = tr.cells[j]
                if widths:
                    cell.width = Cm(widths[j])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                par = cell.paragraphs[0]
                par.paragraph_format.space_after = Pt(0.5)
                par.paragraph_format.space_before = Pt(0.5)
                par.alignment = (WD_ALIGN_PARAGRAPH.LEFT if j == 0
                                 else WD_ALIGN_PARAGRAPH.CENTER)
                txt = val[self.lang] if isinstance(val, dict) else val
                add_rich(par, txt, self.lang, fs)
            if i % 2 == 1:
                for cell in tr.cells:
                    shade(cell, "F4F7FB")

        np_ = self.doc.add_paragraph()
        np_.paragraph_format.space_before = Pt(3)
        np_.paragraph_format.space_after = Pt(10)
        np_.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_rich(np_, note, self.lang, 7.6, italic=True, color=MUTED)

    # --------------------------------------------------------------- figure
    def figure(self, fname, caption=None, width_cm=None, note=None):
        path = os.path.join(FIGDIR, fname)
        assert os.path.exists(path), path
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(8)
        par.paragraph_format.space_after = Pt(3)
        keep_with_next(par)
        par.add_run().add_picture(path, width=Cm(width_cm or self.usable_cm))
        if caption is None:
            hit = [c for c in CAPTIONS if c["file"] == fname]
            caption = hit[0][f"caption_{self.lang}"] if hit else fname
        cp = self.doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        cp.paragraph_format.space_after = Pt(10)
        add_rich(cp, caption, self.lang, 8.0, italic=True, color=MUTED)

    def save(self, path):
        self.doc.core_properties.title = os.path.basename(path)
        self.doc.core_properties.author = "CHAN Sing Yeung"
        self.doc.core_properties.comments = "Generated from measured artefacts; see MANIFEST.md"
        self.doc.save(path)
        return path
