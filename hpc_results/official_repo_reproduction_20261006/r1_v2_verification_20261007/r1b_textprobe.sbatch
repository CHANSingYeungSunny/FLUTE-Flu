#!/bin/bash
#SBATCH --job-name=r1b_txtprobe
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007/probe_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007/probe_%j.err
#
# C6 closure: per-checkpoint text-path probe. CPU ONLY -> ZERO GPU-hours.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
RUN=${ROOT}/r1_v2_20261007

if [[ "$(hostname)" == hpclogin* ]]; then echo "[probe] REFUSING login node"; exit 3; fi
export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

cd "${A0}" || exit 2
$PY -u "${VER}/probe_text_path_r1b.py" \
    --code-root "${A0}" --r1b "${R1B}" --run-dir "${RUN}" \
    --out "${VER}/R1B_CHECKPOINT_TEXT_PROBE.json"
rc=$?
echo "[probe] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}