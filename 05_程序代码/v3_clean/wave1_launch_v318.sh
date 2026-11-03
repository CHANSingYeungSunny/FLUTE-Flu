#!/bin/bash
# Wave-1 launcher (v3.18). Reads the one-time authorization token from its file
# into the environment and execs the controller. The controller validates the
# token and IMMEDIATELY unsets it, so the value can never reach a sbatch child,
# a log, a manifest or an artifact. The value is never printed here.
set -euo pipefail

BASE=/scratch/sychan552/_v318d
cd "$BASE"

TOKEN_FILE="$BASE/wave1_authorization.token"
[ -f "$TOKEN_FILE" ] || { echo "[launch] FAIL-STOP: token file missing" >&2; exit 1; }

export WAVE1_AUTHORIZATION_TOKEN="$(cat "$TOKEN_FILE")"
exec bash "$BASE/wave1_controller_v318.sh"
