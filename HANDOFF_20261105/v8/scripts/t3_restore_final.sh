#!/bin/bash
# T3 FINAL — restore the two quarantined corrupt NPZ from their existing VALID
# 7-channel copies, validate all 388 cells, then re-run final_llm_import once.
# All numpy work inside sbatch on a compute node (AGENTS.md RULE 1).
set -u
R=/gpfs1/home/sychan552/stage5_a2_durable
Q=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue
A=$R/analysis
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=$Q/finalise/T3_v8
TS=$(date -u +%Y%m%dT%H%M%SZ)
LOGS=$OUT/restore_$TS
mkdir -p "$LOGS"
echo "=== T3_RESTORE START $(date -u +%FT%TZ) host=$(hostname) job=${SLURM_JOB_ID:-none} ==="

echo "--- BEFORE: paper_tables hashes ---"
sha256sum "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" > "$LOGS/hashes_before.txt"
cat "$LOGS/hashes_before.txt"

echo "--- restore by COPY (source valid 7ch NPZ, never delete anything) ---"
for L in 36 60; do
  SRC=$R/author_runs/L${L}_all7/pred_miflu_L${L}_seed2021.npz
  DST=$R/expanded_runs/miflu_L${L}_s2021/pred_miflu_L${L}_s2021.npz
  echo "SRC=$SRC size=$(stat -c %s "$SRC" 2>/dev/null) sha256=$(sha256sum "$SRC" 2>/dev/null | cut -d' ' -f1)"
  echo "DST=$DST exists_before=$([ -e "$DST" ] && echo yes || echo no)"
  cp -f "$SRC" "$DST"
  echo "COPY_RC=$? DST_size=$(stat -c %s "$DST") DST_sha256=$(sha256sum "$DST" | cut -d' ' -f1)"
done

echo "--- validate ALL 388 expanded_runs pred NPZ (numpy inside sbatch) ---"
"$PY" -u - > "$LOGS/validation.json" 2> "$LOGS/validation.err" <<'PY'
import glob, json, os
import numpy as np
R="/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs"
files=sorted(glob.glob(os.path.join(R,"**","pred_*.npz"),recursive=True))
ok,bad=0,[]
for p in files:
    try:
        z=np.load(p,allow_pickle=False)
        pred=np.asarray(z["pred"]); tgt=np.asarray(z["target"])
        assert pred.shape==tgt.shape and pred.ndim==3 and pred.shape[1]==7
        assert np.isfinite(pred).all() and np.isfinite(tgt).all()
        ok+=1
    except Exception as e:
        bad.append({"path":p,"error":type(e).__name__+": "+str(e)[:160]})
restored=[]
for L in (36,60):
    p=os.path.join(R,f"miflu_L{L}_s2021",f"pred_miflu_L{L}_s2021.npz")
    z=np.load(p,allow_pickle=False)
    restored.append({"path":p,"pred_shape":list(np.asarray(z["pred"]).shape),
                     "space":str(z["space"]) if "space" in z.files else None,
                     "protocol":str(z["protocol"]) if "protocol" in z.files else None,
                     "keys":list(z.files),
                     "finite":bool(np.isfinite(np.asarray(z["pred"])).all())})
print(json.dumps({"total_npz":len(files),"readable":ok,"unreadable":bad,
                  "restored":restored},indent=2))
PY
echo "VALIDATION_RC=$?"
cat "$LOGS/validation.json"
cat "$LOGS/validation.err"

echo "--- re-run exact final_llm_import task ONCE ---"
echo "COMMAND=QUEUE_FORCE_FINALISE=1 $PY -u $Q/master_task_v2.py run --task-id final_llm_import --kind f5_llm_import --model - --L - --seed - --env hpc --require-a100 0"
cd "$Q" || exit 90
QUEUE_FORCE_FINALISE=1 "$PY" -u "$Q/master_task_v2.py" run \
  --task-id final_llm_import --kind f5_llm_import \
  --model - --L - --seed - --env hpc --require-a100 0 \
  > "$LOGS/final_llm_import.stdout" 2> "$LOGS/final_llm_import.stderr"
RC=$?
echo "TASK_RC=$RC"
echo "--- stdout ---"; cat "$LOGS/final_llm_import.stdout"
echo "--- stderr ---"; cat "$LOGS/final_llm_import.stderr"
echo "--- finalise record ---"; cat "$Q/finalise/final_llm_import.json" 2>/dev/null
echo "--- AFTER: paper_tables hashes ---"
sha256sum "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" > "$LOGS/hashes_after.txt"
cat "$LOGS/hashes_after.txt"
echo "--- hash diff ---"; diff "$LOGS/hashes_before.txt" "$LOGS/hashes_after.txt" || true
echo "--- proof table rows ---"; wc -l "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
echo "OUTPUT_LOG_DIR=$LOGS"
echo "=== T3_RESTORE END $(date -u +%FT%TZ) ==="
exit "$RC"
