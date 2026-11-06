#!/bin/bash
#SBATCH --job-name=t2_fm_matrix
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/matrix_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/matrix_%j.err
# ALL model work inside sbatch on a GPU compute node (AGENTS.md RULE 1).
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm
LOGS=$BASE/logs
VENV=/home/sychan552/.venvs/mlflu_fm
MODELS=/gpfs1/scratch/sychan552/models
WORK=$BASE/extracted
mkdir -p "$LOGS" "$BASE/matrix_out" "$WORK"
echo "=== T2_MATRIX START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo "--- verify ALL FOUR remote tars INSIDE this compute-node job ---"
echo "EXPECTED (local Windows sha256, size):"
echo "  f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18  34652160  chronos_bolt_tiny.tar"
echo "  d6df552e68fc0f2fbad20141d8b852870af76580d51c89508b2a221021f2da16  184893440  chronos_t5_small.tar"
echo "  963d6d6adf8d91c8d8f0a7362eed981bcd147d6d766e7980622141fdd0ebeb13  814376960  timesfm_1_0_200m.tar"
echo "  7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363  3990978560  timesfm_2_0_500m_pytorch.tar"
for f in chronos_bolt_tiny.tar chronos_t5_small.tar timesfm_1_0_200m.tar timesfm_2_0_500m_pytorch.tar; do
  echo "REMOTE $f size=$(stat -c %s "$MODELS/$f") sha256=$(sha256sum "$MODELS/$f" | cut -d' ' -f1)"
done
echo "TOTAL_REMOTE_TAR_BYTES=$(du -cb "$MODELS"/*.tar | tail -1 | cut -f1)"

echo "--- verify + extract TimesFM 2.0 tar INSIDE compute node ---"
TAR=$MODELS/timesfm_2_0_500m_pytorch.tar
echo "tar_size=$(stat -c %s "$TAR")"
echo "tar_sha256=$(sha256sum "$TAR" | cut -d' ' -f1)"
echo "EXPECTED_TAR_SHA256=7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363"
mkdir -p "$WORK/timesfm_2_0_500m_pytorch"
tar -xf "$TAR" -C "$WORK/timesfm_2_0_500m_pytorch"
echo "TAR_EXTRACT_RC=$?"
echo "torch_model.ckpt sha256=$(sha256sum "$WORK/timesfm_2_0_500m_pytorch/timesfm_2_0_500m_pytorch/torch_model.ckpt" 2>/dev/null | cut -d' ' -f1)"
echo "EXPECTED_LFS_OID=a3a1362cdc26f0dde45c9790c438951ff02af96b2d1d6445fdb58f28c77e18de"

nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader,nounits -l 1 > "$LOGS/matrix_vram_sample.csv" 2> "$LOGS/matrix_vram_sample.err" &
NSMI_PID=$!

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
  /usr/bin/time -v -o "$LOGS/matrix_time_v.txt" \
  timeout 3000s "$VENV/bin/python" -u "$BASE/t2_matrix.py" \
  > "$LOGS/matrix_stdout.txt" 2> "$LOGS/matrix_stderr.txt"
MRC=$?
echo "MATRIX_RC=$MRC"
kill "$NSMI_PID" 2>/dev/null || true
wait "$NSMI_PID" 2>/dev/null || true

echo "--- peak VRAM ---"
"$VENV/bin/python" - <<'PY'
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/matrix_vram_sample.csv"
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
echo "--- stdout ---"; cat "$LOGS/matrix_stdout.txt"
echo "--- stderr tail ---"; tail -40 "$LOGS/matrix_stderr.txt"
echo "--- time -v ---"; cat "$LOGS/matrix_time_v.txt"
echo "--- outputs ---"; ls -la "$BASE/matrix_out/"
echo "--- FOUNDATION_CELLS.csv ---"; cat "$BASE/matrix_out/FOUNDATION_CELLS.csv" 2>/dev/null
echo "=== T2_MATRIX END $(date -u +%FT%TZ) ==="
exit "$MRC"
