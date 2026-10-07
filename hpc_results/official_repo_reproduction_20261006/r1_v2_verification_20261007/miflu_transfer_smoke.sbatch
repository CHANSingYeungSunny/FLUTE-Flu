#!/bin/bash
#SBATCH --job-name=miflu_tr_smoke
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/historical_replacement_20261007/logs/smoke_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/historical_replacement_20261007/logs/smoke_%j.err
#
# Transfer smoke test: shape / path / contract validation only.
# CPU ONLY -> ZERO GPU-hours.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/historical_replacement_20261007
DATA=/scratch/sychan552/innovation_deploy_root_v3_clean14/data/raw/national_illness_raw.csv

mkdir -p "${OUT}"/{logs,preds,ckpt,manifests,scoring}
if [[ "$(hostname)" == hpclogin* ]]; then echo "[smoke] REFUSING login node"; exit 3; fi
export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

echo "[smoke] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
echo "[smoke] data sha: $(sha256sum ${DATA} | cut -d' ' -f1)"

cd "${A0}" || exit 2
$PY -u "${VER}/miflu_transfer_train.py" \
    --code-root "${A0}" --data "${DATA}" --r1b "${R1B}" \
    --horizon 24 --seed 42 --device cpu --epochs 1 --batch 4 \
    --smoke --smoke-steps 4 \
    --out "${OUT}/smoke"
rc=$?
echo "[smoke] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}