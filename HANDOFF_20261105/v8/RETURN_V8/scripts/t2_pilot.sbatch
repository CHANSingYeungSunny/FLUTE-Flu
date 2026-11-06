#!/bin/bash
#SBATCH --job-name=t2_fm_pilot
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:35:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/pilot_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/pilot_%j.err
# ALL model work (extract, SHA verify, torch load, forward) is INSIDE this sbatch
# job on a GPU COMPUTE node. Nothing on the login node. AGENTS.md RULE 1.
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm
LOGS=$BASE/logs
VENV=/home/sychan552/.venvs/mlflu_fm
MODELS=/gpfs1/scratch/sychan552/models
WORK=$BASE/extracted
mkdir -p "$LOGS" "$BASE/pilot_out" "$WORK"
echo "=== T2_PILOT START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
echo "--- GPU ---"
nvidia-smi -L
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo "--- verify tar SHA-256 before extraction (compute node) ---"
sha256sum "$MODELS/chronos_bolt_tiny.tar"
echo "EXPECTED=f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18"
mkdir -p "$WORK/chronos_bolt_tiny"
tar -xf "$MODELS/chronos_bolt_tiny.tar" -C "$WORK/chronos_bolt_tiny"
echo "TAR_EXTRACT_RC=$?"
echo "--- model file SHA-256 ---"
sha256sum "$WORK/chronos_bolt_tiny/chronos_bolt_tiny/model.safetensors"
echo "EXPECTED_LFS_OID=75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32"

echo "--- nvidia-smi VRAM sampling (1 s) ---"
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader,nounits -l 1 > "$LOGS/pilot_vram_sample.csv" 2> "$LOGS/pilot_vram_sample.err" &
NSMI_PID=$!

echo "--- run pilot with /usr/bin/time -v ---"
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
  /usr/bin/time -v -o "$LOGS/pilot_time_v.txt" \
  timeout 900s "$VENV/bin/python" -u "$BASE/t2_pilot.py" \
  > "$LOGS/pilot_stdout.txt" 2> "$LOGS/pilot_stderr.txt"
PILOT_RC=$?
echo "PILOT_RC=$PILOT_RC"
kill "$NSMI_PID" 2>/dev/null || true
wait "$NSMI_PID" 2>/dev/null || true

echo "--- peak VRAM ---"
"$VENV/bin/python" - <<'PY'
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/pilot_vram_sample.csv"
vals = []
try:
    for line in open(p, errors="replace"):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 4:
            try: vals.append(int(float(parts[2])))
            except Exception: pass
except OSError as e:
    print("open_error", e)
print("peak_vram_mib=%d" % max(vals) if vals else "peak_vram_mib=NOT_MEASURED")
print("n_samples=%d" % len(vals))
PY
echo "--- stdout ---"; cat "$LOGS/pilot_stdout.txt"
echo "--- stderr tail ---"; tail -30 "$LOGS/pilot_stderr.txt"
echo "--- time -v ---"; cat "$LOGS/pilot_time_v.txt"
echo "--- outputs ---"; ls -la "$BASE/pilot_out/"
echo "=== T2_PILOT END $(date -u +%FT%TZ) ==="
exit "$PILOT_RC"
