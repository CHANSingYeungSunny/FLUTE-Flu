# HISTORICAL QWEN CHECKPOINT-REDUCTION PROVENANCE

Generated 2026-10-06. Read-only evidence. **No checkpoint was loaded into memory** —
all conclusions below come from file sizes, names, formats, inode metadata and full
SHA-256, per the brief's constraint.

---

## 1. Headline

The Qwen artifacts dominate the historical deployment (**138.07 GiB of 201.7 GiB of
checkpoint data**), and they were reduced by a factor of **4,167×** for deployment:

```
full training checkpoint   6,176,478,657 B   5.75 GiB
compact export                 1,482,128 B   1.41 MiB
                            ratio  4,167x
```

A 1.41 MiB export cannot contain a 1.5 B-parameter base model. **The base model is
therefore an external dependency of every reduced Qwen artifact.**

---

## 2. The reduction pipeline is visible in the file names

Only **four** distinct checkpoint basenames exist in the entire family:

| Basename | Count | Total size | Interpretation |
|---|---:|---:|---|
| `best_val_mse.pt` | 447 | 201.26 GiB | full training checkpoint (one per run) |
| `compact.safetensors` | 97 | 0.29 GiB | **the reduced deployment artifact** |
| `compact.pre.safetensors` | 49 | 0.15 GiB | pre-reduction snapshot |
| `compact.post.safetensors` | 1 | ~0.01 MiB | post-reduction single record |

The `compact.pre` → `compact` → `compact.post` progression is direct evidence that a
**checkpoint-reduction step was run and logged**, not merely that outputs were trimmed.

---

## 3. Measured reduction per artifact class

From `durable_sim/<arm>__<model>__L<hh>__seed<n>__w1/compact.safetensors`:

| Model | compact export | full checkpoint | ratio |
|---|---:|---:|---:|
| `qwen_time_llm` | **1.41 MiB** | 5.75 GiB | **4,167×** |
| `gpt2`/`miflu` family | 3.94 MiB | 313 MiB | ~79× |
| `calf_llm` | 7.56 MiB | — | — |
| `timecma_llm` | 5.31 MiB | — | — |
| `patchtst` | 0.34 MiB | — | — |
| `itransformer` | 0.29 MiB | — | — |
| `nlinear` | 0.01 MiB | — | — |

Full table: `HISTORICAL_QWEN_CHECKPOINT_DEPENDENCIES.csv` (215 rows).

Interpretation: the export size tracks the **trainable delta**, not the model. For
`nlinear` (2.5–6.3 k parameters) 0.01 MiB is the whole model; for `qwen_time_llm`
(370 k–758 k trainable out of a frozen 1.5 B base) 1.41 MiB is the adapter/head only.
That is the signature of an **inference-only export with the base model left outside**.

---

## 4. Techniques — status of each

`HISTORICAL_CHECKPOINT_REDUCTION_TECHNIQUES.csv` records 27 candidate techniques with an
evidence status. Summary:

| Status | Count | Examples |
|---|---:|---|
| `EVIDENCE_SUPPORTED` | 10 | optimizer-state removal, best-checkpoint-only retention, safetensors conversion, inference-only export, external base-model dependency, custom checkpoint filtering, base-model deduplication, intermediate-checkpoint removal, scheduler-state removal, one-checkpoint-per-run retention |
| `LIKELY` | 2 | LoRA adapter-only saving, unused-training-tensor removal |
| `PLAUSIBLE_BUT_UNVERIFIED` | 1 | shared Hugging Face cache (`HF_HOME` set externally; not inspected) |
| `UNKNOWN` | 6 | LoRA merging, fp32→fp16, fp32→bf16, fp16→bf16, tokenizer dedup, config dedup |
| `NOT_EVIDENCED` | 6 | INT8, INT4, GPTQ, AWQ, bitsandbytes, shard consolidation |
| `RULED_OUT` | 2 | **symbolic links (0 found)**, **hard links (0 found)** |

**Quantization is not evidenced.** No `.gguf`, `.onnx`, GPTQ or AWQ artifacts exist; the
only formats present are `.pt` and `.safetensors`. Any claim that the Qwen artifacts were
quantized is unsupported and must not be made.

**dtype conversion is UNKNOWN and stays unknown**: distinguishing fp32 from fp16/bf16
requires reading a tensor header, which would mean loading checkpoint metadata that the
brief asked to avoid. Note that a 5.75 GiB full checkpoint for a 1.5 B model is
consistent with **fp32** (1.5e9 × 4 B = 6.0 GB), which is weak evidence *against*
half-precision conversion of the full file — recorded as an inference, not a measurement.

---

## 5. The 17 questions, answered

| # | Question | Answer |
|---|---|---|
| 1 | Historical model identity | `qwen_time_llm` — the project's **Time-LLM-INSPIRED adaptation on Qwen2.5-1.5B**, not the official Time-LLM |
| 2 | Historical experiment identity | the Track-B `primary` arm, horizons 24/36/48/60, seeds 42+, arms `primary`/`ablation`/`negative_control` |
| 3 | Predates the official repo pull? | **YES** — latest mtime 2026-09-21, clone 2026-09-24 |
| 4 | Independently loadable? | **NO** — the compact export is 1.41 MiB; a base model must be supplied |
| 5 | Separate base model required? | **YES** |
| 6 | LoRA adapter required? | very likely, but whether the adapter is stored separately from the head is `UNKNOWN` |
| 7 | Adapter appears merged? | `UNKNOWN` — cannot be determined without loading tensors |
| 8 | External tokenizer required? | **YES** — 0 tokenizer files in the whole family |
| 9 | HF cache required? | very likely (`HF_HOME` external); `PLAUSIBLE_BUT_UNVERIFIED` |
| 10 | Symlink targets required? | **NO** — 0 symlinks exist |
| 11 | Hard-linked data involved? | **NO** — 0 files with link count > 1 |
| 12 | Historical custom code required? | **YES** — the self-built `scripts/` shipped inside each directory |
| 13 | Absolute paths embedded? | `UNKNOWN` — not inspected (would require loading state dicts) |
| 14 | Reconstructable? | the *full* checkpoint is present, so the model can in principle be re-exported; the *export procedure* is not documented |
| 15 | Unique? | **YES** — all 24 Qwen checkpoints > 5 GB have distinct SHA-256 |
| 16 | Only deployment-ready checkpoint for that model? | **LIKELY** — the `durable_sim` compact exports are the only reduced artifacts present |
| 17 | Suitable only for historical recovery? | **YES** |
| 18 | Would using it in A0-R / A1-P / A2-F create an invalid mixture? | **YES** |

---

## 6. Compatibility verdict

```
INCOMPATIBLE_ACROSS_TRACKS_UNLESS_PROVEN_OTHERWISE
```

**Reason**: these artifacts (a) belong to the self-built lineage, (b) predate the official
repository, and (c) were produced by a checkpoint-reduction step that changed the artifact
relative to the trained model. Scoring a reduced Track-B checkpoint inside an A2-F
comparison would silently change the model under test while claiming the new protocol —
a protocol mixture, not a comparison. No such proof exists, so the default applies.

---

## 7. Preservation

All Qwen artifacts: **`UNSAFE_TO_DELETE`** / **`NOT_AUTHORIZED_FOR_DELETION`**.
Nothing was opened, loaded, moved, copied, re-exported or modified.