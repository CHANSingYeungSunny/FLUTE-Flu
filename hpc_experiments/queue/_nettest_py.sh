#!/bin/bash
# Can a COMPUTE node (tiny) do a HuggingFace metadata call + download?
# curl works from this node (measured 719801: HTTP 200); the question is whether
# the python stack that actually downloads (huggingface_hub) can reach the hub.
set -uo pipefail
OUT=$1
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export HF_HUB_CACHE=/home/sychan552/scratch/hf_cache
{
  echo "host=$(hostname) date=$(date '+%F %T')"
  echo "--- proxy env ---"
  env | grep -i -E 'proxy|no_proxy' || echo "no proxy vars"
  echo "--- curlrc ---"
  cat ~/.curlrc 2>/dev/null || echo "no ~/.curlrc"
  echo "--- curl HEAD ---"
  timeout 30 curl -sS -o /dev/null -w 'code=%{http_code} time=%{time_total}\n' \
      https://huggingface.co/api/models/tencent/Penguin-Encoder 2>&1
  echo "--- python urllib 60s ---"
  timeout 70 "$PY" - <<'PY' 2>&1
import json, urllib.request, time
t = time.time()
try:
    r = urllib.request.urlopen("https://huggingface.co/api/models/tencent/Penguin-Encoder", timeout=60)
    d = json.loads(r.read().decode())
    print("URLLIB_OK", r.status, "sha=", d.get("sha"), "dt=%.1fs" % (time.time() - t))
except Exception as e:
    print("URLLIB_FAIL", type(e).__name__, str(e)[:200])
PY
  echo "--- huggingface_hub HfApi (the real download path) ---"
  timeout 120 "$PY" - <<'PY' 2>&1
import time
t = time.time()
try:
    from huggingface_hub import HfApi
    info = HfApi().model_info("tencent/Penguin-Encoder")
    print("HFAPI_OK sha=", info.sha, "dt=%.1fs" % (time.time() - t))
except Exception as e:
    print("HFAPI_FAIL", type(e).__name__, str(e)[:300])
PY
} > "$OUT" 2>&1
