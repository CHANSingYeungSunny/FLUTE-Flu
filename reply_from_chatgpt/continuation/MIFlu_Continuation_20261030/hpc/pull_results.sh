#!/bin/bash
# Run on the user's local computer/Git Bash after jobs finish; no delete/mirror.
set -euo pipefail
MIFLU_HOST=sychan552@burgundy.hpc.cityu.edu.hk
MIFLU_REMOTE=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030
MIFLU_LOCAL="${1:-./HPC_results_20261030}"
mkdir -p "${MIFLU_LOCAL}"
scp -r "${MIFLU_HOST}:${MIFLU_REMOTE}/runs" "${MIFLU_LOCAL}/"
scp -r "${MIFLU_HOST}:${MIFLU_REMOTE}/logs" "${MIFLU_LOCAL}/"
scp -r "${MIFLU_HOST}:${MIFLU_REMOTE}/paper_tables" "${MIFLU_LOCAL}/"
