#!/bin/bash
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
cd "$Q" || exit 1
echo "=== job table ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.11M %.21S'
echo
echo "=== writer cycles (last 12 events) ==="
grep -E "WRITER:|FINALISATION PASS|TASK (DONE|SKIPPED) +final_|no-new-cells" queue_events.log | tail -12
echo
echo "=== finalise_status.json ==="
cat finalise_status.json 2>/dev/null
echo
echo "=== table mtimes ==="
ls -l --time-style=+%F' '%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" \
  "$A/paper_tables/BENCH_EFFICIENCY.csv" "$A/paper_tables/BENCH_CRPS_WIS.csv" 2>/dev/null
echo "  figures: $(ls -1 "$A/results/bench_figures" 2>/dev/null | wc -l)"
echo "  miflu markers: $(ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify | wc -l)"
echo
echo "=== queue histogram ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-26s %d\n", k, c[k]}' master_queue.tsv | sort
echo
echo "=== Qwen lane + MIFlu lanes ==="
for j in 720068 719833 719835 720052; do
  printf '  %-8s ' "$j"
  scontrol show job "$j" 2>/dev/null | tr ' ' '\n' \
    | grep -E '^(JobName|JobState|Partition|TimeLimit|StartTime)=' | tr '\n' ' '
  echo
done
