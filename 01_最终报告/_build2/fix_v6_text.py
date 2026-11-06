# -*- coding: utf-8 -*-
import glob
base = r"C:\Users\Asus\Desktop\FYP code\_review_20261104\full\MIFlu_Reviewed_Project\01_最终报告\_build2\dlv"
pairs = [
    ("is not supported by any artefact in this repository and has been ",
     "is supported by the Burgundy queue and per-cell manifests; the "),
    ("removed from the reports.", "7-variable trend is not claimed."),
]
for f in glob.glob(base + r"\text_*.py"):
    s = open(f, encoding="utf-8").read()
    n = 0
    for a, b in pairs:
        n += s.count(a); s = s.replace(a, b)
    open(f, "w", encoding="utf-8").write(s)
    print(f.split("\\")[-1], n)
