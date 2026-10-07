#!/bin/bash
#SBATCH --job-name=finalizeC
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/finalize_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/finalize_%j.err
#
# Track C deliverable finalisation — CPU ONLY, zero GPU-hours.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
VER=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007
if [[ "$(hostname)" == hpclogin* ]]; then echo "[fin] REFUSING login node"; exit 3; fi
echo "[fin] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
$PY -u "${VER}/finalize_track_c.py"
rc=$?
echo "[fin] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}