#!/bin/bash
#SBATCH --job-name=s1es
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/s1_earlystop_20261008/logs/s1es_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/s1_earlystop_20261008/logs/s1es_%A_%a.err
#
# TRACK S — STOPPING-CRITERIA SUPPLEMENTARY EXPERIMENT.
#
# Purpose: give supervisor question 5, condition (2), a real measurement:
# does patience-based early stopping on validation loss (with rollback to the
# best weights) change the outcome versus the fixed-20-epoch + best-validation
# checkpoint rule that Track C actually used?
#
# This is NOT Track C (frozen, untouched) and NOT an R1-C candidate
# (the R1-C matrix is frozen at two entries; nothing is added here).
# Only the stopping rule differs; everything else is byte-identical to the
# Track C trainer.
#
# Submit: sbatch --array=<i>-<i> --export=ALL,SEED=<s>,PAT=<p> s1_earlystop.sbatch
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/s1_earlystop_20261008
DATA=${A0}/dataset/illness/national_illness.csv
DATA_SHA=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

HOR=(24 36 48 60); L=${HOR[$SLURM_ARRAY_TASK_ID]}
SEED=${SEED:-42}
PAT=${PAT:-5}
TAG="s1es_p${PAT}__L${L}__seed${SEED}"
D="${OUT}/runs/${TAG}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[s1es] REFUSING login node"; exit 3; fi
if [ -f "${D}/manifest_${TAG}.json" ]; then echo "[s1es] ${TAG} complete - skip"; exit 0; fi
mkdir -p "${D}" "${OUT}/logs" "${OUT}/manifests"

GOT=$(sha256sum "${DATA}" | cut -d' ' -f1)
[[ "${GOT}" != "${DATA_SHA}" ]] && { echo "[s1es] FATAL dataset sha"; exit 4; }

echo "[s1es] job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID} patience=${PAT} L=${L} seed=${SEED}"
export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
cd "${A0}" || exit 2

$PY -u "${VER}/s1_earlystop_train.py" \
    --code-root "${A0}" --data "${DATA}" --r1b "${R1B}" \
    --horizon "${L}" --seed "${SEED}" --device cuda \
    --epochs 20 --lr 5e-4 --batch 16 \
    --early-stop 1 --patience "${PAT}" \
    --out "${D}"
rc=$?
el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
printf 'S1ES\t%s_%s\tp%s\tL%s\tseed%s\t%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${SLURM_ARRAY_TASK_ID}" "${PAT}" "${L}" "${SEED}" "${el:-?}" "${rc}" \
  >> "${OUT}/manifests/S1ES_RESOURCE_LEDGER.csv"
echo "[s1es] rc=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}
