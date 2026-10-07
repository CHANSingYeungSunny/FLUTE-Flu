# innov-v2.4 — isolated deployment verification

| item | value |
|---|---|
| deployment root | `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.4_5a4c3247` |
| scientific protocol | `innov-v2.0` |
| implementation source | `innov-v2.4` |
| runtime aggregate | `5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d` (77 files) |
| archive | `bc6e8bff6f77c8b5e23634466f8d09b13927dd74198c67194c6befe28c4375ae` (102 members, two builds identical) |
| plan hash | `aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961` |

## Why this file was created

The v2.4 cascade produced the pilot-side reports (`results/innovation/hpc_pilot/…`) but the
deployment-verification directory for v2.4 was never written, unlike v2.2 and v2.3. This file closes
that gap from evidence already collected; no new HPC action was performed and no prior evidence was
modified.

## Verification results

| check | result |
|---|---|
| explicit deployment-root verification | **77/77**, `actual == expected`, exit 0 |
| local extraction verification (explicit temp root) | 77/77, missing/mismatched/unexpected = 0 |
| deterministic bundle | 2 builds, byte-identical |
| runtime path guard | 11 paths checked, **0 violations** |
| strict offline GPT-2 | `gpt2_offline_load=OK` |
| `bash -n` (4 pilots + worker + submit) | 6/6 OK |
| unit tests | 17/17 pass |
| destination pre-existed / silent overwrite | no / no |
| extracted into the original reproduction repository | **no** |

A100 caveat: the cluster A100 evidence is job **556143**, observed under **innov-v2.2**
(`gpu-a100-03`, NVIDIA A100-SXM4-80GB, exactly one GPU). No v2.4 model job has run on an A100.

## Command used for the read-only re-check

```bash
cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.4_5a4c3247
export INNOVATION_DEPLOYMENT_ROOT="$PWD"
python scripts/innovation/verify_source_snapshot.py \
  --deployment-root "$PWD" \
  --manifest results/innovation/source_snapshot_manifest.json \
  --expect 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d
python scripts/innovation/runtime_guard.py --deployment-root "$PWD"
```

## Gate

```text
source_deployment_verified                        = true
pilot_precheck                                    = PASS
pilot_submission_ready                            = true      # infrastructure readiness only
full_sweep_submission_ready                       = false
test_sealed                                       = true
frozen_winner_exists                              = false
pilot_execution_verified                          = false
historical_original_repository_integrity_verified = false
```

No `sbatch` was invoked; the four pilots await a separate explicit authorization.
