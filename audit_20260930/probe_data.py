"""Establish the identity of every candidate national-ILI data file.

The audit must decide which file the training runs actually consumed, so this
records rows, columns, value ranges, the OT column statistics that the paper's
Table II lets us check against, and pairwise cell-level equality.

No file is modified.
"""
import hashlib
import json
import os

import pandas as pd

ROOT = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
OUT = os.path.join(ROOT, "audit_20260930")

CANDIDATES = {
    "author_repo/national_illness.csv":
        r"recovery\author_repo\dataset\illness\national_illness.csv",
    "author_repo/national_illness_orig.csv":
        r"recovery\author_repo\dataset\illness\national_illness_orig.csv",
    "project/raw/national_illness_raw.csv":
        r"data\raw\national_illness_raw.csv",
    "project/raw/national_illness_raw_paper_exact.csv":
        r"data\raw\national_illness_raw_paper_exact.csv",
}

# Paper Table II: national-illness dataset descriptive statistics.
TABLE2 = {
    "1 Percentage of ILI patient visits (weighted)": (1.851, 7.715, 1.342),
    "2 Percentage of ILI patient visits (unweighted)": (1.845, 7.780, 1.308),
    "3 ILI patient count age 0-4": (3434.814, 24097, 3152.330),
    "4 ILI patient count age 5-24": (4981.128, 45513, 5950.799),
    "5 Total ILI patient count": (13540.720, 111361, 15003.120),
    "6 Number of healthcare providers": (1608.262, 3453, 681.227),
    "7 Total ILI patient visits": (651497.500, 1640587, 348838.200),
}

print("=" * 100)
print("PART 1 - file inventory")
print("=" * 100)
info = {}
for tag, rel in CANDIDATES.items():
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print(f"  MISSING  {tag}")
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    df = pd.read_csv(p)
    rec = {
        "path": rel,
        "sha256": h,
        "bytes": os.path.getsize(p),
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "columns": list(map(str, df.columns)),
        "fts_col_present": "fts" in df.columns,
        "first_row": {str(k): str(v) for k, v in df.iloc[0].items()},
        "last_row": {str(k): str(v) for k, v in df.iloc[-1].items()},
        "nan_total": int(df.isna().sum().sum()),
    }
    info[tag] = rec
    print(f"\n  {tag}")
    print(f"    sha256 = {h}")
    print(f"    rows={rec['rows']}  cols={rec['cols']}  bytes={rec['bytes']}  NaNs={rec['nan_total']}")
    print(f"    columns = {rec['columns']}")
    print(f"    'fts' attr column present = {rec['fts_col_present']}")
    print(f"    first = {rec['first_row']}")
    print(f"    last  = {rec['last_row']}")

print()
print("=" * 100)
print("PART 2 - the numeric block, per file (last 7 numeric-ish columns)")
print("=" * 100)
numeric = {}
for tag, rel in CANDIDATES.items():
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        continue
    df = pd.read_csv(p)
    num = df.select_dtypes("number")
    if num.shape[1] >= 7:
        # author file: date,1..6,OT ; orig: named cols. Take the last 7 numeric.
        num = num.iloc[:, -7:]
    numeric[tag] = num.reset_index(drop=True)
    print(f"\n  {tag}  shape={num.shape}")
    for i, c in enumerate(num.columns):
        print(f"    {str(c):>14}  mean={num[c].mean():>16.4f}  max={num[c].max():>14.4f} "
              f" sd={num[c].std(ddof=1):>16.4f}")

print()
print("=" * 100)
print("PART 3 - compare the 7-column block against paper Table II")
print("=" * 100)
keys = list(numeric.keys())
if keys:
    base = keys[0]
    for tag in keys:
        print(f"\n  {tag}")
        num = numeric[tag]
        rows = list(TABLE2.items())
        for i, (label, (m, mx, sd)) in enumerate(rows):
            if i >= num.shape[1]:
                break
            c = num.columns[i]
            dm = num[c].mean() - m
            dx = num[c].max() - mx
            ds = num[c].std(ddof=1) - sd
            flag = "OK " if (abs(dm) < 0.01 and abs(ds) < 0.01 and abs(dx) < 0.5) else "DIFF"
            print(f"    {flag} var{i+1}: mean {num[c].mean():>14.3f} (paper {m:>12.3f}) "
                  f"max {num[c].max():>10.0f} (paper {mx:>7}) sd {num[c].std(ddof=1):>12.3f} (paper {sd:>11.3f})")

print()
print("=" * 100)
print("PART 4 - cell-level equality between the candidate files")
print("=" * 100)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        na, nb = numeric[a], numeric[b]
        same_shape = na.shape == nb.shape
        if not same_shape:
            print(f"  {a}  vs  {b}: SHAPE DIFFERS {na.shape} vs {nb.shape}")
            continue
        diff = (na.to_numpy(dtype=float) - nb.to_numpy(dtype=float))
        nz = int((abs(diff) > 1e-9).sum())
        print(f"  {a}  vs  {b}: shape equal {same_shape}, differing cells = {nz}, "
              f"max |diff| = {abs(diff).max():.10g}")

with open(os.path.join(OUT, "data_files_probe.json"), "w", encoding="utf-8") as f:
    json.dump({"files": info,
               "sha256": {k: v["sha256"] for k, v in info.items()}}, f, indent=2)
print(f"\nwrote {OUT}/data_files_probe.json")