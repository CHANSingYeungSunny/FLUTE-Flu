#!/bin/bash
#SBATCH --job-name=r1_evaluate
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_eval_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_eval_%j.err
#
# R1-B evaluation: reload validation-selected checkpoints, evaluate Test ONCE,
# persist predictions/targets, score independently, run the text-path probe on
# each checkpoint.  CPU-ONLY, ZERO GPU-HOURS.  PREPARED - NOT SUBMITTED.
set -uo pipefail
R1=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1
PRE=/gpfs1/home/sychan552/official_repo_reproduction_20261006
mkdir -p "${R1}"/{scoring,preds}
[[ "$(hostname)" == hpclogin* ]] && { echo REFUSING; exit 3; }
echo "[r1eval] host=$(hostname) start=$(date -u +%FT%TZ)"
echo "[r1eval] NOTE: the evaluation entry point must be wired together with the"
echo "[r1eval] R1-B trainer, so that the same 7-channel contract is used."
echo "[r1eval] Then: independent scoring + text-path probe per checkpoint."
echo "[r1eval] BLOCKED until the R1-B trainer exists."
exit 0
