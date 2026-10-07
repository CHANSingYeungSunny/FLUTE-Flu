#!/bin/bash
#SBATCH --job-name=miflu_fig_L24
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --time=01:00:00
#SBATCH --output=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_fig_L24_%j.out
#SBATCH --error=/home/sychan552/scratch/CHATTIME/Chattime/logs/miflu_fig_L24_%j.err

# HPC_GUIDE §4 — module preamble FIRST
module unload default && module load old_modules
export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

python scripts/generate_figures_from_ckpt.py \
  --device cuda \
  --ckpt /scratch/sychan552/CHATTIME/Chattime/hpc_results/journal_evidence/full_H24/reps_1_to_10/rep_01/checkpoints/best_model_L24.pt \
  --out /scratch/sychan552/CHATTIME/Chattime/hpc_results/journal_evidence/logs/fig_miflu_eval_continuous_L24_from_ckpt.png
