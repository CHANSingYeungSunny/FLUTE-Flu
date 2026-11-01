#!/bin/bash
# successor_lane.sh -- the PART-TWO successor lane (no #SBATCH header: it is
# always submitted with `sbatch --partition=stingy --gres=gpu:a100:1 ...`, which
# is what makes the gres/resource flags of the caller authoritative).
#
# It continues after the P0 lane: P1 first, then P2, in priority order. Almost
# every P2 row is BLOCKED_MISSING_WEIGHTS and will be skipped -- that is correct
# and expected; the point is that the two arms whose weights ARE local
# (Qwen/Qwen2.5-1.5B and deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B) become
# runnable the moment a slot exists.
#
# QUEUE_ONLY_PRIORITY="P1 P2" does double duty: it takes P1 then P2, AND it makes
# the lane own every cell in that scope instead of one cksum(task_id) % 2 half.
# Inter-lane exclusion is the atomic per-task claim -- there is no second
# mechanism, and no need for one.
#
# Both local arms are `qwen2`, so both run in `mlflu_hpc` (py3.9 / tr4.57.6); the
# queue's `env` column says so per row, and a row whose interpreter is missing is
# SKIPPED `env-missing` and never retried.
#
# It NEVER executes F1-F5 and never writes paper_tables/: that is the writer
# lane's (`QUEUE_WRITE_ONLY`) exclusive right.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
export QUEUE_STRIPE=0
export QUEUE_PARTITION=stingy
export QUEUE_WALL_SECONDS=14400
export QUEUE_SMOKE_ABORT=1      # first cell of each ARM is its smoke test
export QUEUE_TASK_TIMEOUT=7200
export QUEUE_ONLY_PRIORITY="P1 P2"
exec bash "${QDIR}/master_controller_v2.sh"
