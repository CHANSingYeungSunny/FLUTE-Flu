#!/bin/bash
# launcher for the RESUME of the ONE-TIME final Test evaluation.
# The authorization receipt already exists, so this only continues the SAME
# immutable evaluation (test_eval_id taken from the receipt); it never creates
# a second Test evaluation. Mechanical environment only: thread caps for the
# login node; no scientific, checkpoint, or protocol change.
set -u
ROOT=/scratch/sychan552/innovation_deploy_root_v2_10
cd "$ROOT"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH

nohup python hpc_scripts/autonomous/run_one_time_test.py \
  --deployment-root "$ROOT" \
  --expect-manifest-sha 558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5 \
  --expect-cohort-sha 8695b8ea6151c5dd350411449141e4e547c7bd0aaa263e402695279477e0327d \
  > test_resume.log 2>&1 &
echo "LAUNCHED pid=$!"
