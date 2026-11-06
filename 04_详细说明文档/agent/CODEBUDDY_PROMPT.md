# AGENT HARD RULE (read AGENTS.md first)

---

## HARD RULE — Burgundy login node (2026-11-05 incident, applies to EVERY agent)

**All model work must run via `sbatch` on a compute node.** Never run inference,
`torch.load`, `import torch/transformers`, recursive `du -sh` or downloads on the
login node — that caused a ~2-hour outage on 2026-11-05. Login node is only for
`squeue`/`sacct`/`scontrol`/`mmlsquota`/short `ls`/`cat`.

If ssh authenticates but returns zero bytes: disable
`ServerAliveInterval/CountMax`, open ONE connection with no retry loop, and issue
`pkill` as the **FIRST** command in the first shell window (a `D`-state task keeps
`SIGKILL` pending; `ps` first lost a real window). Never `scancel`.

Full rules: **`AGENTS.md`** (root). SOP: `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`.
Incident: `HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md`.
Tool: `05_程序代码/hpc_login_node_recover.py`.
Also: a `legacy_done.tsv` row is NOT a validated cell, and `squeue -h` prints a
`Last update ...` line so `grep -q .` is not a valid job-existence guard.


# CODEBUDDY — MASTER PROMPT (copy everything below the line into CodeBuddy)

---

## YOUR ROLE

You are the **execution owner** for a research project that is 70 % done. A previous session
(DeepSeek) built the pipelines, ran the experiments, and left a complete written record. Your job
is to finish the remaining experiments, aggregate the results that are already sitting on the HPC
but were never pulled back, regenerate the documents from verified data, package everything for a
writing agent, and drive the three open research gaps.

**You are not starting from scratch and you must not re-derive anything.** Everything measured is
on disk with evidence. Your value is execution and verification, not exploration.

## READ THESE FILES FIRST, IN THIS ORDER

```
CODEBUDDY_START_HERE.md          ← current state + the 8 non-negotiables
04_详细说明文档/HANDOFF_20261102.md         ← every measured number, every bug, publishability assessment
04_详细说明文档/NEXT_STAGE_PROMPTS.md       ← §0 the three gaps · §1 your brief · §2 the ChatGPT prompt
AGENTS.md                        ← protocol R1–R6 + 13 hard rules (violating any invalidates the paper)
04_详细说明文档/BUG_POSTMORTEM_20261102.md  ← 8 defects + 7 diagnostic mistakes + a 9-item pre-claim checklist
04_详细说明文档/EXECUTION_PLAN_PART3.md     ← ordered plan + 9 anti-collision rules
01_最终报告/MANIFEST.md         ← what already exists and where
```

## THE PROJECT IN SIX LINES

An independent reproduction of **MIFlu** (Moon et al., IEEE JBHI 2025) plus a three-way benchmark
the original lacks. Data: CDC national influenza, **966 weekly rows, 7 channels**, verified
bit-identical to the author's file (max|diff| = 0.000e+00). Arms: **16 conventional forecasters +
MIFlu + 11 frozen LLM encoders**. Reproduce `Table V`, then answer *which model a public-health
team should actually deploy* — where the answer is not the MSE winner.

## STATE AT HANDOFF — VERIFIED

| Item | Number |
|---|---|
| Reproduction, 4-horizon mean | **1.4995 vs paper 1.4355 = +4.5 % worse**, sign crossover **2–2** (L24 −15.4 %, L36 −4.6 %, L48 +17.0 %, L60 +23.4 %) |
| MIFlu benchmark row | **12 / 12** cells exist (seeds 42/43/44) — **but see GAP-A below** |
| Non-LLM benchmark | **192 / 192** cells, 16 models, windows **160/144/144/128** |
| LLM encoder benchmark | **132 / 156** cells = 11 arms × 12 — **but the per-arm metrics were never aggregated; see GAP-B** |
| Contamination audit | **80 / 80 PASS**, 0 contaminated |
| MSE champion | **PatchTST 1.6621** (NLinear 1.8716, DNN 2.1415) |
| Peak-skill champion | **NLinear only**, 4/16, PTE **1.677 wk**, PIE **9.477 %**; PatchTST PTE 1.240 but PIE 32.755 % → fails K&S |
| Pareto | slope **+0.1171** per decade, R² 0.0223, set {NLinear 2,520; PatchTST 531,878}; 211× params for 11.2 % lower MSE |
| Seed fix live since | **2026-11-02 03:57:47** — any LLM ±sd from before is invalid (sd was exactly 0) |
| Windows rule | `(W//16)*16` because MIFlu's loader uses `drop_last=True`; discarded windows are ~1.41× harder |

## THE TWO URGENT GAPS (do these first — they are why the report has blank tables)

