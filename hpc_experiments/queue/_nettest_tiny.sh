#!/bin/bash
# Decisive test: do COMPUTE nodes (tiny partition) have outbound internet?
# Writes its evidence to a file we can read from the login node.
set -uo pipefail
OUT=$1
{
  echo "host=$(hostname) date=$(date '+%F %T')"
  echo "curl_hf_code=$(timeout 20 curl -sS -o /dev/null -w '%{http_code}' https://huggingface.co/api/models/Qwen/Qwen2.5-1.5B 2>&1)"
  echo "python_urllib=$(timeout 20 python3 - <<'PY'
import urllib.request
try:
    r = urllib.request.urlopen('https://huggingface.co/api/models/Qwen/Qwen2.5-1.5B', timeout=15)
    print(r.status, len(r.read()))
except Exception as e:
    print('FAIL', type(e).__name__, str(e)[:120])
PY
)"
} > "$OUT" 2>&1
