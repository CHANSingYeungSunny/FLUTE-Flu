#!/bin/bash
set -uo pipefail
for j in 720068 720064 719835 719833 720052; do
  printf '%-8s ' "$j"
  scontrol show job "$j" 2>/dev/null | tr ' ' '\n' \
    | grep -E '^(JobName|JobState|Partition|TimeLimit|StartTime|Reason)=' | tr '\n' ' '
  echo
done
echo "--- sacct 720068 ---"
sacct -j 720068 -o JobID,JobName,State,ExitCode,Elapsed 2>/dev/null
echo "--- sacct 720064 ---"
sacct -j 720064 -o JobID,JobName,State,ExitCode 2>/dev/null
echo "--- runner map ---"
for f in runner_s0.job runner_s1.job runner_sw.job runner_scpu.job; do
  printf '%-16s %s\n' "$f" "$(tr '\n' ' ' < "$f" 2>/dev/null)"
done
