#!/bin/bash
# Budget accounting for the Stage-5 A2 round (user cap = 2.0 GPU-hours).
echo "=== per-job allocation (top-level only, -X) ==="
sacct -u sychan552 -S 2026-09-24 -X --noheader \
      --format=JobID,JobName,State,Elapsed,AllocTRES%40,Submit,Start,End -P
echo
echo "=== GPU-seconds / GPU-hours total (gres/gpu allocated, -X) ==="
sacct -u sychan552 -S 2026-09-24 -X --noheader --format=Elapsed,AllocTRES%40 -P \
| awk -F'|' '
  {
    el=$1; tres=$2;
    n=index(el,"-");
    if (n>0) { d=substr(el,1,n-1); t=substr(el,n+1) } else { d=0; t=el }
    split(t,a,":"); s=d*86400+a[1]*3600+a[2]*60+a[3];
    g=0;
    if (match(tres,/gpu:[a-z0-9]+:[0-9]+/)) {
      x=substr(tres,RSTART,RLENGTH); split(x,b,":"); g=b[3];
    }
    tot += s*g;
    if (g>0) printf "  %-10s %-14s %-12s gpu=%d  %8.1f s  %.4f GPU-h\n", $3, $1, "", g, s, s*g/3600;
  }
  END { printf "\nTOTAL = %.0f GPU-s = %.4f GPU-hours\n", tot, tot/3600 }'
echo
echo "=== node state / pending ==="
squeue -u sychan552
echo "=== running dispatchers / tmux on login ==="
ps -u sychan552 -o pid,etime,cmd | grep -Ei "dispatch|tmux|score_test|train_" | grep -v grep
echo "=== tmux sessions ==="
tmux ls 2>&1
echo "=== nohup.out ==="
ls -la ~/nohup.out /scratch/sychan552/a2_stage5/nohup.out 2>&1 | head
