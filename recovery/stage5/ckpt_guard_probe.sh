#!/bin/bash
echo "=== date ==="; date -u; date
echo
echo "=== scratch usage / quota / cleanup ==="
quota -s 2>&1 | head -20
echo "--- lscratch-style info ---"
lscratch -s 2>&1 | head -5 || echo "(no lscratch)"
echo "--- scratch quota by fs ---"
df -h /gpfs1/scratch 2>&1 | tail -2
echo
echo "=== home quota (persistent) ==="
quota -s /home/sychan552 2>&1 | head -10
df -h /home/sychan552 2>&1 | tail -2
echo "--- home used by dirs ---"
du -sh /home/sychan552/* 2>/dev/null | sort -h | tail -20
echo
echo "=== a2_stage5 checkpoint tree ==="
du -sh /scratch/sychan552/a2_stage5/results/stage5/ckpt/author_966/*
ls -1 /scratch/sychan552/a2_stage5/results/stage5/ckpt/author_966/miflu | wc -l
ls -1 /scratch/sychan552/a2_stage5/results/stage5/ckpt/author_966/notext | wc -l
ls -1 /scratch/sychan552/a2_stage5/results/stage5/ckpt/author_966/nlinear | wc -l
echo
echo "=== other existing durable roots (project convention) ==="
ls -d /home/sychan552/*durable* /home/sychan552/innovation_durable 2>/dev/null
du -sh /home/sychan552/innovation_durable 2>/dev/null
echo
echo "=== queue / procs ==="
squeue -u sychan552
tmux ls 2>&1
