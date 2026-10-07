#!/usr/bin/env python
"""Confirm the two lock files describe the same 108 runs.

`CHECKPOINT_LOCK.json` is the build script's own output and may nest the records
differently from the flattened CSV, so compare the actual (model, L, seed) sets
rather than counting top-level keys.
"""
import csv, json, os, sys

D = sys.argv[1] if len(sys.argv) > 1 else "/home/sychan552/stage5_a2_durable/stage6"
csvp = os.path.join(D, "scoring", "CHECKPOINT_LOCK.csv")
jsonp = os.path.join(D, "scoring", "CHECKPOINT_LOCK.json")

blob = json.load(open(jsonp))
print("=== json top-level structure ===")
print("  type:", type(blob).__name__)
if isinstance(blob, dict):
    for k, v in blob.items():
        n = len(v) if isinstance(v, (list, dict)) else "-"
        print(f"  {k}: {type(v).__name__} len={n}")

def triples_from_json(node):
    """Find every dict carrying model/L/seed, at any depth."""
    out = set()
    if isinstance(node, dict):
        if {"model", "L", "seed"} <= set(node):
            out.add((node["model"], int(node["L"]), int(node["seed"])))
        for v in node.values():
            out |= triples_from_json(v)
    elif isinstance(node, list):
        for v in node:
            out |= triples_from_json(v)
    return out

rows = list(csv.DictReader(open(csvp)))
csv_set = {(r["model"], int(r["L"]), int(r["seed"])) for r in rows}
json_set = triples_from_json(blob)

print("\n=== set comparison ===")
print(f"  csv  runs: {len(csv_set)}   distinct (model,L,seed): {len(csv_set)}")
print(f"  json runs: {len(json_set)}")
print(f"  csv - json = {sorted(csv_set - json_set)}")
print(f"  json - csv = {sorted(json_set - csv_set)}")
print("  MATCH" if csv_set == json_set else "  *** MISMATCH ***")

# every model must be complete: 4 L x 3 seeds
from collections import defaultdict
per = defaultdict(list)
for m, L, s in csv_set:
    per[m].append((L, s))
print("\n=== per-model completeness (expect 4 L x 3 seeds = 12) ===")
ok = True
for m in sorted(per):
    cells = per[m]
    n = len(cells)
    Ls = sorted({c[0] for c in cells})
    seeds = sorted({c[1] for c in cells})
    good = n == 12 and Ls == [24, 36, 48, 60] and seeds == [42, 43, 44]
    ok &= good
    print(f"  {m:16s} {n:2d}  L={Ls}  seeds={seeds}  {'OK' if good else '*** SHORT ***'}")
print(f"  total = {sum(len(v) for v in per.values())} (expect 108)")
print("  ALL COMPLETE" if ok and sum(len(v) for v in per.values()) == 108 else "  *** INCOMPLETE ***")
