# A100 allocation environment check — result (job 556143)

Implementation source `innov-v2.2` · scientific protocol `innov-v2.0`
Authorization: **exactly one no-training A100 environment check**. Pilots, screening, full sweep, ablations, test
evaluation and any training job remain **unauthorized and unsubmitted**.

## Command

```bash
cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.2_06b83e18
CONFIRM_INNOVATION_SUBMIT=YES sbatch hpc_scripts/gpu_allocation_env_check.sh
```

| field | value |
|---|---|
| Slurm job ID | **556143** |
| state / exit code | **COMPLETED / 0:0** |
| elapsed | 00:00:49 (limit 00:15:00) |
| partition | stingy |
| node | **gpu-a100-03** |
| requested TRES | `cpu=2,mem=8G,node=1,billing=15,gres/gpu=1,gres/gpu:a100=1` |
| allocated TRES | `cpu=2,mem=8G,node=1,billing=15,gres/gpu=1,gres/gpu:a100=1` |
| `CUDA_VISIBLE_DEVICES` | `0` |

## GPU / CUDA facts

| field | value |
|---|---|
| `torch.cuda.is_available()` | **true** |
| `torch.cuda.device_count()` | **1** |
| GPU name | **NVIDIA A100-SXM4-80GB** |
| total memory | 85 093 777 408 B (81 920 MiB) |
| compute capability | 8.0 |
| torch / CUDA runtime | 2.5.1 / 11.8 |
| cuDNN | 90100 |
| driver / CUDA (nvidia-smi) | 580.167.08 / 13.0 |
| tiny allocation probe | ok |
| exactly one A100 | **true** |
| strict offline GPT-2 load | **OK** |

## Runtime source verification (inside the job)

`verification_mode=explicit_root`, **70/70** files,
`actual_aggregate_sha256 == expected == 06b83e18e4bb66d69ae457087fa5024bb4a50884bca3c080ca51af35de575e86`,
exit 0. Plan hash `aa4ab1c8842e…9e7961` matches. Script SHA-256 identical locally and on HPC
(`85703d5d692844996e548ceb98cc303ebc76ba97a0a29331f1501d81664d9721`).

## No side effects

`training_performed=false`, `data_loaded=false`; no run directory, no `registry.csv` row, no checkpoint,
prediction, metric or figure, no frozen winner, no nested `sbatch`. The only files created are the JSON report
and the two Slurm logs. Local `registry.csv` (14 rows) and `results/innovation/runs` (14 dirs) are unchanged.

## Gate

```
a100_environment_check_verified = true
hpc_a100_allocation_verified    = true
pilot_submission_ready          = false
full_sweep_submission_ready     = false
blocker                         = RUNTIME_METADATA_CHAIN_INCOMPLETE
secondary_blocker               = ORIGINAL_REPRO_REPOSITORY_INTEGRITY_NOT_FULLY_VERIFIED
test_sealed                     = true
frozen_winner_exists            = false
original_reproduction_repository_integrity_verified = false   # compute_miflu_indicators.py UNRESOLVED
```

The A100 check clears only the allocation blocker. Pilot submission stays blocked by the runtime metadata chain
and by the unresolved reproduction-repository file.
