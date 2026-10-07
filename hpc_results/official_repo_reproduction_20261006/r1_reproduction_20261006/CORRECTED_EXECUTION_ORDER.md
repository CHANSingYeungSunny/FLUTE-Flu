# CORRECTED EXECUTION ORDER

Generated 2026-10-06. **Supersedes** the A2-F-first ordering used in the previous rounds.

---

## 1. The mandatory sequence

```
R1  Reproduce the original MIFlu paper on the author's official GitHub repository
      |
      +-- R1-A  literal released-code reproduction        (what the repo produces)
      +-- R1-B  paper-intended reconstruction             (the reproduction attempt)
      +-- R1-C  sensitivity analysis for UNRECOVERED items (declared, bounded)
      |
R2  Verify whether the reproduction genuinely matches the paper
      |
      +-- verdict: EXACT_OR_NEAR / PARTIAL / EXECUTABLE_BUT_NOT_REPRODUCED / NOT_REPRODUCIBLE
      |
R3  Inspect and reconstruct the OLD pre-official-repository 4 LLM vs 4 non-LLM comparison
      |
R4  Replace ONLY the old self-built MIFlu with the reproduced official-repository MIFlu
      |
R5  Rerun the SAME 4 LLM vs 4 non-LLM comparison under a defined replacement protocol
      |
R6  Compare old vs new; identify how the official MIFlu changes the ranking
```

Each stage's output is the next stage's input. **No stage may be skipped**, and none may
be replaced by a different experiment.

---

## 2. Where the completed work sits

| Completed work | Status under the corrected order | May be used for |
|---|---|---|
| **F1** six-model A2-F pilot | `EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT` — **frozen** | supplementary evidence; cost data; the corrected text-path verification |
| **A2 / stage-5 / stage-6** eight-model A2-basis benchmark | **A2 basis**, corrected reconstruction — *not* R5 | input to **R3** as a record of what the *new* codebase produced; not a replacement for the old comparison |
| **A0-R** released-code replays (4 horizons feature-0) | released-code behaviour evidence | input to **R1-A** |
| **Historical Track B** (`innovation_deploy_root_v3_*`, `results/v3_clean`) | preserved, `UNSAFE_TO_DELETE` | input to **R3** |
| Text-path probes | verified evidence | input to **R1-B** (they establish that the released text path is inert) |
| Post-run audit + budget audit | reference | R1 budget planning |

**None of these satisfies R1, R4, R5 or R6.**

---

## 3. Stage detail

### R1 — reproduce the paper (three tracks, run in this order)

| Track | What it is | Depends on | GPU |
|---|---|---|---|
| **R1-A** | literal official released-code execution, behaviour preserved (feature-0, Test-selected, inactive text path) | already substantially done at four horizons | done |
| **R1-B** | paper-intended reconstruction on the official repository: restore functional text use, the paper target/aggregation contract, LoRA, and the best recoverable training configuration | the contract audit (§4 of this round) | needs authorization |
| **R1-C** | bounded sensitivity analysis over genuinely `UNRECOVERED` items, with a **predeclared** candidate set | R1-B | needs authorization |

**R1-C is not accuracy hunting.** It runs a small predeclared candidate set justified by
documentary evidence, and its results are reported as *sensitivity*, never as *reproduction*.

### R2 — verify

Report per horizon and per metric: paper value, reproduced mean, reproduced SD, absolute
difference, relative difference, repetition count, and the exact contract. Apply the
verdict scale in `R1_REPRODUCTION_SUCCESS_GATES.md`.

**A one-horizon or one-run match is not success.** The paper reports ten repetitions, so a
paper-level success claim must address ten repetitions unless strong evidence establishes
a different interpretation of the repetition mechanism.

### R3 — inspect the old comparison

Recover, from the preserved pre-2026-09-24 artifacts:
- the exact model set (4 LLM + 4 non-LLM);
- the dataset(s) and row counts;
- the evaluation contract and metric;
- the split, scaler, seeds and horizons;
- the old results and ranking;
- each model's implementation identity and provenance.

**Confirmed constraint from the post-run audit**: Track-B artifacts contain **no `.npy`
predictions** and **no entry-point script**, so the old numbers can be *read* but not
*recomputed*. R3 must therefore reconstruct the comparison's *definition* rather than
re-score its outputs.

### R4 — replace only MIFlu

Everything else is held fixed. The replacement must record:
- which old MIFlu artifact is being replaced;
- which R1 output replaces it;
- what does **not** match between old and new (dataset vintage, rows, protocol) and how
  that mismatch is handled;
- why the swap is attributable.

### R5 — rerun 4 vs 4

Same model set, same protocol definition, same evaluation logic — with the reproduced
MIFlu in place. Requires its own run matrix and authorization.

### R6 — compare

Report the old ranking, the new ranking, and the per-model and per-rank changes, with an
explicit statement of which differences are attributable to the MIFlu swap and which are
attributable to any unavoidable protocol drift.

---

## 4. Immediate next actions (this round)

| # | Action | Status |
|---|---|---|
| 1 | freeze F1, cancel F2 | ✅ done (`F1_SCOPE_CORRECTION.md`) |
| 2 | restore the primary objective | ✅ done (this file + `PRIMARY_OBJECTIVE_RESTORATION.md`) |
| 3 | resolve the R1 reproduction contract | ✅ `R1_PAPER_REPRODUCTION_CONTRACT.md` |
| 4 | re-verify the paper target values | ✅ `R1_PAPER_TARGET_VALUES.csv` |
| 5 | classify every required setting | ✅ `R1_HYPERPARAMETER_EVIDENCE.csv` |
| 6 | document paper-vs-code conflicts | ✅ `R1_PAPER_CODE_CONFLICTS.md` |
| 7 | list what remains unrecovered | ✅ `R1_UNRECOVERED_INFORMATION.md` |
| 8 | prepare the minimal reproduction pilot | ✅ `R1_REPRODUCTION_PILOT_PLAN.md` + matrix + budget + gates + Slurm plan |
| 9 | submit GPU work | ❌ **NOT DONE — requires a new reproduction-specific authorization** |

---

## 5. Budget rule for R1

The F1 authorization is **exclusive** to the F1 six-model contract. Its unspent
0.35 GPU-h **may not** fund R1. R1 requires a **new, reproduction-specific** authorization,
which is requested in `R1_REPRODUCTION_GPU_BUDGET.md` and **not yet granted**.