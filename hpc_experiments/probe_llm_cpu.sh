#!/bin/bash -l
#SBATCH --job-name=llm_cpu
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-cpu-%j.out
#
# CPU-only offline loadability test. gpu_v100s nodes hang inside nvidia-smi
# (uninterruptible sleep), so the GPU route is unavailable. Loading a 1.5B model
# on CPU in fp16 needs ~3 GB RAM and answers the question that matters:
#   can transformers resolve these repos OFFLINE from the shared cache?
set -uo pipefail
module unload default
module load old_modules
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=8

echo "=== env ==="; date -Is
"${PY}" -c "import torch,transformers;print('torch',torch.__version__,'tf',transformers.__version__)"
echo "=== cache ==="; du -sh /home/sychan552/scratch/hf_cache/models--* 2>/dev/null

for M in "Qwen/Qwen2.5-1.5B" "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"; do
  echo; echo "########## ${M} ##########"
  echo "--- config ---"
  timeout 120 "${PY}" - <<PYEOF
import traceback
try:
    from transformers import AutoConfig
    c = AutoConfig.from_pretrained("${M}", local_files_only=True)
    print("CONFIG OK:", c.model_type, getattr(c,"hidden_size",None),
          getattr(c,"num_hidden_layers",None), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "--- tokenizer ---"
  timeout 180 "${PY}" - <<PYEOF
import traceback
try:
    from transformers import AutoTokenizer
    t = AutoTokenizer.from_pretrained("${M}", local_files_only=True)
    e = t("Influenza-like illness forecast.", return_tensors="pt")
    print("TOKENIZER OK:", tuple(e["input_ids"].shape), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "--- model fp16 on CPU + forward ---"
  timeout 600 "${PY}" - <<PYEOF
import traceback, time, torch
try:
    from transformers import AutoModel, AutoTokenizer
    t0=time.time()
    m = AutoModel.from_pretrained("${M}", local_files_only=True,
                                  torch_dtype=torch.float16,
                                  low_cpu_mem_usage=True).eval()
    n = sum(p.numel() for p in m.parameters())
    print("LOAD OK %.0fs params=%.3fB" % (time.time()-t0, n/1e9), flush=True)
    t = AutoTokenizer.from_pretrained("${M}", local_files_only=True)
    ids = t("Influenza-like illness forecast.", return_tensors="pt")
    t0=time.time()
    with torch.no_grad(): out = m(**ids)
    print("FORWARD OK", tuple(out.last_hidden_state.shape),
          "%.1fs" % (time.time()-t0), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "rc=$?"
done
echo "[cpu] DONE $(date -Is)"
