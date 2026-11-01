#!/bin/bash
#SBATCH --job-name=miflu_compute
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32000M
#SBATCH --time=12:00:00
#SBATCH --output=compute-%j.out
#SBATCH --requeue
#SBATCH --exclude=gpu-a100-05,gpu-a100-09
#
# Compute lane: trains + exports + oracle-gates the 22 missing MIFlu cells.
# Skip-if-complete, 1 worker, A100-only, resumable, self-requeues before wall.
# Never writes paper_tables/ — that belongs to the writer lane alone.
set -u
R=/gpfs1/home/sychan552/stage5_a2_durable
C=$R/code
V=$R/author_runs/.miflu_verify
Q=$C/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HALT=$Q/HALT
TRAINLOG=$Q/compute_train.log
WALL_LIMIT=42000
START=$(date +%s)
log() { echo "[compute $$ $(date '+%F %T')] $*" >> "$TRAINLOG"; }

# cell|expected_test_mse_all(oracle)
CELLS="
36|2027|1.400796
36|2028|1.302717
36|2029|1.404061
36|2030|1.328807
48|2022|1.711215
48|2023|1.663857
48|2024|1.879495
48|2025|1.723161
48|2026|1.620327
48|2027|1.628296
48|2028|1.588157
48|2029|1.570881
48|2030|1.675020
60|2021|1.599641
60|2022|1.664878
60|2023|1.821282
60|2024|1.915250
60|2026|1.984315
60|2027|1.614602
60|2028|1.401814
60|2029|1.520661
60|2030|1.895393
"

log "=== started job=${SLURM_JOB_ID:-?} part=${SLURM_JOB_PARTITION:-?} node=$(hostname) ==="

# A100 gate
GPU=$($PY - <<'EOF' 2>/dev/null || echo GATE_FAIL
try:
    import torch
    print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA")
except Exception as e:
    print("GATE_FAIL")
EOF
)
case "$GPU" in
  *A100*) log "A100 gate OK: $GPU" ;;
  *) log "ABORT: not A100 -> $GPU"; exit 0 ;;
esac

cd "$C" || { log "FATAL cd"; exit 0; }

done_cells=0; fail_cells=0
for row in $CELLS; do
  [ -f "$HALT" ] && { log "HALT -> stop"; exit 0; }
  now=$(date +%s)
  if [ $(( now - START )) -gt $WALL_LIMIT ]; then
    log "wall guard -> scontrol requeue"
    scontrol requeue "${SLURM_JOB_ID:-}" && exit 0
    log "requeue failed -> exit"; exit 0
  fi

  L=$(echo "$row" | cut -d'|' -f1)
  S=$(echo "$row" | cut -d'|' -f2)
  EXP=$(echo "$row" | cut -d'|' -f3)
  mk=$(ls "$V" 2>/dev/null | grep -c "L${L}_s${S}\.json")
  if [ "$mk" -gt 0 ]; then log "skip L$L s$S (verified)"; continue; fi

  log "--- TRAIN L$L s$S (expect $EXP) ---"
  $PY train_miflu.py \
      --profile author_repo_966 --text-source author_file \
      --horizon "$L" --seed "$S" --reps 1 --epochs 20 --batch-size 16 \
      --learning-rate 0.0001 --containment strict \
      --export-dir "$R/author_runs/L${L}_all7" \
      --ckpt-dir   "$R/author_runs/ckpt_retrain/L${L}_s${S}" \
      >> "$TRAINLOG" 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then
    log "train FAILED rc=$rc L$L s$S (attempt recorded, continuing)"
    fail_cells=$(( fail_cells + 1 )); continue
  fi

  log "--- EXPORT L$L s$S ---"
  $PY export_miflu_all7.py --horizon "$L" --seed "$S" >> "$TRAINLOG" 2>&1 \
    || log "export FAILED L$L s$S (continuing)"

  # gate: marker must exist now; writer lane does the deep oracle check
  if ls "$V" 2>/dev/null | grep -q "L${L}_s${S}\.json"; then
    log "OK L$L s$S verified"; done_cells=$(( done_cells + 1 ))
  else
    log "NO MARKER after export L$L s$S"; fail_cells=$(( fail_cells + 1 ))
  fi
done

log "=== finished done=$done_cells fail=$fail_cells ==="
exit 0
