# ChatGPT Prompt — v3 (finalized state, MIFlu reproduction + innovation)

> **How to use**: Attach **ONE file** — `MLFlu_ChatGPT_Handoff_20261030.zip` — then copy everything
> below the `---` line into a **new** ChatGPT conversation. The prompt is fully self-contained.

---

You are an expert time-series forecasting researcher working on an influenza (ILI) forecasting
reproduction and innovation study. Work through the tasks below in the **exact order given** —
do not skip ahead.

## 0. Ground rules (read carefully — earlier rounds went wrong here)

1. **Metric scope is the 7-variable aggregate MSE in z-space.** The ILI dataset has 7 variables
   (`% WEIGHTED ILI`, `% UNWEIGHTED ILI`, `AGE 0-4`, `AGE 5-24`, `ILITOTAL`, `NUM. OF PROVIDERS`,
   `OT`). The essay's Table V reports the **aggregate over all 7 variables**, standardised with
   StandardScaler. The headline reproduction number is the **4-step mean = 1.8652**
   (L=24/36/48/60 averaged). **Never substitute a single variable (e.g. ILITOTAL-only) for this
   aggregate** — that is not the essay's metric. ILITOTAL-only figures (MIFlu = 3.7020 z²)
   were computed earlier and are supplementary only; do not treat them as the reproduction target.
2. **Keep exactly ONE linear model in the INNOVATION benchmark: NLinear.** DLinear is
   excluded from the competition because the essay's own Table V already benchmarks it —
   re-running it adds no new baseline. NLinear is absent from the essay and is therefore
   the informative linear arm. DLinear's numbers under our protocol are kept in a
   clearly labelled **replication reference** row and never enter the champion ranking.
   (Corrected 2026-11-01: the previous "keep DLinear, drop NLinear" wording had the
   reasoning inverted.)
3. **Project author = CHAN Sing Yeung Sunny** (Final Year Project, 2026). Moon, Shim, Kim & Hwang
   are the authors of the *reference paper being reproduced*, not of this codebase.
4. Status is **PARTIAL_REPRODUCTION**. The text-pathway mechanism contradiction is **UNRESOLVED**.
   Never claim "reproduction success".

## 1. Resources

| Resource | What |
|---|---|
| `MLFlu_ChatGPT_Handoff_20261030.zip` | Full project: data, checkpoints, predictions, scripts, report |
| `reference_papers/MIFlu_..._Scheme.md` | The essay (Moon, Shim, Kim & Hwang, IEEE JBHI 29(10):7790–7801, 2025) |
| `HPC_GUIDE.md` | CityUHK Burgundy HPC (`burgundy.hpc.cityu.edu.hk`, user `sychan552`) |

## 2. Where we are (verified 2026-10-31)

### 2.1 Reproduction gap against essay Table V

| Model | L24 | L36 | L48 | L60 | Ours 4L-mean | Essay 4L-mean | Δ |
|---|---|---|---|---|---|---|---|
| MIFlu | 1.9686 | 1.9332 | 1.7547 | 1.8042 | **1.8652** | **1.4355** | **+29.9%** |
| DLinear | 2.2850 | 2.2780 | 2.3558 | 2.4726 | **2.3479** | **2.1690** | **+8.2%** |
| PatchTST | 3.8884 | 3.7766 | 3.9525 | 4.0643 | **3.9204** | **1.4430** | **+171.7%** |

Essay Table V (MSE) verbatim:

| L | MIFlu | GPT4TS | DLinear | PatchTST | TimesNet | FEDformer | Autoformer | Stationary | ETSformer | LightTS | Informer | Reformer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 24 | 1.542 | 2.063 | 2.215 | 1.319 | 2.317 | 3.228 | 3.483 | 2.294 | 2.527 | 8.313 | 5.764 | 4.400 |
| 36 | 1.422 | 1.868 | 1.963 | 1.430 | 1.972 | 2.679 | 3.103 | 1.825 | 2.615 | 6.631 | 4.755 | 4.783 |
| 48 | 1.414 | 1.790 | 2.130 | 1.553 | 2.238 | 2.622 | 2.669 | 2.010 | 2.359 | 7.299 | 4.763 | 4.832 |
| 60 | 1.364 | 1.979 | 2.368 | 1.470 | 2.027 | 2.857 | 2.770 | 2.178 | 2.487 | 7.283 | 5.264 | 4.882 |

