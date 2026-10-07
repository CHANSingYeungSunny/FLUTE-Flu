# CURRENT FILESYSTEM AND QUOTA STATUS

Generated 2026-10-06. Measured with `mmlsquota` (lightweight, login-node safe) and by the
two read-only CPU Slurm jobs 606430 / 606432.

---

## 1. Quota (live measurement)

```
mmlsquota -u sychan552
```

| Filesystem | Used | Quota | Limit | In doubt | Grace | Status |
|---|---:|---:|---:|---:|---|---|
| **home** | 28,171,472 KB ≈ **26.9 GB** | 52,428,800 KB = 50 GB | 104,857,600 KB = 100 GB | 0 | none | ✅ **OK** (≈54 % of quota) |
| **scratch** | **433,264,576 KB ≈ 413.2 GB** | 314,572,800 KB = **300 GB** | 1,073,741,824 KB = 1000 GB | 0 | **expired** | ❌ **OVER QUOTA by ≈113 GB** |

**Consequence**: `/gpfs1/scratch` is effectively **read-only** for this account. Writes fail
intermittently with `Disk quota exceeded` (observed on an `scp` of a 10 KB file).

**Mitigation in force**: every output of this and the previous continuation is written under
`/gpfs1/home/sychan552/`. The author's repository checkout on scratch is used **read-only**,
which is unaffected by the quota.

---

## 2. Where the scratch usage sits

| Path | Size |
|---|---:|
| `/gpfs1/scratch/sychan552` (total) | **443.6 GB** (matches the quota figure) |
| `…/CHATTIME` | 190 GB |
| **`…/innovation_deploy_root_v3_*` (19 dirs)** | **204.6 GiB ≈ 219.7 GB** (46 % of the account) |
| `…/a0_replay` (author checkout) | small (11 top-level entries) |
| other deploy roots / staging | remainder |

Within the v3 family, usage concentrates in `results/`:

| Directory | Total | of which checkpoints |
|---|---:|---:|
| `v3_clean6` | 52 G | 50.49 GiB |
| `v3_5` | 50 G | 49.00 GiB |
| `v3_clean12` | 11 G | 9.54 GiB |
| `v3_clean14` | 11 G | 9.54 GiB |
| `v3_clean13` | 9.7 G | 9.54 GiB |
| `v3_clean4/5/7/8/9/10` | 9.5–9.6 G each | 9.45–9.50 GiB each |
| `v3_3`, `v3_4` | 7.1 G each | 7.00 GiB each |
| `v3_1/2`, `v3_clean1/2/11` | 23–27 M each | ~0 |

---

## 3. The decisive storage finding

**Deduplication cannot relieve this quota.**

| Method | Reclaimable | Basis |
|---|---:|---|
| naive (same size + same basename) | 186.7 GiB | ❌ refuted |
| **full SHA-256** (all 594 checkpoints) | **66.7 MiB** | ✅ verified |
| small files (< 4 MiB; 20,792 hashed) | 245.9 MiB | ✅ verified |
| **total** | **≈ 312.6 MiB = 0.1 % of the overage** | |

The family is **204.6 GiB of essentially unique content**; all 24 files larger than 5 GB
(Qwen, 138.06 GiB combined) have **distinct** SHA-256 values.

**Therefore**: relieving the quota requires deleting **real historical runs**. That is a
scientific and authorization decision. **Scratch cleanup is NOT authorized and was NOT
performed.**

---

## 4. Filesystem properties of the historical family

| Property | Value |
|---|---|
| symlinks | **0** |
| broken symlinks | **0** |
| hard-linked files (nlink > 1) | **0** |
| shared inodes | **0** (implied) |
| apparent size == actual usage? | ✅ **yes, exactly** — no link-based sharing exists |
| git metadata inside any v3 dir | **none** |
| `.npy` prediction files | **0** (in 27,019 files) |

---

## 5. Writable locations

| Path | Writable? | Used for |
|---|---|---|
| `/gpfs1/home/sychan552/…` | ✅ yes (26.9/50 GB used) | **all outputs of this work** |
| `/gpfs1/scratch/sychan552/…` | ❌ effectively no | read-only access to the author checkout |
| local Windows workspace | ✅ yes | deliverables, scripts |

---

## 6. Protection status

| Object | Status |
|---|---|
| 19 `innovation_deploy_root_v3_*` directories | **`UNSAFE_TO_DELETE`** |
| 995 byte-identical duplicate groups | **`NOT_AUTHORIZED_FOR_DELETION`** |
| all other pre-existing artifacts | untouched — verified in `FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md` |

---

## 7. Options to put to the user (not acted on)

1. **Delete** `HISTORICAL_INTERMEDIATE_BUILD` directories that contain no unique checkpoint —
   but uniqueness is not yet proven for any of them, and deleting historical runs is a
   scientific loss even when they are reproducible.
2. **Move** the family to a larger allocation rather than deleting it (preserves everything,
   needs a target and a copy budget).
3. **Accept** the quota state and continue writing to `/home` — current practice, and it has
   worked for two consecutive rounds.

This document recommends nothing; it reports the state and the options.