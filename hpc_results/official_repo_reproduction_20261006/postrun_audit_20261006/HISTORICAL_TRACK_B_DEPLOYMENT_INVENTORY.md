# HISTORICAL TRACK B — DEPLOYMENT INVENTORY

Generated 2026-10-06 from **read-only** evidence gathered by CPU-only Slurm job 606430.
Classification: `HISTORICAL_TRACK_B_PRE_OFFICIAL_REPOSITORY_DEPLOYMENT`.
**Every directory is `UNSAFE_TO_DELETE`.**

Raw data: `hpc_out/v3_perdir.tsv`, `v3_toplevel.tsv`, `v3_largest_files.tsv`,
`v3_largest_subdirs.tsv`, `v3_timestamps.tsv`, `checkpoint_sha256.tsv`.
Table: `HISTORICAL_TRACK_B_DEPLOYMENT_INVENTORY.csv` (19 rows).

---

## 1. The family at a glance

| Property | Value |
|---|---|
| directories | **19** |
| host path | `/gpfs1/scratch/sychan552/innovation_deploy_root_v3_*` |
| owner / group | `sychan552` / `sychan552` (all 19) |
| total apparent size | **219,722,194,209 bytes = 204.6 GiB** |
| total actual (disk) usage | **219,722,194,209 bytes = 204.6 GiB** — *identical*, because there are **no symlinks and no hard links** |
| total files | **27,019** |
| checkpoint-like files | 594 (447 `.pt` + 147 `.safetensors`) = 201.7 GiB |
| symlinks | **0** |
| broken symlinks | **0** |
| hard-linked files (nlink > 1) | **0** |
| git metadata | **none** — no `.git` in any of the 19 |
| earliest file mtime | **2026-09-16T15:40:54Z** (`v3_1`) |
| latest file mtime | **2026-09-21T04:56:42Z** (`v3_clean14`) |
| share of the account's scratch usage | 204.6 of 443.6 GB ≈ **46 %** |

---

## 2. The decisive provenance fact

```
latest mtime anywhere in the family = 2026-09-21T04:56:42Z
author repo clone                  = 2026-09-24T09:54:29+08:00  (= 2026-09-24T01:54:29Z)
```

**Every directory in the family predates the official repository pull by at least
2 days 21 hours.** The Track-B classification is therefore **filesystem-proven**, not
merely recalled. This is the strongest available evidence for the lineage boundary.

---

## 3. Structure of every directory

All 19 share the same shape — a staged copy of the **self-built** project plus that
build's outputs:

```
<dir>/
  data/          hpc_results/      hpc_scripts/      results/      scripts/
  [tests/]       [docs/]           [MIFlu_innovation_plan_v2.md]   [bundle.zip]
```

`v3_1`–`v3_5` additionally carry `MIFlu_innovation_plan_v2.md` and `tests/`; `v3_2` and
`v3_3` carry a `bundle.zip`. The `v3_clean*` family dropped those and kept
`data/ hpc_results/ hpc_scripts/ results/ scripts/`.

The heavy content is always under `results/` — 52 GiB, 50 GiB, 11 GiB … see §4.

### Run-directory naming inside `results/`

Two patterns appear:

- `results/innovation/runs/national-ili__<model>__none__identity__L<hh>__seed<n>__<UTCstamp>__nogit/checkpoints/best_val_mse.pt`
- `results/v3_clean/implementation/gate_<jobid>/runs/<arm>__<model>__L<hh>__seed<n>__w1/checkpoints/best_val_mse.pt`

The `__nogit` suffix is itself evidence that the builds recorded the absence of a git
identity — consistent with the self-built lineage.

---

## 4. Per-directory table

