#!/bin/bash
# Round 2: the first attempt died on "Disk quota exceeded" while writing into
# /scratch. Write the transcript into $HOME instead and check both filesystem
# quotas, because an exhausted scratch is itself an audit finding.
set -uo pipefail
OUT=$HOME/audit_hpc2.txt
exec > "$OUT" 2>&1

echo "############ 0. quota / usage"
echo "--- home ---"
du -sh "$HOME" 2>/dev/null
df -h "$HOME" 2>/dev/null | tail -2
echo "--- scratch ---"
du -sh /scratch/sychan552 2>/dev/null
df -h /scratch/sychan552 2>/dev/null | tail -2
echo "--- largest dirs in scratch/project ---"
du -sh /scratch/sychan552/a2_stage5/results/* 2>/dev/null | sort -h | tail -8
echo "--- lfs quota if available ---"
lfs quota -u "$USER" /scratch 2>/dev/null | head -12

echo
echo "############ A. job timeline, oldest submit first"
sacct -u "$USER" -S 2026-09-20 -E now -X --noheader \
      --format=JobID,JobName%18,Submit,Start,End,Elapsed,State,AllocTRES%48 -P 2>/dev/null \
  | sort -t'|' -k3 > "$HOME/_tl_tmp.txt"
wc -l < "$HOME/_tl_tmp.txt"
cat "$HOME/_tl_tmp.txt"
rm -f "$HOME/_tl_tmp.txt"

echo
echo "############ B. per-job-name first/last submit and state counts"
sacct -u "$USER" -S 2026-09-20 -E now -X --noheader \
      --format=JobName,State,Submit -P 2>/dev/null \
  | awk -F'|' '{c[$1"|"$2]++; if(!($1 in f) || $3<f[$1]) f[$1]=$3; if($3>l[$1]) l[$1]=$3}
       END{for(k in c){split(k,p,"|");
           printf "  %-18s %-30s n=%-3d first=%s last=%s\n",p[1],p[2],c[k],f[p[1]],l[p[1]]}}' \
  | sort

echo
echo "############ C. A0 587091 (default / multimodal=0) numbers"
grep -inE 'mse|mae|Best performance' "$HOME/../scratch/sychan552/a0_runs/logs/a0_587091.out" 2>/dev/null | tail -8
grep -inE 'mse|mae|Best performance' /scratch/sychan552/a0_runs/logs/a0_587091.out 2>/dev/null | tail -8
echo "--- 587068 tail (why did sacct say FAILED?) ---"
tail -12 /scratch/sychan552/a0_runs/logs/a0_587068.out 2>/dev/null
echo "--- 587091 tail ---"
tail -12 /scratch/sychan552/a0_runs/logs/a0_587091.out 2>/dev/null

echo
echo "############ D. A0 provenance files"
for f in /scratch/sychan552/a0_runs/runs/*_provenance.txt; do
  echo "===== $f"
  cat "$f" 2>/dev/null | head -40
done

echo
echo "############ E. A0 full argv lines (both jobs)"
for j in 587068 587091; do
  echo "--- $j"
  grep -h 'Namespace(' /scratch/sychan552/a0_runs/logs/a0_${j}.out 2>/dev/null | head -2
done

echo
echo "############ F. stage5/stage6 ledger summary"
for s in stage5 stage6; do
  f=/scratch/sychan552/a2_stage5/results/$s/logs/run_ledger.csv
  echo "--- $s  rows=$(tail -n +2 "$f" 2>/dev/null | wc -l)"
  head -1 "$f" 2>/dev/null
  tail -n +2 "$f" 2>/dev/null | awk -F, '{print $NF}' | sort | uniq -c
  echo "    distinct model names:"
  tail -n +2 "$f" 2>/dev/null | awk -F, '{print $3}' | sort | uniq -c
  echo "    first/last start stamp:"
  tail -n +2 "$f" 2>/dev/null | grep -o 'start=[0-9TZ:-]*' | sort | sed -n '1p;$p'
done

echo
echo "############ G. artefacts"
for s in stage5 stage6; do
  echo "--- $s"
  echo "    ckpt=$(find /scratch/sychan552/a2_stage5/results/$s/ckpt -name '*.pth' 2>/dev/null | wc -l)"
  echo "    preds=$(ls /scratch/sychan552/a2_stage5/results/$s/scoring/predictions/*.npz 2>/dev/null | wc -l)"
  echo "    lock=$(tail -n +2 /scratch/sychan552/a2_stage5/results/$s/scoring/CHECKPOINT_LOCK.csv 2>/dev/null | wc -l)"
  echo "    score_matrix rows=$(tail -n +2 /scratch/sychan552/a2_stage5/results/$s/scoring/score_matrix.csv 2>/dev/null | wc -l)"
done

echo
echo "############ H. score matrix headers for both stages"
echo "--- stage5 cols"
head -1 /scratch/sychan552/a2_stage5/results/stage5/scoring/score_matrix.csv 2>/dev/null
echo "--- stage6 cols"
head -1 /scratch/sychan552/a2_stage5/results/stage6/scoring/score_matrix.csv 2>/dev/null

echo
echo "############ I. queue"
squeue -u "$USER" -o '%i %T %M %j %S' 2>/dev/null
echo "(empty = nothing queued)"

echo
echo "############ J. filesystem timestamps of key artefacts (ordering evidence)"
for p in \
  /scratch/sychan552/a0_runs/logs/a0_587091.out \
  /scratch/sychan552/a0_runs/logs/a0_587068.out \
  /scratch/sychan552/a2_stage5/results/stage5/scoring/CHECKPOINT_LOCK.json \
  /scratch/sychan552/a2_stage5/results/stage5/scoring/score_matrix.csv \
  /scratch/sychan552/a2_stage5/results/stage6/scoring/CHECKPOINT_LOCK.json \
  /scratch/sychan552/a2_stage5/results/stage6/scoring/score_matrix.csv ; do
  [ -e "$p" ] && stat -c '  %y  %n' "$p"
done