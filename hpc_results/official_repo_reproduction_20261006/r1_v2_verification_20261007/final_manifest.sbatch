#!/bin/bash
#SBATCH --job-name=manifestC
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/manifest_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/manifest_%j.err
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
VER=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007
if [[ "$(hostname)" == hpclogin* ]]; then echo "REFUSING login node"; exit 3; fi
$PY -u "${VER}/final_track_c_manifest.py"
exit $?
