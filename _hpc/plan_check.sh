#!/bin/bash -l
#SBATCH --job-name=miflu_plan
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-miflu-plan-%j.out
#
# CPU-only dry run of the controller's plan: prints, for all 40 (L, seed) cells,
# whether it is already verified / needs a forward-pass export / needs a retrain,
# which checkpoint the trust order picks, and the per-seed oracle it must match.
# No training, no GPU. It also re-verifies the cells already on disk (markers).
set -uo pipefail
module unload default 2>/dev/null
module load old_modules 2>/dev/null
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "${CODE}" || exit 1
echo "[plan] host=$(hostname) job=${SLURM_JOB_ID:-?} $(date -Is)"
"${PY}" -u miflu_controller_v2.py --plan
echo "[plan] rc=$?"
"${PY}" miflu_controller_v2.py --count
