#!/bin/bash
#SBATCH --job-name=s6_score
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=results/stage6/logs/score_%j.out
#SBATCH --error=results/stage6/logs/score_%j.err
#
# Stage 6 — unified Test scoring for the NINE-model comparison (the A2 trio
# plus the six additional backbones), plus the independent recomputation.
# Runs only after all 108 learned checkpoints exist and are locked.
set -eo pipefail
cd /scratch/sychan552/a2_stage5

export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export ACTIVE_PROFILE=author_966
export MPLBACKEND=Agg

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=results/stage6/scoring
mkdir -p "$OUT"

echo "[s6score] step 0/4 — expose the A2 trio under the stage6 roots  $(date -u +%FT%TZ)"
bash recovery/stage6/prepare_lock.sh

echo "[s6score] step 1/4 — lock all 108 checkpoints (9 models x 4 L x 3 seeds)  $(date -u +%FT%TZ)"
$PY -u scripts/build_lock_stage5.py --root results/stage6 --out "$OUT" \
  --template results/stage6/lock_templates.json

echo "[s6score] step 2/4 — Test scoring (108 learned fits + 8 baselines)  $(date -u +%FT%TZ)"
$PY -u scripts/score_test_stage5.py --stage6 \
  --ckpt-root results/stage6/ckpt/author_966 \
  --export-dir "$OUT" --device cuda

echo "[s6score] step 3/4 — independent recomputation from artefacts  $(date -u +%FT%TZ)"
$PY -u recovery/stage6/recompute_eight.py --scoring "$OUT"

echo "[s6score] done $(date -u +%FT%TZ)"
