#!/bin/bash
#SBATCH --job-name=s6_llm_check
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/sychan552/a2_stage5/logs/s6_llm_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/logs/s6_llm_%j.err
# CPU-only => ZERO GPU-hours. Loads the REAL frozen text backbones and runs one
# forward pass per backbone, so the measured cost estimate rests on verified
# executability rather than on the B-track's assumption that it still works.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 MPLBACKEND=Agg
export ACTIVE_PROFILE=author_966
echo "[s6llm] $(date -u +%FT%TZ) host=$(hostname)"

for BB in qwen_time_llm calf_llm timecma_llm; do
  echo "--- $BB (architecture self-check, real backbone, CPU)"
  /usr/bin/time -f "    wall=%e s maxrss=%M KB" \
  /home/sychan552/.conda/envs/mlflu_hpc/bin/python \
    scripts/train_backbone_966.py --backbone $BB --self-check 2>&1 \
    | grep -E "self-check|wall=|Error|error" | sed 's/^/  /'
done

echo
echo "--- dlinear / patchtst / itransformer (control)"
for BB in dlinear patchtst itransformer; do
  /home/sychan552/.conda/envs/mlflu_hpc/bin/python \
    scripts/train_backbone_966.py --backbone $BB --self-check 2>&1 \
    | grep -E "self-check" | sed 's/^/  /'
done

echo
echo "=== Qwen asset identity actually resolved (must be the pinned revision) ==="
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY' 2>&1 | sed 's/^/  /'
import sys
sys.path.insert(0, "/scratch/sychan552/a2_stage5/scripts")
from innovation import assets as AS
src, kw = AS.resolve_pretrained_source("Qwen/Qwen2.5-1.5B")
print("resolved source :", src)
print("loader kwargs   :", kw)
d = AS.asset_descriptor("Qwen/Qwen2.5-1.5B")
print("repo id         :", d.get("model_repo_id"), "revision:", d.get("model_revision"))
print("declared bytes  :", f"{AS.total_bytes(d):,}")
PY

echo
echo "=== author_966 strict preflight for the two gpt2-backed LLM models (CPU fwd) ==="
for BB in timecma_llm calf_llm; do
  for L in 24 60; do
    /usr/bin/time -f "    wall=%e s maxrss=%M KB" \
    /home/sychan552/.conda/envs/mlflu_hpc/bin/python \
      scripts/train_backbone_966.py --backbone $BB --horizon $L \
      --profile author_966 --containment strict --preflight 2>&1 \
      | grep -E "preflight|wall=|Error" | sed 's/^/  /'
  done
done

echo
echo "[s6llm] done $(date -u +%FT%TZ)"
