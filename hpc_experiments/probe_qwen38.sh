#!/bin/bash -l
#SBATCH --job-name=qwen38_load
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-q38-%j.out
#
# Load test for Qwen3.8-27B-FP8 — the only open "latest" LLM small enough to run
# here (DeepSeek's newest open models are 291B-1.7T). Answers:
#   * does the fp8 checkpoint resolve offline?
#   * does ~29 GB of weights fit in an A100-40G with room for activations?
#   * one forward at our sequence length
set -uo pipefail
module unload default
module load old_modules
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export HF_HUB_CACHE=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

echo "=== env ==="; date -Is
timeout 15 nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo NSMI_FAIL
"${PY}" -c "import torch,transformers;print('torch',torch.__version__,'tf',transformers.__version__)"
echo "=== size on disk ==="; du -sh /home/sychan552/scratch/hf_cache/models--Qwen--Qwen3.8-27B-FP8 2>/dev/null

timeout 600 "${PY}" - <<'PYEOF'
import traceback, time, torch
name = "Qwen/Qwen3.8-27B-FP8"
try:
    from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
    c = AutoConfig.from_pretrained(name, local_files_only=True)
    print("CONFIG OK:", c.model_type, "hidden", getattr(c,"hidden_size",None),
          "layers", getattr(c,"num_hidden_layers",None),
          "dtype", getattr(c,"torch_dtype",None), flush=True)
    tok = AutoTokenizer.from_pretrained(name, local_files_only=True)
    t0 = time.time()
    m = AutoModelForCausalLM.from_pretrained(name, local_files_only=True,
                                             torch_dtype="auto", low_cpu_mem_usage=True)
    m = m.cuda().eval()
    n = sum(p.numel() for p in m.parameters())
    print("LOAD OK %.0fs params=%.2fB  VRAM=%.2fGB" % (
        time.time()-t0, n/1e9, torch.cuda.memory_allocated()/1e9), flush=True)
    ids = tok("Influenza-like illness weekly forecast for the next 4 weeks:", return_tensors="pt").to("cuda")
    torch.cuda.reset_peak_memory_stats(); t0=time.time()
    with torch.no_grad(): out = m(**ids, output_hidden_states=True)
    print("FORWARD OK logits", tuple(out.logits.shape), "%.2fs peakVRAM %.2fGB" % (
        time.time()-t0, torch.cuda.max_memory_allocated()/1e9), flush=True)
except Exception:
    traceback.print_exc()
PYEOF
echo "[q38] DONE $(date -Is)"
