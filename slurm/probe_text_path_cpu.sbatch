#!/bin/bash
#SBATCH --job-name=probe_text_cpu
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_text_cpu_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_text_cpu_%j.err
#
# text-path probe, CPU half. No gres/gpu => ZERO GPU-hours.
# Identical script to the GPU half; only --device differs.
#
# WRITES GO TO HOME: the scratch user quota is over its limit (grace expired),
# so /gpfs1/scratch writes fail with "Disk quota exceeded". Scratch is used
# READ-ONLY here (the author repo checkout).
#
# NEVER run this on the login node.
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HOME_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
A0=/scratch/sychan552/a0_replay            # author repo, commit 6ed2101 (READ ONLY)
COMPAT=${HOME_ROOT}/hpc_compat

mkdir -p "${HOME_ROOT}/logs"

echo "[probe-cpu] host=$(hostname) start=$(date -u +%FT%TZ)"
echo "[probe-cpu] slurm job ${SLURM_JOB_ID} partition ${SLURM_JOB_PARTITION}"

# login-node guard: this must run on a compute node
if [[ "$(hostname)" == hpclogin* ]]; then
  echo "[probe-cpu] REFUSING to run on a login node"; exit 3
fi

echo "=== environment (on the compute node) ==="
$PY - <<'PYEOF'
import importlib, sys
print("python", sys.version.split()[0])
for m in ("torch", "transformers", "peft", "einops", "numpy"):
    try:
        mod = importlib.import_module(m)
        print(f"  OK      {m:<12} {getattr(mod, '.__version__', '?') if False else getattr(mod,'__version__','?')}")
    except Exception as e:
        print(f"  MISSING {m:<12} {type(e).__name__}: {e}")
PYEOF
echo "=== end environment ==="

# PYTHONPATH: compat dir FIRST so sitecustomize (numpy aliases + peft symbol)
# and the einops/embed shims load; the author tree is never written to.
export PYTHONPATH="${COMPAT}:${A0}:${PYTHONPATH:-}"

$PY -u "${HOME_ROOT}/scripts/probe_text_path_deterministic.py" \
    --repo "${A0}" \
    --compat "${COMPAT}" \
    --L 24 --batch 8 --device cpu --positive-control \
    --out "${HOME_ROOT}/probe/text_path_probe_cpu.json"

rc=$?
echo "[probe-cpu] exit=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}
