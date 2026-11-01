#!/bin/bash
# _qwen_lane.sh -- replace the redundant second MIFlu lane with a Qwen2.5-1.5B
# lane (priority filter P1, disjoint from 719833's P0 MIFlu cells).
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. redeploy the private controller/task with the lane-scoping changes ==="
sed -i 's/\r$//' master_controller_v2.sh master_task_v2.py
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
sed -i 's|^import queue_store |import queue_store_v2 as queue_store |' master_task_v2.py
bash -n master_controller_v2.sh && echo "  controller syntax OK"
"$PY" -m py_compile master_task_v2.py && echo "  task syntax OK"
grep -c 'QUEUE_ONLY_PRIORITY\|smoke_abort_arm' master_controller_v2.sh | sed 's/^/  new controller hooks: /'

echo
echo "=== 1. cancel 720064 (it would duplicate 719833's P0 MIFlu cells) ==="
for j in $(squeue -u sychan552 -h -j 720064 -o '%i %j %T' 2>/dev/null | awk '$1==720064{print $1}'); do
  echo "  scancel $j ($(st "$j" Name) start=$(st "$j" StartTime)) reason=would-duplicate-P0-MIFlu-owned-by-719833"
  scancel "$j" 2>&1
done
sed -i '/^720064$/d' runner_s1.job 2>/dev/null
sleep 4

echo
echo "=== 2. submit the Qwen2.5-1.5B lane (gpu_a100, 12 h, stripe 1, P1 only) ==="
X=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=12:00:00 --requeue --exclude=gpu-a100-05,gpu-a100-09 \
      --output="$Q/slurm-Q-%j.out" \
      --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=43200,QUEUE_ONLY_PRIORITY=P1,QUEUE_SMOKE_ABORT=1,QUEUE_TASK_TIMEOUT=7200 \
      "$Q/master_controller_v2.sh" 2>&1)
X=${X%%;*}
case "$X" in
  ''|*[!0-9]*) echo "  QWEN LANE SUBMIT FAILED: $X"; exit 1 ;;
esac
printf '%s\n' "$X" >> runner_s1.job
printf '  QWEN lane %s part=%s wall=%s start=%s state=%s\n' "$X" \
  "$(st "$X" Partition)" "$(st "$X" TimeLimit)" "$(st "$X" StartTime)" "$(st "$X" JobState)"

echo
echo "=== 3. queue: the P1 cells this lane owns ==="
awk -F'\t' 'NR>1 && $6=="P1"{printf "  %-24s env=%-4s state=%-8s %s\n",$1,$7,$8,substr($11,1,40)}' master_queue.tsv | head -14
echo "  P1 TODO total: $(awk -F'\t' 'NR>1 && $6=="P1" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)"

echo
echo "=== 4. jobs now ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.11M %.21S'

echo
echo "=== 5. markers / table ==="
echo "  miflu markers: $(ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify | wc -l)"
ls -l --time-style=+%F' '%H:%M:%S /gpfs1/home/sychan552/stage5_a2_durable/analysis/paper_tables/BENCH_MSE_BY_MODEL_L.csv
echo "  figures: $(ls -1 /gpfs1/home/sychan552/stage5_a2_durable/analysis/results/bench_figures 2>/dev/null | wc -l)"
