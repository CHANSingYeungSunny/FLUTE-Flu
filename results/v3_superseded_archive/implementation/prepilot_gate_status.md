# Pre-Pilot Gate status

Generated 2026-09-16T15:48:10Z.

**Outcome: FAILED.** No Pilot was submitted.

| # | Job | Node | State | Exit | Elapsed | Models OK | Assets |
|---|---|---|---|---|---|---|---|
| 1 | 563486 | gpu-a100-05 | FAILED | 1:0 | 00:01:04 | 0/8 | False |
| 2 | 563498 | gpu-a100-05 | FAILED | 1:0 | 00:02:33 | 0/8 | True |
| 3 | 565800 | gpu-a100-03 | FAILED | 1:0 | 00:01:12 | 5/8 | True |

## Acceptance criteria

| Criterion | Result |
|---|---|
| slurm_state_COMPLETED | False |
| exit_code_0_0 | False |
| partition_stingy | True |
| allocated_gpu_a100_1 | True |
| source_files_verified_85_of_85 | True |
| source_aggregate_matches | True |
| runtime_guard_violations | 0 |
| canonical_data_sha256_matches | True |
| test_access_count | 0 |
| holdout_access_count | 0 |
| formal_pilot_jobs_submitted_before_gate | 0 |
| cuda_visible_and_usable | True |
| all_eight_models_built_with_gradients | False |

## What passed

- `HPC_GUIDE.md` hash unchanged; full text read before any HPC action.
- Isolated deployment root verified: 85/85 files, aggregate `6d6d37a75e0dd7a6137a194a8d12347d207fa4a013eb5b65136068bc2f358544`, exit 0.
- `runtime_guard`: 0 violations; no runtime import from the original repository.
- Canonical data SHA-256 matches; Test and holdout access counts are 0.
- Qwen pinned revision downloaded: 7 files, 3,098,955,511 bytes, revision `8faed761d45a263340a0528343f099c05c9a4323`.
- On gpu-a100-03, CUDA works and five models build with a verified backward pass, including gpt2_miflu (82,136,232 total / 1,030,056 trainable params, 45 grads, forward shape [2, 7, 24]).

## What failed

- **D1 (fixed)**: Time-LLM repository commit had been used as the Qwen revision; corrected to `8faed761d45a263340a0528343f099c05c9a4323`.
- **D2 (resolved operationally)**: gpu-a100-05 rejected every CUDA allocation; excluding that node fixed it, so no project code change was needed.
- **D3 (fixed)**: unsupported `model_id` is no longer passed to the GPT-2 adapter.
- **D4 (partially open)**: the assets are downloaded and correct, but `from_pretrained` does not resolve them from the hub cache on the compute node and falls back to a network lookup.

## Retries

Three Gate runs were used (563486, 563498, 565800). This prompt permitted one further retry beyond 563498; it was spent on 565800. No further Gate retry is permitted here.

## Next step

Repair the asset-resolution plumbing in the text-backbone loader (pass the pinned revision or the local snapshot path, or set `local_files_only=True`), then perform a fresh Gate run. Pilots may only be submitted after that Gate passes.
