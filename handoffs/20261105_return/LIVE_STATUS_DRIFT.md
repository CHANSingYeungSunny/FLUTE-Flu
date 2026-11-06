# Live status moves faster than this ZIP (read me first)

This return package is a **snapshot at 2026-11-04 15:35 UTC (23:35 HKT)**.
`RUN_LEDGER.csv`, `RUN_METRICS.csv`, `HPC_VALIDATED_CELLS.tsv` and
`VALIDATION_RESULT.json` all describe THAT instant: 117/1120 validated cells.

A later read at **15:47 UTC** showed:

| Item | 15:35 snapshot | 15:47 UTC live |
|---|---|---|
| Core panel | 160/160 | 160/160 |
| National 28-arm matrix | 117/1120 | **139/1120** |
| `trackB_v2_all_l0` (gpu_a100) | PENDING | PENDING (Priority) |
| `trackB_v2_all_l1` (gpu_a100) | PENDING | PENDING (Priority) |
| `trackB_v2_all_l2` (stingy) | PENDING | **RUNNING 8:46 on gpu-a100-03** |
| controller 735298 / post-all 735299 | RUNNING | RUNNING |
| duplicate cells claimed by 2 lanes | 0 | **0** |
| `all/failed/` | 0 | 0 |
| scratch quota | ~320 G / 300 G soft | ~320 G / 300 G soft, grace 10 days |

The 40 rows in `all/retry.tsv` seen at 15:35 were legacy rows from the ORIGINAL
`lane_all.sh` (classical models wrongly routed to `train_backbone_966.py`).
At 15:47 they were archived on HPC to `all/retry.legacy_20261104.tsv` with
`all/RETRY_ARCHIVE_NOTE.md`. They are NOT live v2 failures.

**Do not treat the counts in this ZIP as final.** Before writing any result
table, re-run the command in `REPRODUCE.md` and re-generate the return package
from the same machine data source. `RAW_EVIDENCE/cells/` contains only the
artefacts that existed at snapshot time.
