#!/bin/bash
# DEFAULT-DENY one-time Test runner. Requires an explicit authorization token.
set -euo pipefail
: "${ONE_TIME_TEST_AUTHORIZATION:?REFUSED: set ONE_TIME_TEST_AUTHORIZATION=<token>}"
: "${INNOVATION_DEPLOYMENT_ROOT:?set INNOVATION_DEPLOYMENT_ROOT to the v2.10 root}"
cd "$INNOVATION_DEPLOYMENT_ROOT"
EXPECT="558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5"
ACTUAL="$(sha256sum results/innovation/frozen_model_manifest.json | cut -d" " -f1)"
if [ "$ACTUAL" != "$EXPECT" ]; then echo "FREEZE_MANIFEST_MISMATCH"; exit 1; fi
echo "[test] authorization token present; frozen manifest verified"
python scripts/innovation/runner.py --test-evaluation --frozen-manifest results/innovation/frozen_model_manifest.json
echo "[test] one-time Test evaluation complete"