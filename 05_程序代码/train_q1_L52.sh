#!/bin/bash
#SBATCH --job-name=MLFlu_train_L52
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/home/sychan552/scratch/MLFLU/logs/train_L52-%j.out
#SBATCH --error=/home/sychan552/scratch/MLFLU/logs/train_L52-%j.err

ulimit -u 1000

# ── Mandatory after maintenance: unload default, load old_modules ──
module unload default && module load old_modules

# ── Activate conda env via absolute PATH (avoids conda load issues on GPU nodes) ──
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
which python && python -c "import torch, pandas; print('env ok', torch.__version__)"

# ── Cache inside scratch (protect 50GB home quota) ──
export HF_HOME=$HOME/scratch/MLFLU/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export TORCH_HOME=$HOME/scratch/MLFLU/.cache/torch
mkdir -p "$HF_HOME" "$TORCH_HOME"

echo "==== MLFlu TRAIN L=52 (N=7) start: $(date) ===="
echo "host: $(hostname)  user: $(whoami)"
nvidia-smi || echo "[warn] nvidia-smi unavailable"

cd $HOME/scratch/MLFLU/scripts
# N=7, single horizon L=52 (ChatTime walk-forward protocol).
# 10 reps x 20 epochs; best-val-loss rep saved to checkpoints/best_miflu_L52.pth.
# Avoid submitting multiple training jobs concurrently on one node (NaN-rep risk).
BATCH=${BATCH:-16}
python train_miflu.py --horizon 52 --reps 10 --epochs 20 --batch $BATCH --seed 42
echo "==== MLFlu TRAIN L=52 (N=7) end: $(date) ===="
