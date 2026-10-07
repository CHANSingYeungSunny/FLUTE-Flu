import re
from collections import defaultdict
import statistics as st

path = "training_miflu_log_514859.txt"
lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
pat = re.compile(r"L=(\d+) DONE: test_mse=([0-9.]+)\(All\) [0-9.]+\(ILI\) test_mae=([0-9.]+)")
d = defaultdict(list)
m = defaultdict(list)
for l in lines:
    mm = pat.search(l)
    if mm:
        L = int(mm.group(1))
        d[L].append(float(mm.group(2)))
        m[L].append(float(mm.group(3)))

for L in sorted(d):
    print(f"L={L}: MSE_All={st.mean(d[L]):.4f}+/-{st.pstdev(d[L]):.4f}  MAE_All={st.mean(m[L]):.4f}+/-{st.pstdev(m[L]):.4f}  n={len(d[L])}")
