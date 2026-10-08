# PAPER-LEVEL REPRODUCTION VERDICT

Generated 2026-10-06. One verdict per result family, then one overall verdict.

# OVERALL: `PARTIAL_REPRODUCTION`

**Updated 2026-10-07** after the corrected R1-B pilot completed (jobs
608045/608061/608087/608105, 0.5094 GPU-h). The core National-Illness result has now
been **executed and measured**, and it lands **outside the predeclared tolerance at
all four horizons** — so `EXACT_OR_NEAR_REPRODUCTION` is excluded on evidence, not on
absence of a run.

Method-specification items (Tables I, II, IV, X) reproduce. The proposed scheme's own
quantitative result does **not**. The regional, few-shot and sensitivity families
remain blocked by missing data or unrecovered configuration, and the ablation and
embedder-comparison families have not been run.

**No family achieved `EXACT_OR_NEAR_REPRODUCTION` on a quantitative MIFlu result.**

---

## 1. The eleven separate questions

The brief requires these to be answered **separately**, not collapsed.

| # | Question | Answer |
|---|---|---|
| 1 | does the official code **execute**? | **YES** — four horizons ran on A100 (jobs 606365/606378/606385/606412); the R1-B subclass additionally runs and its corrections are measured |
| 2 | do the **core National-Illness values reproduce**? | **PARTIALLY — and measured (R1-C: 24 fits, 3 seeds 1000/1001/1002, all rc 0)**: reference C0 mean MSE 1.8561 (SD 0.0878) vs paper 1.4355 (**+29.30 %**, +0.4206); released-scheduler C1 mean 1.8225 (SD 0.0405) vs 1.4355 (**+26.96 %**, +0.3870); **0/4 horizons inside the predeclared ±0.10 band** for either candidate. C0 per-horizon (3-seed) 2.0460 / 1.9036 / 1.7339 / 1.7408; C1 per-horizon 2.0588 / 1.8154 / 1.7166 / 1.6991. Best candidate C1 still outside 5 %; MSE is not accuracy. |
| 3 | does the **paper-described mechanism** reproduce? | **PARTIALLY, and measured**: the released mechanism does **not** work (text inert, LoRA off, freeze a no-op, one channel); the R1-B reconstruction restores text (`inert → active`) and freezing (`100 % → 1.93 %`) |
| 4 | does the **textual pathway** reproduce? | **the released one: NO** (exactly 0 effect, CPU + A100, positive control). **The reconstructed one: YES** (`max\|Δ\| = 5.88e-02`) |
| 5 | do **LoRA and freezing** reproduce? | **freezing: YES** (measured). **LoRA: PARTIAL** — wired, works on HPC for the author's class, unverified for the R1-B subclass |
| 6 | do the **ablations** reproduce (Table VIII)? | **NOT_YET_RUN** |
| 7 | do the **sensitivity trends** reproduce (Figs 5, 6)? | **NOT_YET_RUN**, and they are **regional** (US-Region, L=20, T 10–50, K 1–7) — a dataset the released tree does not contain |
| 8 | do the **regional results** reproduce (Table VI)? | `BLOCKED_BY_MISSING_DATA` — the US-Region dataset is not released |
| 9 | do the **few-shot results** reproduce (Fig 7)? | `BLOCKED_BY_MISSING_CONFIGURATION` — training fractions and subsampling are unrecovered |
| 10 | are the **runtime results** comparable (Table IX)? | `HARDWARE_NORMALIZED_ONLY` — the paper used an RTX 3090, the HPC uses an A100 |
| 11 | is the **full paper reproducible from released artifacts**? | **NO** — see §3 |

---

## 2. Verdict per paper item

