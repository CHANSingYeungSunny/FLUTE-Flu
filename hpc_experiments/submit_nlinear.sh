#!/bin/bash -l
#SBATCH --job-name=nlinear_add
#SBATCH --partition=gpu_v100s
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-nlinear-%j.out
#
# Adds NLinear as the linear representative of the expanded benchmark
# (DLinear is already in the essay's Table V, so it is a replication reference,
# not a new baseline). 12 cells: 4 horizons x 3 seeds. Runs on gpu_v100s so it
# does not compete with the MIFlu L48/L60 job on stingy.
set -uo pipefail
module unload default
module load old_modules
CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
EXP=/home/sychan552/stage5_a2_durable/expanded_runs
cd "${CODE}"
for L in 24 36 48 60; do
  for s in 42 43 44; do
    d="${EXP}/nlinear_L${L}_s${s}"
    [ -f "${d}/pred_nlinear_L${L}_s${s}.npz" ] && { echo "[skip] nlinear L=${L} s=${s}"; continue; }
    "${PY}" -u train_backbone_966.py --backbone nlinear --horizon "${L}" --seed "${s}" \
      --profile author_966 --containment strict \
      --export-dir "${d}" --ckpt-dir "${d}/ckpt" || echo "[FAIL] nlinear L=${L} s=${s}"
  done
done
echo "[nlinear] DONE $(date -Is)"
