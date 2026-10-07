#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_render_v2.py
==================
Objective, per-page render audit of the v2 report.

For every rendered page PNG it computes:

  * ink fraction      — share of non-white pixels (detects blank / near-blank pages)
  * content bbox      — in centimetres, converted from pixels at the render DPI
  * margin overrun    — content extending outside the declared text frame

Page geometry assumed: A4 portrait 21.0 x 29.7 cm.
Declared text frame:   left 2.3 cm, right 2.3 cm, top 2.2 cm, bottom 2.2 cm
                       (bottom frame is relaxed for the footer band).

Usage: python scripts/audit_render_v2.py <png_dir> <dpi>
"""
from __future__ import annotations

import os
import sys

from PIL import Image

A4_W_CM, A4_H_CM = 21.0, 29.7
MARGIN_L, MARGIN_R = 2.3, 2.3
MARGIN_T, MARGIN_B = 2.2, 2.2
FOOTER_BAND_CM = 1.6          # footer lives inside the bottom margin
# Word shifts a table 0.19 cm into the gutter by default so that cell TEXT
# aligns with body text. The table therefore appears to cross the declared
# margin by that amount on every table-bearing page. The tolerance below
# accommodates that standard indent; anything beyond it is a real overrun.
TOL = 0.25                    # cm tolerance


def bbox_nonwhite(im, thresh=245):
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    xmin, ymin, xmax, ymax = w, h, -1, -1
    for y in range(h):
        row_hit = False
        for x in range(w):
            if px[x, y] < thresh:
                row_hit = True
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
        if row_hit:
            if y < ymin:
                ymin = y
            ymax = y
    return xmin, ymin, xmax, ymax, w, h


def main():
    png_dir = sys.argv[1]
    dpi = float(sys.argv[2]) if len(sys.argv) > 2 else 110.0
    files = sorted(f for f in os.listdir(png_dir)
                   if f.startswith("page_") and f.endswith(".png"))
    cm = 2.54 / dpi

    print("page,width_cm,height_cm,ink_pct,left_cm,right_cm,top_cm,bottom_cm,flag")
    flags = []
    for fn in files:
        p = os.path.join(png_dir, fn)
        im = Image.open(p)
        w, h = im.size
        g = im.convert("L")
        hist = g.histogram()
        nonwhite = sum(hist[:245])
        ink = nonwhite / float(w * h) * 100.0
        x0, y0, x1, y1, _, _ = bbox_nonwhite(im)
        l, r = x0 * cm, (w - 1 - x1) * cm
        t, b = y0 * cm, (h - 1 - y1) * cm

        note = []
        if ink < 0.6:
            note.append("NEAR_BLANK")
        if l < MARGIN_L - TOL:
            note.append("LEFT_OVERRUN")
        if r < MARGIN_R - TOL:
            note.append("RIGHT_OVERRUN")
        if t < MARGIN_T - TOL:
            note.append("TOP_OVERRUN")
        if b < MARGIN_B - FOOTER_BAND_CM - TOL:
            note.append("BOTTOM_OVERRUN")
        flag = ";".join(note) if note else "OK"
        if note:
            flags.append((fn, flag))

        print(f"{fn},{w * cm:.2f},{h * cm:.2f},{ink:.2f},"
              f"{l:.2f},{r:.2f},{t:.2f},{b:.2f},{flag}")

    print("")
    print(f"pages={len(files)} flagged={len(flags)}")
    for fn, fl in flags:
        print(f"  {fn}: {fl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
