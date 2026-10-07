# F1 HOME QUOTA CHECK

Generated 2026-10-06. Measured with `mmlsquota` (lightweight, login-node safe).

## 1. Measurement

| Filesystem | Used | Quota | Limit | Grace | Status |
|---|---:|---:|---:|---|---|
| **home** | 28,172,304 KB = **26.86 GB** | 52,428,800 KB = **50 GB** | 100 GB | none | OK |
| **scratch** | 433,264,576 KB = **413.2 GB** | 314,572,800 KB = **300 GB** | 1000 GB | **expired** | **OVER QUOTA** |

## 2. Available safe home storage

```
quota           50.00 GB
used            26.86 GB
headroom        23.14 GB
less the F1 projection (100 MB rounded up)   ->  23.04 GB still free afterwards
```

## 3. The guard, and why it passes

The F1 scripts refuse to run when `(quota - used) < 1 GB`:

```
available 23.14 GB  >=  required 1.00 GB   ->  PASS (23x margin)
projected F1 output  0.10 GB               ->  226x smaller than available
```

## 4. Scratch

**F1 writes nothing to scratch.** The only scratch access is READ-ONLY, for the project
code root and the author dataset. Scratch is over quota and must not receive output.

## 5. Note on file-count quota

The home file-count quota is `0` (unlimited) with 91k files in use, so F1's ~50 new
files raise no file-count concern.

## 6. Confirmation

No file was deleted to make room, and none will be. The guard exists so a future run
cannot silently fill the filesystem; it is not a mechanism for reclaiming space.
