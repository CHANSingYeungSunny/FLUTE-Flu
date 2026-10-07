# HPC CLEANUP — RECLAIMED SPACE

Date: 2026-10-07 (HKT). Host: CityUHK Burgundy (`hpclogin02`).
Authorisation: continuous-execution authorisation, sections 5–8.

## Headline

| | before | after | change |
|---|---:|---:|---:|
| **scratch used** | **414 GB** | **285 GB** | **−129 GB** |
| scratch soft quota | 300 GB | 300 GB | — |
| scratch **grace** | **expired** | **none** | **violation cleared** |
| home used | 30 GB | 30 GB | 0 |

`mmlsquota` after cleanup:

```
Filesystem type   GB   quota   limit  grace
home       USR    30      50     100  none
scratch    USR   285     300    1024  none
```

## What was removed

**359 full checkpoints, 128.82 GiB** — every one a `best_val_mse.pt` from a
superseded `innovation_deploy_root_*`, removed only after nine independent
guards passed for that exact file:

1. its root is a superseded deploy root (the active root `clean14` was excluded outright);
2. a durable copy of the same run exists under `innovation_durable/`;
3. that copy's `compact_manifest.json` reports `reconstruction_exact: true`;
4. … reports `n_keys_unequal: 0`;
5. … reports empty `missing_keys`;
6. … reports empty `unexpected_keys`;
7. … holds `predictions/validation_predictions.csv`;
8. … holds all four metric JSON files;
9. the durable `compact.safetensors` **sha256 matches the manifest**, and the
   file's size equals the manifest's recorded `source_bytes`.

Guard 9 is the load-bearing one: it binds the durable artefact to the very run
being deleted, so a name collision cannot cause a wrong deletion.

Full per-file record: `HPC_CLEANUP_EXECUTED.csv` (654 rows — 359 `delete`,
294 `retain`, one row per file with its guard outcome).

## What was deliberately NOT removed

| item | size | why retained |
|---|---:|---|
| `CHATTIME/.ollama/models` | 77 G | no active script references it, but exact re-pull not verified — `PROTECTED_UNCERTAIN` |
| `innovation_deploy_root_v3_5` full `.pt` | 50 G | 56 checkpoints with **no durable manifest match** |
| `CHATTIME/.cache` | 27 G | regenerable in principle; retained because it is not provably unused |
| `innovation_deploy_root_v3_3` / `v3_4` | 7.1 G each | full `.pt` not matched to a durable manifest |
| `innovation_deploy_root_v2_8` | 4.2 G | 218 `.pt` from the pre-v3 track; no durable manifest |
| `v3_cache` | 3.4 G | HF cache; network reachable but held for the historical-replacement run |
| `a2_stage5` (scratch) | 7.9 G | durable archive exists at `home/stage5_a2_durable`, but byte-identity not yet re-proven this pass |
| `a0_replay` | 0.4 G | **the running R1-B pilot reads its dataset and text embeddings from here** |

**294 full checkpoints (67.32 GiB) failed at least one guard and were kept.**
They are recorded as `PROTECTED_UNCERTAIN`, not deleted.

## Method — no blanket deletion

No `rm -rf $HOME/*`, no `rm -rf $SCRATCH/*`, no `find … -delete`.
Every removal was a single explicit `os.remove(path)` over the exact path list
in `HPC_CLEANUP_PLAN.csv`, re-validated at delete time by
`execute_checkpoint_cleanup.py`. The classifier, the plan and the execution
record are all retained so the whole action is replayable.

## Integrity of what remains

The durable copies that justify each deletion carry their own sha256
(`compact_sha256`) recorded in the executed CSV, and those manifests assert
`reconstruction_exact: true` against a source tensor set that excludes no
unexpected keys. The `gpt2` base snapshot the reconstruction needs is present
in the pinned cache and was **not** touched.

## Post-cleanup capacity

Free against the soft quota: **≈15 GB**, plus 724 GB of headroom to the hard
limit. The R1-B locked-checkpoint path needs **16.6 MiB per fit** and the
historical 1025-row replacement is projected in single-digit GB; both fit
comfortably. No further cleanup is required to proceed.