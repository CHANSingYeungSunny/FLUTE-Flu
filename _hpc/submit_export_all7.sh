#!/bin/bash -l
#SBATCH --job-name=miflu_all7
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-miflu-all7-%j.out
#
# Forward-pass-only re-export of MIFlu predictions for ALL 7 variables, from the
# saved reproduction-protocol checkpoints. No training happens here.
#
# One job per horizon so the four run in parallel; a cell whose 7-variable CSV
# already exists is skipped, so re-submitting after the training jobs finish
# only does the missing work.
set -uo pipefail
module unload default
module load old_modules
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "${CODE}"

if [ -n "${LH:-}" ]; then
  echo "[all7] horizons: ${LH}"
  "${PY}" -u export_miflu_all7.py --all --horizons ${LH} --device cpu
else
  "${PY}" -u export_miflu_all7.py --all --device cpu
fi
