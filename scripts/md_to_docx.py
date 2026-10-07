#!/usr/bin/env python
"""
md_to_docx.py — render a Markdown source into a .docx using ONLY the stdlib.
============================================================================

WHY THIS EXISTS
---------------
The advisor requires the Word (.docx) and Markdown (.md) versions of the
Q&A report to be byte-for-byte identical in CONTENT. On this machine neither
`pandoc`, `python-docx` nor the `docx` npm package is installed, so there is
no off-the-shelf converter. Generating BOTH artefacts from a SINGLE Markdown
source is the only way to guarantee they cannot drift apart.

Supported Markdown (exactly the subset the report actually uses):
    # / ## / ### headings
    paragraphs with **bold**, *italic*, `code`, [text](url)
    - bullet lists     1. numbered lists
    > blockquotes (which may themselves contain - bullets)
    ``` fenced code
    --- horizontal rule
    ![alt](path) images (embedded)
    | pipe | tables |

Usage:
    python scripts/md_to_docx.py <input.md> <output.docx>
"""

from __future__ import annotations

import os
import re
import struct
import sys
import zipfile
import xml.sax.saxutils as sx

EMU_PER_INCH = 914400
CONTENT_WIDTH_EMU = 5943600          # 6.5in of text on US Letter w/ 1in margins

# bold | italic | code | link
INLINE_RE = re.compile(
    r"\*\*(.+?)\*\*"          # 1 bold
    r"|\*([^*]+)\*"           # 2 italic
    r"|`([^`]+)`"             # 3 code
    r"|\[(.+?)\]\((.+?)\)"    # 4,5 link
)


def esc(t: str) -> str:
    return sx.escape(t, {'"': "&quot;", "'": "&apos;"})


def png_size(path: str) -> tuple:
    """Read (width, height) straight from the PNG IHDR chunk."""
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    w = struct.unpack(">I", head[16:20])[0]
    h = struct.unpack(">I", head[20:24])[0]
    return int(w), int(h)


# --------------------------------------------------------------------------- #
# Relationships / hyperlinks
# --------------------------------------------------------------------------- #
class RelBag:
    def __init__(self):
        self.items = []          # (rId, type, target, mode)

    def add(self, rel_type: str, target: str, mode: str = "") -> str:
        rid = f"rId{len(self.items) + 1}"
        self.items.append((rid, rel_type, target, mode))
        return rid

    def xml(self) -> str:
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<Relationships xmlns="http://schemas.openxmlformats.org/'
               'package/2006/relationships">']
        for rid, rtype, target, mode in self.items:
            m = ' TargetMode="External"' if mode == "External" else ""
            out.append(f'<Relationship Id="{rid}" '
                       f'Type="{rtype}" Target="{esc(target)}"{m}/>')
        out.append("</Relationships>")
        return "".join(out)


