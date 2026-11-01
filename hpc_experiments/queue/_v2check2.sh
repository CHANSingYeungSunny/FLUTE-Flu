#!/bin/bash
# _v2check2.sh -- re-run the static checks and the offline proofs after the
# single-writer change, and demonstrate the three concurrency properties.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

for f in master_controller.sh watchdog.sh submit_night.sh cpu_worker.sh writer.sh; do
  sed -i 's/\r$//' "$f"; sed -i '1s/^\xEF\xBB\xBF//' "$f"
done
for f in master_task.py queue_store.py make_queue.py cost_model.py; do
  sed -i 's/\r$//' "$f"; sed -i '1s/^\xEF\xBB\xBF//' "$f"
done

echo "=== 1. syntax ==="
for f in master_controller.sh watchdog.sh submit_night.sh cpu_worker.sh writer.sh; do
  bash -n "$f" && echo "  OK   $f" || echo "  FAIL $f"
done
for f in master_task.py queue_store.py make_queue.py cost_model.py; do
  "$PY" -m py_compile "$f" && echo "  OK   $f" || echo "  FAIL $f"
done

echo
echo "=== 2. SELFTEST (crash / oracle / claim / env-missing) ==="
bash master_controller.sh --selftest > /tmp/selftest.out 2>&1
echo "rc=$?"
sed -n '/--- sandbox queue AFTER ---/,$p' /tmp/selftest.out

echo
echo "=== 3. SINGLE-WRITER PROOF: a compute lane must NOT run an F1-F5 row ==="
SBX=$(mktemp -d "${Q}/selftest.writer.XXXXXX")
printf 'task_id\tkind\tmodel\tL\tseed\tpriority\tenv\tstate\tattempts\tlast_job\tnote\n' > "$SBX/master_queue.tsv"
printf 'final_analysis_chain\tf3_analysis_chain\t-\t-\t-\tP4\thpc\tTODO\t0\t-\tmust not run on a compute lane\n' >> "$SBX/master_queue.tsv"
printf 'selftest_ok1\tmiflu_cell\tMIFlu\t24\t2021\tP0\thpc\tTODO\t0\t-\t\n' >> "$SBX/master_queue.tsv"
QUEUE_DIR="$SBX" QUEUE_SELFTEST=0 QUEUE_HW_ASSERT=0 QUEUE_MAX_TASKS=3 \
QUEUE_IDLE_POLL=0 QUEUE_STRIPE=1 QUEUE_PARTITION=selftest QUEUE_EXCLUDE="-" QUEUE_MAXGEN=1 \
  bash master_controller.sh --stripe 1 --no-hw-assert --no-idle-wait --partition selftest >> /tmp/wr1.out 2>&1
echo "  compute-lane controller rc=$?"
echo "  final_analysis_chain state after a compute lane saw it: $(awk -F'\t' '$1=="final_analysis_chain"{print $8}' "$SBX/master_queue.tsv")  (must be TODO)"
grep -c "TASK START final_analysis_chain" /tmp/wr1.out | sed 's/^/  times the compute lane started it: /'
echo "  finalise rows the compute lane reported as its own work: $(grep -c 'FINALISATION PASS' /tmp/wr1.out || true) (must be 0)"

echo
echo "=== 4. ATOMIC CLAIM: two concurrent claim attempts, exactly one wins ==="
B2=$(mktemp -d "${Q}/claimtest.XXXXXX")
mkdir -p "$B2/locks"
: > "$B2/master_queue.tsv"
QUEUE_DIR="$B2" QUEUE_CLAIM_HOLD=4 bash master_controller.sh --claim-test shared_task > /tmp/c1.out 2>&1 &
P1=$!
sleep 1
QUEUE_DIR="$B2" QUEUE_CLAIM_HOLD=1 bash master_controller.sh --claim-test shared_task > /tmp/c2.out 2>&1 &
P2=$!
wait $P1; R1=$?
wait $P2; R2=$?
echo "  attempt A rc=$R1 : $(cat /tmp/c1.out | tail -1)"
echo "  attempt B rc=$R2 : $(cat /tmp/c2.out | tail -1)"
[ "$R1" -ne "$R2" ] && echo "  PASS: exactly one claim succeeded" || echo "  FAIL: both got the same outcome"

echo
echo "=== 5. QUEUE-STORE CONCURRENCY: two processes, different rows ==="
B3=$(mktemp -d "${Q}/storetest.XXXXXX")
cp queue_store.py "$B3/"
printf 'task_id\tkind\tmodel\tL\tseed\tpriority\tenv\tstate\tattempts\tlast_job\tnote\n' > "$B3/master_queue.tsv"
for i in 1 2 3 4 5 6 7 8; do
  printf 'row_%s\tmiflu_cell\tMIFlu\t24\t2021\tP0\thpc\tTODO\t0\t-\t\n' "$i" >> "$B3/master_queue.tsv"
done
cat > "$B3/worker.py" <<'PY'
import sys, time
sys.path.insert(0, sys.argv[1])
import queue_store
tid = sys.argv[2]
for _ in range(10):
    queue_store.set_state(tid, "DONE", "updated by %s" % tid)
    time.sleep(0.01)
print("done", tid)
PY
"$PY" "$B3/worker.py" "$B3" row_1 & WA=$!
"$PY" "$B3/worker.py" "$B3" row_8 & WB=$!
wait $WA; wait $WB
n_done=$(awk -F'\t' 'NR>1 && $8=="DONE"{n++} END{print n+0}' "$B3/master_queue.tsv")
echo "  rows in file after two concurrent writers: $(( $(wc -l < "$B3/master_queue.tsv") - 1 )) (must be 8)"
echo "  rows marked DONE: ${n_done} (must be 2: row_1 and row_8)"
awk -F'\t' 'NR>1 && $8=="DONE"{printf "  %s -> %s (%s)\n", $1, $8, $11}' "$B3/master_queue.tsv"

echo
echo "=== 6. import_miflu_predictions.py: rebuild or merge? ==="
grep -n "rmtree\|os.unlink\|os.remove\|shutil.move\|glob(" scripts_placeholder 2>/dev/null || true
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
grep -n "rmtree\|os.unlink\|os.remove\|shutil\." "$A/scripts/import_miflu_predictions.py" | head -20
echo "  (no unlink/rmtree above => it only WRITES cells; it never deletes another cell's files)"

echo
echo "=== 7. cost model (report only, no mutation) ==="
"$PY" cost_model.py 2>&1 | tail -40
