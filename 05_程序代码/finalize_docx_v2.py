#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_docx_v2.py
===================
Finalises the v2 report for delivery:

  1. open the DOCX in Word,
  2. update every field (this populates the table of contents),
  3. save the DOCX (so the delivered file ships with a populated TOC),
  4. export a PDF,
  5. render every PDF page to PNG for the visual audit.

Usage: python scripts/finalize_docx_v2.py "<path.docx>" "<out_dir>"
"""
from __future__ import annotations

import os
import sys


def main():
    docx = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir,
                       os.path.splitext(os.path.basename(docx))[0] + ".pdf")

    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(docx, ReadOnly=False)

        # --- populate the TOC and every other field -----------------------
        for i in range(1, doc.TablesOfContents.Count + 1):
            try:
                doc.TablesOfContents(i).Update()
            except Exception as exc:            # noqa: BLE001
                print(f"[finalize] TOC {i} update failed: {exc}")
        try:
            doc.Fields.Update()
        except Exception as exc:                # noqa: BLE001
            print(f"[finalize] Fields.Update failed: {exc}")
        doc.Repaginate()
        pages = doc.ComputeStatistics(2)        # 2 = wdStatisticPages
        words = doc.ComputeStatistics(0)        # 0 = wdStatisticWords
        print(f"[finalize] pages={pages} words={words}")

        doc.Save()
        doc.ExportAsFixedFormat(
            OutputFileName=pdf,
            ExportFormat=17, OpenAfterExport=False,
            OptimizeFor=0, Range=0, Item=0, IncludeDocProps=True,
            KeepIRM=True, CreateBookmarks=1, DocStructureTags=True,
            BitmapMissingFonts=True, UseISO19005_1=False)
        doc.Close(True)
    finally:
        word.Quit()

    print(f"[finalize] docx  : {docx}  ({os.path.getsize(docx):,} B)")
    print(f"[finalize] pdf   : {pdf}  ({os.path.getsize(pdf):,} B)")

    import fitz
    d = fitz.open(pdf)
    pngs = []
    for i, page in enumerate(d):
        pix = page.get_pixmap(dpi=110)
        p = os.path.join(out_dir, f"page_{i + 1:02d}.png")
        pix.save(p)
        pngs.append((p, os.path.getsize(p)))
    n = d.page_count
    d.close()
    print(f"[finalize] pages rendered: {n}")
    for p, sz in pngs:
        print(f"[finalize]   {os.path.basename(p)}  {sz:,} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
