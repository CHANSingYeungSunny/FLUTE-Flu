#!/bin/bash
# T3 retry — quarantine unreadable legacy NPZ (MOVE, never delete) then rerun
# the exact final_llm_import task once. All inside sbatch on a compute node.
set -u
ROOT=/gpfs1/scratch/sychan552/stage5_a2_durable
RUNS=/gpfs1/home/sychan552/stage5_a2_durable
Q=$ROOT/code/queue
A=$RUNS/analysis
E=$RUNS/expanded_runs
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=$Q/finalise/T3_v8
TS=$(date -u +%Y%m%dT%H%M%SZ)
QR=$Q/finalise/T3_v8/quarantine_$TS
mkdir -p "$OUT" "$QR"
echo "T3B_START_UTC=$(date -u +%FT%TZ) HOST=$(hostname) JOB=${SLURM_JOB_ID:-none}"

# ---- 1. scan EVERY npz for readability (numpy load), record bad ones ----
"$PY" -u - > "$OUT/npz_scan_$TS.json" 2> "$OUT/npz_scan_$TS.err" <<'PY'
import glob, json, os
import numpy as np
E = "/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs"
files = sorted(glob.glob(os.path.join(E, "**", "pred_*.npz"), recursive=True))
bad, good = [], 0
for p in files:
    try:
        with np.load(p, allow_pickle=False) as z:
            _ = z["pred"].shape
        good += 1
    except Exception as ex:
        bad.append({"path": p, "size": os.path.getsize(p),
                    "error": type(ex).__name__ + ": " + str(ex)[:160]})
print(json.dumps({"total": len(files), "readable": good, "unreadable": bad}, indent=2))
PY
echo "--- npz scan ---"; cat "$OUT/npz_scan_$TS.json"; cat "$OUT/npz_scan_$TS.err"

# ---- 2. archive unreadable files (move) with hash provenance ----
"$PY" -u - "$TS" "$QR" <<'PY'
import json, os, shutil, sys, hashlib
ts, qr = sys.argv[1], sys.argv[2]
scan = sorted(__import__("glob").glob("/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/finalise/T3_v8/npz_scan_%s.json" % ts))[-1]
d = json.load(open(scan))
moves = []
for b in d["unreadable"]:
    p = b["path"]
    if not os.path.exists(p):
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    rel = os.path.relpath(p, "/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs")
    dst = os.path.join(qr, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(p, dst)
    moves.append({"from": p, "to": dst, "size": b["size"], "sha256": h, "error": b["error"]})
json.dump(moves, open(os.path.join(qr, "QUARANTINE.json"), "w"), indent=2)
print(json.dumps(moves, indent=2))
PY
echo "QUARANTINE_DIR=$QR files=$(find "$QR" -type f ! -name QUARANTINE.json | wc -l)"

HASH_BEFORE=$OUT/hashes_before_retry_$TS.txt
HASH_AFTER=$OUT/hashes_after_retry_$TS.txt
for f in "$A"/paper_tables/BENCH_*.csv; do [ -f "$f" ] && sha256sum "$f"; done | sort > "$HASH_BEFORE"

# ---- 3. rerun the exact task once ----
echo "COMMAND=QUEUE_FORCE_FINALISE=1 $PY -u $Q/master_task_v2.py run --task-id final_llm_import --kind f5_llm_import --model - --L - --seed - --env hpc --require-a100 0"
cd "$Q" || exit 90
QUEUE_FORCE_FINALISE=1 "$PY" -u "$Q/master_task_v2.py" run \
  --task-id final_llm_import --kind f5_llm_import \
  --model - --L - --seed - --env hpc --require-a100 0 \
  > "$OUT/final_llm_import_retry_$TS.stdout" 2> "$OUT/final_llm_import_retry_$TS.stderr"
RC=$?
echo "TASK_RC=$RC"
echo "--- stdout ---"; cat "$OUT/final_llm_import_retry_$TS.stdout"
echo "--- stderr ---"; cat "$OUT/final_llm_import_retry_$TS.stderr"

for f in "$A"/paper_tables/BENCH_*.csv; do [ -f "$f" ] && sha256sum "$f"; done | sort > "$HASH_AFTER"
echo "--- hash diff ---"; diff "$HASH_BEFORE" "$HASH_AFTER" || true
echo "--- finalise record ---"; cat "$Q/finalise/final_llm_import.json" 2>/dev/null || echo NO_JSON
echo "--- proof table head ---"; head -5 "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" 2>/dev/null || echo NO_PROOF
echo "T3B_END_UTC=$(date -u +%FT%TZ)"
exit "$RC"
