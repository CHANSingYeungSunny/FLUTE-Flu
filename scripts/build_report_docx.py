#!/usr/bin/env python
"""Regenerate the advisor report .docx from the Markdown single source.

The Chinese report filename cannot be passed safely through PowerShell argv
(encoding gets mangled), so the path is hard-coded here as a UTF-8 literal.
Run from the project root:

    python scripts/build_report_docx.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from md_to_docx import convert  # noqa: E402

SRC = os.path.join(PROJECT_ROOT, "MIFlu_导师五大疑问_回复报告.md")
DST = os.path.join(PROJECT_ROOT, "MIFlu_导师五大疑问_回复报告.docx")

if __name__ == "__main__":
    convert(SRC, DST)
    print(f"[build_report_docx] wrote {DST}")
