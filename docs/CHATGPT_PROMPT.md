# ChatGPT Prompt — MIFlu Reproduction Gap Analysis & Innovation Benchmark

> **How to use**: Copy everything below the `---` line into a new ChatGPT conversation. Attach the zip file `MLFlu_ChatGPT_Handoff_20261030.zip` when prompted. The prompt is self-contained — ChatGPT needs no prior context.

---

You are an expert time-series forecasting researcher specializing in influenza (ILI) surveillance, multimodal LLM-based forecasting, and reproducible science. You will work through a complete research pipeline: understand a reproduction project, diagnose why the reproduction deviates from the original paper, close the gap if possible, and then design and execute an expanded innovation benchmark suitable for a top-tier journal publication.

## 1. Your Inputs

You have access to three key resources:

1. **`MLFlu_ChatGPT_Handoff_20261030.zip`** — A complete handoff package of the MLFlu reproduction project. Extract and read it thoroughly. It contains:
   - `02_author_repo/` — The original MIFlu author code and data (including GPT-2 text embeddings `text_emb_label_0507_{24,36,48,60}.txt`)
   - `03_data/` — Official 966-row US CDC National-Illness dataset (`national_illness.csv`, SHA256 `2a96dfed…`), scaler parameters
   - `04_benchmark/` — Current benchmark results, authoritative report (DOCX/MD), peak criteria
   - `05_reproduction_audit/` — Full audit trail, R1C verification, SHA256 manifests
   - `06_scripts/` — Complete reproduction codebase (~111 Python scripts + tests)
   - `08_paper_tables/` — Authoritative TRACK_C tables (MSE/MAE rankings, per-horizon champions, PTE/PIE, etc.)

2. **`reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md`** — The full text of the target paper: Moon, Shim, Kim & Hwang, "MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme," IEEE JBHI 29(10):7790–7801, 2025 (DOI: 10.1109/JBHI.2025.3561214). The data are US CDC National-Illness (not Hong Kong). Read this carefully to understand the architecture, hyperparameters, and evaluation protocol.

3. **`HPC_GUIDE.md`** — Guide for running GPU training on the CityUHK Burgundy HPC cluster (`burgundy.hpc.cityu.edu.hk`, user `sychan552`, passwordless SSH). Use this for retraining models or running new experiments.

## 2. Project Context & Current State

### 2.1 What has been done

This is a **partial reproduction** of MIFlu on the official 966-row National-Illness dataset. The full pipeline (data → training → scoring → authoritative tables → report) is operational. The reproduction uses strict 966-row data with zero tolerance for missing values.

### 2.2 Paper's Table V (target values — MSE)

| L | MIFlu | GPT4TS | DLinear | PatchTST | TimesNet | FEDformer | Autoformer | Stationary | ETSformer | LightTS | Informer | Reformer |
|---|-------|--------|---------|----------|----------|-----------|------------|------------|-----------|---------|----------|----------|
| 24 | 1.542 | 2.063 | 2.215 | **1.319** | 2.317 | 3.228 | 3.483 | 2.294 | 2.527 | 8.313 | 5.764 | 4.400 |
| 36 | **1.422** | 1.868 | 1.963 | 1.430 | 1.972 | 2.679 | 3.103 | 1.825 | 2.615 | 6.631 | 4.755 | 4.783 |
| 48 | **1.414** | 1.790 | 2.130 | 1.553 | 2.238 | 2.622 | 2.669 | 2.010 | 2.359 | 7.299 | 4.763 | 4.832 |
| 60 | **1.364** | 1.979 | 2.368 | 1.470 | 2.027 | 2.857 | 2.770 | 2.178 | 2.487 | 7.283 | 5.264 | 4.882 |

- Paper MIFlu 4-step mean MSE: **1.4355** (this is the target)
- Paper averages over **10 repetitions** (seeds)
- MSE computed on **StandardScaler-normalized** data (z-space), NOT denormalized

### 2.3 Our Reproduction (TRACK_C — current)

**Overall MSE ranking (4-step mean, 3 seeds: 42/43/44):**

| Rank | Model | mean_MSE_4L | SD | mean_MAE_4L | Side |
|------|-------|-------------|-----|-------------|------|
| 1 | MIFlu | **1.8652** | 0.0916 | 0.8842 | LLM |
| 2 | NLinear | 2.0495 | 0.0299 | 0.9566 | non-LLM |
| 3 | DLinear | 2.3478 | 0.0040 | 1.0884 | non-LLM |
| 4 | TimeCMA-LLM | 2.6700 | 0.0177 | 1.0927 | LLM |
| 5 | PatchTST | 3.9205 | 0.0543 | 1.3826 | non-LLM |
| 6 | iTransformer | 3.9847 | 0.0317 | 1.3545 | non-LLM |
| 7 | Qwen-Time-LLM | 5.2196 | 0.0701 | 1.5784 | LLM |
| 8 | CALF-LLM | 5.5153 | 0.0307 | 1.6080 | LLM |

