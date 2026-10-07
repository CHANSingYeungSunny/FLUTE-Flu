# Stage 3 — supervisor brief (concise)

## Answer to Ben (verbatim intent preserved)

Three things differ, and the controlled author-data comparison is what
separates them:

1. **Data**: the author's 966-row vintage (`2002w40–2021w13`) vs our 1,025-row
   July snapshot (`2002w01–2021w52`, with a 19-week hole in 2002). Same source
   (CDC FluView), different span and 72 overlapping weeks with value revisions.
2. **Implementation**: the released code (`main_ILI_lora.py`) is materially
   buggy (text inert, feature-0 Test, Test-in-loop); our MIFlu is a corrected
   reconstruction (text-first, 7-channel, LoRA+freeze, validation selection).
3. **What a rerun isolates**: NLinear vs MIFlu is *not* the text causal effect.
   Full MIFlu vs its no-text ablation is the relevant within-model contrast.
   Running all three on the same 966-row data under one protocol separates
   "data difference" from "implementation difference" from "text effect".

We do **not** claim the paper is disproved. We claim the released code does not
execute the pipeline the paper describes, and our corrected model on the author
data is the right vehicle to test the paper's own number.

## Corrected finding (supersedes an earlier Stage-2 claim)

The project **has already run** the 966-row author data with its corrected
model — job 514859 (L24 MSE_All 2.238) and control966 (L24 1.379) — plus the
1,025-row paper-window run (MSE_All 2.593/3.341/3.237/3.559, 1.7–2.6× paper).
What remains genuinely undone: **A0** (replay the released code verbatim) and a
**coherent A2 matrix** (MIFlu / no-text / NLinear / naive on 966 rows). See
`hpc_results/paper_exact/REPLICATION_VERDICT.md`.

## Calendar-gap consequence (prioritized; corrected)

The 19-week hole (2002 w21–39) sits at **row 20**, before any forecast origin.
Its only effect on the 1,025-row data: **20 train origins** (rows 0–19) get a
104-row lookback that spans ~123 calendar weeks. **Zero** targets cross the
gap, **zero** lead-mismatches, and seasonal-naive lag-52 is **fully
calendar-valid** (all target rows ≥ 104 are in the dense region). The author
966-row data has **no gap at all**. Consequence: no gap-driven rerun of
training/selection is required; the 20 affected train origins are a negligible
receptive-field inflation, preserved as a disclosed limitation.

## Recommended minimum scope (45 rows)

- **A0** diagnostic: 1 fit (L24, seed 42, released defaults) — answers "what
  does the code compute", not a benchmark.
- **A2** comparison: 36 learned fits (4 horizons × 3 seeds {42,43,44} ×
  {MIFlu, no-text, NLinear}) + 8 deterministic naive evals. This is the
  minimum, not the 10-rep paper reproduction.
- **B/C**: no new runs. B already frozen (v3_clean + 8-17); C holdout is
  `EXPOSED`, no untouched interval identified.

## Old-result status

- v3_clean results and the 8-17/paper_exact runs: **REUSE** (preserved; their
  limitation is that they are the corrected model, not A0).
- Nothing is `SUPERSEDED` by this brief; the corrected model's 966-row runs are
  **EVIDENCE**, and only A0/A2 remain `TO-RERUN-PROPOSED`.

## Decisions blocking runs

| Decision (D) | Affected runs | Recommended default |
| --- | --- | --- |
| D-adapter | all A2 (apply `author_data_adapter.patch`) | apply after `git apply --check` |
| D-a0-env | A0-01 | approve GPU node + confirm gpt2 cache |
| D-nlinear | A2-NLIN-*, A2-LV-*, A2-SN-* (new runners) | authorize the two thin runners |
| D-split | A2 (676/97/193 vs 676/96/194) | author 676/97/193 (matches author convention + §2 window table) |
| D-target | metric definition | keep frozen `average_MSE_4L` (7-var z-space) |
| D-scope | whether to expand beyond A0+A2 | keep A0+A2; defer 8-model/regional/few-shot |
| D-compute | GPU-hour budget | ~1.2 GPU-h ≪ any cap |
| D-holdout | C | no new Test evaluation; no fresh interval exists |
| D-naming | corrected variant name | "project reconstruction with documented deviations" |

No D above blocks the *preparation* (all artifacts are written); each D only
blocks its listed runs.

## Closure statement

No GPU jobs, training, or new Test evaluation were launched. All Stage 3
artifacts are prepared under `recovery/stage3/`; the exact commands are ready
or explicitly marked `BLOCKED_PENDING_PATCH` / `BLOCKED`.
