#!/usr/bin/env python3
"""Reconcile the run ledgers against the score matrices, and print the exact
scheduler timestamps for the A0 GPU jobs.

The ledgers record submissions (including retries); the score matrices record
what actually got evaluated. An audit must show that every scored (model, L,
seed) cell is backed by a ledger row, and explain every ledger row that is NOT
scored. Nothing here writes to the results tree.
"""
import csv
import json
import os
import subprocess
import sys

ROOT = "/scratch/sychan552/a2_stage5/results"


def rows(path):
    """The run ledgers are headerless: run_id,jobid,model,L,seed,marker,exit."""
    if not os.path.exists(path):
        return None
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


def rows_dict(path):
    """The lock tables DO have a header."""
    if not os.path.exists(path):
        return None
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def key3(r):
    """Works for both a 7-column ledger row and a dict from a lock table."""
    if isinstance(r, dict):
        return (r["model"].strip(), str(r["L"]).strip(), str(r["seed"]).strip())
    return (r[2].strip(), str(r[3]).strip(), str(r[4]).strip())


print("=" * 78)
print("1. LEDGER vs SCORE MATRIX, per stage")
print("=" * 78)
for stage in ("stage5", "stage6"):
    led = rows(f"{ROOT}/{stage}/logs/run_ledger.csv")
    sc = rows_dict(f"{ROOT}/{stage}/scoring/score_matrix.csv")
    print(f"\n--- {stage}")
    print(f"    ledger rows      = {len(led)}")
    print(f"    score rows       = {len(sc)}")

    led_keys = [key3(r) for r in led]
    sc_keys = [key3(r) for r in sc]
    led_set, sc_set = set(led_keys), set(sc_keys)

    print(f"    unique ledger cells = {len(led_set)}")
    print(f"    unique scored cells = {len(sc_set)}")
    dup = sorted({k for k in led_keys if led_keys.count(k) > 1})
    print(f"    ledger cells appearing more than once (retries): {len(dup)}")
    for k in dup[:12]:
        n = led_keys.count(k)
        print(f"        {k}  x{n}")

    print(f"    scored but NOT in ledger : {sorted(sc_set - led_set)}")
    print(f"    in ledger but NOT scored : {sorted(led_set - sc_set)}")

    # which model names appear where
    from collections import Counter
    print("    ledger model counts:", dict(Counter(k[0] for k in led_keys)))
    print("    scored model counts:", dict(Counter(k[0] for k in sc_keys)))

    # every scored cell must have a model in the lock
    lock = rows_dict(f"{ROOT}/{stage}/scoring/CHECKPOINT_LOCK.csv")
    if lock:
        lk = set(key3(r) for r in lock)
        learned = set(k for k in sc_set if k[0] != "naive")
        print(f"    lock rows = {len(lock)}")
        print(f"    scored learned cells missing from lock: {sorted(learned - lk)}")
        print(f"    lock cells never scored            : {sorted(lk - sc_set)}")

print()
print("=" * 78)
print("2. A0 GPU JOBS - exact scheduler timestamps (local HKT)")
print("=" * 78)
out = subprocess.run(
    ["sacct", "-j", "587048,587054,587059,587068,587091",
     "--noheader", "-X", "-P",
     "--format=JobID,JobName,Submit,Start,End,Elapsed,State,ExitCode,AllocTRES"],
    capture_output=True, text=True).stdout
for line in out.strip().splitlines():
    print("   ", line)
print("\n   NOTE stage6 first fit started 2026-09-26T10:34:29Z "
      "(= 18:34:29 HKT) per the ledger above.")

print()
print("=" * 78)
print("3. s6_score jobs and whether they produced the scoring artefacts")
print("=" * 78)
out = subprocess.run(
    ["sacct", "-u", os.environ["USER"], "-S", "2026-09-26", "-E", "now", "-X",
     "--noheader", "-P", "--format=JobID,JobName,Submit,End,Elapsed,State,ExitCode"],
    capture_output=True, text=True).stdout
for line in out.strip().splitlines():
    if "score" in line.lower():
        print("   ", line)

for f in ("score_matrix.csv", "score_summary.csv", "average_mse_4L.csv",
          "CHECKPOINT_LOCK.csv", "CHECKPOINT_LOCK.json", "recomputed_average_mse_4L.csv"):
    p = f"{ROOT}/stage6/scoring/{f}"
    if os.path.exists(p):
        import datetime
        st = os.stat(p)
        print(f"    {f:32s} mtime={datetime.datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}  size={st.st_size}")

print()
print("=" * 78)
print("4. stage6 s6_score job stderr tail (why sacct says FAILED)")
print("=" * 78)
for j in ("587373", "587385"):
    for ext in ("err", "out"):
        for base in (f"/scratch/sychan552/a2_stage5/logs/s6_score_{j}.{ext}",
                     f"/scratch/sychan552/a2_stage5/recovery/stage6/logs/s6_score_{j}.{ext}",
                     f"{ROOT}/stage6/logs/s6_score_{j}.{ext}"):
            if os.path.exists(base):
                print(f"--- {base}")
                with open(base) as fh:
                    t = fh.read().strip().splitlines()
                for l in t[-14:]:
                    print("     ", l)

print()
print("=" * 78)
print("5. availability of a0 GPU raw logs and their key numbers")
print("=" * 78)
for j in ("587068", "587091"):
    p = f"/scratch/sychan552/a0_runs/logs/a0_{j}.out"
    if not os.path.exists(p):
        print(f"    {p} MISSING")
        continue
    with open(p) as fh:
        txt = fh.read()
    print(f"--- {j}")
    for line in txt.splitlines():
        low = line.lower()
        if "best performance" in low or low.strip().startswith(("mse:", "mae:", "mse_mean", "mae_mean")) \
           or "mae:" in low and "mse:" in low:
            print("     ", line.strip()[:160])