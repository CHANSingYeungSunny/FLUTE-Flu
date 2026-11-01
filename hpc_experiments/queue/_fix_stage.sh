#!/bin/bash
# Fix the staged layout: the analysis scripts glob hpc_results/expanded_runs/*,
# so `hpc_results` must be a DIRECTORY containing a symlink, not a symlink to
# expanded_runs itself. Also report what reference inputs are still missing.
set -uo pipefail
R=/gpfs1/home/sychan552/stage5_a2_durable
A=$R/analysis
rm -f "$A/hpc_results"
mkdir -p "$A/hpc_results"
[ -e "$A/hpc_results/expanded_runs" ] || ln -s "$R/expanded_runs" "$A/hpc_results/expanded_runs"
[ -e "$A/hpc_results/expanded_runs_v100_nlinear" ] || ln -s "$R/expanded_runs_v100_nlinear" "$A/hpc_results/expanded_runs_v100_nlinear"

echo "=== layout ==="
ls -l "$A/hpc_results"
echo "cells: $(ls -1 "$A"/hpc_results/expanded_runs/*/pred_*.npz 2>/dev/null | wc -l)"
echo "paper_tables csvs: $(ls -1 "$A"/paper_tables/*.csv 2>/dev/null | wc -l)"
ls -1 "$A"/paper_tables 2>/dev/null | head -12

echo
echo "=== what analysis_expanded.py reads for 'family' ==="
grep -n "family" "$A/scripts/analysis_expanded.py" | head -10
grep -rn "BENCHMARK_MODEL_ROSTER\|_FAMILY\|families" "$A/scripts/analysis_expanded.py" "$A/scripts/recipes.py" 2>/dev/null | head -10
