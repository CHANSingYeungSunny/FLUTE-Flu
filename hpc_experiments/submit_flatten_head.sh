#!/bin/bash -l
# Flatten-head experiment: retrain MIFlu with the reference-faithful
# per-variable Flatten_Head (TSL style) instead of the legacy mean-pooled head.
#
# Hypothesis: the legacy head mean-pools all 294 (=7 vars x 42 patches) tokens into
# ONE 768-d vector before projecting to 168 outputs, destroying variable identity
# and patch order. The Flatten_Head keeps each variable's patch sequence, giving
# 774,168 head params vs 129,192.
#
# 12 cells = 4 horizons x 3 seeds, matching the existing Track C protocol.
#SBATCH --job-name=miflu_flatten
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-flatten-%j.out

set -euo pipefail
module unload default
module load old_modules

CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/home/sychan552/stage5_a2_durable/flatten_runs
mkdir -p "${OUT}"

# 1 = reference-faithful per-variable Flatten_Head (the fix)
export MIFLU_FLATTEN_HEAD=1

cd "${CODE}"
echo "[flatten] MIFLU_FLATTEN_HEAD=${MIFLU_FLATTEN_HEAD}"
"${PY}" -c "import torch; print('torch', torch.__version__)"

for L in 24 36 48 60; do
  for SEED in 42 43 44; do
    echo "=================== L=${L} seed=${SEED} ==================="
    "${PY}" -u train_miflu.py \
      --profile author_966 \
      --horizon "${L}" \
      --seed "${SEED}" \
      --epochs 20 \
      --batch 16 \
      --containment strict \
      --export-dir "${OUT}/L${L}_s${SEED}" \
      --ckpt-dir   "${OUT}/ckpt_L${L}_s${SEED}" \
      || echo "[warn] L=${L} seed=${SEED} failed"
  done
done

echo "[flatten] DONE"
