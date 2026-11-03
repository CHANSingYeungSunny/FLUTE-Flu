#!/usr/bin/env bash
# =============================================================================
# submit_miflu_array.sh  —  MIFlu paper-protocol L=48/60 as a SLURM JOB ARRAY
# CityUHK Burgundy HPC. On login node run ONLY:
#     sbatch --array=0-1%1 /home/sychan552/scratch/CHATTIME/Chattime/submit_miflu_array.sh
#
# NOTE: L=24 and L=36 already COMPLETED (best_miflu_L24.pth / best_miflu_L36.pth
# present, results CSVs written). This array covers only the two remaining horizons.
#
# The array index maps to a horizon (NOT an env var at submit time):
#     task 0 -> L=48
#     task 1 -> L=60
# The `%1` throttle guarantees AT MOST ONE sub-task runs at a time, which:
#   (a) avoids the account "max 1 pending job" QOS limit (a job array counts
#       as a single submission, not 3), and
#   (b) avoids the prior "same-node concurrent training -> NaN" pitfall
#       (sub-tasks run strictly sequentially, never concurrently).
#
# Per-sub-task outputs (logs/checkpoints/CSV) are tagged with the resolved L.
# =============================================================================
#SBATCH --job-name=miflu_paper_array
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_array_L%a.out
#SBATCH --error=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_array_L%a.err

set -euo pipefail

export USER_ID="sychan552"
export SCRATCH="/gpfs1/scratch/${USER_ID}/CHATTIME"
export PROJECT_ROOT="${SCRATCH}/Chattime"
export HF_HOME="${SCRATCH}/.cache"
export TRANSFORMERS_CACHE="$HF_HOME"
export HF_DATASETS_CACHE="$HF_HOME"
export CHATTIME_PROJECT_ROOT="$PROJECT_ROOT"

# Map SLURM_ARRAY_TASK_ID -> horizon.
# L=24 and L=36 already COMPLETED; this array covers only L=48 and L=60.
case "${SLURM_ARRAY_TASK_ID}" in
  0) MIFLU_HORIZON=48 ;;
  1) MIFLU_HORIZON=60 ;;
  *) echo "[slurm][BLOCKER] unexpected SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID} (expected 0-1)"; exit 3 ;;
esac
echo "[slurm] array task ${SLURM_ARRAY_TASK_ID} -> L=${MIFLU_HORIZON}"

# Module preamble — MUST run first (post-2026-maintenance requirement).
module unload default && module load old_modules

# Conda activation via PATH-prepend (NOT `conda activate` — fails on GPU nodes).
export PATH="/home/${USER_ID}/.conda/envs/mlflu_hpc/bin:$PATH"
echo "[slurm] python: $(which python) -> $(python --version 2>&1)"

# Deps safeguard (per HPC_GUIDE §4).
python -c "import torch, numpy, scipy, matplotlib, pandas; print('[slurm] deps ok')" \
  || { echo "[slurm][BLOCKER] missing runtime dep"; exit 3; }

mkdir -p "${PROJECT_ROOT}/logs" "${PROJECT_ROOT}/data" "${PROJECT_ROOT}/checkpoints"
cd "${PROJECT_ROOT}"
echo "[slurm] PWD=$(pwd)"
echo "[slurm] HF_HOME=${HF_HOME}"

echo "[slurm] launching: python scripts/train_miflu.py --horizon ${MIFLU_HORIZON} --reps 10 --epochs 20 --batch 16 --seed 42"
python scripts/train_miflu.py --horizon ${MIFLU_HORIZON} --reps 10 --epochs 20 --batch 16 --seed 42

echo "[slurm] done (L=${MIFLU_HORIZON}). Paper-protocol outputs under ${PROJECT_ROOT}/data/ and ${PROJECT_ROOT}/checkpoints/"