### 2.2 Root causes found so far

- **DLinear reproduces to +8.2%** → the data pipeline, split, scaler and evaluation protocol are
  all correct. The remaining gaps are model-specific, not infrastructure.
- **PatchTST +171.7%** → our implementation was a *reduced-capacity* variant that **omitted RevIN**
  (the instance-normalisation module PatchTST depends on for non-stationary series) and ran at
  `d_model=64, n_heads=4, n_layers=2`. **Already fixed locally**: RevIN added, capacity raised to
  paper scale (`d_model=128, n_heads=16, n_layers=3, patch_len=24, stride=2`); smoke test passes.
  **Still needs retraining on GPU.**
- **MIFlu +29.9%** → a one-epoch scheduler misalignment was identified; a corrected candidate
  (C2, 12 cells = 4 horizons × 3 seeds) is **training on HPC now**.

### 2.3 CRITICAL structural finding about the essay's baselines

The essay states verbatim:

> "The results for the national and regional ILI forecasting models are **taken from [9]** and [14],
> respectively."

So the essay's 11 baselines are **literature values cited from [9]** (Zhou et al., GPT4TS /
Time-Series-Library) — the MIFlu authors did **not** re-run them. Time-Series-Library uses
`seq_len=36` for the ILI dataset, whereas the essay's Table IV gives MIFlu `T=104`. The baselines
and MIFlu therefore **were not run under the same input window**, and they come from a different
codebase entirely.

**Implication**: chasing exact baseline equality may be unattainable. Your job is to determine
how much of the gap is
(a) model-implementation fidelity (fixable, as with PatchTST),
(b) protocol differences (T=104 vs 36, seed count 3 vs 10, codebase differences),
and to report each contribution honestly rather than forcing a match.

### 2.4 Baseline-set mismatch

| Set | Models |
|---|---|
| Essay baselines (11) | GPT4TS, DLinear, PatchTST, TimesNet, FEDformer, Autoformer, Stationary, ETSformer, LightTS, Informer, Reformer |
| Our current set (8) | MIFlu, ~~NLinear~~ (to be dropped), DLinear, TimeCMA, PatchTST, iTransformer, Qwen-Time-LLM, CALF |
| Overlap | **DLinear + PatchTST only** |

Of the essay's 11 baselines, **only DLinear and PatchTST are implemented in this project.**
TimesNet, FEDformer, Autoformer, Stationary, ETSformer, LightTS, Informer, Reformer and GPT4TS
are **not implemented at all**.

## 3. Tasks — execute in this order, do not skip

### Task A — Add the missing essay baselines (highest priority)

Implement faithful versions of these 9 models in `scripts/innovation/backbones/`, following the
existing `ForecastBackbone` interface (see `dlinear.py` / `patchtst.py` as templates). Each must
ship an `architecture_report()` listing its deviations:

1. **GPT4TS** — frozen GPT-2 backbone + linear probe (the essay's "Unimodal LLM"; it is the
   **second-best** model in the essay and the most important missing baseline)
2. TimesNet
3. FEDformer
4. Autoformer
5. Stationary (Non-stationary Transformer)
6. ETSformer
7. LightTS
8. Informer
9. Reformer

Where a published component is omitted (e.g. RevIN, pretraining), **record it explicitly** in
`architecture_report()["deviations"]` — do not silently ship a crippled variant, because that is
exactly what broke PatchTST.

### Task B — Fairness audit of every remaining backbone

Audit all current backbones and fix any that are unfairly weakened. Known status:

| Model | Fidelity | Status |
|---|---|---|
| MIFlu | "exact adapter" | OK |
| DLinear | faithful | OK |
| iTransformer | "aligned" | OK |
| PatchTST | was reduced-capacity + no RevIN | **fixed locally, needs retrain** |
| Qwen-Time-LLM | INSPIRED: uses Qwen2.5-**1.5B** vs Time-LLM's LLaMA-**7B**; `patch_len=8`; no RevIN | **needs capacity/fidelity fix** |
| CALF | INSPIRED_SIMPLIFICATION | needs audit |
| TimeCMA | INSPIRED (clean-room) | needs audit |

