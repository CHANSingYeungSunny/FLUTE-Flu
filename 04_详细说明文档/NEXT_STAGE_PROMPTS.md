# NEXT-STAGE PROMPTS — CodeBuddy (execution) and ChatGPT (writing/research)

**What this is.** The two self-contained briefs that hand this project off. §1 is for CodeBuddy
(execution, HPC, repository, document generation). §2 is for ChatGPT (writing, format, journal
choice, innovation research). Both assume **zero prior context** and must be usable on their own.

**When to use it.** The moment this session ends. Nothing else needs to be explained to either
agent if they read this file plus `04_详细说明文档/HANDOFF_20261102.md`.

**What it points to.** `04_详细说明文档/HANDOFF_20261102.md` (all measured facts), `04_详细说明文档/BUG_POSTMORTEM_20261102.md`,
`04_详细说明文档/PROTOCOL_AMENDMENT_SEEDS.md`, `04_详细说明文档/EXECUTION_PLAN_PART3.md`, `02_数字表格/*.csv`.

---

## §0. THE THREE REMAINING GAPS — read this before either prompt

These are the only things standing between "solid 06_原始数据集" and "submittable manuscript". They are
listed here once so both prompts can refer to them instead of repeating them.

### GAP 1 — Rolling-origin evaluation (methodological hole, costs compute)
The entire benchmark rests on **one fixed 70/10/20 chronological split**. A top-tier reviewer
will raise this first: conclusions may be split-dependent. The fix is a 5-fold walk-forward
evaluation — `05_程序代码/walk_forward.py` is already written and tested (`assert_folds` proves the
test blocks are disjoint and strictly ordered; the `val_floor_rows=75` widening is documented
because a pure 70/10/20 layout is arithmetically impossible at L≥36 on 966 rows).
**Cost: 155–360 A100-hours** (200 MIFlu fold cells ≈ 120–270 h; 960 arm fold cells ≈ 35–90 h).
The queue rows exist in `04_详细说明文档/QUEUE_ROWS_PART2.md` §2a/§2b but are **not** in `master_queue.tsv`.

### GAP 2 — Cross-dataset generalisation (external validity, costs 06_原始数据集 work)
Every number comes from **US CDC national ILI, 966 weeks, 7 channels**. A reviewer will ask
whether the method generalises beyond the US reporting system. The 7-channel structure
(`OT`, `%WEIGHTED ILI`, five age bands) is CDC-specific, so **there is no "Chinese 7-channel"
dataset** — do not pretend otherwise. The realistic options, in order of value:
1. **WHO FluNet multi-country** (fully public, weekly, per country): Japan, Korea, UK, Australia,
   China. Run the pipeline on a reduced feature set for a handful of models. This directly answers
   "does it depend on the US reporting system".
2. **US regional / HHS-10** — this is the original paper's Table VI and is already queued.
3. Chinese CDC hand-collection — **not feasible** (not machine-readable in bulk); say so if asked.
**Verdict for venue choice**: not strictly required for IEEE JBHI (a method paper on one national
dataset is publishable), but its absence is the most common reason a reproduction+benchmark paper
is sent back as "major revision". For JBI or above, external validation is close to mandatory.

### GAP 3 — A genuine innovation claim (research, not compute)
At present the project has exactly **one** original finding:
> **The MSE champion is not the peak-skill champion** — PatchTST wins accuracy (MSE 1.6621) and
> timing (PTE 1.240 wk) but fails calibration (PIE 32.755 %), while NLinear is the only model
> satisfying Kramer & Shaman (PTE ≤ 1 wk AND PIE ≤ 25 %) and only at step 0.

That is a real contribution but it is a *finding*, not yet an *innovation*. A defensible
innovation must be a **method or a decision rule we propose**, e.g. one of:
- a **calibration-aware model-selection rule** for epidemiological forecasting (pick on the
  K&S criterion, not MSE) with a cost analysis of what accuracy you give up;
- a **hybrid** that keeps PatchTST's timing and NLinear's calibration (e.g. PatchTST point
  forecast + NLinear-style recalibration of the predictive interval), evaluated on both metrics;
- **frozen-LLM-encoder selection guidance**: which encoder families (Qwen vs Llama vs Tencent
  embedding models) actually help, at what parameter cost — the 11-arm 06_原始数据集 already exists to
  support or refute this.
The third is the cheapest because the data is already on disk.

---

## §1. PROMPT FOR CODEBUDDY (execution)

