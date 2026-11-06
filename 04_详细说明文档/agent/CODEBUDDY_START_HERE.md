# CODEBUDDY — START HERE

You are taking over an active project. The previous session (DeepSeek) ended here and handed
off. **Your mission:** finish the remaining experiments, bring the results home, produce the
documents, and then hand a package to ChatGPT.

Read these five files, in this order, before doing anything:

| # | File | Why |
|---|---|---|
| 1 | `04_详细说明文档/HANDOFF_20261102.md` | **All measured facts** — every number, every bug, the publishability assessment, the venue recommendation |
| 2 | `04_详细说明文档/NEXT_STAGE_PROMPTS.md` | **§1 is your brief**; §0 lists the three remaining gaps; §2 is the prompt you will later hand to ChatGPT |
| 3 | `AGENTS.md` | Protocol R1–R6 and the 13 hard rules. Violating any of them invalidates the paper |
| 4 | `04_详细说明文档/BUG_POSTMORTEM_20261102.md` | The eight defects that nearly destroyed the results, plus seven diagnostic mistakes — read this so you do not repeat them |
| 5 | `04_详细说明文档/EXECUTION_PLAN_PART3.md` | The ordered work plan and the nine anti-collision rules |

---

## STATE AT HANDOFF (2026-11-02 18:55 HKT)

### Complete and verified

| Item | Numbers |
|---|---|
| MIFlu reproduction (Table V) | 4-horizon mean **1.4995** vs paper **1.4355** = **+4.5 %**, with a horizon sign crossover (win L24 1.3045 / L36 1.3561, lose L48 1.6543 / L60 1.6829) |
| MIFlu benchmark row | **12 / 12** cells (seeds 42/43/44) |
| Non-LLM benchmark | **192 / 192** cells, 16 models, seeds 42/43/44, windows 160/144/144/128 |
| LLM-encoder benchmark | **132 / 156** cells = **11 arms × 12**; 24 skipped (two Tencent embedding models cannot emit per-layer hidden states) |
| Contamination audit | **80 / 80 PASS**, 0 contaminated, 0 unverifiable |
| Seed fix | live since **2026-11-02 03:57:47**; cells before that timestamp are invalid (sd was exactly 0) |

### In flight on the HPC (Burgundy, account `sychan552`)

- **Table VIII** (`table8_cell`, 60 total): ~27 done when handed off, ~31 remaining, ~7.7 min/cell
- **Table VI** regional (`table6_cell`, 21): queued at P4, starts only after Table VIII drains,
  **~22 min/cell measured** (not the earlier 2–3 min estimate)
- Driver: `persistent_driver.sh`, job **722968**, partition `tiny`, 5-day wall, **no cutoff**,
  auto-submits lanes until the queue drains
- Queue: `$R/code/queue/master_queue.tsv`, ~1951 rows
- `R=/gpfs1/home/sychan552/stage5_a2_durable`

### Not started

- Table IX (gated on Table VI)
- Rolling origin, 1020 cells — **155–360 A100-hours** (Gap 1)
- Cross-dataset validation on WHO FluNet (Gap 2)
- A genuine innovation claim (Gap 3) — currently only one finding: *the MSE champion is not the
  peak-skill champion*

---

## YOUR FOUR JOBS, IN ORDER

### 1. Keep the cluster moving
```bash
ssh -o BatchMode=yes -o ConnectTimeout=30 -o IdentitiesOnly=yes \
    -i "$HOME/.ssh/id_ed25519" -o PreferredAuthentications=publickey cityu
```
- Poll every 15 min: `sacct -X -S <today> -u sychan552` and
  `grep -P '\t(table8|table6)_cell\t' $R/code/queue/master_queue.tsv | cut -f8 | sort | uniq -c`
- **Use `sacct` / `scontrol`, never `squeue`** — on this cluster `squeue` is user-scoped and cached
- Measure `Test-NetConnection burgundy.hpc.cityu.edu.hk -Port 22` **before** diagnosing any
  outage. `Connection closed by <ip> port 22` with TCP open is our own retry rate, not the cluster
