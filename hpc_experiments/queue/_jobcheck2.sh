#!/bin/bash
set -uo pipefail
for j in 720070 720068 719835 719833 720052 720004; do
  printf '%-8s ' "$j"
  scontrol show job "$j" 2>/dev/null | tr ' ' '\n' \
    | grep -E '^(JobName|JobState|Partition|TimeLimit|StartTime)=' | tr '\n' ' '
  echo
done
echo "--- squeue (may be cached) ---"
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.21S'
echo "--- runner map ---"
for f in runner_s0.job runner_s1.job runner_s1.qwen.job runner_sw.job runner_scpu.job; do
  printf '%-20s %s\n' "$f" "$(tr '\n' ' ' < "$f" 2>/dev/null)"
done
