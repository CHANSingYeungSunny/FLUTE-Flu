#!/bin/bash
# MEASURE, don't assume: does `scontrol requeue $SLURM_JOB_ID` on `tiny`
#   (a) keep the same job id, (b) reset `Elapsed` to 0, (c) give a fresh wall clock?
# That is the arithmetic the 12 h chain rests on. Runs twice, then exits.
set -uo pipefail
TAG=/gpfs1/home/sychan552/stage5_a2_durable/code/queue/requeue_test
mkdir -p "$TAG"
N=$(( $(cat "$TAG/count" 2>/dev/null || echo 0) + 1 ))
echo "$N" > "$TAG/count"
{
  echo "=== generation $N  job=${SLURM_JOB_ID} start=$(date '+%F %T')  TimeLimit=$(scontrol show job "$SLURM_JOB_ID" | tr ' ' '\n' | sed -n 's/^TimeLimit=//p')"
  sacct -j "$SLURM_JOB_ID" -n -X -o JobID,State,Elapsed,Timelimit
} >> "$TAG/log"
sleep 75
{
  echo "generation $N before-requeue elapsed: $(sacct -j "$SLURM_JOB_ID" -n -X -o Elapsed | tr -d ' ')"
  echo "generation $N submit-time: $(scontrol show job "$SLURM_JOB_ID" | tr ' ' '\n' | sed -n 's/^SubmitTime=//p')"
} >> "$TAG/log"
if [ "$N" -lt 2 ]; then
  echo "generation $N -> scontrol requeue" >> "$TAG/log"
  scontrol requeue "$SLURM_JOB_ID" >> "$TAG/log" 2>&1
  exit 0
fi
{
  echo "generation $N final: $(sacct -j "$SLURM_JOB_ID" -n -X -o State,Elapsed | tr -s ' ')"
  echo "SAME_JOB_ID=$SLURM_JOB_ID"
} >> "$TAG/log"
