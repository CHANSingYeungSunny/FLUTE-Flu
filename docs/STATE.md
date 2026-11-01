# docs/STATE.md — what is true now (numbers, artefacts, code entry points)

> **What this is:** the current measured state of the project, moved *verbatim* out of `AGENTS.md` — §0 project identity, §1.1 reproduction, §1.2 benchmark rankings, §1.3 artefact list, §5 key code entry points, §12 context-engineering note. Nothing was re-typed, summarised or re-numbered; the original § numbers are kept so old cross-references still resolve.
> **When to read it:** immediately after `AGENTS.md` in every session, and any time you need a number, an artefact path, or a script entry point.
> **What it points to:** `docs/LEDGER.md` (the dated history behind every number), `docs/WORK_BREAKDOWN.md` (what is not done yet, §11 + §13), `docs/HPC_RUNBOOK.md` (how to run anything), `docs/AUTHOR_REPO_FIDELITY.md` (what matches the author repo), `docs/LLM_ARMS.md` (LLM roster/env), `docs/METHODOLOGY_METRICS_AND_SPLIT.md` (why the metrics are what they are), `paper_tables/*.csv` (the measured tables), `hpc_results/expanded_runs/**/pred_*.npz` (the raw predictions every table derives from).
> **Depends on:** `AGENTS.md` (R1–R6 and the 13 hard rules of §2 are normative), `docs/METHODOLOGY_METRICS_AND_SPLIT.md`, `docs/BENCHMARK_MODEL_ROSTER.md`.
> **Chain:** `AGENTS.md` → **this file** → `docs/LEDGER.md` → the specific evidence file named in the ledger row.

**Contents of this file:** §0 what the project is · §1.1 reproduction · §1.2 benchmark + peak-skill rankings · §1.3 generated artefacts · §5 key code entry points · §12 context-engineering note.

---

## 0. What this project is

**CHAN Sing Yeung Sunny — Final Year Project (2026), CityU HK.**
An **independent reproduction + benchmark + innovation** study of

> Moon, Shim, Kim & Hwang, *MIFlu: Large Language Model-Based Multimodal
> Influenza Forecasting Scheme*, IEEE JBHI 29(10):7790–7801 (2025).

Dataset: **US CDC National-Illness** (weekly, 2002–2021, 7 variables), **not Hong Kong**.
Working directory: `C:\Users\Asus\Desktop\FYP code\MLFlu`.
Author repo (verbatim copy): `recovery/author_repo/`.

### The three deliverables
1. **Reproduction** — reproduce the paper's Table V (MIFlu, 4 horizons, 7-variable
   aggregate MSE/MAE) from the author's released code.
2. **Benchmark** — compare MIFlu against a wide model set, ranked on
   **peak skill (PTE/PIE) on ILITOTAL**, not just MSE.
3. **Innovation** — built on top later.

---

## 1. CURRENT STATE (2026-11-01)

### 1.1 Reproduction — **essentially complete, target met**

| L | ours (10-rep mean) | paper Table V | Δ |
|---|---:|---:|---:|
| 24 | **1.3045** | 1.542 | −15.4% |
| 36 | **1.3561** | 1.422 | −4.6% |
| 48 | **1.6543** | 1.414 | +17.0% |
| 60 | **1.6829** | 1.364 | +23.4% |
| **4-horizon mean** | **1.4995** | **1.4355** | **+4.5%** ✅ |

Project's own success criterion was ≤5% → **met**. But note the **sign crossover**:
we beat the paper at L24/36 and lose at L48/60. This is attributed to (a) we select
checkpoints on **validation**, the authors select on **test** (`main_ILI_lora.py`
L211/L225), and (b) training-budget/epoch differences. The reported claim must be
"4-horizon mean within +4.5%, with a systematic short/long crossover", never
"we beat the paper".

MAE (L24): 0.7482 vs paper 0.726 (+3.1%); (L36): 0.7712 vs 0.779 (−1.0%).
**MSE and MAE disagree in sign at L24** → evidence that MSE is outlier-sensitive.

