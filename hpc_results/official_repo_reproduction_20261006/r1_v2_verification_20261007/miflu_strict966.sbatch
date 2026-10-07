#!/bin/bash
#SBATCH --job-name=miflu_c
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/miflu_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007/logs/miflu_%A_%a.err
#
# TRACK C — official-repository-based corrected MIFlu, author-966 strict
# containment. Submit: sbatch --array=<i>-<i> --export=ALL,SEED=<s> miflu_strict966.sbatch
# i = horizon index (0..3 -> L 24/36/48/60).  One element per submission.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/strict966_championship_20261007
DATA=${A0}/dataset/illness/national_illness.csv
DATA_SHA=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

HOR=(24 36 48 60); L=${HOR[$SLURM_ARRAY_TASK_ID]}
SEED=${SEED:-42}
TAG="miflu_strict966__L${L}__seed${SEED}"
D="${OUT}/runs/${TAG}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[C] REFUSING login node"; exit 3; fi

if [ -f "${D}/manifest_${TAG}.json" ] && [ -f "${D}/test_predictions_${TAG}.csv" ]; then
  echo "[C] ${TAG} already complete - skipping"; exit 0
fi
mkdir -p "${D}" "${OUT}/logs" "${OUT}/manifests"

GOT=$(sha256sum "${DATA}" | cut -d' ' -f1)
[[ "${GOT}" != "${DATA_SHA}" ]] && { echo "[C] FATAL dataset sha ${GOT}"; exit 4; }
case "${D}" in /gpfs1/home/*) ;; *) echo "[C] FATAL output not under HOME"; exit 5;; esac

echo "[C] job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID} host=$(hostname) L=${L} seed=${SEED} start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[C] gpu: /'

export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

cd "${A0}" || exit 2
$PY -u "${VER}/miflu_strict966_train.py" \
    --code-root "${A0}" --data "${DATA}" --r1b "${R1B}" \
    --horizon "${L}" --seed "${SEED}" --device cuda \
    --epochs 20 --lr 5e-4 --batch 16 \
    --out "${D}"
rc=$?
echo "[C] rc=${rc} end=$(date -u +%FT%TZ)"

el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
g=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o AllocTRES%80 2>/dev/null | grep -o 'gres/gpu:a100=[0-9]*' | head -1 | cut -d= -f2)
mr=$(sacct -j "${SLURM_JOB_ID}" --noheader -o MaxRSS 2>/dev/null | sort -rn | head -1 | tr -d ' ')
printf 'MIFLU_STRICT966\t%s_%s\tL%s\tseed%s\t%s\tgpu=%s\tmaxrss=%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${SLURM_ARRAY_TASK_ID}" "${L}" "${SEED}" "${el:-unknown}" "${g:-0}" "${mr:-?}" "${rc}" \
  >> "${OUT}/manifests/TRACK_C_MIFLU_RESOURCE_LEDGER.csv"
exit ${rc}