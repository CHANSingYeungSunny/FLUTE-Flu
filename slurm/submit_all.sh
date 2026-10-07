#!/bin/bash
# Submit order for the 2026-10-06 continuation round.
# RUN THIS ON THE LOGIN NODE (sbatch submission only — never compute).
#
# stingy allows ONE concurrent job, so everything is chained with
# --dependency=afterok.
set -euo pipefail

echo "STEP 0 — confirm nothing of ours is already queued (do NOT duplicate runs):"
squeue -u "$USER"
sacct -S 2026-09-26 -X -o JobID,JobName,State,Elapsed,AllocTRES | head -40

echo
echo "STEP 1 — text-path probe, CPU half (zero GPU-hours):"
CPU_ID=$(sbatch --parsable slurm/probe_text_path_cpu.sbatch)
echo "  cpu probe job = ${CPU_ID}"

echo "STEP 2 — text-path probe, GPU half, chained after the CPU half:"
GPU_ID=$(sbatch --parsable --dependency=afterok:${CPU_ID} slurm/probe_text_path_gpu.sbatch)
echo "  gpu probe job = ${GPU_ID}"

echo "STEP 3 — compare the two probe JSONs and write text_path_probe_comparison.csv:"
sbatch --dependency=afterok:${GPU_ID} --partition=stingy \
       --job-name=probe_cmp --time=00:10:00 --mem=4G \
       --output=/gpfs1/scratch/sychan552/CHATTIME/Chattime/logs/probe_cmp_%j.out \
       --wrap "python3 slurm/probe_text_path_compare.py"

echo
echo "STEP 4 — A1 reproduction array (8 fits, ~0.1 GPU-hours at the measured 0.0125 h/fit):"
echo "  NOTE: A1 is a reconstructed configuration, NOT a reproduction claim."
echo "  Uncomment only when the budget for it is confirmed:"
echo "  # sbatch --dependency=afterok:${GPU_ID} slurm/miflu_a1_array.sbatch"
