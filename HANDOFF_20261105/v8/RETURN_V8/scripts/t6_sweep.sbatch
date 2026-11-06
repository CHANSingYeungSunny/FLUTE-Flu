#!/bin/bash
#SBATCH --job-name=t6_final_sweep
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6sweep_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/t6sweep_%j.err
set -u
echo "host=$(hostname) date=$(date -u +%FT%TZ)"
bash /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/t6_sweep.sh
echo "T6_SWEEP_SCRIPT_RC=$?"
