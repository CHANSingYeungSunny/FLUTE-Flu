#!/bin/bash
# Remote-persistent auto-submit for L=60 after L=48 (job 506643) COMPLETES.
# Runs on the HPC LOGIN NODE (setsid), fully independent of the user's local
# machine / VPN. Uses `sacct` (not `squeue -j`) to detect completion, because
# this cluster's squeue misbehaves with -j on some login nodes.
set -u
LOG=/home/sychan552/scratch/CHATTIME/Chattime/logs/remote_autosubmit_L60.log
PIDFILE=/home/sychan552/scratch/CHATTIME/Chattime/logs/remote_autosubmit_L60.pid
WATCH_JOB=506643
echo "$$" > "$PIDFILE"
log(){ echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
log "REMOTE_AUTOSUBMIT_L60 v2 started (pid $$); watching job $WATCH_JOB via sacct."

while true; do
  # Detect completion via sacct (reliable across login nodes)
  STATE=$(sacct -j "$WATCH_JOB" -o State -n -X 2>/dev/null | head -1)
  if [ "$STATE" = "COMPLETED" ] || [ "$STATE" = "FAILED" ] || [ "$STATE" = "CANCELLED" ] || [ "$STATE" = "TIMEOUT" ]; then
    if [ "$STATE" = "COMPLETED" ]; then
      log "L=48 ($WATCH_JOB) COMPLETED -> submitting L=60."
      OUT=$(cd /home/sychan552/scratch/CHATTIME/Chattime && MIFLU_HORIZON=60 sbatch submit_miflu_paper_protocol.sh 2>&1)
      log "SUBMIT RESULT: $OUT"
      if echo "$OUT" | grep -q 'Submitted batch job'; then
        NJOB=$(echo "$OUT" | grep -oP 'Submitted batch job \K\d+')
        log "L=60 submitted as job $NJOB. DONE."
        break
      else
        log "SUBMIT UNEXPECTED (retry 60s): $OUT"
        sleep 60
      fi
    else
      log "L=48 ended with state=$STATE (not COMPLETED). Aborting auto-submit."
      break
    fi
  else
    log "L=48 state='${STATE:-unknown}' (not done yet). sleep 90s."
    sleep 90
  fi
done
log "REMOTE_AUTOSUBMIT_L60 v2 exiting."
rm -f "$PIDFILE"
