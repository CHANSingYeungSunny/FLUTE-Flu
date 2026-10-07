"""Determine whether the paper's result tables carry machine-readable text.

The prompt requires the national MSE/MAE targets (L=24/36/48/60) to be verified
from this PDF. A plain text extraction returned the table captions but none of
the numbers, so this probe checks whether the table bodies are real text spans,
vector drawings, or raster images -- and if images, tries OCR.
"""
import json
import re
import sys

import fitz  # PyMuPDF

PDF = r"c:\Users\Asus\Desktop\FYP code\MLFlu\reference_papers\MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.pdf"
OUT = r"c:\Users\Asus\Desktop\FYP code\MLFlu\audit_20260930"

doc = fitz.open(PDF)
print(f"pages={doc.page_count}  pdf={PDF}")

# Table captions that matter, by the page they were seen on.
WANT = ["T ABLE V", "T ABLE VI", "T ABLE VII", "T ABLE VIII", "T ABLE IX", "T ABLE X"]

report = {"pages": [], "table_pages": {}}
for pno in range(doc.page_count):
    page = doc[pno]
    raw = page.get_text("text")
    imgs = page.get_images(full=True)
    blocks = page.get_text("dict")["blocks"]
    n_text = sum(1 for b in blocks if b.get("type") == 0)
    n_img = sum(1 for b in blocks if b.get("type") == 1)
    # digits present anywhere on the page
    nums = re.findall(r"\b\d+\.\d{2,4}\b", raw)
    rec = {"page": pno + 1, "chars": len(raw), "text_blocks": n_text,
           "image_blocks": n_img, "xobjects": len(imgs),
           "decimal_numbers_found": len(nums), "sample": nums[:12]}
    report["pages"].append(rec)
    hits = [w for w in WANT if w in raw]
    if hits:
        report["table_pages"][str(pno + 1)] = hits

print("\n=== per page ===")
print(f"{'pg':>3} {'chars':>6} {'tblk':>5} {'iblk':>5} {'xobj':>5} {'decs':>5}  captions")
for r in report["pages"]:
    caps = report["table_pages"].get(str(r["page"]), [])
    print(f"{r['page']:>3} {r['chars']:>6} {r['text_blocks']:>5} {r['image_blocks']:>5} "
          f"{r['xobjects']:>5} {r['decimal_numbers_found']:>5}  {','.join(caps)}")

print("\n=== decimal numbers per page (first 12) ===")
for r in report["pages"]:
    if r["decimal_numbers_found"]:
        print(f"  p{r['page']:>2}: {r['sample']}")

# ---- if the tables are images, try to render + OCR -------------------------
table_pages = sorted(int(p) for p in report["table_pages"])
print(f"\n=== table-bearing pages: {table_pages} ===")

try:
    import pytesseract
    HAVE_OCR = True
except Exception as e:  # noqa: BLE001
    HAVE_OCR = False
    print(f"pytesseract unavailable: {type(e).__name__}: {e}")

report["ocr_available"] = HAVE_OCR

if HAVE_OCR:
    for pno in table_pages:
        page = doc[pno - 1]
        pix = page.get_pixmap(dpi=400)
        img = fitz.Pixmap(pix)
        png = f"{OUT}/page{pno}.png"
        pix.save(png)
        txt = pytesseract.image_to_string(png, config="--psm 6")
        tpath = f"{OUT}/page{pno}_ocr.txt"
        with open(tpath, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"  p{pno}: rendered {png} ({len(txt)} ocr chars) -> {tpath}")
        # look for the known targets
        for v in ["1.542", "1.422", "1.414", "1.364", "0.726", "0.779", "0.757", "0.719"]:
            if v in txt:
                print(f"      FOUND {v}")

with open(f"{OUT}/pdf_table_probe.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\nwrote {OUT}/pdf_table_probe.json")