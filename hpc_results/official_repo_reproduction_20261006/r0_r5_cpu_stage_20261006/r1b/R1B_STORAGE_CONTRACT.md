# R1B STORAGE CONTRACT

## Location

| Item | Value |
|---|---|
| output root | **`$HOME/official_repo_reproduction_20261006/`** |
| scratch | **prohibited for output** — 413 GB used against a 300 GB quota, grace expired; a 10 KB `scp` was rejected with `Disk quota exceeded` |
| code root | `/scratch/sychan552/a2_stage5` — **read-only** |

## The measured size that matters

| Trainer path | Per checkpoint |
|---|---:|
| **full `state_dict`** (`train_miflu.py`; also what F1 produced) | **331,158,882 B** measured by job 607887 |
| `save_locked_ckpt` (trainable tensors only) | ≈ 4.1 MB |

The F1 projection assumed the locked path and predicted 3.9 MB; the actual was **329 MB — a
factor of 85**. Every R1-B estimate therefore uses a **measured** value.

## Forecasts

| Stage | Fits | locked | full state_dict |
|---|---:|---:|---:|
| R1-B pilot | 4 | **16.6 MiB** | 1.22 GiB |
| 10-repetition expansion | 40 | **159.4 MiB** | **12.24 GiB** |
| historical replacement | 40 | **159.4 MiB** | **12.24 GiB** |

Home has **23.1 GB** free, so the locked path fits everywhere and **two full-path runs
cannot be in flight at once**.

## Mandatory protocol

1. **Use the locked-checkpoint path.** The guard refuses a full-path plan that would exceed
   the headroom.
2. **Preflight before writing**: refuse if the target is on scratch and scratch is not
   declared healthy; refuse if free space is UNKNOWN; refuse if free < `max(1 GiB, 10 x
   projected)`.
3. **Atomic writes only** (`atomic_save_npz` / `atomic_save_torch`): temp file in the same
   directory, fsync, `os.replace`. A failed overwrite leaves the original byte-identical.
4. **Postflight after writing**: fail if any `.part` file remains.
5. **Retention**: one best checkpoint per (model, L, repetition); never optimizer state,
   scheduler state or per-epoch checkpoints.
6. **No deletion of existing artifacts**, ever, without explicit path-level authorization.

Implementation: `storage/storage_guard.py`; tests: `storage/storage_guard_tests.py`
(**24/24 pass**). Verdict: **`HPC_STORAGE_READY`**.