| Item | Verdict | Basis |
|---|---|---|
| **Table I** (prompt template) | `EXACT_OR_NEAR_REPRODUCTION` | the template is transcribed and present in both sources |
| **Table II** (national statistics) | **`EXACT_OR_NEAR_REPRODUCTION`** | the 966-row file reproduces it **7/7**, max deviation **0.03 %** — re-verified 2026-10-07 against the **printed values** in `reference_papers/…Scheme.md` (TABLE II, line 158) |
| **Table III** (US-Region statistics) | **`VERIFIED_AVAILABLE`** | **CORRECTED 2026-10-07**: the printed values ARE available (`reference_papers/…Scheme.md`, TABLE III, line 169 — 10 regions × Average/Max/SD + Total). The earlier `UNREADABLE` label was a **search error** (truncated grep), not a source limitation. The underlying US-Region **data** is still unreleased, so the statistics cannot be recomputed — Table VI remains `BLOCKED_BY_MISSING_DATA` |
| **Table IV** (models + hyperparameters) | **`EXACT_OR_NEAR_REPRODUCTION`** | the settings block is cross-verified and matches the released argparse for batch/T/K/Lp/S/r |
| **Table V — MIFlu column (8 cells)** | **`PARTIAL_REPRODUCTION`** | R1-C complete (24 fits, 3 seeds 1000/1001/1002, all rc 0); reference C0 mean 1.8561 (**+29.30 %**), released-scheduler C1 mean 1.8225 (**+26.96 %**); **0/4 horizons inside ±0.10**; 3 repetitions, verdict capped at `PARTIAL_REPRODUCTION`; 5 % not reached; MSE is not accuracy |
| **Table V — 11 baseline columns (88 cells)** | **`NOT_APPLICABLE`** | the paper states these are taken from refs [9] and [14] — quoting a copied number is not reproducing it |
| **Table VI** (regional RMSE/PCC) | `BLOCKED_BY_MISSING_DATA` | US-Region dataset absent |
| **Table VII** (embedder comparison) | `NOT_YET_RUN` | needs GPT-2 / LLaMA2-7B / BERT embedder variants; the X row equals Table V's GPT4TS column (a consistency check the paper itself provides) |
| **Table VIII** (ablation) | `NOT_YET_RUN` | needs one working switch per component |
| **Table IX** (training time) | `HARDWARE_NORMALIZED_ONLY` | ReILIF 130 min, MIFlu 119 min on an RTX 3090 |
| **Table X** (appendix prompt) | `EXACT_OR_NEAR_REPRODUCTION` | present verbatim in both the PDF text layer and the Markdown |
| **Fig. 1, 2** | `FIGURE_DIGITIZED_APPROXIMATION` | schematic / boxen plots |
| **Fig. 3** (four-horizon summary) | `DERIVED_FROM_OTHER_PAPER_VALUES` | it is the arithmetic 4-horizon mean of Table V |
| **Fig. 4** | `NOT_YET_RUN` | |
| **Fig. 5** (T sensitivity) | `BLOCKED_BY_MISSING_DATA` | regional |
| **Fig. 6** (K sensitivity) | `BLOCKED_BY_MISSING_DATA` | regional |
| **Fig. 7** (few-shot) | `BLOCKED_BY_MISSING_CONFIGURATION` | |
| the released code executing | `EXECUTABLE_BUT_NOT_REPRODUCED` | it runs, but with one channel, Test-based selection, an inert text path and LoRA disabled |

### Counts

| Verdict | Count |
|---|---:|
| `EXACT_OR_NEAR_REPRODUCTION` | **4** (Tables I, II, IV, X) |
| `NOT_APPLICABLE` | **2** (Table III, Table V's baseline columns) |
| `NOT_YET_RUN` | 6 |
| `BLOCKED_BY_MISSING_DATA` | 3 |
| `BLOCKED_BY_MISSING_CONFIGURATION` | 1 |
| `FIGURE_DIGITIZED_APPROXIMATION` | 2 |
| `DERIVED_FROM_OTHER_PAPER_VALUES` | 1 |
| `HARDWARE_NORMALIZED_ONLY` | 1 |
| `EXECUTABLE_BUT_NOT_REPRODUCED` | 1 |

> **The four `EXACT_OR_NEAR` items are all non-forecasting items** — a prompt template, a
> statistics table, a settings table and a prompt example. **Not one forecasting result has
> been reproduced.** That is the honest headline.

---

## 3. Why the full paper is not reproducible from the released artifacts

| Blocking fact | Evidence |
|---|---|
| the released code **cannot** produce a seven-variable score | `data_loader.py` slices one channel and its Test path covers channel 0 only |
| the released text path is **provably inert** | measured exactly 0 on CPU and A100, with a positive control |
| the paper's **pooling axis is never stated** | Q12 `UNRECOVERED` — so even a matching number could not be proven to be the same quantity |
| **epochs/lr ARE stated (Table IV)** but the **optimizer and scheduler are not** | `UNRECOVERED` |
| the **regional dataset is not released** | Table VI and Figs 5–6 are unreachable |
| the **few-shot configuration is not released** | Fig. 7 unreachable |
| the **Table V column provenance is unstated** | the paper names only the baseline provenance |

**Verdict: `NOT_REPRODUCIBLE_FROM_RELEASED_ARTIFACTS` for the paper as a whole**, while
**four specific non-forecasting items are exactly reproduced**.

---

## 4. What may and may not be claimed

**May be claimed**

- "The released code executes; it does not implement the paper's multivariate multimodal
  mechanism."
- "The paper's National-Illness dataset is the 966-row file — verified against its own
  Table II, 7/7."
- "The paper's national training configuration is given in Table IV: 20 epochs, batch 16,
  lr 0.0005, T 104."
- "The paper's Table V has exactly one author-generated column; the other eleven are quoted
  from refs [9] and [14]."

**Must not be claimed**

- ❌ "we reproduced the paper" / "we reproduced Table V" / "we matched 1.4355"
- ❌ "the paper discloses no training configuration" — **Table IV does**
- ❌ "the released code is the paper's implementation"
- ❌ any verdict resting on Table V alone

---

## 5. What would change this verdict

| Action | Would move |
|---|---|
| the R1-B pilot runs and lands inside the predeclared tolerance | the Table V MIFlu column → `PARTIAL_REPRODUCTION` (a single repetition cannot exceed this) |
| the 10-repetition expansion runs and holds | possibly → `CORE_RESULTS_REPRODUCED_WITH_RECONSTRUCTED_SETTINGS` |
| an author inquiry answers the pooling axis and the checkpoint rule | removes the largest permanent limitation |
| the US-Region dataset is obtained | unblocks Table VI and Figs 5–6 |

**Nothing moves on its own.** Each requires an authorization or an artifact that does not
currently exist.