#!/bin/bash
# =============================================================================
# Serial auto-submit — MIFlu training-recipe sensitivity scan (paper window).
#
# WHY: on the CONFIRMED paper window (OURS rows 20-985) our GPT4TS baseline
# reproduces the paper (1.976 vs 1.925) but MIFlu's own components do not:
#   LoRA-only  -> 2.047 (WORSE than our 1.976 baseline; paper: 1.647)
#   text-only  -> 1.909 (+3.4% only;                    paper: 1.570)
# Both complexity-adding components underperform while the simplest config does
# best => classic signature of UNDER-TRAINING (insufficient epochs) and/or a LoRA
# learning rate that is too small to converge within 20 epochs.
#
# THIS SCAN (cheap probe: single horizon L=24, 3 reps) separates the two causes:
#   A. epochs  = 50, 100          -> does more training unlock the components?
#   B. lora_lr = 0.005, 0.05      -> does LoRA just need a bigger lr? (20 epochs)
# Reference points at L=24 (3 reps, 20 ep, paper window):
#   no_lora_multi  1.980 | no_multi 2.402 | no_lora 2.119 | full = pending
#
# Cost: A ~= 20 + 39 min; B ~= 2 x 8 min  => ~75 min total, serial (stingy QOS
# allows only ONE pending job).
# =============================================================================
cd /home/sychan552/scratch/CHATTIME/Chattime

run_arm () {
  local DESC="$1"; shift
  local EPOCHS="$1"; shift
  local LORA_LR="$1"; shift

  # Wait for the queue to clear before submitting (QOS: max 1 pending job)
  while squeue -u sychan552 2>/dev/null | grep -Eq 'miflu_pa|anchor'; do
    sleep 60
  done

  local LRARG=""
  if [ -n "${LORA_LR}" ]; then LRARG="--lora-lr ${LORA_LR}"; fi

  echo "[sens] submitting: ${DESC} (epochs=${EPOCHS} lora_lr=${LORA_LR:-default}) at $(date)"
  OUT=$(ANCHOR_VARIANT=full ANCHOR_WINDOW=paper ANCHOR_REPS=3 \
        ANCHOR_EXTRA="--horizon 24 --epochs ${EPOCHS} ${LRARG}" \
        sbatch scripts/submit_anchor_gpt4ts.sh)
  echo "[sens] $OUT"
  JOBID=$(echo "$OUT" | awk '/Submitted batch job/{print $4}')
  echo "[sens] jobid=$JOBID"

  # Step 1: wait until the jobid APPEARS in squeue (Slurm accounting lags)
  for i in $(seq 1 24); do
    if squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; then
      echo "[sens] job $JOBID visible (attempt $i)"; break
    fi
    sleep 5
  done

  # Step 2: wait until it DISAPPEARS (finished)
  while squeue -j "$JOBID" 2>/dev/null | grep -q "$JOBID"; do sleep 60; done
  echo "[sens] ${DESC} finished at $(date)"
  sleep 10
}

#      desc                  epochs  lora_lr
run_arm "ep50"               50      ""
run_arm "ep100"              100     ""
run_arm "loralr0.005-ep20"   20      "0.005"
run_arm "loralr0.05-ep20"    20      "0.05"

echo "[sens] sensitivity scan complete."
