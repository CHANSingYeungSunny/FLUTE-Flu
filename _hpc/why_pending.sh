#!/bin/bash
set -u
echo "=== user queue (all states) ==="
squeue -u sychan552 -o '%.8i %.14j %.8P %.9T %.10M %.6D %.25R' 2>&1
echo
echo "=== stingy partition queue ==="
squeue -p stingy -o '%.8i %.10u %.14j %.9T %.10M %.25R' 2>&1 | head -15
echo
echo "=== nodes with a100 gres ==="
sinfo -N -p stingy -o '%.14N %.10P %.8t %.20G %.10C %.12m' 2>&1 | head -15
echo
echo "=== job 719191 detail (scontrol) ==="
scontrol show job 719191 2>&1 | head -30
