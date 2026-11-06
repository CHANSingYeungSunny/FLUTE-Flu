#!/bin/bash
#SBATCH --job-name=t6_miflu_fix
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:12:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/miflufix_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/miflufix_%j.err
set -u
R=/gpfs1/home/sychan552/stage5_a2_durable
C=/gpfs1/scratch/sychan552/stage5_a2_durable/code
L=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/final_sweep
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
mkdir -p "$L"
echo "=== T6_MIFLU_FIX START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
nvidia-smi -L
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader,nounits -l 1 > "$L/miflu_fix_vram.csv" 2> "$L/miflu_fix_vram.err" &
PID=$!
/usr/bin/time -v -o "$L/miflu_fix_time_v.txt" timeout 600s "$PY" -u "$C/export_miflu_all7.py" \
  --cells 36:2023 --ckpt "$R/author_runs/ckpt_L36_s2023/best_miflu_L36.pth" \
  --out-dir /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/final_sweep_out/miflu_fix \
  --tag t6miflufix --device cuda > "$L/miflu_fix.stdout" 2> "$L/miflu_fix.stderr"
RC=$?
kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true
echo "MIFLU_FIX_RC=$RC"
"$PY" - <<'PY'
p="/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/final_sweep/miflu_fix_vram.csv"
vals=[]
for line in open(p,errors="replace"):
    parts=[x.strip() for x in line.split(",")]
    if len(parts)>=4:
        try: vals.append(int(float(parts[2])))
        except Exception: pass
print("miflu_fix peak_vram_mib=%d" % max(vals) if vals else "miflu_fix peak_vram_mib=NOT_MEASURED")
print("miflu_fix n_samples=%d" % len(vals))
PY
echo "--- stdout tail ---"; tail -8 "$L/miflu_fix.stdout"
echo "--- stderr tail ---"; tail -5 "$L/miflu_fix.stderr"
echo "=== T6_MIFLU_FIX END $(date -u +%FT%TZ) ==="