> You are taking over an active research-engineering project. Everything below is current and
> measured; treat `04_详细说明文档/HANDOFF_20261102.md` as the authoritative record and read it first,
> together with `AGENTS.md` (protocol R1–R6 and 13 hard rules), `04_详细说明文档/BUG_POSTMORTEM_20261102.md`,
> `04_详细说明文档/PROTOCOL_AMENDMENT_SEEDS.md`, `04_详细说明文档/EXECUTION_PLAN_PART3.md`,
> `04_详细说明文档/QUEUE_ROWS_PART2.md` and `04_详细说明文档/NEXT_STAGE_PROMPTS.md` (§0 = the three remaining gaps).
>
> **The project.** An independent reproduction of MIFlu (Moon et al., IEEE JBHI 2025) plus a
> three-way benchmark on the CDC national influenza dataset (966 weekly rows, 7 channels,
> verified bit-identical to the author's file): 16 conventional forecasters, MIFlu itself, and
> 11 frozen LLM encoders. Already complete: reproduction 40/40 cells (4-horizon mean 1.4995 vs
> the paper's 1.4355, +4.5 %, with a horizon sign crossover), MIFlu benchmark row 12/12,
> non-LLM benchmark 192/192, LLM benchmark 132/156 (24 cells skipped because two Tencent
> embedding models cannot emit per-layer hidden states). In flight: Table VIII (60 cells) and
> Table VI regional (21 cells). Not started: Table IX and rolling origin.
>
> **Your first job is to keep the cluster moving.**
> - SSH: `ssh -o BatchMode=yes -o ConnectTimeout=30 -o IdentitiesOnly=yes -i "$HOME\.ssh\id_ed25519" -o PreferredAuthentications=publickey cityu`.
>   Measure `Test-NetConnection burgundy.hpc.cityu.edu.hk -Port 22` **before** diagnosing any
>   failure: `Connection closed by <ip> port 22` while TCP is open is almost always our own ssh
>   retry rate, not an outage. Never retry ssh faster than once per 60–90 s.
> - Cluster root `R=/gpfs1/home/sychan552/stage5_a2_durable`; queue `$R/code/queue`.
> - Poll every 15 minutes: `sacct -X -S <today> -u sychan552`, and
>   `grep -P '\t(table8|table6)_cell\t' $R/code/queue/master_queue.tsv | cut -f8 | sort | uniq -c`.
>   **Use `sacct`/`scontrol`, never `squeue`** — on this cluster it is user-scoped and cached.
> - The driver `722968` (`persistent_driver.sh` on `tiny`, 5-day wall, no cutoff) auto-submits
>   lanes until the queue drains. Do not restart it unless it dies; if you must,
>   `grep -c 'PATCH 2026-11-02' persistent_driver.sh` and
>   `grep -c 'lk_acquire' master_controller_v2.sh` must both be non-zero first.
> - **One open defect to fix before Table VI**: the attempt cap is not enforced (rows have
>   reached `attempts=26` against a stated maximum of 2). Table VI cells cost ~22 minutes each,
>   so an unenforced retry loop is expensive. Fix: assert `attempts > MAXATT → SKIPPED` **before**
>   dispatch.
>
> **Your second job is to bring the results home and regenerate the analysis.**
> Copy `03_预测数据_证据/`, `expanded_runs/`, `analysis/02_数字表格/` and
> `analysis/results/bench_figures/` to the local repo, then run the chain
> `analysis_expanded.py → analysis_postprocess.py → seasonal_naive_baseline.py → plot_bench.py →
> plot_pareto.py`, followed by `verify_bench_unchanged.py` and `verify_miflu_oracle.py`.
> `verify_bench_unchanged` is expected to FAIL until the frozen baseline is re-frozen — **only
> re-freeze after confirming the diff is explained by the new cells** (the new MIFlu benchmark
> row and the 11 LLM arms). Never re-freeze to silence an unexplained difference.
>
> **Your third job is repository hygiene.** Remove `_*.out`, `_*.err`, `*.tmp`, and `*.bak.*`
> older than 24 h from the repo root and any non-source location. **Never delete**
> `03_预测数据_证据/**`, `expanded_runs/**`, `02_数字表格/*.csv`, `04_详细说明文档/**`, `05_程序代码/**`, or any
> `pred_*.npz` — those are the only re-derivation source for every published number. Write
> `04_详细说明文档/REPO_HYGIENE.md` saying what to ignore and what is authoritative, and extend
> `.gitignore` so the junk cannot come back.
>
> **Your fourth job is the documents.** Produce, in `01_最终报告/`, DOCX **and** PDF, in
> **English and Simplified Chinese**: (a) a long internal technical report, (b) an FYP progress
> report that follows `Requirements_ProjectProgressReport_2627A (1).pdf` exactly. Use
> python-docx and export PDFs through LibreOffice. Every caption must state the metric, the
> window rule `(W//16)*16` = 160/144/144/128, and the hardware (A100-SXM4-80GB, `stingy`, CityU
> HPC Burgundy). Required figures: de-normalised ILITotal curves (ground truth vs step 0/1/2/3)
> for at least MIFlu, PatchTST and NLinear; the Pareto plot; a per-step PTE/PIE heat map.
> Verify the Chinese documents by extracting their text back out — this project has been bitten
> twice by encoding corruption.
>
> **Your fifth job is the three gaps in §0.** Rolling origin is 155–360 A100-hours: put it in the
> queue as the last tranche and report when it can realistically start. Cross-dataset
> generalisation: build a WHO FluNet multi-country loader and run a reduced benchmark
> (Japan, Korea, UK, Australia, China) — this is cheap relative to its value. Innovation: read §0
> Gap 3, pick the option whose 06_原始数据集 already exists (the 11-arm LLM encoder study), and draft the
> claim plus the experiment that supports it.
>
> **Non-negotiables.** Never claim the reproduction beat the original (+4.5 % with a sign
> crossover). Never quote an LLM ±sd from before the seed fix of 2026-11-02 03:57:47 (the seed
> never entered the training path before then; sd was exactly 0). Never present the `--no-text`
> ablation as an effect — it is bit-identical to the full model because the text sits behind the
> causal mask, so it is a structural verification only. Never fabricate a number for Table VI,
> Table VIII or Table IX — write "not yet available" and name the job.
>
> **Finally**, produce `01_最终报告/chatgpt_prompt.md`: the §2 prompt below, updated with the
> actual deliverable filenames, page counts, and any value you had to mark "not yet available".

---

## §2. PROMPT FOR CHATGPT (writing, format, venue, innovation research)

> You are writing three interlinked documents for a final-year project and a journal submission.
> You have no prior context; everything you need follows.
>
> **The project.** An independent reproduction of MIFlu (Moon et al., *IEEE Journal of
> Biomedical and Health Informatics*, 2025) plus a three-way benchmark the original paper does not
> contain. Data: CDC national influenza surveillance, 966 weekly rows, 7 channels, verified
> bit-identical to the author's released file. Arms: 16 conventional forecasters, MIFlu itself,
> and 11 frozen LLM encoders used as feature extractors with a single shared linear head.
>
> **Never claim the reproduction beat the original.** The 4-horizon mean is 1.4995 against the
> paper's 1.4355, i.e. **+4.5 % worse**, and the sign flips by horizon — we are better at L24
> (1.3045 vs 1.2946) and L36 (1.3561 vs 1.4321) and worse at L48 (1.6543 vs 1.4695) and L60
> (1.6829 vs 1.5457). Report the crossover explicitly; a reproduction study that hides a sign
> crossover is not publishable.
>
> **Two protocols, both stated in every caption.** The reproduction uses **10 repetitions, seeds
> 2021–2030**, to match the original author. The benchmark uses **3 seeds, 42/43/44, for every
> model** — the current norm: PatchTST (ICLR 2023) and iTransformer (ICLR 2024) both report
> 3-seed means; cite them for credibility. MIFlu therefore appears twice, once as a reproduction
> and once as a benchmark entry; the two numbers answer different questions and are not
> comparable to each other. State this where a reader will look for it, not in a footnote.
>
> **Two metrics, for two different purposes.** The benchmark metric is the **7-variable aggregate
> MSE in z-space**, computed on the shared evaluation windows **`(W//16)*16` = 160/144/144/128**.
> Justify this: MIFlu's own loader uses `DataLoader(batch_size=16, drop_last=True)` and therefore
> discards the final partial batch (170→160, 158→144, 146→144, 134→128); those discarded windows
> are **~1.41× harder** (measured 1.3929–1.4423). Scoring all 17 models on the same cropped
> windows is the only like-for-like choice. The peak-skill metric is **PTE/PIE on ILITOTAL
> de-normalised to patient counts**, against the Kramer & Shaman (2019) acceptance criterion
> **PTE ≤ 1 week AND PIE ≤ 25 %**, evaluated per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. The
> 7-variable aggregate cannot be de-normalised (OT train mean 493,629 versus %WEIGHTED ILI 1.74),
> which is exactly why PTE/PIE use ILITotal only. Explain this rather than letting a reviewer
> discover it.
>
> **The headline finding to argue.** *The MSE champion is not the peak-skill champion.* PatchTST
> has the lowest MSE (1.6621) and the best PTE (1.240 weeks) but fails calibration (PIE 32.755 %).
> NLinear is the only model satisfying the epidemiological criterion — **4 of 16 cells, PTE 1.677
> weeks, PIE 9.477 %** — and only at step 0. NLinear has 2,520 parameters, PatchTST 531,878;
> PatchTST spends **211× the parameters for 11.2 % lower MSE**. The efficiency regression across
> all arms has slope **+0.1171 per decade of parameters, R² = 0.0223**, i.e. parameter count
> explains almost nothing. Argue the practical consequence: choosing a forecaster by MSE can give
> a model that misses the epidemiological acceptance criterion entirely.
>
> **The second axis.** 11 frozen LLM encoders, 12 cells each (4 horizons × seeds 42/43/44):
> Qwen2.5-1.5B; DeepSeek-R1-Distill Qwen-1.5B, Qwen-7B, Llama-8B, Qwen-14B, Qwen-32B; Tencent
> ContextPilot-8B and -14B; Tencent Hunyuan-1.8B, -4B, -7B. Each arm is the frozen encoder plus
> one shared `nn.Linear(D, L)` head, channel-independent. **24 cells were skipped** because
> `WeMM-Embedding-2B/-4B` are embedding-only and cannot emit per-layer hidden states. Also
> excluded, with reasons that must appear in the paper: Penguin-Encoder (requires
> `trust_remote_code`), Youtu-HiChunk (no per-layer hidden states), KaLM-Embedding-Gemma3-12B
> (download failed), Qwen3.8-27B-FP8 (dequantises to ~54.7 GB, not run) and Llama-70B (does not
> fit an 80 GB A100). The Llama-8B arm exists specifically to separate *scale* from *base
> architecture*: it is near-isoscale to Qwen-7B with a different base.
>
> **Disclose, do not hide, these four limitations.** (1) **Rolling-origin evaluation is not
> available** — the benchmark uses one fixed chronological split, which is the single most likely
> rejection reason; the walk-forward code exists but costs 155–360 A100-hours. (2) The
> **`--no-text` ablation is bit-identical** to the full model because the text embeddings sit
> behind the causal mask, so that row is a *structural verification*, never an ablation effect.
> (3) All results come from **one national dataset**; cross-dataset validation (WHO FluNet
> multi-country) is the identified next step. (4) The author's code selects the checkpoint on the
> **test** set (`main_ILI_lora.py` L211/L225) — that is leakage; we select on validation and
> disclose the deviation.
>
> **What to produce.**
> 1. **Overleaf-ready LaTeX** for three documents, each as a compileable project (`main.tex`,
>    `refs.bib`, `figures/`): (a) a long internal technical report, (b) a concise FYP progress
>    report, (c) an IEEE-style manuscript including an innovation section.
> 2. **English and Simplified Chinese** versions of all three, plus DOCX and PDF exports.
> 3. A **venue recommendation with reasoning**: which journal or conference fits this work best
>    and why, and which part of the work (reproduction / benchmark / peak-skill finding /
>    LLM-encoder study / proposed innovation) belongs in which venue. IEEE JBHI is the natural
>    first candidate because it published the original; say so only if you agree after checking
>    current scope and acceptance trends, otherwise name a better target and justify it.
> 4. An **innovation research memo**: search recent IEEE-level and adjacent literature on frozen
>    foundation-model features for epidemiological time series and on calibration-aware model
>    selection, identify a genuine gap, and propose two or three executable options with compute
>    cost and expected contribution. Rank them.
>
> **A section a reviewer will look for, which you must write.** A short "design decisions"
> subsection answering, in one paragraph each: why 10 seeds for the reproduction but 3 for the
> benchmark (with the PatchTST / iTransformer citations); why this 70/10/20 chronological split
> and why validation-based checkpoint selection; why the `(W//16)*16` window rule; why two
> different metrics; why MIFlu appears twice; why 24 LLM cells are missing.
