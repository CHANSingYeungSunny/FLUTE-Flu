#!/bin/bash
#SBATCH --job-name=trackC_score
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/score_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/score_%j.err
#
# Track C scoring — CPU ONLY, zero GPU-hours.
# Moved here from an ssh one-liner: the canonical scorer reads the full 96-cell
# key contract and is far too heavy for a login node.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
VER=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007
B=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007

if [[ "$(hostname)" == hpclogin* ]]; then echo "[score] REFUSING login node"; exit 3; fi
mkdir -p "${B}/logs"

echo "[score] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
$PY -u "${VER}/score_track_c.py" --out "${B}"
rc=$?
echo "[score] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}