#!/bin/bash
# _repair_and_resubmit.sh -- repair the queue rows damaged by the earlier
# runaway no-GPU run, then resubmit the corrected writer and prove it writes.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

echo "=== -1. de-CRLF and rewire the private-name copies ==="
sed -i 's/\r$//' master_controller_v2.sh
sed -i '1s/^\xEF\xBB\xBF//' master_controller_v2.sh
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
grep -c 'master_task_v2.py' master_controller_v2.sh | sed 's/^/  references to master_task_v2.py: /'
bash -n master_controller_v2.sh && echo "  syntax OK" || { echo "  SYNTAX FAIL"; exit 1; }

echo "=== 0. what is FAILED and why ==="
awk -F'\t' 'NR>1 && $8=="FAILED"{printf "  %-26s %-12s env=%-4s att=%-2s lj=%-6s %s\n",$1,$2,$7,$9,$10,substr($11,1,70)}' master_queue.tsv

echo
echo "=== 1. repair: the only legitimate FAILED rows are none; every FAILED row ==="
echo "    here was produced by a no-GPU login-node run during testing (hw.not-a100)"
echo "    and never executed on real hardware. Reset those to TODO with attempts=0."
"$PY" - <<'PY'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import queue_store_v2 as qs
fixed = []
with qs.locked():
    rows = qs.read_rows()
    for r in rows:
        if r[qs.IDX["state"]] != "FAILED":
            continue
        note = r[qs.IDX["note"]]
        if "not-a100" in note or r[qs.IDX["last_job"]] == "local":
            r[qs.IDX["state"]] = "TODO"
            r[qs.IDX["attempts"]] = "0"
            r[qs.IDX["last_job"]] = "-"
            r[qs.IDX["note"]] = "repaired: the FAILED state came from a no-GPU " \
                                "login-node test run, not from the cluster (was: %s)" % note[:90]
            fixed.append(r[0])
    qs.write_rows(rows)
print("  reset %d row(s) to TODO:" % len(fixed))
for t in fixed:
    print("   ", t)
PY

echo
echo "=== 2. reset the F1-F5 attempt counters (our own test runs consumed them) ==="
"$PY" - <<'PY'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import queue_store_v2 as qs
with qs.locked():
    rows = qs.read_rows()
    n = 0
    for r in rows:
        if r[qs.IDX["kind"]] in qs.FINALISE_KINDS:
            r[qs.IDX["state"]] = "TODO"
            r[qs.IDX["attempts"]] = "0"
            r[qs.IDX["last_job"]] = "-"
            r[qs.IDX["note"]] = "reset for the writer-lane deployment"
            n += 1
    qs.write_rows(rows)
print("  %d finalise row(s) reset" % n)
PY

echo
echo "=== 3. queue histogram now ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-26s %d\n", k, c[k]}' master_queue.tsv | sort

echo
echo "=== 4. cancel the previous writer attempt, resubmit the corrected one ==="
for j in $(cat runner_sw.job 2>/dev/null); do scancel "$j" 2>&1; done
sleep 4
W=$(sbatch --parsable --partition=tiny --cpus-per-task=8 --mem=8G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-W3-%j.out" \
      --export=ALL,QUEUE_WRITE_POLL=120,QUEUE_WRITE_MAX_SECONDS=43200 \
      "$Q/writer_v2.sh" 2>&1)
W=${W%%;*}
case "$W" in ''|*[!0-9]*) echo "  WRITER SUBMIT FAILED: $W"; exit 1 ;; esac
printf '%s\n' "$W" > runner_sw.job
printf '  writer job %-8s part=%s wall=%s start=%s state=%s\n' "$W" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^Partition=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^TimeLimit=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^StartTime=//p')" \
  "$(scontrol show job "$W" | tr ' ' '\n' | sed -n 's/^JobState=//p')"

echo
echo "=== 5. wait for cycle 1 (table mtime must move from $(date -r $(stat -c %Y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv") '+%H:%M:%S')) ==="
before=$(stat -c %Y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv")
for i in $(seq 1 60); do
  m=$(stat -c %Y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" 2>/dev/null)
  if [ -n "$m" ] && [ "$m" != "$before" ]; then
    echo "  CYCLE 1 WROTE: $(date -r "$m" '+%F %T')  (was $(date -r "$before" '+%F %T'))"
    before=$m
    break
  fi
  sleep 10
done
echo
echo "=== 6. writer status + tail ==="
cat finalise_status.json 2>/dev/null
echo
tail -12 "$(ls -t slurm-W3-*.out 2>/dev/null | head -1)" 2>/dev/null
