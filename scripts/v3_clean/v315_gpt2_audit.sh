#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v315_gpt2audit
#SBATCH --output=/scratch/sychan552/_v315d/logs/slurm_%j_gpt2audit.out
#SBATCH --error=/scratch/sychan552/_v315d/logs/slurm_%j_gpt2audit.err

# READ-ONLY structural audit of the GPT-2 family architecture contract.
# Determines where the nested frozen GPT-2 backbone actually lives inside
# `inner.*` so the contract metadata can be corrected WITHOUT touching any
# compact tensor selection, checkpoint content, model, prediction or metric.
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

python -u "$BASE/gpt2_contract_audit.py" --out "$BASE/gpt2_contract_audit.json" \
  --models gpt2_miflu \
           without_dataset_information without_task_instruction \
           without_input_variable_description without_lora \
           without_multimodality without_lora_and_multimodality \
           zero_text shuffled_text \
           nlinear qwen_time_llm
echo "AUDIT_DONE rc=$?"