> **Window-count disclosure.** The released code's test loader sets `drop_last=True`,
> so test metrics cover **160 of 170 windows**; the paper's Table V figures are
> computed on the same subset, and our reproduction is therefore compared
> **like-for-like**.
>
> **RULING 2026-11-01 — the evaluation window set is now identical for everything.**
> Because those 10/14/2/6 discarded windows are anomalously hard (measured: full-170
> MSE = **1.4111×** the first-160 MSE on four L24 MIFlu seeds, per-seed 1.3929–1.4423),
> **every model, every horizon, every table and every figure** is now scored on the
> first `(W // 16) * 16` test windows — MIFlu's own set: **160 / 144 / 144 / 128** at
> L = 24/36/48/60 (available 170/158/146/134). One definition lives in
> `scripts/eval_windows.py::eval_slice`; `n_eval_windows` is carried by every row of
> every table and asserted uniform across arms at each horizon. All benchmark numbers
> below were **re-derived** under this rule (pre-ruling tables are frozen as
> `paper_tables/BENCH_*.pre_evalwindow16.csv`). MIFlu's benchmark row must therefore
> land on its reproduction values exactly — checked by
> `scripts/verify_miflu_oracle.py` (tolerance 1e-5 against the per-seed oracle).

### 1.2 Benchmark — 192 cells complete, all on disk

**Hardware: all 204 cells are A100-SXM4-80GB — the V100 confound is CLOSED (2026-11-01, §1.5).**
`paper_tables/BENCH_GPU_PROVENANCE.csv`: 192 cells from job 715984 (`gpu-a100-05`) + the 12
NLinear cells re-run in job **719191** (`gpu-a100-04`) = **204 A100, 0 non-A100**.

`hpc_results/expanded_runs/` — 16 models × 4 horizons × 3 seeds (42/43/44) +
12 NLinear cells = **204 `pred_*.npz`** (each: `pred`, `target` (W,7,L),
`target_start_row`, `L`, `seed`, `var_cols`, `model`, `profile`, `containment`, `space`).

**All numbers below are scored on the shared evaluation windows 160/144/144/128
(re-derived 2026-11-01, `scripts/eval_windows.py`; the pre-ruling values are in
`paper_tables/BENCH_*.pre_evalwindow16.csv`).**

**MSE ranking (7-var, z-space), DLinear excluded:**

| # | model | family | mean | L24 | L36 | L48 | L60 |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | PatchTST | transformer | **1.6621** | 1.4402 | 1.6154 | 1.9288 | 1.6640 |
| 2 | NLinear | linear | 1.8716 | 1.7971 | 1.7950 | 1.9574 | 1.9368 |
| 3 | DNN | neural | 2.1415 | 1.8920 | 1.7684 | 2.2603 | 2.6451 |
| 4 | TimeCMA | llm | 2.6081 | 2.3281 | 2.5794 | 2.7104 | 2.8146 |
| 5 | GradientBoosting | classical | 3.6645 | 3.5658 | 3.6867 | 3.6533 | 3.7521 |
| 6 | KNN | classical | 3.7854 | 3.7231 | 3.7623 | 3.7740 | 3.8820 |
| 7 | RandomForest | classical | 3.8901 | 3.5486 | 3.8251 | 4.0159 | 4.1710 |
| 8 | iTransformer | transformer | 3.9945 | 3.7656 | 4.0596 | 4.0438 | 4.1088 |
| 9 | DecisionTree | classical | 4.3198 | 4.5340 | 4.1380 | 4.2186 | 4.3884 |
| 10 | GRU | neural | 4.8870 | 4.2895 | 5.3099 | 5.1751 | 4.7736 |
| 11 | LSTM | neural | 5.0088 | 4.4965 | 5.1359 | 5.2088 | 5.1939 |
| 12 | RNN | neural | 5.0674 | 4.4222 | 5.2893 | 5.3424 | 5.2157 |
| 13 | Qwen-Time | llm | 5.2557 | 4.7190 | 5.1325 | 5.6894 | 5.4818 |
| 14 | SVR | classical | 5.3388 | 5.2248 | 5.3581 | 5.3781 | 5.3940 |
| 15 | CALF | llm | 5.5785 | 5.3624 | 5.5113 | 5.6442 | 5.7962 |
| 16 | CNN | neural | 5.6155 | 5.5021 | 5.3098 | 5.2801 | 6.3698 |

**Peak-skill ranking (K&S: PTE ≤ 1 wk AND PIE ≤ 25%), 16 cells per model:**

