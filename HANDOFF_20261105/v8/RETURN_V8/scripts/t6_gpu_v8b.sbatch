#!/bin/bash
#SBATCH --job-name=t6_res_gpu_v8b
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --exclude=gpu-a100-03
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_gpu_v8b_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6_gpu_v8b_%j.err
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res
LOGS=$BASE/logs
OUT=$BASE/gpu_forward_out_v8b
CODE=/gpfs1/scratch/sychan552/stage5_a2_durable/code
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CKPT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs/ckpt_L36_s2023/best_miflu_L36.pth
mkdir -p "$LOGS" "$OUT"
EC=$LOGS/exit_codes_gpu_v8b.txt
: > "$EC"
echo "=== T6_GPU_V8B START $(date -u +%FT%TZ) job=$SLURM_JOB_ID host=$(hostname) ==="
{ echo "utc=$(date -u +%FT%TZ)"; echo "hostname=$(hostname)";
  echo "SLURM_JOB_ID=$SLURM_JOB_ID"; echo "SLURM_JOB_PARTITION=$SLURM_JOB_PARTITION";
  echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-unset}";
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}";
  "$PY" -V 2>&1 | sed 's/^/python_V=/'; } > "$LOGS/env_probe_gpu_v8b.txt" 2>&1
nvidia-smi -L > "$LOGS/nvidia_smi_L_gpu_v8b.txt" 2>&1
echo "nvidia_smi_L rc=$?" >> "$EC"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$LOGS/gpu_identity_v8b.txt" 2>&1
echo "gpu_identity rc=$?" >> "$EC"
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader,nounits -l 1 > "$LOGS/nvidia_smi_sample_v8b.csv" 2> "$LOGS/nvidia_smi_sample_v8b.err" &
NSMI_PID=$!
/usr/bin/time -v -o "$LOGS/time_v_gpu_forward_v8b.txt" \
  timeout 600s "$PY" -u "$CODE/export_miflu_all7.py" \
    --cells 36:2023 --ckpt "$CKPT" --out-dir "$OUT" --tag t6v8b --device cuda \
    > "$LOGS/gpu_forward_v8b.out" 2> "$LOGS/gpu_forward_v8b.err"
GPU_RC=$?
echo "gpu_forward rc=$GPU_RC" >> "$EC"
kill "$NSMI_PID" 2>/dev/null || true
wait "$NSMI_PID" 2>/dev/null || true
"$PY" - <<'PY' > "$LOGS/peak_vram_v8b.txt" 2>&1
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/nvidia_smi_sample_v8b.csv"
vals, names, lines = [], set(), 0
try:
    for line in open(p, errors="replace"):
        lines += 1
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 4:
            names.add(parts[1])
            try: vals.append(int(float(parts[2])))
            except Exception: pass
except OSError as e:
    print("open_error=", e)
print("sample_lines=%d" % lines)
print("gpu_names=%s" % (";".join(sorted(names)) if names else "NONE"))
if vals:
    print("peak_vram_mib=%d" % max(vals))
    print("min_vram_mib=%d" % min(vals))
    print("peak_source=nvidia-smi memory.used MiB n_samples=%d" % len(vals))
    print("status=MEASURED")
else:
    print("peak_vram_mib=NOT_MEASURED")
    print("reason=no usable memory.used samples")
    print("status=NOT_MEASURED")
PY
echo "peak_vram_derivation rc=$?" >> "$EC"
echo "--- gpu_forward stdout tail ---"; tail -25 "$LOGS/gpu_forward_v8b.out"
echo "--- gpu_forward stderr tail ---"; tail -25 "$LOGS/gpu_forward_v8b.err"
echo "--- peak vram ---"; cat "$LOGS/peak_vram_v8b.txt"
sha256sum "$LOGS"/env_probe_gpu_v8b.txt "$LOGS"/nvidia_smi_L_gpu_v8b.txt \
  "$LOGS"/gpu_identity_v8b.txt "$LOGS"/nvidia_smi_sample_v8b.csv \
  "$LOGS"/time_v_gpu_forward_v8b.txt "$LOGS"/gpu_forward_v8b.out \
  "$LOGS"/gpu_forward_v8b.err "$LOGS"/peak_vram_v8b.txt > "$LOGS/logs_manifest_gpu_v8b.sha256" 2>&1
echo "=== T6_GPU_V8B END $(date -u +%FT%TZ) ==="
