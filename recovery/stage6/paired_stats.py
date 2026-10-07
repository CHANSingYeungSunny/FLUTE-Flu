#!/usr/bin/env python
"""Paired comparison of the eight-model primary metric.

The eight models were fitted under one protocol, so the natural test is paired
at (L, seed): the same 12 cells for every model. An unpaired ranking of means
would hide that the seed spread is comparable to the gaps between neighbours.
"""
import csv
import statistics as st
from collections import defaultdict

EIGHT = ["miflu", "nlinear", "dlinear", "timecma_llm",
         "patchtst", "itransformer", "qwen_time_llm", "calf_llm"]
CONTROL = "notext"
SEEDS = (42, 43, 44)
LS = (24, 36, 48, 60)

cells = defaultdict(dict)          # model -> (L,seed) -> mse_all
with open("results/stage6/scoring/score_matrix.csv", newline="") as f:
    for r in csv.DictReader(f):
        cells[r["model"]][(int(r["L"]), int(r["seed"]))] = float(r["mse_all"])

for m in EIGHT + [CONTROL]:
    assert len(cells[m]) == 12, (m, len(cells[m]))

# ---- primary metric: mean over seeds, then equal-weight mean over L --------
def primary(m):
    per_l = [st.mean(cells[m][(L, s)] for s in SEEDS) for L in LS]
    return st.mean(per_l), per_l

print("=== primary metric average_MSE_4L and its two stages of averaging ===")
rows = []
for m in EIGHT + [CONTROL]:
    p, per_l = primary(m)
    rows.append((p, m, per_l))
    print(f"  {m:16s} {p:.6f}   " + "  ".join(f"L{L}={v:.4f}" for L, v in zip(LS, per_l)))
rows.sort()

# ---- spread of the 12 cells, to judge whether gaps mean anything -----------
print("\n=== per-model cell spread (12 paired cells) ===")
spread = {}
for m in EIGHT + [CONTROL]:
    v = [cells[m][k] for L in LS for s in SEEDS for k in [(L, s)]]
    spread[m] = st.stdev(v)
    print(f"  {m:16s} mean={st.mean(v):.4f}  sd={spread[m]:.4f}")

# ---- paired differences on the 12 cells -----------------------------------
def paired(a, b):
    d = [cells[a][k] - cells[b][k] for L in LS for s in SEEDS for k in [(L, s)]]
    mean = st.mean(d)
    sd = st.stdev(d)
    return mean, sd, sum(1 for x in d if x > 0), d

print("\n=== paired differences on the 12 (L,seed) cells: A - B ===")
print("    negative mean means A is better; n_win = cells where A beats B")
pairs = [(CONTROL, "miflu"), (CONTROL, "nlinear"), ("miflu", "nlinear"),
         ("miflu", "dlinear"), ("miflu", "timecma_llm"),
         ("nlinear", "dlinear"), ("nlinear", "timecma_llm"),
         ("dlinear", "timecma_llm"),
         ("timecma_llm", "patchtst"), ("patchtst", "itransformer")]
for a, b in pairs:
    mean, sd, win, d = paired(a, b)
    se = sd / len(d) ** 0.5
    t = mean / se if se else float("nan")
    print(f"  {a:15s} - {b:15s}  mean={mean:+.4f}  sd={sd:.4f}  "
          f"t={t:+.2f}  A better in {win}/12")

# ---- sign flips across L for the headline text question --------------------
print("\n=== miflu - notext per L (mean over 3 seeds) ===")
for L in LS:
    a = st.mean(cells["miflu"][(L, s)] for s in SEEDS)
    b = st.mean(cells[CONTROL][(L, s)] for s in SEEDS)
    wins = sum(1 for s in SEEDS if cells["miflu"][(L, s)] < cells[CONTROL][(L, s)])
    print(f"  L={L:2d}  miflu={a:.4f}  notext={b:.4f}  delta={a-b:+.4f}  "
          f"miflu wins {wins}/3 seeds")

# ---- the two named sets the script prints ---------------------------------
non_llm = [primary(m)[0] for m in ["miflu", "nlinear", "dlinear", "patchtst", "itransformer"]]
llm = [primary(m)[0] for m in ["qwen_time_llm", "calf_llm", "timecma_llm"]]
print(f"\n=== descriptive set means (NOT a random sample) ===")
print(f"  non-LLM (n={len(non_llm)}): {st.mean(non_llm):.6f}")
print(f"  LLM     (n={len(llm)}): {st.mean(llm):.6f}")

# ---- rank table for the report ---------------------------------------------
print("\n=== final ranking with cell sd ===")
for i, (p, m, _) in enumerate(rows, 1):
    tag = " [mechanism control, not one of the eight]" if m == CONTROL else ""
    print(f"  {i:2d}. {m:16s} {p:.6f}  (cell sd {spread[m]:.4f}){tag}")
