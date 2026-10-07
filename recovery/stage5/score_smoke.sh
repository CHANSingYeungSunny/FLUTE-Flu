#!/bin/bash
# Smoke-test the independent scoring entry on L=24 (miflu complete + naive).
cd /scratch/sychan552/a2_stage5
export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export ACTIVE_PROFILE=author_966
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
$PY scripts/score_test_stage5.py --horizons 24 \
  --ckpt-root results/stage5/ckpt/author_966 \
  --export-dir results/stage5/scoring_smoke 2>&1
