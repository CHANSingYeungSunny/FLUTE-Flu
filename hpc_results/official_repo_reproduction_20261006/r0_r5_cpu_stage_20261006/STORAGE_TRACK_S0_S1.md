# STORAGE TRACK S0–S1

Generated 2026-10-06. S0 audits the current storage state; S1 recovers how the historical
project avoided storage overload.

**Source**: the read-only HPC audit already performed this project (jobs **606430** metadata,
**606432** full content hashing) — no new HPC job was needed.

---

## S0 — Current storage state

### Quotas (measured)

| Filesystem | Used | Quota | Limit | Grace | Status |
|---|---:|---:|---:|---|---|
| **home** | 28,172,304 KB ≈ **26.86 GB** | 52,428,800 KB = **50 GB** | 100 GB | none | ✅ OK |
| **scratch** | 433,264,576 KB ≈ **413.2 GB** | 314,572,800 KB = **300 GB** | 1000 GB | **expired** | ❌ **OVER by ≈113 GB** |

**Scratch is effectively read-only for this account**: writes fail intermittently with
`Disk quota exceeded` (observed on an `scp` of a 10 KB file). It has **not** improved since
the earlier measurement.

### Where the scratch usage sits

| Path | Size |
|---|---:|
| `/gpfs1/scratch/sychan552` (total) | **443.6 GB** |
| `…/CHATTIME` | 190 GB |
| **`innovation_deploy_root_v3_*` (19 dirs)** | **204.6 GiB ≈ 219.7 GB** (46 %) |

### The decisive S0 finding — **deduplication cannot help**

| Method | Reclaimable |
|---|---:|
| naive (same size **and** same basename) | 186.7 GiB — ❌ refuted |
| **full SHA-256, all 594 checkpoint files** | **66.7 MiB (0.032 %)** |
| small files (< 4 MiB; 20,792 hashed) | 245.9 MiB |
| **total** | **≈ 312.6 MiB = 0.1 % of the overage** |

**All 24 files larger than 5 GB have distinct SHA-256 values** (138.06 GiB of Qwen, no
duplicates). The family is 204.6 GiB of essentially unique content.

Also measured: **0 symlinks, 0 hard links, 0 shared inodes** across the family, so apparent
size == actual usage exactly.

### Other S0 facts

| Item | Value |
|---|---|
| inode / file usage | home 91,307 files against a 0 file-count quota (unlimited) |
| model caches | `HF_HOME=/home/sychan552/.cache/huggingface` (external to the deploy family) |
| default output location for future work | **`$HOME`** — not scratch |
| scratch cleanup | **not authorised and not performed** |

---

## S1 — How the historical project avoided storage overload

The historical deployment embedded a **checkpoint-reduction pipeline**, visible in the file
names. The entire family contains only **four distinct checkpoint basenames**:

| Basename | Count | Total | Interpretation |
|---|---:|---:|---|
| `best_val_mse.pt` | 447 | 201.26 GiB | full training checkpoint (one per run) |
| **`compact.safetensors`** | 97 | **0.29 GiB** | **the reduced deployment artifact** |
| `compact.pre.safetensors` | 49 | 0.15 GiB | pre-reduction snapshot |
| `compact.post.safetensors` | 1 | ~0.01 MiB | post-reduction record |

The `compact.pre → compact → compact.post` progression is direct evidence that a
**reduction step was run and logged**, not merely that outputs were trimmed afterwards.

### The measured reduction

| Model | compact export | full checkpoint | ratio |
|---|---:|---:|---:|
| **`qwen_time_llm`** | **1.41 MiB** | 5.75 GiB | **4,167×** |
| gpt2/miflu family | 3.94 MiB | 313 MiB | ~79× |
| calf_llm | 7.56 MiB | — | — |
| timecma_llm | 5.31 MiB | — | — |
| patchtst | 0.34 MiB | — | — |
| itransformer | 0.29 MiB | — | — |
| nlinear | 0.01 MiB | — | — |

**The export size tracks the trainable delta, not the model.** That is the signature of an
**inference-only export with the base model left outside** — and it explains why a 1.5 B
Qwen deployment fits in 1.41 MiB.

### Techniques — status

| Status | Count | Examples |
|---|---:|---|
| `EVIDENCE_SUPPORTED` | 10 | optimizer-state removal, best-checkpoint-only retention, safetensors conversion, inference-only export, external base-model dependency, custom checkpoint filtering, intermediate-checkpoint removal, scheduler-state removal |
| `LIKELY` | 2 | LoRA adapter-only saving, unused-training-tensor removal |
| `PLAUSIBLE_BUT_UNVERIFIED` | 1 | shared HF cache |
| `UNKNOWN` | 6 | LoRA merging, fp16/bf16 conversions, tokenizer/config dedup |
| `NOT_EVIDENCED` | 6 | INT8, INT4, GPTQ, AWQ, bitsandbytes, shard consolidation |
| `RULED_OUT` | 2 | **symlinks (0)**, **hard links (0)** |

**Quantization is not evidenced anywhere.** No `.gguf`, `.onnx`, GPTQ or AWQ artifacts
exist. **Any claim that the Qwen checkpoints were quantized is unsupported.**

### The one reduction this project already uses

`save_locked_ckpt()` in `train_backbone_966.py` stores **only tensors with
`requires_grad=True`**, and writes a **frozen-key sidecar** so the reconstruction can be
*proven* rather than trusted. That is the historical technique, still in use.

**Note for the R1-B budget**: `train_miflu.py` (a different trainer) stores the **full**
`state_dict`, which is why the F1 checkpoints were **329 MB each** rather than the 3.9 MB
projected. Any R1-B storage estimate must use the measured 329 MB, not the projection.

---

## What this means for the reproduction and replacement stages

| Stage | Storage consequence |
|---|---|
| R1-B pilot (4 fits) | if `save_locked_ckpt` is used: ~16 MB. If full `state_dict`: **~1.3 GB** |
| R1-B 10-repetition expansion (40 fits) | ~160 MB · or **~13 GB** with full state_dict |
| historical replacement (40 fits on the 1025 contract) | same order; **must use the locked-checkpoint path** |
| all outputs | **`$HOME`** — 23.1 GB headroom available |
| scratch | **must not receive new output** |

**S2–S5 are not yet produced.** `STORAGE_READY` is therefore **not issued**, and no GPU job
may be submitted until it is.

### The storage guard the future scripts must implement

```
projected_output  = fits x measured_checkpoint_size + predictions + logs
required_headroom = max(1 GB, 10 x projected_output)
refuse to run if (home_quota - home_used) < required_headroom
```

The F1 scripts already carry a 1 GB-headroom version of this guard; the R1-B scripts must
carry it too, **and must use the measured checkpoint size rather than a projection** — the
F1 projection was wrong by 85×.