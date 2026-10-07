import re, glob, statistics as st
from collections import defaultdict

d = defaultdict(list); m = defaultdict(list)
pat = re.compile(r"L=(\d+) DONE: test_mse=([0-9.]+)\(All\) [0-9.]+\(ILI\) test_mae=([0-9.]+)")
for f in glob.glob("src_logs_0817/*.out"):
    for l in open(f, encoding="utf-8", errors="replace"):
        mm = pat.search(l)
        if mm:
            L = int(mm.group(1))
            d[L].append(float(mm.group(2))); m[L].append(float(mm.group(3)))
for L in sorted(d):
    print(f"L={L}: MSE_All={st.mean(d[L]):.4f}+/-{st.pstdev(d[L]):.4f}  MAE_All={st.mean(m[L]):.4f}+/-{st.pstdev(m[L]):.4f}  n={len(d[L])}")
