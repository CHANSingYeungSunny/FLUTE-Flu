# RETURN SUMMARY — Track-B execution (patched v2 chain)

**Capture UTC:** 2026-11-04T15:35:00Z (HKT 2026-11-04 23:35). This replaces the 09:14 UTC snapshot,
which is stale. Read `SCHEDULER_FIX.md` for the defects that were found and repaired.

> **Scope of the validator:** `validate_return.py` checks structure, hashes and
> limited status consistency ONLY. A PASS is not scientific validation, not
> evidence of correct statistics, and not publication readiness.
> `scientific_readiness` is `NOT_ASSESSED`.
>
> **This is a snapshot.** Cell counts increased from 117 to 139 within
> 12 minutes. See `LIVE_STATUS_DRIFT.md` before quoting any number.

## 1. Status counts (planned denominator)

| Phase | Planned | Completed (validated) | Queued / running | Failed | Skipped | Blocked | Not executed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Track B core panel (4 arms x 4 L x 10 seeds) | 160 | **160** | 0 | 0 | 0 | 0 | 0 |
| Track B national 28-arm matrix | 1120 | **117** | 1003 | 0 | 0 | 0 | 0 |
| Track C rolling origins / regions | not frozen | 0 | 0 | 0 | 0 | 0 | not executed |
| Legacy Table VI regional queue | 70 rows | 41 DONE | 9 TODO | 0 | 19 SKIPPED | - | 1 stale RUNNING |
| Legacy walk-forward queue | 1040 rows | 632 DONE | 170 TODO | 0 | 238 SKIPPED | - | - |
| Legacy Table VIII ablation | 60 | 60 DONE | 0 | 0 | 0 | - | - |

`RUN_LEDGER.csv` covers the 1120 national rows. Core-panel cells are a separate,
partly overlapping panel (MIFlu/NLinear/PatchTST/DLinear); 40 DLinear cells are
extra controls outside the 28-arm denominator. **Core and national panels contain
duplicate runs of the same (model,L,seed) configurations — do NOT pool them as
independent replicates.** See `HPC_VALIDATED_CELLS.tsv`.

## 2. New common ten-seed matrix: submitted, NOT finished

- **Submitted.** Real job IDs: first submission 734673/734674/734675/734676 (cancelled),
  second 734749/734750/734751 (cancelled), final patched v2 lanes
  **735300/735301/735313**, controller
  **735298**, post-all adapter **735299**, core controller
  **735297**.
- At capture: 2 lanes `PENDING (Priority)` on `gpu_a100`, 1 `PENDING` on `stingy`,
  controller and post-all `RUNNING` on `tiny`. No 0-second churn jobs remain.
- **117/1120 cells have validated outputs.** Real per-run metrics are in
  `RUN_METRICS.csv` (1,886 rows) and raw artefacts in `RAW_EVIDENCE/cells/`.
- **Measured cost:** pilot job 734051 on V100 = 748 s (20 epochs, 37.3 s/epoch,
  0.71 GB). Core MIFlu cells on A100 ≈ 8.5 min/cell from lane timestamps.
  The 1120 campaign has no complete measured cost; no A100-hour figure is invented.
  Remaining time cannot be estimated reliably because it is dominated by queue
  wait on a 6-node `gpu_a100` partition.

## 3. Reuse vs rerun

- Old 42/43/44 three-seed benchmark: **separate historical panel**, NOT a subset of
  2021-2030. Must not be pooled into a ten-seed estimate.
- Old 40 ten-seed MIFlu reproduction runs: reusable only after log/weight/prediction/
  config provenance matching; **not verified**.
- Core-panel and national-panel duplicates: each row is a distinct run; mark reuse
  explicitly if one is substituted for the other.

## 4. Old snapshot vs new results (do not force new numbers to old values)

| Item | Old snapshot | Current status |
|---|---|---|
| Holm | 0/136 rejections, min adj p≈0.0664, NLinear–PatchTST 0.1172 | old-snapshot fact; **not** recomputed for new runs |
| Peak / PTE-PIE | MIFlu L24 s2021 step0 PTE 0.0 / PIE 18.80 | partial step-level table in `AGGREGATION/TRACKB_PEAK_PARTIAL.csv`; event-level detection not done |
| no-text | 3 passed / 0 skipped (fixed-weight eval, CPU, GPT-2 cached) | does NOT establish gradient/LoRA reachability during training |
| Ablation | 27/60 user snapshot vs 60/60 public README | queue shows 60/60 DONE with per-cell manifests; 7-variable aggregate trend not recomputed |
| Regional / rolling | Table VI 41 DONE / 9 TODO; WF 632 DONE / 170 TODO | legacy chain is STOPPED; `post_all_v2.sh` hands off after `all/phase.done` |
| MSE order | MIFlu < PatchTST < NLinear; PIE inverted at both ends | old-snapshot fact, not an independence claim |

## 5. Two ZIPs and the exact next command

- `RETURN_TO_CHATGPT.zip` — this consolidated tree **excluding** `RAW_EVIDENCE/`.
- `RAW_EVIDENCE.zip` — the `RAW_EVIDENCE/` subtree with identical relative paths.
  **Extract both into one directory** to recreate the consolidated tree; until then
  raw integrity validation cannot pass.

```
ssh sychan552@burgundy.hpc.cityu.edu.hk 'squeue -u sychan552; \
  /gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python \
  /gpfs1/scratch/sychan552/trackB_20261104/cellok.py count \
  /gpfs1/scratch/sychan552/trackB_20261104/all/export \
  /gpfs1/scratch/sychan552/trackB_20261104/all/cells_all.tsv'
```
Then re-run `make_return_manifest.py` / `validate_return.py` after any new cells land.

## 6. Unverified items and their effect on submission claims

See `UNVERIFIED_ITEMS.md`. In short: the original paper PDF and pinned official
commit were not opened; current IEEE JBHI author guidance/fees/AI disclosure were
not read from the official page; Chronos/TimesFM controls, >=3 eligible rolling
origins and >=3 compatible regions, CDC calendar/vintage and event-level peak
detection were not executed. `PROTOCOL_LOCK.json` is **not frozen** although the
matrix was already submitted — recorded as a deviation, not back-dated.
Consequently: no claim of prospective pre-registration, no claim of real-time or
clinical deployment validation, no claim of equivalence from non-significance,
and no promise of acceptance.

## Tool runs (protocol Z)

`make_return_manifest.py` and `validate_return.py` were both run against the consolidated tree. Full outputs and exit codes are in `logs/return_tool_runs.log`.

- `make_return_manifest.py . --exclude VALIDATION_RESULT.json` → **896 files hashed, exit 0**
- `validate_return.py . --out VALIDATION_RESULT.json` → **integrity_status PASS, errors [], exit 0**, `scientific_readiness: NOT_ASSESSED`

**Scope:** these tools validate return structure, hashes and limited status consistency only. They do not validate scientific assumptions, model equivalence, actual training, statistics, literature or publication readiness. A PASS does not mean the experiments were correct or complete.
