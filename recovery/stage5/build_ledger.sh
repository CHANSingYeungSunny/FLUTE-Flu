#!/bin/bash
# Stage 5 A2 — GPU accounting for this round, rebuilt from the scheduler.
# sacct -X (top-level jobs only) so .batch/.extern steps of the same allocation
# are not counted twice. Each job allocated gres/gpu=1 (A100) on partition stingy.
sacct -u sychan552 -S 2026-09-25T00:00:00 -X --noheader \
  --format=JobID,JobName,State,Elapsed,AllocTRES%40,Submit,Start,End -P \
| /home/sychan552/.conda/envs/mlflu_hpc/bin/python -c '
import sys, re
def secs(e):
    if "-" in e:
        d, _, t = e.partition("-")
    else:
        d, t = "0", e
    parts = (t.split(":") + ["0", "0", "0"])[:3]
    return int(d)*86400 + int(parts[0])*3600 + int(parts[1])*60 + int(float(parts[2]))
tot = {}
rows = []
for line in sys.stdin:
    f = line.rstrip("\n").split("|")
    if len(f) < 5: continue
    jid, name, state, el, tres = f[0], f[1], f[2], f[3], f[4]
    m = re.search(r"gres/gpu=a100:(\d+)", tres) or re.search(r"gres/gpu=(\d+)", tres)
    g = int(m.group(1)) if m else 0
    s = secs(el); gh = s*g/3600
    cat = ("preflight" if "preflight" in name else "verify" if "verify" in name
           else "scoring" if "score" in name else "fit" if "task" in name else "other")
    rows.append((jid, name, state, el, g, gh, cat, f[5]))
    tot["TOTAL"] = tot.get("TOTAL", 0)+gh
    tot[cat] = tot.get(cat, 0)+gh
    tot["gpu_seconds"] = tot.get("gpu_seconds", 0)+s*g
print("%-8s %-13s %-14s %-9s %-3s %-9s %-9s %s" % ("JOBID","NAME","STATE","ELAPSED","GPU","GPU_H","CAT","SUBMIT"))
for r in sorted(rows, key=lambda x: x[7]):
    print("%-8s %-13s %-14s %-9s %-3d %-9.4f %-9s %s" % r)
print()
for k in ("preflight","verify","fit","scoring","other"):
    if k in tot: print("  %-10s %.4f GPU-h" % (k, tot[k]))
print("  %-10s %.4f GPU-h  (= %.0f GPU-seconds)" % ("TOTAL", tot["TOTAL"], tot["gpu_seconds"]))
print("  %-10s 2.0000 GPU-h" % "CAP")
print("  %-10s %.4f GPU-h" % ("REMAINING", 2.0-tot["TOTAL"]))
'
