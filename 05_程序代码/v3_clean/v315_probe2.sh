#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v315_probe2
#SBATCH --output=/scratch/sychan552/_v315d/logs/slurm_%j_probe2.out
#SBATCH --error=/scratch/sychan552/_v315d/logs/slurm_%j_probe2.err

# Decisive identity probe for the MIFlu (gpt2_miflu) frozen backbone.
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
mkdir -p "$BASE/logs"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

python -u "$BASE/probe_gpt2_identity.py" --out "$BASE/probe2.json" \
  --models gpt2_miflu without_lora zero_text nlinear qwen_time_llm
echo "PROBE2_DONE rc=$?"
