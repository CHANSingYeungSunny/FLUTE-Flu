#!/bin/bash
# Explicit adapter: only after the 1120 phase is validated complete, hand the
# legacy stage5_a2_durable queue (Table VI / walk-forward TODOs) to ONE driver.
set -u
R=/gpfs1/scratch/sychan552/trackB_20261104
ALL="$R/all"
Q=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
mkdir -p "$ALL/logs"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ALL/logs/post_all_v2.log"; }
START=$(date +%s)

# 1. wait for validated completion (not a self-reported sentinel)
while [ ! -f "$ALL/phase.done" ]; do
  if [ $(( $(date +%s) - START )) -gt 345600 ]; then log "POST_ALL_TIMEOUT waiting phase.done"; exit 0; fi
  sleep 600
done
log "PHASE_DONE_SEEN"

# 2. snapshot the legacy queue TODOs as evidence (no invention)
"$PY" - <<'PY' >> "$ALL/logs/post_all_v2.log" 2>&1
import csv, collections, os
q="/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/master_queue.tsv"
out="/gpfs1/scratch/sychan552/trackB_20261104/all/LEGACY_TODO.tsv"
rows=[]
with open(q,encoding="utf-8") as f:
    rd=csv.DictReader(f,delimiter="\t")
    for r in rd:
        if r.get("state")=="TODO": rows.append(r)
with open(out,"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["task_id","kind","priority","state"])
    for r in rows: w.writerow([r.get("task_id"),r.get("kind"),r.get("priority"),r.get("state")])
c=collections.Counter(r.get("kind") for r in rows)
print("LEGACY_TODO_TOTAL",len(rows),dict(c))
PY
cat "$ALL/LEGACY_TODO.tsv" 2>/dev/null | wc -l >> "$ALL/logs/post_all_v2.log"

# 3. do not start while any Track-B GPU lane is still alive
while squeue -u "$USER" -h -n trackB_v2_all_l0,trackB_v2_all_l1,trackB_v2_all_l2,trackB_v2_core_l0,trackB_v2_core_l1 2>/dev/null | grep -q .; do
  log "WAIT_TRACKB_GPU_LANES"; sleep 600
done

# 4. one-shot guard: submit the legacy driver exactly once
GUARD="$ALL/post_all_v2.submitted.d"
if mkdir "$GUARD" 2>/dev/null; then
  log "SUBMIT_LEGACY_DRIVER persistent_driver.sh (one shot)"
  (cd "$Q" && sbatch persistent_driver.sh) >> "$ALL/logs/post_all_v2.log" 2>&1 \
    && log "LEGACY_DRIVER_SUBMITTED" || log "LEGACY_DRIVER_SUBMIT_FAILED"
  echo "$(date -u +%FT%TZ)" > "$GUARD/timestamp"
else
  log "LEGACY_DRIVER_ALREADY_SUBMITTED (guard present)"
fi
log "POST_ALL_DONE"
