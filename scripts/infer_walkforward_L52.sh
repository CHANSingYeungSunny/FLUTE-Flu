#!/bin/bash
#SBATCH --job-name=MLFlu_infer_L52
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/home/sychan552/scratch/MLFLU/logs/infer_L52-%j.out
#SBATCH --error=/home/sychan552/scratch/MLFLU/logs/infer_L52-%j.err

ulimit -u 1000
set -e

# ── Mandatory after maintenance: unload default, load old_modules ──
module unload default && module load old_modules

# ── Activate conda env via absolute PATH ──
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
which python && python -c "import torch, pandas; print('env ok', torch.__version__)"

# ── Cache inside scratch ──
export HF_HOME=$HOME/scratch/MLFLU/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export TORCH_HOME=$HOME/scratch/MLFLU/.cache/torch
mkdir -p "$HF_HOME" "$TORCH_HOME"

echo "==== MLFlu INFER walk-forward L=52 (N=7) start: $(date) ===="
echo "host: $(hostname)  user: $(whoami)"
nvidia-smi || echo "[warn] nvidia-smi unavailable"

cd $HOME/scratch/MLFLU/scripts
# Requires checkpoints/best_miflu_L52.pth from train_q1_L52.sh (submit AFTER training).
# Writes results/ili/miflu_fulltest_walkforward.csv (single continuous series).
python generate_walkforward.py --ckpt /home/sychan552/scratch/MLFLU/checkpoints/best_miflu_L52.pth
echo "==== MLFlu INFER walk-forward L=52 (N=7) end: $(date) ===="
