import os, sys, time
os.environ.setdefault("HF_HOME", "/home/sychan552/scratch/hf_cache")
from huggingface_hub import snapshot_download

for name in ["Qwen/Qwen2.5-1.5B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"]:
    print(f"=== {name} ===", flush=True)
    t0 = time.time()
    try:
        p = snapshot_download(name, cache_dir=os.environ["HF_HOME"])
        print(f"OK {time.time()-t0:.0f}s -> {p}", flush=True)
    except Exception as e:
        print(f"FAILED {type(e).__name__}: {str(e)[:300]}", flush=True)
print("ALL DONE", flush=True)
