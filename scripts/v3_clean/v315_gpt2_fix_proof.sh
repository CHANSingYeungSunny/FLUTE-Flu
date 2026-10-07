#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=110G
#SBATCH --time=02:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v315_d15b
#SBATCH --output=/scratch/sychan552/_v315d/logs/slurm_%j_d15b.out
#SBATCH --error=/scratch/sychan552/_v315d/logs/slurm_%j_d15b.err

# D15b proof: the corrected architecture contract changes ONLY metadata.
# Compact tensor SHA-256 / keys / values must be identical with detection
# ON vs detection OFF, and identical to the pre-fix durable compact.
set -uo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v315d
R=/scratch/sychan552/innovation_deploy_root_v3_clean9
SCRATCH=/scratch/sychan552/innovation_deploy_root_v3_clean6/results/v3_clean/runs
GATE=$R/results/v3_clean/implementation/gate_571905/runs
DUR=/home/sychan552/innovation_durable/screening
mkdir -p "$BASE/logs" "$BASE/d15b"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

python -u "$BASE/verify_gpt2_contract_fix.py" \
  --out "$BASE/d15b" \
  --scratch-root "$SCRATCH" \
  --gate-runs "$GATE" \
  --durable "$DUR"
echo "D15B_DONE rc=$?"
