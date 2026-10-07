#!/bin/bash
# =============================================================================
# Serial auto-submit for the MIFlu component-diagnosis sweep (all on the
# CONFIRMED paper window = OURS rows 20-985).
#
# Runs three ablation arms, cheapest/most-informative first:
#   1. no_multi  (LoRA only, no text)  ~13 min  -> is LoRA working?
#   2. no_lora   (text only, no LoRA)  ~35 min  -> is the textual embedder working?
#   3. full      (MIFlu, both)         ~35 min  -> re-confirm the 1.952 deficit
# Compare against Table VIII: GPT4TS 1.925 | LoRA-only 1.647 | text-only 1.570 | full 1.436.
#
# stingy QOS allows at most ONE pending job -> must block until the previous jobid
# has LEFT the queue before submitting the next.
#
# FIX (learned the hard way): after sbatch, first wait until the jobid APPEARS in
# squeue (Slurm accounting lags seconds), THEN wait until it DISAPPEARS. Polling
# only for disappearance right after sbatch sees an empty queue, wrongly concludes
# "finished", and the next submit dies with QOSMaxSubmitJobPerUserLimit.
# =============================================================================
cd /home/sychan552/scratch/CHATTIME/Chattime

#        variant    expected-runtime note
ARMS="no_multi no_lora full"

for V in $ARMS; do
  # Don't submit while any other job of ours is still in the queue
  while squeue -u sychan552 2>/dev/null | grep -Eq 'miflu_pa|anchor'; do
    sleep 60
  done

  echo "[diag] submitting variant=$V window=paper reps=3 at $(date)"
  OUT=$(ANCHOR_VARIANT=$V ANCHOR_WINDOW=paper ANCHOR_REPS=3 \
        sbatch scripts/submit_anchor_gpt4ts.sh)
  echo "[diag] $OUT"
  JOBID=$(echo "$OUT" | awk '/Submitted batch job/{print $4}')
  echo "[diag] variant=$V jobid=$JOBID"

  # Step 1: wait until the jobid APPEARS in squeue (max ~2 min)
  for i in $(seq 1 24); do
    if squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; then
      echo "[diag] job $JOBID visible in queue (attempt $i)"
      break
    fi
    sleep 5
  done

  # Step 2: wait until the jobid DISAPPEARS (finished)
  while squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; do
    sleep 60
  done
  echo "[diag] variant=$V (job $JOBID) finished at $(date)"
  sleep 10
done
echo "[diag] all three arms done."
