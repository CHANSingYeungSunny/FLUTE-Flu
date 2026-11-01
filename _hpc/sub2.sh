#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
for f in submit_bisect.sh submit_nlinear_a100.sh; do sed -i 's/\r$//' "$f"; chmod +x "$f"; bash -n "$f" || echo "SYNTAX FAIL $f"; done
echo "=== submitting bisection (tiny/CPU) ==="
sbatch submit_bisect.sh
echo "=== submitting NLinear A100 re-run (stingy, will pend behind 719030) ==="
sbatch submit_nlinear_a100.sh
sleep 12
squeue -u sychan552 -h -o "%.10i %.10P %.16j %.9T" 2>&1 | head
