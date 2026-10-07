#!/bin/bash
# Stage 5 A2 ??targeted top-up dispatcher (2026-09-26 takeover).
# Purpose: fill ONLY the missing no-text (no_multi) seeds 43/44 for L in
# 24 36 48 60. seed 42 is already fitted and its locked checkpoint exists, so
# the corrected resume guard in train_ablation.py will skip it.
# All other 28 fits are COMPLETE and are NOT touched.
#
# Ownership lock: /scratch/sychan552/a2_stage5/results/stage5/logs/EXEC_LOCK
# This dispatcher is the ONLY process allowed to submit stage-5 jobs.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
LOG=results/stage5/logs/dispatch_log.txt
LOCK=results/stage5/logs/EXEC_LOCK
mkdir -p results/stage5/logs

if [ -e "$LOCK" ] && ! grep -q "dispatcher_notext_topup" "$LOCK" 2>/dev/null; then
  echo "[topup] ABORT: lock $LOCK exists and is not owned by this script:" >&2
  cat "$LOCK" >&2
  exit 9
fi
cat > "$LOCK" <<EOF
owner=dispatcher_notext_topup
pid=$$
host=$(hostname)
started_utc=$(date -u +%FT%TZ)
scope=notext L=24,36,48,60 seeds 43,44 (seed 42 already complete)
note=sole submitter for stage-5 A2 jobs; delete only when this script has exited
EOF

echo "[topup] dispatcher started $(date -u +%FT%TZ) pid=$$" | tee -a "$LOG"

submit_one() {
  local M="$1" L="$2" tries=0 out jid
  while : ; do
    tries=$((tries+1))
    out=$(sbatch --export=ALL,MODEL="$M",L="$L" recovery/stage5/run_task.sh 2>&1)
    jid=$(printf '%s\n' "$out" | sed -n 's/.*Submitted batch job \([0-9][0-9]*\).*/\1/p' | head -1)
    if [ -n "$jid" ]; then printf '%s' "$jid"; return 0; fi
    if [ $((tries % 10)) -eq 1 ]; then
      echo "[topup] waiting to submit $M L=$L (tries=$tries) at $(date -u +%FT%TZ)" >> "$LOG"
    fi
    if [ "$tries" -ge 360 ]; then printf ''; return 1; fi
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
    sleep 15
  done
}

for L in 24 36 48 60; do
  jid=$(submit_one notext "$L")
  if [ -z "$jid" ]; then
    echo "[topup] GAVE UP on notext L=$L" | tee -a "$LOG"; continue
  fi
  echo "[topup] submitted notext L=$L job=$jid at $(date -u +%FT%TZ)" | tee -a "$LOG"
  wait_done "$jid"
  st2=$(sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
  el=$(sacct -j "$jid" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
  echo "[topup] job=$jid notext L=$L state=$st2 elapsed=$el" | tee -a "$LOG"
done
echo "[topup] queue finished at $(date -u +%FT%TZ)" | tee -a "$LOG"
rm -f "$LOCK"
echo "[topup] lock released"
