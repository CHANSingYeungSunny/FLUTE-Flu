# R8 — CONTROLLED RERUN PLAN

## The intervention, in one line

```
FIXED   : qwen_time_llm, calf_llm, timecma_llm, nlinear, dlinear, patchtst, itransformer
REPLACED: gpt2_miflu   (project self-built  ->  official-repo-based MIFlu on the
                         historical 1025-row contract)
```

## Run matrix for the replaced slot

| Element | Value |
|---|---|
| model | official-repository-based MIFlu (R1-B architecture and mechanism) |
| dataset | July-2026 snapshot, **1025 rows**, SHA-256 to be pinned at run time |
| split | **717 / 102 / 206** |
| scaler | fitted on the 717 training rows only |
| horizons | 24 / 36 / 48 / 60, each an independent run |
| seeds | **42–51** (10), matching the historical frozen seed set |
| containment | strict |
| checkpoint selection | validation-only (B-5) |
| **fits** | **4 horizons x 10 seeds = 40** |
| storage | **159.4 MiB** on the locked path; 12.24 GiB on the full path — **use the locked path** |
| GPU estimate | 40 x measured 0.0533 h = **2.13 GPU-h** base; 2.56 with a 20 % buffer |

## Staging

```
S2a  CPU: pin the historical dataset hash, split, scaler and origin list      (0 GPU-h)
S2b  CPU: assert the new origins are IDENTICAL to the historical ones          (0 GPU-h)
S2c  GPU: 40 fits, one job at a time, locked checkpoints                       (2.13 GPU-h)
S2d  CPU: score with ONE scorer; re-aggregate the seven historical rows too    (0 GPU-h)
S2e  CPU: ranking comparison, per-horizon, per-seed, group summaries           (0 GPU-h)
```

**S2b is the control's integrity check.** If the new origins do not match the historical
ones exactly, the comparison is not controlled and must stop.

## Two tracks must be scored, not one

The historical comparison has **two stages that disagree**: Wave-1 validation (where
`gpt2_miflu` won) and the one-time Test/Holdout (where it lost). The replacement is
evaluated on **both**, because a replacement that flips only one of them is a different
finding from one that flips both.
