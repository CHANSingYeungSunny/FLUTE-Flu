#!/bin/bash -l
# AUTHOR-FAITHFUL MIFlu run: exact recovery/author_repo/models/GPT4TS_lora.py
# architecture — channel-independent ((b m) batch merge), text APPENDED after time
# patches, take FIRST patch_num tokens, per-variable flatten head Linear(42*768, L).
#
# L=24 only, 10 reps (seeds 42-51) = same protocol as the essay's "mean of 10
# repetitions". Compare against:
#   essay L24 = 1.542 | Track C = 1.9686 | flatten-head = 1.8972
#SBATCH --job-name=miflu_author
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-author-%j.out

set -euo pipefail
module unload default
module load old_modules

CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/home/sychan552/stage5_a2_durable/author_runs
mkdir -p "${OUT}"

# author_faithful is the DEFAULT in miflu_model.MIFlu now.
# MIFLU_FLATTEN_HEAD only controls the legacy A/B path; leave it on.
export MIFLU_FLATTEN_HEAD=1

cd "${CODE}"
echo "[author] MIFLU_FLATTEN_HEAD=${MIFLU_FLATTEN_HEAD} (author_faithful defaults ON)"
"${PY}" -c "import torch, miflu_model as m; print('torch', torch.__version__); \
import inspect; sig=inspect.signature(m.MIFlu.__init__); \
print('MIFlu params:', [p for p in sig.parameters if 'author' in p or 'text' in p])"

echo "=================== L=24 seed=2021 (10 reps) ==================="
# NOTE: --seed is NOT passed: the default is 2021, the author's `fix_seed`
# (recovery/author_repo/main_ILI_lora.py L27). Passing --seed 42 previously
# overrode it and silently used a different draw.
"${PY}" -u train_miflu.py \
  --profile author_repo_966 \
  --horizon 24 \
  --text-source author_file \
  --reps 10 \
  --epochs 20 \
  --batch 16 \
  --learning-rate 0.0001 \
  --containment strict \
  --export-dir "${OUT}/L24_s2021" \
  --ckpt-dir   "${OUT}/ckpt_L24_s2021"

echo "[author] DONE"
