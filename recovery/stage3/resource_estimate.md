# Stage 3 — resource estimates (measured vs extrapolated)

Evidence base: `hpc_results/paper_exact/training_miflu_log_514859.txt` (966-row
job) and `hpc_results/paper_exact/REPLICATION_VERDICT.md` (1025-row 8-17 run).
Both ran the project's corrected MIFlu on NVIDIA A100-SXM4-80GB.

## Measured (logged, not assumed)

| Quantity | Value | Source |
| --- | --- | --- |
| Hardware | NVIDIA A100-SXM4-80GB | log 514859 |
| GPU memory | ~0.88 GB (fits many copies per node) | log 514859 |
| Epoch time (corrected MIFlu, LoRA r=4, batch 16) | ~7.8–8.3 s | log 514859 (966 rows) |
| Epochs per rep | 20 | configs.py |
| Reps in the *paper* protocol | 10 | configs.py (`num_repetitions=10`) |
| Reps in the *A2 minimum* protocol | 3 seeds × 1 rep | a2_frozen_protocol.json |

## Extrapolated (derived from the measured epoch time)

Per-fit wall time for corrected MIFlu / no-text (20 epochs, 1 seed):

```
20 epochs × ~8 s = ~160 s ≈ 2.7 min per fit
```

| Matrix leg | Fits | Est. wall time (serial) | Est. GPU-hours |
| --- | ---: | ---: | ---: |
| A0 diagnostic (1×L24×S42) | 1 | ~2.7 min | ~0.05 |
| A2-MIFlu (4L × 3S) | 12 | ~32 min | ~0.53 |
| A2-NOTEXT (4L × 3S) | 12 | ~32 min | ~0.53 |
| A2-NLIN (4L × 3S) | 12 | UNMEASURED (linear model; expected ≪ MIFlu) | <0.05 |
| A2 naive (deterministic) | 8 | <1 min | <0.02 |
| **Total** | **45** | **≲ 70 min serial** | **≲ 1.2 GPU-h** |

With 4-way concurrency (A100 has ample headroom at 0.88 GB/fit), total **wall
time ≲ 20 minutes**. The whole A2 matrix is ~1 GPU-hour-class, far below any
budget concern.

## UNMEASURED (state honestly; do not run now)

- **NLinear epoch time** on 966 rows — not logged. Linear T→L is trivial; a
  bounded pilot (1×L24×S42, ~seconds) would confirm. Marked `UNMEASURED`.
- **A0 (author code) epoch time** — never run. The author code is a *full
  fine-tune* (freeze no-op, PEFT off), not LoRA, so per-epoch cost will be
  higher than the project's 8 s. Bounded pilot: 1×L24×S42 first; do not
  extrapolate the full sweep from it.
- **Storage**: checkpoints are LoRA-scale (few MB) except A0 full fine-tune
  (a 6-layer GPT-2 ~124M params ≈ 500 MB per checkpoint). Predictions/CSVs are
  KB-scale. Total well under 1 GB for the A2 matrix; A0 depends on how many
  checkpoints are retained.

## Retries / search

None of these runs sweep hyperparameters, prompts, or seeds beyond the frozen
list; there is no tuning loop. Retries are only for OOM/crash, unlikely at
0.88 GB. No search budget is allocated.

## Basis statement

The ~8 s/epoch figure is **measured**; per-fit and total times are
**extrapolated** from it by multiplication. NLinear/naive/A0 figures are
**UNMEASURED** and bounded by pilot proposals, not asserted.
