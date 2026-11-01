#!/bin/bash -l
#SBATCH --job-name=miflu_c2
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%x-%j.out

# One serial 12-cell job, not a 12-task array: guide says stingy permits one job.
# Prior Track C cost ~1.51 A100 hours; 2h is justified headroom, below the 4h cap.
set -euo pipefail
module unload default
module load old_modules
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
MIFLU_PYTHON="${C2_PYTHON:-/home/sychan552/.conda/envs/mlflu_hpc/bin/python}"
export HF_HOME="${C2_HF_HOME:-/home/sychan552/.cache/huggingface}"
unset TRANSFORMERS_CACHE
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
MIFLU_DATA_ROOT="${MIFLU_ROOT}/inputs/handoff"
MIFLU_AUTHOR="${MIFLU_DATA_ROOT}/02_author_repo/code"
MIFLU_RUN="${MIFLU_ROOT}/runs/c2_${SLURM_JOB_ID:?submit with sbatch}"
mkdir -p "${MIFLU_RUN}" "${MIFLU_ROOT}/logs"
exec > >(tee -a "${MIFLU_ROOT}/logs/c2_${SLURM_JOB_ID}.log") 2>&1
trap '"${MIFLU_PYTHON}" "${MIFLU_ROOT}/code/aggregate_c2.py" --runs "${MIFLU_RUN}" --out "${MIFLU_RUN}/paper_tables" --handoff "${MIFLU_DATA_ROOT}"' EXIT
"${MIFLU_PYTHON}" "${MIFLU_ROOT}/code/hpc_preflight.py" --root "${MIFLU_ROOT}" --kind c2 --out "${MIFLU_RUN}/preflight.json"
for MIFLU_L in 24 36 48 60; do
  for MIFLU_SEED in 42 43 44; do
    "${MIFLU_PYTHON}" -u "${MIFLU_ROOT}/code/candidate_c2_train.py" \
      --code-root "${MIFLU_AUTHOR}" \
      --data "${MIFLU_AUTHOR}/dataset/illness/national_illness.csv" \
      --r1b "${MIFLU_DATA_ROOT}/05b_r1b_model" \
      --horizon "${MIFLU_L}" --seed "${MIFLU_SEED}" --device cuda \
      --epochs 20 --lr 0.0005 --batch 16 --lr-schedule r1c_type1 \
      --out "${MIFLU_RUN}/L${MIFLU_L}_seed${MIFLU_SEED}"
  done
done
