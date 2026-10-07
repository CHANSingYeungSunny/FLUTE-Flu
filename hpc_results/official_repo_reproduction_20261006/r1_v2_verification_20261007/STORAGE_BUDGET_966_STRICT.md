# STORAGE BUDGET — author-966 strict-containment eight-model championship

Generated 2026-10-07. Gate required by the authorisation §10.

# VERDICT: `STORAGE_READY_FOR_966_STRICT_8MODEL`

---

## 1. Current quota state

```
Filesystem type   GB   quota   limit  grace
home       USR    31      50     100  none
scratch    USR   285     300    1024  none
```

`home` free against the soft quota: **19 GB**.
`scratch` is writable and **no longer over quota** — the over-quota / expired-grace
condition described in the brief was cleared earlier in this session
(`HPC_CLEANUP_RECLAIMED_SPACE.md`: 414 GB → 285 GB, grace `expired` → `none`).

All championship output is written under `$HOME`; scratch is read-only for this work.

## 2. Recovered storage use in the previous champion experiment

| item | size | note |
|---|---:|---|
| `stage5_a2_durable` (36 A2 checkpoints, full) | 7.4 G | retained, protected |
| `innovation_durable` (578 compact ckpts + preds) | 4.3 G | retained, protected |
| `official_repo_reproduction_20261006` | 5.5 G | R1-B + Track-H evidence |
| **base models** | | |
| `gpt2` (home HF cache) | 0.65 G | shared by MIFlu, calf_llm, timecma_llm |
| `Qwen2.5-1.5B` (`v3_cache`, scratch) | 3.4 G | qwen_time_llm only; **retained in cleanup** |
| superseded full checkpoints removed | 128.8 G | 2026-10-07 cleanup |

**Actual unique physical storage is well below apparent storage**: frozen text-backbone
tensors are *not* stored in any checkpoint (sidecar `.frozen_keys.json` instead),
which is what keeps Qwen fits at ~5 MB rather than ~3 GB each.

## 3. Projected requirement — strict-966 eight-model matrix

Matrix: **8 models × 4 horizons × 3 seeds (42/43/44) = 96 fits**.

| component | per unit | units | total |
|---|---:|---:|---:|
| locked checkpoint (adapter + head) | ~7–11 MB | 96 | ~0.9 GB |
| predictions + targets (val + test CSV) | ~2–12 MB | 96 | ~0.6 GB |
| canonical key sets | — | 4 L × 3 seeds | **0.26 GB** (built, measured) |
| logs, manifests, provenance | ~50 KB | 96 | ~5 MB |
| independent score tables | ~1 MB | 8 models | ~10 MB |
| figures + final report | — | — | ~0.2 GB |
| **projected retained total** | | | **~2.0 GB** |
| peak temporary (atomic-write +1 copy) | | | +0.1 GB |
| **projected peak** | | | **~2.1 GB** |

### Per-model budget

| model | backbone | ckpt/fit | 12 fits | backbone stored? |
|---|---|---:|---:|---|
| miflu (official-repo) | gpt2 | ~8 MB | ~0.10 GB | frozen, not stored |
| qwen_time_llm | Qwen2.5-1.5B | ~5 MB | ~0.06 GB | frozen, not stored (else ~3 GB/fit) |
| calf_llm | gpt2 | ~5 MB | ~0.06 GB | frozen, not stored |
| timecma_llm | gpt2 | ~5 MB | ~0.06 GB | frozen, not stored |
| nlinear | none | <1 MB | ~0.01 GB | n/a |
| dlinear | none | <1 MB | ~0.01 GB | n/a |
| patchtst | none | ~1 MB | ~0.02 GB | n/a |
| itransformer | none | ~1 MB | ~0.02 GB | n/a |

**Per seed ≈ 0.67 GB · per horizon ≈ 0.5 GB · per model ≈ 0.06–0.1 GB.**

## 4. Dependency check — base models present

| dependency | required by | present? |
|---|---|---|
| `gpt2` | miflu, calf_llm, timecma_llm | ✅ home HF cache + `v3_cache` |
| `Qwen/Qwen2.5-1.5B` | qwen_time_llm | ✅ `/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B` |
| author-966 dataset | all | ✅ sha `2a96dfed…ebfe5` |
| tokenizers/configs | all | ✅ alongside the snapshots |

No dependency is missing. **No base model was deleted in the earlier cleanup** —
`v3_cache` was explicitly retained as `REGENERABLE_CACHE` for exactly this reason.

## 5. Safe free-space margin

| | GB |
|---|---:|
| projected peak requirement | 2.1 |
| free against soft quota | 19.0 |
| **margin** | **~17 GB (9× the requirement)** |

Margin is adequate for the championship plus the final DOCX and figures.

## 6. Gate result

**`STORAGE_READY_FOR_966_STRICT_8MODEL`** — quota is within limit on both
filesystems, grace is `none` on both, all required base models and datasets are
present and hash-verified, and the projected peak is ~9× inside the free margin.

No further cleanup is required to proceed. The 294 retained
`PROTECTED_UNCERTAIN` checkpoints (67.32 GiB) remain untouched.