**Per-horizon MSE (each step separately):**

| L | MIFlu | NLinear | DLinear | TimeCMA | PatchTST | iTransformer | Qwen-T-LLM | CALF-LLM |
|---|-------|---------|---------|---------|----------|--------------|------------|----------|
| 24 | 1.9686 | 2.1008 | 2.2850 | 2.4541 | 3.8884 | 3.7511 | 4.6187 | 5.2711 |
| 36 | 1.9332 | 2.0277 | 2.2780 | 2.6432 | 3.7766 | 3.9813 | 4.9957 | 5.3431 |
| 48 | 1.7547 | 2.0033 | 2.3558 | 2.7203 | 3.9525 | 4.0343 | 5.6660 | 5.6149 |
| 60 | 1.8042 | 2.0664 | 2.4726 | 2.8625 | 4.0643 | 4.1721 | 5.5978 | 5.8321 |

**PTE/PIE aggregate (Kramer & Shaman 2019 criteria: PTE ≤ 1 week AND PIE ≤ 25%):**

| Model | Hit Rate% | Mean PTE (wk) | Mean PIE (%) | PTE≤1 & PIE≤25%? |
|-------|-----------|---------------|--------------|-------------------|
| NLinear | 100.0 | 0.28 | 3.14 | ✅ PASS |
| DLinear | 86.1 | 0.92 | 17.72 | ✅ PASS |
| MIFlu | 41.7 | 0.29 | 25.0 | ⚠️ BORDERLINE |
| Qwen-Time-LLM | 2.8 | 0.96 | 36.33 | ❌ FAIL (PIE) |
| TimeCMA-LLM | 0.0 | 1.38 | 50.44 | ❌ FAIL (both) |
| PatchTST | 0.0 | 0.67 | 66.61 | ❌ FAIL (PIE) |
| iTransformer | 0.0 | 0.72 | 66.16 | ❌ FAIL (PIE) |
| CALF-LLM | 0.0 | 0.93 | 81.25 | ❌ FAIL (PIE) |

**Key deviation**: Our MIFlu 1.8652 vs paper 1.4355 = **+29.9% higher**. Current verdict: `PARTIAL_REPRODUCTION`.

### 2.4 Scaler for denormalization

```
ILITOTAL: mean = 9439.84, std = 9003.15
% WEIGHTED ILI: mean = 1.7401, std = 1.2278
```

**IMPORTANT**: The paper computes National MSE/MAE in z-space (StandardScaler normalized) across **all 7 variables aggregated**. A single ILITOTAL scaler CANNOT denormalize the 7-variable aggregate MSE — you must first extract ILITOTAL-only errors (feature index 4), then apply `MSE_physical = MSE_z * std^2`. The physical unit for ILITOTAL is **patient counts** (MSE in patient-count²). For the 7-variable aggregate, report z-space only.

### 2.5 Paper architecture (key hyperparameters)

- **Forecasting LLM**: First K=6 layers of GPT-2 (national), K=4 (regional)
- **Low-rank dimension**: r=4
- **Input window**: T=104 (national)
- **Patch length**: Lp=24, Stride: S=2 (national)
- **Text embedder**: Full GPT-2 (same as forecasting LLM for knowledge alignment)
- **Training**: 20 epochs, batch size 16, lr=0.0005
- **Evaluation**: Mean of 10 repetitions

---

## PART A: Reproduction Gap Analysis & Closure

Your first task is to **diagnose and attempt to close** the 29.9% MSE gap (1.8652 → 1.4355).

### A1. Systematic gap decomposition

Analyze potential sources of deviation. For each, check against the codebase in `06_scripts/` and the audit trail in `05_reproduction_audit/`:

1. **Data split protocol**: Paper uses train/val/test splits. Verify our split boundaries match exactly (train_end=676, val_end=773, test from 773 onward on 966 rows). Check if the paper's 966-row data is identical to ours (SHA256: `2a96dfed…`).

2. **Number of repetitions**: Paper averages 10 runs. We used 3 seeds (42/43/44). Running more seeds may reduce variance but likely won't shift the mean by 30%.

