#!/bin/bash
set -uo pipefail
cd /home/sychan552/stage5_a2_durable || exit 1
rm -f STAGE5_A2_DURABLE_SHA256SUMS.txt
find . -type f ! -name 'STAGE5_A2_DURABLE_SHA256SUMS.txt' -exec sha256sum {} + \
  | sort -k2 > STAGE5_A2_DURABLE_SHA256SUMS.txt
echo "files=$(wc -l < STAGE5_A2_DURABLE_SHA256SUMS.txt)"
du -sh .
ls -1 stage6 a0 a1
