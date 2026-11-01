import os, traceback
os.environ["HF_HUB_CACHE"] = "/home/sychan552/scratch/hf_cache"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from transformers import AutoConfig, AutoTokenizer

for name in ["Qwen/Qwen2.5-1.5B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"]:
    try:
        c = AutoConfig.from_pretrained(name, local_files_only=True)
        t = AutoTokenizer.from_pretrained(name, local_files_only=True)
        print("OK   %s | %s hidden=%s layers=%s vocab=%s" % (
            name, c.model_type, getattr(c, "hidden_size", None),
            getattr(c, "num_hidden_layers", None), len(t)), flush=True)
    except Exception as e:
        print("FAIL %s | %s: %s" % (name, type(e).__name__, str(e)[:180]), flush=True)
