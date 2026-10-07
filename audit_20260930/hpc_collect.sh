#!/bin/bash
# Read-only collection of the scheduler's own record for every job this account
# ran, plus the run ledgers the jobs wrote. Nothing here submits or modifies
# anything; it exists so the audit can quote scheduler timestamps instead of
# transcribed reports.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 2>/dev/null || cd /scratch/sychan552

echo "############ A. full job timeline (Submit -> Start -> End), oldest first"
sacct -u "$USER" -S 2026-09-20 -E now -X --noheader \
      --format=JobID,JobName%18,Submit,Start,End,Elapsed,State,AllocTRES%52 -P 2>/dev/null \
| sort -t'|' -k3

echo
echo "############ B. job-name inventory with counts and first/last submit"
sacct -u "$USER" -S 2026-09-20 -E now -X --noheader \
      --format=JobName,State,Submit -P 2>/dev/null \
| awk -F'|' '{c[$1"|"$2]++; if(!(($1) in f) || $3<f[$1]) f[$1]=$3; if($3>l[$1]) l[$1]=$3}
     END{for(k in c){split(k,p,"|"); printf "  %-18s %-28s n=%-3d first=%s last=%s\n",p[1],p[2],c[k],f[p[1]],l[p[1]]}}' \
| sort

echo
echo "############ C. A0 evidence: what the two diagnostic jobs actually contain"
for j in 587048 587054 587059 587068 587091; do
  echo "--- job $j ---"
  for d in /scratch/sychan552/a0_runs/logs /scratch/sychan552/a2_stage5/results/stage6/a0_gpu /scratch/sychan552/a2_stage5/results/stage6/logs; do
    for f in "$d"/*"$j"*; do
      [ -e "$f" ] || continue
      echo "    FILE $f  ($(wc -c <"$f") bytes)"
    done
  done
done

echo
echo "############ D. A0 terminal numbers, straight from the job outputs"
for j in 587068 587091; do
  f=$(ls /scratch/sychan552/a0_runs/logs/a0_${j}*.out 2>/dev/null | head -1)
  echo "--- $j : ${f:-<no out file>}"
  [ -n "$f" ] && { echo "    first line: $(head -1 "$f")"; echo "    mse/mae lines:"; grep -inE 'mse|mae' "$f" | tail -6; }
  e=$(ls /scratch/sychan552/a0_runs/logs/a0_${j}*.err 2>/dev/null | head -1)
  [ -n "$e" ] && { echo "    stderr tail:"; tail -6 "$e"; }
done

echo
echo "############ E. A0 ledger as written by the jobs"
cat /scratch/sychan552/a0_runs/a0_ledger.csv 2>/dev/null
find /scratch/sychan552/a0_runs -maxdepth 2 -name '*.csv' -o -maxdepth 2 -name '*.txt' 2>/dev/null | head -20

echo
echo "############ F. Stage 5 (A2) run ledger"
head -1 results/stage5/logs/run_ledger.csv 2>/dev/null
tail -n +2 results/stage5/logs/run_ledger.csv 2>/dev/null | wc -l

echo
echo "############ G. Stage 6 run ledger"
head -1 results/stage6/logs/run_ledger.csv 2>/dev/null
tail -n +2 results/stage6/logs/run_ledger.csv 2>/dev/null | head -5
echo "   rows = $(tail -n +2 results/stage6/logs/run_ledger.csv 2>/dev/null | wc -l)"

echo
echo "############ H. artefacts on disk"
echo "  stage5 ckpt  = $(find results/stage5/ckpt -name '*.pth' 2>/dev/null | wc -l)"
echo "  stage6 ckpt  = $(find results/stage6/ckpt -name '*.pth' 2>/dev/null | wc -l)"
echo "  stage5 preds = $(ls results/stage5/scoring/predictions/*.npz 2>/dev/null | wc -l)"
echo "  stage6 preds = $(ls results/stage6/scoring/predictions/*.npz 2>/dev/null | wc -l)"
echo "  stage5 lock  = $(tail -n +2 results/stage5/scoring/CHECKPOINT_LOCK.csv 2>/dev/null | wc -l)"
echo "  stage6 lock  = $(tail -n +2 results/stage6/scoring/CHECKPOINT_LOCK.csv 2>/dev/null | wc -l)"

echo
echo "############ I. scoring summary files"
ls -la results/stage5/scoring/ 2>/dev/null | head -25
echo "---"
ls -la results/stage6/scoring/ 2>/dev/null | head -25

echo
echo "############ J. any queue right now"
squeue -u "$USER" -o '%i %T %M %j %S' 2>/dev/null