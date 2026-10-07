#!/bin/bash
# Sequential dispatcher for Stage 5 A2 (stingy QOS: MaxSubmitJobsPerUser=1).
# Strategy (robust to SLURM's stdout "Last update" noise and to the short window
# where a freshly submitted job is not yet registered):
#   * submit each task, retrying while the QOS submit-limit rejects us;
#   * wait for completion via `sacct -X` (allocation-only, terminal states).
# Run inside tmux so it survives ssh disconnects.
set -uo pipefail
cd /scratch/sychan552/a2_stage5
LOG=results/stage5/logs/dispatch_log.txt
mkdir -p results/stage5/logs

submit_one() {
  local M="$1" L="$2" tries=0 out jid
  while : ; do
    tries=$((tries+1))
    out=$(sbatch --export=ALL,MODEL="$M",L="$L" recovery/stage5/run_task.sh 2>&1)
    jid=$(printf '%s\n' "$out" | sed -n 's/.*Submitted batch job \([0-9][0-9]*\).*/\1/p' | head -1)
    if [ -n "$jid" ]; then
      printf '%s' "$jid"
      return 0
    fi
    # Only the QOS submit limit should reject us (one job at a time); keep retrying.
    if [ $((tries % 10)) -eq 1 ]; then
      echo "[dispatch] waiting to submit $M L=$L (tries=$tries) at $(date -u +%FT%TZ)" >> "$LOG"
    fi
    if [ "$tries" -ge 360 ]; then
      echo "[dispatch] GAVE UP on $M L=$L after $tries tries at $(date -u +%FT%TZ)" >> "$LOG"
      printf ''
      return 1
    fi
    sleep 30
  done
}

wait_done() {
  local jid="$1" st
  while : ; do
    st=$(sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
    case "$st" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|BOOT_FAIL|DEADLINE|PREEMPTED)
        return 0 ;;
    esac
    sleep 20
  done
}

for spec in "$@"; do
  M="${spec%%:*}"
  L="${spec##*:}"

  jid=$(submit_one "$M" "$L")
  if [ -z "$jid" ]; then
    echo "[dispatch] GAVE UP on $M L=$L at $(date -u +%FT%TZ)" | tee -a "$LOG"
    continue
  fi
  echo "[dispatch] submitted $M L=$L job=$jid at $(date -u +%FT%TZ)" | tee -a "$LOG"

  wait_done "$jid"

  st2=$(sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
  el=$(sacct -j "$jid" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
  echo "[dispatch] job=$jid $M L=$L state=$st2 elapsed=$el" | tee -a "$LOG"
done
echo "[dispatch] queue finished at $(date -u +%FT%TZ)" | tee -a "$LOG"