| # | model | pass/16 | PTE≤1wk | PIE≤25% | mean PTE | mean PIE |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **NLinear** | **4** | 4 | **16** | 1.68 | **9.5** |
| 2 | PatchTST | 0 | **6** | 0 | **1.24** | 32.8 |
| 3 | RNN | 0 | 4 | 0 | 2.48 | 60.7 |
| 4 | GRU | 0 | 2 | 0 | 2.49 | 61.1 |
| 5–16 | DNN, Qwen, TimeCMA, DT, GB, LSTM, RF, KNN, iTransformer, SVR, CALF, CNN | 0 | 0 | 0 | 2.1–6.6 | 42–82 |

**Key findings to write up:**
- NLinear is the **only** model meeting K&S, and only at **step 0 (1 week ahead)**,
  for all four horizons. From step 1 (2 weeks) onward, *every* model fails.
- **Timing is achievable, intensity is not**: PatchTST has the best timing (1.24 wk,
  6/16 within a week) but **PIE 0/16** (33% mean); NLinear is the mirror image.
- **MSE champion ≠ peak champion** (PatchTST vs NLinear) — both champions are
  **unchanged** by the evaluation-window ruling, and the MSE ordering of all 16 arms is
  also unchanged; what moved is the magnitude (per-model full-170 / first-N ratio
  0.9887–1.1800, mean 1.0204) and the K&S cells (PatchTST's PTE≤1wk count 7 → 6).
- At step 0, NLinear's mean MSE (0.2226 over the four horizons) is **3.2× better**
  than PatchTST's (0.7027) — that short-lead dominance is *why* it wins K&S.

### 1.3 Generated artefacts (local, already produced)

| Path | Content |
|---|---|
| `paper_tables/BENCH_MSE_BY_MODEL_L.csv` | per model × L MSE/MAE (7-var + ILITOTAL + phys) |
| `paper_tables/BENCH_MSE_BY_STEP.csv` | per model × L × step |
| `paper_tables/BENCH_PTE_PIE_BY_STEP.csv` | per model × L × step, PTE/PIE/pass |
| `paper_tables/BENCH_KS_CHAMPION_DETAIL.csv` | **256 rows**, full K&S detail |
| `paper_tables/BENCH_MSE_BY_FAMILY.csv`, `..._BY_SIDE.csv` | aggregates |
| `results/bench_figures/*.png` | **64 figures** = 16 models × 4 horizons, 4 panels each (step 0–3), y = ILITOTAL patients, x = test week — drawn on **exactly the windows the tables score** (160/144/144/128), count printed in the figure subtitle |
| `results/bench_figures/pareto_frontier.png` | **Pareto frontier figure** (item ①) — 7-var aggregate MSE vs parameter count (log), Pareto step line, 11 parametrised models labelled, window counts printed in-figure; `scripts/plot_pareto.py` |
| `paper_tables/DENORMALIZED_MSE_MAE_BY_VARIABLE.csv` | per-variable physical MSE/MAE |
| `paper_tables/PER_STEP_PTE_PIE_BY_MODEL.csv`, `..._PER_SEASON.csv` | earlier, on frozen Track-C |
| `docs/METHODOLOGY_METRICS_AND_SPLIT.md` | **the metric/split rationale — cite this in the paper** |
| `docs/STATUS_20261031.md` | reproduction fix log + job history |
| `paper_tables/BENCH_SEASONAL_NAIVE.csv` | seasonal-naive baseline (52-week lag) under the same A2 protocol — 7-var z-space MSE/MAE per L on the shared evaluation windows: **5.5768 / 6.9446 / 6.5842 / 5.7471** at L=24/36/48/60, scored on 160/144/144/128 windows (`n_windows`, `n_windows_available`, `n_eval_windows` columns) |
| `paper_tables/BENCH_EFFICIENCY.csv` | Pareto/slope efficiency **+ `rel_improve_vs_seasonal_pct`** (per L, then mean over L) + `n_eval_windows_L24…L60`; slope **+0.1171**, R² **0.0223**, Pareto set {NLinear, PatchTST}, PatchTST **211×** the parameters for **11.2%** lower MSE; rel-improve PatchTST **+73.17%**, NLinear +69.62%, DNN +65.06% … CNN +8.46% |
| `paper_tables/BENCH_*.pre_miflu.csv` | **frozen pre-MIFlu backups** of the five benchmark tables (historical reference) |
| `paper_tables/BENCH_*.pre_evalwindow16.csv` | **frozen pre-ruling backups** (170/158/146/134 windows) of all 13 benchmark tables — rollback reference for the evaluation-window ruling |
| `paper_tables/BENCH_*.post_evalwindow16.csv` | **frozen post-ruling reference** (160/144/144/128 windows) — the bit-identity baseline every future re-run (e.g. the MIFlu merge) is checked against |
| `scripts/eval_windows.py` | **the ONE definition of the evaluation window set** (`eval_slice(W, batch=16) = (W//16)*16`, `crop()`, `assert_uniform()`), imported by every analysis/plot script; docstring cites `train_miflu.train_L`'s `drop_last=True` |
| `scripts/compare_evalwindow.py` | reports what the window ruling changed (per-model MSE before/after, both rankings, K&S counts) from the pre/post backups — the evidence file of the ruling |
| `scripts/verify_miflu_oracle.py` | asserts the MIFlu row equals its reproduction (oracle per-seed 7-var MSE, tolerance 1e-5 on the shared windows); oracle arithmetic verified now, npz check auto-runs once the 7-channel export is imported |
| `scripts/import_miflu_predictions.py` | MIFlu export → benchmark cell converter; **refuses to write** unless the windows and ground truth match an existing cell of the same L (`--check` verifies without writing). Handles the ILITOTAL-only CSV (`partial=True`), the 7-var 13-column CSV, and npz passthrough |
| `scripts/verify_bench_unchanged.py` | proves no *unexplained* change: bit-identity against `*.post_evalwindow16.csv`, row-completeness + reported deltas against the older freezes, DLinear absent, and `n_eval_windows` uniform per horizon; also re-derives all 64 (model, L) 7-var MSEs from the npz under the window rule (max |diff| 7.7e-09) |
| `docs/MIFLU_MERGE_BLOCKED_20261101.md` | why the MIFlu **row** is not merged yet: HPC down + all three local exports contradict §1.1 |
| `scripts/llm_encoder_backbone.py` | **the frozen-LLM adapter** (2026-11-01): `FrozenLLMEncoder` — per-channel prompt → frozen causal/instruct LLM (`requires_grad=False`, `eval()` always) → masked mean-pooled last hidden state → **ONE shared `nn.Linear(D, L)`** → `(B,7,L)`; chunked encoder pass (`--encoder-batch-size`), CPU-vector cache keyed by `(model_id, revision, prompt_sha256)`, provenance dict (model id, pinned revision sha, torch/transformers versions, encoder params, device). No arm is scored yet — see `docs/LLM_ARMS.md` §7 |
| `tests/test_llm_encoder_backbone.py` | **31 CPU unit tests** for the adapter: shape `(B,7,L)`, channel permutation, frozen-encoder bit-equality after `optimizer.step()`, `(W,7,L)` layout + transposed rejection, seed determinism, cache call-count, encoder-batch-size exactness, prompt/hidden-state/provenance guards. No GPU, no download, `import transformers` asserted absent |
| `_dryrun/llm_encoder/DRYRUN_RECORD.md` | CPU `--dry-run` wiring proof (L=24/seed=42, mock encoder): cell keys/shapes `(170,7,24)`, `check_cell_layout → W=170, n_eval=160`, `target` bit-identical to `calf_llm_L24_s42`; **the mock npz and its `metrics.csv` were deleted**, only the probe-only manifests are kept (rule 13(b)) |

---

### 1.5 Hardware provenance — the V100 confound is CLOSED (2026-11-01)

`paper_tables/BENCH_GPU_PROVENANCE.csv` now reads **204 cells, 204 A100-SXM4-80GB, 0 non-A100**:
192 cells from job 715984 (`gpu-a100-05`, `stingy`) and the 12 NLinear cells from job **719191**
(`gpu-a100-04`, `stingy`, A100-SXM4-80GB, COMPLETED, 00:00:53).

Those 12 cells were the **K&S champion**, so they were re-run rather than disclosed. The old set is
preserved in `hpc_results/expanded_runs_v100_nlinear/`; the before/after is
`paper_tables/BENCH_NLINEAR_A100_DELTA.csv` (`scripts/compare_nlinear_a100.py`), scored on the same
shared windows:

| metric | V100 | A100 | delta |
|---|---:|---:|---:|
| MSE 7-var z, 4-horizon mean | 1.8715832975 | 1.8715832984 | +8.9e-10 |
| PTE mean (16 cells) | 1.677083 wk | 1.677083 wk | 0 |
| PIE mean (16 cells) | 9.476573 % | 9.476573 % | +1.4e-07 pp |
| **K&S pass / 16** | **4** | **4** | **unchanged** |

NLinear is pure FP32 linear algebra with no cuDNN/TF32 path, so it is hardware-invariant: the
training agrees to 15 significant digits (`mse_all=2.085732936859131` in both runs) and the
predictions differ only in the last fp32 bit. **The "only NLinear satisfies K&S" claim was
re-verified across all 16 arms on A100** — arms with at least one passing cell = **1 of 16**
(nearest PatchTST 0/16: PTE 1.240 wk but PIE 32.755 %).

Consequence for the paper: the table note may state **GPU = A100-SXM4-80GB, partition = `stingy`,
CityU HPC Burgundy** for every benchmark cell (§2 rule 13d), and no timing claim crosses a hardware
mix any more. The V100-era table contract is kept as
`paper_tables/BENCH_*.post_evalwindow16_v100nlinear.csv` (13 files) so history is not lost.

### 1.6 MIFlu export — 18/40 verified, controller queued on `stingy` (2026-11-01 21:50)

- **18/40 cells verified** (`.miflu_verify/*.json`): L24 seeds 2021–2030 (10), L36 2021–2026 (6),
  L48 2021, L60 2025. **The 22 missing cells** are L36 2027–2030, L48 2022–2030,
  L60 2021–2024 + 2026–2030 — all of them **retrains** (no export-only cell is left).
- Controller **719715** is **PENDING on `stingy`** with `MIFLU_WORKERS=1`, `--exclude=gpu-a100-05`,
  4 h wall, **12 600 s budget** (enough for all 22 cells in one window), `MIFLU_MAXGEN=1` so it does
  not queue a stray successor. Slurm reports `StartTime=2026-11-02T03:28:28` because **every healthy
  A100 of that partition is allocated** (measured `AllocTRES`): 719208 holds 4 GPUs on
  gpu-a100-03/06, 719397+705753 hold node 04, 719593+719356 hold node 05. The 4th GPU on
  **gpu-a100-05** is idle but that node is CUDA-dead and is excluded by policy.
- **WALL TIME IS NOT THE LEVER — the wall-time/backfill hypothesis is FALSIFIED (2026-11-01 21:55).**
  Everything was tested against `gpu_a100`: a 2 h job got `StartTime 02:50:39`, a **45 min** job
  **02:50:39**, a **25 min controller** (719695) **02:50:39**, and a **12 min controller** (719712)
  **02:50:39**. Shrinking the wall 10× changed nothing, so backfill is not the constraint —
  **there is simply no free GPU**: nodes 07/08/10/11/12 each show `gres/gpu:a100=4` of 4 allocated,
  and node 09 is `DOWN+DRAIN+NOT_RESPONDING`. The "cluster is not saturated" reading comes from
  CityU's `squeue` wrapper, which is **user-scoped** (`squeue -a -t R` returns 0 gpu rows for us
  while 20 GPUs are allocated); `scontrol show node … AllocTRES` is the authoritative view.
