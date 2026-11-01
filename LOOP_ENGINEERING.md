# LOOP_ENGINEERING.md — the autonomous execution loop for this project

> Companion to `AGENTS.md`. `AGENTS.md` is *state*; this file is *process*.
> Every iteration of the agent must follow this loop. Keep both in sync.

---

## 0. Goal (the single objective everything serves)

Produce a **top-tier-journal-publishable** study with three finished parts, in this
dependency order:

1. **Perfect reproduction** — the paper's Table V reproduced under the author's
   released code, with every deviation disclosed. *Achieved: 4-horizon mean
   1.4995 vs 1.4355 = +4.5% (≤5% criterion met).* Remaining: MIFlu's K&S cells so it
   appears in the peak table.
2. **Benchmark** — a defensible multi-model comparison using four complementary
   rankings (accuracy, peak skill, efficiency, probabilistic skill) plus statistical
   significance, with **no leakage** and **no cross-scale champion claim**.
3. **Innovation** — a contribution built only after (1) and (2) are frozen.

**Definition of done:** `AGENTS.md` §11 is fully ✅, every artefact in §1.3 exists on
disk and is reproducible by a command, and every claim traces to a table.

---

## 1. The loop (one iteration)

```
READ  → AGENTS.md §1 (state), §7 (next actions), §13 (work breakdown)
PLAN  → pick the highest-value ❌/🟡 item; write it as a todo list
BUILD → make the smallest change that moves that item to ✅
VERIFY→ run the command that proves it; never mark ✅ without evidence
RECORD→ append to AGENTS.md §10 LEDGER; update §1/§1.3/§11/§13
REPEAT
```

Rules that make the loop work:

- **One item per iteration.** Parallel edits create untraceable state.
- **Verify before recording.** §10 rows need a command or file path as evidence.
- **Never leave a 🟡 in the ledger without a written reason.**
- **Escalate honestly**: if an item cannot be finished, convert it to ❌ with the
  blocking condition, not to a vague ✅.

---

## 2. Skills in play (what the agent is allowed/expected to use)

| Skill / tool | When |
|---|---|
| `read` / `grep` / `glob` | establish state before editing; never assume file contents |
| `write` / `edit` | produce artefacts; edit-then-verify, never blind overwrite |
| `pwsh` | run analysis, ssh to the HPC, inspect artifacts |
| `web_search` / `web_fetch` | **only** for external facts (model sizes, metric definitions); never for project state |
| `todo_write` | one entry per planned action of the current iteration |
| subagents / workflow | only for genuinely independent fan-out (e.g. many-file audits) |

**Evidence hierarchy:** file on disk > command output > this file > model memory.
If they conflict, the disk wins and the file gets corrected.

---

## 3. RAG (what to retrieve, and from where)

This project uses **explicit file retrieval**, not a vector store. The retrieval order
is fixed:

1. `AGENTS.md` — state, rules, ledger, work breakdown
2. `docs/METHODOLOGY_METRICS_AND_SPLIT.md` — why each metric and split was chosen
3. `paper_tables/*.csv` — the measured numbers
4. `hpc_results/expanded_runs/**/pred_*.npz` — the raw predictions (ground truth of
   every table)
5. `docs/STATUS_20261031.md` — reproduction fix log
6. `reference_papers/MIFlu_*.md` — the essay itself (Table V, VI, VIII, IX)

Never re-derive a number that exists in (3); never contradict (1) without measuring.

---

## 4. Harness facts the loop depends on

| Fact | Consequence for the loop |
|---|---|
| `AGENTS.md` is auto-injected as workspace instructions | put must-know facts there, not in a skill |
| HPC `stingy` = 1 running + 1 pending | chain with self-requeue, never queue 2 |
| HPC `gpu_a100` is congested (days) | prefer `stingy` or `gpu_v100s` for GPU work |
| Compute nodes have **no internet** | download on the login node, run offline |
| `HF_HUB_CACHE` must be set | else "weights exist but not found" |
| Local analysis needs no GPU | do post-processing while jobs queue |
| Windows: `scp` path must not end with `\`; `ssh` mangles `$()` | write remote scripts to files |

---

## 5. Constraints (hard, inherited from AGENTS.md §2)

1. Reproduction metric = 7-variable aggregate MSE/MAE in z-space. Never substitute.
2. Benchmark peak metric = PTE/PIE on ILITOTAL (de-normalised). 7-var aggregate is a
   loss, not a series — it cannot be de-normalised.
3. **DLinear excluded everywhere.**
4. Checkpoint selection = **validation**; never replicate the author's test selection.
5. A-track vs B-track numbers never comparable.
6. Text-pathway contradiction stays UNRESOLVED.
7. No "we beat the paper" claim.
8. MSE ≠ accuracy; report both champions.
9. **Every claim must trace to a table or a command.**

---

## 6. Current iteration queue (mirrors AGENTS.md §13, highest value first)

| # | item | why now |
|---|---|---|
| 1 | Merge MIFlu into the champion tables + regenerate figures | the paper's主角 is missing from its own benchmark table |
| 2 | seasonal-naive baseline + relative-improvement column | item ② of the cross-scale methodology is the only missing leg |
| 3 | Pareto frontier **figure** (MSE vs params, frontier line) | ① is meant to be the headline visual |
| 4 | Reproducibility protocol (revision pin + manifest + frozen feature table) | required before any LLM arm is added |
| 5 | National training-time table (NOT Table IX — see below) | cheap, from existing logs |
| 6 | Rolling origin (5 folds) | needs retraining; prerequisite for credibility |
| 7 | 8 new LLM arms | need the protocol from #4 and free GPU |

### ⚠️ Correction recorded 2026-11-01: Table IX ≠ national timings

**Table IX is the training time of the *regional* ILI models.** Its rows correspond to
the Table VI run configuration (`T=20`, `L∈{2,3,5,10,13,15,20}`, `K=4`, 50 epochs,
batch 32). Therefore **Table IX cannot be produced before Table VI is actually
executed and timed.** What we can produce now is a *national* training-time table
under the Table IV/V configuration — a different table, and it must not be labelled
Table IX.

---

## 7. Failure protocol

- A failed job → record the reason in `AGENTS.md` §10, then continue the queue.
- A wrong claim of mine → correct it in §10 with the date and the corrected statement
  (see the Table IX row above; earlier I wrongly said "IX now, easy").
- A blocked item → convert to ❌ with the blocking condition, never silently drop.
- If two sources disagree → measure, then record which one was right.
