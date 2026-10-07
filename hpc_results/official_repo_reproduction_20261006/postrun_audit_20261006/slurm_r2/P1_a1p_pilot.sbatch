#!/bin/bash
#SBATCH --job-name=a1p_p1
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/a1p_p1_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/a1p_p1_%A_%a.err
#
# ===========================================================================
# PREPARED, NOT SUBMITTED.  BLOCKED until the paper-contract audit is closed.
# ===========================================================================
# Option P1 - minimum A1-P pilot: 1 seed, 4 horizons, ~1.11 GPU-h.
#
# DO NOT SUBMIT until ALL of these hold:
#   (a) the reconstructed contract is declared in writing, per-parameter
#       provenance labelled (HYPERPARAMETER_PROVENANCE_V2.md);
#   (b) checkpoint selection is VALIDATION-ONLY, replacing the released
#       Test-selection defect;
#   (c) predictions and targets are persisted so the score can be
#       independently recomputed (the released code does NOT do this);
#   (d) the multivariate formulation is used, NOT the released single-channel
#       slice (data_loader.py:305 slices feat_id:feat_id+1).
#
# Until (a)-(d) hold, running this would produce a precise measurement of an
# unrecovered contract - see NEXT_GPU_BUDGET_OPTIONS.md section 3.
#
# Use slurm/miflu_a1_array.sbatch (the A0-R released-code harness) ONLY for
# A0-R. Never label its output A1-P.
# ===========================================================================
set -uo pipefail
echo "[a1p] PREPARED, NOT SUBMITTED, and INTENTIONALLY BLOCKED."
echo "[a1p] Read A2F_FAIR_COMPARISON_CONTRACT.md and"
echo "[a1p] NEXT_GPU_BUDGET_OPTIONS.md section 3 before enabling this script."
exit 0
