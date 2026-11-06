#!/bin/bash
#SBATCH --job-name=t6_res_gpu
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --exclude=gpu-a100-03
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:12:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_res_gpu_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_res_gpu_%j.err
#
# TASK 6 - OPTIONAL short GPU job. REAL model forward pass (NOT a synthetic
# benchmark): runs the project's own export_miflu_all7.py from an EXISTING
# checkpoint with --device cuda. Safe: job 743850 (wf_fix218) runs on the
# `stingy` partition node gpu-a100-03, which is EXCLUDED here; all outputs are
# written ONLY under t6_res/. All model work is inside sbatch (AGENTS.md RULE 1).
set -u

BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res
LOGS=$BASE/logs
OUT=$BASE/gpu_forward_out
CODE=/gpfs1/scratch/sychan552/stage5_a2_durable/code
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CKPT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs/ckpt_L36_s2023/best_miflu_L36.pth
mkdir -p "$LOGS" "$OUT"

EC=$LOGS/exit_codes_gpu.txt
: > "$EC"

echo "=== t6_res_gpu START $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "job_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/job_timing_gpu.txt"

{
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"
  echo "SLURM_JOB_ID=$SLURM_JOB_ID"
  echo "SLURM_JOB_NAME=$SLURM_JOB_NAME"
  echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-<unset>}"
  echo "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
  echo "uname=$(uname -a)"
  echo "python_binary=$PY"
  "$PY" -V 2>&1 | sed 's/^/python_V=/'
  echo "checkpoint=$CKPT"
} > "$LOGS/env_probe_gpu.txt" 2>&1
echo "env_probe_gpu rc=$?" >> "$EC"

scontrol show job "$SLURM_JOB_ID" > "$LOGS/scontrol_job_gpu.txt" 2>&1
echo "scontrol_show_job_gpu rc=$?" >> "$EC"

# --- GPU identity + VRAM sampling (only because this job HAS a GPU) ----------
nvidia-smi -L > "$LOGS/nvidia_smi_L_gpu.txt" 2>&1
echo "nvidia_smi_L_gpu rc=$?" >> "$EC"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader \
    > "$LOGS/gpu_identity.txt" 2>&1
echo "gpu_identity rc=$?" >> "$EC"

nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
           --format=csv,noheader,nounits -l 1 \
           > "$LOGS/nvidia_smi_gpu_sample.csv" 2> "$LOGS/nvidia_smi_gpu_sample.err" &
NSMI_PID=$!
echo "nvidia_smi_sampling_started pid=$NSMI_PID" > "$LOGS/gpu_probe_gpu.txt"

# --- REAL forward pass from an existing checkpoint (time-boxed) --------------
# `timeout 540s` is a hard inner bound; slurm --time=00:12:00 is the outer bound.
/usr/bin/time -v -o "$LOGS/time_v_gpu_forward.txt" \
    timeout 540s "$PY" -u "$CODE/export_miflu_all7.py" \
        --cells 36:2023 \
        --ckpt "$CKPT" \
        --out-dir "$OUT" \
        --tag t6res \
        --device cuda \
        > "$LOGS/gpu_forward.out" 2> "$LOGS/gpu_forward.err"
GPU_RC=$?
echo "gpu_forward rc=$GPU_RC" >> "$EC"

# --- stop sampling + derive peak VRAM ----------------------------------------
kill "$NSMI_PID" 2>/dev/null || true
wait "$NSMI_PID" 2>/dev/null || true

"$PY" - <<'PY' > "$LOGS/peak_vram_gpu.txt" 2>&1
import os
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/nvidia_smi_gpu_sample.csv"
vals = []
names = set()
lines = 0
if os.path.exists(p):
    for line in open(p, errors="replace"):
        lines += 1
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 4:
            names.add(parts[1])
            try:
                vals.append(int(float(parts[2])))
            except Exception:
                pass
print("sample_lines=%d" % lines)
print("gpu_names=%s" % (";".join(sorted(names)) if names else "NONE"))
if vals:
    print("peak_vram_mib=%d" % max(vals))
    print("peak_source=nvidia_smi_gpu_sample.csv memory.used MiB (n_samples=%d)" % len(vals))
    print("min_vram_mib=%d" % min(vals))
    print("status=MEASURED")
else:
    print("peak_vram_mib=NOT_MEASURED")
    print("reason=nvidia-smi sampling produced no usable memory.used samples")
    print("status=NOT_MEASURED")
PY
echo "peak_vram_derivation rc=$?" >> "$EC"

echo "job_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGS/job_timing_gpu.txt"
echo "=== t6_res_gpu END $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

sha256sum \
  "$LOGS/env_probe_gpu.txt" "$LOGS/scontrol_job_gpu.txt" "$LOGS/nvidia_smi_L_gpu.txt" \
  "$LOGS/gpu_identity.txt" "$LOGS/nvidia_smi_gpu_sample.csv" \
  "$LOGS/nvidia_smi_gpu_sample.err" "$LOGS/gpu_probe_gpu.txt" \
  "$LOGS/time_v_gpu_forward.txt" "$LOGS/gpu_forward.out" "$LOGS/gpu_forward.err" \
  "$LOGS/peak_vram_gpu.txt" "$LOGS/job_timing_gpu.txt" \
  > "$LOGS/logs_manifest_gpu.sha256" 2>&1
echo "manifest_gpu rc=$?" >> "$EC"
echo "T6_RES_GPU_DONE"
