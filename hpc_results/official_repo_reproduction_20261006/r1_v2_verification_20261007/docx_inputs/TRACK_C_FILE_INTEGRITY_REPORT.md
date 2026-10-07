# TRACK C — FILE INTEGRITY REPORT

Generated from the validated Track C results. **Nothing was re-scored, re-selected or re-run.**

## Integrity facts

- scored cells: **96** (96 expected) — all present
- cells rejected by the canonical scorer: **0**
- seed-42 gate: **22 PASS / 0 FAIL**
- champion: **miflu** — mean Test average_MSE_4L **1.865155** (SD 0.091556, 3 matched seeds)
- Test was never used for fitting or checkpoint selection in any cell (`test_access_during_fit = False` on all 12 MIFlu manifests)
- rejected stage-6 MIFlu recorded in `TRACK_C_MODEL_IDENTITY.csv` (sha 76b81b5b0dfa5bde) and excluded from the ranking

## Quota (authoritative, from mmlsquota — NOT filesystem free space)

- **home**: used 31 GB / soft 50 GB / hard 100 GB, grace `none`, headroom to soft **19 GB**
- **scratch**: used 285 GB / soft 300 GB / hard 1024 GB, grace `none`, headroom to soft **15 GB**

## Group-mean caveat (both conclusions preserved)

1. the corrected official-repository-based MIFlu is the **best individual model**;
2. the **non-LLM group mean is better** than the LLM group mean.

- LLM: 3.817505
- non-LLM: 3.075638