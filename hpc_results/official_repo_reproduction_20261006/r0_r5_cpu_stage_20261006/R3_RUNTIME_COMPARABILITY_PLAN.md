# R3 RUNTIME COMPARABILITY PLAN (Table IX)

## The paper's values

| Model | Training time |
|---|---:|
| ReILIF | **130 min** |
| MIFlu | **119 min** |

Both are **regional** (US-Region), and both were measured on a **GeForce RTX 3090**.

## Why exact equality is impossible and must not be attempted

| Factor | Paper | This project |
|---|---|---|
| GPU | GeForce RTX 3090 | **A100-SXM4-80GB** |
| dataset | US-Region | not released |
| Python / PyTorch | 3.9.18 / 2.1.0 | 3.9 / **2.5.1** |

Across different hardware, **exact time equality is not a reproduction criterion**. The
verdict for Table IX is **`HARDWARE_NORMALIZED_ONLY`**, and the paper separately warns against
extrapolating from a quick model.

## What to record instead

| Quantity | Source |
|---|---|
| wall time per fit | Slurm `Elapsed` |
| GPU-hours | allocated GPUs x elapsed |
| peak VRAM | `nvidia-smi` sampling inside the job |
| total parameters | the model contract |
| trainable parameters | the model contract (measured: 1,673,496 with LoRA) |
| checkpoint size | **measured (331,158,882 B on the full path)** — not projected |
| inference cost | per-origin forward time |
| embedding preparation | the text-asset load |

## Cost figure already measured

The **A2/LoRA configuration** costs a measured **0.0533 GPU-h per fit**; the **author's
released default** costs **0.2769 GPU-h per fit** because its ineffective freeze trains the
whole 82.7 M-parameter stack — a **19x** difference attributable purely to B-4.

## Status

`HARDWARE_NORMALIZED_ONLY`, and the regional half is `BLOCKED_BY_MISSING_DATA`.
