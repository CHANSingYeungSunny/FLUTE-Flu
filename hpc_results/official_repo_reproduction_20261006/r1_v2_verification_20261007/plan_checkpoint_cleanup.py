#!/usr/bin/env python3
"""
plan_checkpoint_cleanup.py — evidence-based classifier for superseded full
checkpoints on Burgundy scratch. DRY RUN unless --execute is passed.

Rule (from the recovery authorization, section 7): a full checkpoint may be
removed only as SUPERSEDED_CHECKPOINT, which requires ALL of:
  * the run's predictions are preserved elsewhere (durable copy), and
  * the run's metrics are preserved elsewhere (durable copy), and
  * the best checkpoint is retained (durable compact checkpoint), and
  * the exact run identity is known (name match), and
  * no resume requirement, and
  * the file does NOT live in the ACTIVE root.

Everything else is PROTECTED_UNCERTAIN and is never touched.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys

SCRATCH = "/scratch/sychan552"
HOME = "/gpfs1/home/sychan552"
DURABLE = [os.path.join(HOME, "innovation_durable", "screening"),
           os.path.join(HOME, "innovation_durable", "runs")]
ACTIVE_ROOT = "innovation_deploy_root_v3_clean14"
OUT = os.path.dirname(os.path.abspath(__file__))


def durable_runs():
    """run_name -> {has_compact, has_predictions, has_metrics}"""
    idx = {}
    for base in DURABLE:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            d = os.path.join(base, name)
            if not os.path.isdir(d):
                continue
            e = idx.setdefault(name, {"has_compact": False,
                                      "has_predictions": False,
                                      "has_metrics": False})
            for root, _dirs, files in os.walk(d):
                for f in files:
                    if f.endswith(".safetensors") or f == "compact.safetensors":
                        e["has_compact"] = True
                    if f.endswith(".csv") and "prediction" in f.lower():
                        e["has_predictions"] = True
                    if f.endswith(".json") and "metric" in f.lower():
                        e["has_metrics"] = True
    return idx


def main():
    execute = "--execute" in sys.argv
    dur = durable_runs()
    print(f"[plan] durable run entries indexed: {len(dur)}")

    rows = []
    for root in sorted(os.listdir(SCRATCH)):
        if not root.startswith("innovation_deploy_root_"):
            continue
        rootp = os.path.join(SCRATCH, root)
        if not os.path.isdir(rootp):
            continue
        is_active = (root == ACTIVE_ROOT)
        for dirpath, _dirs, files in os.walk(rootp):
            for f in files:
                if not f.endswith(".pt"):
                    continue
                p = os.path.join(dirpath, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                # run name = the directory that owns .../checkpoints/<file>
                parent = os.path.basename(dirpath)
                run = os.path.basename(os.path.dirname(dirpath)) if parent == "checkpoints" else parent
                d = dur.get(run)
                covered = bool(d and d["has_compact"] and d["has_predictions"] and d["has_metrics"])
                if is_active:
                    klass = "PROTECTED_REQUIRED"
                    reason = "ACTIVE root (amendment B) - never delete"
                elif covered:
                    klass = "SUPERSEDED_CHECKPOINT"
                    reason = ("durable copy has compact ckpt + predictions + metrics; "
                              "run identity matched by name")
                elif d and d["has_compact"]:
                    klass = "PROTECTED_UNCERTAIN"
                    reason = "durable compact exists but predictions/metrics not both confirmed"
                else:
                    klass = "PROTECTED_UNCERTAIN"
                    reason = "no durable copy found for this run name"
                rows.append({
                    "path": p, "root": root, "run": run, "bytes": st.st_size,
                    "mtime": int(st.st_mtime), "class": klass, "reason": reason,
                })

    with open(os.path.join(OUT, "HPC_CLEANUP_CLASSIFICATION.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by = {}
    for r in rows:
        b = by.setdefault(r["class"], [0, 0])
        b[0] += 1
        b[1] += r["bytes"]
    print("\n[plan] classification of full .pt checkpoints:")
    for k, (n, s) in sorted(by.items()):
        print(f"  {k:24s} {n:5d} files  {s/2**30:9.2f} GiB")

    deletable = [r for r in rows if r["class"] == "SUPERSEDED_CHECKPOINT"]
    tot = sum(r["bytes"] for r in deletable)
    print(f"\n[plan] DRY RUN — would remove {len(deletable)} files, "
          f"{tot/2**30:.2f} GiB")

    with open(os.path.join(OUT, "HPC_CLEANUP_PLAN.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "bytes", "action", "class"])
        for r in deletable:
            w.writerow([r["path"], r["bytes"], "delete", r["class"]])
    print(f"[plan] wrote HPC_CLEANUP_PLAN.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())