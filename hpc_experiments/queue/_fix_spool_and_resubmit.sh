#!/bin/bash
# _fix_spool_and_resubmit.sh -- the sbatch-spool bug: every lane that derives its
# queue dir from $0 dies at start. Repair, prove, and resubmit the two lanes.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. deploy the fixed code ==="
for f in master_controller_v2.sh watchdog.sh successor_watch.sh; do
  sed -i 's/\r$//' "$f"; sed -i '1s/^\xEF\xBB\xBF//' "$f"
done
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
for f in master_controller_v2.sh watchdog.sh successor_watch.sh successor_lib.sh successor_lane.sh; do
  bash -n "$f" && echo "  OK   $f" || echo "  FAIL $f"
done

echo
echo "=== 1. PROOF the fix: run the controller the way sbatch does (from a spool-like path) ==="
SP=$(mktemp -d /tmp/spooltest.XXXXXX)
cp master_controller_v2.sh "$SP/slurm_script"
( cd /tmp && bash "$SP/slurm_script" --dry-run 2>&1 | head -12 )
rm -rf "$SP"

echo
echo "=== 2. the two lanes carry the BROKEN code, so they must be replaced ==="
printf '  720083 %s start=%s   (would die: missing queue file in /var/spool/...)\n' "$(st 720083 JobState)" "$(st 720083 StartTime)"
printf '  720070 %s start=%s   (same)\n' "$(st 720070 JobState)" "$(st 720070 StartTime)"
scancel 720083 720070 2>&1
sleep 6
printf '  720083 -> %s\n' "$(st 720083 JobState)"
printf '  720070 -> %s\n' "$(st 720070 JobState)"

echo
echo "=== 3. resubmit: P0 lane to stingy (same spec) ==="
P=$(sbatch --parsable --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=04:00:00 --requeue --exclude=gpu-a100-05 \
      --output="$Q/slurm-P0-%j.out" \
      --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=14400,QUEUE_ONLY_PRIORITY=P0 \
      "$Q/master_controller_v2.sh" 2>&1)
P=${P%%;*}
case "$P" in ''|*[!0-9]*) echo "  P0 SUBMIT FAILED: $P" ;; *) echo "$P" > runner_s0.job
  echo "$P" > P0_LANE.job
  printf '  P0 lane %s start=%s state=%s\n' "$P" "$(st "$P" StartTime)" "$(st "$P" JobState)" ;; esac

echo
echo "=== 4. resubmit: Qwen P1 lane to gpu_a100 (same spec) ==="
X=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=12:00:00 --requeue --exclude=gpu-a100-05,gpu-a100-09 \
      --output="$Q/slurm-Q-%j.out" \
      --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=43200,QUEUE_ONLY_PRIORITY=P1,QUEUE_SMOKE_ABORT=1,QUEUE_TASK_TIMEOUT=7200 \
      "$Q/master_controller_v2.sh" 2>&1)
X=${X%%;*}
case "$X" in ''|*[!0-9]*) echo "  QWEN SUBMIT FAILED: $X" ;; *) echo "$X" > runner_s1.job
  printf '  QWEN lane %s start=%s state=%s\n' "$X" "$(st "$X" StartTime)" "$(st "$X" JobState)" ;; esac

echo
echo "=== 5. resubmit the successor watcher (fixed) ==="
W=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=12:00:00 --requeue \
      --output="$Q/slurm-SW-%j.out" --export=ALL,QUEUE_SUCC_POLL=120 \
      "$Q/successor_watch.sh" 2>&1)
W=${W%%;*}
case "$W" in ''|*[!0-9]*) echo "  SW SUBMIT FAILED: $W" ;;
  *) printf '  successor watcher %s start=%s state=%s\n' "$W" "$(st "$W" StartTime)" "$(st "$W" JobState)" ;; esac

echo
echo "=== 6. jobs ==="
squeue -u sychan552 -o '%.8i %.10P %.20j %.2t %.21S'
echo
echo "=== 7. wait for the watcher's first decision (max 4 min) ==="
for i in $(seq 1 24); do
  [ -s successor.log ] && break
  sleep 10
done
cat successor.log 2>/dev/null || echo "  (still no log)"
echo
echo "=== 8. P0 lane + writer + watchdog intact ==="
for j in "$P" "$X" 720052 720004; do
  [ -n "${j:-}" ] || continue
  printf '  %-8s %-14s %-9s start=%-20s %s\n' "$j" "$(st "$j" JobName)" "$(st "$j" JobState)" \
    "$(st "$j" StartTime)" "$(st "$j" TimeLimit)"
done