### GAP-A — MIFlu benchmark row is not in the table
12 cells exist on the cluster but **have not cleared the oracle gate**, so the benchmark table
has only **16 rows**. A benchmark table without the paper's own method is unpublishable.
**Do:** confirm the 12 cells pass `_bench_manifest_ok()` + `_npz_cell_gate(n_vars=7)`; if the gate
rejects, find out why (the export path vs the gate path is the known trap — see
`04_详细说明文档/BUG_POSTMORTEM_20261102.md` A9, where `audit_miflu_cells.py --apply` was deleting benchmark
cells; that is fixed, verify the fix holds for all 12). Then add the row.

### GAP-B — 11 LLM arms have no accuracy numbers
132 cells are DONE on the cluster, but **the aggregation was never pulled**. The report therefore
lists the 11 arms and their completion with **no MSE/PTE/PIE**. This is the paper's most novel
axis. **Do:** pull the 132 `pred_*.npz`, compute per-arm 7-variable z-space MSE on the shared
windows **and** per-step PTE/PIE on ILITotal, then put the 11 rows into the benchmark tables.

## YOUR WORK, IN ORDER

### 1. HPC operations (do not break what is running)
```bash
ssh -o BatchMode=yes -o ConnectTimeout=30 -o IdentitiesOnly=yes \
    -i "$HOME/.ssh/id_ed25519" -o PreferredAuthentications=publickey cityu
# R=/gpfs1/home/sychan552/stage5_a2_durable   ;  queue at  $R/code/queue
```
- Poll **every 15 minutes**: `sacct -X -S <today> -u sychan552`
  and `grep -P '\t(table8|table6)_cell\t' $R/code/queue/master_queue.tsv | cut -f8 | sort | uniq -c`
- **Use `sacct` / `scontrol`; never `squeue`** — user-scoped and cached on this cluster.
- **Measure TCP first**: `Test-NetConnection burgundy.hpc.cityu.edu.hk -Port 22`. If TCP is open
  and ssh says `Connection closed`, that is **our own retry rate**, not an outage. Never retry
  ssh faster than once per 60–90 s.
- Driver **722968** (`persistent_driver.sh`, `tiny`, 5-day wall, no cutoff) auto-submits lanes
  until the queue drains. Do not restart it unless it has died. Before any restart:
  `grep -c 'PATCH 2026-11-02' persistent_driver.sh` and `grep -c 'lk_acquire'
  master_controller_v2.sh` must both be non-zero.
- **Fix A6 before Table VI starts**: the attempt cap is not enforced (rows reached `attempts=26`
  against a max of 2). Assert `attempts > MAXATT → SKIPPED` **before** dispatch. Table VI cells
  cost ~22 min each, so an unenforced retry loop is very expensive.

### 2. Bring results home and rebuild the analysis
Pull `03_预测数据_证据/`, `expanded_runs/`, `analysis/02_数字表格/`, `analysis/results/bench_figures/`.
Then run in order:
`analysis_expanded.py → analysis_postprocess.py → seasonal_naive_baseline.py → plot_bench.py → plot_pareto.py`,
then `verify_bench_unchanged.py` and `verify_miflu_oracle.py`.
`verify_bench_unchanged` will FAIL until the frozen baseline is re-frozen — **re-freeze only after
confirming the diff is explained by the new cells**. Never re-freeze to silence an unexplained
difference.

### 3. Regenerate the documents from verified 06_原始数据集
The generator already exists and **asserts every headline number against `02_数字表格/*.csv`**, so
a drifting CSV fails the build instead of silently changing the prose:
```bash
python 01_最终报告/_build2/build_docs.py
python 01_最终报告/_build2/to_pdf.py
python 01_最终报告/_build2/verify_docs.py     # must report FAILURES: 0
python 01_最终报告/_build2/make_manifest.py
python 01_最终报告/_build2/make_zip.py
```
Re-run this after GAP-A and GAP-B so the tables are populated. The Chinese round-trip check is
part of `verify_docs.py` — **do not skip it**, this project has been corrupted twice by encoding
(see `05_程序代码/repair_mojibake.py`).

### 4. Refactor the project — this is a REAL restructure, not a cleanup

**Two separate jobs; do both, in this order.**

#### 4a. Junk cleanup (mechanical, already scripted)
`05_程序代码/clean_junk.py --apply --hours N` refuses to touch `03_预测数据_证据/`, `expanded_runs/`,
`02_数字表格/`, `04_详细说明文档/`, `05_程序代码/`, or any `pred_*.npz`. 217 files (76.9 KiB) become eligible on
2026-11-03. `.gitignore` is already extended. **NEVER delete a `pred_*.npz`** — it is the only
re-derivation source for every published number.

