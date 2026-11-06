#!/bin/bash
#SBATCH --job-name=wf_probe
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/probe_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/probe_%j.err
set -u
echo "host=$(hostname) date=$(date -u +%FT%TZ)"
/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python -u /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/wf_probe.py
echo "PY_RC=$?"
