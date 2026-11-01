#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
for f in miflu_a100_controller.sh export_miflu_all7.py; do sed -i 's/\r$//' "$f"; done
chmod +x miflu_a100_controller.sh
bash -n miflu_a100_controller.sh || { echo "CTRL SYNTAX FAIL"; exit 1; }
echo "CTRL_BASH_OK"
"${PY}" -c 'import ast; ast.parse(open("export_miflu_all7.py").read()); print("PY_SYNTAX_OK")' || exit 1
echo "--- submitting A100 controller (self-requeueing) ---"
sbatch miflu_a100_controller.sh
sleep 10
squeue -u sychan552 -o "%.10i %.10P %.16j %.9T %R" 2>&1 | head -8
echo
echo "--- L24 export job tail ---"
tail -6 slurm-miflu-all7-719001.out 2>/dev/null
echo
echo "--- L24_all7 so far ---"
ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/L24_all7/ 2>/dev/null | wc -l
