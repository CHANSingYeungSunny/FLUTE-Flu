#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo "=== cancelling the two ad-hoc jobs to free the QOS slots ==="
scancel 718998 719001 2>&1
sleep 8
sacct -j 718998,719001 -o JobID,JobName%16,State,Elapsed 2>&1 | head -6
echo
sed -i 's/\r$//' miflu_a100_controller.sh
chmod +x miflu_a100_controller.sh
bash -n miflu_a100_controller.sh && echo CTRL_BASH_OK
echo "=== submit single A100 controller (L24 exports + 27 training cells) ==="
sbatch miflu_a100_controller.sh
sleep 10
squeue -u sychan552 -o "%.10i %.10P %.16j %.9T %R" 2>&1 | head -6