| Directory | Size | Files | Dirs | CKPT files | CKPT GiB | latest mtime (UTC) |
|---|---:|---:|---:|---:|---:|---|
| `v3_1` | 23 M | 147 | 25 | — | — | 2026-09-16T15:40:54Z |
| `v3_2` | 23 M | 155 | 27 | — | — | 2026-09-16T16:22:18Z |
| `v3_3` | 7.1 G | 302 | 77 | 8 | 7.00 | 2026-09-16T17:16:13Z |
| `v3_4` | 7.1 G | 307 | 77 | 8 | 7.00 | 2026-09-16T21:25:02Z |
| **`v3_5`** | **50 G** | 1,445 | 368 | 56 | **49.00** | 2026-09-17T03:03:24Z |
| `v3_clean1` | 23 M | 145 | 23 | — | — | 2026-09-17T16:16:17Z |
| `v3_clean2` | 24 M | 787 | 24 | — | — | 2026-09-17T16:32:25Z |
| `v3_clean3` | 2.8 G | 895 | 52 | 9 | 2.75 | 2026-09-17T17:05:32Z |
| `v3_clean4` | 9.5 G | 927 | 63 | 16 | 9.45 | 2026-09-17T17:40:40Z |
| `v3_clean5` | 9.6 G | 1,117 | 117 | 16 | 9.45 | 2026-09-18T06:31:59Z |
| **`v3_clean6`** | **52 G** | **5,023** | **1,142** | **221** | **50.49** | 2026-09-18T12:19:39Z |
| `v3_clean7` | 9.6 G | 1,124 | 134 | 16 | 9.45 | 2026-09-18T17:48:07Z |
| `v3_clean8` | 9.6 G | 1,140 | 134 | 32 | 9.50 | 2026-09-18T19:16:27Z |
| `v3_clean9` | 9.6 G | 1,142 | 134 | 32 | 9.50 | 2026-09-18T20:49:59Z |
| `v3_clean10` | 9.6 G | 1,146 | 134 | 32 | 9.50 | 2026-09-18T22:41:39Z |
| `v3_clean11` | 27 M | 818 | 35 | 4 | 0.00 | 2026-09-18T23:00:18Z |
| `v3_clean12` | 11 G | 3,252 | 730 | 48 | 9.54 | 2026-09-19T06:40:47Z |
| `v3_clean13` | 9.7 G | 1,175 | 150 | 48 | 9.54 | 2026-09-19T10:26:25Z |
| **`v3_clean14`** | **11 G** | **5,972** | **1,481** | **48** | **9.54** | 2026-09-21T04:56:42Z |

---

## 5. Models, datasets, seeds, horizons present

| Axis | Values observed in the family |
|---|---|
| models (by path token) | `qwen` 138.07 GiB / 33 files · `miflu` 18.41 / 69 · `calf` 9.02 / 28 · `timecma` 8.96 / 28 · `patchtst` 0.03 / 68 · `itransformer` 0.02 / 68 · `dlinear` ~0 / 68 · `nlinear` ~0 / 72 · (unattributed) 27.20 / 160 |
| horizons | L = 24, 36, 48, 60 (in `__L<hh>__` path fields) |
| seeds | 42, 43, 44, … (in `__seed<n>__` path fields); the `durable_sim` exports show seeds up to 51 |
| arms | `primary`, `ablation`, `negative_control` (e.g. `without_task_instruction`, `without_lora`, `zero_text`) |
| datasets | the family carries a `data/` subtree in every directory; both the author 966-row and the July-2026 1025-row files are referenced across the project, so **the dataset version is NOT uniform across all 19** and must be treated as per-directory |
| checkpoint formats | `.pt` (447, full training checkpoints) and `.safetensors` (147, reduced exports) |

---

## 6. Role labels (assigned conservatively)

| Label | Directories |
|---|---|
| `HISTORICAL_FINAL_DEPLOYMENT_POSSIBLE_DUPLICATE` | `v3_5` (50 G), `v3_clean6` (52 G), `v3_clean14` (11 G) |
| `HISTORICAL_INTERMEDIATE_BUILD` | `v3_1`…`v3_4`, `v3_clean1`…`v3_clean5`, `v3_clean7`…`v3_clean13` |
| `HISTORICAL_CHECKPOINT_REDUCTION_WORKSPACE` | directories containing `durable_sim/…/compact*.safetensors` |
| `HISTORICAL_CACHE_ONLY` | none identified — no directory is cache-only |
| `HISTORICAL_ROLE_UNKNOWN` | `v3_clean11` (27 M, 4 checkpoint files, 0.00 GiB) — near-empty of checkpoints |

**No directory is labelled `HISTORICAL_FINAL_DEPLOYMENT_UNIQUE`**, because establishing
uniqueness would require a full cross-directory content diff, which this round did not
perform at that granularity. See `HISTORICAL_TRACK_B_DEPENDENCY_MAP.md` for what that
would require.

---

## 7. Deletion status

**All 19: `UNSAFE_TO_DELETE`.** Nothing was deleted, moved, renamed, compressed,
truncated or modified by this audit — the only writes were the audit's own outputs under
`postrun_audit_20261006/out/`.

Note the storage consequence: the family is **204.6 GiB of essentially unique content**
(see `HISTORICAL_DEPLOYMENT_STORAGE_ACCOUNTING.md`), so it also cannot be reduced
meaningfully by deduplication. Freeing scratch space would require deleting real runs,
which is **not authorized**.