# -*- coding: utf-8 -*-
"""Extract the authoritative DOCX report into a Markdown mirror + verify key numbers.

Why not pandoc: unavailable in this environment; python-docx 1.2.0 is the fallback and also
lets us run consistency checks (forbidden phrases must not appear, key numbers must appear).

Usage:
    python scripts/extract_docx_to_md.py
    python scripts/extract_docx_to_md.py --docx <in.docx> --out <out.md>
"""
from __future__ import annotations

import argparse
import os
import re
import sys

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOCX = os.path.join(
    BASE, "reports", "concise_final",
    "MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx")
DEFAULT_OUT = os.path.join(BASE, "reports", "concise_final", "REPORT_精简终版.md")

# figure files live beside the benchmark evidence; paths are relative to the output .md
FIG_DIR_REL = os.path.join("..", "..", "results", "v3_clean", "analysis",
                           "peak_criteria", "report_figures")
FIG_BY_NUM = {
    1: "fig1_ranking.png", 2: "fig2_r1c.png", 3: "fig3_ptepie.png",
    4: "fig4_group.png", 5: "fig5_miflu.png", 6: "fig6_covid.png",
}

# consistency gates
MUST_CONTAIN = ["1.8652", "1.4355", "+29.9%", "PARTIAL_REPRODUCTION", "36/36", "15/36"]
MUST_NOT_CONTAIN = ["自定义", r"\bC0\b", r"\bC1\b"]


def iter_block_items(doc: Document):
    """Yield (kind, obj) in true document order (paragraphs and tables interleaved)."""
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield "p", Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield "tbl", Table(child, doc)


def para_text(p: Paragraph) -> str:
    return p.text.strip()


def has_drawing(p: Paragraph) -> bool:
    return bool(p._element.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
                or p._element.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"))


def heading_level(p: Paragraph) -> int:
    name = (p.style.name or "").lower()
    m = re.match(r"heading (\d)", name)
    return int(m.group(1)) if m else 0


def table_to_md(tbl: Table, blockquote: bool = False) -> list[str]:
    rows = [[c.text.strip().replace("\n", " ") for c in r.cells] for r in tbl.rows]
    if not rows:
        return []
    if blockquote:  # callout box (1x1 table) renders nicer as a quote
        return ["> **" + rows[0][0] + "**"] if len(rows[0]) == 1 else []
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |",
           "|" + "|".join(["---"] * ncol) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def extract(docx_path: str, out_path: str) -> tuple[str, list[str]]:
    doc = Document(docx_path)
    lines: list[str] = []
    blocks = list(iter_block_items(doc))
    pending_picture = False
    problems: list[str] = []

    for i, (kind, obj) in enumerate(blocks):
        if kind == "p":
            text = para_text(obj)
            if has_drawing(obj):
                pending_picture = True
                continue
            if not text:
                continue
            lvl = heading_level(obj)
            if pending_picture:
                m = re.match(r"图(\d)", text)
                if m and int(m.group(1)) in FIG_BY_NUM:
                    rel = os.path.join(FIG_DIR_REL, FIG_BY_NUM[int(m.group(1))]).replace("\\", "/")
                    lines.append(f"![{text}]({rel})")
                else:
                    lines.append("*[figure — see DOCX]*")
                pending_picture = False
                continue
            if lvl:
                lines.append("#" * lvl + " " + text)
            else:
                lines.append(text)
            lines.append("")
        else:  # table
            is_callout = len(obj.rows) == 1 and len(obj.columns) == 1
            lines += table_to_md(obj, blockquote=is_callout)
            lines.append("")
            pending_picture = False

    md = "\n".join(lines).strip() + "\n"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    for token in MUST_CONTAIN:
        if token not in md:
            problems.append(f"MISSING required token: {token}")
    for pattern in MUST_NOT_CONTAIN:
        if re.search(pattern, md):
            problems.append(f"FORBIDDEN token present: {pattern}")
    return md, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="DOCX -> Markdown mirror with consistency checks")
    ap.add_argument("--docx", default=DEFAULT_DOCX)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    if not os.path.exists(args.docx):
        print(f"[extract] ABORT: docx not found: {args.docx}", file=sys.stderr)
        return 2
    md, problems = extract(args.docx, args.out)
    print(f"[extract] wrote {args.out} ({len(md)} chars)")
    if problems:
        for p in problems:
            print(f"[extract] FAIL {p}")
        return 1
    print("[extract] OK — all key numbers present, no forbidden phrases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
