import os, time
CACHE = "/home/sychan552/scratch/hf_cache"
os.environ["HF_HOME"] = CACHE
os.environ["HF_HUB_CACHE"] = CACHE
from huggingface_hub import snapshot_download

name = "Qwen/Qwen3.8-27B-FP8"
print(f"=== {name} ===", flush=True)
t0 = time.time()
p = snapshot_download(name, cache_dir=CACHE)
print(f"OK {time.time()-t0:.0f}s -> {p}", flush=True)
print("DONE", flush=True)
