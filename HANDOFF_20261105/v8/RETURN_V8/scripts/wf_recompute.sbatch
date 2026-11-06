#!/bin/bash
#SBATCH --job-name=t1_wf_recompute_v8
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:40:00
#SBATCH --dependency=afterany:743850
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/recompute_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/recompute_%j.err
set -u
D=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
W=/gpfs1/home/sychan552/stage5_a2_durable/hpc_results/walk_forward
echo "host=$(hostname) start_utc=$(date -u +%FT%TZ) job=${SLURM_JOB_ID}"
echo "COMMAND=$PY -u $D/wf_recompute.py --wf-root $W --out-dir $D/v8_out --baseline $D/WF_RECOMPUTED_v7_baseline.csv"
/usr/bin/time -v "$PY" -u "$D/wf_recompute.py" \
  --wf-root "$W" --out-dir "$D/v8_out" \
  --baseline "$D/WF_RECOMPUTED_v7_baseline.csv"
RC=$?
echo "RECOMPUTE_RC=$RC end_utc=$(date -u +%FT%TZ)"
echo "=== output files + sha256 ==="
sha256sum "$D"/v8_out/* 2>/dev/null
exit "$RC"
