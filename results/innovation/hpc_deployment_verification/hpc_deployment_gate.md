# HPC deployment gate (separate from the local `pre_hpc_gate.json`)

Scientific protocol `innov-v2.0` · implementation source `innov-v2.1`
Deployment root: `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.1_dc7ee964`
(resolves to `/gpfs1/scratch/...`)

## Readiness

| Gate | Value |
|---|---|
| `source_deployment_verified` | **true** |
| `hpc_base_environment_verified` | **true** |
| `hpc_a100_allocation_verified` | **false** |
| `pilot_submission_ready` | **false** |
| `full_sweep_submission_ready` | **false** |
| `blocker` | **`UNVERIFIED_HPC_A100_ALLOCATION`** |

## Verified hashes

| Artefact | SHA-256 |
|---|---|
| archive | `c7ff4849c7a2ed9f5576eb1b21ce748fe99915823884ae057fda9600fea1ddb9` |
| runtime file-set aggregate | `dc7ee9649c8d840a0453c9728b417059e5bc86fa7d859f224b5e3a67d43c07b4` |
| `hpc_scripts/hpc_env_check.sh` | `746bdf561ccab21f0e453e67d1949ce97cca9dbce2558ddb4ac7b7d8eb6b632c` |
| authoritative plan | `aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961` |

## Why `pilot_submission_ready=false`

Source deployment is verified (69/69, `explicit_root`, exit 0) and the base
environment + strict-offline GPT-2 load passed, but **no A100 has been observed
inside an allocated job** — the environment check ran on a **login node**
(`LOGIN_NODE_GPU_NOT_EXPECTED`). Per the gate rules this alone keeps pilot
submission blocked.

Second, independent item to close before pilot submission: the pilot-spec
**metadata gap D1** (`experiment_stage`, `test_access_allowed`, `protocol_version`
are absent from `hpc_scripts/pilot_specs.json`). Closing it requires a frozen-source
change → new source cascade → re-deploy.

## Safety

`submission_attempted=false` · `sbatch_invoked=false` · `test_sealed=true` ·
`frozen_winner_exists=false` · `model_ranking_produced=false` ·
`test_access_count=0` · `pilot_runs_executed=0`

**No pilot job was submitted or run. No HPC deployment beyond source
verification is claimed.**
