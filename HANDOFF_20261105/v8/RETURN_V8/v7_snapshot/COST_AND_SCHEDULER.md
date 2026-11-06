# COST AND SCHEDULER

Captured 2026-11-04T15:35:00Z. Supersedes the 09:13 UTC snapshot, which said `squeue` was empty
and that no job was submitted by the session. That is no longer true.

## Live scheduler (patched v2)

| Job ID | Name | Partition | State at capture |
|---|---|---|---|
| 735297 | trackB_v2_core_ctl | tiny | completed (core 160/160 validated) |
| 735298 | trackB_v2_all_ctl | tiny | RUNNING |
| 735299 | trackB_v2_post_all | tiny | RUNNING |
| 735300 | trackB_v2_all_l0 | gpu_a100 | PENDING (Priority) |
| 735301 | trackB_v2_all_l1 | gpu_a100 | PENDING (Priority) |
| 735313 | trackB_v2_all_l2 | stingy | PENDING (Priority) |

Live exports are in `logs/trackB_v2/live_squeue.txt`, `job_accounting.txt`,
`validated_counts.txt` and `quota.txt`. The 21 old-chain jobs (734673-734676,
734688, 734749-734751, 734617, 734618, 734753, 734754, 734756, 734757,
735139, 735152, 735277-735281) were cancelled and confirmed with `scontrol`;
see `logs/trackB_v2/cancel_verification.log`.

`SCHEDULER_FIX.md` documents why the old chain could never finish (it counted
`results_*.csv`, which only the MIFlu runner emits) and why it produced a stream
of 0-second tiny jobs.

## Measured costs (real, not estimates)

- Pilot 734051 (`stingy`, V100-SXM2-32GB): 20 epochs, 37.3 s/epoch, 748 s total,
  0.71 GB GPU, 170 test windows at L=24, MSE_AllVars 1.236440. V100, NOT A100.
- Core MIFlu A100 cells: about 8.5 min/cell from consecutive lane timestamps.
- Legacy Table VIII cells: 930-1025 s each (A100-SXM4-80GB), from old manifests.
- No A100-hour total is invented for the 1120 matrix. Remaining runtime is
  dominated by queue wait on a 6-node `gpu_a100` partition and cannot be
  estimated reliably from these samples.

## Quota (measured, `logs/trackB_v2/quota.txt`)

- home: 23 GB used / 50 GB soft / 100 GB hard, grace none.
- scratch: ~320 GB used / 300 GB soft / 1024 GB hard, grace 10 days.
  Soft is exceeded by ~20 GB; hard limit is not approached.
- v2 controller warns above 450 GB, pauses new lane submission above 900 GB.
- Checkpoint pruning is OPT-IN (`TRACKB_AUTO_PRUNE=1`) because RETURN_CONTRACT
  requires retaining per-seed checkpoints on HPC; nothing was auto-deleted.
