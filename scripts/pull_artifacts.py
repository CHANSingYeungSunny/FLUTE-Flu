#!/usr/bin/env python
"""pull_artifacts.py — structured, contamination-free pull of MIFlu journal
evidence artifacts from HPC into the local GOLDEN directory tree.

Maps the HPC per-horizon run dirs (full_H{L}/reps_1_to_10/rep_01/) into the
immutable local structure required by the Golden Rule:
  results/ili/journal_evidence/full/horizon_L{L}/rep_01/
    checkpoints/best_model_full_L{L}_rep01.pt
    predictions_full_L{L}_paper_protocol.csv
    metrics.csv
    figures/
Each file is fetched by explicit name (no glob), so a missing artifact fails
loudly instead of silently contaminating the tree.
"""
import os
import subprocess
import sys

HPC_USER = "sychan552@burgundy.hpc.cityu.edu.hk"
HPC_BASE = "/scratch/sychan552/CHATTIME/Chattime/hpc_results/journal_evidence"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_BASE = os.path.join(PROJECT_ROOT, "results", "ili", "journal_evidence")
VARIANT = "full"
HORIZONS = [24, 36, 48, 60]


def scp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r = subprocess.run(["scp", "-o", "BatchMode=yes", src, dst],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! scp FAILED {src}\n{r.stderr}", file=sys.stderr)
        raise SystemExit(1)
    sz = os.path.getsize(dst)
    print(f"  pulled -> {os.path.relpath(dst)}  ({sz:,} bytes)")


def main():
    for L in HORIZONS:
        src_rep = f"{HPC_BASE}/{VARIANT}_H{L}/reps_1_to_10/rep_01"
        dst_rep = os.path.join(LOCAL_BASE, VARIANT, f"horizon_L{L}", "rep_01")
        print(f"[L={L}] {src_rep}  ->  {os.path.relpath(dst_rep)}")
        scp(f"{HPC_USER}:{src_rep}/checkpoints/best_model_L{L}.pt",
            os.path.join(dst_rep, "checkpoints", f"best_model_{VARIANT}_L{L}_rep01.pt"))
        scp(f"{HPC_USER}:{src_rep}/predictions_miflu_L{L}_paper_protocol.csv",
            os.path.join(dst_rep, f"predictions_{VARIANT}_L{L}_paper_protocol.csv"))
        scp(f"{HPC_USER}:{src_rep}/metrics.csv",
            os.path.join(dst_rep, "metrics.csv"))
        os.makedirs(os.path.join(dst_rep, "figures"), exist_ok=True)
    print("PULL COMPLETE")


if __name__ == "__main__":
    main()
