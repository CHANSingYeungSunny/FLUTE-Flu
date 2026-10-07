# TRACK C — MASTER CONTRACT

`AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP`
Frozen 2026-10-07. This is the **primary final championship**.

---

## 1. The scientific question

> Among the same four LLM-side models and four non-LLM-side models, which
> achieves the lowest **one-time Test** MSE under the author-966
> strict-containment contract?

The champion is selected **only** from Test. Validation exists solely to pick
the checkpoint.

## 2. Dataset and split

| field | value |
|---|---|
| file | `recovery/author_repo/dataset/illness/national_illness.csv` (mirror: `/scratch/sychan552/a0_replay/dataset/illness/`) |
| rows | **966** |
| sha256 | **`2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`** |
| variables | 7 (`% WEIGHTED ILI`, `% UNWEIGHTED ILI`, `AGE 0-4`, `AGE 5-24`, `ILITOTAL`, `NUM. OF PROVIDERS`, `OT`) |
| Train | `[0, 676)` — 676 rows |
| Validation | `[676, 773)` — 97 rows |
| Test | `[773, 966)` — 193 rows |
| T | 104 |
| horizons | 24 / 36 / 48 / 60 |
| seeds | **42, 43, 44** (matched across all eight models) |
| scaler | per-column mean/std, **train rows only** |

### Why 966 rows and not 1025

The 966-row file is the **paper-analysis dataset**: Table II's descriptive
statistics match it **7/7** (max deviation 0.02 %), whereas the July-2026
1025-row snapshot matches only 1/7. Its integer 70:10:20 split is
**676 / 97 / 193**. The 1025-row file belongs to Track H and is **never** mixed
with Track C metrics.

## 3. Strict containment

For every window, with `o` = last input index:

```
input  = data[o-T+1 : o+1]        (T, N)
target = data[o+1   : o+1+L]      (L, N)
origins = [max(split_start-1, T-1), split_end-L-1]
```

and the load-bearing invariants:

```
target_start >= split_start
target_end   <= split_end - 1
target_end    = target_start + L - 1
```

**Split membership is determined by the TARGET range, never by `o`.** This was
the second defect found and is now enforced by a regression assertion in both
the key builder and the Track C dataset loader.

Resulting strict origin counts (verified):

| L | Train | Validation | Test |
|---|---:|---:|---:|
| 24 | 549 | 74 | **170** |
| 36 | 537 | 62 | **158** |
| 48 | 525 | 50 | **146** |
| 60 | 513 | 38 | **134** |

The historical 1025-row rule assigned a window by target **start** only, so
targets spilled across boundaries (23 train, 23/103 validation at L=24).
**Strict containment removes that contamination**, which is precisely why
Track C replaces it as the championship contract.

## 4. Roles

| split | role | may it enter the ranking? |
|---|---|---|
| Train | fitting only | no |
| Validation | checkpoint selection / early stopping | **no** |
| Test | evaluated **once** after the checkpoint is frozen | **yes — exclusively** |

Forbidden and not done: reading Test every epoch, selecting a checkpoint on
Test, tuning after seeing Test, choosing a seed on Test, omitting an
unfavourable seed, mixing Validation into the championship average.

## 5. Canonical keys

One key set per (horizon, seed), identical for all eight models:

```
dataset_hash, seed, horizon, split, forecast_origin, target_start_row,
target_end_row, forecast_lead, feature_index, corrected_feature_name
```

`forecast_origin = o` (last input index); `target_start_row = o+1`;
`target_end_row = o+L`.

| manifest | rows |
|---|---:|
| `STRICT_966_TRAIN_KEYS.csv` | 1,858,248 |
| `STRICT_966_VALIDATION_KEYS.csv` | 182,448 |
| `STRICT_966_TEST_KEYS.csv` | 521,136 |

**Key-set SHA-256: `4ad79bb1…d1961`** (superseded invalid set, recorded but not
used: `0742b4ab…042a7`).

The scorer rejects: missing, extra or duplicate keys; shifted origins; wrong
leads, feature indices, labels, split, seed, horizon or dataset hash; and any
mixture of historical and strict keys. **No ranking is produced unless all
eight accepted Test key sets are identical.**

## 6. The eight model identities (fixed)

| side | model | Track C provenance |
|---|---|---|
| LLM | **official-repository-based corrected MIFlu** | **retrained** (12 cells) |
| LLM | qwen_time_llm | re-scored |
| LLM | calf_llm | re-scored |
| LLM | timecma_llm | re-scored |
| non-LLM | nlinear | re-scored |
| non-LLM | dlinear | re-scored |
| non-LLM | patchtst | re-scored |
| non-LLM | itransformer | re-scored |

No model is added, removed, renamed or substituted.

### MIFlu configuration (frozen, never tuned after any result)

`T=104 · epochs=20 · batch=16 · lr=5e-4 · LoRA r=4 on c_attn · PEFT=1 ·
effective freeze · validation-only selection · Test read once · locked
checkpoint · atomic write` — all 12 cells identical.

## 7. Cell classification (96 cells)

| class | cells | models |
|---|---:|---|
| `RESCORE_ONLY` | 84 | the seven reusable models |
| `GPU_RETRAIN` | 12 | MIFlu only |

### Why the stage-6 MIFlu cells were rejected

They pass **every structural test** — strict containment, `author_966`, z-space,
canonical origins, correct `var_cols`, correct shapes — and are still
inadmissible, because `pred_miflu_*` is **byte-identical** to the A2 artefact
(`sha256 76b81b5b0dfa5bde`), i.e. the project's own from-scratch reconstruction,
which the brief forbids. **Key compatibility does not establish implementation
identity.**

## 8. Metric arithmetic

```
mse_z = mean over all valid (origin, feature, lead) of (y_pred_z - y_true_z)^2
mae_z = mean over the same of |y_pred_z - y_true_z|

average_MSE_4L = (MSE_L24 + MSE_L36 + MSE_L48 + MSE_L60) / 4
```

Champion = lowest **mean `average_MSE_4L` across matched seeds 42/43/44**.

One scorer for all eight models — no model is scored by its own code path.

## 9. Win rule

```
diff = A - B ;  A wins only if diff < 0 ;  ties within tolerance
```

## 10. Storage

`STORAGE_READY_FOR_966_STRICT_8MODEL`. Projected peak ~2.1 GB against ~19 GB
free. GPT-2 and Qwen2.5-1.5B base caches are **protected** and must not be
removed while Track C is active. Only the best validation-selected locked
checkpoint is retained per cell; no per-epoch checkpoints, no optimizer state.

## 11. Relationship to the other tracks

| track | what it is | champion? |
|---|---|---|
| **H** | 1025-row historical replacement, old self-built MIFlu, contaminated split | no — `PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE` |
| **R** | author-966 R1-B paper reproduction | no — `PARTIAL_REPRODUCTION` |
| **C** | **this contract** | **YES** |

Absolute scores are **never** compared across tracks.