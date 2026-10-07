# Reproduce — innovation infrastructure (round 1)

Everything in this round runs locally on CPU/GPU with **no downloads**.

## One command

```bash
bash scripts/innovation/reproduce.sh
```

Windows PowerShell equivalent:

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/innovation/audit_repo.py
python tests/innovation/test_run_id.py
python tests/innovation/test_no_overwrite.py
python tests/innovation/test_checkpoint_resume.py
python tests/innovation/test_test_gate.py
python tests/innovation/test_peak_criteria.py
python tests/innovation/test_backbone_shapes.py
python tests/innovation/test_architecture_equivalence.py
python tests/innovation/test_numeric_regression.py
python scripts/innovation/smoke.py
python scripts/innovation/select_best_model.py
python scripts/innovation/hpc_specs.py
```

## Single ad-hoc run

```bash
python scripts/innovation/runner.py \
    --model patchtst --text-encoder none --fusion identity \
    --horizon 24 --seed 42 --epochs 20
```

Add `--skip-if-done` for resumable HPC workers and `--max-seconds N` for a
wall-clock timeout.

## HPC (generated, NOT submitted)

```bash
# inspect first
ls hpc_scripts/submit_innovation_*.sh
# when you decide to run a sweep (respects stingy's 1-slot QOS cap):
sbatch hpc_scripts/submit_innovation_screening.sh
```

`hpc_scripts/innovation_worker.sh` runs ONE spec per job, resumable, with a
4h cap, `--mem=16G`, preemption handling and `--max-seconds` timeout.

## Artifact locations

```
results/innovation/
  audit/                      audit.md, plan_compliance_matrix.md, early_stopping_audit.md,
                              peak_criteria_spec.md, plan_sha256.json, environment.txt,
                              dependency_probe.json, prompt_variation_report.json
  registry.csv                append-only run index
  runs/{run_id}/              create-only per-run artifact tree
  test_evaluations/{id}/      ONLY after a winner is frozen (empty this round)
  model_selection_audit.json  validation-only selection record
```
