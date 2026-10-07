#!/bin/bash
#SBATCH --job-name=s6_cpu_validate
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/sychan552/a2_stage5/logs/s6_validate_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/logs/s6_validate_%j.err
#
# Stage 6 CPU validation — ZERO GPU request, therefore ZERO GPU-hours.
#   part 1: A0 released-code CPU audit (deps, assets, imports, split arithmetic)
#   part 2: six-backbone architecture self-check (forward shapes, no training)
#   part 3: author_966 strict-window preflight for each backbone (CPU forward)
# Nothing here trains, scores Test, or touches a GPU.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
export MPLBACKEND=Agg
mkdir -p logs

echo "############ PART 1 — A0 released-code CPU audit ############"
bash recovery/a0/a0_cpu_audit.sh 2>&1

echo
echo "############ PART 2 — backbone architecture self-check ############"
for BB in dlinear patchtst itransformer qwen_time_llm calf_llm timecma_llm; do
  echo "--- $BB"
  $PY scripts/train_backbone_966.py --backbone $BB --self-check 2>&1 | grep -E "self-check" | sed 's/^/  /'
done

echo
echo "############ PART 3 — author_966 strict preflight (CPU) ############"
for BB in dlinear patchtst itransformer; do
  for L in 24 60; do
    echo "--- $BB L=$L"
    $PY scripts/train_backbone_966.py --backbone $BB --horizon $L \
        --profile author_966 --containment strict --preflight 2>&1 | tail -3 | sed 's/^/  /'
  done
done

echo
echo "############ PART 4 — reuse proof: A2 MIFlu/NLinear protocol identity ############"
$PY - <<'PY' 2>&1 | sed 's/^/  /'
import hashlib, inspect, sys, os
sys.path.insert(0, "/scratch/sychan552/a2_stage5/scripts")
import train_nlinear_966 as A2
src = inspect.getsource(A2)
print("train_nlinear_966.load_and_normalize sha256 :",
      hashlib.sha256(A2.load_and_normalize.__code__.co_code.__repr__().encode()).hexdigest()[:16])
print("train_nlinear_966.build_windows   sha256 :",
      hashlib.sha256(A2.build_windows.__code__.co_code.__repr__().encode()).hexdigest()[:16])
print("train_nlinear_966.eval_mse        sha256 :",
      hashlib.sha256(A2.eval_mse.__code__.co_code.__repr__().encode()).hexdigest()[:16])
import train_backbone_966 as S6
print("train_backbone_966 reuses the SAME objects:",
      S6.build_windows is A2.build_windows,
      S6.load_and_normalize is A2.load_and_normalize,
      S6.eval_mse is A2.eval_mse)
# window counts must equal the frozen A2 table
for L in (24, 36, 48, 60):
    dd = A2.load_and_normalize("author_966")
    Xt, Yt, Xv, Yv, Xte, Yte, s = A2.build_windows(
        dd["data_norm"], 104, L, dd["train_end"], dd["val_end"], containment="strict")
    print(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)}")
PY

echo
echo "############ PART 5 — code identity of the eight-model branch ############"
sha256sum scripts/train_backbone_966.py scripts/train_nlinear_966.py \
          scripts/innovation/backbones/dlinear.py \
          scripts/innovation/backbones/patchtst.py \
          scripts/innovation/backbones/itransformer.py \
          scripts/innovation/backbones/llm_inspired.py \
          scripts/innovation/assets.py scripts/configs.py 2>&1 | sed 's/^/  /'
echo
echo "[s6] CPU validation done $(date -u +%FT%TZ)"
