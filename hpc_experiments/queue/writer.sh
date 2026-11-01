#!/bin/bash -l
#SBATCH --job-name=mlflu_writer
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=5-00:00:00
#SBATCH --requeue
#SBATCH --output=queue/slurm-W-%j.out
#
# Job W -- the SINGLE WRITER of results (queue v2).
#
# The one outcome that matters tonight is cells -> paper_tables/. Exactly one
# process may own that transformation: two lanes rebuilding the tables from
# different partial subsets would each produce a plausible table, with no error
# anywhere and no way to tell which one is right. So F1-F5 live here and nowhere
# else:
#
#   * the GPU compute lanes (stripe 0/1) and the CPU download lane NEVER execute
#     an F1-F5 task -- `is_mine()` returns false for finalise kinds unless
#     QUEUE_WRITE_ONLY=1, which only this wrapper sets;
#   * this lane holds `queue/.writer.lock` (flock) for its whole life, so a
#     second writer cannot even start;
#   * inside F1-F5 the task itself holds `queue/.finalise.lock` and a per-task
#     claim, so the invariant is enforced three times over.
#
# It polls the on-disk cell signature (count + newest mtime of pred_*.npz under
# expanded_runs/ and author_runs/L*_all7/) and runs F1 -> F5 ONCE whenever that
# signature changes; it no-ops in ~1 s when nothing new landed. It honours
# `queue/HALT` and exits after QUEUE_WRITE_MAX_SECONDS (12 h) so a 5-day
# allocation cannot squat.
#
# NO `#SBATCH --gres` HERE ON PURPOSE: the controller's own header requests an
# A100, and a header gres cannot be overridden from the command line, so a
# GPU-less partition rejects it with "Requested node configuration is not
# available". This wrapper is gres-free. Memory must respect tiny's
# DefMemPerCPU=1024 (mem <= cpus x 1 GB).
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
export QUEUE_WRITE_ONLY=1
export QUEUE_STRIPE=w
export QUEUE_PARTITION=tiny
export QUEUE_HW_ASSERT=0
export QUEUE_WRITE_POLL=${QUEUE_WRITE_POLL:-120}
export QUEUE_WRITE_MAX_SECONDS=${QUEUE_WRITE_MAX_SECONDS:-43200}
exec bash "${QDIR}/master_controller.sh" --writer
