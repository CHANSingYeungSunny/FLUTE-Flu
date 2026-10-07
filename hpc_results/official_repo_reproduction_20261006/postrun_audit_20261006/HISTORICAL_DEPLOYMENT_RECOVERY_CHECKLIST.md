# HISTORICAL DEPLOYMENT — RECOVERY CHECKLIST

Generated 2026-10-06. **No inference was run.** This is a *plan*, not a result.

The 20 fields the brief requires are recorded per directory in
`HISTORICAL_DEPLOYMENT_RECOVERY_MATRIX.csv` (19 rows × 22 columns). This document
summarises and adds the cross-directory view.

---

## 1. Per-deployment status at a glance

| Field | Finding (all 19 directories) |
|---|---|
| 1 source directory | `/gpfs1/scratch/sychan552/innovation_deploy_root_v3_*` |
| 2 historical source code | **PRESENT** — the self-built `scripts/` is staged inside each directory |
| 3 required checkpoint | `results/**/checkpoints/best_val_mse.pt` (full) or `durable_sim/**/compact.safetensors` (reduced) |
| 4 required base model | **EXTERNAL** — GPT-2, and a Qwen2.5-1.5B base for the Qwen arms |
| 5 required LoRA adapter | **LIKELY** — export sizes match an adapter/head; separate storage `UNKNOWN` |
| 6 required tokenizer | **EXTERNAL** — 0 tokenizer files in 27,019 files |
| 7 required configuration | **EXTERNAL** — 0 `config.json` |
| 8 required Python environment | the Track-B conda env; **no requirements file shipped** |
| 9 expected entry command | **`UNRECOVERED`** — no launch script, README or CI config anywhere |
| 10 cache requirements | `HF_HOME=/home/sychan552/.cache/huggingface` (external, unverified) |
| 11 link requirements | **NONE** — 0 symlinks, 0 hard links |
| 12 missing dependencies | base weights, tokenizer, config, entry command |
| 13 probable runnability | **LOW** as-is; **MEDIUM** if an entry command is recovered |
| 14 runnable if other v3 dirs disappear | **YES** for code and results (self-contained); the external assets are external regardless |
| 15 minimum future recovery test | see §3 |
| 16 expected prediction file | **NONE** — 0 `.npy` exist |
| 17 expected metric | CSV metrics only; **recomputation impossible** |
| 18 verification checksum | the recorded full SHA-256 values in `HISTORICAL_DEPLOYMENT_DUPLICATE_CANDIDATES.csv` |
| 19 tied to the self-built implementation | **YES** |
| 20 why it cannot substitute for an official run | different codebase, earlier lineage, post-training checkpoint reduction, no saved predictions |

---

## 2. Named candidates

| Role | Candidate | Justification |
|---|---|---|
| **strongest historical final-deployment candidate** | `innovation_deploy_root_v3_clean14` | **latest mtime in the entire family** (2026-09-21T04:56:42Z); 11 GiB; 5,972 files; 48 checkpoints |
| runner-up | `innovation_deploy_root_v3_clean6` | largest (52 GiB), most files (5,023) and most checkpoints (221) |
| runner-up | `innovation_deploy_root_v3_5` | 50 GiB; last of the pre-`clean` builds (2026-09-17) |
| **strongest historical Qwen deployment candidate** | `durable_sim/**/primary__qwen_time_llm__L*__seed*__w1/compact.safetensors` | the only deployment-ready Qwen artifacts that exist (1.41 MiB, 4,167× reduced) |

**Directories containing unique artifacts**: not determinable this round — establishing it
requires a full content diff across all 27,019 files. See
`HISTORICAL_TRACK_B_DEPENDENCY_MAP.md` §4 for the job that would settle it.

**Cross-directory dependencies**: **none**. 0 symlinks, 0 hard links, 0 shared inodes. The
19 directories are independent copies; the only sharing is *duplicated content*
(995 identical-content groups, 312.6 MiB, mostly the staged source tree repeating).

**Files required to recover the original comparison**: the checkpoints are all present; the
missing pieces are the base weights, tokenizers, configs and the entry command. Because no
predictions were saved, recovering the *comparison* would require **re-running** it, not
merely reloading artifacts.

**Artifacts that should remain preserved after the new benchmark completes**:
all 19 directories, and specifically the three final-deployment candidates and every Qwen
compact export. None of them is reproducible from what remains, and the Qwen exports are
the only reduced form in existence.

---

## 3. Minimum future recovery test (CPU-only Slurm job; not run here)

```
1. load ONE compact.safetensors; print key names and dtypes   (no base model needed)
2. classify the keys: adapter-only vs adapter+head            -> resolves several
                                                                 HISTORICAL_CHECKPOINT_
                                                                 REDUCTION_TECHNIQUES rows
3. confirm whether an external Qwen2.5-1.5B base is required
4. one forward pass under CPU
```

Steps 1–2 are cheap and would resolve most `UNKNOWN` entries. **This is recovery
*execution*, which the brief did not authorize — so it is documented, not run.**

---

## 4. Preservation

**Nothing was deleted, moved, renamed, compressed, truncated or modified.** All 19
directories remain `UNSAFE_TO_DELETE`; all duplicate candidates remain
`NOT_AUTHORIZED_FOR_DELETION`.