#!/bin/bash
#SBATCH --job-name=s5_score
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=16G
#SBATCH --time=00:40:00
#SBATCH --output=results/stage5/logs/score_%j.out
#SBATCH --error=results/stage5/logs/score_%j.err
#
# Stage 5 A2 — the single, unified Test-scoring entry (runs on a GPU compute node).
# Ordering inside this one job:
#   step 1  lock all 36 learned-fit checkpoints (SHA-256 + validation-selection
#           evidence). Fails closed if any fit is missing or unevidenced.
#   step 2  Test inference for those 36 checkpoints + the 8 deterministic
#           baselines, from the locked files only.
#   step 3  independent recomputation of average_MSE_4L from the dumped
#           prediction artefacts, cross-checked against step 2's tables.
# HORIZONS env var (optional): comma-separated subset, e.g. "24".
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
OUT=results/stage5/scoring
mkdir -p "$OUT"

echo "[score] step 1/3 — checkpoint lock  $(date -u +%FT%TZ)"
$PY -u scripts/build_lock_stage5.py --root results/stage5 --out "$OUT"

echo "[score] step 2/3 — Test scoring  $(date -u +%FT%TZ)"
if [ -n "${HORIZONS:-}" ]; then
  $PY -u scripts/score_test_stage5.py \
    --ckpt-root results/stage5/ckpt/author_966 \
    --export-dir "$OUT" --device cuda --horizons "$HORIZONS"
else
  $PY -u scripts/score_test_stage5.py \
    --ckpt-root results/stage5/ckpt/author_966 \
    --export-dir "$OUT" --device cuda
fi

echo "[score] step 3/3 — independent recomputation  $(date -u +%FT%TZ)"
$PY -u recovery/stage5/recompute_from_artifacts.py --scoring "$OUT"

echo "[score] done  $(date -u +%FT%TZ)"
