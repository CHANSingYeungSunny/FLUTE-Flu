#!/bin/bash
#SBATCH --job-name=r1_preflight
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_preflight_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_preflight_%j.err
#
# R1 preflight gate. CPU-ONLY, ZERO GPU-HOURS.  PREPARED - NOT SUBMITTED.
set -uo pipefail
R1=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1
PRE=/gpfs1/home/sychan552/official_repo_reproduction_20261006
mkdir -p "${R1}/logs"
[[ "$(hostname)" == hpclogin* ]] && { echo REFUSING; exit 3; }
echo "[r1pre] host=$(hostname) start=$(date -u +%FT%TZ)"
echo "--- gate 1: queue empty ---"
squeue -u "$USER" | tail -n +2 | wc -l | sed 's/^/  queued jobs: /'
echo "--- gate 6: home margin ---"
mmlsquota -u sychan552 home 2>/dev/null | tail -1
echo "--- gate 7/8: no Historical Track B reference in R1 inputs ---"
grep -rIl "innovation_deploy_root_v3" "${PRE}/r1_reproduction_20261006" 2>/dev/null | wc -l | sed 's/^/  files referencing Track B: /'
echo "--- gate 10: scorer acceptance ---"
python3 "${PRE}/f1_preflight_20261006/scorer_acceptance_tests.py" 2>&1 | tail -3
echo "--- gate 4: R1-B trainer present? ---"
for c in "${PRE}/r1_reproduction_20261006/r1_train.py" /scratch/sychan552/a2_stage5/r1_train.py; do
  [[ -f "$c" ]] && echo "  FOUND $c" || echo "  MISSING $c"
done
echo "[r1pre] end=$(date -u +%FT%TZ)"
exit 0
