#!/bin/bash
# Syntax-check every queue script, then submit the CPU worker via the no-gres
# wrapper (the controller's own `#SBATCH --gres=gpu:a100:1` header is what made
# every tiny submission fail with "Requested node configuration is not available").
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$QDIR" || exit 1

echo "=== syntax ==="
for f in master_controller.sh watchdog.sh cpu_worker.sh; do
  if bash -n "$f"; then echo "  OK   $f"; else echo "  FAIL $f"; fi
done
head -c 2 watchdog.sh | od -An -c

echo
echo "=== CPU worker (job C) via cpu_worker.sh ==="
C=""
for spec in "8 8G" "4 4G" "2 2G"; do
  set -- $spec
  out=$(sbatch --parsable --partition=tiny --cpus-per-task="$1" --mem="$2" \
        --time=5-00:00:00 --requeue --output="$QDIR/slurm-C-%j.out" "$QDIR/cpu_worker.sh" 2>&1)
  id=${out%%;*}
  case "$id" in ''|*[!0-9]*) echo "  cpu=$1 mem=$2 rejected: $(printf '%s' "$out" | head -1)"; continue ;; esac
  C=$id; echo "  cpu=$1 mem=$2 -> job $C"; break
done
if [ -n "$C" ]; then printf '%s\n' "$C" > runner_scpu.job; else echo "  CPU WORKER NOT SUBMITTED"; fi

echo
echo "=== CHAIN ==="
squeue -u sychan552 -o '%.8i %.10P %.14j %.2t %.11M %.21S %.12r' 2>&1
