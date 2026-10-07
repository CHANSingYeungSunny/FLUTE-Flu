#!/bin/bash
#SBATCH --job-name=probe_text_gpu
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_text_gpu_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_text_gpu_%j.err
#
# text-path probe, GPU half. Identical script to the CPU half; only --device
# differs. stingy runs ONE concurrent job, so submit with
#   --dependency=afterok:<cpu_jobid>
#
# WRITES GO TO HOME (scratch user quota is over its limit).
# NEVER run this on the login node.
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HOME_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
A0=/scratch/sychan552/a0_replay
COMPAT=${HOME_ROOT}/hpc_compat

mkdir -p "${HOME_ROOT}/logs"

echo "[probe-gpu] host=$(hostname) start=$(date -u +%FT%TZ)"
echo "[probe-gpu] slurm job ${SLURM_JOB_ID} partition ${SLURM_JOB_PARTITION}"
if [[ "$(hostname)" == hpclogin* ]]; then
  echo "[probe-gpu] REFUSING to run on a login node"; exit 3
fi
nvidia-smi --query-gpu=name,memory.total --format=csv || true

export PYTHONPATH="${COMPAT}:${A0}:${PYTHONPATH:-}"

$PY -u "${HOME_ROOT}/scripts/probe_text_path_deterministic.py" \
    --repo "${A0}" \
    --compat "${COMPAT}" \
    --L 24 --batch 8 --device cuda --positive-control \
    --out "${HOME_ROOT}/probe/text_path_probe_gpu.json"

rc=$?
echo "[probe-gpu] exit=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}
