#!/bin/bash -l
#SBATCH --job-name=mlflu_cpu_worker
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=5-00:00:00
#SBATCH --requeue
#SBATCH --output=queue/slurm-C-%j.out
#
# Job C -- the CPU worker (queue v2). Downloads the remaining LLM checkpoints,
# pins each revision sha, proves a hidden-state read-out with a 2-layer CPU smoke
# test and flips the corresponding queue rows BLOCKED_MISSING_WEIGHTS -> TODO (or
# -> SKIPPED with the measured reason). It NEVER touches a GPU (rule 13(b)) and
# it is NOT on the critical path: the 22 MIFlu cells and the 12 Qwen2.5-1.5B
# cells do not depend on it.
#
# WHY THIS WRAPPER AND NOT THE CONTROLLER DIRECTLY: the controller carries a
# `#SBATCH --gres=gpu:a100:1` header (it is normally a GPU job). Submitting it
# to `tiny` with that header fails with "Requested node configuration is not
# available" because tiny has no GPUs, and a command-line --cpus/--mem does not
# override the header's --gres. This wrapper has no gres line at all.
#
# QUEUE_STRIPE=cpu is the lane name; the controller accepts it only together
# with QUEUE_CPU_ONLY=1 (a v1 controller died here on a missing QUEUE_STRIPE).
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
export QUEUE_STRIPE=cpu
export QUEUE_CPU_ONLY=1
export QUEUE_PARTITION=tiny
export QUEUE_WALL_SECONDS=${QUEUE_WALL_SECONDS:-432000}
export QUEUE_TASK_TIMEOUT=${QUEUE_TASK_TIMEOUT:-21600}
export QUEUE_HW_ASSERT=0
export QUEUE_ALLOW_CPU_KINDS=1
exec bash "${QDIR}/master_controller.sh"