3. **Architecture fidelity**: 
   - Verify GPT-2 layer count (K=6), low-rank adaptation (r=4), patch length (Lp=24), stride (S=2)
   - Check if our GPT-2 text embeddings (`text_emb_label_0507_{24,36,48,60}.txt`) match what the paper used
   - Verify the fusion mechanism (cross-attention or concatenation?)

4. **Training protocol**:
   - Epochs (20), batch size (16), learning rate (0.0005)
   - Optimizer (Adam? AdamW?), scheduler, warmup
   - Loss function (MSE? MAE? Huber?)

5. **Normalization**: Confirm StandardScaler fits on train split only (mean/std from rows 0–676). Check if our scaler matches the paper's exactly.

6. **Evaluation window**: Confirm test window boundaries and that MSE is computed on the same set of data points.

### A2. Gap closure experiments

If any discrepancy is found in A1, use the HPC cluster (see `HPC_GUIDE.md`) to retrain with corrected settings. Priority order:

1. **Quick wins**: Adjust hyperparameters (epochs, lr, batch size) — can run on a single GPU in hours
2. **Architecture fixes**: If GPT-2 layer count or fusion mechanism is wrong — requires retraining
3. **Data protocol**: If split is wrong — requires rescoring at minimum

For each experiment, report:
- What was changed
- New MSE (4-step mean + per-step)
- Improvement or degradation
- Whether this moves closer to 1.4355

### A3. Realistic assessment

If the gap cannot be fully closed (e.g., due to hardware differences, random seed sensitivity, or unreported details in the paper), provide:
- An honest decomposition of the gap (X% due to seeds, Y% due to architecture, Z% unexplained)
- Whether 5% tolerance is achievable
- What the closest achievable MSE is

---

## PART B: Innovation Benchmark for Publication

This is the main contribution for journal publication. Design and execute an expanded, rigorous benchmark.

### B1. Denormalize MSE values (ILITOTAL only)

**Critical**: The 7-variable aggregate MSE CANNOT be denormalized with a single scaler. You must:
1. Extract ILITOTAL-only (feature index 4) MSE from raw predictions
2. Then convert: `MSE_physical = MSE_z_ILITOTAL * std^2 = MSE_z_ILITOTAL * 9003.15^2`
3. Report both z-space and physical-unit MSE side by side

For the 7-variable aggregate, report z-space only (no physical unit).

Provide a table showing:
| Model | MSE (z-space, 4L mean) | MSE (physical, 4L mean) | MAE (z-space) | MAE (physical) |

### B2. Per-step MSE breakdown

For every model, show **separate MSE for each lead time** (L=24, 36, 48, 60), not just the 4-step mean. This reveals:
- Which lead time each model performs best/worst
- Short-term (L=24) vs long-term (L=60) performance trends
- Whether MIFlu's advantage is uniform or concentrated at specific horizons

Output format:
| Model | L=24 MSE | L=36 MSE | L=48 MSE | L=60 MSE | 4L Mean | Best Step | Worst Step |

