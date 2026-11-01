#!/bin/bash
# _submit_wd_proof.sh -- submit the layout-aware watchdog (the writer 720002 is
# already queued) and then prove the writer wrote, with two distinct mtimes.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

state_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p'; }
start_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p'; }
wall_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^TimeLimit=//p'; }
part_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^Partition=//p'; }
show() { printf '  job %-8s part=%-7s wall=%-11s start=%-20s state=%s\n' \
           "$1" "$(part_of "$1")" "$(wall_of "$1")" "$(start_of "$1")" "$(state_of "$1")"; }

echo "=== writer lane (already submitted) ==="
W=$(head -1 runner_sw.job 2>/dev/null)
show "${W:-none}"

echo
echo "=== watchdog (tiny, 11-column aware, max wall) ==="
D=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-D-%j.out" \
      --export=ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=432000 \
      "$Q/watchdog.sh" 2>&1)
D=${D%%;*}
if [ -z "$D" ]; then
  echo "  WATCHDOG SUBMIT FAILED (empty)"
elif printf '%s' "$D" | grep -qvE '^[0-9]+$'; then
  echo "  WATCHDOG SUBMIT FAILED: $D"
else
  show "$D"
fi

echo
echo "=== runner map ==="
for f in runner_s0.job runner_s1.job runner_scpu.job runner_sw.job; do
  printf '  %-18s %s\n' "$f" "$(tr '\n' ' ' < "$f" 2>/dev/null)"
done

echo
echo "=== table mtime BEFORE ==="
ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"

echo
echo "=== wait for the writer's first status file (max 8 min) ==="
for i in $(seq 1 48); do
  [ -f finalise_status.json ] && break
  sleep 10
done
if [ -f finalise_status.json ]; then
  "$PY" - <<'PY'
import json, time, os
d = json.load(open("finalise_status.json"))
print("  cycle=%s pid=%s job=%s when=%s task=%s ok=%s gate=%s n_cells=%s n_arms=%s"
      % (d.get("cycle"), d.get("pid"), d.get("slurm_job"), d.get("when"), d.get("task"),
         d.get("ok"), d.get("gate"), d.get("n_cells"), d.get("n_arms")))
print("  last_table_mtime=%s" % d.get("last_table_mtime"))
print("  markers=%s failures=%s" % (d.get("n_markers"), d.get("failures")))
PY
else
  echo "  no finalise_status.json yet"
fi

echo
echo "=== writer job log tail ==="
for f in "$Q"/slurm-W-*.out; do
  [ -f "$f" ] || continue
  echo "  --- $f ---"
  tail -20 "$f"
done
echo
echo "=== writer events ==="
grep -E "WRITER|FINALISATION PASS|TASK (START|DONE) +final_" queue_events.log | tail -20
echo
echo "=== table mtime AFTER ==="
ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" \
       "$A/paper_tables/BENCH_EFFICIENCY.csv" 2>/dev/null
