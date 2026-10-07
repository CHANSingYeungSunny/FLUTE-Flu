# F1 SUBMISSION ORDER

Generated 2026-10-06. **Nothing has been submitted.**

## 1. Constraint that dictates the design

```
sacctmgr show qos partition-stingy  ->  MaxSubmit=1  MaxJobsPU=1
```

**One job at a time.** A multi-element `--array` is rejected outright
(`QOSMaxSubmitJobPerUserLimit`, observed on job 606363). Therefore F1 submits **9 jobs
sequentially**, each awaited before the next.

## 2. Order

| # | Job | Content | Device | Why here |
|---:|---|---|---|---|
| 0 | CPU dry-run | `f1_score_all.py --allow-partial` over whatever exists | CPU | proves the scorer and gates work before any GPU time |
| 1 | GPU index 0 | corrected MIFlu L=24 | a100 | primary arm first: if the wave is interrupted, the most informative cells exist |
| 2 | GPU index 1 | corrected MIFlu L=36 | a100 | |
| 3 | GPU index 2 | corrected MIFlu L=48 | a100 | |
| 4 | GPU index 3 | corrected MIFlu L=60 | a100 | |
| 5 | GPU index 4 | no-text MIFlu L=24 | a100 | the matched control, so the mechanism contrast completes before the cheap arms |
| 6 | GPU index 5 | no-text MIFlu L=36 | a100 | |
| 7 | GPU index 6 | no-text MIFlu L=48 | a100 | |
| 8 | GPU index 7 | no-text MIFlu L=60 | a100 | |
| 9 | CPU wave | NLinear ×4, DLinear ×4, Last Value ×4, Seasonal Naive ×4, **then independent scoring of all 24 artefacts** | CPU (0 GPU-h) | must follow the GPU wave because it scores their artefacts |

### Why this differs slightly from the brief's suggested order

The brief proposed CPU scorer tests → Last Value → Seasonal Naive → NLinear → DLinear →
MIFlu → no-text → final scoring.

F1 runs the **GPU arms first** instead, for one reason: **stingy allows only one job at a
time, so the total wall clock is the same either way**, but if the quota or the session
runs out mid-wave, front-loading the two MIFlu arms leaves the *primary comparison* (full
vs no-text, which is the mechanism question) complete rather than leaving it as the
missing half. The cheap deterministic arms are placed last precisely because they are
cheap to redo.

The CPU dry-run at step 0 is retained from the brief's spirit: the scorer and the gates
are validated before the first GPU second is spent.

## 3. Expected completion criteria

| Stage | Done when |
|---|---|
| GPU wave | all 8 elements COMPLETED, each with a checkpoint in `f1/ckpt/<tag>/` and `fit_exit_code=0` in its manifest |
| CPU wave | 16 deterministic/linear artefacts written, then `f1_score_all.py` exits 0 |
| pilot COMPLETE | `f1_gate_report.json` shows `status = COMPLETE` |

## 4. Wall clock

```
8 GPU fits x 192 s          = 1536 s
8 CPU model fits x 40 s     =  320 s
8 naive runs x 15 s         =  120 s
scoring                     =   60 s
                            --------
total                       = 2036 s  =  ~34 min
```
Plus queue gaps at MaxSubmit=1; budget **45 minutes** end to end.

## 5. Launcher

`scripts/run_f1_sequential.sh` implements exactly this order, submits **one element at a
time**, waits for each terminal state, appends to `f1/manifests/SUBMISSION_LOG.tsv`, and
is safe to re-run. It submits nothing by itself.
