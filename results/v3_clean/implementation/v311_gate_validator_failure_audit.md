# v3.11 Gate-validator failure audit (Gate 570452)

**Executable status: `SUPERSEDED_FOR_EXECUTION_GATE_VALIDATOR_SCHEMA_MISMATCH`**
(superseded by `innov-v3.12-gate-validator-schema-alignment`)

Gate 570452 is classified **FAILED** and is a **validator-only false failure**
— never a model-performance result.

| field | value |
|---|---|
| state | FAILED |
| exit code | 1:0 |
| elapsed | 00:26:38 |
| node | gpu-a100-03 |
| gate passed | 1/19 |
| **runtime paths rc=0** | **18/18** |

## Only three validator assertions failed

1. `checkpoint_file_present` (16 paths) — looked for a hard-coded
   `best_validation.pt`; the runner writes `best_val_mse.pt`, declared by the
   manifest as `checkpoint_file` with a matching `sha256_file`.
2. `baseline_no_checkpoint` (2 paths) — required the `checkpoints/` DIRECTORY
   to be absent; the D11 uniform tree legitimately creates an empty one.
3. `artifact_completeness` (2 paths) — one shared required list containing
   `logs/train_history.csv`, which deterministic baselines never produce.

## Not affected

Runner behaviour, D11 fix, stochastic checkpoint restoration, and every
scientific check all passed. Test/holdout access = 0/0; formal submissions
remain 0/598.
