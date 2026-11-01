#!/bin/bash
# Housekeeping after the 2026-11-01 scope reversal.
#
# The 42/43/44 design was overruled (AGENTS.md HARD RULE 10: two protocols,
# never mixed). Artefacts produced by the cancelled jobs 718929 / 718930 must be
# moved out of the way so nothing downstream can import them as a benchmark row.
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
Q="${AR}/_quarantine_seeds424344"
mkdir -p "${Q}"
for d in L24_s42 L24_s43 L24_s44 L36_s42 L36_s43 L36_s44 L48_s42 L48_s43 L48_s44 L60_s42 L60_s43 L60_s44; do
  if [ -d "${AR}/${d}" ]; then mv "${AR}/${d}" "${Q}/" && echo "[moved] ${d}"; fi
done
for d in ckpt_L24_s42 ckpt_L24_s43 ckpt_L24_s44 ckpt_L36_s42 ckpt_L36_s43 ckpt_L36_s44 ckpt_L48_s42 ckpt_L48_s43 ckpt_L48_s44 ckpt_L60_s42 ckpt_L60_s43 ckpt_L60_s44; do
  if [ -d "${AR}/${d}" ]; then mv "${AR}/${d}" "${Q}/" && echo "[moved] ${d}"; fi
done
if [ -d "${AR}/_seedruns" ]; then
  for d in "${AR}"/_seedruns/*; do
    [ -d "$d" ] && mv "$d" "${Q}/" && echo "[moved] _seedruns/$(basename "$d")"
  done
fi
echo
echo "=== author_runs top level now ==="
ls -1 "${AR}"
echo
echo "=== quarantine ==="
ls -1 "${Q}" 2>/dev/null
