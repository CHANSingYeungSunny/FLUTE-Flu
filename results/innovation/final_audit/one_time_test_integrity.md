# One-time Test single-use integrity

**Result: PASSED**

| Requirement | Value | Required |
|---|---|---|
| `receipt_count` | `1` | `1` |
| `test_eval_id_count` | `1` | `1` |
| `declared_access_count` | `1` | `1` |
| `immutable_test_manifest_count` | `1` | `1` |
| `champion_model_key` | `'nlinear'` | `'nlinear'` |
| `champion_cells` | `40` | `40` |
| `baseline_cells` | `12` | `12` |
| `total_valid_cells` | `52` | `52` |
| `missing_cells` | `0` | `0` |
| `duplicate_cells` | `0` | `0` |
| `checkpoint_hash_failures` | `0` | `0` |
| `post_test_reselection_count` | `0` | `0` |

## Evidence

- Receipt created `2026-09-15T14:57:10Z`, manifest created `2026-09-15T14:57:10Z`; receipt precedes/equals manifest: **True**
- Receipt and manifest carry the same `test_eval_id`: **True**
- Receipt frozen-model hash matches manifest: **True**
- Selection audit `test_accessed` = **False**; freeze audit passed = **True**
- Stage-F cohort: 160 cells, complete = **True**
- `sacct` contains **no** Test job: the Test never ran as a Slurm job; the only executions were the (prohibited) login-node `nohup` process and the compliant `sbatch` resume 560659, both reusing the same receipt.
- Resumes reused the same receipt, manifest and evaluation ID; completed cells were skipped by create-only logic and were not rewritten.
