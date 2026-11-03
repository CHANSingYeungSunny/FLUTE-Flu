#!/usr/bin/env bash
# =============================================================================
# submit_miflu_paper_protocol.sh  —  MIFlu paper-protocol FOUR-HORIZON training
# CityUHK Burgundy HPC. On login node run ONLY:
#     sbatch /home/sychan552/scratch/CHATTIME/Chattime/submit_miflu_paper_protocol.sh
# Do NOT run python directly on the login node (no GPU, no model).
#
# PHASE-1 PROTOCOL (authoritative):
#   L ∈ {24, 36, 48, 60} are FOUR INDEPENDENT RUNS, each trained separately.
#   NOT a single rolling L=52 walk-forward. See docs/full_repo_audit_report.md §A.3.
#
# USAGE — submit the four horizons as FOUR SEPARATE jobs (one GPU each, stingy):
#   for L in 24 36 48 60; do
#     MIFLU_HORIZON=$L sbatch \
#       /home/sychan552/scratch/CHATTIME/Chattime/submit_miflu_paper_protocol.sh
#   done
#   (Each job trains one L with 10 reps; outputs go to data/results_miflu_paper_protocol_*.csv
#    and data/predictions_miflu_L{L}_paper_protocol.csv. Checkpoint: checkpoints/best_miflu_L{L}.pth)
#
# Passing a horizon: the script reads $MIFLU_HORIZON. If unset, it runs the full
# sweep [24,36,48,60] inside ONE job (not recommended on stingy 4h cap for all four
# at once — prefer one job per L as shown above).
#
# DEFAULT PARTITION: stingy + gpu:a100:1 (4h QOS cap). Never exceed --time=04:00:00.
# =============================================================================
#SBATCH --job-name=miflu_paper_L${MIFLU_HORIZON}
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_paper_L%j.out
#SBATCH --error=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_paper_L%j.err

set -euo pipefail

export USER_ID="sychan552"
export SCRATCH="/gpfs1/scratch/${USER_ID}/CHATTIME"
export PROJECT_ROOT="${SCRATCH}/Chattime"
export HF_HOME="${SCRATCH}/.cache"
export TRANSFORMERS_CACHE="$HF_HOME"
export HF_DATASETS_CACHE="$HF_HOME"
export CHATTIME_PROJECT_ROOT="$PROJECT_ROOT"

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

# Build the --horizon arg (one L per job is the intended Phase-1 pattern).
HORIZON_ARG=""
if [ -n "${MIFLU_HORIZON:-}" ]; then
  HORIZON_ARG="--horizon ${MIFLU_HORIZON}"
  echo "[slurm] Phase-1 single-horizon mode: L=${MIFLU_HORIZON}"
else
  echo "[slurm] Full sweep mode: L ∈ {24,36,48,60} (one job)"
fi

echo "[slurm] launching: python scripts/train_miflu.py ${HORIZON_ARG} --reps 10 --epochs 20 --batch 16 --seed 42"
python scripts/train_miflu.py ${HORIZON_ARG} --reps 10 --epochs 20 --batch 16 --seed 42

echo "[slurm] done. Paper-protocol outputs under ${PROJECT_ROOT}/data/ and ${PROJECT_ROOT}/checkpoints/"
