#!/bin/bash
# _find_tencent_cache.sh -- the 7 tencent arms are not in scratch/hf_cache; find
# wherever the probe job actually put them. Read-only, bounded depth.
set -uo pipefail
echo "=== HF_HOME-style caches under scratch and home (depth 3) ==="
find /home/sychan552/scratch /home/sychan552 -maxdepth 3 -type d -name 'models--tencent--*' \
  -printf '  %p\n' 2>/dev/null | head -20
echo
echo "=== any models--* dir at all under scratch (depth 3) ==="
find /home/sychan552/scratch -maxdepth 3 -type d -name 'models--*' -printf '  %p\n' 2>/dev/null | head -20
echo
echo "=== hf_models (the curl-fallback target) ==="
ls -1 /home/sychan552/scratch/hf_models 2>/dev/null | head -20 || echo "  absent"
echo
echo "=== scratch top level sizes ==="
ls -1 /home/sychan552/scratch 2>/dev/null | head -20
echo
echo "=== cache dirs referenced by any recent job output ==="
grep -l 'HF_HOME' /gpfs1/home/sychan552/stage5_a2_durable/code/queue/*.sh 2>/dev/null | head
grep -h 'HF_HOME' /gpfs1/home/sychan552/stage5_a2_durable/code/queue/*.sh 2>/dev/null | sort -u | head
echo
echo "=== what 720218 was told to do (its spooled script is gone, look for its wrapper) ==="
ls -1t /gpfs1/home/sychan552/stage5_a2_durable/code/queue/*probe* \
        /gpfs1/home/sychan552/stage5_a2_durable/code/*probe* 2>/dev/null | head -10
echo
echo "=== disk ==="
df -h /home/sychan552/scratch /gpfs1/home/sychan552 2>/dev/null | sed 's/^/  /'
