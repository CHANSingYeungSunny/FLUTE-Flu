#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_clean_gate.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_clean_gate.err

# clean-v3 compute-node pre-execution Gate.
# Exercises every Wave-1 runtime path through the REAL clean_runner.py and
# verifies the frozen contracts. Runs on a compute node only.
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export MPLBACKEND=Agg

: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
cd "$DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

echo "[gate] job=${SLURM_JOB_ID} node=${SLURMD_NODENAME} root=${DEPLOYMENT_ROOT}"
python scripts/innovation/clean_gate.py
echo "[gate] rc=$? at $(date)"
