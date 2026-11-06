#!/bin/bash
# Track-B v2 controller. Singleton via mkdir; completion by VALIDATED cells, not file counts.
set -u
PHASE="$1"
R=/gpfs1/scratch/sychan552/trackB_20261104
if [ "$PHASE" = "core" ]; then
  BASE="$R/core"; NLANES=2; TOTAL=160; JOBPFX=trackB_v2_core_l; CELLS="$R/core/cells.tsv"
else
  BASE="$R/all"; NLANES=3; TOTAL=1120; JOBPFX=trackB_v2_all_l; CELLS="$R/all/cells_all.tsv"
fi
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HELPER="$R/cellok.py"
LOCK="$BASE/controller_v2.lock.d"
mkdir -p "$BASE/logs"

# --- singleton (mkdir is atomic on GPFS; flock is NOT a cross-node mutex here) ---
if ! mkdir "$LOCK" 2>/dev/null; then
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))
  if [ "$age" -lt 7200 ]; then echo "$(date -u +%FT%TZ) CONTROLLER_ALREADY_RUNNING age=$age"; exit 0; fi
  echo "$(date -u +%FT%TZ) STALE_CONTROLLER_LOCK age=$age -> taking over"; rm -rf "$LOCK"
  mkdir "$LOCK" 2>/dev/null || exit 0
fi
echo "$$ $(hostname) ${SLURM_JOB_ID:-none} $(date -u +%FT%TZ)" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT INT TERM

log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$BASE/logs/controller_v2.log"; }
START=$(date +%s)
WALL_LIMIT=${CONTROLLER_WALL_SECONDS:-82800}   # 23h; renew 1h before wall

quota_used() { /usr/lpp/mmfs/bin/mmlsquota --block-size G -u "$USER" 2>/dev/null | awk '$1=="scratch"{print $3}'; }

log "CONTROLLER_START phase=$PHASE total=$TOTAL job=${SLURM_JOB_ID:-none}"
while true; do
  done_now=$("$PY" "$HELPER" count "$BASE/export" "$CELLS" 2>/dev/null | head -1 | awk '{print $2}')
  done_now=${done_now:-0}
  # Count ONLY permanently blocked cells (attempts >= 2), else a single failure
  # wave would falsely satisfy done+blocked >= TOTAL and end the phase early.
  blocked=0
  if [ -d "$BASE/failed" ]; then
    blocked=$(find "$BASE/failed" -type f -exec cat {} + 2>/dev/null | awk '$1>=2{n++}END{print n+0}')
  fi
  if [ -f "$BASE/blocked.tsv" ]; then
    b2=$(wc -l < "$BASE/blocked.tsv"); blocked=$(( blocked > b2 ? blocked : b2 ))
  fi
  used=$(quota_used); used=${used:-0}

  if [ "$done_now" -ge "$TOTAL" ]; then
    touch "$BASE/phase.done"; log "PHASE_DONE complete=$done_now/$TOTAL blocked=$blocked"; exit 0
  fi
  # No infinite loop: if every remaining cell is permanently blocked, record and hand over.
  if [ "$blocked" -gt 0 ] && [ $(( done_now + blocked )) -ge "$TOTAL" ]; then
    "$PY" "$HELPER" pending "$BASE/export" "$CELLS" "$BASE/BLOCKED_CELLS.tsv" 2>/dev/null || true
    touch "$BASE/phase.done"
    log "PHASE_DONE_WITH_BLOCKED complete=$done_now blocked=$blocked total=$TOTAL (BLOCKED_CELLS.tsv)"
    exit 0
  fi
  if [ "$used" -gt 900 ]; then
    log "HARD_QUOTA_PAUSE used=${used}G complete=$done_now/$TOTAL (no new lane submissions)"
    sleep 600; continue
  fi
  if [ "$used" -gt 450 ]; then log "SOFT_QUOTA_WARN used=${used}G (soft 300G, hard 1024G, grace active)"; fi
  # Checkpoint pruning is OPT-IN: RETURN_CONTRACT requires per-seed checkpoints retained
  # on HPC, so we never auto-delete them. Set TRACKB_AUTO_PRUNE=1 only after retrieval.
  if [ "${TRACKB_AUTO_PRUNE:-0}" = "1" ] && [ -x "$R/core/prune_layer.sh" ]; then
    bash "$R/core/prune_layer.sh" >> "$BASE/logs/prune_v2.log" 2>&1 || true
  fi

  # Protocol L: the 1120 phase must not start until core is validated complete.
  if [ "$PHASE" = "all" ] && [ ! -f "$R/core/phase.done" ]; then
    log "WAIT_CORE_PHASE (core not yet validated complete)"
    sleep 600; continue
  fi

  # resubmit only lanes that are absent; static stripes make overlap impossible
  for ((lane=0; lane<NLANES; lane++)); do
    name="${JOBPFX}${lane}"
    if [ -f "$BASE/lane${lane}_v2.done" ]; then continue; fi
    if ! squeue -u "$USER" -h -n "$name" 2>/dev/null | grep -q .; then
      sbatch "$BASE/lane${lane}_v2.sbatch" >> "$BASE/logs/controller_v2.log" 2>&1 \
        && log "RESUBMIT $name" || log "RESUBMIT_FAILED $name"
    fi
  done
  retries=0; [ -f "$BASE/retry.tsv" ] && retries=$(wc -l < "$BASE/retry.tsv")
  log "STATUS complete=$done_now/$TOTAL blocked=$blocked retries=$retries quota=${used}G"

  elapsed=$(( $(date +%s) - START ))
  if [ "$elapsed" -gt "$WALL_LIMIT" ]; then
    # exactly ONE successor per generation; afterany ensures the singleton lock
    # is released before the successor starts (no 0-second churn, no chain death).
    sbatch --dependency=afterany:${SLURM_JOB_ID:-0} "$BASE/controller_v2.sbatch" \
      >> "$BASE/logs/controller_v2.log" 2>&1 \
      && log "RENEW successor submitted at elapsed=$elapsed" || log "RENEW_FAILED"
    exit 0
  fi
  sleep 300
done
