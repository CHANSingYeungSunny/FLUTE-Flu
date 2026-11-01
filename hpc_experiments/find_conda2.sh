#!/bin/bash
# The task brief said "module load Conda/1.10.0", but on this cluster Conda/1.10.0
# is only an extension of IJulia. Real conda distributions are Miniconda3/Anaconda3.
echo '--- spider miniconda ---'
module spider Miniconda3 2>&1 | head -30
echo '--- spider anaconda ---'
module spider Anaconda3 2>&1 | head -30
echo '--- spider miniconda (lower) ---'
module spider miniconda 2>&1 | head -30
echo '--- mlflu_hpc python version ---'
/home/sychan552/.conda/envs/mlflu_hpc/bin/python -V
echo END
