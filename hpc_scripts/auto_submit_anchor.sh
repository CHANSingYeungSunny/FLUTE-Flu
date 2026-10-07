#!/bin/bash
# Serial auto-submit for the GPT4TS anchor probe (paper window first, then control966).
# stingy QOS allows at most ONE pending job, so we must block until the previous
# jobid has LEFT the queue before submitting the next.
#
# FIX applied here (learned from the L=36/48/60 run): after sbatch, first wait
# until the jobid APPEARS in squeue (Slurm accounting lags several seconds),
# THEN wait until it DISAPPEARS. Polling only for disappearance immediately after
# sbatch sees an empty queue, wrongly concludes "finished", and the next submit
# dies with QOSMaxSubmitJobPerUserLimit.
cd /home/sychan552/scratch/CHATTIME/Chattime

for W in paper control966; do
  # Don't submit while any other miflu/anchor job is still in the queue
  while squeue -u sychan552 2>/dev/null | grep -Eq 'miflu_pa|anchor'; do
    sleep 60
  done

  echo "[anchor] submitting window=$W at $(date)"
  OUT=$(ANCHOR_WINDOW=$W sbatch scripts/submit_anchor_gpt4ts.sh)
  echo "[anchor] $OUT"
  JOBID=$(echo "$OUT" | awk '/Submitted batch job/{print $4}')
  echo "[anchor] window=$W jobid=$JOBID"

  # Step 1: wait until the jobid APPEARS in squeue (max ~2 min)
  for i in $(seq 1 24); do
    if squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; then
      echo "[anchor] job $JOBID visible in queue (attempt $i)"
      break
    fi
    sleep 5
  done

  # Step 2: wait until the jobid DISAPPEARS (finished)
  while squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; do
    sleep 60
  done
  echo "[anchor] window=$W (job $JOBID) finished at $(date)"
  sleep 10
done
echo "[anchor] both windows done."
