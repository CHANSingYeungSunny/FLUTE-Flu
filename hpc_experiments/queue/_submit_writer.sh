#!/bin/bash
# _submit_writer.sh -- deploy the SINGLE writer lane (+ the layout-aware
# watchdog) and prove it wrote. Nothing else is touched.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
A=/gpfs1/home/sychan552/stage5_a2_durable/analysis
cd "$Q" || exit 1

state_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p'; }
start_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p'; }
wall_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^TimeLimit=//p'; }
part_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^Partition=//p'; }
show() { printf '  job %-8s part=%-7s wall=%-11s start=%-20s state=%s\n' \
           "$1" "$(part_of "$1")" "$(wall_of "$1")" "$(start_of "$1")" "$(state_of "$1")"; }

echo "=== 0. the old 10-column watchdog must go ==="
scancel 719844 2>&1
sleep 5
echo "  719844 -> $(state_of 719844)"

echo
echo "=== 1. writer lane (tiny, gres-free, max wall 5 d) ==="
W=$(sbatch --parsable --partition=tiny --cpus-per-task=8 --mem=8G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-W-%j.out" \
      --export=ALL,QUEUE_WRITE_POLL=120,QUEUE_WRITE_MAX_SECONDS=43200 \
      "$Q/writer.sh" 2>&1)
W=${W%%;*}
case "$W" in ''|*[!0-9]*) echo "  WRITER SUBMIT FAILED: $W"; exit 1 ;; esac
printf '%s\n' "$W" > runner_sw.job
show "$W"

echo
echo "=== 2. watchdog (tiny, 11-column aware, max wall) ==="
D=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=5-00:00:00 \
      --requeue --output="$Q/slurm-D-%j.out" \
      --export=ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=432000 \
      "$Q/watchdog.sh" 2>&1)
D=${D%%;*}
case "$D" in ''|*[!0-9]*) echo "  WATCHDOG SUBMIT FAILED: $D"; else show "$D"; fi

echo
echo "=== 3. runner map (what the watchdog believes) ==="
for f in runner_s0.job runner_s1.job runner_scpu.job runner_sw.job; do
  printf '  %-18s %s\n' "$f" "$(tr '\n' ' ' < "$f" 2>/dev/null)"
done

echo
echo "=== 4. table mtime BEFORE the writer runs ==="
ls -l --time-style=+%H:%M:%S "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"

echo
echo "=== 5. wait for the writer's first cycle (max 6 min) ==="
for i in $(seq 1 36); do
  if [ -f finalise_status.json ]; then
    m=$(stat -c %y "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv" 2>/dev/null)
    n=$(/home/sychan552/.conda/envs/mlflu_hpc/bin/python -c 'import json;d=json.load(open("finalise_status.json"));print(d["cycle"],d["pid"],d["when"],d["n_cells"],d["n_arms"])' 2>/dev/null)
    echo "  status: cycle/pid/when/n_cells/n_arms = ${n:-unreadable}"
    echo "  table mtime now: ${m}"
    break
  fi
  sleep 10
done
echo
echo "=== 6. writer log tail ==="
tail -25 "$Q"/slurm-W-*.out 2>/dev/null
echo
echo "=== 7. queue events (writer) ==="
grep -E "WRITER|FINALISATION|final_import|final_miflu|final_analysis|final_verify" queue_events.log | tail -18
