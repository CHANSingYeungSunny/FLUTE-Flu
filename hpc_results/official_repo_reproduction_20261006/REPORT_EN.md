# REPORT_EN — Official-Repo Reproduction and Fair LLM vs non-LLM Comparison (2026-10-06)

Directory: `hpc_results/official_repo_reproduction_20261006/`
This round: **read-only inspection + local CPU recomputation + new files only.** No old checkpoint, prediction, report or CSV was deleted or overwritten. **No HPC job was submitted** (see §0).

---

## §0 Execution boundary

**HPC is reachable and was used throughout** (`hpclogin02`, first connected 2026-10-05T20:20Z; note that login needs `-o PreferredAuthentications=publickey`, because `~/.ssh/config` excludes publickey from `PreferredAuthentications`).

**Jobs submitted and completed this round (all COMPLETED; the queue is empty at the end):**

| Job | What | Resource | Elapsed | GPU-h |
|---|---|---|---:|---:|
| 606357 | text-path probe, CPU half | CPU only | 00:01:08 | 0 |
| 606358 | text-path probe, **A100** half | a100:1 | 00:00:30 | 0.00833 |
| 606360 | CPU/GPU probe comparison | CPU only | 00:00:00 | 0 |
| 606361_0 | A1 attempt (failed: `--target_modules` type trap) | a100:1 | 00:00:07 | 0.00194 |
| 606362 | PEFT/LoRA diagnosis (7 spellings tested) | CPU only | 00:00:05 | 0 |
| **606365_0** | **A1 L=24** | a100:1 | 00:17:34 | 0.29278 |
| **606378_1** | **A1 L=36** | a100:1 | 00:16:54 | 0.28167 |
| **606385_2** | **A1 L=48** | a100:1 | 00:16:18 | 0.27167 |
| **606412_3** | **A1 L=60** | a100:1 | 00:15:42 | 0.26167 |

**GPU budget:** stage6 1.1256 + this round 1.11806 = **2.24366 / 2.3**, leaving **0.05634** (≈3.4 minutes of A100) -> the round stopped there.

**Three real blockers found this round (all localised, recorded in `DEVIATION_LEDGER.md` D-10..D-12):**
1. the author's `--target_modules` is declared `type=str` with a **list** default, so any CLI override crashes LoRA;
2. **scratch user quota exceeded** (413 GB against 300 GB, `grace=expired`) -> all writes moved to `/gpfs1/home/`;
3. `partition-stingy` sets `MaxSubmit=1, MaxJobsPU=1` -> each horizon submitted and awaited individually.

## §A Executive summary

| Question | Answer |
|---|---|
| **Was the paper reproduced?** | ❌ **No.** None of Table V–IX or Figures 3–7 are reproduced. A1 now genuinely runs on the author's code across all four horizons, but its metric definition differs, so it is **not** a reproduction. |
| **Best overall model** | Track A (author 966 rows): **`notext` 1.9222** (control); among the eight core models **`miflu` 2.0415** |
| **Best LLM model** | Track A: **`miflu` 2.0415** / Track B: **`gpt2_miflu` 0.7709** (rank 1 overall) |
| **Best non-LLM model** | **`nlinear`** on both tracks (2.0496 / 1.0698) |
| **Matched full vs no-text** | `notext − miflu` = **−0.1194**, t = **−1.50**, 7/12 cells favour no-text → **not significant**; "removing text is better" **cannot be claimed** |
| **Text-path verdict** | ✅ **Resolved on both CPU and A100:** the released code's text has **strictly zero** effect (max\|Δpred\|=0, gradient=0); the **A2 implementation is `text_active`** (max\|Δpred\|=59.7) - so the benchmark's full-vs-no-text contrast is valid |

**Three facts that must be stated together:**

1. **Group means say LLM is worse, but the best-in-group differs across tracks** — Track A's best is `notext` (non-LLM control); Track B's best is `gpt2_miflu` (LLM). **Reporting only one is selective reporting.**
2. **MIFlu and NLinear are indistinguishable** (t = −0.11), and **the sign flips with horizon** (all three L=24 cells lost, most L=36/48/60 cells won).
3. **Track A and Track B absolute numbers must never be compared** (different data, seed counts and test windows).

---

## §B Repository identity

