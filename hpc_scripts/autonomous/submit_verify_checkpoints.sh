#!/bin/bash
# Read-only checkpoint-hash verification for the 52-cell one-time Test.
# Runs on a COMPUTE node via sbatch (never on the login node).
#SBATCH --partition=stingy
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --job-name=verify_ckpt
#SBATCH --output=/scratch/sychan552/innovation_deploy_root_v2_10/hpc_results/innovation/logs/verify_ckpt_%j.out
#SBATCH --error=/scratch/sychan552/innovation_deploy_root_v2_10/hpc_results/innovation/logs/verify_ckpt_%j.err

set -euo pipefail
ROOT=/scratch/sychan552/innovation_deploy_root_v2_10
cd "$ROOT"
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH

sacct -u sychan552 -S 2026-09-15 -o JobID,JobName,State,Elapsed,ExitCode,AllocTRES,NodeList --noheader \
  > results/innovation/final/_sacct_raw.txt 2>/dev/null || true

python -u hpc_scripts/autonomous/verify_test_checkpoints.py
