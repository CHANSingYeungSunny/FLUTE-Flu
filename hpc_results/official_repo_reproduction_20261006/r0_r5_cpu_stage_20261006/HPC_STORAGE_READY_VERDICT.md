# HPC STORAGE READY — VERDICT (S5)

Generated 2026-10-06. Covers Storage Track S2–S5.

# VERDICT: **`HPC_STORAGE_READY`** — with one standing constraint

Storage is fit for the R1-B pilot **provided every job writes to `$HOME`**. Scratch remains
over quota and is expressly excluded.

---

## S2 — Capacity and the three peak-storage forecasts

### Current capacity (measured)

| Filesystem | Used | Quota | Free | Grace | Status |
|---|---:|---:|---:|---|---|
| **home** | 26.86 GB | 50 GB | **≈23.1 GB** | none | ✅ **usable** |
| **scratch** | **413.2 GB** | 300 GB | — | **expired** | ❌ **excluded** |

Inode use: home 91,307 files against an unlimited file-count quota — **no inode pressure**.

### The forecast that matters: which trainer path

The F1 projection was wrong by **~85×** because it assumed `save_locked_ckpt` (trainable
tensors only) while `train_miflu.py` writes the full `state_dict`. The Tier-1 job measured
the real figure:

| Path | Measured per checkpoint |
|---|---:|
| **full `state_dict`** (`train_miflu.py`, F1) | **328,585,240 B ≈ 313 MiB** (Tier-1 job measured **331,158,882 B**) |
| **`save_locked_ckpt`** (trainable only) | ≈ 4.1 MB |

### Forecasts

| Stage | Fits | locked path | full-state_dict path |
|---|---:|---:|---:|
| **R1-B pilot** (4 horizons × 1 rep) | 4 | **16.6 MiB** | **1.22 GiB** |
| **10-repetition expansion** (4 × 10) | 40 | **159.4 MiB** | **12.24 GiB** |
| **historical replacement** (4 horizons × 10 seeds on the 1025 contract) | 40 | **159.4 MiB** | **12.24 GiB** |
| **all three together** (locked) | 84 | **≈0.33 GiB** | — |

**Interpretation**

- On the **locked path**, everything fits in home with ~22.8 GB to spare. No concern.
- On the **full path**, the 10-repetition expansion and the replacement each need
  **~12.2 GiB**. Home has 23.1 GiB, so **one** such run fits and **two cannot run
  concurrently** — and a run that leaves checkpoints behind would exhaust home.

**Therefore the pilot and every later stage MUST use the locked-checkpoint path**, and the
guard must refuse otherwise. That is enforced in `storage/storage_guard.py`.

---

## S3 — Guard, retention and atomic-write protocol

### Retention policy (explicit)

| Kept | Never kept |
|---|---|
| best validation-selected checkpoint, one per (model, L, repetition) | optimizer state after selection |
| final predictions and targets (7-channel NPZ) | scheduler state |
| run manifest and provenance | per-epoch checkpoints |
| slurm stdout/stderr and per-fit logs | intermediate training tensors |
| scoring outputs and the gate report | an HF cache inside the output tree |

**Lifecycle**: during training at most **2** checkpoints exist (rolling best + temp); on
selection the best is promoted atomically and the temp deleted; on completion only the
retained set remains. **Peak is therefore bounded to one checkpoint per fit plus one temp.**

### Atomic-write protocol

`atomic_save_npz()` and `atomic_save_torch()` write to a `.part` file in the **same
directory**, `fsync`, then `os.replace()` — atomic on POSIX and Windows. An interrupted
write leaves the **original untouched** rather than a truncated artefact that would later
pass an existence check.

### Preflight / postflight

```
preflight(target, projected):
    refuse if target is on scratch and scratch is not declared healthy
    refuse if free space is UNKNOWN
    refuse if free < max(1 GiB, 10 x projected)
    else  -> STORAGE_PREFLIGHT_PASS

postflight(target):
    fail if any *.part file remains
    else  -> STORAGE_POSTFLIGHT_PASS, with the file count and total bytes
```

---

## S4 — Test evidence

`storage/storage_guard_tests.py` — **24 / 24 checks pass** (transcript:
`logs/storage_guard_tests.txt`). All artefacts are **synthetic and tiny**; nothing was
written to the HPC.

| Group | Checks | What it proves |
|---|---:|---|
| A projections | 6 | projections use measured sizes; the locked/full ratio is 76×; the two 10-rep forecasts are 159 MiB vs 12.24 GiB |
| B refusals | 6 | refuses scratch unless declared healthy; refuses an unmeasurable filesystem; refuses when free < required headroom; required = max(1 GiB, 10×) |
| C atomic writes | 7 | NPZ and torch saves work; **a simulated failure during `os.replace` leaves the original byte-identical** and no `.part` residue |
| D postflight | 2 | passes on a clean directory; **fails when a `.part` file is present** |
| E retention | 3 | the policy names what is kept and what never is; peak is bounded |

Two guard defects were found by the tests and fixed:
1. `fs_stats` crashed on a path with no existing ancestor → now reports free space as
   UNKNOWN and **refuses** rather than assuming safety;
2. scratch detection used a POSIX prefix that a Windows dev box never matches → now
   inspects path **components**, so the local tests exercise the same branch the HPC runs.

---

## S5 — Verdict and the standing constraints

# `HPC_STORAGE_READY`

| Condition | Status |
|---|---|
| home capacity verified | ✅ 23.1 GB free against a ≤0.33 GiB locked-path total for all three stages |
| inode pressure | ✅ none |
| retention policy defined | ✅ |
| atomic-save protocol implemented | ✅ |
| preflight / postflight implemented | ✅ |
| synthetic guard tests | ✅ **24/24** |
| scratch excluded from all future writes | ✅ enforced in code |

### The standing constraints

1. **All output goes to `$HOME`.** Scratch is 413/300 GB with grace expired and is
   read-only in practice.
2. **The locked-checkpoint path is mandatory.** The full `state_dict` path costs 313 MiB
   per fit and would put a 10-repetition run at 12.24 GiB.
3. **Only one full-path run can be in flight** — home could not hold two.
4. **No cleanup is authorised.** Scratch remains over quota; relieving it requires deleting
   real historical runs, which is the user's decision (deduplication would recover only
   0.06 % of it, so deduplication is not a remedy).

### What this verdict does NOT authorise

`HPC_STORAGE_READY` is a **storage** gate. It does not grant GPU quota. The R1-B pilot still
requires the separate reproduction-specific authorization.