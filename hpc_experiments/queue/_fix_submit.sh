#!/bin/bash
# Fix the two failed submissions (C: memory request; D: UTF-8 BOM on line 1) and
# re-check A/B StartTime. Nothing else is touched.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$QDIR" || exit 1
CTRL=$QDIR/master_controller.sh
WD=$QDIR/watchdog.sh

echo "=== BOM check ==="
for f in master_controller.sh watchdog.sh; do
  printf '%-24s first2bytes=' "$f"; head -c 2 "$f" | od -An -c | tr -d '\n'; echo
done
sed -i '1s/^\xEF\xBB\xBF//' watchdog.sh
sed -i '1s/^\xEF\xBB\xBF//' master_controller.sh
echo "after fix:"
for f in master_controller.sh watchdog.sh; do
  printf '%-24s first2bytes=' "$f"; head -c 2 "$f" | od -An -c | tr -d '\n'; echo
done

echo "=== memory available on the CPU partitions ==="
scontrol show node cpunode-034 2>/dev/null | tr ' ' '\n' | grep -E '^(RealMemory|CfgTRES|AllocTRES)=' | tr '\n' ' '
echo
scontrol show partition tiny 2>/dev/null | tr ' ' '\n' | grep -iE 'mem|MaxTime|TotalNodes' | tr '\n' ' '
echo
scontrol show partition batch 2>/dev/null | tr ' ' '\n' | grep -iE 'mem|MaxTime|TotalNodes' | tr '\n' ' '
echo

echo "=== C: CPU worker on batch (112 nodes), all node memory, 5-day wall ==="
C=$(sbatch --parsable --partition=batch --cpus-per-task=4 --mem=0 --time=5-00:00:00 --requeue \
      --output="$QDIR/slurm-C-%j.out" \
      --export=ALL,QUEUE_CPU_ONLY=1,QUEUE_PARTITION=batch,QUEUE_WALL_SECONDS=432000,QUEUE_TASK_TIMEOUT=21600 \
      "$CTRL" 2>&1)
echo "C=$C"
C=${C%%;*}
case "$C" in
  ''|*[!0-9]*) echo "C SUBMIT FAILED" ;;
  *) printf '%s\n' "$C" > "$QDIR/runner_scpu.job" ;;
esac

echo "=== D: watcher, all node memory, 5-day wall ==="
D=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=0 --time=5-00:00:00 --requeue \
      --output="$QDIR/slurm-D-%j.out" \
      --export=ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=172800 \
      "$WD" 2>&1)
echo "D=$D"
D=${D%%;*}

echo
echo "=== A/B/C/D now ==="
for j in 719832 719833 "$C" "$D"; do
  [ -n "$j" ] || continue
  case "$j" in *[!0-9]*) continue ;; esac
  scontrol show job "$j" 2>&1 | tr ' ' '\n' \
    | grep -E '^(JobId|JobState|Partition|TimeLimit|StartTime|Reason)=' | tr '\n' ' '
  echo
done
