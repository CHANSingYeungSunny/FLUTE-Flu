#!/bin/bash
#SBATCH --job-name=f1_phase3c
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase3c_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase3c_%j.err
#
# Phase 3c only: text-path verification on the four F1 corrected-MIFlu checkpoints.
# CPU-ONLY, ZERO GPU-HOURS. Re-run after fixing the dataset-selection defect in
# f1_text_probe.py (it had chosen the author's numeric-column file, giving
# KeyError: '% WEIGHTED ILI').
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CODE_ROOT=/scratch/sychan552/a2_stage5
F1_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1
F1PRE=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1_preflight_20261006
SEED=42
if [[ "$(hostname)" == hpclogin* ]]; then echo REFUSING; exit 3; fi
echo "[f1p3c] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
FAIL=0
for L in 24 36 48 60; do
  CK="${F1_ROOT}/ckpt/miflu/best_miflu_L${L}_seed${SEED}.pth"
  if [[ -f "${CK}" ]]; then
    $PY -u "${F1PRE}/f1_text_probe.py" --ckpt "${CK}" --L ${L} \
        --code-root "${CODE_ROOT}" \
        --out "${F1_ROOT}/scoring/text_path_probe_L${L}.json" 2>&1 | tail -8 \
      || { echo "  FAILED L=${L}"; FAIL=$((FAIL+1)); }
  else
    echo "  [SKIP] no checkpoint L=${L}"; FAIL=$((FAIL+1))
  fi
done
echo "[f1p3c] failures=${FAIL} end=$(date -u +%FT%TZ)"
exit $(( FAIL > 0 ? 1 : 0 ))