- Watcher **719716** (`tiny`, `miflu_chain_driver4.sh` with `MIFLU_PART=stingy`, `MIFLU_WALL=04:00:00`,
  budget 12 600) resubmits after a CANCEL-preemption; capped at **3 submissions / 10 h**, so it
  cannot thrash.
- **The 8 min/cell figure for 1 worker is a prediction, not a measurement**: 24 s/epoch × 20 epochs,
  and `train_miflu.py` has no per-epoch checkpoint, so a cell must finish inside one window. **No
  1-worker cell has completed on this cluster yet** — the 18 verified cells were produced by
  3-worker generations (and 4 export-only forward passes). Throughput is therefore unknown until
  719652 starts.

**§1.3a additions — part-two runners (2026-11-01 23:50).** These are **code**
artefacts, not results: no rolling-origin / Table VI / Table VIII / Table IX cell
exists on disk yet.

| artefact | what it is | reproduction command |
|---|---|---|
| `scripts/walk_forward.py` | rolling-origin splitter (`Fold`, `make_folds`, `resolve_split`, `restrict_data`, `add_fold_argument`); 5 folds on 966 rows, f5 = the published `676/773/966` split | `python scripts/walk_forward.py --rows 966 --k 5` |
| `scripts/train_regional.py` | Table VI harness (T=20, L in {2,3,5,10,13,15,20}, K=4, 50 ep, batch 32) writing the rule-11 set per cell under `hpc_results/regional/` | `python scripts/train_regional.py --preflight` |
| `scripts/build_table_ix.py` | Table IX = regional training time, aggregated from the cell manifests; exits 3 while nothing is measured | `python scripts/build_table_ix.py --check` |
| `hpc_experiments/weights_worker.py`, `cpu_download_worker.sh` | 11-arm weights fetcher: pinned revision, size, config sha256, incremental manifest, CPU hidden-state probe (OK/UNSUPPORTED + reason), resumable, self-requeue | `python hpc_experiments/weights_worker.py arms`; manifest `/home/sychan552/scratch/mlflu_weights/weights_manifest{_A,_B}.json` |
| `hpc_experiments/measure_llm_forward.py` | measured per-prompt encoder cost and projected per-cell wall (replaces the unanchored 900 s default) | `python hpc_experiments/measure_llm_forward.py --model-id Qwen/Qwen2.5-1.5B ...` |
| `hpc_experiments/make_llm_lanes.py` | one ready-to-`sbatch` 12-cell lane per **OK** arm, with env routing and an A100 assert | `python hpc_experiments/make_llm_lanes.py --manifest M --out-dir D` |
| `docs/QUEUE_ROWS_PART2.md` | the `task_id / kind / model / L / seed / priority / env / expected_artefact / gate` specification for every part-two row, plus the cost table | read it |
| tests | `tests/test_walk_forward.py`, `test_train_regional.py`, `test_miflu_ablations.py`, `test_cpu_download_worker.py`, `test_llm_probe_mode.py` (77 tests) | `python -m pytest -q tests/` → **512 passed, 5 skipped, 2 failed** (both pre-existing) |

