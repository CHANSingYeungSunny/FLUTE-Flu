#!/bin/bash
#SBATCH --job-name=r1c
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1c_bounded_20261007/logs/r1c_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1c_bounded_20261007/logs/r1c_%A_%a.err
#
# R1-C BOUNDED GAP ANALYSIS. Track R only. Does not touch Track C.
# Submit: sbatch --array=<i>-<i> --export=ALL,SEED=<s>,ARM=<C0|C1> r1c_run.sbatch
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/r1c_bounded_20261007
DATA=${A0}/dataset/illness/national_illness.csv
DATA_SHA=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

HOR=(24 36 48 60); L=${HOR[$SLURM_ARRAY_TASK_ID]}
SEED=${SEED:-1000}
ARM=${ARM:-C1}
if [ "$ARM" = "C0" ]; then SCHED=constant; else SCHED=r1c_type1; fi
TAG="r1c_${ARM}__L${L}__seed${SEED}"
D="${OUT}/runs/${TAG}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[r1c] REFUSING login node"; exit 3; fi
if [ -f "${D}/manifest_${TAG}.json" ]; then echo "[r1c] ${TAG} complete - skip"; exit 0; fi
mkdir -p "${D}" "${OUT}/logs" "${OUT}/manifests"

GOT=$(sha256sum "${DATA}" | cut -d' ' -f1)
[[ "${GOT}" != "${DATA_SHA}" ]] && { echo "[r1c] FATAL dataset sha"; exit 4; }

echo "[r1c] job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID} arm=${ARM} sched=${SCHED} L=${L} seed=${SEED}"
export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
cd "${A0}" || exit 2

$PY -u "${VER}/r1c_c1_train.py" \
    --code-root "${A0}" --data "${DATA}" --r1b "${R1B}" \
    --horizon "${L}" --seed "${SEED}" --device cuda \
    --epochs 20 --lr 5e-4 --batch 16 --lr-schedule "${SCHED}" \
    --out "${D}"
rc=$?
el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
printf 'R1C\t%s_%s\t%s\tL%s\tseed%s\t%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${SLURM_ARRAY_TASK_ID}" "${ARM}" "${L}" "${SEED}" "${el:-?}" "${rc}" \
  >> "${OUT}/manifests/R1C_RESOURCE_LEDGER.csv"
echo "[r1c] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}
