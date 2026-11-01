#!/bin/bash
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }
echo "=== successor watcher 720102 ==="
printf '  state=%s part=%s wall=%s start=%s\n' "$(st 720102 JobState)" "$(st 720102 Partition)" \
  "$(st 720102 TimeLimit)" "$(st 720102 StartTime)"
echo
echo "=== successor.log ==="
cat successor.log 2>/dev/null || echo "  (none yet)"
echo
echo "=== sentinel / p0 record ==="
ls -l SUCCESSOR_SUBMITTED 2>/dev/null || echo "  SUCCESSOR_SUBMITTED: absent (not fired)"
printf '  P0_LANE.job = %s\n' "$(cat P0_LANE.job 2>/dev/null)"
echo
echo "=== jobs ==="
squeue -u sychan552 -o '%.8i %.10P %.18j %.2t %.21S'
