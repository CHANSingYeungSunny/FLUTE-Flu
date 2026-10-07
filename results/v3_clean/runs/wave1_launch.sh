#!/bin/bash
# ==========================================================================
# clean-v3 Wave-1 launcher (separate from the controller BY DESIGN)
#
# Its ONLY job is to read the one-time authorization token from its file into
# the environment and exec the controller. The controller then validates the
# token and IMMEDIATELY unsets it, so the value can never reach a Slurm job
# environment, a log, a manifest or an artifact.
#
# The token value is never printed, echoed or logged here.
# ==========================================================================
set -euo pipefail

# resolve the deployment root from this script's own location:
#   <root>/results/v3_clean/runs/wave1_launch.sh
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
cd "$ROOT"

TOKEN_FILE="results/v3_clean/runs/wave1_authorization.token"
[ -f "$TOKEN_FILE" ] || { echo "[launch] FAIL-STOP: token file missing" >&2; exit 1; }

export WAVE1_AUTHORIZATION_TOKEN="$(cat "$TOKEN_FILE")"
exec bash results/v3_clean/runs/wave1_controller.sh
