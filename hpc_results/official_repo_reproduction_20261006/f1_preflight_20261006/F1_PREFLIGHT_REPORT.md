# F1 PREFLIGHT REPORT

Generated 2026-10-06, directory `hpc_results/official_repo_reproduction_20261006/f1_preflight_20261006/`.
**Append-only**: nothing in `postrun_audit_20261006/` or any earlier artifact was
modified, and no file was deleted.

# VERDICT: `READY_TO_SUBMIT`

…**conditional on additional GPU quota being explicitly approved.** The remaining
**0.05639 GPU-h is insufficient and has been left untouched.**

---

## 1. What F1 is

> **A2-F Core Fair-Benchmark Pilot, One Seed**

A **pilot**, not the final A2-F comparison. It may support claims about execution
feasibility, forecast-key consistency, data-contract consistency, text-path
functionality, correctness of independent scoring, a **preliminary** one-seed ordering,
and model-level cost. It may **not** support claims about a statistically reliable best
model, stable superiority, significance, seed robustness, or final LLM-vs-non-LLM
superiority.

---

## 2. Model set (six, exactly as specified)

| # | Model | Category | Device | GPU fits |
|---|---|---|---|---:|
| 1 | corrected text-active MIFlu | 1 · LLM-based **multimodal** | a100 | 4 |
| 2 | matched no-text MIFlu (GPT-2 forecaster retained) | 2 · LLM-based **unimodal** | a100 | 4 |
| 3 | NLinear | 3 · dedicated / non-LLM | CPU | 0 |
| 4 | DLinear | 3 · dedicated / non-LLM | CPU | 0 |
| 5 | Last Value | 4 · naive reference | CPU | 0 |
| 6 | leakage-safe Seasonal Naive | 4 · naive reference | CPU | 0 |

**No Qwen, CALF, TimeCMA, DeepSeek, PatchTST or iTransformer in F1.**

`no-text MIFlu` is labelled **LLM-based unimodal** and must never be counted as non-LLM:
it retains an 82.7 M-parameter pretrained GPT-2 forecaster.

---

## 3. Target contract (chosen explicitly, §5 of the brief)

> All **seven** channels jointly, StandardScaler space, metrics pooled over
> (origins × leads × 7 variables), equal-weight four-horizon average, identical forecast
> keys for every model.

**Justification**: it is the only option under which the six models are asked the same
question. The released code's one-channel contract would discard six declared variables
and make the comparison depend on an implementation defect; `ILITOTAL`-only would be
single-target.

**It must not be described as recovered Table V behaviour**, because **Q12 (the paper's
pooling axis) is `UNRECOVERED`** and the paper does not state which variable(s) the Table V
scalar covers. F1 is a **corrected fair comparison**, not an imitation of Table V.

Full statement: `F1_TARGET_CONTRACT.md`.

---

## 4. Shared evaluation contract

All 20 clauses verified — see `F1_SHARED_EVALUATION_CONTRACT.md` for the enforcement
mechanism of each. Highlights:

| Clause | Status |
|---|---|
| author 966-row dataset, SHA-256 pinned | ✅ job exits 4 on mismatch |
| split 676/97/193, scaler train-only | ✅ asserted in the trainer |
| `--containment strict`, `A2_REQUIRE_STRICT=1` | ✅ non-strict exits |
| validation-only checkpoint selection | ✅ |
| Test evaluated once (`DEFER_TEST=1`) | ✅ |
| shuffle disabled, `drop_last=False` | ✅ |
| predictions **and** targets saved | ✅ NPZ per (model, L, seed) |
| independent scoring | ✅ separate entry point, never called by training |
| no Test-assisted selection | ✅ enforced + rejection test A13 |
| no Historical Track B reuse | ✅ enforced + rejection test A10 |

---

## 5. Numbers

| Item | Value |
|---|---:|
| **GPU fits** | **8** |
| **CPU-only runs** | **16** fits + 4 deterministic evaluations + 1 scoring job |
| base GPU estimate | **0.42664 GPU-h** |
| + 10 % retry buffer | **0.46930 GPU-h** |
| + 20 % retry buffer | **0.51197 GPU-h** |
| **recommended additional quota** | **0.60 GPU-h** |
| expected wall clock @ `MaxSubmit=1` | **≈ 34 min** (budget 45 min) |
| required home storage | **≈ 38 MB** (policy: refuse below 1 GB headroom) |
| available safe home storage | **≈ 23.1 GB** headroom (50 GB quota − 26.86 GB used) |

### The earlier 0.35 GPU-h figure was too low

It averaged MIFlu's true 162 s cost with much cheaper backbone fits (blended
0.0146 h/fit), carried **no** failed-job allowance, and did not separate the
deterministic references (which need **zero** GPU). The model-specific estimate
supersedes it. Rationale in full: `F1_GPU_BUDGET_REQUEST.md` §3.

