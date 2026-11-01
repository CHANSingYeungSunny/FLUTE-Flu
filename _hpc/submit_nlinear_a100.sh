#!/bin/bash -l
#SBATCH --job-name=nlinear_a100
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-nlinear-a100-%j.out
#
# Re-run the 12 NLinear benchmark cells on A100.
#
# WHY: `paper_tables/BENCH_GPU_PROVENANCE.csv` shows the 204 benchmark cells were
# NOT homogeneous -- 192 on A100-SXM4-80GB (job 715984) but the 12 NLinear cells
# on V100-SXM2-32GB (job 717950, gpu-v100s-04). NLinear is the K&S champion, so a
# champion measured on different silicon from its 15 competitors is indefensible
# (AGENTS.md HARD RULE 12). The other 192 cells are NOT touched.
#
# The old V100 cells are preserved under expanded_runs_v100_nlinear/ for the
# before/after record rather than deleted.
set -uo pipefail
module unload default
module load old_modules
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
EXP=/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs
OLD=/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs_v100_nlinear
cd "${CODE}"

echo "[nlinear-a100] host=$(hostname) node=${SLURM_JOB_NODELIST:-?} job=${SLURM_JOB_ID:-?} start=$(date -Is)"
"${PY}" -c "import torch,sys
n=torch.cuda.get_device_name(0); print('[nlinear-a100] MEASURED gpu=',n, torch.cuda.get_device_capability(0))
sys.exit(0 if 'A100' in n else 4)" || { echo "[nlinear-a100] not an A100 - aborting"; exit 1; }

mkdir -p "${OLD}"
for L in 24 36 48 60; do
  for s in 42 43 44; do
    d="${EXP}/nlinear_L${L}_s${s}"
    # preserve the V100 cell before overwriting it
    if [ -f "${d}/pred_nlinear_L${L}_s${s}.npz" ]; then
      mkdir -p "${OLD}/nlinear_L${L}_s${s}"
      cp -n "${d}/pred_nlinear_L${L}_s${s}.npz" "${OLD}/nlinear_L${L}_s${s}/" 2>/dev/null || true
      [ -f "${d}/metrics.csv" ] && cp -n "${d}/metrics.csv" "${OLD}/nlinear_L${L}_s${s}/" 2>/dev/null || true
    fi
    echo "=== nlinear L=${L} seed=${s} $(date +%H:%M:%S) ==="
    "${PY}" -u train_backbone_966.py --backbone nlinear --horizon "${L}" --seed "${s}" \
      --profile author_966 --containment strict \
      --export-dir "${d}" --ckpt-dir "${d}/ckpt_a100" || echo "[FAIL] nlinear L=${L} s=${s}"
  done
done
echo "[nlinear-a100] DONE $(date -Is)"
ls -1 "${EXP}"/nlinear_L*_s*/pred_*.npz 2>/dev/null | wc -l
