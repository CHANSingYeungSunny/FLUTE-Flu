#!/bin/bash
#SBATCH --job-name=q6_attn_audit
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --output=/home/sychan552/scratch/CHATTIME/Chattime/logs/q6_attn_audit_%j.out
#SBATCH --error=/home/sychan552/scratch/CHATTIME/Chattime/logs/q6_attn_audit_%j.err

# HPC_GUIDE §4 — module preamble FIRST
module unload default && module load old_modules
export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

python scripts/q6_text_attention_audit.py
