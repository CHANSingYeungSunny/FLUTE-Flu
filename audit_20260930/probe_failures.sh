#!/bin/bash
# Read-only probe: precisely why the two anomalously-stateful jobs failed, and
# whether the independent recomputation ran as a batch job or interactively.
set -uo pipefail
exec > "$HOME/probe_failures.txt" 2>&1

echo "###### 1. A0 587068 - exit 1 but it printed MSE 0.8581: what failed?"
for f in /scratch/sychan552/a0_runs/logs/a0_587068.err /scratch/sychan552/a0_runs/logs/a0_587068.out; do
  echo "----- $f  (size=$(wc -c <"$f" 2>/dev/null))"
  echo "  [last 18 lines]"
  tail -18 "$f" 2>/dev/null | sed 's/^/    /'
done
echo
echo "  [search for traceback / error / killed in 587068]"
grep -inE 'traceback|error|exception|killed|oom|no such|failed|raise' /scratch/sychan552/a0_runs/logs/a0_587068.out 2>/dev/null | tail -20 | sed 's/^/    /'
echo
echo "  [same for the COMPLETED 587091, as the control]"
grep -inE 'traceback|error|exception|killed|oom|raise' /scratch/sychan552/a0_runs/logs/a0_587091.out 2>/dev/null | tail -10 | sed 's/^/    /'
echo "  [587091 last 8 lines]"
tail -8 /scratch/sychan552/a0_runs/logs/a0_587091.out 2>/dev/null | sed 's/^/    /'

echo
echo "###### 2. a0 log files inventory (sizes + mtimes)"
ls -la --time-style=full-iso /scratch/sychan552/a0_runs/logs/ 2>/dev/null | sed 's/^/  /'

echo
echo "###### 3. s6_score logs - where are they and what do they say"
find /scratch/sychan552/a2_stage5 -maxdepth 4 -name '*s6_score*' 2>/dev/null | sed 's/^/  /'
for f in $(find /scratch/sychan552/a2_stage5 -maxdepth 4 -name '*s6_score*' 2>/dev/null); do
  echo "----- $f (size=$(wc -c <"$f"))"
  echo "  [head 12]"; head -12 "$f" | sed 's/^/    /'
  echo "  [tail 25]"; tail -25 "$f" | sed 's/^/    /'
done

echo
echo "###### 4. independent recomputation: batch job or interactive?"
ls -la --time-style=full-iso /scratch/sychan552/a2_stage5/results/stage6/logs/ 2>/dev/null | sed 's/^/  /'
echo "--- recompute_verify.out"
cat /scratch/sychan552/a2_stage5/results/stage6/logs/recompute_verify.out 2>/dev/null | sed 's/^/  /'
echo "--- recompute_verify.err"
cat /scratch/sychan552/a2_stage5/results/stage6/logs/recompute_verify.err 2>/dev/null | sed 's/^/  /'
echo "--- any sbatch job for recompute?"
sacct -u "$USER" -S 2026-09-26 -E now -X --noheader -P \
      --format=JobID,JobName,Submit,End,Elapsed,State 2>/dev/null \
  | grep -iE 'recomp|score' | sed 's/^/  /'
echo "  (if no 'recompute' job appears above, the recompute was run interactively)"

echo
echo "###### 5. per-run evidence files for stage6"
ls /scratch/sychan552/a2_stage5/results/stage6/per_run/ 2>/dev/null | head -12 | sed 's/^/  /'
echo "  count = $(ls /scratch/sychan552/a2_stage5/results/stage6/per_run/ 2>/dev/null | wc -l)"

echo
echo "###### 6. exact GPU-second accounting from sacct for all a0_gpu + s6_* jobs"
sacct -u "$USER" -S 2026-09-26 -E now -X --noheader -P \
      --format=JobID,JobName,ElapsedRaw,State,AllocTRES 2>/dev/null \
  | awk -F'|' '$2 ~ /^(a0_gpu|s6_)/ {print}' | sed 's/^/  /'
echo "  --- totals"
sacct -u "$USER" -S 2026-09-26 -E now -X --noheader -P \
      --format=JobID,JobName,ElapsedRaw,State,AllocTRES 2>/dev/null \
  | awk -F'|' '$2 ~ /^(a0_gpu|s6_)/ {
        g = ($5 ~ /gres\/gpu/) ? 1 : 0;
        tot += $3; if (g) gpu += $3;
        if ($4=="COMPLETED" && g) done += $3;
        if ($4=="COMPLETED" && g) n++;
        if ($4=="FAILED" && g) {fail += $3; m++}
        all += 1
     }
     END {
        printf "  jobs=%d  total_elapsed_s=%d  gpu_elapsed_s=%d (%.4f GPU-h)\n", all, tot, gpu, gpu/3600;
        printf "  COMPLETED-with-GPU: n=%d  s=%d (%.4f GPU-h)\n", n, done, done/3600;
        printf "  FAILED-with-GPU   : n=%d  s=%d (%.4f GPU-h)\n", m, fail, fail/3600
     }'