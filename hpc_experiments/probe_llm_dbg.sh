#!/bin/bash -l
#SBATCH --job-name=llm_dbg
#SBATCH --partition=gpu_v100s
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:25:00
#SBATCH --output=slurm-dbg-%j.out
#
# Step-wise debug of the offline load. The previous probe hung for the full hour
# with almost no output, so: every stage runs under its own `timeout`, prints
# flushed, and failures print the traceback instead of dying silently.
set -uo pipefail
module unload default
module load old_modules
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

echo "=== 0. env ==="; date -Is
timeout 15 nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader \
  || echo "NSMI_TIMEOUT - node GPU unhealthy, continuing anyway"
"${PY}" -c "import torch,transformers;print('torch',torch.__version__,'tf',transformers.__version__)"

echo "=== 1. cache inventory ==="
du -sh /home/sychan552/scratch/hf_cache/models--* 2>/dev/null
find /home/sychan552/scratch/hf_cache -name "*.safetensors" -o -name "*.bin" 2>/dev/null | head
find /home/sychan552/scratch/hf_cache -name "*.json" 2>/dev/null | head -6

for M in "Qwen/Qwen2.5-1.5B" "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"; do
  echo; echo "########## ${M} ##########"
  echo "--- 2. config (timeout 120) ---"
  timeout 120 "${PY}" - <<PYEOF
import traceback
try:
    from transformers import AutoConfig
    c = AutoConfig.from_pretrained("${M}", local_files_only=True)
    print("CONFIG OK:", c.model_type, "hidden", getattr(c,"hidden_size",None),
          "layers", getattr(c,"num_hidden_layers",None), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "rc=$?"

  echo "--- 3. tokenizer (timeout 180) ---"
  timeout 180 "${PY}" - <<PYEOF
import traceback
try:
    from transformers import AutoTokenizer
    t = AutoTokenizer.from_pretrained("${M}", local_files_only=True)
    enc = t("Influenza-like illness forecast.", return_tensors="pt")
    print("TOKENIZER OK:", tuple(enc["input_ids"].shape), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "rc=$?"

  echo "--- 4. model load fp16 (timeout 420) ---"
  timeout 420 "${PY}" - <<PYEOF
import traceback, time, torch
try:
    from transformers import AutoModel
    t0=time.time()
    m = AutoModel.from_pretrained("${M}", local_files_only=True,
                                  torch_dtype=torch.float16,
                                  low_cpu_mem_usage=True).cuda().eval()
    n = sum(p.numel() for p in m.parameters())
    print("LOAD OK %.0fs params=%.3fB fp16=%.2fGB" % (time.time()-t0, n/1e9, n*2/1e9), flush=True)
    from transformers import AutoTokenizer
    t = AutoTokenizer.from_pretrained("${M}", local_files_only=True)
    ids = t("Influenza-like illness forecast.", return_tensors="pt").to("cuda")
    torch.cuda.reset_peak_memory_stats(); t0=time.time()
    with torch.no_grad(): out = m(**ids)
    print("FORWARD OK", tuple(out.last_hidden_state.shape),
          "%.3fs peakVRAM %.2fGB" % (time.time()-t0, torch.cuda.max_memory_allocated()/1e9), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
  echo "rc=$?"
done
echo "[dbg] DONE $(date -Is)"
