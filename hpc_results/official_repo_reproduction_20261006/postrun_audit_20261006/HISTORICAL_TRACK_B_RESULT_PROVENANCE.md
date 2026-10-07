# HISTORICAL TRACK B — RESULT PROVENANCE

Generated 2026-10-06. Read-only.

## 1. What a Track-B result is

Every number under `results/innovation/**`, `results/v3_clean/**` and inside the 19
`innovation_deploy_root_v3_*` directories was produced by the **self-built** MIFlu
implementation, on a dataset that is **not uniform across the family**, before the author's
repository was pulled (clone 2026-09-24T09:54Z; every directory's latest mtime is <=
2026-09-21T04:56Z).

## 2. Provenance chain of a typical Track-B number

| Stage | Artifact | Present? |
|---|---|---|
| code | `scripts/` inside the directory (self-built) | yes |
| run identity | run dir name encodes arm, model, horizon, seed, UTC stamp, `__nogit` | yes |
| dataset | `data/` inside the directory | yes, but version varies by directory |
| checkpoint | `results/**/checkpoints/best_val_mse.pt` | yes |
| reduced export | `durable_sim/**/compact.safetensors` | yes, for deployment arms |
| **predictions** | `.npy` | **NO - zero .npy files in 27,019 files** |
| **targets** | `.npy` | **NO** |
| metrics | 1,909 `.csv` | yes |
| launch command | — | **NO** - no script, README or CI config |
| git commit | — | **NO** - no `.git` in any of the 19 |

## 3. The decisive limitation

> **Independent re-scoring of any Track-B number is impossible.**
> No predictions or targets were persisted. Only aggregate metrics CSVs exist, and the
> entry-point command that produced them is not recoverable from the artifacts.

Consequences:

1. Track-B metrics can be **quoted** but not **verified** by recomputation.
2. The project's earlier claim that an independent audit re-checked 160 cells at float32
   precision refers to `audit_20260930/` and used prediction `.npz` files from
   **stage5/stage6** — i.e. the **official-repository** lineage, not Track B. That audit
   does **not** cover any Track-B number.
3. Anything in Track B therefore carries a standing `UNVERIFIED_BY_RECOMPUTATION` flag.

## 4. How Track-B results may and may not be used

| Allowed | Not allowed |
|---|---|
| describe the self-built implementation's historical performance | present as author-repository output |
| show the historical deployment existed and what it contained | present as A0-R / A1-P / A2-F |
| quote its metrics with the `UNVERIFIED_BY_RECOMPUTATION` flag | place in a ranking with official-repository numbers |
| use it as a data-vintage landmark | average it with any other track |
| cite it as the *historical* baseline for the thesis narrative | claim the paper was reproduced from it |

## 5. The July-2026 dataset question

The family's `data/` subtrees are not uniform, so some Track-B runs used the 1025-row
July-2026 snapshot and some the 966-row author file. **Because no per-run dataset manifest
was found inside the family, the dataset version for any individual Track-B run is
`UNRECOVERED`** unless the run directory name or a config file states it.

This reinforces rule R5 in `TRACK_SEPARATION_RULES.md`: the July-2026 dataset is an
orthogonal *dataset* axis, and a Track-B × July-2026 cell is a distinct track only if the
dataset version can actually be established for that run.
