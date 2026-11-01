#!/bin/bash
# What analysis capability does the HPC already have? Finalisation (F1-F5) has to
# run somewhere that has BOTH the cells and the analysis scripts.
set -uo pipefail
R=/gpfs1/home/sychan552/stage5_a2_durable
CODE=$R/code

echo "=== analysis scripts anywhere under \$R (depth 3) ==="
for n in analysis_expanded analysis_postprocess seasonal_naive_baseline plot_bench plot_pareto \
         verify_bench_unchanged verify_miflu_oracle import_miflu_predictions eval_windows; do
  printf '%-28s ' "$n"
  found=$(find "$R" -maxdepth 3 -name "$n.py" 2>/dev/null | head -3 | tr '\n' ' ')
  echo "${found:-MISSING}"
done

echo
echo "=== paper_tables / hpc_results present? ==="
ls -ld "$R/paper_tables" "$R/hpc_results" "$CODE/paper_tables" 2>/dev/null
echo "expanded_runs cells: $(ls -1 "$R"/expanded_runs 2>/dev/null | wc -l) dirs"
echo "author_runs L*_all7 npz: $(ls -1 "$R"/author_runs/L*_all7/*.npz 2>/dev/null | wc -l)"

echo
echo "=== does the HPC have a scripts/ tree at all? ==="
ls -d "$R"/code/scripts "$R"/scripts 2>/dev/null || echo "no scripts/ dir"
