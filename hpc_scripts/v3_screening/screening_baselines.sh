#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_screening_baselines.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_screening_baselines.err

# Deterministic naive reference baselines (last_value_naive, seasonal_naive).
# Runs on a COMPUTE node because it reads the full dataset and builds windows.
# No model is constructed, trained or loaded here.
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME

: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
cd "$DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

python scripts/innovation/runtime_guard.py --deployment-root "$DEPLOYMENT_ROOT"
python scripts/innovation/verify_source_snapshot.py \
    --deployment-root "$DEPLOYMENT_ROOT" \
    --manifest results/innovation/source_snapshot_manifest.json

echo "[baselines] job=${SLURM_JOB_ID} node=${SLURMD_NODENAME}"
python scripts/v3/screening_baselines.py
echo "[baselines] rc=0 at $(date)"
