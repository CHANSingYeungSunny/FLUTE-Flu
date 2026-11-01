#!/bin/bash
# Pre-flight (read-only): partition wall limits, then the queue dry-run and the
# state-machine selftest. No job is submitted here.
set -uo pipefail
cd /gpfs1/home/sychan552/stage5_a2_durable/code/queue || exit 1

echo "================ PARTITION WALL LIMITS ================"
for p in gpu_a100 stingy tiny batch; do
  printf '%-10s ' "$p"
  scontrol show partition "$p" 2>&1 | tr ' ' '\n' \
    | grep -E '^(MaxTime|DefaultTime|State|TotalNodes|MaxNodes)=' | tr '\n' ' '
  echo
done

echo
echo "================ JOB A WALL CHOICE ================"
MAXT=$(scontrol show partition gpu_a100 2>/dev/null | tr ' ' '\n' | sed -n 's/^MaxTime=//p')
echo "gpu_a100 MaxTime=${MAXT:-UNKNOWN}; using 432000s (5 days) if UNLIMITED/absent, else MaxTime"
echo "tiny/batch MaxTime=$(scontrol show partition tiny 2>/dev/null | tr ' ' '\n' | sed -n 's/^MaxTime=//p')"

echo
echo "================ DRY RUN (stripe partition proof) ================"
bash master_controller.sh --dry-run 2>&1 | tail -30

echo
echo "================ SELFTEST (state machine, sandbox queue) ================"
bash master_controller.sh --selftest 2>&1 | tail -40
