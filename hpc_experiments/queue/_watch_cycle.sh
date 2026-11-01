#!/bin/bash
# _watch_cycle.sh -- poll until the proof table mtime moves, then print the proof.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
T="$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
cd "$Q" || exit 1

m0=$(stat -c %Y "$T")
echo "  baseline mtime: $(date -d @$m0 '+%F %T')"
for i in $(seq 1 90); do
  m=$(stat -c %Y "$T")
  if [ "$m" != "$m0" ]; then
    echo "  TABLE REWRITTEN -> $(date -d @$m '+%F %T') (was $(date -d @$m0 '+%F %T'))"
    m0=$m
    break
  fi
  sleep 10
done
echo "  current: $(ls -l --time-style=+%F' '%H:%M:%S "$T")"
echo
echo "=== finalise_status.json ==="
cat finalise_status.json 2>/dev/null
echo
echo "=== writer log (cycle 2) ==="
tail -6 "$(ls -t slurm-W3-*.out 2>/dev/null | head -1)" 2>/dev/null
echo
echo "=== F3/f4 log tail ==="
tail -6 finalise/final_analysis_chain.log 2>/dev/null
echo "---"
tail -8 finalise/final_verify_bench.log 2>/dev/null
echo
echo "=== figures ==="
ls -1 "$A/results/bench_figures" 2>/dev/null | wc -l
ls -1t "$A/results/bench_figures" 2>/dev/null | head -5
