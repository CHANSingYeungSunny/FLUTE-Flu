#!/bin/bash
#SBATCH --job-name=miflu_tr_run
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/historical_replacement_20261007/logs/run_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/historical_replacement_20261007/logs/run_%A_%a.err
#
# PHASE D — historical MIFlu replacement, remaining seeds.
# Submit with:  sbatch --array=<i>-<i> --export=ALL,SEED=<s> miflu_transfer_run.sbatch
# i = horizon index (0..3 -> L 24/36/48/60).  One element per submission (MaxSubmit=1).
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/historical_replacement_20261007
DATA=/scratch/sychan552/innovation_deploy_root_v3_clean14/data/raw/national_illness_raw.csv
DATA_SHA=0a0648000066e12fe499f98693885b88ed3bc29fc8daca7f3af171b1bac86088

HOR=(24 36 48 60); L=${HOR[$SLURM_ARRAY_TASK_ID]}
SEED=${SEED:-42}
TAG="miflu_transfer__L${L}__seed${SEED}"
D="${OUT}/runs/${TAG}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[run] REFUSING login node"; exit 3; fi

# resumable: never redo a completed run
if [ -f "${D}/manifest_${TAG}.json" ] && [ -f "${D}/validation_predictions_${TAG}.csv" ]; then
  echo "[run] ${TAG} already complete - skipping"; exit 0
fi
mkdir -p "${D}"

GOT=$(sha256sum "${DATA}" | cut -d' ' -f1)
[[ "${GOT}" != "${DATA_SHA}" ]] && { echo "[run] FATAL dataset sha ${GOT}"; exit 4; }
case "${D}" in /gpfs1/home/*) ;; *) echo "[run] FATAL output not under HOME"; exit 5;; esac

echo "[run] job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID} host=$(hostname) L=${L} seed=${SEED} start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[run] gpu: /'

export PYTHONPATH="${COMPAT}:${A0}:${R1B}:${VER}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

cd "${A0}" || exit 2
$PY -u "${VER}/miflu_transfer_train.py" \
    --code-root "${A0}" --data "${DATA}" --r1b "${R1B}" \
    --horizon "${L}" --seed "${SEED}" --device cuda \
    --epochs 20 --lr 5e-4 --batch 16 --patience 7 \
    --out "${D}"
rc=$?
echo "[run] rc=${rc} end=$(date -u +%FT%TZ)"

el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
g=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o AllocTRES%80 2>/dev/null | grep -o 'gres/gpu:a100=[0-9]*' | head -1 | cut -d= -f2)
printf 'MIFLU_TRANSFER\t%s_%s\tL%s\tseed%s\t%s\tgpu=%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${SLURM_ARRAY_TASK_ID}" "${L}" "${SEED}" "${el:-unknown}" "${g:-0}" "${rc}" \
  >> "${OUT}/manifests/GPU_LEDGER_TRANSFER.tsv"
exit ${rc}