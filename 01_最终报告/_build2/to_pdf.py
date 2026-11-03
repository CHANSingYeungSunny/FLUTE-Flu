# -*- coding: utf-8 -*-
"""Convert the six DOCX 01_最终报告 to PDF with the bundled LibreOffice kit.

Also reports the page count of each PDF (parsed from the PDF itself, no library)
and verifies the %PDF- signature and a non-trivial size.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlv import data as D  # noqa: E402

NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")

OUT = os.path.join(D.ROOT, "01_最终报告")
DOCS = ["report_internal_en", "report_internal_zh",
        "progress_report_en", "progress_report_zh",
        "ieee_manuscript_en", "ieee_manuscript_zh"]


def page_count(pdf: str) -> int:
    """/Type /Page objects, excluding the /Pages tree node."""
    data = open(pdf, "rb").read()
    n = len(re.findall(rb"/Type\s*/Page[^s]", data))
    if n:
        return n
    m = re.search(rb"/Count\s+(\d+)", data)
    return int(m.group(1)) if m else 0


def main():
    rows = []
    for name in DOCS:
        src = os.path.join(OUT, name + ".docx")
        dst = os.path.join(OUT, name + ".pdf")
        if os.path.exists(dst):
            os.remove(dst)
        cp = subprocess.run([NODE, CLI, "convert", "--input", src, "--output", dst],
                            capture_output=True, text=True)
        ok = os.path.exists(dst) and os.path.getsize(dst) > 20_000
        sig = ok and open(dst, "rb").read(5) == b"%PDF-"
        pages = page_count(dst) if ok else 0
        rows.append((name, os.path.getsize(src), os.path.getsize(dst) if ok else 0, pages, sig,
                     cp.returncode, (cp.stderr or "").strip()[:120]))
    print(f"{'document':<24}{'docx B':>10}{'pdf B':>10}{'pages':>7}  sig  rc")
    for r in rows:
        print(f"{r[0]:<24}{r[1]:>10,}{r[2]:>10,}{r[3]:>7}  {r[4]!s:<5} {r[5]}")
        if r[6]:
            print("    stderr:", r[6])
    bad = [r for r in rows if not r[4] or r[3] == 0]
    if bad:
        print("FAILED:", [b[0] for b in bad])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
