# Pilot precheck — innov-v2.4 (no submission)

Deployment root: `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.4_5a4c3247`
Runtime aggregate: `5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d` (77 files)

## Result: PASS (not submitted)

| check | result |
|---|---|
| v2.4 source deployment verified | PASS (77/77, `actual == expected`, exit 0) |
| Pilot/Worker/Submit have no forbidden `cd` | PASS (forbidden string appears only as `FORBIDDEN_ROOT_RAW`) |
| explicit deployment root enforced | PASS (`${INNOVATION_DEPLOYMENT_ROOT:?…}`, no `$(pwd)` fallback) |
| source hash matches | PASS |
| runtime guard passes | PASS (11 paths, 0 violations) |
| strict offline GPT-2 | PASS (`gpt2_offline_load=OK`) |
| pilot specs exactly four | PASS (`gpt2_miflu`, `dlinear`, `patchtst`, `itransformer`) |
| five-layer metadata chain complete | PASS |
| four pilots selection / paper-result / test ineligible | PASS (all false) |
| submit references only the four pilots | PASS |
| dependency is `afterok`, not `afterany` | PASS |
| fail-stop verified | PASS (fake sbatch/sacct: success → 4, failed predecessor → 1) |
| test seal valid | PASS |
| frozen winner absent | PASS |
| full sweep still blocked | PASS (`full_sweep_submission_ready=false`) |

Unit tests: **17/17** pass.

## Fail-closed dry runs (no submission in either case)

```text
INNOVATION_DEPLOYMENT_ROOT unset            -> exit 1, "… must be set to the isolated deployment root", 0 jobs
CONFIRM_INNOVATION_SUBMIT unset             -> exit 0, "submission_attempted=false", 0 jobs
```

## Gate

```text
pilot_precheck                                   = PASS
pilot_submission_ready                           = true       # infrastructure readiness only
full_sweep_submission_ready                      = false
test_sealed                                      = true
frozen_winner_exists                             = false
historical_original_repository_integrity_verified = false
pilot_execution_verified                         = false      # no pilot has run yet
```

`pilot_submission_ready = true` reflects **infrastructure readiness only**. No pilot was submitted
and no `sbatch` was invoked in this turn; submission requires the separate explicit authorization.

## Next authorization command (not executed)

```bash
cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.4_5a4c3247
export INNOVATION_DEPLOYMENT_ROOT="$PWD"
CONFIRM_INNOVATION_SUBMIT=YES sbatch hpc_scripts/submit_innovation_pilot.sh
```
