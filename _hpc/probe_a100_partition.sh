#!/bin/bash -l
#SBATCH --job-name=a100probe
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:03:00
#SBATCH --output=slurm-a100probe-%j.out
#
# PROBE ONLY (rule 13b/c): reports the MEASURED GPU model on the gpu_a100
# partition, so we know whether those nodes are the same A100-SXM4-80GB as the
# 204 benchmark cells before moving any publication-grade work there.
set -uo pipefail
module unload default 2>/dev/null
module load old_modules 2>/dev/null
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo "[probe] host=$(hostname) node=${SLURM_NODELIST:-?} part=${SLURM_JOB_PARTITION:-?} job=${SLURM_JOB_ID:-?}"
"${PY}" -c "
import torch
print('[probe] MEASURED gpu=', torch.cuda.get_device_name(0),
      'cap=', torch.cuda.get_device_capability(0),
      'vram_GiB=', round(torch.cuda.get_device_properties(0).total_memory/2**30, 1),
      'count=', torch.cuda.device_count())
"
