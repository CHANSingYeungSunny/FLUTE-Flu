#!/bin/bash
# A0 follow-up: re-run MODE=0 so that it is strictly comparable to MODE=1.
#
# WHY THIS IS NEEDED
#   The first MODE=0 run (job 587059) printed val/test for iteration 0 and then
#   died at main_ILI_lora.py:251 ('./results/' did not exist) BEFORE the
#   `for i in range(args.itr)` loop advanced to i=1. MODE=1 (job 587068) ran that
#   loop to completion and its final numbers (mse 0.8581) are the SECOND
#   iteration. Comparing 0.9685 (mode0, itr 0) against 0.8581 (mode1, itr 1)
#   would confound multimodal with iteration count.
#   This job re-runs MODE=0 with the identical argv, only so that the released
#   code reaches the same terminal point as MODE=1.
set -uo pipefail
MODE=0 bash /scratch/sychan552/a2_stage5/recovery/a0/a0_gpu_minimal.sh
rc=$?
# A0 does not gate the round on its own exit code; record and continue.
echo "[a0gpu-mode0-replay] wrapper exit=$rc (non-zero from the released code is expected/recorded)"
exit 0
