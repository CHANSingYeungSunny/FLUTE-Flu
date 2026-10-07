#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v313_probe
#SBATCH --output=/scratch/sychan552/_v313/logs/slurm_%j_v313_probe.out
#SBATCH --error=/scratch/sychan552/_v313/logs/slurm_%j_v313_probe.err

# READ-ONLY checkpoint schema probe. Loads checkpoints and reports structure.
# No training, no evaluation, no writes into any deployment root.
set -euo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME

BASE=/scratch/sychan552/_v313
R=/scratch/sychan552/innovation_deploy_root_v3_clean6
LEG=/home/sychan552/innovation_durable/screening

cd "$BASE"
mkdir -p logs

python "$BASE/ckpt_schema_probe.py" --out "$BASE/probe_report.json" \
  "$R/results/v3_clean/runs/primary__nlinear__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__dlinear__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__patchtst__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__itransformer__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__gpt2_miflu__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__qwen_time_llm__L24__seed42__w1/checkpoints/best_val_mse.pt" \
  "$R/results/v3_clean/runs/primary__qwen_time_llm__L24__seed46__w1/checkpoints/best_val_mse.pt" \
  "$LEG/screening_calf_llm_L24_seed42/checkpoints/best_val_mse.pt" \
  "$LEG/screening_timecma_llm_L24_seed42/checkpoints/best_val_mse.pt" \
  "$LEG/screening_gpt2_miflu_L24_seed42/checkpoints/best_val_mse.pt"

echo "PROBE_DONE rc=$?"
