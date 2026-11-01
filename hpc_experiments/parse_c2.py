#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""parse_c2.py — Summarise the C2 corrected-scheduler results per horizon."""
from __future__ import annotations

import re
import sys
from collections import defaultdict

LOG = "/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/logs/c2_711464.log"

ESSAY = {24: 1.542, 36: 1.422, 48: 1.414, 60: 1.364}
TRACKC = {24: 1.9686, 36: 1.9332, 48: 1.7547, 60: 1.8042}

per_L = defaultdict(list)
cur_L = cur_seed = None
for line in open(LOG, encoding="utf-8", errors="replace"):
    m = re.search(r"L=(\d+) seed=(\d+)", line)
    if m:
        cur_L, cur_seed = int(m.group(1)), int(m.group(2))
        continue
    m = re.search(r"test mse=([\d.]+)", line)
    if m and cur_L is not None:
        per_L[cur_L].append((cur_seed, float(m.group(1))))
        cur_L = cur_seed = None

print(f"{'L':>4}{'n':>3}{'C2 mean':>10}{'TrackC':>10}{'Δ C2 vs TC':>13}"
      f"{'Essay':>9}{'Δ C2 vs essay':>15}")
print("-" * 66)
tot_c2, tot_tc, tot_es = [], [], []
for L in (24, 36, 48, 60):
    v = per_L.get(L, [])
    if not v:
        print(f"{L:>4}{0:>3}{'pending':>10}")
        continue
    mc = sum(x[1] for x in v) / len(v)
    d_tc = (mc - TRACKC[L]) / TRACKC[L] * 100
    d_es = (mc - ESSAY[L]) / ESSAY[L] * 100
    print(f"{L:>4}{len(v):>3}{mc:>10.4f}{TRACKC[L]:>10.4f}{d_tc:>12.1f}%"
          f"{ESSAY[L]:>9.4f}{d_es:>14.1f}%")
    tot_c2.append(mc); tot_tc.append(TRACKC[L]); tot_es.append(ESSAY[L])

if tot_c2:
    n = len(tot_c2)
    mc = sum(tot_c2) / n
    print("-" * 66)
    print(f"{'4L*':>4}{n:>3}{mc:>10.4f}{sum(tot_tc)/n:>10.4f}"
          f"{(mc - sum(tot_tc)/n)/(sum(tot_tc)/n)*100:>12.1f}%"
          f"{sum(tot_es)/n:>9.4f}{(mc - sum(tot_es)/n)/(sum(tot_es)/n)*100:>14.1f}%")
    print("(* partial: only completed horizons)")
