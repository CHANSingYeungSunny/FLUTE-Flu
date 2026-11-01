#!/bin/bash -l
#SBATCH --job-name=llm_probe
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-probe-%j.out
#
# Step 1 of adding SOTA open-source LLM arms. Runs on gpu_a100, which has NO
# submission cap, so it proceeds in parallel with the stingy controller 715984.
#
# It answers the questions that decide whether the arms are feasible at all:
#   1. can the HPC reach HuggingFace and download the weights?
#   2. do they load OFFLINE afterwards (the training job must not need network)?
#   3. hidden size / param count / dtype  -> what the adapter must consume
#   4. one forward pass: VRAM and latency at our batch size 16 x 104 steps
#   5. on-disk size per model, so the compaction scheme can be sized
set -uo pipefail
module unload default
module load old_modules

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CACHE=/home/sychan552/scratch/hf_cache
mkdir -p "${CACHE}"
export HF_HOME="${CACHE}"
export TRANSFORMERS_CACHE="${CACHE}"
export HF_HUB_ENABLE_HF_TRANSFER=0

echo "=== env ==="
"${PY}" -c "import torch, transformers; print('torch', torch.__version__, '| transformers', transformers.__version__)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

for M in "Qwen/Qwen2.5-1.5B" "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"; do
  echo
  echo "=================== ${M} ==================="
  echo "--- 1. download ---"
  "${PY}" - <<PYEOF
import os, sys, time
os.environ.setdefault("HF_HOME", "${CACHE}")
try:
    from huggingface_hub import snapshot_download
    t0 = time.time()
    p = snapshot_download("${M}", cache_dir="${CACHE}")
    print("OK downloaded in %.0fs -> %s" % (time.time() - t0, p))
except Exception as e:
    print("DOWNLOAD_FAILED:", type(e).__name__, str(e)[:300])
    sys.exit(3)
PYEOF
  rc=$?
  [ $rc -ne 0 ] && { echo "[probe] ${M} unusable, continuing"; continue; }

  echo "--- 2. offline load + forward ---"
  "${PY}" - <<PYEOF
import os, time, torch
os.environ["HF_HOME"] = "${CACHE}"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
from transformers import AutoConfig, AutoModel, AutoTokenizer
name = "${M}"
cfg = AutoConfig.from_pretrained(name)
tok = AutoTokenizer.from_pretrained(name)
model = AutoModel.from_pretrained(name, torch_dtype=torch.float16).cuda().eval()
n = sum(p.numel() for p in model.parameters())
print("config:", cfg.model_type, "hidden", getattr(cfg, "hidden_size", None),
      "layers", getattr(cfg, "num_hidden_layers", None))
print("params: %.3f B   fp16 on-disk ~%.2f GB" % (n / 1e9, n * 2 / 1e9))
ids = tok("Influenza-like illness forecast.", return_tensors="pt").to("cuda")
sz = ids["input_ids"].shape
print("tokenizer ok, token shape", tuple(sz))
torch.cuda.reset_peak_memory_stats()
t0 = time.time()
with torch.no_grad():
    out = model(**ids)
el = time.time() - t0
print("forward ok: last_hidden_state", tuple(out.last_hidden_state.shape),
      "| %.3fs | peak VRAM %.2f GB" % (el, torch.cuda.max_memory_allocated() / 1e9))
PYEOF

  echo "--- 3. disk usage ---"
  for d in "${CACHE}"/models--*; do [ -d "$d" ] && du -sh "$d"; done
done

echo
echo "[probe] DONE $(date -Is)"
