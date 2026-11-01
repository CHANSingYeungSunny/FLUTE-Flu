#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
for f in miflu_rep_driver.sh submit_rep_L36.sh submit_rep_L48.sh submit_rep_L60.sh submit_export_all7.sh export_miflu_all7.py _quarantine.sh; do
  sed -i 's/\r$//' "$f"
done
chmod +x miflu_rep_driver.sh submit_rep_L36.sh submit_rep_L48.sh submit_rep_L60.sh submit_export_all7.sh _quarantine.sh
for s in miflu_rep_driver.sh submit_rep_L36.sh submit_rep_L48.sh submit_rep_L60.sh submit_export_all7.sh; do
  bash -n "$s" || { echo "SYNTAX FAIL $s"; exit 1; }
done
echo "BASH_OK"
"${PY}" -c 'import ast; ast.parse(open("export_miflu_all7.py").read()); print("PY_SYNTAX_OK")'
echo "--- quarantine ---"
bash _quarantine.sh
