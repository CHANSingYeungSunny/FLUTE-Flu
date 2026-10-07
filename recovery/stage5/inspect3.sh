#!/bin/bash
cd /scratch/sychan552/a2_stage5 || exit 1
echo "=== ckpt sizes ==="
du -sh results/stage5/ckpt/author_966/*
ls -la results/stage5/ckpt/author_966/miflu | head -5
ls -la results/stage5/ckpt/author_966/nlinear | head -5
echo "=== quota ==="
quota -s 2>&1 | head -20
df -h /scratch/sychan552 2>&1 | tail -2
echo "=== deploy root listing ==="
ls -la /scratch/sychan552/a2_stage5
echo "=== scripts dir ==="
ls -la /scratch/sychan552/a2_stage5/scripts | head -40
echo "=== data dir ==="
ls -la /scratch/sychan552/a2_stage5/data
echo "=== results total ==="
du -sh results
