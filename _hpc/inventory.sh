#!/bin/bash
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== ALL ckpt dirs ==="
ls -d "$AR"/ckpt_* 2>/dev/null
echo
echo "=== ALL .pth files (path, bytes, mtime) ==="
find "$AR" -maxdepth 2 -name '*.pth' -printf '%p  %s  %TY-%Tm-%Td %TH:%TM\n' | sort
echo
echo "=== count ==="
find "$AR" -maxdepth 2 -name '*.pth' | wc -l
echo
echo "=== any seed42/43/44 artifacts anywhere in author_runs ==="
find "$AR" -maxdepth 2 \( -name '*seed42*' -o -name '*seed43*' -o -name '*seed44*' -o -name '*_s42*' -o -name '*_s43*' -o -name '*_s44*' \) | sort
echo
echo "=== L24_s42 dir contents ==="
ls -la "$AR"/L24_s42/ 2>&1
echo
echo "=== any pred dirs with s42/s43/s44 ==="
ls -d "$AR"/*_s42* "$AR"/*_s43* "$AR"/*_s44* 2>/dev/null
echo
echo "=== GPU partition status ==="
sinfo -o "%.14P %.6a %.10l %.6D %.6t %.20C" 2>&1 | head -20
echo
echo "=== recent jobs (all states, last 3 days) ==="
sacct -u sychan552 -S $(date -d '3 days ago' +%Y-%m-%d) -o JobID,JobName%30,Partition,State,Elapsed,Start,End 2>&1 | tail -40
