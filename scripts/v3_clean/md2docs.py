"""Convert Markdown to .docx and .pdf (Chinese-capable). Usage:
  python md2docs.py input.md --docx OUT.docx --pdf OUT.pdf

Features:
  * headings, paragraphs, blockquotes, hr, ordered/unordered lists, tables
  * inline **bold**, `code`, *italic*
  * image embed:  ![caption](relative/path.png)  (path relative to the .md file)
  * Unicode superscripts (10^-7, p=3.13e-7) rendered as true superscript runs
  * U+2212 minus sign normalized to ASCII hyphen so signs never drop
"""
import html, os, re, sys

INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")
IMG_RE = re.compile(r"^!\[(.*)\]\(([^)]+)\)\s*$")

# Unicode superscript -> ASCII (rendered as true superscript)
SUP_MAP = {
    "\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3",
    "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
    "\u2078": "8", "\u2079": "9", "\u207b": "-", "\u207a": "+",
    "\u207f": "n",
}


def split_sup(text):
    """Normalize U+2212 -> '-' and split into (is_sup, chunk) segments."""
    text = text.replace("\u2212", "-")
    out, buf, cur = [], [], None
    for ch in text:
        is_sup = ch in SUP_MAP
        if cur is not None and is_sup != cur:
            out.append((cur, "".join(buf)))
            buf = []
        cur = is_sup
        buf.append(SUP_MAP[ch] if is_sup else ch)
    if buf:
        out.append((cur, "".join(buf)))
    return out


def parse_inline(text):
    runs = []
    for p in INLINE_RE.split(text):
        if not p:
            continue
        if p.startswith("**") and p.endswith("**") and len(p) >= 4:
            runs.append((p[2:-2], True, False, False))
        elif p.startswith("`") and p.endswith("`") and len(p) >= 2:
            runs.append((p[1:-1], False, True, False))
        elif p.startswith("*") and p.endswith("*") and len(p) >= 4:
            runs.append((p[1:-1], False, False, True))
        else:
            runs.append((p, False, False, False))
    return runs


def to_html(text):
    out = []
    for t, b, c, i in parse_inline(text):
        parts = []
        for is_sup, chunk in split_sup(t):
            chunk = html.escape(chunk)
            if is_sup:
                chunk = "<super>%s</super>" % chunk
            parts.append(chunk)
        t = "".join(parts)
        if c:
            t = '<font face="Courier" size="8">%s</font>' % t
        if b:
            t = "<b>%s</b>" % t
        if i:
            t = "<i>%s</i>" % t
        out.append(t)
    return "".join(out)


def parse_blocks(text):
    lines = text.split("\n")
    blocks, i, n = [], 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        m = IMG_RE.match(s)
        if m:
            blocks.append(("img", m.group(1).strip(), m.group(2).strip()))
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            blocks.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            blocks.append(("hr",))
            i += 1
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(("quote", "\n".join(buf)))
            continue
        if s.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            tbl = [r for r in tbl if not all(re.match(r"^:?-{2,}:?$", c) for c in r)]
            if tbl:
                blocks.append(("table", tbl[0], tbl[1:]))
            continue
        if re.match(r"^(\s*[-*]\s+|\s*\d+[.)]\s+)", s):
            items, ordered = [], None
            while i < n:
                ss = lines[i].strip()
                mb = re.match(r"^\s*[-*]\s+(.*)$", ss)
                mo = re.match(r"^\s*\d+[.)]\s+(.*)$", ss)
                if mb and ordered in (None, False):
                    ordered = False
                    items.append(mb.group(1).strip())
                    i += 1
                elif mo and ordered in (None, True):
                    ordered = True
                    items.append(mo.group(1).strip())
                    i += 1
                else:
                    break
            blocks.append(("list", ordered, items))
            continue
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|\||[-*]\s+|\d+[.)]\s+|>|!\[)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        blocks.append(("para", "\n".join(buf)))
    return blocks


def resolve_img(path, src_dir):
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(src_dir, path))