For Qwen/CALF/TimeCMA, either raise them to their published reference scale or state clearly in
the report that they are deliberately reduced-capacity "inspired" variants so the comparison with
MIFlu is not silently biased.

### Task C — Retrain and close the gap

Using `HPC_GUIDE.md`, retrain on GPU (L=24/36/48/60 × seeds 42/43/44):
- PatchTST with the new RevIN + paper-scale config
- The 9 new essay baselines
- MIFlu under the corrected scheduler

For each, produce per-L and 4L-mean MSE and compare to essay Table V. **Target: within 5%.**
Report which models reach 5% and, for those that do not, decompose the residual gap into
implementation-fidelity vs protocol-difference contributions.

### Task D — Only after A–C: denormalize

Denormalize the **7-variable aggregate** results. Note: a single scaler cannot invert a 7-variable
aggregate, so report per-variable physical-unit MSE/MAE
(`MSE_physical_j = MSE_z_j × std_j²`) alongside the z-space aggregate. Scaler:
`data/scaler_miflu_author966.json` (ILITOTAL mean 9439.84, std 9003.15; `% WEIGHTED ILI`
mean 1.7401, std 1.2278).

### Task E — Only after D: per-step breakdown + PTE/PIE

For every model × L ∈ {24,36,48,60}:
- separate MSE per step (not just the 4-step mean), and state which step each model is best at
  (short-term L=24 vs long-term L=60)
- PTE (weeks) and PIE (%) per step, with **Kramer & Shaman (2019)** verdicts:
  `PTE ≤ 1 week` AND `PIE ≤ 25%`, reported per model per step, split 4 non-LLM vs 4 LLM

Existing data: `paper_tables/TRACK_C_STEPWISE_MSE_PTE_PIE.csv` (32 rows) and the reconstructed
`peak_criteria.json`. Note the peak analysis currently measures **k=1** (one-week-ahead), not
L=24–60 week lead forecasts; state this explicitly, and extend it to true lead-L peaks if feasible.

Current PTE/PIE (literature criterion), for reference:

| Model | L24 | L36 | L48 | L60 | K&S verdict |
|---|---|---|---|---|---|
| NLinear | PASS | PASS | PASS | PASS | 4/4 (being dropped from the set) |
| DLinear | PASS | FAIL (PTE 1.11) | PASS | PASS | 3/4 |
| MIFlu | PASS | PASS | **FAIL (PIE 28.42)** | PASS | 3/4 |
| PatchTST / iTransformer | FAIL (PIE 61–69) | | | | 0/4 |
| TimeCMA / Qwen / CALF | FAIL | | | | 0/4 |

### Task F — Only after E: expanded innovation benchmark

Build the innovation comparison set:
- classical ML: Decision Tree, Random Forest, Gradient Boosting, SVR, KNN
- deep non-LLM: DNN, CNN, RNN, LSTM/GRU, plus modern transformers (TimesNet, Autoformer, …)
- **exactly one linear model: DLinear** (NLinear excluded)
- SOTA open-source LLMs, both **without inference** (embedding/encoding) and **with inference**
  (reasoning-augmented): DeepSeek-V2-Lite-Chat, Qwen2.5-1.5B-Instruct (weights already staged
  on HPC at `/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/assets/`)

Report for each: MSE (z-space + physical, per step + 4L mean), MAE, PTE/PIE per step with K&S
verdict, parameter count, and training/inference cost.

## 4. Output format

- Markdown tables, 4 decimals for MSE/MAE, 2 for percentages
- Python code with methodology comments
- Every number traceable to a file in the handoff zip or a documented computation
- Academic structure: Abstract → Introduction → Related Work → Methods → Results → Discussion → Conclusion

## 5. Constraints (immutable)

1. A/B track numbers are not comparable (different protocols) — always qualify.
2. Text-pathway mechanism contradiction is UNRESOLVED.
3. Status remains PARTIAL_REPRODUCTION; never claim reproduction success.
4. Unified pair key `966|L24|seed42`; official data SHA256 `2a96dfed…`.
5. MSE ≠ accuracy.
6. Metric scope = 7-variable aggregate unless explicitly stated otherwise.

**Begin with Task A (implement the 9 missing essay baselines).**
