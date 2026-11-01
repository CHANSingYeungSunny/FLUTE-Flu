#!/bin/bash
# Final wiring: (1) record the real job ids per stripe, (2) resubmit the CPU
# worker with a CPU/memory ratio the tiny partition accepts, (3) print StartTimes.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$QDIR" || exit 1
CTRL=$QDIR/master_controller.sh

st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p'; }
state() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p'; }

echo "=== stripe->job map (one id per line; several are allowed) ==="
printf '%s\n' 719833 > runner_s0.job
: > runner_s1.job
for j in 719835 719836 719837; do
  if [ "$(state "$j")" != "" ]; then printf '%s\n' "$j" >> runner_s1.job; fi
done
echo "runner_s0.job: $(cat runner_s0.job | tr '\n' ' ')"
echo "runner_s1.job: $(cat runner_s1.job | tr '\n' ' ')"

echo
echo "=== CPU worker (tiny): cpus and mem must respect DefMemPerCPU=1024 ==="
C=""
for spec in "16 16G" "8 8G" "4 4G" "2 2G"; do
  set -- $spec
  out=$(sbatch --parsable --partition=tiny --cpus-per-task="$1" --mem="$2" --time=5-00:00:00 --requeue \
        --output="$QDIR/slurm-C-%j.out" \
        --export=ALL,QUEUE_CPU_ONLY=1,QUEUE_PARTITION=tiny,QUEUE_WALL_SECONDS=432000,QUEUE_TASK_TIMEOUT=21600 \
        "$CTRL" 2>&1)
  id=${out%%;*}
  case "$id" in ''|*[!0-9]*) echo "  cpu=$1 mem=$2 rejected: $(printf '%s' "$out" | head -1)"; continue ;; esac
  C=$id; echo "  cpu=$1 mem=$2 -> job $C state=$(state "$C") StartTime=$(st "$C")"; break
done
if [ -n "$C" ]; then printf '%s\n' "$C" > runner_scpu.job; else echo "CPU WORKER NOT SUBMITTED"; fi

echo
echo "=== FULL CHAIN ==="
squeue -u sychan552 -o '%.8i %.10P %.14j %.2t %.11M %.21S %.12r' 2>&1
echo
for j in 719833 $(cat runner_s1.job | tr '\n' ' ') "$C" "$(cat runner_s1.job | head -1)" 719844; do
  [ -n "${j:-}" ] || continue
  case "$j" in *[!0-9]*) continue ;; esac
  printf 'job %-8s %s\n' "$j" "$(scontrol show job "$j" 2>/dev/null | tr ' ' '\n' | grep -E '^(JobState|Partition|TimeLimit|StartTime|Reason)=' | tr '\n' ' ')"
done
