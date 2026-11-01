#!/bin/bash
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
echo "=== table mtime BEFORE ==="
ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
echo
echo "=== MIFlu contamination audit (report only) ==="
"$PY" audit_miflu_cells.py 2>&1 | tail -30
echo
echo "=== markers present? ==="
ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify 2>/dev/null | wc -l
ls -d /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify 2>/dev/null || echo "no .miflu_verify dir"
