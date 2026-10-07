"""Render the remaining pages that carry paper result units not yet read:
p3 (Table I prompt), p4-p6 (Fig 2, Tables II/III, Fig 1), p7 (Table IV
comparative models + hyperparameters), p11 (Fig 7 few-shot)."""
import os

import fitz

PDF = r"c:\Users\Asus\Desktop\FYP code\MLFlu\reference_papers\MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.pdf"
OUT = r"c:\Users\Asus\Desktop\FYP code\MLFlu\audit_20260930\tables"
os.makedirs(OUT, exist_ok=True)
doc = fitz.open(PDF)

for pno in (3, 4, 5, 6, 7, 11):
    page = doc[pno - 1]
    for tag, clip in (("top", fitz.Rect(0, 0, page.rect.width, page.rect.height / 2)),
                      ("bot", fitz.Rect(0, page.rect.height / 2, page.rect.width, page.rect.height))):
        pix = page.get_pixmap(dpi=300, clip=clip)
        p = f"{OUT}/p{pno}_{tag}.png"
        pix.save(p)
        print(p)

print("--- pdf internal links / annotations on those pages ---")
for pno in (3, 4, 5, 6, 7, 11):
    pg = doc[pno - 1]
    print(f"  p{pno}: links={len(pg.get_links())} annots={sum(1 for _ in pg.annots())}")