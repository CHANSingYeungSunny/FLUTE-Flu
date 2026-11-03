#!/usr/bin/env python3
"""
render_docx.py — render a DOCX to PDF (Word COM) and then to per-page PNGs
(PyMuPDF) so the layout can be inspected visually.

Usage: python render_docx.py "<path.docx>" "<out_dir>"
"""
from __future__ import annotations

import os
import sys


def docx_to_pdf(docx_path, pdf_path):
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(os.path.abspath(docx_path), ReadOnly=True)
        # 17 = wdExportFormatPDF
        doc.ExportAsFixedFormat(
            OutputFileName=os.path.abspath(pdf_path),
            ExportFormat=17, OpenAfterExport=False,
            OptimizeFor=0, Range=0, Item=0, IncludeDocProps=True,
            KeepIRM=True, CreateBookmarks=1, DocStructureTags=True,
            BitmapMissingFonts=True, UseISO19005_1=False)
        doc.Close(False)
    finally:
        word.Quit()
    return pdf_path


def pdf_to_pngs(pdf_path, out_dir, dpi=110):
    import fitz
    os.makedirs(out_dir, exist_ok=True)
    d = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(d):
        pix = page.get_pixmap(dpi=dpi)
        p = os.path.join(out_dir, f"page_{i+1:02d}.png")
        pix.save(p)
        paths.append(p)
    n = d.page_count
    d.close()
    return paths, n


def main():
    docx = sys.argv[1]
    out_dir = sys.argv[2]
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[render] docx -> pdf: {docx}")
    docx_to_pdf(docx, pdf)
    print(f"[render] pdf  size: {os.path.getsize(pdf):,} bytes")
    pngs, n = pdf_to_pngs(pdf, out_dir)
    print(f"[render] pages: {n}")
    for p in pngs:
        print(f"[render]   {p}  ({os.path.getsize(p):,} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())