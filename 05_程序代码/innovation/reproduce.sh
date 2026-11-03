#!/usr/bin/env bash
# ============================================================================
# One-command reproduction of the innovation infrastructure + pre-HPC checks.
#   usage:  bash scripts/innovation/reproduce.sh
# (Windows PowerShell equivalent: see results/innovation/REPRODUCE.md)
#
# Order matters: the HPC scripts are generated first, the source snapshot is
# frozen second, and only then do the tests run — so the snapshot-integrity test
# always sees a current manifest.
#
# Smoke runs validate the PIPELINE ONLY. They produce NO performance ranking
# and NO paper conclusion. NOTHING is submitted; the test set stays sealed.
# ============================================================================
set -euo pipefail
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")/../.."

echo "== 1. compile =="
python -m compileall scripts/innovation -q

echo "== 2. audit (runtime plan SHA-256, dependency probe, prompt variation) =="
python scripts/innovation/audit_repo.py

echo "== 3. generate HPC scripts incl. pilot (generated, NOT submitted) =="
python scripts/innovation/hpc_specs.py

echo "== 4. freeze the source snapshot (immutable, content-addressed) =="
python scripts/innovation/source_snapshot.py

echo "== 5. verify the snapshot against the working tree (must pass) =="
python scripts/innovation/verify_source_snapshot.py

echo "== 6. unit tests =="
for t in test_run_id test_no_overwrite test_checkpoint_resume test_test_gate \
         test_peak_criteria test_backbone_shapes test_architecture_equivalence \
         test_aggregation_regression test_pipeline_regression_endtoend \
         test_gpt2_control_repro test_eligibility_gate \
         test_pilot_spec_metadata test_metadata_chain \
         test_runtime_path_guard test_canonical_indicator \
         test_source_snapshot_gate; do
  python "tests/innovation/${t}.py"
done

echo "== 7. smoke (8 representative combos; NOT for ranking) =="
python scripts/innovation/smoke.py

echo "== 8. validation-only champion selection (must not read test) =="
python scripts/innovation/select_best_model.py

echo "== 9. Slurm structural + bash -n validation (never submits) =="
python scripts/innovation/slurm_check.py

echo "== 10. pre-HPC gate + human review checklist (never submits) =="
python scripts/innovation/prehpc_report.py

echo "ALL DONE"
