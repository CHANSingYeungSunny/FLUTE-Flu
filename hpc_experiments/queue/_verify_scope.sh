#!/bin/bash
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$Q" || exit 1
echo "=== is_mine priority-scope hook present? ==="
grep -n 'if \[ -n "${ONLY_PRI}" \]; then return 0; fi' master_controller_v2.sh
grep -n 'priority-scoped lane' master_controller_v2.sh
echo "  (both lines must be present: the first makes a P0 lane own all 22 cells)"
echo
echo "=== P0 lane scope simulation: which rows would it pick? ==="
sed -n '/^is_mine()/,/^}/p' master_controller_v2.sh | sed -n '1,26p'
echo
echo "=== 720083 / 720070 price after a short wait ==="
sleep 25
for j in 720083 720070; do
  printf '  %-8s ' "$j"
  scontrol show job "$j" 2>/dev/null | tr ' ' '\n' \
    | grep -E '^(JobState|Partition|TimeLimit|StartTime)=' | tr '\n' ' '
  echo
done
echo
echo "=== markers ==="
ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify | wc -l
