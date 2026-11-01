import os, time
os.environ.setdefault("HF_HOME", "/home/sychan552/scratch/hf_cache")
os.environ.setdefault("HF_HUB_CACHE", "/home/sychan552/scratch/hf_cache")
from huggingface_hub import snapshot_download

name = "deepseek-ai/DeepSeek-V2-Lite-Chat"
print(f"=== {name} ===", flush=True)
t0 = time.time()
p = snapshot_download(name, cache_dir="/home/sychan552/scratch/hf_cache")
print(f"OK {time.time()-t0:.0f}s -> {p}", flush=True)
print("DONE", flush=True)