- **Never retry ssh faster than once per 60–90 s**
- **Fix A6 before Table VI**: the attempt cap is not enforced (rows reached `attempts=26`
  against a max of 2). Assert `attempts > MAXATT → SKIPPED` **before** dispatch. Table VI cells
  cost ~22 min each, so an unenforced retry loop is expensive

### 2. Bring the results home and regenerate the analysis
Copy `03_预测数据_证据/`, `expanded_runs/`, `analysis/02_数字表格/`,
`analysis/results/bench_figures/` to the local repo. Then run, in order:
`analysis_expanded.py → analysis_postprocess.py → seasonal_naive_baseline.py → plot_bench.py →
plot_pareto.py`, then `verify_bench_unchanged.py` and `verify_miflu_oracle.py`.
`verify_bench_unchanged` will FAIL until the frozen baseline is re-frozen — **re-freeze only
after confirming the diff is explained by the new cells**. Never re-freeze to silence an
unexplained difference.

### 3. Repository hygiene
Remove `_*.out`, `_*.err`, `*.tmp`, `*.bak.*` older than 24 h from the root and any non-source
location. **NEVER delete** `03_预测数据_证据/**`, `expanded_runs/**`, `02_数字表格/*.csv`,
`04_详细说明文档/**`, `05_程序代码/**`, or any `pred_*.npz` — those are the only re-derivation source for every
published number. Write `04_详细说明文档/REPO_HYGIENE.md` and extend `.gitignore`.

### 4. Documents, then the ChatGPT package
Produce in `01_最终报告/`, DOCX **and** PDF, in **English and Simplified Chinese**:
a long internal technical report, and an FYP progress report following
`Requirements_ProjectProgressReport_2627A (1).pdf` exactly. Then the IEEE-style manuscript
prototype. Then `PROJECT_HANDOFF.zip` + `MANIFEST.md` + `chatgpt_prompt.md` (build it from
`04_详细说明文档/NEXT_STAGE_PROMPTS.md` §2, filling in the real filenames and page counts).

**A previous session already produced 9 figures** in `01_最终报告/figures/` — de-normalised
ILITotal curves for MIFlu / PatchTST / NLinear at L24 and L60, the Pareto frontier, and a
per-step PTE/PIE heat map, with `figure_captions.json`. Reuse them if they are correct; verify
the axes before trusting them.

Then hand `PROJECT_HANDOFF.zip` + `chatgpt_prompt.md` to ChatGPT and let it do the writing,
format, venue choice and innovation research.

---

## NON-NEGOTIABLES (violating any of these invalidates the paper)

1. **Never claim the reproduction beat the original.** +4.5 % worse, with a sign crossover.
2. **Never quote an LLM ±sd from before 2026-11-02 03:57:47** — the seed never entered the
   training path before then, so the sd was exactly 0 by construction.
3. **The `--no-text` ablation is bit-identical** to the full model (the text sits behind the
   causal mask). Present it as a structural verification, never as an effect.
4. **Never fabricate a number** for Table VI, VIII or IX. Write "not yet available" and name the job.
5. **DLinear is excluded everywhere** (user decision). NLinear is the sole linear-family member.
6. **Publication numbers only on `stingy` / `gpu_a100`**, with measured provenance
   (GPU model, partition, node, job id, wall seconds). Everything else is `probe_only`.
7. **Never report a state from a log line alone.** Read the artefact path, the row state, or the
   exit code that the next stage actually consumes. If you cannot, write "unverified".
8. **One writer per file.** Do not edit `code/queue/*` concurrently with another agent, and do not
   edit files you have delegated to a subagent.

---

## THE ONE-SENTENCE SUMMARY

The project has **publishable 06_原始数据集** (reproduction + 16-model benchmark + 11 LLM encoders + the
"accuracy champion ≠ calibration champion" finding) but **not yet a publishable paper**: it lacks
rolling-origin evaluation, cross-dataset validation, and a stated innovation. Your job is to
finish the HPC work, produce the documents from what exists, and package it for ChatGPT to write
and to research the innovation.
