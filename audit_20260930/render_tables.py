"""Render the paper's table-bearing pages to PNG so the tables can be read
visually, since they are raster images with no text layer and OCR is unavailable.

Pages 8-10 carry Tables V-X (the only quantitative result tables in the paper).
"""
import os

import fitz

PDF = r"c:\Users\Asus\Desktop\FYP code\MLFlu\reference_papers\MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.pdf"
OUT = r"c:\Users\Asus\Desktop\FYP code\MLFlu\audit_20260930\tables"
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(PDF)

# Page 8 = Table V + VI, page 9 = Table VII + Fig 5/6, page 10 = Table VIII + IX.
for pno in (8, 9, 10):
    page = doc[pno - 1]
    # 300 dpi full page, plus a clipped upper/lower half for legibility.
    for tag, clip in (("full", None), ("top", fitz.Rect(0, 0, page.rect.width, page.rect.height / 2)),
                      ("bot", fitz.Rect(0, page.rect.height / 2, page.rect.width, page.rect.height))):
        pix = page.get_pixmap(dpi=300, clip=clip)
        p = f"{OUT}/p{pno}_{tag}.png"
        pix.save(p)
        print(f"{p}  {pix.width}x{pix.height}")

print("\n--- images embedded on those pages ---")
for pno in (8, 9, 10):
    for i, im in enumerate(doc[pno - 1].get_images(full=True)):
        xref = im[0]
        d = doc.extract_image(xref)
        p = f"{OUT}/p{pno}_xobj{i}_{d['width']}x{d['height']}.{d['ext']}"
        with open(p, "wb") as f:
            f.write(d["image"])
        print(f"{p}  ({d['width']}x{d['height']})")