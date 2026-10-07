#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_ablation__without_dataset_information__L60__seed50__w1.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_ablation__without_dataset_information__L60__seed50__w1.err

# clean-v3 Wave 1 row: ablation__without_dataset_information__L60__seed50__w1
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
: "${INNOVATION_DEPLOYMENT_ROOT:?must be set}"
: "${CONFIRM_INNOVATION_SUBMIT:=NO}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] submission_attempted=false"
  exit 0
fi
cd "$INNOVATION_DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs
python scripts/innovation/clean_runner.py --run-key ablation__without_dataset_information__L60__seed50__w1
