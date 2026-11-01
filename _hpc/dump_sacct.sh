#!/bin/bash
# Fresh accounting dump for scripts/build_bench_gpu_provenance.py (login-node safe: sacct + cat).
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
OUT="${CODE}/_sacct_dump.csv"
sacct -S 2026-10-25 -P -o JobID,JobIDRaw,JobName,Partition,State,NodeList,Start,End,Elapsed > "${OUT}" 2>/dev/null
echo "rows=$(wc -l < "${OUT}")"
head -2 "${OUT}"
echo "--- the three jobs this turn cared about ---"
grep -E "^(719030|719191|719222)\|" "${OUT}" | head -12
