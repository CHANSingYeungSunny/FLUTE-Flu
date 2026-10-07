# HPC POST-CLEANUP QUOTA STATUS

Verified 2026-10-07 on `hpclogin02` via `mmlsquota --block-size=G`.

```
                         Block Limits                                    |     File Limits
Filesystem type             GB      quota      limit   in_doubt    grace |    files   quota    limit in_doubt    grace  Remarks
home       USR              30         50        100          1     none |    91681       0        0       68     none
scratch    USR             285        300       1024          2     none |    45945       0        0       98     none
```

## Verdict

| | before | after |
|---|---|---|
| scratch used | 414 GB | **285 GB** |
| scratch soft quota | 300 GB | 300 GB |
| **scratch grace** | **expired** | **none** |
| scratch hard limit | 1024 GB | 1024 GB |
| home used | 30 GB | 30 GB (unchanged) |
| home quota / limit | 50 / 100 GB | 50 / 100 GB |

**The scratch over-quota condition is cleared and grace is restored to `none`.**
Inode counts (45,945 scratch / 91,681 home) are far below any file-count quota
(reported as 0 = unlimited).

## Capacity for the remaining approved work

| upcoming work | projected need | fits? |
|---|---:|---|
| R1-B corrected pilot, remaining horizons | 16.6 MiB per fit (locked path) | ✅ |
| ten-repetition expansion, if justified | ~170 MiB | ✅ |
| historical 1025-row MIFlu replacement | single-digit GB | ✅ |
| atomic writes, logs, predictions | <1 GB | ✅ |

Free to the soft quota ≈ **15 GB**; free to the hard limit ≈ **739 GB**.
Home, where every R1-B artefact is written, holds **20 GB free** against a
50 GB soft quota — the binding constraint for the pilot is home, not scratch,
and it is comfortable.

## Safety margin note

15 GB of soft-quota headroom is adequate but not generous. If a future stage
needs bulk scratch, the next candidates in order of confidence are the 294
unproven checkpoints (67.32 GiB, `PROTECTED_UNCERTAIN`) and `CHATTIME` (190 GB,
needs a usage proof). Neither was touched this pass.

Writes are confirmed working (a probe file was created and removed on scratch).
No active job writes to scratch: the R1-B pilot reads `a0_replay` read-only and
writes only under `$HOME`.