# ---- DOCX ----
def render_docx(blocks, out, src_dir):
    from docx import Document
    from docx.shared import Pt, Mm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.top_margin = sec.bottom_margin = Mm(20)
    sec.left_margin = sec.right_margin = Mm(20)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    def add_runs(p, t, bold=False, code=False, italic=False, size=11):
        for is_sup, chunk in split_sup(t):
            r = p.add_run(chunk)
            r.bold = bold or code
            r.italic = italic
            r.font.size = Pt(size)
            if is_sup:
                r.font.superscript = True
            rpr = r._element.get_or_add_rPr()
            rf = rpr.get_or_add_rFonts()
            if code:
                rf.set(qn("w:ascii"), "Consolas")
                rf.set(qn("w:hAnsi"), "Consolas")
            else:
                rf.set(qn("w:ascii"), "Calibri")
                rf.set(qn("w:hAnsi"), "Calibri")
                rf.set(qn("w:eastAsia"), "SimHei" if bold else "SimSun")

    def para(text, size=11, before=0, after=6, indent=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        if indent:
            p.paragraph_format.left_indent = Mm(indent)
        for si, seg in enumerate(text.split("\n")):
            if si:
                p.add_run().add_break()
            for t, b, c, i in parse_inline(seg):
                add_runs(p, t, b, c, i, size)
        return p

    SZ = {1: 18, 2: 15, 3: 13, 4: 12}
    for b in blocks:
        if b[0] == "h":
            para(b[2], size=SZ[b[1]], before=14 if b[1] <= 2 else 10, after=6)
        elif b[0] == "para":
            para(b[1])
        elif b[0] == "img":
            path = resolve_img(b[2], src_dir)
            if not os.path.exists(path):
                print("WARNING: image not found:", path)
            else:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.keep_with_next = True
                p.add_run().add_picture(path, width=Mm(150))
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.paragraph_format.space_after = Pt(10)
                cap.paragraph_format.keep_with_next = True
                for t, bd, c, i in parse_inline(b[1]):
                    add_runs(cap, t, bd, c, i, size=9)
                    for r in cap.runs:
                        r.italic = True
                        r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        elif b[0] == "quote":
            p = para(b[1], size=10.5, indent=8)
            for r in p.runs:
                r.italic = True
                r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
        elif b[0] == "hr":
            p = doc.add_paragraph()
            ppr = p._p.get_or_add_pPr()
            pb = OxmlElement("w:pBdr")
            bt = OxmlElement("w:bottom")
            bt.set(qn("w:val"), "single")
            bt.set(qn("w:sz"), "6")
            bt.set(qn("w:color"), "999999")
            pb.append(bt)
            ppr.append(pb)
        elif b[0] == "list":
            ordered, items = b[1], b[2]
            for k, item in enumerate(items, 1):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Mm(10)
                p.paragraph_format.space_after = Pt(2)
                add_runs(p, ("%d. " % k) if ordered else "\u2022 ", False, False, False, 11)
                for si, seg in enumerate(item.split("\n")):
                    if si:
                        p.add_run().add_break()
                    for t, bold, code, i in parse_inline(seg):
                        add_runs(p, t, bold, code, i, 11)
        elif b[0] == "table":
            hdr, rows = b[1], b[2]
            tb = doc.add_table(rows=1 + len(rows), cols=len(hdr))
            tb.style = "Table Grid"
            for j, h in enumerate(hdr):
                c = tb.cell(0, j)
                add_runs(c.paragraphs[0], h, True, False, False, 10.5)
                tc = c._tc.get_or_add_tcPr()
                sh = OxmlElement("w:shd")
                sh.set(qn("w:val"), "clear")
                sh.set(qn("w:fill"), "D5E8F0")
                tc.append(sh)
            for ri, row in enumerate(rows):
                for j in range(len(hdr)):
                    cell = tb.cell(ri + 1, j)
                    for t, bold, code, i in parse_inline(row[j] if j < len(row) else ""):
                        add_runs(cell.paragraphs[0], t, bold, code, i, 10.5)
            doc.add_paragraph()
    doc.save(out)


# ---- PDF ----
def render_pdf(blocks, out, src_dir):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, HRFlowable, Image, KeepTogether)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    font = "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont("SimSun", "C:/Windows/Fonts/simsun.ttc", subfontIndex=0))
        pdfmetrics.registerFont(TTFont("SimHei", "C:/Windows/Fonts/simhei.ttf"))
        pdfmetrics.registerFontFamily("SimSun", normal="SimSun", bold="SimHei", italic="SimSun", boldItalic="SimHei")
        font = "SimSun"
    except Exception:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font = "STSong-Light"

    S = {
        "h1": ParagraphStyle("h1", fontName=font, fontSize=17, leading=22, spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName=font, fontSize=14, leading=18, spaceBefore=10, spaceAfter=5),
        "h3": ParagraphStyle("h3", fontName=font, fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=4),
        "h4": ParagraphStyle("h4", fontName=font, fontSize=11.5, leading=15, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName=font, fontSize=10.5, leading=15, spaceAfter=5),
        "quote": ParagraphStyle("quote", fontName=font, fontSize=9.5, leading=14, leftIndent=18, textColor=colors.HexColor("#444444"), spaceAfter=5),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=9, leading=12),
        "cellh": ParagraphStyle("cellh", fontName=font, fontSize=9, leading=12),
        "cap": ParagraphStyle("cap", fontName=font, fontSize=8.5, leading=11, alignment=1,
                              textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=10),
    }

    def to_para(text, style):
        body = text.replace("\n", "<br/>")
        return Paragraph(to_html(body), style)

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    story = []
    for b in blocks:
        if b[0] == "h":
            story.append(Paragraph(to_html(b[2]), S["h%d" % min(b[1], 4)]))
        elif b[0] == "para":
            story.append(to_para(b[1], S["body"]))
        elif b[0] == "img":
            path = resolve_img(b[2], src_dir)
            if not os.path.exists(path):
                print("WARNING: image not found:", path)
            else:
                img = Image(path)
                img.drawWidth = 150 * mm
                img.drawHeight = 150 * mm * img.imageHeight / img.imageWidth
                cap = Paragraph(to_html(b[1]), S["cap"])
                story.append(KeepTogether([img, cap]))
        elif b[0] == "quote":
            story.append(to_para(b[1], S["quote"]))
        elif b[0] == "hr":
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#999999"), spaceAfter=6))
        elif b[0] == "list":
            ordered, items = b[1], b[2]
            for k, item in enumerate(items, 1):
                mark = ("%d. " % k) if ordered else "\u2022 "
                story.append(Paragraph(to_html(mark + item), ParagraphStyle("li", parent=S["body"], leftIndent=18, firstLineIndent=-12, spaceAfter=2)))
        elif b[0] == "table":
            hdr, rows = b[1], b[2]
            data = [[Paragraph(to_html(h), S["cellh"]) for h in hdr]]
            for r in rows:
                data.append([Paragraph(to_html(r[j] if j < len(r) else ""), S["cell"]) for j in range(len(hdr))])
            t = Table(data, colWidths=[(doc.width / len(hdr))] * len(hdr), repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D5E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
    doc.build(story)


def main():
    args = sys.argv[1:]
    src = args[0]
    out_docx = None
    out_pdf = None
    for k in range(1, len(args)):
        if args[k] == "--docx" and k + 1 < len(args):
            out_docx = args[k + 1]
        if args[k] == "--pdf" and k + 1 < len(args):
            out_pdf = args[k + 1]
    base = os.path.splitext(src)[0]
    if out_docx is None:
        out_docx = base + ".docx"
    if out_pdf is None:
        out_pdf = base + ".pdf"
    src_dir = os.path.dirname(os.path.abspath(src))
    with open(src, "r", encoding="utf-8") as f:
        text = f.read()
    blocks = parse_blocks(text)
    render_docx(blocks, out_docx, src_dir)
    print("docx:", out_docx)
    render_pdf(blocks, out_pdf, src_dir)
    print("pdf:", out_pdf)


if __name__ == "__main__":
    main()
