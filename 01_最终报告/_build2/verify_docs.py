# -*- coding: utf-8 -*-
"""Verification of the six 01_最终报告.

1. every DOCX reopens and its text is non-trivial
2. the Chinese documents' text round-trips as valid UTF-8 Chinese (no mojibake),
   checked on the DOCX via python-docx AND via an independent LibreOffice text
   export, and on the PDF via embedded-font inspection
3. the reproduction table still shows the sign crossover (WIN WIN LOSS LOSS)
4. every place that says "not yet available" is listed
5. no document claims that the reproduction beat the paper
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
import builtins

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document  # noqa: E402

from dlv import data as D  # noqa: E402

OUT = os.path.join(D.ROOT, "01_最终报告")
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify")
NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")

DOCS = ["report_internal_en", "report_internal_zh", "progress_report_en",
        "progress_report_zh", "ieee_manuscript_en", "ieee_manuscript_zh"]

MOJIBAKE = ["Ã", "Â", "â€", "ï¿½", "æ\u0088", "\ufffd", "å¤", "ç\u009a", "é\u0080"]
NOT_AVAIL = ["not yet available", "Not yet available", "not yet available in this repo",
             "尚未获得", "尚未取回", "尚未合并"]


def cjk_ratio(s):
    letters = [c for c in s if not c.isspace()]
    if not letters:
        return 0.0
    cjk = sum(1 for c in letters if 0x4E00 <= ord(c) <= 0x9FFF)
    return cjk / len(letters)


def docx_text(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    return "\n".join(parts)


def pdf_fonts(path):
    raw = open(path, "rb").read()
    names = set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-_,.#]+)", raw))
    return sorted(n.decode("latin-1") for n in names)


def lo_text(path, out_txt):
    if os.path.exists(out_txt):
        os.remove(out_txt)
    r = subprocess.run([NODE, CLI, "convert", "--input", path, "--output", out_txt],
                       capture_output=True, text=True)
    if not os.path.exists(out_txt):
        return None, (r.stderr or "")[:200]
    return open(out_txt, encoding="utf-8", errors="replace").read(), ""


def main():
    os.makedirs(V, exist_ok=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    log = open(os.path.join(V, "report.txt"), "w", encoding="utf-8")

    def out(*a):
        s = " ".join(str(x) for x in a)
        builtins.print(s)
        log.write(s + "\n")

    fail = 0
    print = out  # noqa: A001  (local redirection for the rest of the function)
    print("=" * 78)
    print("1. DOCX reopen + text size")
    print("=" * 78)
    texts = {}
    for n in DOCS:
        p = os.path.join(OUT, n + ".docx")
        t = docx_text(p)
        texts[n] = t
        with open(os.path.join(V, n + ".docx.txt"), "w", encoding="utf-8") as fh:
            fh.write(t)
        ok = len(t) > 3000
        fail += 0 if ok else 1
        print(f"  {n:<24} {len(t):>7,} chars   {'OK' if ok else 'TOO SHORT'}")

    print()
    print("=" * 78)
    print("2. Chinese round-trip")
    print("=" * 78)
    for n in ("report_internal_zh", "progress_report_zh", "ieee_manuscript_zh"):
        t = texts[n]
        r = cjk_ratio(t)
        bad = [m for m in MOJIBAKE if m in t]
        # independent path: LibreOffice text export of the same DOCX
        lt, err = lo_text(os.path.join(OUT, n + ".docx"),
                          os.path.join(V, n + ".lo.txt"))
        lo_r = cjk_ratio(lt) if lt else 0.0
        quote = re.sub(r"\s+", "", t)[1000:1020]
        ok = (r > 0.30 and not bad and lt is not None and lo_r > 0.30)
        fail += 0 if ok else 1
        print(f"  {n}")
        print(f"    python-docx : {len(t):,} chars, CJK ratio {r:.3f}, mojibake markers {bad or 'none'}")
        print(f"    LibreOffice : {len(lt) if lt else 0:,} chars, CJK ratio {lo_r:.3f}  {err}")
        print(f"    proof (20 chars): {quote}")
        print(f"    {'PASS' if ok else 'FAIL'}")

    print()
    print("=" * 78)
    print("3. PDF: signature, size, page count, embedded fonts")
    print("=" * 78)
    for n in DOCS:
        p = os.path.join(OUT, n + ".pdf")
        raw = open(p, "rb").read()
        pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
        fonts = pdf_fonts(p)
        cjk_font = [f for f in fonts if re.search(r"SimSun|SimHei|YaHei|Song|Hei|Ming|Noto.*CJK|Droid",
                                                  f, re.I)]
        ok = raw[:5] == b"%PDF-" and len(raw) > 50_000 and pages > 0
        if n.endswith("_zh"):
            ok = ok and bool(cjk_font)
        fail += 0 if ok else 1
        print(f"  {n:<24} {len(raw):>9,} B  {pages:>3} pages  fonts={len(fonts):>2}  "
              f"cjk_font={cjk_font or '—'}  {'OK' if ok else 'CHECK'}")

    print()
    print("=" * 78)
    print("4. The reproduction table still shows the sign crossover")
    print("=" * 78)
    for n in ("report_internal_en", "report_internal_zh", "ieee_manuscript_en", "ieee_manuscript_zh"):
        d = Document(os.path.join(OUT, n + ".docx"))
        found = None
        for t in d.tables:
            signs = [row.cells[4].text.strip() for row in t.rows
                     if len(row.cells) >= 8 and row.cells[0].text.strip().startswith("L=")]
            if len(signs) == 4:
                found = signs
                break
        want_win = ("WIN", "胜")
        ok = found is not None and all(s in want_win for s in found[:2]) and all(
            s in ("LOSS", "负") for s in found[2:])
        fail += 0 if ok else 1
        print(f"  {n:<24} signs={found}  {'OK (2 wins then 2 losses)' if ok else 'MISSING'}")

    print()
    print("=" * 78)
    print("5. 'not yet available' inventory (every place it is written)")
    print("=" * 78)
    for n in DOCS:
        hits = []
        for line in texts[n].split("\n"):
            if any(k in line for k in NOT_AVAIL):
                hits.append(line.strip())
        print(f"  {n}: {len({h[:60] for h in hits})} distinct line(s)")
        for h in sorted(set(hits))[:8]:
            print("     -", h[:150])

    print()
    print("=" * 78)
    print("6. No claim that the reproduction beat the paper")
    print("=" * 78)
    pat = re.compile(r"(beat|exceed|outperform|surpass|超过|优于)(s|ed)?\s*(the\s+)?(paper|original|作者|论文)",
                     re.I)
    for n in DOCS:
        t = texts[n]
        hits = []
        for m in pat.finditer(t):
            ctx = t[max(0, m.start() - 90):m.end() + 40].replace("\n", " ")
            hits.append(ctx)
        print(f"  {n}: {len(hits)} hit(s)")
        for h in hits:
            print("     ...", h[:170])
    print()
    print(f"FAILURES: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
