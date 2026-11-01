#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
for f in miflu_rep_driver.sh export_miflu_all7.py submit_rep_L36.sh submit_rep_L48.sh submit_rep_L60.sh submit_export_all7.sh; do
  sed -i 's/\r$//' "$f"
done
chmod +x miflu_rep_driver.sh submit_rep_L36.sh submit_rep_L48.sh submit_rep_L60.sh submit_export_all7.sh
bash -n miflu_rep_driver.sh || { echo "DRIVER SYNTAX FAIL"; exit 1; }
echo "DRIVER_BASH_OK"
"${PY}" -c 'import ast; ast.parse(open("export_miflu_all7.py").read()); print("PY_SYNTAX_OK")' || exit 1
# clean empty ckpt dir left by the 34 s cancelled run
rmdir /gpfs1/home/sychan552/stage5_a2_durable/author_runs/ckpt_L36_s2022 2>/dev/null
echo "--- submitting ---"
sbatch submit_rep_L36.sh
sbatch submit_rep_L48.sh
sbatch submit_rep_L60.sh
echo "--- L24 export (no new runs needed: 10 checkpoints already exist) ---"
sbatch --export=ALL,LH=24 submit_export_all7.sh
sleep 12
squeue -u sychan552 -h -o "%.10i %.12P %.16j %.9T"
