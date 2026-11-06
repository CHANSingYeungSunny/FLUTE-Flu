# REV9 FRESH LIVE CAPTURE — 2026-11-05T15:30:00Z / 2026-11-05 23:30 HKT

Read-only, verified on the live cluster after login-node recovery.
Supersedes `REV9_CAPTURE_20261105.md` (20:09 HKT, 1056/1120) and the
historical 117 / 139 / 141 reports.

## Cell status (planned denominators)

| Panel | Planned | Validated complete | Blocked / missing |
|---|---:|---:|---|
| Core (MIFlu/NLinear/PatchTST/DLinear, 4L x 10 seeds) | 160 | **160** | 0 |
| National 28-arm (28 x 4 x 10) | 1120 | **1080** | **40** |
| 7-channel MIFlu recovery (40 checkpoints) | 40 | **0** | 40 (export not run) |
| Legacy Table VI / WF TODO | 189 (`code/queue/legacy_todo.tsv`) | 139 | 50 |

`cellok.py count all/export all/cells_all.tsv`: `COMPLETE 1080 / 1120`,
`BY_REASON {"no metrics.csv": 40}`. All 40 are `ds_r1_distill_qwen1_5b`
(`BLOCKED_CELLS.tsv`, 40 rows; `all/failed/` 40 markers all `=2`).
`all/phase.done` exists, written `PHASE_DONE_WITH_BLOCKED complete=1080 blocked=40`.
`core/phase.done` exists; `all/lane0_v2.done`, `lane1_v2.done`, `lane2_v2.done` exist.
**Do not add 160 + 1120 and call that the sample size** — core and national
overlap for named configurations.

## Jobs live at capture

| JobID | Name | State | Time / reason |
|---|---|---|---|
| 739549 | miflu_7ch_export | PENDING | gpu_a100, Priority, `StartTime=2026-11-07T13:20:16`, 2h wall |
| 739626 | mlflu_p3_driver | RUNNING | tiny, 2:19:08 |
| 739628 | mlflu_p3_s1 | PENDING | gpu_a100, Priority, `StartTime=2026-11-07T13:20:16` |
| 737759 | legacy_todo_ctl | RUNNING | tiny, 9:32:48 |
| 737762 | legacy_todo_ctl | PENDING | Dependency `afterany:737759(unfulfilled)` |

Completed today exit 0:0: 735298, 735299, 735300, 735301, 737282, 737712,
739627. TIMEOUT (pre-existing stingy 6h wall): 735313, 736302, 737938.
FAILED (pre-existing, 14:06, before the kill): 737711 exit 3:0.

## Quota (measured, not the 306 G historical report)

```
home       USR  23374512 KB / 52428800 soft / 104857600 hard, grace none
scratch    USR 329453424 KB / 314572800 soft (~314 GiB / 300 GiB),
                1073741824 hard, grace 9 days
```
No dataset, checkpoint, raw prediction or encoder cache was deleted.

## Scientific status — still BLOCKED

- `core/export7ch/` is **empty** (0 npz). The 40 MIFlu checkpoints exist
  (`core/ckpt/miflu/L*_s*/best_miflu_L*.pth`, count 40), but no 7-channel
  prediction tensor has been produced.
- Local `RAW_EVIDENCE/cells` has 237 seven-channel NPZ (non-MIFlu), 40
  MIFlu ILITOTAL-only CSV, **0** MIFlu NPZ. So no harmonised leaderboard,
  no new Holm, no event-level peak table.
- `export7ch_all.sbatch` is correct in shape (loops 4L x 10 seeds, skips
  existing npz, `--device cuda`, 2h wall), but is queued on `gpu_a100` until
  11-07. **Do not submit a duplicate** while 739549 is alive.
- Legacy chain is stalled by the stale `--dependency=afterok:737712`.

## Reconciliation of conflicting TODO counts

Two DIFFERENT legacy files exist and must not be conflated:
- `code/queue/legacy_todo.tsv` = **189 rows**, with `legacy_done.tsv` = 139
  → "139/189".
- `trackB_20261104/all/LEGACY_TODO.tsv` = **191 rows** (192 lines incl. header);
  `post_all_v2.sh` breakdown: `table6_cell 19`, `wf_arm_cell 110`,
  `wf_classical_cell 42`, `wf_miflu_cell 18`, `table_ix 1`,
  `f5_llm_import 1` = 191. This is the "19 Table VI TODO + 170 WF TODO"
  summary (110+42+18 = 170).
Legacy `DONE` rows in `master_queue.tsv` are a separate, older status set and
must not be counted as v2 completion without a configuration match.

## Empty decision_tree dirs

`all/export/decision_tree` has **0 empty directories** and 40/40 complete
cells. The earlier "13 empty dirs" observation was a transient in-flight
state and is now stale. The ZIP's complete decision-tree cells are a different
observation; both must be identified by configuration, not path name.


---

## Update 2026-11-05T15:46:49Z / 2026-11-05 23:46 HKT (supersedes the 15:30 snapshot above)

- `739549 miflu_7ch_export` PENDING, `StartTime=2026-11-07T13:20:16` — **7ch npz still 0/40**.
- `740183 trackB_v2_fix40` submitted (one, no duplicate) for the 40 blocked cells;
  also PENDING with the same StartTime. Root cause (HF cache layout) fixed and
  verified offline; `run_lane_v2.sh` patched with backup.
- `740169 legacy_todo_lane` COMPLETED 0:0 after the stale dependency was removed.
- **`legacy_done.tsv` 189/189 is misleading**: the final 50 tasks logged
  `rc=3 / SKIP_REASON=bad table6 task id`. `legacy_lane.sh` marks DONE on any
  attempt. These are NOT validated cells. Do not quote 189/189 as completion.
- cellok still `COMPLETE 160/160` core, `COMPLETE 1080/1120` national.
- No `CANCELLED` job since 15:00 UTC; no job was killed by the recovery `pkill`.
- Quota: home 23,374,512 KB; scratch 329,469,744 KB / 314,572,800 soft, grace 9 days.
