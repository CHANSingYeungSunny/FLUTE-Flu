#!/bin/bash
# Cleanly restart the Stage 6 pipeline: kill leftovers, then relaunch detached.
cd /scratch/sychan552/a2_stage5 || exit 1

for p in $(pgrep -f 'pipeline_stage6.sh' 2>/dev/null); do
  [ "$p" = "$$" ] && continue
  kill -9 "$p" 2>/dev/null && echo "killed stale pipeline pid $p"
done
sleep 2
echo "remaining before start: $(pgrep -c -f 'pipeline_stage6.sh' 2>/dev/null || echo 0)"

nohup setsid bash recovery/stage6/pipeline_stage6.sh \
  >> results/stage6/logs/pipeline_nohup.log 2>&1 < /dev/null &
disown
sleep 3
echo "--- live pipelines now ---"
pgrep -af 'pipeline_stage6.sh' 2>/dev/null
