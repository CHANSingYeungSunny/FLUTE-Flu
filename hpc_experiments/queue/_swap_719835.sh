#!/bin/bash
# _swap_719835.sh -- 719835 holds the 02:50:39 gpu_a100 slot but carries spooled
# v1 code that cannot parse the 11-column queue (its STATE field reads `hpc`), so
# it can never execute a row. Replace it with a lane that can, and read the price.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== before ==="
printf '  719835 start=%s state=%s\n' "$(st 719835 StartTime)" "$(st 719835 JobState)"
printf '  720068 start=%s state=%s (Qwen lane, currently not tonight)\n' "$(st 720068 StartTime)" "$(st 720068 JobState)"

echo
echo "=== cancel 719835 (v1 code vs 11-column queue: 0 rows executable) ==="
scancel 719835 2>&1; sleep 5
printf '  719835 now=%s\n' "$(st 719835 JobState)"

echo
echo "=== cancel 720068 (its 12 h request was priced at 22:05 tomorrow) and resubmit ==="
scancel 720068 2>&1; sleep 4
X=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=12:00:00 --requeue --exclude=gpu-a100-05,gpu-a100-09 \
      --output="$Q/slurm-Q-%j.out" \
      --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=43200,QUEUE_ONLY_PRIORITY=P1,QUEUE_SMOKE_ABORT=1,QUEUE_TASK_TIMEOUT=7200 \
      "$Q/master_controller_v2.sh" 2>&1)
X=${X%%;*}
case "$X" in ''|*[!0-9]*) echo "  SUBMIT FAILED: $X"; exit 1 ;; esac
printf '%s\n' "$X" > runner_s1.qwen.job
printf '  QWEN lane %s part=%s wall=%s start=%s state=%s\n' "$X" \
  "$(st "$X" Partition)" "$(st "$X" TimeLimit)" "$(st "$X" StartTime)" "$(st "$X" JobState)"

echo
echo "=== jobs now ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.21S'
