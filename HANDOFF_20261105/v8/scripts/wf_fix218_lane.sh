#!/bin/bash
# wf_fix218 shard runner — completes the 218 empty walk-forward cells that were
# SKIPPED after 2 failed attempts with reason "CUDA busy/unavailable on this node".
# It runs the SAME task ids / kind / model / L / seed as the original queue rows,
# i.e. the legacy WF N=3 (seeds 42/43/44) protocol that the 802 already-valid
# cells belong to. Output NPZ go to the canonical WF_ROOT so wf_recompute.py
# sees one panel; provenance is recorded separately by _provenance in this dir.
set -u
ROOT=/gpfs1/scratch/sychan552/stage5_a2_durable
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
DIR=$ROOT/code/queue/wf_fix218
TODO=$DIR/todo.tsv
LOG=$DIR/logs
SHARD=${1:-0}
NSHARD=${2:-1}
mkdir -p "$LOG"
echo "$(date -u +%FT%TZ) LANE_START shard=$SHARD nshard=$NSHARD host=$(hostname)" >> "$LOG/shard${SHARD}.log"
i=0
while IFS=$'\t' read -r task kind model L seed rest; do
  [ -n "$task" ] || continue
  [ "$task" = "task_id" ] && continue
  i=$((i+1))
  if [ $(( (i-1) % NSHARD )) -ne "$SHARD" ]; then continue; fi
  echo "$(date -u +%FT%TZ) START $task" >> "$LOG/shard${SHARD}.log"
  "$PY" -u "$ROOT/code/queue/master_task_v2.py" run --task-id "$task" --kind "$kind" \
     --model "$model" --L "$L" --seed "$seed" --env hpc --require-a100 1 \
     >> "$LOG/shard${SHARD}.log" 2>&1
  rc=$?
  echo "$(date -u +%FT%TZ) END $task rc=$rc" >> "$LOG/shard${SHARD}.log"
  printf '%s\t%s\n' "$task" "$rc" >> "$LOG/results_shard${SHARD}.tsv"
done < "$TODO"
echo "$(date -u +%FT%TZ) LANE_END shard=$SHARD processed=$i" >> "$LOG/shard${SHARD}.log"
