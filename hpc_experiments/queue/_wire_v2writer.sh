#!/bin/bash
# _wire_v2writer.sh -- make the private-name writer self-consistent and submit it.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

echo "=== 0. de-CRLF / de-BOM ==="
for f in master_controller_v2.sh master_task_v2.py queue_store_v2.py writer_v2.sh audit_miflu_cells.py; do
  sed -i 's/\r$//' "$f"
  sed -i '1s/^\xEF\xBB\xBF//' "$f"
done

echo "=== 1. rewire the private copies to each other ==="
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
sed -i 's|^import queue_store |import queue_store_v2 as queue_store |' master_task_v2.py
sed -i 's|^import queue_store$|import queue_store_v2 as queue_store|' master_task_v2.py
sed -i 's|master_controller\.sh|master_controller_v2.sh|' writer_v2.sh
grep -n "master_task_v2\|queue_store_v2" master_controller_v2.sh master_task_v2.py | head -8
grep -n "master_controller_v2" writer_v2.sh

echo
echo "=== 2. syntax ==="
bash -n master_controller_v2.sh && echo "  OK master_controller_v2.sh" || echo "  FAIL"
bash -n writer_v2.sh && echo "  OK writer_v2.sh" || echo "  FAIL"
"$PY" -m py_compile master_task_v2.py && echo "  OK master_task_v2.py" || echo "  FAIL"
"$PY" -m py_compile queue_store_v2.py && echo "  OK queue_store_v2.py" || echo "  FAIL"

echo
echo "=== 3. import smoke (private modules only) ==="
"$PY" - <<'PY'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import queue_store_v2, master_task_v2
print("  imports OK; queue =", queue_store_v2.QUEUE)
print("  counts:", queue_store_v2.counts())
print("  finalise kinds:", sorted(master_task_v2.KIND_TO_ID))
print("  analysis tree:", master_task_v2.ANALYSIS)
PY

echo
echo "=== 4. table mtime BEFORE ==="
ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"

echo
echo "=== 5. submit the writer (private code, tiny, 5 d, gres-free) ==="
W=$(sbatch --parsable --partition=tiny --cpus-per-task=8 --mem=8G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-W2-%j.out" \
      --export=ALL,QUEUE_WRITE_POLL=120,QUEUE_WRITE_MAX_SECONDS=43200 \
      "$Q/writer_v2.sh" 2>&1)
W=${W%%;*}
case "$W" in
  ''|*[!0-9]*) echo "  WRITER SUBMIT FAILED: $W"; exit 1 ;;
esac
printf '%s\n' "$W" > runner_sw.job
printf '  writer job %s part=%s wall=%s start=%s state=%s\n' "$W" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^Partition=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^TimeLimit=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^StartTime=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^JobState=//p')"

echo
echo "=== 6. wait for cycle 1 (max 8 min) ==="
before=$(stat -c %Y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" 2>/dev/null)
for i in $(seq 1 48); do
  m=$(stat -c %Y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" 2>/dev/null)
  if [ -n "$m" ] && [ "$m" != "$before" ]; then
    echo "  TABLE REWRITTEN: mtime $(date -r "$m" '+%F %T') (was $(date -r "$before" '+%F %T'))"
    break
  fi
  sleep 10
done
echo "  table now: $(ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv")"
echo
echo "=== 7. writer status + log ==="
cat finalise_status.json 2>/dev/null
echo
ls -t slurm-W2-*.out 2>/dev/null | head -1 | xargs -r tail -20
echo
echo "=== 8. writer events ==="
grep -E "WRITER|FINALISATION PASS|final_import|final_miflu|final_analysis|final_verify" queue_events.log | tail -14
