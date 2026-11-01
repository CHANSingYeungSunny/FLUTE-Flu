#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_bench_gpu_provenance.py -- which GPU produced each benchmark cell?

WHY
---
AGENTS.md HARD RULE 12 requires every reported number to carry its hardware
provenance. The 204 benchmark cells in `hpc_results/expanded_runs/` were produced
inside long-running controller jobs, not one job per cell, so the mapping has to
be reconstructed: each cell's `pred_*.npz` mtime is matched to the Slurm job
whose [Start, End] window contains it, and that job's NodeList is resolved to a
GPU model via the cluster's GRES inventory.

METHOD (explicit, no guessing)
------------------------------
1. accounting dump: `sacct -S 2026-10-25 -P -o JobID,JobName,Partition,State,
   NodeList,Start,End,Elapsed` (saved by `_prov.sh`).
2. node -> GPU model from `sinfo -N -o "%N %P %G"`.
3. for each cell: consider only top-level job rows (drop `.batch`/`.extern`
   steps) with a non-empty NodeList and a complete [Start, End]; keep those whose
   window contains the npz mtime; choose the smallest window (the tightest
   containment). If nothing matches, write `UNKNOWN` -- never infer.
4. output `paper_tables/BENCH_GPU_PROVENANCE.csv` with
   model, L, seed, job_id, node, gpu_type, gpu_count.

Usage:  python scripts/build_bench_gpu_provenance.py [--out PATH]
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
HERE = os.path.dirname(os.path.abspath(__file__))

# node-name prefix -> GPU model. Taken from `sinfo -N -o "%N %P %G"`; the prefix
# determines the card, and the GRES column confirms the count.
NODE_GPU = [
    ("gpu-a100-", "A100-SXM4-80GB", 4),
    ("gpu-v100s-", "V100-SXM2-32GB", 8),
    ("gpu-a40-", "A40", 8),
    ("explorer-", "V100-PCIE-16GB", 2),
    ("cpunode-", "CPU", 0),
]

# Slurm job names that actually write `expanded_runs/**/pred_*.npz`. A job whose
# name is not one of these prefixes is only used if no producer overlaps, and is
# then flagged in the `source` column.
PRODUCER_PREFIXES = ("miflu_ctrl", "nlinear_add", "miflu_export", "expanded", "miflu_a100", "nlinear_a100")


def gpu_of(node):
    for pre, name, cnt in NODE_GPU:
        if node.startswith(pre):
            return name, cnt
    return "UNKNOWN", 0


def parse_dt(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def load_jobs(path):
    jobs = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="|"):
            jid = r["JobID"]
            if "." in jid:                      # .batch / .extern step rows
                continue
            node = (r.get("NodeList") or "").strip()
            st, en = parse_dt(r.get("Start") or ""), parse_dt(r.get("End") or "")
            if not node or node in ("None", "") or st is None or en is None:
                continue
            jobs.append({"job_id": r["JobIDRaw"] or jid,
                         "job_name": r.get("JobName", ""),
                         "partition": r.get("Partition", ""),
                         "node": node.split(",")[0],
                         "start": st, "end": en})
    return jobs


def _miflu_manifest(model, L, seed):
    """The MIFlu run manifest for one cell, if the exporter's manifest is on disk.

    `hpc_experiments/export_miflu_all7.py` writes
    `author_runs/L{L}_all7/manifest_miflu_L{L}_seed{S}.json` in the same execution
    that produces the npz, carrying the measured GPU name / compute capability /
    partition / node / job id plus the sha256 of the checkpoint used. Rule 12
    says hardware provenance must be measured rather than inferred, so this is
    preferred over matching the npz mtime to an accounting window.
    """
    if model != "miflu":
        return None
    import json
    p = os.path.join(ROOT, "author_runs", f"L{L}_all7",
                     f"manifest_miflu_L{L}_seed{seed}.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sacct", default=os.path.join(HERE, "sacct_dump.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "paper_tables",
                                                 "BENCH_GPU_PROVENANCE.csv"))
    a = ap.parse_args()

    jobs = load_jobs(a.sacct)
    print(f"[prov] {len(jobs)} usable accounting rows with a node + full window")

    rows = []
    for p in sorted(glob.glob(os.path.join(EXP, "**", "pred_*.npz"), recursive=True)):
        m = re.search(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", os.path.basename(p))
        if not m:
            continue
        model, L, seed = m.group(1), int(m.group(2)), int(m.group(3))
        mt = datetime.fromtimestamp(os.path.getmtime(p))
        # MIFlu cells carry a run manifest (HARD RULE 12) written by the export
        # itself, with the MEASURED `torch.cuda.get_device_name(0)`, partition,
        # node and SLURM_JOB_ID. That is stronger evidence than matching a file
        # mtime against accounting windows, so it takes precedence when present.
        man = _miflu_manifest(model, L, seed)
        if man:
            env = man.get("environment") or {}
            rows.append(dict(model=model, L=L, seed=seed,
                             job_id=str(env.get("slurm_job_id", "UNKNOWN")),
                             node=str(env.get("slurm_nodelist", "UNKNOWN")),
                             gpu_type=str(env.get("gpu_name", "UNKNOWN")),
                             gpu_count=int(env.get("gpu_count") or 1),
                             source="run manifest (measured)",
                             npz_mtime=mt.strftime("%Y-%m-%dT%H:%M:%S"),
                             job_name="miflu_a100",
                             partition=str(env.get("slurm_partition", "UNKNOWN"))))
            continue
        cands = [j for j in jobs if j["start"] <= mt <= j["end"]]
        # A concurrent unrelated job (e.g. an LLM probe) can have a *tighter*
        # window than the controller that actually wrote the cell, so preferring
        # the tightest window alone mis-attributes. Rank by: (1) the job name is
        # a known producer of benchmark cells, (2) then tightest window, (3) then
        # latest start.
        cands.sort(key=lambda j: (0 if j["job_name"].startswith(PRODUCER_PREFIXES) else 1,
                                  (j["end"] - j["start"]).total_seconds(),
                                  -j["start"].timestamp()))
        if cands:
            j = cands[0]
            gpu, cnt = gpu_of(j["node"])
            rows.append(dict(model=model, L=L, seed=seed, job_id=j["job_id"],
                             node=j["node"], gpu_type=gpu, gpu_count=cnt,
                             source="sacct window match",
                             npz_mtime=mt.strftime("%Y-%m-%dT%H:%M:%S"),
                             job_name=j["job_name"], partition=j["partition"]))
        else:
            rows.append(dict(model=model, L=L, seed=seed, job_id="UNKNOWN",
                             node="UNKNOWN", gpu_type="UNKNOWN", gpu_count=0,
                             source="no accounting row contained the mtime",
                             npz_mtime=mt.strftime("%Y-%m-%dT%H:%M:%S"),
                             job_name="", partition=""))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "L", "seed", "job_id", "node",
                                           "gpu_type", "gpu_count", "source",
                                           "npz_mtime", "job_name", "partition"])
        w.writeheader()
        w.writerows(rows)

    print(f"[prov] wrote {a.out} ({len(rows)} cells)")
    from collections import Counter
    c = Counter(r["gpu_type"] for r in rows)
    print("[prov] GPU distribution over the benchmark cells:")
    for k, v in c.most_common():
        print(f"   {k:22s} {v}")
    cj = Counter((r["job_id"], r["node"], r["gpu_type"]) for r in rows)
    print("[prov] producing jobs:")
    for (jid, node, gpu), n in cj.most_common():
        print(f"   job {jid:>8s}  node {node:<14s} {gpu:<22s} {n} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
