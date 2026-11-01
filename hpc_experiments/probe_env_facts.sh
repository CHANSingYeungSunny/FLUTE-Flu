#!/bin/bash
# Facts needed before building the fresh py3.12 env:
#  - which torch version mlflu_hpc uses (so the new env matches in behaviour)
#  - which CUDA the A100 partition provides
#  - exact module names available for conda
echo '=== mlflu_hpc torch version (file read, no import) ==='
head -5 /home/sychan552/.conda/envs/mlflu_hpc/lib/python3.9/site-packages/torch/version.py 2>&1
echo '=== mlflu_hpc torch CUDA build ==='
grep -o '"[^"]*"' /home/sychan552/.conda/envs/mlflu_hpc/lib/python3.9/site-packages/torch/version.py 2>&1 | head -10
echo '=== stingy node features / gres ==='
scontrol show node stingy 2>&1 | head -20
echo '=== module avail miniconda ==='
module avail miniconda Miniconda3 2>&1 | head -30
echo '=== home disk (df, cheap) ==='
df -h /home/sychan552 2>&1 | tail -2
echo END
