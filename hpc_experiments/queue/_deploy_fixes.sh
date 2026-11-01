#!/bin/bash
# _deploy_fixes.sh -- redeploy the writer with the two fixes, restart it, and
# submit the second compute lane the parent asked for.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
T="$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. rewire private copies ==="
for f in master_controller_v2.sh master_task_v2.py; do
  sed -i 's/\r$//' "$f"; sed -i '1s/^\xEF\xBB\xBF//' "$f"
done
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
sed -i 's|^import queue_store |import queue_store_v2 as queue_store |' master_task_v2.py
bash -n master_controller_v2.sh && echo "  controller syntax OK"
"$PY" -m py_compile master_task_v2.py && echo "  task syntax OK"
echo "  task refs: $(grep -c 'queue_store_v2' master_task_v2.py)  controller refs: $(grep -c 'master_task_v2.py' master_controller_v2.sh)"

echo
echo "=== 1. stop the previous writer generation, start the fixed one ==="
for j in $(cat runner_sw.job 2>/dev/null); do
  echo "  scancel $j ($(st "$j" JobName) $(st "$j" JobState)) reason=superseded-by-fixed-writer"
  scancel "$j" 2>&1
done
sleep 5
W=$(sbatch --parsable --partition=tiny --cpus-per-task=8 --mem=8G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-W4-%j.out" \
      --export=ALL,QUEUE_WRITE_POLL=120,QUEUE_WRITE_MAX_SECONDS=43200 \
      "$Q/writer_v2.sh" 2>&1)
W=${W%%;*}
case "$W" in ''|*[!0-9]*) echo "  WRITER SUBMIT FAILED: $W"; exit 1 ;; esac
printf '%s\n' "$W" > runner_sw.job
printf '  writer %s part=%s wall=%s start=%s state=%s\n' "$W" \
  "$(st "$W" Partition)" "$(st "$W" TimeLimit)" "$(st "$W" StartTime)" "$(st "$W" JobState)"

echo
echo "=== 2. second compute lane (parent's compute_lane.sh, gpu_a100 12 h) ==="
if [ -f compute_lane.sh ]; then
  C=$(sbatch --parsable --partition=gpu_a100 --time=12:00:00 \
        --output="$Q/slurm-CL-%j.out" "$Q/compute_lane.sh" 2>&1)
  C=${C%%;*}
  case "$C" in
    ''|*[!0-9]*) echo "  compute lane SUBMIT FAILED: $C" ;;
    *) printf '  compute %s part=%s wall=%s start=%s state=%s\n' "$C" \
         "$(st "$C" Partition)" "$(st "$C" TimeLimit)" "$(st "$C" StartTime)" "$(st "$C" JobState)"
       printf '%s\n' "$C" >> runner_s1.job ;;
  esac
else
  echo "  compute_lane.sh is NOT on the cluster"
fi

echo
echo "=== 3. all my jobs ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.11M %.21S'

echo
echo "=== 4. wait for the fixed writer's first cycle (max 8 min) ==="
m0=$(stat -c %Y "$T")
for i in $(seq 1 48); do
  m=$(stat -c %Y "$T")
  [ "$m" != "$m0" ] && { echo "  TABLE REWRITTEN -> $(date -d @$m '+%F %T') (was $(date -d @$m0 '+%F %T'))"; break; }
  sleep 10
done
echo "  table: $(ls -l --time-style=+%F' '%H:%M:%S "$T")"

echo
echo "=== 5. finalise_status.json ==="
"$PY" - <<'PY'
import json
try:
    d = json.load(open("finalise_status.json"))
except Exception as e:
    print("  unreadable:", e); raise SystemExit
for k in ("cycle","when","pid","slurm_job","task","ok","gate","signature",
          "n_markers","n_cells","n_arms","last_table_mtime","last_error"):
    print("  %-18s %s" % (k, d.get(k)))
PY

echo
echo "=== 6. oracle verdict lines ==="
grep -E "RESULT:|\[FAIL\]|PARTIAL MEAN" finalise/final_miflu_oracle.log | tail -8
echo
echo "=== 7. writer events (fixed gen) ==="
grep -E "WRITER|FINALISATION PASS|TASK (START|DONE|SKIPPED) +final_" queue_events.log | tail -12
