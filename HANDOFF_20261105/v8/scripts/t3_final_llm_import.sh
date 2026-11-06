#!/bin/bash
# T3 — run the legacy final_llm_import (f5_llm_import) ONCE on a compute node.
# All work here runs inside sbatch; nothing heavy on the login node.
set -u
ROOT=/gpfs1/scratch/sychan552/stage5_a2_durable
RUNS=/gpfs1/home/sychan552/stage5_a2_durable
Q=$ROOT/code/queue
A=$RUNS/analysis
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=$Q/finalise/T3_v8
TS=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$OUT"
echo "T3_START_UTC=$(date -u +%FT%TZ) HOST=$(hostname) JOB=${SLURM_JOB_ID:-none}"

# ---- 1. backup old paper_tables BEFORE anything can rewrite them ----
BAK=$A/paper_tables.bak_T3_$TS
cp -a "$A/paper_tables" "$BAK"
echo "BACKUP_PATH=$BAK"
echo "BACKUP_FILE_COUNT=$(find "$BAK" -maxdepth 1 -type f | wc -l)"

HASH_BEFORE=$OUT/hashes_before_$TS.txt
HASH_AFTER=$OUT/hashes_after_$TS.txt
for f in "$A"/paper_tables/BENCH_*.csv; do
  [ -f "$f" ] && sha256sum "$f"
done | sort > "$HASH_BEFORE"
echo "HASH_BEFORE=$HASH_BEFORE lines=$(wc -l < "$HASH_BEFORE")"

# ---- 2. run the exact queue task once; force past the no-new-cells guard ----
echo "COMMAND=QUEUE_FORCE_FINALISE=1 $PY -u $Q/master_task_v2.py run --task-id final_llm_import --kind f5_llm_import --model - --L - --seed - --env hpc --require-a100 0"
cd "$Q" || exit 90
QUEUE_FORCE_FINALISE=1 "$PY" -u "$Q/master_task_v2.py" run \
  --task-id final_llm_import --kind f5_llm_import \
  --model - --L - --seed - --env hpc --require-a100 0 \
  > "$OUT/final_llm_import_$TS.stdout" 2> "$OUT/final_llm_import_$TS.stderr"
RC=$?
echo "TASK_RC=$RC"
echo "--- stdout tail ---"; tail -40 "$OUT/final_llm_import_$TS.stdout"
echo "--- stderr tail ---"; tail -40 "$OUT/final_llm_import_$TS.stderr"

# ---- 3. hashes after + diff ----
for f in "$A"/paper_tables/BENCH_*.csv; do
  [ -f "$f" ] && sha256sum "$f"
done | sort > "$HASH_AFTER"
echo "HASH_AFTER=$HASH_AFTER lines=$(wc -l < "$HASH_AFTER")"
echo "--- hash diff (before vs after) ---"
diff "$HASH_BEFORE" "$HASH_AFTER" || true
echo "--- finalise log tail ---"
tail -60 "$Q/finalise/final_llm_import.log" 2>/dev/null || echo "NO_FINALISE_LOG"
echo "--- finalise record ---"
cat "$Q/finalise/final_llm_import.json" 2>/dev/null || echo "NO_FINALISE_JSON"
echo "T3_END_UTC=$(date -u +%FT%TZ)"
exit "$RC"
