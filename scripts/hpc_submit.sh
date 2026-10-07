#!/usr/bin/env bash
# ============================================================================
#  hpc_submit.sh  —  Submit the journal-reproducibility experiments to `stingy`
# ============================================================================
#  The `stingy` partition permits ONLY ONE concurrent job with a 4h wall limit.
#  Strategy:
#    * One job runs the SEQUENTIAL orchestrator (run_journal_experiments.py),
#      which chains every experiment; train_ablation.py resumes per-experiment,
#      so if the 4h limit is hit mid-job, simply re-submit this same script and
#      completed (L, rep) pairs are skipped.
#    * Each experiment writes to its own dir:
#        hpc_results/journal_evidence/<exp>/reps_1_to_10/{metrics.csv,
#                                                          summary.csv,
#                                                          rep_*/checkpoint.pth,
#                                                          predictions_miflu_L24_*.csv}
#
#  Edit the scheduler directives below for your cluster. Defaults are SLURM;
#  PBS (qsub) equivalents are commented.
# ----------------------------------------------------------------------------
#SBATCH --job-name=miflu_journal
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:1                 # MIFlu needs a GPU; remove if CPU-only.
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00             # hard 4h cap on stingy
#SBATCH --output=hpc_results/journal_evidence/slurm_%j.out
#SBATCH --error=hpc_results/journal_evidence/slurm_%j.err
## PBS equivalent:
##   #PBS -N miflu_journal
##   #PBS -q stingy
##   #PBS -l nodes=1:ppn=8:gpus=1,mem=32gb,walltime=04:00:00
##   #PBS -o hpc_results/journal_evidence/pbs.out
##   #PBS -e hpc_results/journal_evidence/pbs.err

set -euo pipefail
cd "$(dirname "$0")/.."                       # project root

# Resume-safe: re-submitting re-runs only missing (L, rep) pairs.
python scripts/run_journal_experiments.py "$@"

# ----------------------------------------------------------------------------
#  Optional: after the sweep completes, build the aggregated Table VIII + the
#  supplementary physical-unit table + the evaluation figures, on the HPC or
#  locally:
#    python scripts/aggregate_journal_tables.py
#    python scripts/make_miflu_evaluation_figure.py \
#        --pred_csv hpc_results/journal_evidence/full/reps_1_to_10/predictions_miflu_L24_paper_protocol.csv \
#        --L 24 --fig_dir results/ili/figures --met_dir results/ili/metrics
# ----------------------------------------------------------------------------