#### 4b. Structural refactor — the job the user actually asked for
The repository has accumulated ~20 overlapping `04_详细说明文档/*.md`, many one-off `patch_*.py` /
`_n3_*.py` / `_fix_*.sh` scripts, duplicate build trees (`01_最终报告/_build` and `_build2`), and
scratch files at the root. It is unreadable to an outsider and it burns the context of every agent
that opens it. **Restructure it, do not just delete files.**

Target layout (create it; move, do not copy):
```
README.md                  ← what the project is, how to reproduce, where the numbers live
ARCHITECTURE.md            ← NEW: one page, module map, data flow, entry points
src/                       ← the importable code: models, data loaders, metrics, queue engine
05_程序代码/                   ← runnable entry points only (train_*, analysis_*, plot_*, verify_*)
experiments/               ← one subdir per experiment family: reproduction/, benchmark/, llm/, regional/, rolling_origin/
06_原始数据集/                      ← raw + derived splits (no scratch)
results/                   ← 02_数字表格/, bench_figures/, expanded_runs/ (the evidence)
04_详细说明文档/                      ← CONSOLIDATED documentation, see below
01_最终报告/              ← the six documents + figures + zip
archive/                   ← superseded scripts and one-off patches, preserved but out of the way
```
Rules for the move:
1. **Every file you move goes into a single `MANIFEST_MOVE.tsv`** (`old_path  new_path  reason`).
   A reader must be able to find anything that disappeared.
2. **Consolidate `04_详细说明文档/*.md` from ~20 files down to at most 8**, by merging rather than deleting:
   keep `HANDOFF`, `PROTOCOL` (merge `PROTOCOL_AMENDMENT_SEEDS`), `METHODOLOGY`, `BUGS` (merge
   `BUG_POSTMORTEM` + `OUTAGE_RECOVERY` + `HPC_RUNBOOK` gotchas), `EXECUTION` (merge
   `EXECUTION_PLAN_PART3` + `QUEUE_ROWS_PART2` + `NEXT_STAGE_PROMPTS`), `REPO_HYGIENE`,
   `LEDGER` (append-only, never merge or rewrite), `STATE`. Record what merged into what in the
   first line of each surviving file.
3. **Move every `patch_*.py`, `_n3_*.py`, `_fix_*.sh`, `_deploy_*.sh`, `_probe_*.sh` into
   `archive/patches/`** with a one-line header saying what it patched and whether the patch is now
   permanent. They are history, not tools.
4. **Keep `pred_*.npz`, `02_数字表格/*.csv`, `04_详细说明文档/LEDGER.md` exactly where the analysis scripts
   expect them, or update the scripts' paths in the same commit.** A refactor that breaks the
   analysis chain is a regression, not a refactor.
5. **Prove it still works after moving**: re-run
   `analysis_expanded.py → analysis_postprocess.py → seasonal_naive_baseline.py → plot_bench.py →
   plot_pareto.py` and `verify_docs.py`. Both must pass with the **same numbers as before the
   move**. Paste the before/after table hashes. If a number changes, you broke something — revert
   that move.
6. **Then** regenerate `PROJECT_HANDOFF.zip` from the new layout and update `MANIFEST.md`.

#### 4c. Refactor NOW — do not wait for the HPC
**An earlier version of this prompt said to defer the refactor until Table VIII and Table VI were
stable. That was wrong and is withdrawn.** Rolling origin will take days to weeks, so a refactor
gated on "everything finished" never happens — and in the meantime nobody can find the report, the
progress report, the manuscript, or which folder holds which result. That is an unacceptable state
for a project that has to be handed to a writing agent today.

**Refactor first, before the document regeneration, before the zip, before anything that depends on
layout.** The only real hazard is a *path change* breaking a running job, and that hazard has a
trivial fix: **the HPC side reads its own files under `$R/...` and must not be affected at all.**
Rules:

1. **Refactor the LOCAL repository only.** Do not move, rename or delete anything under `$R` on the
   cluster. The HPC queue, controller and driver keep their paths; there is no coupling to break.
2. **Keep these local paths fixed** so the analysis chain and the document generator keep working:
   `03_预测数据_证据/`, `expanded_runs/`, `02_数字表格/`, `01_最终报告/`, `04_详细说明文档/LEDGER.md`. Move
   everything else freely.
3. **If you must move one of the five fixed paths**, update every consumer in the same commit and
   prove it with a before/after run of the analysis chain **and** `verify_docs.py` — same numbers,
   same page counts. A refactor that changes a number is a regression: revert that single move.
4. **Refactor a copy first if you are unsure** (`refactor_preview/`), diff the outputs, then apply.

#### 4d. Publish a human-readable map — the user's actual need
Before and after the move, write **`WHERE_EVERYTHING_IS.md`** at the repo root. A reader must be
able to answer, in under ten seconds:
- Where is the **internal report**, the **FYP progress report**, the **IEEE manuscript** — in DOCX
  and PDF, English and Chinese? (Answer: `01_最终报告/`, six document bases × 2 formats.)
