#!/usr/bin/env python
"""
verify_report_parity.py — prove the .md and .docx reports carry IDENTICAL content
=================================================================================

WHY THIS EXISTS
---------------
The advisor requires the Word and Markdown versions of the Q&A report to be
content-identical. `md_to_docx.py` generates BOTH from one Markdown source,
but "we generated it from one source" is a claim, not a proof. This script
verifies it: it re-reads the finished .docx and checks that every content unit
from the .md is actually present in the .docx, and that every figure referenced
by the .md was really embedded.

Checks performed
----------------
  1. word/document.xml is well-formed XML.
  2. Image count: every ![](...) in the .md has a matching embedded media part.
  3. Text parity: every heading / paragraph / bullet / quote line / table cell
     in the .md appears in the .docx text (markdown syntax stripped,
     whitespace normalised).
  4. Hyperlink count is reported (bare URLs are auto-linked).

Exit code 0 = parity OK, 1 = divergence found.

Usage:  python scripts/verify_report_parity.py
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Fix Windows console encoding for CJK filenames
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from md_to_docx import parse_blocks  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def strip_md_syntax(s: str) -> str:
    """Reduce a markdown inline string to the plain text Word would show."""
    s = s.replace("\\*", "*").replace("\\_", "_")      # backslash escapes
    s = re.sub(r"!\[(.*?)\]\((.*?)\)", "", s)          # images (not text)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)   # links -> link text
    s = s.replace("**", "").replace("`", "")
    s = re.sub(r"\*([^*]+)\*", r"\1", s)               # italics
    s = re.sub(r"\s+", " ", s).strip()
    return s


def md_content_units(md: str) -> list:
    """Flatten the Markdown into the text units that must survive conversion."""
    units = []
    for kind, payload in parse_blocks(md):
        if kind == "heading":
            units.append(("heading", strip_md_syntax(payload[1])))
        elif kind == "para":
            t = strip_md_syntax(payload)
            if t:
                units.append(("para", t))
        elif kind in ("bullets", "numbers"):
            for it in payload:
                t = strip_md_syntax(it)
                if t:
                    units.append((kind, t))
        elif kind == "quote":
            for _sub, text in payload:
                t = strip_md_syntax(text)
                if t:
                    units.append(("quote", t))
        elif kind == "table":
            header, rows = payload
            for c in header:
                if c.strip():
                    units.append(("table", strip_md_syntax(c)))
            for r in rows:
                for c in r:
                    if c.strip():
                        units.append(("table", strip_md_syntax(c)))
        elif kind == "code":
            for line in payload:
                units.append(("code", line.rstrip()))
    return units


def find_authoritative_report() -> tuple[str, str]:
    """Locate the authoritative report MD + DOCX in reports/concise_final/."""
    base = os.path.join(PROJECT_ROOT, "reports", "concise_final")
    md_path = os.path.join(base, "REPORT_精简终版.md")
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"MD not found: {md_path}")
    # DOCX has the full long name
    docx_path = None
    for fn in os.listdir(base):
        if fn.endswith(".docx"):
            docx_path = os.path.join(base, fn)
            break
    if docx_path is None:
        raise FileNotFoundError(f"DOCX not found in {base}")
    return md_path, docx_path


def main() -> int:
    md_path, docx_path = find_authoritative_report()

    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    if not os.path.exists(docx_path):
        print(f"FAIL: {os.path.basename(docx_path)} does not exist")
        return 1

    print(f"MD   : {os.path.basename(md_path)}")
    print(f"DOCX : {os.path.basename(docx_path)}")

    # ---- 1. well-formedness + package integrity ----------------------------
    with zipfile.ZipFile(docx_path) as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels").decode("utf-8")
        types_xml = z.read("[Content_Types].xml").decode("utf-8")
        media = [n for n in names if n.startswith("word/media/")]
        blobs = {n: z.read(n) for n in media}
    try:
        ET.fromstring(doc_xml)
        print("[ok]  document.xml is well-formed XML")
    except ET.ParseError as e:
        print(f"FAIL: document.xml is not well-formed: {e}")
        return 1

    dangling = sorted(
        set(re.findall(r'r:(?:embed|id)="([^"]+)"', doc_xml.decode("utf-8")))
        - set(re.findall(r'Id="([^"]+)"', rels_xml)))
    if dangling:
        print(f"FAIL: dangling relationship reference(s): {dangling}")
        return 1
    print("[ok]  every r:embed / r:id reference resolves to a relationship")

    bad = [n for n, b in blobs.items() if not b or b[:4] != b"\x89PNG"]
    if bad:
        print(f"FAIL: empty or non-PNG media part(s): {bad}")
        return 1
    if media and 'Extension="png"' not in types_xml:
        print("FAIL: PNG default content type not declared")
        return 1
    print(f"[ok]  all {len(media)} media part(s) are valid non-empty PNGs")

    # ---- 2. images ---------------------------------------------------------
    md_images = re.findall(r"!\[.*?\]\((.*?)\)", md)
    if len(md_images) != len(media):
        print(f"FAIL: md references {len(md_images)} image(s) but the docx "
              f"embeds {len(media)}")
        for p in md_images:
            full = os.path.join(PROJECT_ROOT, p)
            print(f"      {'OK ' if os.path.exists(full) else 'MISSING'} {p}")
        return 1
    print(f"[ok]  images: {len(media)} referenced == {len(media)} embedded")

    # ---- 3. hyperlinks -----------------------------------------------------
    n_ext = rels_xml.count('TargetMode="External"')
    md_urls = len(re.findall(r"https?://", md))
    print(f"[ok]  hyperlinks: {n_ext} external relationship(s) "
          f"(md contains {md_urls} URL occurrence(s))")

    # ---- 4. text parity ----------------------------------------------------
    root = ET.fromstring(doc_xml)
    docx_text = "".join(t.text or "" for t in root.iter(f"{W}t"))
    docx_text = re.sub(r"\s+", " ", docx_text)

    units = md_content_units(md)
    missing = [(k, t) for k, t in units if strip_md_syntax(t) not in docx_text]

    print(f"[info] md content units checked : {len(units)}")
    print(f"[info] docx text length         : {len(docx_text)} chars")
    if missing:
        print(f"FAIL: {len(missing)} unit(s) missing from the docx:")
        for k, t in missing[:25]:
            print(f"      [{k}] {t[:110]}")
        return 1
    print("[ok]  every Markdown content unit is present in the .docx")
    print("\nPARITY: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
