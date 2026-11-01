# STORAGE PLAN — capacity, what may be deleted, and how to reproduce a deleted model

**What this is.** The measured capacity facts for CityU HPC Burgundy as they affect this
project, the deletion policy the user authorised on 2026-11-02 00:24, the list of
**never-delete** artefacts, and the record format that lets a deleted LLM checkpoint be
re-downloaded bit-for-bit later.

**When to read it.** Before deleting anything on the cluster; before planning a large run
(rolling origin, 14 LLM arms, regional Table VI); when a job dies with `No space left` or
`Disk quota exceeded`; and whenever you need to prove which model revision produced a row.

**What it points to.** `docs/HPC_RUNBOOK.md` (paths, partitions, gotchas),
`docs/LLM_ARMS.md` (§6 roster and environments), `docs/QUEUE_ROWS_PART2.md` (cost tables),
`weights_manifest_A.json` / `weights_manifest_B.json` (the reproduction record).

**Depends on.** Nothing; it is a facts file. Numbers below were measured, not estimated.

---

## 1. MEASURED CAPACITY (2026-11-02 00:24, `df -h`)

```
home     : 140T total /  41T used / 100T avail   29%   (/gpfs1/home)
scratch  : 2.0P total / 1.2P used / 766T avail   61%   (/gpfs1/scratch)
```

`df` reports the **filesystem**, not a per-user quota. If a **1024 GiB scratch** quota
applies, current usage is far under it:

| Path | Used | Notes |
|---|---|---|
| `scratch/hf_cache` | **145 G** | all downloaded LLM weights (was 48 G at 23:40, growing ~2.3 GB/min) |
| `scratch/mlflu_weights` | 17 M | `weights_manifest_*.json` |
| `home/.../author_runs` | 8.4 G | MIFlu npz + checkpoints + verify markers |
| `home/.../analysis` | 19 M | scripts + `paper_tables` copies + figures |

## 2. TOTAL REQUIREMENT FOR THE WHOLE PROGRAMME

| Item | Estimated size |
|---|---|
| 13 LLM checkpoints (full weights) | **≈ 210 GB** |
| MIFlu 40 checkpoints (≈7 MB each) | ≈ 0.3 GB |
| reproduction + benchmark npz (244 cells × ≈1 MB) | ≈ 0.3 GB |
| Table VI regional cells (21) | ≈ 0.05 GB |
| rolling origin: 200 MIFlu + 960 arm cells, npz | ≈ 1.2 GB |
| rolling origin: intermediate checkpoints | ≈ 15 GB |
| **TOTAL** | **≈ 230 GB** |

**230 GB is under a quarter of a 1024 GiB quota.** Capacity is therefore **not** the
constraint on this project; **A100-hours are**. Consequence: do not spend effort on
aggressive deletion; spend it on scheduling.

## 3. DELETION POLICY (user-authorised 2026-11-02 00:24 — "as aggressive as you like,
except the latest reproduction and the latest benchmark")

### MAY be deleted, on these conditions only
| Target | Precondition |
|---|---|
| an LLM checkpoint under `hf_cache` | that arm's **12 cells are all `DONE`** and are already in `paper_tables/`; the manifest row is `OK` and its `revision` sha is recorded |
| intermediate rolloing-origin checkpoints | that fold's npz have been written |
| `ckpt_best_repro/` originals | the retrained replacement has passed the per-seed oracle gate (≤1e-5) |
| `_seedruns/` raw output | a summary line is kept in the log |
| V100-era npz | the frozen CSV copies (`BENCH_*.post_evalwindow16_v100nlinear.csv`) exist |
| superseded `/tmp/slurm_script` style scratch and `_probe/` cells | always safe — they are `probe_only` and enter no table |

### NEVER delete — these are the paper's ground truth
```
hpc_results/expanded_runs/**/pred_*.npz     # ground truth of every table and figure
author_runs/L*_all7/*.npz                   # MIFlu 7-variable predictions
author_runs/L*_all7/manifest_miflu_*.json   # sha256 provenance per cell
author_runs/.miflu_verify/                  # the 18→40 verification markers
paper_tables/*.csv                          # frozen baselines
docs/*.md                                   # the project's memory
```
**All npz together are < 2 GB but they are the only thing every number can be re-derived
from. Deleting them destroys the paper; deleting a 30 GB checkpoint costs one re-download.**

## 4. REPRODUCTION RECORD — so a deleted checkpoint can be fetched again exactly

`weights_manifest_A.json` / `weights_manifest_B.json` already carry, per model:
`model_id`, `revision` (pinned commit sha), `size_bytes`, `config_sha256`,
hidden-state probe verdict (`OK` / `UNSUPPORTED` + reason), and the HF source.

Before deleting any checkpoint, confirm the row exists and is `OK`, then append one line to
`scratch/mlflu_weights/DELETED_MODELS.tsv`:

```
model_id <TAB> revision_sha <TAB> size_bytes <TAB> source(HF) <TAB> arms_cells_done <TAB> deleted_on_utc
```

Replication is then `snapshot_download(repo_id=<model_id>, revision=<revision_sha>)` — a
pinned sha, so the bytes match the ones the published numbers were produced with. **A
model may never be deleted before its revision sha is recorded**, or the row becomes
irreproducible.

## 5. ROLLING ORIGIN — the one place storage must be planned deliberately

| Item | Rule |
|---|---|
| checkpoints | write **only** to `scratch`, never to `home` (home may be a 100 GiB quota) |
| npz | keep — ≈1.2 GB for the whole 5-fold programme |
| delete | intermediate optimiser state after a fold's npz are written |
| order | Table VI first (≈1 A100-h for a complete table), then LLM arms, rolling origin **last** (120–270 A100-h for MIFlu alone; 35–90 A100-h for the 16 arms) |

## 6. PRIORITY ORDER FOR SPENDING THE NEXT GPU HOURS (value per A100-hour)

1. **Table VI regional, MIFlu only** — 21 cells ≈ **1 A100-h** for a complete new table.
2. **LLM arms whose manifest row is `OK`** — 12 cells each; encoder prompts are cached, so
   cost is per-prompt, not per-cell (≈5,551 prompts per arm).
3. **Table VIII ablations** — `no_lora` 12 cells ≈ 1–1.6 h; K-sweep 48 ≈ 3–6 h.
   Caveat: `--no-text` is **bit-identical** to the full arm (text sits behind the causal
   mask), so that row is a **structural verification only**, not an ablation effect.
4. **Rolling origin** — last; 120–270 A100-h for MIFlu's 200 cells, 35–90 A100-h for the
   960 arm cells. A 1-seed pass is EXPLORATORY under `AGENTS.md` rule 9, not a table row.
5. **Table IX** — produces nothing until Table VI cells exist.
