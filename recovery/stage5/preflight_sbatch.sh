#!/bin/bash
#SBATCH --job-name=s5_preflight
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=results/stage5/logs/preflight_%j.out
#SBATCH --error=results/stage5/logs/preflight_%j.err
#
# Stage 5 — compute-node preflight. Authorized (2 GPU-h ceiling, stingy/A100).
# Uses train/validation inputs only; never reads or scores the Test split.
set -eo pipefail

cd "${SLURM_SUBMIT_DIR:-/scratch/sychan552/a2_stage5}"

PYTHONPATH="${SLURM_SUBMIT_DIR:-/scratch/sychan552/a2_stage5}/scripts${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH
export HF_HOME="${HF_HOME:-/home/sychan552/.cache/huggingface}"
export HF_DATASETS_CACHE="$HF_HOME"
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export ACTIVE_PROFILE=author_966
export A2_REQUIRE_STRICT=1

mkdir -p results/stage5/logs

/home/sychan552/.conda/envs/mlflu_hpc/bin/python \
  recovery/stage5/preflight_compute_node.py \
  --profile author_966 --horizon 24 --containment strict \
  --out recovery/stage5/preflight_result.json

echo "[preflight] done"
