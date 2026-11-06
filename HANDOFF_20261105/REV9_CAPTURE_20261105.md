# Revision 9 live capture — 2026-11-05 20:09 HKT (12:09 UTC)

This is a **fresh filesystem/scheduler capture**, not the dated 117/139/141 ledger snapshot.

## Live execution state

| Item | Value |
|---|---|
| `cellok.py count all/export all/cells_all.tsv` | **COMPLETE 1056 / 1120** |
| Remaining | **64** = 23 `no cell dir` + 41 `no metrics.csv` |
| Core (MIFlu/NLinear/PatchTST/DLinear) | **160 / 160** |
| Legacy Table VI/WF (`legacy_done.tsv`) | **139 / 189** |
| Legacy failures (`rc != 0` in `legacy_lane.log`) | **0** |
| Empty `decision_tree` directories in `all/export` | **0** |
| `735301` | RUNNING 11h38 on `gpu-a100-10` |
| `735300` | no longer in queue (wall/exit; check `sacct` before reuse) |
| `735298`, `735299` | RUNNING (v2 controllers) |
| `737759` | RUNNING (legacy controller); `737762` PENDING successor |
| scratch quota | **314 / 300 GB soft, grace 9 days, 1024 GB hard** |
| home quota | 23 / 50 GB soft, 100 GB hard |

No new jobs were submitted and no active job was cancelled during this capture.

## Why this matters for the revision-9 prompt

The prompt's dated counts (117, 139, 141) are historical. The live count is **1056/1120**, and
the legacy TODO count is **139/189**. The old 13-empty-`decision_tree` observation is **stale**:
the current `all/export/decision_tree` has **0 empty directories** and 40/40 complete cells.

## The blocking scientific issue: incompatible scoring panels

Verified directly from the files:

- **MIFlu export** (`predictions_miflu_L24_paper_protocol.csv`) has columns:
  `split, abs_week, step, epiweek, week_start_date, ground_truth_ili, prediction_ili,
  ground_truth_ili_phys, prediction_ili_phys`
  → **ILITOTAL only**, no seven-channel tensor.
- **Other-model export** (`pred_nlinear_L24_s2021.npz`) has:
  `pred (170, 7, 24) float32`, `target (170, 7, 24) float32`, `target_start_row (170,) int32`,
  `L`, `seed`.
  The shape is consistent with `(N, channel=7, horizon=24)`, but the axis order still has to be
  verified against `L` and the seven channel names before scoring.
- Therefore the 1056 "complete" cells do **not** yet form a harmonised seven-channel leaderboard.
  MIFlu contributes only ILITOTAL at its own cropped panel; the 237 seven-channel NPZ cells use
  a different panel.

## Highest-priority next action (O1)

Recover **seven-channel MIFlu predictions from the existing checkpoints**, not retrain:

1. Load each `core/ckpt/miflu/L*_s*/best_miflu_L*.pth` (40 cells).
2. Run inference over **all valid test windows** with `drop_last=False`.
3. Export `pred/target (N, 7, L)` plus `target_start_row`, channel order, scaler mean/std,
   profile hash, checkpoint hash.
4. Build both panels: all-valid and historical crop, with identical target populations.
5. Only then recompute MSE/MAE, peaks, and paired statistics.

If checkpoint recovery is impossible, report the exact missing configurations and the smallest
justified rerun set — do not restart the 40 cells blindly.

## Current status label

**IN PROGRESS.** 1056/1120 national cells and 139/189 legacy cells are complete by the checker;
no harmonised leaderboard, no new Holm, no event-level table, and no revision-9 scientific
rewrite are claimed from this capture.
