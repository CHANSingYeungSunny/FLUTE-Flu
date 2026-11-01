#!/bin/bash
set -u
echo "=== cancelling training + old-format export jobs ==="
scancel 718980 718981 718982 718983 718984 718985 718986 2>&1
sleep 6
sacct -j 718980,718981,718982,718983,718984,718985,718986 -o JobID,JobName%16,State,Elapsed 2>&1 | head -24
echo
echo "=== any stale per-seed checkpoints from the killed runs? ==="
ls -la /gpfs1/home/sychan552/stage5_a2_durable/author_runs/ckpt_L*_s20*/ 2>/dev/null | head -30
echo
echo "=== existing all7 CSVs ==="
ls -la /gpfs1/home/sychan552/stage5_a2_durable/author_runs/L*_all7/ 2>/dev/null | head -20
