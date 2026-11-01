# SKILL.md — the MIFlu reproduction + benchmark playbook

> **What this is:** the *procedural* memory of this project — every methodological
> decision that was measured, ruled on, or discovered the hard way, written so a future
> agent can reproduce it instead of re-deriving it. It is deliberately **not** the
> state file and **not** the loop:
>
> | File | Role |
> |---|---|
> | `AGENTS.md` | **state** — protocol R1–R6, the 13 hard rules, current numbers, the map |
> | `SKILL.md` (this file) | **how** — the decisions, their justification, and the traps |
> | `LOOP_ENGINEERING.md` | **process** — the iteration loop, RAG order, failure protocol |
> | `docs/LEDGER.md` | **history** — append-only dated rows, one per state change |
>
> **When to read it:** before writing or re-running any analysis/plotting code, before
> importing or merging anywhere a MIFlu number could land, before writing the paper's
> methodology section, and at the start of a session that intends to *change* a number
> rather than only quote one.
> **Depends on:** `AGENTS.md` §2 (the 13 hard rules are normative; this file never
> overrides them).
> **Chain:** `AGENTS.md` → **`SKILL.md`** → `docs/STATE.md` / `docs/METHODOLOGY_METRICS_AND_SPLIT.md`
> → `docs/LEDGER.md` → the individual evidence file.

---

## 1. When to use this skill

Use this skill for any task that touches the *science* of this repository: re-deriving a
benchmark table or figure, importing a new model's predictions into the comparison,
reproducing Table V, choosing seeds or hardware for a run whose number may reach the
paper, deciding what a number may be called in a caption, or writing the methodology /
fidelity section of the report. It is the file that answers "why is the window count
160?", "why are there two seed protocols?", "may I report this GPU wall-clock?", and
"why does the author's code give 1.3045 instead of the paper's 1.542?". Do **not** use it
for cluster mechanics (that is `docs/HPC_RUNBOOK.md`), for the current values of numbers
(that is `docs/STATE.md`), or for what remains to be done (that is
`docs/WORK_BREAKDOWN.md`).

---

## 2. The single dataset and its identity proof

**Canonical source = the author repository's own CSV**, copied verbatim into this repo:

| fact | value |
|---|---|
| file | `data/raw/national_illness_author_repo_966.csv` |
| SHA-256 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` |
| shape | **966 rows × 8 columns** |
| columns | `date` (weekly timestamp) + `1, 2, 3, 4, 5, 6, OT` (7 numeric channels) |
| coverage | US CDC National-Illness, weekly, 2002–2021 (**not Hong Kong**) |

`data/raw/COLUMN_MAP_national_illness.csv` holds the author-column ↔ essay-variable
mapping, which must be used whenever a name rather than an index is needed:

| author column | variable | unit | role |
|---|---|---|---|
| `1` | `% WEIGHTED ILI` | % of visits | population-weighted ILI signal |
| `2` | `% UNWEIGHTED ILI` | % of visits | unweighted variant |
| `3` | `AGE 0-4` | patients | age-stratified burden |
| `4` | `AGE 5-24` | patients | age-stratified burden |
| `5` | **`ILITOTAL`** | **patients** | **the benchmark target** (the paper's Fig. 7 series) |
| `6` | `NUM. OF PROVIDERS` | count | reporting coverage |
| `OT` | `OT` | count | 7th channel (Time-Series-Library target-name leftover) |

**Two profiles exist and they read different files** (`scripts/configs.py::resolve_profile`):

| half of the project | profile | file read |
|---|---|---|
| reproduction (Table V) | `author_repo_966` | `national_illness_author_repo_966.csv` — the author's file, byte-for-byte |
| benchmark (all 204 cells) | `author_966` | `national_illness_raw_paper_exact.csv` — a reprocessed copy (966 × 9, named columns + `epiweek` / `release_date`) |

**The 7 numeric channels are bit-identical between the two profiles.** Measured by
mapping the author columns onto the reprocessed names and differencing all 966 rows:
`max|diff| = 0.000e+00` and `n_diff = 0` for **every** channel (`% WEIGHTED ILI`,
`% UNWEIGHTED ILI`, `AGE 0-4`, `AGE 5-24`, `ILITOTAL`, `NUM. OF PROVIDERS`, `OT`). Only
column names differ, plus the metadata split into `epiweek` + `release_date`.

**The metadata columns are never model inputs**, because every training script builds its
channel list as

```python
cols = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
```

(`scripts/train_miflu.py`, `scripts/train_backbone_966.py`,
`scripts/train_classical_966.py`, and the historical scripts under `hpc_results/`).
Consequently the benchmark and the reproduction are computed on **exactly the same 7
series**, no data-identity re-run is needed, and the two halves are comparable.

**Canonical choice going forward: `--profile author_repo_966`.** New runs should point at
the author's file so that file-level conformance is literal; if a legacy benchmark cell is
re-run against it, the numbers reproduce (identical channels) at the cost of GPU hours.

**Split** (the author's own borders, `Dataset_Custom.__read_data__`): `num_train =
int(966·0.7) = 676`, `num_test = int(966·0.2) = 193`, validation = the remainder.
With `T = 104` and `containment="strict"` (the whole target block must lie inside its
split) that yields **549 / 74 / 170** windows at L = 24.

---

## 3. The evaluation-window rule — `(W // 16) * 16`, one set for everything

**The fact.** `train_miflu.train_L` builds its *test* loader as

```python
el = DataLoader(TensorDataset(Xte, Yte), batch_size=16, shuffle=False, drop_last=True)
```

`drop_last=True` silently discards the final partial batch, so only
`(W // 16) * 16` test windows are ever scored:

| L | test windows available | windows evaluated | discarded |
|---|---:|---:|---:|
| 24 | 170 | **160** | 10 |
| 36 | 158 | **144** | 14 |
| 48 | 146 | **144** | 2 |
| 60 | 134 | **128** | 6 |

**Why it matters.** Those discarded windows are **anomalously hard**: measured on four
L=24 MIFlu seeds, the full-170 MSE is **1.4111×** the first-160 MSE (per-seed ratios
1.3929–1.4423). A table that scores MIFlu on 160 windows and the other arms on 170 is
therefore not a comparison — it is a ~40 % handicap for one side.

**The ruling (user, 2026-11-01, non-negotiable).** *Every* model, *every* horizon, *every*
table and *every* figure is scored on the **first `(W // 16) * 16` test windows** — MIFlu's
own set. Pieces:

* **One definition:** `scripts/eval_windows.py::eval_slice(W, batch=16) -> (W // 16) * 16`.
  Import it; never hard-code 160 anywhere else. The module also provides
  `check_cell_layout` / `crop` (which assert the `(W, 7, L)` layout — window axis **0**,
  variable axis 1, lead axis 2 — before slicing, so a transposed array fails loudly) and
  `assert_uniform` (one count per horizon across all arms).
* **Every row states the count:** `n_eval_windows` (plus `n_windows_available` and, where
  useful, `windows_discarded`). At a given L it must be **identical for all arms** and
  equal to MIFlu's; the analysis scripts assert this, `scripts/verify_bench_unchanged.py`
  re-asserts it, and `scripts/verify_miflu_oracle.py` asserts it again across models.
* **Figures draw the same windows**, and the figure subtitle prints the count, so a figure
  cannot disagree with a table.
* **The MIFlu benchmark row must therefore equal its reproduction values exactly**
  (1.3045 / 1.3561 / 1.6543 / 1.6829), checked to **1e-5** against the per-seed oracle
  (`scripts/verify_miflu_oracle.py`). The per-seed oracle lives in that script and in
  `docs/LEDGER.md`.
* **Frozen references:** `paper_tables/BENCH_*.pre_evalwindow16.csv` (the 170-window-era
  values, rollback) and `BENCH_*.post_evalwindow16.csv` (the current contract, bit-identity
  baseline for every future re-run).

**Documented consequence.** The ruling moves every number but did **not** reorder the 16
arms: MSE champion stayed PatchTST (1.9613 → 1.6621) and the K&S champion stayed NLinear
(4/16, PTE 1.62 → 1.68 wk, PIE 10.1 → 9.5 %). What moved: per-model full-170 / window-set
ratio 0.9887–1.1800 (mean 1.0204), and PatchTST's `PTE ≤ 1 wk` count 7 → 6. Evidence:
`scripts/compare_evalwindow.py`.

**Pipeline order (the one that must not be reordered):**

```text
python scripts/analysis_expanded.py        # MSE / step / PTE-PIE tables + n_eval_windows
python scripts/analysis_postprocess.py     # efficiency, CRPS/WIS, paired tests (REGENERATES
                                           #   BENCH_EFFICIENCY.csv from scratch)
python scripts/seasonal_naive_baseline.py  # naive baseline + adds rel_improve_vs_seasonal_pct
                                           #   to BENCH_EFFICIENCY.csv — must be AFTER postprocess
python scripts/plot_bench.py               # 64 four-panel figures
python scripts/plot_pareto.py              # Pareto figure (asserts slope/R²/Pareto == the CSV)
python scripts/verify_bench_unchanged.py   # bit-identity vs *.post_evalwindow16.csv
python scripts/verify_miflu_oracle.py      # MIFlu row == reproduction (skips if not merged)
python scripts/compare_evalwindow.py       # what the window rule changed (report only)
```

---

## 4. Two protocols — never mixed

| | **reproduction** (Table V) | **benchmark** |
|---|---|---|
| purpose | reproduce the paper's Table V | compare MIFlu against the wider model set |
| repetitions | **10** | 1 fit per (L, seed) |
| seeds | **2021–2030** | **42, 43, 44** |
| reported number | mean over the 10 reps | mean over the 3 seeds (± sd, `n_seeds` in the caption) |
| metric | 7-variable aggregate MSE/MAE in **z-space** | 7-var MSE for the table axis; **PTE/PIE on ILITOTAL** for peak skill |
| location | `author_runs/L{L}_s2021/`, `ckpt_L{L}_s2021/` | `hpc_results/expanded_runs/<model>_L{L}_s{S}/` |
| numbers | 1.3045 / 1.3561 / 1.6543 / 1.6829 | see `docs/STATE.md` §1.2 |

Never use an artefact from one protocol as a row of the other (`AGENTS.md` §2 rules 9–10).
`author_runs/L{L}_s2021_pred/` is reproduction-protocol, single-seed, and its CSVs are
deliberately named `repro_pred_L{L}.csv` so a benchmark glob cannot pick them up.

**One documented exception — MIFlu.** MIFlu's benchmark row **is** its reproduction run
(10 reps, seeds 2021–2030), because the paper must report ONE MIFlu instance rather than
two. Consequences that must be stated in the caption:

* MIFlu's row is a 10-rep mean while the other 16 arms are 3-seed means;
* MIFlu is therefore **excluded from the paired sign-flip tests** (no matched cells exist);
* no other model may deviate from its protocol's seed set.

---

## 5. Hardware policy — the GPU and the partition are part of the result

* **Publication-grade runs only on an A100, in the `stingy` partition** of CityU HPC
  *Burgundy* (A100-SXM4-80GB, sm_80, TF32 on). `gpu_a100` is acceptable **only** if its
  queue start is short — it has been booked many hours to a full day ahead.
* **Every other partition or GPU model is probe-only** (feasibility: "does it deploy,
  does it forward at all"). Probe runs are marked `probe_only=True` in their manifest and
  must **never** enter `paper_tables/*`, a figure, or a claim — discard the probe and
  re-run on A100/`stingy`.
* **Every manifest records, measured and never assumed:** GPU name
  (`torch.cuda.get_device_name(0)`), GPU count, compute capability
  (`torch.cuda.get_device_capability(0)`), Slurm partition, node (`SLURM_NODELIST`), job
  id (`SLURM_JOB_ID`), start/end timestamps + wall-clock seconds, and library versions
  (python / torch / transformers) plus the code identity.
* **No timing claim may cross a hardware mix.** The benchmark cells are 192 on
  A100-SXM4-80GB + 12 NLinear cells on V100-SXM2-32GB (`paper_tables/BENCH_GPU_PROVENANCE.csv`)
  — the V100 set is exactly the K&S champion, which is why that confound is still open.
* Pre-flight is mandatory: probe anywhere free, then **re-run the real pass on A100/`stingy`**.

---

## 6. Full-artefact contract — a run is incomplete until it writes everything

One execution must emit **all** of the following, in the same job (`AGENTS.md` §2 rule 11):

1. `results_*.csv` — MSE/MAE for the **7-variable aggregate**, **per variable**,
   **ILITOTAL-only**, and the **physical (de-normalised)** units;
2. **per-window predictions for all 7 variables** — `.npz` with `pred` / `target` shaped
   `(W, 7, L)` plus `target_start_row` (and `partial`, `space`, `profile`,
   `containment`, `var_cols`), and a CSV twin;
3. therefore everything PTE/PIE, CRPS/WIS, the paired tests and every figure need;
4. a **manifest** — seed, full config, library versions, wall-clock, parameter counts,
   **sha256 of the checkpoint actually used**, and the measured GPU/partition/node block
   of §5.

A run that saves only scalar metrics is **invalid**: delete it and re-run. Never "patch it
later" by retraining just to export predictions — the export costs as much as the original
training, so the original run was wasted (`AGENTS.md` §2 rule 11 exists because this
happened to 40 reproduction runs on 2026-11-01).

The exporter that satisfies the contract for MIFlu is
`hpc_experiments/export_miflu_all7.py` (forward pass only, no training); the importer is
`scripts/import_miflu_predictions.py`, which **refuses to write** unless the windows and
ground truth match an existing benchmark cell of the same L.

---

## 7. Metric definitions — what each number is, and is not

1. **7-variable aggregate MSE / MAE, z-space** — the **reproduction** metric. Fit the
   `StandardScaler` on the train slice only, then average the squared error over all 7
   channels and all leads. It is the only quantity Table V reports. **Never substitute
   ILITOTAL-only here**: it is ≈1.9–2.0× larger on the same predictions and therefore not
   comparable with the paper.
2. **PTE / PIE on ILITOTAL, de-normalised to patients** — the **benchmark peak** metric.
   PTE = |forecast peak week − observed peak week| in weeks; PIE = |forecast peak −
   observed peak| / observed peak, in %. Peaks are detected with
   `scipy.signal.find_peaks(prominence=0.15·range, distance=15)`; a forecast is matched
   within ±8 weeks. **Kramer & Shaman pass = PTE ≤ 1 week AND PIE ≤ 25 %** (conjunctive:
   good timing cannot compensate for bad intensity).
3. **Never de-normalise the 7-variable aggregate.** It is a *loss*, not a series:
   `OT`'s train mean is ≈493,629 and `% WEIGHTED ILI`'s is ≈1.74, so a "physical 7-var
   curve" would be ~97 % the `OT` curve and dimensionally meaningless. Curves are drawn for
   `ILITOTAL` only (as the paper's Fig. 7 does).
4. **CRPS / WIS** — parametric, from a Gaussian whose mean is the across-seed ensemble mean
   and whose sd is the across-seed ensemble spread. Deterministic arms have zero spread, so
   **σ is floored at 0.05 sd** (a forecast may not claim more certainty than that); WIS uses
   the Bracher et al. (2021) normalisation over the α ∈ {0.02 … 0.98} intervals. The **log
   score is diagnostic only** — it is dominated by the σ floor and must never be ranked.
5. **Efficiency** — the **Pareto frontier** in (MSE, parameter count), non-dominated in the
   sense "sort by params ascending, keep a model only when its MSE strictly improves on the
   best so far", plus the **OLS slope of MSE on log₁₀(parameters)** across the parametrised
   arms. Current values: slope **+0.1171** MSE per decade, R² **0.0223**, Pareto set
   **{NLinear 2,520; PatchTST 531,878}** — more parameters do *not* lower MSE.
6. **Relative to seasonal-naive** — `rel_improve_vs_seasonal_pct = (naive_MSE − model_MSE) /
   naive_MSE × 100`, computed per L and then averaged over L. The naive forecast repeats the
   value observed 52 weeks earlier, constant across leads, under the **identical** protocol
   (same profile, same train-only scaler, same windows, same `(W//16)*16` rule). Current
   naive MSE: **5.5768 / 6.9446 / 6.5842 / 5.7471** at L = 24/36/48/60; every arm beats it on
   the 4-horizon mean, but CALF and CNN do **not** beat it at L = 60 — report per horizon.

---

## 8. What must never be claimed

1. **No "we beat the paper".** The status is *reproduced within +4.5 % on the 4-horizon
   mean*, with a **sign crossover** (we are below the paper at L = 24/36, above at
   L = 48/60). The claim is the crossover, never a win.
2. **No single champion across scale classes.** MSE champion and peak-skill champion are
   different models (PatchTST vs NLinear) and that disagreement is a reported finding, not
   something to resolve away.
3. **No 7-variable number for a partial-channel export.** A cell that carries fewer than 7
   channels has `mse_7var_z = NaN` by construction (`partial_export=True`,
   `n_channels_used < 7`). Computing it by `nanmean` would silently forge a number.
4. **No timing claim across mixed GPUs** (see §5). Also no timing claim from a probe run.
5. **DLinear never appears** — not in a ranking, table, figure or aggregate. The paper's own
   Table V already benchmarks it; NLinear is the sole linear-family member.
6. **No cross-protocol table.** A-track (966 rows) and B-track (1025 rows) numbers are not
   comparable, and the paper's 1.4355 is a third protocol.
7. **No claim about the text pathway's mechanism** — the contradiction (GPU gradients
   non-zero vs CPU effect exactly zero) is unresolved.
8. **No "MIFlu row" until the oracle check passes** — if the merged row does not equal the
   reproduction values to 1e-5, the import or the window rule is wrong.

---

## 9. Known author-code defects (publishable evidence, and traps to avoid)

1. **Checkpoint selection uses the test set.** `main_ILI_lora.py` evaluates test every
   epoch (L211) and keeps the lowest-test-MSE checkpoint (L225) → leakage. **We select on
   validation** and disclose the deviation (`AGENTS.md` §2 rule 4).
2. **The test loader covers ONE variable.** Its `__len__` returns 170 rather than 170 × 7:
   the released evaluation loop reports a single-variable (ILITOTAL-ish) curve, not the
   7-variable aggregate the paper's Table V quotes.
3. **`freeze` is a no-op** — calling it does not actually freeze the intended parameters.
4. **The repo defaults reproduce GPT4TS, not MIFlu.** With `PEFT=0, multimodal=0` the
   released defaults give ≈**2.063** (the GPT4TS baseline), because LoRA and the text path
   are disabled. Never treat a default-config run as a MIFlu reproduction.
5. **The text embedding is a constant vector discarded after GPT-2** — every sample gets
   the same embedding, and its representation is thrown away downstream, so the "LLM
   pathway" cannot carry sample-specific information as written. This is why the mechanism
   claim in §8.7 is off limits.
6. **`drop_last=True` on the TEST loader discards windows** — the defect that produced §3:
   160 of 170 windows at L=24, and those 10 are ≈**1.4111×** harder (per-seed
   1.3929–1.4423 on four L24 seeds; e.g. seed 2022 1.201078 → 1.686578). Every published
   MIFlu test metric therefore covers 91 % of the test set. **Our response is uniformity,
   not disclosure-only**: we evaluate everything on the author's window set (§3), so the
   comparison is like-for-like and the row equals the reproduction exactly.
7. The paper never states epochs or learning rate ("set empirically"); the code and the
   paper's table disagree (1 epoch vs 20; lr 1e-4 vs 5e-4). We follow the code (20 epochs,
   lr 1e-4) and disclose it.

---

## 10. Pointers — where the rest of the memory lives

| Need | File |
|---|---|
| protocol, 13 hard rules, current 10-line state, the memory map | `AGENTS.md` |
| the numbers right now, artefact list, code entry points | `docs/STATE.md` |
| every dated state change, append-only | `docs/LEDGER.md` |
| definition of done, §13 A–G status, next actions, open questions | `docs/WORK_BREAKDOWN.md` |
| ssh/sbatch/paths/partitions/queue gotchas + the A100 checklist | `docs/HPC_RUNBOOK.md` |
| what matches the author repo at file/hash/parameter level, and the deviations to disclose | `docs/AUTHOR_REPO_FIDELITY.md` |
| LLM arm roster, `qwen3_5` / `mlflu_llm` environments, measured load tests, exclusions | `docs/LLM_ARMS.md` |
| metric and split rationale — **cite this in the paper**, incl. §4a the window rule | `docs/METHODOLOGY_METRICS_AND_SPLIT.md` |
| the iteration loop, RAG order, failure protocol | `LOOP_ENGINEERING.md` |
| the benchmark roster (names, families, provenance) | `docs/BENCHMARK_MODEL_ROSTER.md` |
| why the MIFlu row was withheld and what reconciled it | `docs/MIFLU_MERGE_BLOCKED_20261101.md` |
| the raw per-window predictions every table derives from | `hpc_results/expanded_runs/**/pred_*.npz` (204 cells) |

---

## 11. Open blockers (as of 2026-11-01, in the order they must be closed)

1. **The 12 NLinear cells are still on V100** (`gpu-v100s-04`, job 717950) while the other
   192 are A100 — and those 12 are the K&S champion's cells. `code/submit_nlinear_a100.sh`
   re-runs them on `stingy` A100 (preserving the V100 set in `expanded_runs_v100_nlinear/`)
   and aborts unless the measured GPU name contains `A100`; it is **QOS-blocked** while
   controller 719030 holds the single `stingy` slot. After it lands: regenerate
   `BENCH_GPU_PROVENANCE.csv`, assert 204/204 A100, and record the NLinear before/after
   deltas in the ledger — the ranking may move.
2. **The MIFlu benchmark row is not merged.** The 7-variable export exists
   (`hpc_experiments/export_miflu_all7.py`) and A100-only controller **job 719030** is
   producing the 27 missing reproductions (L36/48/60 × 10 reps; L24's 10 checkpoints are
   exported). Until then `scripts/verify_miflu_oracle.py` reports SKIPPED for the npz half.
3. **LLM arms have an adapter but no rows (updated 2026-11-01).** The *code-level*
   blocker is closed: `scripts/llm_encoder_backbone.py::FrozenLLMEncoder` loads a frozen
   causal/instruct LLM, mean-pools the last hidden state per channel and trains **one
   shared `nn.Linear(D, L)`**; `scripts/train_backbone_966.py --backbone llm_encoder`
   wires it into the A2 protocol (T=104, `containment="strict"`, 676/773 split, seeds
   42/43/44, `(W//16)*16` windows) and `--arm-label` keeps each model a separate row. It is
   unit-tested on CPU (`tests/test_llm_encoder_backbone.py`, 31 passed, no download) and
   dry-run proven (mock cell written, verified `(170,7,24)`, then deleted). **Still open:**
   per-model checkpoints + pinned revisions, the per-model venv (`mlflu_llm` for
   `qwen3_5`-family, `mlflu_hpc` otherwise), an A100-asserting wrapper + 12-cell loop, and
   the frozen feature table. Qwen3.8-27B is bf16 **54.73 GB** on an A100 (fp8 is
   dequantised on sm_80), so it needs the 80 GB cards and `--encoder-batch-size 1–2`.
   Per-model blockers: `docs/LLM_ARMS.md` §7.1.
4. **Rolling origin (5 folds) does not exist** — it needs retraining under a
   walk-forward split, and no current number may be called "rolling-origin".
5. **Table VI (regional HHS-10), Table VIII (ablations) and Table IX (training time) are
   not done.** Table IX is *regional* training time, so it depends on the Table VI
   configuration (T=20, L ∈ {2,3,5,10,13,15,20}, K=4, 50 epochs, batch 32) having actually
   been run and timed; national timings are a different table and must not be labelled IX.