---

## 6. Defects found and fixed during this preflight

| # | Defect | Severity | Fix |
|---|---|---|---|
| **D1** | Seasonal Naive **leaked at L = 60**: `ref = ts + s − 52` reads rows `ts+0…ts+7`, which are actual target rows. **8 leaking leads.** The in-file guard checked nothing. | **serious** — it would have scored a leaky reference in the pilot | `naive_leakage_safe.py`, using `ref = ts − 52 + (s mod 52)`; 6/6 self-tests pass |
| **D2** | The scorer **crashed** on a shape mismatch instead of rejecting it | **moderate** — the pilot's whole purpose is contract validation | `scorer_f1.py` (validation-first), arithmetic still delegated to the original |
| D3 | my own declared variable-key list used wrong aliases | minor | corrected to `scripts/configs.py::VAR_COLS`; the gate caught it |
| D4 | `--allow-partial` printed "ALL GATES PASS" while completeness gates failed | minor but misleading | explicit `status` field added |
| D5 | my first F1 model-name list did not match the runner's `model=` value | minor | aligned |

**D1's fix is independently corroborated**: the corrected naive reproduces the published
values **bit-identically** at L = 24/36/48 (no leakage possible) and differs **only** at
L = 60 (2.103470 → **1.917433**), while Last Value is unchanged at every horizon. The
project's published `seasonal_naive` four-horizon average therefore becomes **2.222290**
(vs 2.268799). Recorded, not silently changed.

---

## 7. Evidence produced

| Type | Result |
|---|---|
| Seasonal-naive leakage self-test | **6/6 PASS** |
| Scorer acceptance tests (synthetic arrays only) | **20/20 PASS** |
| Dry run over 8 real artefacts | 8 accepted, **0 rejected**, **0 key violations** |
| Forecast-key identity vs the trained arms | 170 origins (L=24) and 134 (L=60) — **matches the recorded strict-containment counts** |
| Static audit of 23 script properties | **23/23 verified** |
| `bash -n` / `ast.parse` on all F1 scripts | OK |

---

## 8. Remaining blockers

| # | Blocker | Blocks |
|---|---|---|
| **B1** | **GPU quota** — 0.05639 remains; F1 needs ~0.43–0.60 | the entire pilot |
| B2 | the F1 sbatch **does not yet call the trainer for the DLinear tag** via the exact recorded flag set — it follows `train_backbone_966.py --backbone dlinear`, which is the same entry point used in stage6, so this is a wiring confirmation rather than a design gap | DLinear arm only |
| B3 | text-path re-verification on the selected checkpoint can only run **after** a fit exists | the COMPLETE claim (not the gates) |
| B4 | scratch is over quota (413/300 GB, grace expired) | nothing in F1 — all output is on `$HOME` |

**No blocker prevents submission once quota is approved.** B2 and B3 are post-approval
steps already placed in the submission order.

---

## 9. Submission order

```
0  CPU dry run (--allow-partial)              prove the gates work before GPU time
1-4  GPU: corrected MIFlu L=24/36/48/60       primary arm first
5-8  GPU: no-text MIFlu   L=24/36/48/60       the matched control
9  CPU: NLinear, DLinear, naive x8, then independent scoring of all 24 artefacts
10 (post-run) text-path probe on the selected corrected-MIFlu checkpoint
11 (post-run) final ranking + pilot report
```

**One array element per submission** — `MaxSubmit=1` rejects anything larger. Launcher:
`scripts/run_f1_sequential.sh` (submits nothing by itself).

**Why the GPU arms come first**: with one job at a time the wall clock is identical either
way, so front-loading the two MIFlu arms means an interrupted wave still leaves the
*primary comparison* intact. Rationale: `F1_SUBMISSION_ORDER.md` §2.

---

## 10. Files in this preflight directory

16 required deliverables, all Slurm scripts, all configurations and all test logs — see
`F1_FILE_MANIFEST.csv`.

---

## 11. Confirmations

| Confirmation | Evidence |
|---|---|
| **No GPU job was submitted** | `squeue -u $USER` empty; no `sbatch` was invoked this round |
| **The 0.05639 GPU-h is untouched** | no GPU job exists to charge |
| **No file was deleted or modified** | 66/66 pre-existing deliverables byte-identical (re-verified); five historical result trees unchanged; 19 `innovation_deploy_root_v3_*` directories unchanged; git state identical (49 M / 9 D / 179 ??) |
| **No login-node computation** | all work in this round was local; both sbatch scripts carry a `hpclogin*` guard and were never submitted |
| **Scratch not used for output** | every F1 path points at `$HOME` |

**Do not submit F1 until additional GPU quota is explicitly available.**