# HISTORICAL DEPLOYMENT — STORAGE ACCOUNTING

Generated 2026-10-06. Evidence: CPU-only Slurm jobs **606430** (metadata, `du`, inodes)
and **606432** (full SHA-256 of all 594 checkpoint-like files and 20,792 small files).
Both jobs were **strictly read-only**. ZERO GPU-hours.

---

## 1. Headline

> **The 204.6 GiB family is essentially all unique content.**
> Full content hashing finds only **66.7 MiB** of byte-identical checkpoint data —
> **0.032 %** of the family. Deduplication cannot meaningfully relieve the quota.

---

## 2. Apparent vs actual vs unique

| Measure | Value |
|---|---:|
| **total apparent size** (`du -sb --apparent-size`) | **219,722,194,209 B = 204.6 GiB** |
| **actual disk usage** (`du -sb`) | **219,722,194,209 B = 204.6 GiB** |
| **estimated unique physical storage** | **≈ 216,441,000,000 B ≈ 201.6 GiB** |
| byte-identical reclaimable (checkpoints, full SHA-256) | **69,969,264 B = 66.7 MiB** |
| byte-identical reclaimable (small files, full SHA-256) | **245.9 MiB** |
| **total reclaimable by deduplication** | **≈ 312.6 MiB** |

**Apparent == actual**, exactly, because the family contains **0 symlinks** and **0
hard-linked files** (verified by inode link count across all 594 checkpoint files). There
is no link-based sharing to account for.

---

## 3. Why the naive estimate was wildly wrong

A first pass grouped files by `(size, basename)` and reported **≈ 186.7 GiB**
reclaimable. That estimate is **refuted** by full hashing:

| Approach | Basis | Estimated reclaimable | Verdict |
|---|---|---:|---|
| naive | same size **and** same basename | 186.7 GiB | ❌ **wrong by ~2,900×** |
| **full SHA-256** | byte-identical content | **66.7 MiB** | ✅ verified |

The naive method was misled by the naming scheme: 447 of 594 checkpoint files are called
`best_val_mse.pt`, and the Qwen ones share a size (6,176,478,657 B) because they are the
same *architecture* — but they are **different training runs**.

**The strongest single piece of evidence**:

```
files larger than 5 GB          : 24
distinct SHA-256 among them     : 24
combined size                   : 138.06 GiB
=> ALL 24 ARE DIFFERENT
```

Those 24 files are the entire Qwen footprint (138.06 GiB). Not one is a duplicate.

---

## 4. Duplicate structure (verified)

| Category | Files | Identical groups | Reclaimable |
|---|---:|---:|---:|
| checkpoint-like (`.pt`, `.safetensors`) | 594 | **28** | **66.7 MiB** |
| small files (`< 4 MiB`: `.py .json .sh .csv .md`) | 20,792 | 967 | **245.9 MiB** |
| **total** | 21,386 | 995 | **≈ 312.6 MiB** |

Detail in `HISTORICAL_DEPLOYMENT_DUPLICATE_CANDIDATES.csv` (400 rows, largest groups
first; every row carries the full SHA-256 that justifies the claim).

The largest duplicate groups are **small files copied into all 19 directories** — e.g. a
50.5 MiB group appearing **19 times**, which is the staged source tree repeating itself.
That is the real duplication pattern: the *code*, not the *checkpoints*.

---

## 5. Qwen

| | Value |
|---|---:|
| Qwen checkpoint files | 33 |
| Qwen checkpoint bytes | **138.07 GiB** (67 % of the checkpoint footprint) |
| identical-content groups among them | **3** |
| reclaimable | **4.2 MiB** |

Detailed in `HISTORICAL_QWEN_REDUCTION_PROVENANCE.md`.

---

## 6. External dependencies that make the numbers non-self-contained

| Dependency | Evidence |
|---|---|
| Hugging Face model cache | every sbatch in the project sets `HF_HOME=/home/sychan552/.cache/huggingface`; **the family contains no cache of its own** |
| a Qwen2.5-1.5B base model | the compact Qwen export is 1.41 MiB, so the 1.5B base is **not inside** it |
| tokenizers | `find -name 'tokenizer*'` → **0 files** in the whole family |
| configuration files | `find -name 'config.json'` → **0 files** |
| the self-built code | shipped *inside* each directory under `scripts/`, so the code is not an external dependency — but it is a **Track-B** dependency in the lineage sense |

So the family's **204.6 GiB understates** what would be needed to run it: the cache and
the base weights live elsewhere and are not counted here.

---

## 7. Deletion status

Every duplicate candidate is marked:

```
NOT_AUTHORIZED_FOR_DELETION
```

and every directory:

```
UNSAFE_TO_DELETE
```

**Scratch cleanup was not performed and is not authorized.** This document is an
accounting exercise only.

### Practical consequence for the quota problem

Scratch is **413 GB used against a 300 GB quota, grace expired**. The audit shows
deduplication would recover **≈ 313 MiB** — i.e. **0.1 %** of the overage. Relieving the
quota therefore requires deleting **real historical runs**, which is a scientific and
authorization decision, not a housekeeping one. Options to put to the user later:

1. delete only `HISTORICAL_INTERMEDIATE_BUILD` directories that contain no unique
   checkpoint (none has yet been proven unique-free);
2. move the family to a larger allocation rather than deleting it;
3. accept the quota state and continue writing to `/home` (current practice).