- Where are the **reproduction results** (Table V, per-seed oracle)?
- Where are the **benchmark results** (16 arms), the **LLM arm results**, the **PTE/PIE per-step
  results**, the **Pareto** numbers?
- Where are the **figures**, and which figure answers which question?
- Where is the **raw per-window evidence** every number can be re-derived from?
- Where is the **HPC state** (queue, driver, logs) and how do I check it?

Format it as one table per question, with a **one-line description of what each file contains**, not
just its name. If a file name does not say what it holds, say so and propose the rename.

### 5. The three open research gaps (`04_详细说明文档/NEXT_STAGE_PROMPTS.md` §0)
- **Gap 1 — rolling origin.** 1020 cells, **155–360 A100-hours**. `05_程序代码/walk_forward.py` is
  written and `assert_folds` proves the test blocks are disjoint and ordered. Queue rows are in
  `04_详细说明文档/QUEUE_ROWS_PART2.md` §2a/§2b but are **not** in `master_queue.tsv`. Enqueue as the final
  tranche and report when it can realistically start.
- **Gap 2 — cross-dataset generalisation.** Every number is US CDC. There is **no Chinese
  7-channel dataset** — do not pretend otherwise. Build a **WHO FluNet multi-country** loader
  (Japan, Korea, UK, Australia, China) and run a reduced benchmark. This is cheap relative to its
  value and directly answers "does this depend on the US reporting system".
- **Gap 3 — a genuine innovation claim.** Currently there is one finding: *the MSE champion is not
  the peak-skill champion*. That is a finding, not an innovation. Three candidates, cheapest first:
  (a) a **calibration-aware model-selection rule** (select on K&S, quantify the accuracy given up);
  (b) a **hybrid** that keeps PatchTST's timing and recalibrates the interval to NLinear's level;
  (c) **frozen-encoder selection guidance** — which families (Qwen / Llama / Tencent embedding)
  actually help, at what parameter cost. Option (c) is cheapest because the 11-arm 06_原始数据集 already
  exists. Pick one, write the claim, design the experiment, run it.

### 6. Package for the writing agent
Produce/refresh `01_最终报告/PROJECT_HANDOFF.zip`, `MANIFEST.md`, and `chatgpt_prompt.md`
(build the last one from `04_详细说明文档/NEXT_STAGE_PROMPTS.md` §2, updating filenames, page counts and every
"not yet available" you have now filled in). Hand the zip + prompt to ChatGPT for Overleaf LaTeX,
venue choice and innovation research.

## NON-NEGOTIABLES

1. **Never claim the reproduction beat the original.** +4.5 % worse with a **2–2 sign crossover**.
2. **The paper's per-horizon Table V is 1.542 / 1.422 / 1.414 / 1.364** (mean 1.4355). An earlier
   handoff listed 1.2946/1.4321/1.4695/1.5457 — that set was wrong and has been corrected. Use the
   former. It is the only set that reproduces the documented crossover.
3. **Never quote an LLM ±sd from before 2026-11-02 03:57:47** — the seed never entered the training
   path, so sd was exactly 0 by construction.
4. **`--no-text` is bit-identical** to the full model (text sits behind the causal mask). It is a
   *structural verification*, never an ablation effect.
5. **Never fabricate a number.** Write "not yet available" and name the job.
6. **DLinear is excluded everywhere** (user decision). NLinear is the sole linear-family member.
7. **Publication numbers only on `stingy` / `gpu_a100`**, with measured provenance (GPU model,
   partition, node, job id, wall seconds). Everything else is `probe_only`.
8. **Never report a state from a log line alone.** Read the artefact path, the row state, or the
   exit code the next stage consumes. If you cannot, write **"unverified"**.
9. **One writer per file.** Do not edit `code/queue/*` while another agent holds it, and do not edit
   files you delegated to a subagent. Five agents wrote one queue file on 2026-11-01 and it cost hours.

## WHAT "DONE" LOOKS LIKE

- Benchmark table has **17 rows** (16 arms + MIFlu) with MSE and PTE/PIE per step.
- LLM table has **11 rows with real MSE/PTE/PIE**, not just a roster.
- `verify_docs.py` reports `FAILURES: 0`, all Chinese text round-trips, all 6 PDFs non-zero.
- `PROJECT_HANDOFF.zip` refreshed, `chatgpt_prompt.md` lists **zero** remaining "not yet available"
  except rolling origin and cross-dataset — which are honestly out of scope for tonight.
- The three gaps have either a result or a dated plan with a cost in A100-hours.

## THE SENTENCE THAT MATTERS MOST

> The project has **publishable data** but not yet a **publishable paper**. Your job is to close the
> two blank tables from data that already exists on the cluster, then drive the three research gaps
> to either a result or a priced plan. **When in doubt, measure; never report from a log line.**