## 5. Key code entry points

| File | Purpose |
|---|---|
| `scripts/miflu_model.py` | MIFlu model (author-faithful path, `use_text_ln=False`) |
| `scripts/train_miflu.py` | reproduction runner (`--profile author_repo_966`, `--text-source author_file`, `--learning-rate`, `--seed` default 2021) |
| `scripts/train_backbone_966.py` | benchmark backbone runner (exports `pred_*.npz`) |
| `scripts/train_classical_966.py` | sklearn arms (DT/RF/HistGB/SVR/KNN), imports A2 protocol verbatim |
| `scripts/analysis_expanded.py` | 192-cell analysis → MSE/step/PTE-PIE tables (DLinear filtered out), scored on the shared `(W//16)*16` windows, `n_eval_windows` on every row |
| `scripts/eval_windows.py` | **the single evaluation-window definition** — `eval_slice`, `crop`, `assert_uniform`; import this, never hard-code 160 |
| `scripts/plot_bench.py` | 64 four-panel figures, drawn on exactly the windows the tables score |
| `scripts/analysis_denorm_stepwise.py` | earlier per-variable denorm + per-season PTE/PIE |
| `scripts/analysis_postprocess.py` | v2.1 post-processing → efficiency (Pareto), CRPS/WIS, paired tests |
| `scripts/seasonal_naive_baseline.py` | 52-week-lag baseline under the A2 protocol + `rel_improve_vs_seasonal_pct` |
| `hpc_experiments/submit_controller.sh` | resumable benchmark controller (self-requeues) |
| `hpc_experiments/submit_author.sh` | MIFlu reproduction job |
| `hpc_experiments/probe_qwen38.sh` | Qwen3.8-27B-FP8 load test |
| `docs/METHODOLOGY_METRICS_AND_SPLIT.md` | metric/split rationale for the paper |
| `data/raw/COLUMN_MAP_national_illness.csv` | author column ↔ essay variable mapping |

---

## 12. CONTEXT-ENGINEERING NOTE (why this file exists)

Long agent runs decay at context-window boundaries. The established remedy is an
externalised scratchpad that is auto-injected, written on every change, and carries an
explicit definition-of-done — plus a **resume checklist** (§9) and a **ledger** (§10)
so that history is append-only. `AGENTS.md` at the repo root is that artifact because
this harness loads it as workspace instructions automatically; unlike a skill, it
cannot be skipped by simply not invoking it.

Practical rules that follow:
- Prefer writing a fact here over re-deriving it next session.
- Record **why** a decision was made, not only what was done (§3, §6).
- Record **failures** too (§4 gotchas) — they cost the most time to rediscover.
