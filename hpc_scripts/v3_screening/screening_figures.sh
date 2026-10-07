#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_screening_figures.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_screening_figures.err

# Phase 2 figure generation, provenance sidecars and figure QA.
# Figures and QA are built ONLY from the 48 accepted durable Screening
# artifacts plus the validated baseline artifacts: no model is loaded, no
# checkpoint is restored, no inference is re-run.
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH

: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
cd "$DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

export SCREENING_DURABLE=/home/sychan552/innovation_durable/screening
export MPLBACKEND=Agg

echo "[figures] job=${SLURM_JOB_ID} node=${SLURMD_NODENAME}"
python scripts/v3/build_screening_figures.py
echo "[figures] figures rc=$? at $(date)"
# Gate v2 is intentionally NOT run here: it asserts `local_sync_passed`, which
# requires the evidence-pack hash to exist first. It runs after the pack is
# built and hashed.
