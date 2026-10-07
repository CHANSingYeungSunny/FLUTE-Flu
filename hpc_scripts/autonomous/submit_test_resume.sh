#!/bin/bash
# RESUME of the ONE-TIME final Test evaluation — submitted as a Slurm job.
#
# The single-use authorization receipt already exists, so this only continues the
# SAME immutable evaluation (test_eval_id is read from the receipt). It NEVER
# creates a second Test evaluation, manifest or receipt: run_one_time_test.py
# skips any cell whose metric file already exists (create-only) and only creates
# the manifest when absent.
#
# Runs on a COMPUTE node via sbatch — never on the login node.
# (Incident 2026-09-16: launching this with `nohup` on hpclogin02 drove the
#  process into D state and made the login node unable to fork new SSH sessions.
#  Permanent rule: all compute goes through sbatch.)
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --job-name=onetime_test_resume
#SBATCH --output=/scratch/sychan552/innovation_deploy_root_v2_10/hpc_results/innovation/logs/test_resume_%j.out
#SBATCH --error=/scratch/sychan552/innovation_deploy_root_v2_10/hpc_results/innovation/logs/test_resume_%j.err

set -euo pipefail

ROOT=/scratch/sychan552/innovation_deploy_root_v2_10
cd "$ROOT"

# Optional legacy module preamble (MOTD: needed only for pre-2021 software).
if command -v module >/dev/null 2>&1; then
  module unload default 2>/dev/null || true
  module load old_modules 2>/dev/null || true
fi

export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
# Environment-only thread caps (do not alter scientific inputs or checkpoints).
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "[test_resume] host=$(hostname) start=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "[test_resume] job=$SLURM_JOB_ID root=$ROOT"

python -u hpc_scripts/autonomous/run_one_time_test.py \
  --deployment-root "$ROOT" \
  --expect-manifest-sha 558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5 \
  --expect-cohort-sha 8695b8ea6151c5dd350411449141e4e547c7bd0aaa263e402695279477e0327d

echo "[test_resume] finished=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
