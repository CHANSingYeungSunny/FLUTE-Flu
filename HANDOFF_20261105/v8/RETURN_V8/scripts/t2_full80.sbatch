#!/bin/bash
#SBATCH --job-name=t2_fm_full80
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:50:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/full80_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/full80_%j.err
# ALL model work inside sbatch on a GPU compute node (AGENTS.md RULE 1).
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm
LOGS=$BASE/logs
VENV=/home/sychan552/.venvs/mlflu_fm
mkdir -p "$LOGS" "$BASE/full80_out"
echo "=== T2_FULL80 START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader,nounits -l 1 > "$LOGS/full80_vram_sample.csv" 2> "$LOGS/full80_vram_sample.err" &
NSMI_PID=$!

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
  /usr/bin/time -v -o "$LOGS/full80_time_v.txt" \
  timeout 2400s "$VENV/bin/python" -u "$BASE/t2_full80.py" \
  > "$LOGS/full80_stdout.txt" 2> "$LOGS/full80_stderr.txt"
MRC=$?
echo "FULL80_RC=$MRC"
kill "$NSMI_PID" 2>/dev/null || true
wait "$NSMI_PID" 2>/dev/null || true

echo "--- peak VRAM ---"
"$VENV/bin/python" - <<'PY'
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/full80_vram_sample.csv"
vals = []
try:
    for line in open(p, errors="replace"):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 4:
            try: vals.append(int(float(parts[2])))
            except Exception: pass
except OSError as e: print("open_error", e)
print("peak_vram_mib=%d" % max(vals) if vals else "peak_vram_mib=NOT_MEASURED")
print("n_samples=%d" % len(vals))
PY
echo "--- stdout ---"; cat "$LOGS/full80_stdout.txt"
echo "--- stderr tail ---"; tail -30 "$LOGS/full80_stderr.txt"
echo "--- time -v ---"; cat "$LOGS/full80_time_v.txt"
echo "--- outputs ---"; ls -la "$BASE/full80_out/" | head -20
echo "--- NPZ count ---"; find "$BASE/full80_out" -name "*.npz" | wc -l
echo "--- CSV head ---"; head -4 "$BASE/full80_out/FOUNDATION_80_CELLS.csv" 2>/dev/null
echo "=== T2_FULL80 END $(date -u +%FT%TZ) ==="
exit "$MRC"
