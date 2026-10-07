# Failed runs resolution (pre-HPC)

- `repository_head`: `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` (short `1f6563f`)
- `working_tree_dirty`: `True`
- `fix_commit`: **null** (the repair is uncommitted)
- `fix_identifier`: `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9`
- `fix_files`: `scripts/innovation/runner.py`
- `fix_files_aggregate_sha256`: `2cc28336f85e7841bf1f5203b90529da340bc5046e673f24c53c82bd380e7136`
- `timestamp_utc`: `2026-09-14T21:01:34Z`

## Per-file SHA-256

| `scripts/innovation/runner.py` | `03b4b6584d4301fcf6799bfb5c89ebe57400a537f7d47e000d7ad8f063594829` |

## The 5 failed registry entries

| failed run_id | root cause | fix_identifier | replacement run_id | resolution |
|---|---|---|---|---|
| `national-ili__dlinear__none__identity__L24__seed42__20260914T110544Z__1f6563f` | TypeError: __init__() got an unexpected keyword argument 'device' | `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9` | `national-ili__dlinear__none__identity__L24__seed42__20260914T181420Z__1f6563f` | **resolved** |
| `national-ili__nlinear__none__identity__L24__seed42__20260914T110553Z__1f6563f` | TypeError: __init__() got an unexpected keyword argument 'device' | `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9` | `national-ili__nlinear__none__identity__L24__seed42__20260914T110634Z__1f6563f` | **resolved** |
| `national-ili__patchtst__none__identity__L24__seed42__20260914T110553Z__1f6563f` | TypeError: __init__() got an unexpected keyword argument 'device' | `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9` | `national-ili__patchtst__none__identity__L24__seed42__20260914T110637Z__1f6563f` | **resolved** |
| `national-ili__itransformer__none__identity__L24__seed42__20260914T110553Z__1f6563f` | TypeError: __init__() got an unexpected keyword argument 'device' | `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9` | `national-ili__itransformer__none__identity__L24__seed42__20260914T110641Z__1f6563f` | **resolved** |
| `national-ili__fusion-forecaster__tfidf-svd__concat-projection__L24__seed42__20260914T110554Z__1f6563f` | RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu! (when checking argument for argument mat2 in method wrapper_CUDA_mm) | `working-tree@1f6563f+innovation-pkg:a8ec1a4f9db9` | `national-ili__fusion-forecaster__tfidf-svd__concat-projection__L24__seed42__20260914T110644Z__1f6563f` | **resolved** |

## Eligibility of failed runs

All 5 failed runs are recorded in the registry with `status=failed`; they carry `selection_eligible=false` (or no eligibility fields at all) and are therefore **ineligible for model selection** by construction (`select_best_model.py` eligibility gate). 5/5 have a successful same-spec replacement.
