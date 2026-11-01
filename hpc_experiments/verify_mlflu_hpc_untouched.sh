#!/bin/bash
#SBATCH --job-name=mlflu_hpc_guard
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=slurm-hpcguard-%j.out
#
# Step 5: prove the NEW environment work did not touch mlflu_hpc.
# mlflu_hpc must still have transformers 4.57.6 - the 16 benchmark arms depend on
# it. Both the pip metadata and a real import are reported.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo "host=$(hostname) job=${SLURM_JOB_ID:-none}"; date -Is
"$PY" -V
echo '--- metadata ---'
"$PY" -m pip show transformers torch 2>&1 | grep -E '^(Name|Version):'
echo '--- real import (compute node, not the login node) ---'
"$PY" -c "import transformers, torch; print('mlflu_hpc transformers', transformers.__version__); print('mlflu_hpc torch', torch.__version__)"
echo "--- env directory mtime (must predate today's new-env work) ---"
stat -c '%y  %n' /home/sychan552/.conda/envs/mlflu_hpc \
                  /home/sychan552/.conda/envs/mlflu_hpc/lib/python3.9/site-packages/transformers/__init__.py 2>&1
echo '--- NEW env is a separate tree ---'
ls -d /home/sychan552/.venvs/mlflu_llm 2>&1
echo 'GUARD_DONE'
