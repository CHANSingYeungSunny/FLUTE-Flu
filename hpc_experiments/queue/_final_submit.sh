#!/bin/bash
# The 5-day gpu_a100 request is priced out of tonight: StartTime 2026-11-02T22:05.
# Wall length IS a scheduling lever for a long reservation, so pick the LONGEST
# wall that still starts tonight. Then fix the CPU worker (batch rejects it; tiny
# has a per-job memory QOS limit) by walking a memory ladder.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$QDIR" || exit 1
CTRL=$QDIR/master_controller.sh
EX=gpu-a100-05,gpu-a100-09

st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p'; }
state() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p'; }

try_A() {  # $1 = wall, $2 = wall seconds
  local w=$1 ws=$2 id s
  id=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
        --time="$w" --requeue --exclude="$EX" --output="$QDIR/slurm-A-%j.out" \
        --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS="$ws" \
        "$CTRL" 2>&1)
  id=${id%%;*}
  case "$id" in ''|*[!0-9]*) echo "A wall=$w SUBMIT FAILED: $id"; return 1 ;; esac
  s=$(st "$id")
  echo "A wall=$w -> job $id state=$(state "$id") StartTime=$s"
  echo "$id $s"
  return 0
}

echo "=== cancel the 5-day job whose StartTime is tomorrow night ==="
scancel 719832 2>&1; sleep 4

for spec in "12:00:00 43200" "06:00:00 21600" "04:00:00 14400"; do
  set -- $spec
  out=$(try_A "$1" "$2") || continue
  jid=${out%% *}; start=${out#* }
  echo "$jid" > "$QDIR/runner_s1.job"
  # keep it if it starts before tomorrow 09:00
  case "$start" in
    2026-11-02*) echo "KEEPING job $jid (starts $start)"; break ;;
    *)           echo "cancelling $jid (starts $start, too late)"; scancel "$jid"; sleep 3 ;;
  esac
done

echo
echo "=== C: CPU worker on tiny, memory ladder ==="
C=""
for mem in 32G 16G 8G 4G 2G 1G; do
  id=$(sbatch --parsable --partition=tiny --cpus-per-task=4 --mem=$mem --time=5-00:00:00 --requeue \
        --output="$QDIR/slurm-C-%j.out" \
        --export=ALL,QUEUE_CPU_ONLY=1,QUEUE_PARTITION=tiny,QUEUE_WALL_SECONDS=432000,QUEUE_TASK_TIMEOUT=21600 \
        "$CTRL" 2>&1)
  case "${id%%;*}" in ''|*[!0-9]*) echo "  mem=$mem rejected"; continue ;; esac
  C=${id%%;*}; echo "  mem=$mem -> job $C state=$(state "$C") StartTime=$(st "$C")"; break
done
[ -n "$C" ] && echo "$C" > "$QDIR/runner_scpu.job"

echo
echo "=== D: watcher on tiny, memory ladder ==="
D=""
for mem in 2G 1G; do
  id=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=$mem --time=5-00:00:00 --requeue \
        --output="$QDIR/slurm-D-%j.out" \
        --export=ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=172800 \
        "$QDIR/watchdog.sh" 2>&1)
  case "${id%%;*}" in ''|*[!0-9]*) echo "  mem=$mem rejected"; continue ;; esac
  D=${id%%;*}; echo "  mem=$mem -> job $D state=$(state "$D") StartTime=$(st "$D")"; break
done

echo
echo "=== FINAL CHAIN RECORD ==="
for f in runner_s0.job runner_s1.job runner_scpu.job; do
  [ -f "$f" ] && printf '%-18s %s\n' "$f" "$(cat "$f")"
done
echo "A(stripe1)=$(cat runner_s1.job 2>/dev/null)  B(stripe0)=$(cat runner_s0.job 2>/dev/null)  C(cpu)=$C  D(watchdog)=${D:-FAILED}"
for j in "$(cat runner_s1.job 2>/dev/null)" "$(cat runner_s0.job 2>/dev/null)" "$C" "$D"; do
  [ -n "${j:-}" ] || continue
  case "$j" in *[!0-9]*) continue ;; esac
  scontrol show job "$j" 2>&1 | tr ' ' '\n' \
    | grep -E '^(JobId|JobName|JobState|Partition|TimeLimit|StartTime|Reason|ExcNodeList)=' | tr '\n' ' '
  echo
done
squeue -u sychan552 -o '%.8i %.10P %.12j %.2t %.12M %.20S %.10r' 2>&1
