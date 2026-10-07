#!/bin/bash
# Serial auto-submit for L=48/60 under stingy QOS (max 1 pending job).
# FIX (vs previous version): after sbatch, first WAIT until the jobid actually
# appears in squeue (Slurm accounting lags a few seconds), THEN wait until it
# disappears (COMPLETED). The old version polled immediately, saw an empty
# squeue, concluded "finished", and submitted the next job -> QOSMaxSubmitJobPerUserLimit.
cd /home/sychan552/scratch/CHATTIME/Chattime

for L in 48 60; do
  # Wait until no miflu_pa job is in the queue before submitting
  while squeue -u sychan552 2>/dev/null | grep -q miflu_pa; do
    sleep 60
  done

  echo "[auto] submitting L=$L at $(date)"
  OUT=$(MIFLU_HORIZON=$L sbatch scripts/submit_miflu_paper_protocol.sh)
  echo "[auto] $OUT"
  JOBID=$(echo "$OUT" | awk '/Submitted batch job/{print $4}')
  echo "[auto] L=$L jobid=$JOBID"

  # Step 1: wait until the jobid APPEARS in squeue (max ~2 min)
  for i in $(seq 1 24); do
    if squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; then
      echo "[auto] L=$L job $JOBID visible in queue (attempt $i)"
      break
    fi
    sleep 5
  done

  # Step 2: wait until the jobid DISAPPEARS from squeue (finished)
  while squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; do
    sleep 60
  done
  echo "[auto] L=$L (job $JOBID) finished at $(date)"
  sleep 10
done
echo "[auto] all L=48/60 done."
