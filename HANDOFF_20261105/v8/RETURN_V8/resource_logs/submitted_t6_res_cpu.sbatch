#!/bin/bash
#SBATCH --job-name=t6_res_cpu
#SBATCH --partition=tiny
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_res_cpu_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_res_cpu_%j.err
#
# TASK 6 resource measurements - CPU-only sbatch job on `tiny`.
# AGENTS.md RULE 1: all Python / numpy NPZ work here runs on a COMPUTE node,
# never on the Burgundy login node. `import torch` (record_versions.py) is
# therefore allowed inside THIS job.
set -u

BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res
LOGS=$BASE/logs
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
mkdir -p "$LOGS"

EC=$LOGS/exit_codes.txt
: > "$EC"

echo "=== t6_res_cpu START $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "job_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/job_timing.txt"

# --------------------------------------------------------------- 0. env probe
{
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"
  echo "SLURM_JOB_ID=$SLURM_JOB_ID"
  echo "SLURM_JOB_NAME=$SLURM_JOB_NAME"
  echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-<unset>}"
  echo "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION"
  echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK:-<unset>}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
  echo "uname=$(uname -a)"
  echo "nproc=$(nproc)"
  echo "python_binary=$PY"
  "$PY" -V 2>&1 | sed 's/^/python_V=/'
  /usr/bin/time --version 2>&1 | head -1 | sed 's/^/gnu_time_version=/'
} > "$LOGS/env_probe.txt" 2>&1
echo "env_probe rc=$?" >> "$EC"

# authoritative job record (proves no gpu gres was allocated)
scontrol show job "$SLURM_JOB_ID" > "$LOGS/scontrol_job.txt" 2>&1
echo "scontrol_show_job rc=$?" >> "$EC"

# --------------------------------------------- 1. GPU presence + VRAM sampling
# Sampling with `nvidia-smi -l 1` happens ONLY if this job actually has a GPU.
GPU_PRESENT=0
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi -L > "$LOGS/nvidia_smi_L.txt" 2>&1
    NSMI_RC=$?
    echo "nvidia_smi_L rc=$NSMI_RC" >> "$LOGS/gpu_probe.txt"
    grep -qi "GPU [0-9]" "$LOGS/nvidia_smi_L.txt" && GPU_PRESENT=1
else
    echo "nvidia-smi: command not found on this node (CPU-only tiny partition)" \
        > "$LOGS/nvidia_smi_L.txt"
    echo "nvidia_smi_L rc=127" >> "$LOGS/gpu_probe.txt"
fi
echo "GPU_PRESENT=$GPU_PRESENT" | tee -a "$LOGS/gpu_probe.txt"

if [ "$GPU_PRESENT" -eq 1 ]; then
    nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
               --format=csv,noheader,nounits -l 1 \
               > "$LOGS/nvidia_smi_sample.csv" 2> "$LOGS/nvidia_smi_sample.err" &
    NSMI_PID=$!
    echo "nvidia_smi_sampling_started pid=$NSMI_PID" >> "$LOGS/gpu_probe.txt"
else
    cat > "$LOGS/peak_vram_mib.txt" <<'EOF'
peak_vram_mib=NOT_MEASURED
reason=no GPU allocated in this job (sbatch --partition=tiny, no --gres=gpu requested; nvidia-smi -L found no usable device). Peak VRAM therefore cannot be sampled.
EOF
    echo "nvidia_smi_sampling=SKIPPED reason=no GPU allocated in this job" >> "$LOGS/gpu_probe.txt"
fi

# -------------------------------------- 2. software versions (inside compute)
/usr/bin/time -v -o "$LOGS/time_v_versions.txt" \
    "$PY" -u "$BASE/record_versions.py" > "$LOGS/versions.json" 2> "$LOGS/versions.stderr.txt"
echo "record_versions rc=$?" >> "$EC"

# -------------------------------- 3. real training wall times from queue logs
/usr/bin/time -v -o "$LOGS/time_v_wall.txt" \
    "$PY" -u "$BASE/extract_wall.py" > "$LOGS/wall_extraction.out" 2> "$LOGS/wall_extraction.stderr.txt"
echo "extract_wall rc=$?" >> "$EC"

# ------------------------- 4. NPZ scoring-path latency (NOT a model forward)
/usr/bin/time -v -o "$LOGS/time_v_latency.txt" \
    "$PY" -u "$BASE/measure_latency.py" > "$LOGS/npz_scoring_latency.out" \
    2> "$LOGS/npz_scoring_latency.stderr.txt"
echo "measure_latency rc=$?" >> "$EC"

# ------------------------------------------------------------ 5. finish / VRAM
if [ "$GPU_PRESENT" -eq 1 ]; then
    kill "$NSMI_PID" 2>/dev/null || true
    wait "$NSMI_PID" 2>/dev/null || true
    "$PY" - <<'PY' > "$LOGS/peak_vram_mib.txt" 2>&1
import re
v = []
try:
    for line in open("/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/nvidia_smi_sample.csv"):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            try:
                v.append(int(float(parts[2])))
            except Exception:
                pass
except FileNotFoundError:
    pass
if v:
    print("peak_vram_mib=%d" % max(v))
    print("samples=%d source=nvidia_smi_sample.csv (memory.used MiB)" % len(v))
else:
    print("peak_vram_mib=NOT_MEASURED")
    print("reason=nvidia-smi sampling produced no usable memory.used samples")
PY
fi

# archive the exact submitted scripts as evidence
cp "$BASE/t6_res_cpu.sbatch"        "$LOGS/submitted_t6_res_cpu.sbatch"       2>/dev/null || true
cp "$BASE/record_versions.py"       "$LOGS/submitted_record_versions.py"      2>/dev/null || true
cp "$BASE/extract_wall.py"          "$LOGS/submitted_extract_wall.py"         2>/dev/null || true
cp "$BASE/measure_latency.py"       "$LOGS/submitted_measure_latency.py"      2>/dev/null || true

echo "job_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGS/job_timing.txt"
echo "=== t6_res_cpu END $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# deterministic manifest of the raw logs produced by THIS job
sha256sum \
  "$LOGS/env_probe.txt" "$LOGS/scontrol_job.txt" "$LOGS/gpu_probe.txt" \
  "$LOGS/nvidia_smi_L.txt" "$LOGS/peak_vram_mib.txt" "$LOGS/time_v_versions.txt" \
  "$LOGS/versions.json" "$LOGS/versions.stderr.txt" "$LOGS/time_v_wall.txt" \
  "$LOGS/wall_extraction.out" "$LOGS/wall_extraction.stderr.txt" \
  "$LOGS/training_wall_extraction.tsv" "$LOGS/training_wall_summary_all_models.tsv" \
  "$LOGS/training_wall_targets.tsv" "$LOGS/training_wall_evidence.json" \
  "$LOGS/shard0_wall_extraction.tsv" "$LOGS/time_v_latency.txt" \
  "$LOGS/npz_scoring_latency.out" "$LOGS/npz_scoring_latency.stderr.txt" \
  "$LOGS/npz_scoring_latency.json" "$LOGS/npz_scoring_latency.tsv" \
  "$LOGS/job_timing.txt" \
  "$LOGS/submitted_t6_res_cpu.sbatch" "$LOGS/submitted_record_versions.py" \
  "$LOGS/submitted_extract_wall.py" "$LOGS/submitted_measure_latency.py" \
  > "$LOGS/logs_manifest.sha256" 2>&1
echo "manifest rc=$?" >> "$EC"
echo "T6_RES_CPU_DONE"