Also provide a **normalized per-step profile** (each model's MSE at each step divided by its own 4L mean) to show relative degradation with lead time.

### B3. PTE/PIE per-model per-step analysis

Deep dive into Peak Timing Error (PTE) and Peak Intensity Error (PIE) using the **Kramer & Shaman (2019) acceptance criteria: PTE ≤ 1 week AND PIE ≤ 25%**.

For **each model × each lead time (L=24/36/48/60)**, compute and report:
- Mean PTE (weeks)
- Mean PIE (%)
- Whether PTE ≤ 1 week: PASS/FAIL
- Whether PIE ≤ 25%: PASS/FAIL
- Combined criterion (PTE≤1 AND PIE≤25%): PASS/FAIL
- Peak hit rate (%)

Output format (one row per model × L):
| Model | L | PTE (wk) | PIE (%) | PTE≤1? | PIE≤25%? | Combined | Hit Rate% |

**Also analyze**:
- Which models satisfy the Kramer & Shaman criteria at which lead times
- Whether MIFlu's peak prediction improves or degrades with lead time
- The relationship between MSE ranking and PTE/PIE performance (they may not correlate!)
- Comparison with the paper's claims about peak prediction capability

### B4. Expanded model comparison

Replace the current 4 LLM vs 4 non-LLM setup with a **broader, more diverse model suite**. Requirements:

**Keep only ONE linear model** (choose NLinear OR DLinear, not both).

**Add classical ML models** (non-neural):
- Decision Tree / Random Forest
- Gradient Boosting (XGBoost, LightGBM, or similar)
- Support Vector Regression (SVR)
- k-Nearest Neighbors (KNN)

**Add deep learning models** (non-LLM):
- DNN (fully connected)
- CNN (1D convolutional)
- RNN / LSTM / GRU
- At least one modern transformer variant not yet tested (e.g., Autoformer, FEDformer, TimesNet, or iTransformer if not already included)

**Add SOTA open-source LLMs** (both without and with inference/reasoning):
- **Without inference (direct embedding/encoding)**: Qwen2.5, DeepSeek-V2/V3, LLaMA-3, Mistral — use as text encoders or time-series adapters
- **With inference (reasoning-augmented)**: Same models but with chain-of-thought or reasoning prompts to generate textual features
- Consider GPT-4o or Claude as API-based upper bounds (if feasible)

**For each model**, report:
- MSE (z-space + physical, per-step + 4L mean)
- MAE (z-space + physical)
- PTE/PIE per-step with Kramer & Shaman criteria
- Training/inference cost (GPU hours, parameters, FLOPs if available)
- Whether it uses text/multimodal input

### B5. Innovation analysis

Based on the expanded benchmark, write an analysis section suitable for a top-tier journal (IEEE JBHI, Nature Digital Medicine, or similar):

1. **What makes MIFlu special?** Is the GPT-2 text embedding genuinely useful, or does a well-tuned non-LLM model match it?
2. **Linear vs non-linear**: NLinear/DLinear often wins peak criteria — is the field overcomplicating things?
3. **LLM value proposition**: Under what conditions do LLMs help? (data size, text quality, task complexity)
4. **SOTA LLM frontier**: Do newer LLMs (DeepSeek, Qwen2.5) improve over GPT-2? Is the improvement from scale or from architecture?
5. **Peak prediction vs point prediction**: The tension between MSE-optimal and peak-optimal models — propose a hybrid or ensemble approach
6. **Practical deployment**: Which model would a public health agency actually use? (accuracy, interpretability, cost, latency)

---

## Output Format Requirements

1. **All tables in Markdown** with clear column headers and consistent decimal places (4 decimal places for MSE/MAE, 2 for percentages)
2. **Python code** for any new analysis, with comments explaining the methodology
3. **Figures**: Describe what plots to generate (at minimum: per-step MSE comparison bar chart, PTE/PIE scatter plot, model cost-accuracy Pareto frontier)
4. **Report structure**: Follow academic paper conventions (Abstract → Introduction → Related Work → Methods → Results → Discussion → Conclusion)
5. **Reproducibility**: Every number must be traceable to a specific file/CSV in the handoff package or a clearly documented computation

---

## Honesty & Scientific Integrity Constraints

These constraints are **non-negotiable** and must be preserved in all outputs:

1. **A/B track numbers are NOT comparable**: The paper's 1.4355 (Table V, 10-run average) and our 1.8652 (TRACK_C, 3-seed average) come from different experimental protocols. Never present them as directly comparable without qualification.

2. **Text pathway mechanism contradiction is UNRESOLVED**: The text embeddings are constant vectors (same for all time steps), yet the paper claims text pathway influence. This contradiction has NOT been resolved. Do NOT claim "reproduction success" — use "PARTIAL_REPRODUCTION" framing.

3. **Peak criteria** (PTE≤1wk & PIE≤25%): NLinear 36/36 (100%), DLinear 31/36 (86.1%), MIFlu 15/36 (41.7%). Earlier docs misattributed DLinear's 31/36 to MIFlu — corrected. Peak analysis measures k=1 (one-week-ahead predictions), NOT L=24–60 week lead forecasts. Be precise about which criteria and which lead time you cite.

4. **Unified pair key**: All strict-966 comparisons use `UNIFIED_PAIR_KEY=966|L24|seed42`. Do not mix with other configurations.

5. **Single authoritative report**: `REPORT_精简终版.docx` + its MD mirror are the only authoritative report. Do not create conflicting reports.

6. **Official data SHA256**: `2a96dfed…` — never silently modify data. If data issues are found, report them explicitly.

7. **MSE ≠ accuracy**: MSE ranking and accuracy-based metrics are not interchangeable. Always specify which metric you are using.

---

## Execution Order

1. First, extract and read the zip thoroughly. Build a mental model of the project structure.
2. Read the paper (especially Section V: Experiments, Table V, and Section VI: Analysis).
3. Read `HPC_GUIDE.md` to understand GPU access.
4. Execute Part A (gap analysis) — this informs Part B.
5. Execute Part B (innovation benchmark) — this is the publication contribution.
6. Compile everything into a structured report with tables, figures, and analysis.

**Begin now. Start by extracting the zip and reading the project structure.**
