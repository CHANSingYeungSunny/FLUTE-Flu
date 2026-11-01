#!/bin/bash
# submit_night.sh -- the actual submission: cancel the old chain, then start
#   A (gpu_a100, 5-day wall, STRIPE=1)   primary engine, consumes the whole queue
#   B (stingy,   4 h wall,  STRIPE=0)    second worker on the disjoint half
#   C (tiny,     5-day wall, CPU_ONLY)   downloads + revision pin + hidden-state smoke
#   D (tiny,     5-day wall)             watcher: restarts A/B/C if they vanish
# and record each job id in queue/runner_s<stripe>.job so the watcher knows what
# is already alive (otherwise it would duplicate everything on its first poll).
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$QDIR" || exit 1
CTRL=$QDIR/master_controller.sh
WD=$QDIR/watchdog.sh
EX_A100=gpu-a100-05,gpu-a100-09

echo "=== cancelling the old parked chain ==="
scancel 719715 719716 2>&1
sleep 5
squeue -u sychan552 -o '%.8i %.10P %.9j %.2t %.10M' 2>&1

echo
echo "=== A: gpu_a100, 5-day wall, stripe 1 (PRIMARY) ==="
A=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=5-00:00:00 --requeue --exclude="$EX_A100" \
      --output="$QDIR/slurm-A-%j.out" \
      --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=432000 \
      "$CTRL" 2>&1)
echo "A=$A"; A=${A%%;*}

echo "=== B: stingy, 4 h wall, stripe 0 ==="
B=$(sbatch --parsable --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=04:00:00 --requeue --exclude=gpu-a100-05 \
      --output="$QDIR/slurm-B-%j.out" \
      --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=14400 \
      "$CTRL" 2>&1)
echo "B=$B"; B=${B%%;*}

echo "=== C: tiny CPU worker (downloads + probes + unblock) ==="
C=$(sbatch --parsable --partition=tiny --cpus-per-task=4 --mem=32G --time=5-00:00:00 --requeue \
      --output="$QDIR/slurm-C-%j.out" \
      --export=ALL,QUEUE_CPU_ONLY=1,QUEUE_PARTITION=tiny,QUEUE_WALL_SECONDS=432000,QUEUE_TASK_TIMEOUT=21600 \
      "$CTRL" 2>&1)
echo "C=$C"; C=${C%%;*}

echo "=== D: tiny watcher ==="
D=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=5-00:00:00 --requeue \
      --output="$QDIR/slurm-D-%j.out" \
      --export=ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=172800 \
      "$WD" 2>&1)
echo "D=$D"; D=${D%%;*}

printf '%s\n' "$A" > "$QDIR/runner_s1.job"
printf '%s\n' "$B" > "$QDIR/runner_s0.job"
printf '%s\n' "$C" > "$QDIR/runner_scpu.job"

echo
echo "=== record ==="
for j in "$A" "$B" "$C" "$D"; do
  printf '%s ->\n' "$j"
  scontrol show job "$j" 2>&1 | tr ' ' '\n' | grep -E '^(JobId|JobState|Partition|TimeLimit|StartTime|Reason|ExcNodeList|ReqTRES)=' | tr '\n' ' '
  echo
done

echo
echo "=== stripe split of the runnable work (P0/P1) ==="
awk -F'\t' 'NR>1 && ($6=="P0"||$6=="P1"){cmd="cksum <<< \""$1"\""; }' "$QDIR/master_queue.tsv" > /dev/null
for pri in P0 P1 P2 P3; do
  n0=0; n1=0
  while IFS=$'\t' read -r tid kind model L seed p st att lj note; do
    [ "$tid" = "task_id" ] && continue
    [ "$p" = "$pri" ] || continue
    s=$(printf '%s' "$tid" | cksum | awk '{print $1 % 2}')
    if [ "$s" = "0" ]; then n0=$((n0+1)); else n1=$((n1+1)); fi
  done < "$QDIR/master_queue.tsv"
  echo "$pri: stripe0(stingy)=$n0 stripe1(gpu_a100)=$n1"
done
echo
echo "P0 detail:"
while IFS=$'\t' read -r tid kind model L seed p st att lj note; do
  [ "$tid" = "task_id" ] && continue
  [ "$p" = "P0" ] || continue
  printf '  %s stripe=%s %s\n' "$tid" "$(printf '%s' "$tid" | cksum | awk '{print $1 % 2}')" "$st"
done < "$QDIR/master_queue.tsv"
