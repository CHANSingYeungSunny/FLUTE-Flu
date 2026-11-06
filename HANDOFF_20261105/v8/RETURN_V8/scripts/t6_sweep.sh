#!/bin/bash
# T6 FINAL SWEEP — measure peak VRAM + inference latency for the remaining models.
# Every model workload runs INSIDE this sbatch job on an A100 compute node.
set -u
ROOT=/gpfs1/home/sychan552/stage5_a2_durable
CODE=/gpfs1/scratch/sychan552/stage5_a2_durable/code
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res
LOGS=$BASE/logs/final_sweep
OUT=$BASE/final_sweep_out
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
VENV=/home/sychan552/.venvs/mlflu_fm
mkdir -p "$LOGS" "$OUT"
echo "=== T6_SWEEP START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$LOGS/gpu_identity.txt"

# measure_model <name> <command...> : per-model VRAM sampling + /usr/bin/time -v
measure_model() {
  local name=$1; shift
  local csv="$LOGS/${name}_vram.csv"
  echo "--- MODEL $name START $(date -u +%FT%TZ) ---"
  nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
    --format=csv,noheader,nounits -l 1 > "$csv" 2> "$LOGS/${name}_vram.err" &
  local pid=$!
  /usr/bin/time -v -o "$LOGS/${name}_time_v.txt" timeout 600s "$@" \
    > "$LOGS/${name}.stdout" 2> "$LOGS/${name}.stderr"
  local rc=$?
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  echo "$name RC=$rc END $(date -u +%FT%TZ)"
  "$PY" - "$csv" "$name" >> "$LOGS/summary_vram.txt" <<'PY'
import sys
p, name = sys.argv[1], sys.argv[2]
vals=[]
try:
    for line in open(p, errors="replace"):
        parts=[x.strip() for x in line.split(",")]
        if len(parts)>=4:
            try: vals.append(int(float(parts[2])))
            except Exception: pass
except OSError as e: print(name,"open_error",e)
if vals: print(f"{name} peak_vram_mib={max(vals)} min_vram_mib={min(vals)} n_samples={len(vals)} status=MEASURED")
else: print(f"{name} peak_vram_mib=NOT_MEASURED n_samples=0 reason=no_usable_samples")
PY
  return 0
}

# --- 1. MIFlu: real forward from an existing checkpoint (no training) ---
measure_model miflu "$CODE/export_miflu_all7.py" \
  --cells 36:2023 \
  --ckpt "$ROOT/author_runs/ckpt_L36_s2023/best_miflu_L36.pth" \
  --out-dir "$OUT/miflu" --tag t6final --device cuda

# --- 2/3. NLinear + PatchTST: the project's real training+inference script ---
for m in nlinear patchtst; do
  mkdir -p "$OUT/$m"
  measure_model "$m" "$PY" -u "$CODE/train_backbone_966.py" \
    --backbone "$m" --horizon 24 --seed 42 --profile author_966 \
    --containment strict --fold 3 --export-dir "$OUT/$m"
done

# --- 4. one frozen language encoder ---
measure_model frozen_encoder "$VENV/bin/python" -u \
  "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/t6_model_probe.py" \
  --model frozen_encoder

# --- 5/6. Chronos + TimesFM (isolated env, warm-up + repeated) ---
for m in chronos timesfm; do
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
    measure_model "$m" "$VENV/bin/python" -u \
      "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/t6_model_probe.py" \
      --model "$m"
done

echo "=== SUMMARY VRAM ==="; cat "$LOGS/summary_vram.txt"
echo "=== PROBE STDOUTS ==="
for m in frozen_encoder chronos timesfm; do echo "--- $m"; tail -30 "$LOGS/$m.stdout"; done
echo "=== STDERR TAILS ==="
for m in miflu nlinear patchtst frozen_encoder chronos timesfm; do
  echo "--- $m stderr"; tail -6 "$LOGS/$m.stderr" 2>/dev/null
done
echo "=== TIME -V WALL CLOCKS ==="
for m in miflu nlinear patchtst frozen_encoder chronos timesfm; do
  echo -n "$m "; grep -E "Elapsed \(wall clock\)|Maximum resident" "$LOGS/${m}_time_v.txt" 2>/dev/null | tr '\n' ' '; echo
done
sha256sum "$LOGS"/* > "$LOGS/LOGS_MANIFEST.sha256" 2>/dev/null || true
echo "=== T6_SWEEP END $(date -u +%FT%TZ) ==="
