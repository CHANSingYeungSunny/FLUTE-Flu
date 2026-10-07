# HISTORICAL TRACK B — DEPENDENCY MAP

Generated 2026-10-06 from read-only evidence (jobs 606430, 606432).

---

## 1. What each directory depends on

```
innovation_deploy_root_v3_N/
├── scripts/          self-built code            -> SELF-CONTAINED
├── data/             dataset copies             -> SELF-CONTAINED
├── hpc_scripts/      submission scripts         -> SELF-CONTAINED
├── hpc_results/      run outputs                -> SELF-CONTAINED
└── results/          checkpoints + metrics      -> SELF-CONTAINED
                     BUT at run time they needed:
        ├── HF model cache      /home/sychan552/.cache/huggingface   EXTERNAL
        ├── GPT-2 base weights                                        EXTERNAL
        ├── Qwen2.5-1.5B base weights                                 EXTERNAL
        ├── tokenizers                                                EXTERNAL
        └── the Track-B conda env  (mlflu_hpc)                        EXTERNAL
```

**Key structural fact**: each directory is a *staged copy of the whole project*, so the
directories do not depend on each other — but all of them depend on the same
out-of-family assets.

---

## 2. Cross-directory dependencies

| Dependency type | Count | Evidence |
|---|---:|---|
| symbolic links | **0** | `find -type l` across the family → 0 rows |
| broken symbolic links | **0** | `find -xtype l` → 0 rows |
| hard links (nlink > 1) | **0** | inode link count across 594 checkpoint files → 0 |
| shared inodes | **0** | implied by the above |
| **duplicated content** | **995 groups, 312.6 MiB** | full SHA-256 (`HISTORICAL_DEPLOYMENT_DUPLICATE_CANDIDATES.csv`) |

So the directories are **independent copies**, not views onto shared storage. The
duplication that exists is real duplication of small files (code, configs, CSVs staged
into all 19 directories) — the largest single group recurs **19 times**.

---

## 3. Content dependency on the outside world

| Asset | Inside the family? | Consequence |
|---|---|---|
| self-built source code | ✅ yes, in `scripts/` | recoverable |
| dataset copies | ✅ yes, in `data/` | recoverable, but **the version is not uniform across the 19** |
| full training checkpoints | ✅ yes (`best_val_mse.pt`) | recoverable |
| reduced exports | ✅ yes (`compact*.safetensors`) | recoverable |
| metrics CSVs | ✅ yes (1,909 `.csv`) | recoverable |
| **predictions / targets** | ❌ **no `.npy` anywhere** | **metrics cannot be independently recomputed** |
| base model weights | ❌ no | must be re-downloaded |
| tokenizers | ❌ no (0 files) | must be re-downloaded |
| configuration files | ❌ no (0 `config.json`) | must be reconstructed |
| entry-point command | ❌ no launch script, README or CI config | must be reconstructed |
| requirements / environment spec | ❌ no | must be reconstructed |

---

## 4. What a full cross-directory uniqueness proof would require

The inventory could **not** establish which directories contain *unique* artifacts,
because that needs a content-level diff across 27,019 files. A minimal next step would be
a further CPU-only Slurm job that:

1. groups **all** files (not just checkpoints and small files) by SHA-256 — the current
   hash job covered 594 large + 20,792 small files, i.e. most of the 27,019 but not all;
2. emits, per directory, the set of hashes that appear **only** there.

Until that runs, every directory stays `HISTORICAL_ROLE_UNKNOWN` at the uniqueness level,
and the default `UNSAFE_TO_DELETE` is the only defensible status.

---

## 5. Dependency verdict

```
INCOMPATIBLE_ACROSS_TRACKS_UNLESS_PROVEN_OTHERWISE
```

Nothing in the family is reachable from A0-R / A1-P / A2-F without crossing the lineage
boundary. The internal dependencies are benign (self-contained copies); the *external*
dependencies (base weights, tokenizer, config, entry command) are the real obstacle to
any future recovery — and none of them is required to keep the artifacts **preserved**,
which is all this round was authorized to do.