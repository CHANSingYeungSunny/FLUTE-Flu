#!/bin/bash
# Stage the analysis pipeline ON THE CLUSTER so finalisation (F1-F5) can run
# unattended. The HPC has the cells (expanded_runs/, author_runs/) but had NO
# analysis scripts and no paper_tables/, so a queue that "trains and stops"
# would leave npz on disk and every table untouched.
#
# Layout created at $R/analysis (a mini repo root):
#   scripts/        <- the local scripts/*.py (uploaded by the caller)
#   hpc_results  -> ../expanded_runs        (what the analysis scripts glob)
#   author_runs  -> ../author_runs
#   data         -> ../data
#   paper_tables/   (output; the morning deliverable)
#   figures/        (output)
set -uo pipefail
R=/gpfs1/home/sychan552/stage5_a2_durable
A=$R/analysis

mkdir -p "$A/scripts" "$A/paper_tables" "$A/figures" "$A/hpc_results_x"
[ -e "$A/hpc_results" ] || ln -s "$R/expanded_runs" "$A/hpc_results"
[ -e "$A/author_runs" ] || ln -s "$R/author_runs" "$A/author_runs"
[ -e "$A/data" ] || ln -s "$R/data" "$A/data"
rmdir "$A/hpc_results_x" 2>/dev/null || true

echo "=== staged layout ==="
ls -l "$A" | sed -n '1,12p'
echo "scripts: $(ls -1 "$A"/scripts/*.py 2>/dev/null | wc -l) files"
echo "cells visible via hpc_results: $(ls -1 "$A"/hpc_results 2>/dev/null | wc -l)"
echo "npz under hpc_results/*/pred_*.npz: $(ls -1 "$A"/hpc_results/*/pred_*.npz 2>/dev/null | wc -l)"
echo "author_runs all7 npz: $(ls -1 "$A"/author_runs/L*_all7/*.npz 2>/dev/null | wc -l)"