| Item | Value | Verdict |
|---|---|---|
| Project remote | `CHANSingYeungSunny/FLUTE-Flu.git` | — |
| Project commit | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` (**1 commit only**) | ⚠️ no git history for experiment ordering |
| Branch | `recovery-stage4` | — |
| Author remote | `Jmoon3108/MIFlu.git` | ✅ **the author's official repo** |
| Author commit | `6ed210150b8819313947cf607eb1821c87b1bee3` (2025-03-21) | ✅ matches the recovery-plan record exactly |
| Author tree modified locally? | compat layer sits on a separate `sys.path`; **author sources byte-identical** | ✅ |
| Data SHA-256 (Track A, actually used) | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | ✅ matches prior records |
| Data SHA-256 (author default file) | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | — |

**Reproducibility gap:** `scripts/miflu_model.py` (among others) has **uncommitted changes** and the repo has a single commit, so **the code version used at training time cannot be recovered from git.** Declared.

---

## §C Paper targets vs actual results

### Paper targets (Table V)

| L | MSE | MAE |
|---:|---:|---:|
| 24 | 1.542 | 0.726 |
| 36 | 1.422 | 0.779 |
| 48 | 1.414 | 0.757 |
| 60 | 1.364 | 0.719 |
| mean | 1.4355 | 0.74525 |

> **Key qualification:** §V-C states the national/regional comparison-baseline results are **taken from [9] and [14]** — i.e. the baseline columns of Table V are **quoted, not re-run**. Whether MIFlu's own column is also quoted is not stated.

### Ours (Track A, author 966 rows, z-space, **3 seeds**)

| L | our MSE | paper MSE | abs diff | ratio |
|---:|---:|---:|---:|---:|
| 24 | 2.4439 | 1.542 | +0.902 | 1.58× |
| 36 | 1.9360 | 1.422 | +0.514 | 1.36× |
| 48 | 1.7677 | 1.414 | +0.354 | 1.25× |
| 60 | 2.0184 | 1.364 | +0.654 | 1.48× |
| mean | **2.0415** | 1.4355 | +0.606 | **1.42×** |

### ⚠️ This table is **not** reproduction evidence

| Why not comparable | |
|---|---|
| Hyperparameters undisclosed | the paper says only "set empirically"; **no epochs or lr values** (§D) |
| Repetitions | ours **3**, paper **10** |
| Scaling convention | the paper's own scaler convention is undisclosed |
| Text path | the paper's own token order is **self-contradictory** (L205/L219/L225); we use a declared repair |

**Must say:** "our 2.0415 is a different measurement from the paper's 1.4355 and **does not constitute a reproduction**."
**Must not say:** "we reproduced the paper's 1.4355", or anything implying numerical proximity equals success.

### 3-seed vs 10-seed status (stated separately)

| Track | Seeds | Status |
|---|---|---|
| Track A (author 966) | **3** (42/43/44) | ✅ done, 12 cells per model only |
| Track A extended to 10 | 10 | ❌ **not run**; 88 missing fits (A2 config 0.0146 h/fit ≈ 1.29 GPU-h) |
| **A1 track (author code)** | **1/10** | ⚠️ **4/4 horizons run** (2026-10-06, jobs 606365/606378/606385/606412), 1 repetition each; 10 repetitions would cost ≈11.27 GPU-h |
| Track B (July 1025) | **10** (42–51) | ✅ done (historical track) |

---

### A1 has now actually run (2026-10-06, on the author's own entry point)

**Config:** author's `main_ILI_lora.py`, `multimodal=1` `PEFT=1` `lora_r=4`, 20 epochs, lr 5e-4, batch 16, `itr=1`.

| L | `mse_mean` | best-epoch MSE | best-epoch MAE | Wall | Job |
|---:|---:|---:|---:|---:|---|
| 24 | 0.6044 | **0.5344** @ep8 | 0.4503 | 17:34 | 606365_0 |
| 36 | 0.6028 | **0.5387** @ep10 | 0.4195 | 16:54 | 606378_1 |
| 48 | 0.6571 | **0.6069** @ep16 | 0.4684 | 16:18 | 606385_2 |
| 60 | 0.6545 | **0.5933** @ep5 | 0.5093 | 15:42 | 606412_3 |

> ⚠️ **This is not a reproduction of Table V.** The author's Test scores **feature 0 only** and selects the checkpoint by **Test MSE**; the paper asks for **10 repetitions**, this round did **1** per horizon; epochs and lr are **undisclosed** by the paper. These numbers are a **different measurement** from the paper's 1.542/1.422/1.414/1.364 and must not be compared with them.

## §D A0 / A1 / A2 must not be conflated

| | **A0** released-code replay | **A1** reconstructed paper config | **A2** corrected fair benchmark |
|---|---|---|---|
| Code | author verbatim | author + paper settings | corrected reconstruction |
| Purpose | record actual released behaviour | main paper-reproduction track | fair comparison |
| Hyperparameters | author defaults (1 ep / 1e-4) | 20 ep / 5e-4 (**reconstructed**) | 20 ep / 5e-4 |
| Text path | as released (inert) | as released | declared repair (text prefixed) |
| LoRA | **never applied** | applied | applied |
| Freeze | **no-op (100% trainable)** | per variant | effective |
| Checkpoint rule | **selected on Test** (leakage) | same as A0 | validation-only |
| Test variables | **feature 0 only** | same as A0 | all seven |
| Completion | ⚠️ **minimum diagnostic only** (1 epoch, itr=1, L=24) | ⚠️ **4/4 horizons run, 1/10 repetitions each** (2026-10-06) | ✅ 108 fits + 116 scores |

**Hard rules:** A0's output is not a clean holdout and not a successful reproduction; A2 is **not** an "unmodified paper reproduction" and must always carry the corrected-reconstruction label; the three must never be ranked or averaged together.

### Measured defects in the author's released code

| Defect | Evidence |
|---|---|
| Test covers `feat_id=[0]` only | measured `test=[0]`; `drop_last` shrinks 170→160 |
| Test read every epoch and used to pick the checkpoint | source L211/225/264; re-verified this round |
| early stopping call commented out | L235-236 |
| `PEFT=0` default → **LoRA never applied** | measured: `llmmodel` is a bare `GPT2Model` |
| `freeze` is a no-op | measured **82,705,944 / 82,705,944 = 100% trainable** |
| Text path inert | see §E |

---

## §E Text-path verdict (P0 resolved)

### Verdict: `text_inert` — the released implementation's text CONTENT has strictly zero effect

| Criterion | Measured |
|---|---|
| **Equal-length different-content text swap**, `max\|Δpred\|` | **0.000000e+00** (exact zero) |
| Text embedding gradient norm | **0.0** (exact zero) |
| Time-series embedding gradient norm (control) | **0.032782** (non-zero → the measurement chain works) |
| Positions the forecasting head reads | **42** = `patch_num`; text sits at [42, 358], **outside the read range** |
| Dropout state | all `training=False` |
| **Positive control** (prefix-text repair, declared change) | `max\|Δpred\|` = **3.55e-05** → **the probe can detect text influence** |

### What the earlier "CPU/GPU contradiction" was

The A0 GPU evidence compared `--multimodal 0` vs `1`, **which also changes the sequence length (42 → 359)** and therefore the dropout RNG consumption during training — a different optimisation trajectory. **That is not a text effect.**

New measurement this round (fixed weights, eval mode, dropout off):

| Comparison | Seq len | `max\|Δpred\|` | Reading |
|---|---|---|---|
| `multimodal=0` vs `1` | 42 vs 359 | **2.38e-07** | ≈ float32 rounding → **mathematically equivalent** |
| Equal-length different-content text | 359 vs 359 | **0.000e+00** | exact zero |

This agrees exactly with the static causal-mask analysis: the 42 retained patch positions all precede the text and, under causal attention, **cannot** see it.

**Conclusion:** the Stage-2 CPU verdict was right; the A0 GPU reading was a misinterpretation. This item can be **closed**.
**The GPU half has now run on an HPC A100** (job 606358, 0.00833 GPU-h), and comparison job **606360 printed `CPU/GPU verdicts AGREE`**. All three runs - local CPU, HPC CPU, HPC A100 - return the same verdict, and **HPC CPU and A100 produce identical parameter SHA-256** (`d7ad42ee…`), i.e. bit-reproducible across devices.

### E.2 The A2 implementation is `text_active` (stated separately from the author's code)

The verdict above concerns the **author's released code**. The benchmark, however, reports **A2**, so A2 was verified on its own (`probe_a2_text_path.py`, real trained checkpoint):

| Implementation | Text-path structure | Verdict | Equal-length swap `max\|Δpred\|` | Text gradient |
|---|---|---|---:|---:|
| **Author's released** `GPT4TS_lora.py` | text **after** the patches (unreachable under causal attention) | **`text_inert`** | **0.0** | **0.0** |
| **A2 corrected** `miflu_model.py` | text **before** the patches; reads the **trailing** patches (L376/L407) | **`text_active`** | **59.6875** | **7.13e+08** |

(A2's L=24 and L=60 prompts happen to be exactly the same length - 1552 chars -> `(1,369,768)` - so this is a clean equal-length, different-content control. The 12 "missing" keys on load are GPT-2 causal-mask **buffers**: deterministic constants, not trained values, so the real trained weights were used.)

**Conclusion:** the benchmark's `notext` vs `miflu` contrast **is** a genuine text-content contrast. The two findings do not conflict, but must not be borrowed from one another: A2's `text_active` does not excuse the author's code, and the author's `text_inert` does not invalidate A2's mechanism experiment.

---

## §F LLM vs non-LLM fair comparison

### F.1 Track A (author 966 rows, z-space, 3 seeds × 4 horizons)

| Rank | Model | Family | Identity | average_MSE_4L |
|---:|---|---|---|---:|
| — | **notext** | **CONTROL (LLM retained)** | reconstructed ablation | **1.922158** |
| 1 | miflu | LLM | corrected reconstruction | 2.041519 |
| 2 | nlinear | non-LLM | **canonical** | 2.049550 |
| — | seasonal_naive | baseline | deterministic | 2.268799 |
| 3 | dlinear | non-LLM | own re-implementation | 2.347832 |
| 4 | timecma_llm | LLM | TimeCMA-**INSPIRED** | 2.670009 |
| 5 | patchtst | non-LLM | PatchTST-**INSPIRED** | 3.920470 |
| 6 | itransformer | non-LLM | own re-implementation | 3.984699 |
| 7 | qwen_time_llm | LLM | Time-LLM-**INSPIRED** | 5.219555 |
| 8 | calf_llm | LLM | CALF-**INSPIRED** | 5.515300 |
| — | last_value_naive | baseline | deterministic | 7.165831 |

**Group means (supplementary, not the primary claim)**

| Convention | LLM group | non-LLM group | Gap |
|---|---:|---:|---:|
| **4 vs 4** | **3.861596** | **3.075638** | +0.785958 |
| 3 vs 5 | 4.468288 (n=3) | 2.868814 (n=5) | +1.599474 |

> `notext` belongs to **neither** group: it keeps the GPT-2 forecasting backbone and LoRA.

### F.2 Primary results (specific models, predeclared comparisons)

| Comparison | Mean diff | t | Wins | Verdict |
|---|---:|---:|---|---|
| **miflu − nlinear** | −0.0080 | −0.11 | **7/12** | **indistinguishable** |
| **notext − miflu** (mechanism) | −0.1194 | −1.50 | 7/12 | **not significant** → cannot claim text removal helps |
| notext − nlinear | −0.1274 | −2.28 | 11/12 | no-text better |
| dlinear − nlinear | +0.2983 | +8.51 | 0/12 | significantly worse |
| timecma_llm − nlinear | +0.6205 | +10.94 | 0/12 | significantly worse |
| patchtst − nlinear | +1.8709 | +39.16 | 0/12 | significantly worse |
| itransformer − nlinear | +1.9351 | +31.47 | 0/12 | significantly worse |
| qwen_time_llm − nlinear | +3.1700 | +21.66 | 0/12 | significantly worse |
| calf_llm − nlinear | +3.4658 | +46.63 | 0/12 | significantly worse |

> ⚠️ Win counts are corrected. The original `paired_stats.txt` `n_win` column was **inverted** (`miflu−nlinear` printed 5/12, actually 7/12). See `SCORING_CORRECTION_NOTE.md`. **Mean differences and t values are unaffected.**

### F.3 Per-horizon winners (sign flips)

| L | Best overall | Best LLM | Best non-LLM | notext |
|---:|---|---|---|---:|
| 24 | **notext** 1.9796 | miflu 2.4439 | **nlinear** 2.1008 | 1.9796 |
| 36 | **notext** 1.8268 | **miflu** 1.9360 | nlinear 2.0277 | 1.8268 |
| 48 | **miflu** 1.7677 | **miflu** 1.7677 | nlinear 2.0033 | 1.7901 |
| 60 | **miflu** 2.0184 | **miflu** 2.0184 | nlinear 2.0664 | 2.0921 |

**At L=24 NLinear clearly beats MIFlu (2.1008 vs 2.4439); at L=36/48/60 MIFlu leads. A single-horizon result must not be extrapolated.**

### F.4 Stability

| Model | L24 | L36 | L48 | L60 | Range |
|---|---:|---:|---:|---:|---:|
| notext | 1.9796 | 1.8268 | 1.7901 | 2.0921 | 0.302 |
| **miflu** | 2.4439 | 1.9360 | 1.7677 | 2.0184 | **0.676** |
| **nlinear** | 2.1008 | 2.0277 | 2.0033 | 2.0664 | **0.098** |
| dlinear | 2.2850 | 2.2780 | 2.3558 | 2.4726 | 0.195 |

**MIFlu's spread across horizons is 6.9× NLinear's** (12-cell SD 0.2838 vs 0.0736). **NLinear is markedly more stable.**

### F.5 Cost

| Item | Value |
|---|---|
| Measured per-fit cost | **0.0125 GPU-h** (20 epochs; 1.05 GPU-h / 72 fits) |
| Stage 6 consumed | 1.0500 GPU-h (+0.0756 failed) |
| Stage 6 authorised cap | 2.3 GPU-h, **1.1744 remaining** |
| A1 array (8 fits) | ≈ 0.10 GPU-h |
| Track A extension to 10 seeds | ≈ 1.84 GPU-h (**exceeds the remaining budget**) |
| This round (10-06) HPC consumption | **0.0** (no job submitted) |

### F.6 Track B (July-2026, 1025 rows, 10 seeds) — historical track only

| Rank | Model | Family | average_MSE_4L |
|---:|---|---|---:|
| 1 | **gpt2_miflu** | LLM | **0.770872** |
| 2 | nlinear | non-LLM | 1.069767 |
| 3 | patchtst | non-LLM | 1.075951 |
| 4 | dlinear | non-LLM | 1.170933 |
| 5 | timecma_llm | LLM | 1.181449 |
| 6 | itransformer | non-LLM | 1.252982 |
| 7 | qwen_time_llm | LLM | 1.253096 |
| 8 | calf_llm | LLM | 1.764871 |

4v4 group means: LLM **1.242572** vs non-LLM **1.142408** (+0.100164).

**Tension:** the group mean says LLM is worse, yet **the best individual is an LLM**. The two tracks point in opposite directions (Track A's best-in-group is `notext`).

---

## §G Comparison with older results (three tracks, kept apart)

| | **Track A** (this round) | **Track B** (historical) | **older 8-17 / 514859** |
|---|---|---|---|
| Data | author 966 | July-2026 **1025** | 966 / 1025 mixed |
| Split | 676/97/193 | different | 676/**96/194** |
| Seeds | 3 | 10 | 10 reps |
| Checkpoint selection | validation-only | validation | **none** |
| Channels | all 7 | all 7 | **ILI only** |
| L=24 headline | 2.4439 | 0.7324 (gpt2_miflu) | 2.593 / 2.238 / 1.379 |

**Hard rules:** absolute MSE must **never** be compared across these; Track A 2.0415 vs Track B 0.7709 differ by 2.6× **purely from protocol differences**. Older results are data-vintage landmarks only and must not enter any ranking or average. The old Test is exposed → labelled **retrospective**.

---

## §H Limitations (report with every conclusion)

| Category | Detail |
|---|---|
| **Unrecovered hyperparameters** | epochs and lr are **never disclosed** by the paper. 20 ep / 5e-4 is a **reconstructed assumption** — not the paper's value, not the author's operational value (defaults 1 ep / 1e-4). |
| **Upstream documentation error** | the recovery plan L161 and Recovery Prompt L63 label 20/5e-4 as "Paper:", with **no source**. Corrected this round. |
| **Implementation identity** | only **NLinear is canonical**. PatchTST is **INSPIRED**, CALF/TimeCMA/Qwen are **INSPIRED/adaptation**. Using the official repo does **not** make them official implementations. |
| **`notext` is not a non-LLM** | it keeps the GPT-2 backbone and LoRA; counting it in the non-LLM group would pollute the mean. |
| **Exposed Test** | every Test result is **retrospective**. |
| **Remaining seeds** | Track A has 3 of the paper's 10; 88 fits missing. |
| **Quota** | Stage 6 has **1.1744 GPU-h** left; the 10-seed extension needs ≈1.84 → **over budget**. |
| **No untouched holdout** | **no genuinely unseen interval exists**; renaming an old interval is forbidden. Track C cannot proceed. |
| **A0 incomplete** | only a 1-epoch / itr=1 / L=24 minimum diagnostic. |
| **A1 repetitions insufficient** | 1 of 10 per horizon. The full 40-fit set costs **11.27 GPU-h** (measured 0.2817/fit); only **0.056** remained. |
| **Regional / few-shot / Tables VI, VII, IX** | **never run**; must be declared as not-run, not dropped from the denominator. |
| **Git traceability** | single-commit repo with uncommitted model changes → **the training-time code version cannot be restored**. |
| **scratch quota exceeded** | `mmlsquota`: **413 GB used / 300 GB quota**, `grace=expired`. `/gpfs1/scratch` writes fail intermittently; all output moved to `/gpfs1/home/`. The big consumers (`innovation_deploy_root_v3_*`, 52+50+11+11+9.7+9.6x6 GB) were **not deleted** by this round - user decision needed. |
| **Group interpretation** | four fixed implementations per group are **not a random sample**; group means must not be read as inferences about LLM / non-LLM families. |

---

## §I Deliverables (22 items)

| # | File | Status |
|---|---|---|
| 1 | `STATUS_BEFORE_CONTINUATION.md` | ✅ |
| 2 | `REPOSITORY_PROVENANCE.md` | ✅ |
| 3 | `HYPERPARAMETER_PROVENANCE.md` | ✅ |
| 4 | `DEVIATION_LEDGER.md` | ✅ |
| 5 | `TEXT_PATH_RESOLUTION.md` | ✅ (CPU verdict final; GPU review PENDING) |
| 6 | `IMPLEMENTATION_IDENTITY.md` | ✅ |
| 7 | `RUN_MANIFEST.csv` | ✅ 118 rows |
| 8 | `REMAINING_RUN_MATRIX.csv` | ✅ 51 rows |
| 9 | `author_paper_targets.csv` | ✅ |
| 10–11 | `reproduction_results_per_seed.csv` / `_aggregate.csv` | ✅ 116 / 11 rows |
| 12 | `paper_vs_reproduction.csv` | ✅ (carries the "not a reproduction" note) |
| 13–16 | `benchmark_results_{per_seed,per_horizon,per_variable,average_4L}.csv` | ✅ |
| 17 | `paired_stats_corrected.csv` / `.md` + `SCORING_CORRECTION_NOTE.md` | ✅ (4 unit tests pass) |
| 18 | `cost_summary.csv` | ✅ |
| 19 | `failures_and_retries.csv` | ✅ |
| 20–21 | `REPORT_ZH.md` / `REPORT_EN.md` | ✅ |
| 22 | `scripts/probe_text_path_deterministic.py`, `scripts/score_predictions_independent.py`, `scripts/paired_stats_corrected.py`, `slurm/*.sbatch`, `slurm/submit_all.sh` | ✅ **written, not submitted** |

Also: `indep_scorer_*.csv/json`, `text_path_probe_cpu_local*.json`, `build_deliverables.py`

---

## §J Next minimal actions

1. **[needs the user]** restore HPC network access (VPN / jump host).
2. **[first HPC command]** `ssh cityu 'squeue -u $USER; sacct -S 2026-09-26 -X'` → confirm no leftover jobs; **do not resubmit identical runs**.
3. **[HPC]** `bash slurm/submit_all.sh` → CPU probe → GPU probe → comparison; the A1 array is commented out pending budget confirmation.
4. **[local]** after any result lands, run `scripts/score_predictions_independent.py` and `scripts/paired_stats_corrected.py`.
5. **[supervisor decision]** (i) is there a genuinely untouched generalisation interval; (ii) is a full A0 replay authorised; (iii) is the Track A extension to 10 seeds authorised (≈1.84 GPU-h, over budget).

**Until HPC access returns, no training, evaluation or reproduction may be claimed as complete.**