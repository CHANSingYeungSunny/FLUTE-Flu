# v3.10 artifact-directory failure audit (Gate 569016)

**Executable status: `SUPERSEDED_FOR_EXECUTION_ARTIFACT_DIRECTORY_INITIALIZATION_FAILURE`**
(superseded by `innov-v3.11-artifact-directory-initialization`)

## Gate 569016

| field | value |
|---|---|
| state | FAILED |
| exit code | 1:0 |
| elapsed | 00:24:33 |
| node | gpu-a100-06 |
| passed | 1/19 |
| runtime paths failed | 18 |

## Observed

- **16 stochastic paths** failed at `logs/train_history.csv`
- **2 baseline paths** failed at `predictions/validation_predictions.csv`
- training **completed** for the stochastic paths
- the **best checkpoint existed** for the stochastic paths
- the **four metric artifacts existed** for the baseline paths
- formal rows submitted = **0/598**, Test access = **0**, holdout access = **0**
- **scientific protocol changed = false**

## Confirmed working (earlier repairs)

D8 import path, D9 backbone kwarg, D10 Gate run-key — all **verified** in this run.

## Root cause

`clean_runner.py` never created the per-run artifact sub-directories. The
training arms hit `logs/` first (line 330); the checkpoint-free baselines hit
`predictions/` first (line 263). `metrics/` and `checkpoints/` existed only
because `_atomic_write_json` creates the parent of the file it writes.

> Gate outputs are **infrastructure diagnostics only** — they are **never**
> scientific results and never enter any ranking.
