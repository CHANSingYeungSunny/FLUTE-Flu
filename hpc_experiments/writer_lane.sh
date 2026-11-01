#!/bin/bash
#SBATCH --job-name=miflu_writer
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=1900M
#SBATCH --time=5-00:00:00
#SBATCH --output=writer-%j.out
#SBATCH --requeue
#
# Writer lane v2: runs the finalisation chain EVERY cycle (master_task is
# idempotent and no-ops in ~1s when nothing changed), so a failed or
# lock-blocked cycle is retried automatically 2 minutes later. This removes
# the "last count" gating bug that made v1 give up after one skip.
set -u
R=/gpfs1/home/sychan552/stage5_a2_durable
A=$R/analysis
V=$R/author_runs/.miflu_verify
Q=$R/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
LOCK=$A/.finalise.lock
HALT=$Q/HALT
STAT=$Q/finalise_status.json
WALL_LIMIT=426000
START=$(date +%s)
log() { echo "[writer $$ $(date '+%F %T')] $*"; }

cd "$A" || { log "FATAL cd $A"; exit 1; }
log "v2 started job=${SLURM_JOB_ID:-?} node=$(hostname)"

# clear a stale lock left by a dead predecessor (safe: no other writer may run)
rm -f "$LOCK" 2>/dev/null

cycle=0
while :; do
  [ -f "$HALT" ] && { log "HALT -> exit"; exit 0; }
  now=$(date +%s)
  if [ $(( now - START )) -gt $WALL_LIMIT ]; then
    log "wall guard -> requeue"
    scontrol requeue "${SLURM_JOB_ID:-}" && exit 0
    exit 0
  fi

  cycle=$(( cycle + 1 ))
  n=$(ls "$V" 2>/dev/null | wc -l)
  before=$(stat -c %Y paper_tables/BENCH_MSE_BY_MODEL_L.csv 2>/dev/null || echo 0)

  ok=""
  if [ -f "$Q/master_task.py" ]; then
    $PY "$Q/master_task.py" run --task-id final_analysis_chain --kind finalise --env hpc \
      >> "$Q/writer_finalise.log" 2>&1 && ok="master_task"
  fi
  if [ -z "$ok" ]; then
    for s in import_miflu_predictions verify_miflu_oracle analysis_expanded \
             analysis_postprocess seasonal_naive_baseline plot_bench plot_pareto; do
      [ -f "scripts/$s.py" ] && { $PY "scripts/$s.py" >> "$Q/writer_finalise.log" 2>&1 \
        && ok="$ok $s" || log "step $s failed"; }
    done
  fi

  after=$(stat -c %Y paper_tables/BENCH_MSE_BY_MODEL_L.csv 2>/dev/null || echo 0)
  if [ "$after" != "$before" ]; then log "TABLE REWRITTEN markers=$n steps:$ok"; fi
  printf '{"cycle":%d,"markers":%d,"table_mtime":%s,"before":%s,"steps":"%s","pid":%d,"ts":"%s"}\n' \
    "$cycle" "$n" "$after" "$before" "$ok" "$$" "$(date -u '+%FT%TZ')" > "$STAT" 2>/dev/null

  sleep 120
done