# --------------------------------------------------------------------------- #
# Inline runs
# --------------------------------------------------------------------------- #
def run_xml(text: str, bold=False, italic=False, mono=False) -> str:
    if not text:
        return ""
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if mono:
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return (f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>')


HYPERLINK_TYPE = ("http://schemas.openxmlformats.org/officeDocument/2006/"
                  "relationships/hyperlink")
URL_RE = re.compile(r"(https?://[^\s，。）)、；;\"']+)")


def hyperlink_run(text: str, rid: str) -> str:
    return (f'<w:hyperlink r:id="{rid}">'
            f'<w:r><w:rPr><w:color w:val="0563C1"/>'
            f'<w:u w:val="single"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'
            f"</w:hyperlink>")


def plain_runs(text: str, rels: RelBag) -> str:
    """Emit plain text, turning any bare URL into a clickable hyperlink."""
    out, pos = [], 0
    for m in URL_RE.finditer(text):
        if m.start() > pos:
            out.append(run_xml(text[pos:m.start()]))
        url = m.group(1)
        out.append(hyperlink_run(url, rels.add(HYPERLINK_TYPE, url, "External")))
        pos = m.end()
    if pos < len(text):
        out.append(run_xml(text[pos:]))
    return "".join(out)


def unescape_md(s: str) -> str:
    """Resolve backslash escapes so they do not leak into the Word output."""
    return s.replace("\\*", "*").replace("\\_", "_")


def inline_runs(text: str, rels: RelBag) -> str:
    text = unescape_md(text)
    out = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            out.append(plain_runs(text[pos:m.start()], rels))
        if m.group(1) is not None:
            out.append(run_xml(m.group(1), bold=True))
        elif m.group(2) is not None:
            out.append(run_xml(m.group(2), italic=True))
        elif m.group(3) is not None:
            out.append(run_xml(m.group(3), mono=True))
        else:
            out.append(hyperlink_run(m.group(4),
                                     rels.add(HYPERLINK_TYPE, m.group(5),
                                              "External")))
        pos = m.end()
    if pos < len(text):
        out.append(plain_runs(text[pos:], rels))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Block parser
# --------------------------------------------------------------------------- #
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
IMG_RE = re.compile(r"^!\[(.*?)\]\((.*?)\)$")
BULLET_RE = re.compile(r"^[-*+]\s+(.*)$")
NUM_RE = re.compile(r"^\d+\.\s+(.*)$")
TBLSEP_RE = re.compile(r"^\|[\s:\-|]+\|$")


def _is_block_start(s: str) -> bool:
    return (not s or s.startswith("|") or s.startswith("#") or s.startswith(">")
            or s.startswith("```") or bool(BULLET_RE.match(s))
            or bool(NUM_RE.match(s)) or bool(HR_RE.match(s))
            or bool(IMG_RE.match(s)))


def parse_blocks(md: str):
    lines = md.split("\n")
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", code))
            continue
        if HR_RE.match(s):
            blocks.append(("hr", None))
            i += 1
            continue
        m = IMG_RE.match(s)
        if m:
            blocks.append(("image", (m.group(1), m.group(2))))
            i += 1
            continue
        m = HEAD_RE.match(s)
        if m:
            blocks.append(("heading", (len(m.group(1)), m.group(2).strip())))
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and TBLSEP_RE.match(lines[i + 1].strip()):
            header = split_row(s)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", (header, rows)))
            continue
        if s.startswith(">"):
            items = []
            while i < n and lines[i].strip().startswith(">"):
                inner = lines[i].strip().lstrip(">").strip()
                if BULLET_RE.match(inner):
                    items.append(("bullet", BULLET_RE.match(inner).group(1)))
                elif inner:
                    items.append(("text", inner))
                i += 1
            blocks.append(("quote", items))
            continue
        if BULLET_RE.match(s):
            items = []
            while i < n and BULLET_RE.match(lines[i].strip()):
                items.append(BULLET_RE.match(lines[i].strip()).group(1))
                i += 1
            blocks.append(("bullets", items))
            continue
        if NUM_RE.match(s):
            items = []
            while i < n and NUM_RE.match(lines[i].strip()):
                items.append(NUM_RE.match(lines[i].strip()).group(1))
                i += 1
            blocks.append(("numbers", items))
            continue
        para = []
        while i < n:
            cur = lines[i].strip()
            if _is_block_start(cur):
                break
            para.append(cur)
            i += 1
        if para:
            blocks.append(("para", " ".join(para)))
        else:
            i += 1
    return blocks


# --------------------------------------------------------------------------- #
# OOXML emitters
# --------------------------------------------------------------------------- #
def p(children: str, style: str = "", extra_ppr: str = "") -> str:
    """One paragraph. `w:pStyle` must come first inside `w:pPr`."""
    inner = ""
    if style:
        inner += f'<w:pStyle w:val="{style}"/>'
    inner += extra_ppr
    ppr = f"<w:pPr>{inner}</w:pPr>" if inner else ""
    return f"<w:p>{ppr}{children}</w:p>"


def split_row(line: str) -> list:
    """Split a markdown table row on UNESCAPED pipes only.

    `\\|` is a literal pipe inside a cell (e.g. `max \\|x\\|`); splitting on
    every pipe would both corrupt the cell text and shift every later column,
    silently dropping values from the rendered table.
    """
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", body)]


def emit_table(header, rows, rels: RelBag) -> str:
    ncols = len(header)
    grid = "".join(f'<w:gridCol w:w="{int(9360 / max(ncols, 1))}"/>' for _ in range(ncols))
    borders = ("<w:tblBorders>"
               + "".join(f'<w:{e} w:val="single" w:sz="4" w:space="0" '
                         f'w:color="AAAAAA"/>'
                         for e in ("top", "left", "bottom", "right",
                                   "insideH", "insideV"))
               + "</w:tblBorders>")

    cw = int(9360 / max(ncols, 1))

    def cell(text, is_header):
        shd = ('<w:shd w:val="clear" w:color="auto" w:fill="E8EEF7"/>'
               if is_header else "")
        # Render inline Markdown (bold / code / links) instead of dumping the
        # raw cell text, otherwise **...** and `...` leak into Word verbatim.
        runs = inline_runs(text, rels) or run_xml("")
        return (f'<w:tc><w:tcPr><w:tcW w:w="{cw}" w:type="dxa"/>{shd}'
                f'</w:tcPr><w:p>{runs}</w:p></w:tc>')

    body = ""
    hdr = "".join(cell(h, True) for h in header)
    body += (f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{hdr}</w:tr>')
    for r in rows:
        r = list(r) + [""] * (ncols - len(r))
        body += "<w:tr>" + "".join(cell(c, False) for c in r[:ncols]) + "</w:tr>"
    return (f'<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/>{borders}'
            f'<w:tblCellMar>'
            f'<w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
            f'<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/>'
            f'</w:tblCellMar></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>')


def emit_image(alt: str, path: str, project_root: str, rels: RelBag, media: list) -> str:
    full = path if os.path.isabs(path) else os.path.join(project_root, path)
    if not os.path.exists(full):
        # Never silently degrade: a missing figure would make the .docx and
        # the .md diverge, which is exactly what this converter exists to prevent.
        raise FileNotFoundError(
            f"figure referenced in the Markdown is missing: {path!r} "
            f"(resolved to {full!r})")
    w, h = png_size(full)
    cx = CONTENT_WIDTH_EMU
    cy = int(cx * h / w)
    if cy > 8000000:                      # keep very tall figures on the page
        cy = 8000000
        cx = int(cy * w / h)
    idx = len(media) + 1
    name = f"image{idx}.png"
    media.append((f"word/media/{name}", full))
    rid = rels.add("http://schemas.openxmlformats.org/officeDocument/2006/"
                   "relationships/image", f"media/{name}")
    return (
        f'<w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{idx}" name="Picture {idx}" descr="{esc(alt)}"/>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{idx}" name="{esc(alt)}" descr="{esc(alt)}"/>'
        f'<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch>'
        f'</pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def build_document_xml(md: str, project_root: str):
    rels = RelBag()
    media: list = []
    body = []

    for kind, payload in parse_blocks(md):
        if kind == "heading":
            lvl, text = payload
            lvl = min(lvl, 4)
            body.append(p(inline_runs(text, rels), style=f"Heading{lvl}"))
        elif kind == "para":
            body.append(p(inline_runs(payload, rels)))
        elif kind == "bullets":
            for it in payload:
                body.append(p(inline_runs(it, rels), extra_ppr=
                            '<w:numPr><w:ilvl w:val="0"/>'
                            '<w:numId w:val="1"/></w:numPr>'
                            '<w:ind w:left="720" w:hanging="360"/>'))
        elif kind == "numbers":
            for it in payload:
                body.append(p(inline_runs(it, rels), extra_ppr=
                            '<w:numPr><w:ilvl w:val="0"/>'
                            '<w:numId w:val="2"/></w:numPr>'
                            '<w:ind w:left="720" w:hanging="360"/>'))
        elif kind == "quote":
            for sub_kind, text in payload:
                indent = ('<w:ind w:left="720"/>'
                          if sub_kind == "bullet" else '<w:ind w:left="360"/>')
                body.append(p(inline_runs(text, rels), style="Quote",
                             extra_ppr=indent))
        elif kind == "code":
            for line in payload:
                body.append(p(run_xml(line, mono=True), extra_ppr=
                             '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
                             '<w:ind w:left="360"/>'))
        elif kind == "table":
            body.append(emit_table(payload[0], payload[1], rels))
            body.append(p(""))
        elif kind == "image":
            body.append(emit_image(payload[0], payload[1], project_root, rels, media))
        elif kind == "hr":
            body.append(p("", extra_ppr='<w:pBdr><w:bottom w:val="single" '
                                        'w:sz="6" w:space="1" w:color="BBBBBB"/>'
                                        '</w:pBdr>'))

    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<w:body>" + "".join(body) +
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>")
    return doc, rels, media


STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/'
    'wordprocessingml/2006/main">'
    "<w:docDefaults><w:rPrDefault><w:rPr>"
    '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="SimSun"/>'
    '<w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:outlineLvl w:val="0"/><w:spacing w:before="240" w:after="180"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="1F3864"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:outlineLvl w:val="1"/><w:spacing w:before="280" w:after="160"/>'
    '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="8EAADB"/></w:pBdr></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="2E5496"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:outlineLvl w:val="2"/><w:spacing w:before="220" w:after="120"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="2E5496"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading4">'
    '<w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:outlineLvl w:val="3"/><w:spacing w:before="180" w:after="100"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Quote">'
    '<w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="C00000"/></w:pBdr>'
    '<w:shd w:val="clear" w:color="auto" w:fill="FDF2F2"/>'
    '<w:spacing w:after="120"/></w:pPr>'
    '<w:rPr><w:color w:val="7F0000"/></w:rPr></w:style>'
    "</w:styles>")

NUMBERING = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:numbering xmlns:w="http://schemas.openxmlformats.org/'
    'wordprocessingml/2006/main">'
    '<w:abstractNum w:abstractNumId="0">'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x2022;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
    '<w:abstractNum w:abstractNumId="1">'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
    '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
    '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
    "</w:numbering>")


def convert(md_path: str, docx_path: str) -> None:
    # The report .md sits IN the project root, so image paths in the Markdown
    # are relative to its own directory — one dirname(), not two.
    project_root = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    doc_xml, rels, media = build_document_xml(md, project_root)

    styles_rid = rels.add("http://schemas.openxmlformats.org/officeDocument/"
                          "2006/relationships/styles", "styles.xml")
    numbering_rid = rels.add("http://schemas.openxmlformats.org/officeDocument/"
                             "2006/relationships/numbering", "numbering.xml")

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
        'package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Override PartName="/word/document.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>',
        "</Types>",
    ]

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
        'relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>')

    os.makedirs(os.path.dirname(os.path.abspath(docx_path)), exist_ok=True)
    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", doc_xml)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/numbering.xml", NUMBERING)
        z.writestr("word/_rels/document.xml.rels", rels.xml())
        for arcname, src in media:
            z.write(src, arcname)

    print(f"[md_to_docx] wrote {docx_path}")
    print(f"[md_to_docx] embedded {len(media)} image(s), "
          f"{sum(1 for _, t, _, m in rels.items if m == 'External')} hyperlink(s)")


def find_report() -> str:
    """Locate the advisor Q&A Markdown report in the project root.

    Auto-discovery exists because passing a CJK filename through the Windows
    command line mangles it; letting Python find the file avoids that entirely.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in sorted(os.listdir(root)):
        if name.endswith(".md") and "五大疑问" in name and "回复报告" in name:
            return os.path.join(root, name)
    raise FileNotFoundError("advisor Q&A report .md not found in project root")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        convert(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        md = find_report()
        convert(md, os.path.splitext(md)[0] + ".docx")
    else:
        print("usage: python scripts/md_to_docx.py [input.md output.docx]")
        sys.exit(1)
