# v3 environment and weight-access plan

Generated 2026-09-15T20:00:06Z.
No weights downloaded and no model loaded this turn.

## Environment

| Environment | Python | PyTorch | CUDA | Transformers | Cache | Disk GB |
|---|---|---|---|---|---|---|
| `mlflu_v3_core` | 3.10 | 2.5.1 | 11.8 | 4.57.6 | /gpfs1/scratch/sychan552/v3_cache/core | 8 |
| `mlflu_v3_qwen` | 3.11 | 2.2.2 | 11.8 | 4.37.2 | /gpfs1/scratch/sychan552/v3_cache/qwen | 6 |
| `mlflu_v3_crossmodal` | 3.11 | 2.1.2 | 12.1 | repository-pinned compatible release | /gpfs1/scratch/sychan552/v3_cache/crossmodal | 6 |

All future smoke commands use `sbatch` on a compute node; none was executed this turn.

## Weight access

| model_key | source | download | user action | reason |
|---|---|---|---|---|
| `gpt2_miflu` | already cached offline (v2) | no | no | - |
| `calf_llm` | GPT-2 backbone, already cached offline | no | no | - |
| `timecma_llm` | GPT-2 backbone, already cached offline | no | yes | upstream repository licence is NOASSERTION; manual review required |
| `qwen_time_llm` | Qwen/Qwen2.5-1.5B (Hugging Face) | yes | yes | network download onto HPC and licence confirmation |

Total new download: **3.1 GB** (Qwen2.5-1.5B only; GPT-2 is already cached).
