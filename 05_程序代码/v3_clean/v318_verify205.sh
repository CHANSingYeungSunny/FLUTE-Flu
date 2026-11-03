#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=110G
#SBATCH --time=03:50:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v318_verify205
#SBATCH --output=/scratch/sychan552/_v318d/logs/slurm_%j_verify205.out
#SBATCH --error=/scratch/sychan552/_v318d/logs/slurm_%j_verify205.err

# ONE verification job for all 205 accepted rows (Path A: same-source re-export
# from the ORIGINAL full checkpoint + strict restoration + hash checks).
# It never trains, never rewrites a compact package.
set -uo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v318d
R=/scratch/sychan552/innovation_deploy_root_v3_clean12
mkdir -p "$BASE/logs" "$BASE/verify205"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

python -u "$BASE/verify_205_rows.py" \
  --inventory "$BASE/inventory_205.json" \
  --durable-root /home/sychan552/innovation_durable/screening \
  --out-dir "$BASE/verify205"
echo "VERIFY205_DONE rc=$?"
