#!/bin/bash
# PROOF THAT F3 EXECUTES AND REWRITES A TABLE.
# Runs the real finalise task through `master_task.py` exactly as the controller
# would (same argv, same code path) and shows the mtime of the table changing.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$QDIR" || exit 1

echo "=== P4 rows in the queue ==="
awk -F'\t' 'NR>1 && $6=="P4"{printf "  %-24s kind=%-9s env=%-4s state=%s\n", $1, $2, $7, $8}' master_queue.tsv

echo
echo "=== table mtime BEFORE ==="
for t in BENCH_MSE_BY_MODEL_L.csv BENCH_EFFICIENCY.csv BENCH_CRPS_WIS.csv; do
  [ -f "$A/paper_tables/$t" ] && printf '  %-28s %s  %s bytes\n' "$t" "$(date -r "$A/paper_tables/$t" '+%F %T')" "$(stat -c %s "$A/paper_tables/$t")"
done

echo
echo "=== running the real task: master_task.py run --task-id final_analysis_chain --kind finalise ==="
nice -n 10 timeout 1800 "$PY" -u master_task.py run \
    --task-id final_analysis_chain --kind finalise --env hpc --require-a100 0
echo "exit=$?"

echo
echo "=== table mtime AFTER ==="
for t in BENCH_MSE_BY_MODEL_L.csv BENCH_EFFICIENCY.csv BENCH_CRPS_WIS.csv; do
  [ -f "$A/paper_tables/$t" ] && printf '  %-28s %s  %s bytes\n' "$t" "$(date -r "$A/paper_tables/$t" '+%F %T')" "$(stat -c %s "$A/paper_tables/$t")"
done
echo
echo "=== figures written by plot_bench/plot_pareto ==="
ls -1 "$A/figures" 2>/dev/null | wc -l
echo
echo "=== finalise record ==="
tail -20 finalise/final_analysis_chain.log 2>/dev/null
