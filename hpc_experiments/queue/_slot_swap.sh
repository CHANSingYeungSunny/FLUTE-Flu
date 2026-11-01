#!/bin/bash
# _slot_swap.sh -- reclaim gpu_a100 QOS slots from jobs that cannot contribute
# tonight, then submit the hardened stripe-1 lane and read its StartTime.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. rewire the private copies (CRLF, module name, task path) ==="
sed -i 's/\r$//' master_task_v2.py master_controller_v2.sh
sed -i 's|^import queue_store |import queue_store_v2 as queue_store |' master_task_v2.py
sed -i 's|^import queue_store$|import queue_store_v2 as queue_store|' master_task_v2.py
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
grep -c queue_store_v2 master_task_v2.py | sed 's/^/  queue_store_v2 refs: /'
grep -c master_task_v2.py master_controller_v2.sh | sed 's/^/  master_task_v2 refs: /'
"$PY" -m py_compile master_task_v2.py && echo "  task syntax OK"
bash -n master_controller_v2.sh && echo "  controller syntax OK"

echo "=== A. what the v1 controller does with the v2 11-column queue ==="
head -2 master_queue.tsv | tail -1 | {
  IFS=$'\t' read -r tid kind model L seed pri st8 att lj note
  echo "  v1 reads 10 names off 11 fields:"
  echo "    tid=$tid  kind=$kind  L=$L  priority=$pri"
  echo "    v1's STATE field = '$st8'      <-- this is the ENV column, never 'TODO'"
  echo "    so v1 pick_next() can never pick a row, while global_count(TODO) is non-zero."
}

echo
echo "=== B. gpu_a100 jobs now (StartTime decides usefulness tonight) ==="
for j in $(squeue -u sychan552 -h -p gpu_a100 -o '%i'); do
  printf '  %-8s %-14s %-9s start=%-20s %s\n' "$j" "$(st "$j" Name)" "$(st "$j" JobState)" \
    "$(st "$j" StartTime)" "$(st "$j" TimeLimit)"
done
echo "  now = $(date '+%F %T')   tonight ends ~2026-11-02 08:00"

echo
echo "=== C. cancel only jobs that provably cannot contribute tonight ==="
echo "  720017 miflu_compute  start 2026-11-03T13:04  -> after the night; frees a QOS slot"
echo "  719836  mlflu_master   start 2026-11-02T22:05  -> after the night; old v1 code"
echo "  719837  mlflu_master   start 2026-11-02T14:50  -> after the night; old v1 code"
for j in 720017 719836 719837; do
  echo "  scancel $j ($(st "$j" Name) start=$(st "$j" StartTime)) reason=cannot-contribute-tonight"
  scancel "$j" 2>&1
done
sleep 6

echo
echo "=== D. submit the hardened stripe-1 lane (gpu_a100, 12 h) ==="
X=$(sbatch --parsable --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=12:00:00 --requeue --exclude=gpu-a100-05,gpu-a100-09 \
      --output="$Q/slurm-A-%j.out" \
      --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=43200 \
      "$Q/master_controller_v2.sh" 2>&1)
X=${X%%;*}
case "$X" in
  ''|*[!0-9]*) echo "  HARDENED LANE SUBMIT FAILED: $X" ;;
  *) printf '%s\n' "$X" >> runner_s1.job
     printf '  hardened lane %s part=%s wall=%s start=%s state=%s\n' "$X" \
       "$(st "$X" Partition)" "$(st "$X" TimeLimit)" "$(st "$X" StartTime)" "$(st "$X" JobState)" ;;
esac

echo
echo "=== E. 719835 holds the 02:50:39 slot but runs v1 code against the v2 queue ==="
echo "  719835 start=$(st 719835 StartTime) state=$(st 719835 JobState)"
echo "  720017/719836/719837 were cancelled above; 719835 and 719833 are left as-is"
echo "  unless the parent decides otherwise (they are the parent's jobs)."

echo
echo "=== F. full picture ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.11M %.21S'

echo
echo "=== G. writer status (fixed generation) ==="
"$PY" - <<'PY'
import json
try:
    d = json.load(open("finalise_status.json"))
except Exception as e:
    print("  unreadable:", e); raise SystemExit
if "slurm_job" not in d:
    print("  (this file was written by the other agent's writer schema:", sorted(d), ")")
else:
    for k in ("cycle","when","pid","slurm_job","task","ok","gate","signature",
              "n_markers","n_cells","n_arms","last_table_mtime","last_error"):
        print("  %-18s %s" % (k, d.get(k)))
PY
echo
echo "=== H. table mtime ==="
ls -l --time-style=+%F' '%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
echo "  figures: $(ls -1 "$A/results/bench_figures" 2>/dev/null | wc -l)"
