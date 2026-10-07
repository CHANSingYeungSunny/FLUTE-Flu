# A2-F CORE FAIR-BENCHMARK PILOT, ONE SEED — EXECUTION REPORT

Generated 2026-10-06. Authorization: **0.60 GPU-h, new and independent** (the previous
round's 0.05639 remainder was **not** carried over).

# STATUS: `COMPLETE` — all 8 success gates pass, 0.25 / 0.60 GPU-h used

---

## 1. Slurm jobs

| # | Job ID | Phase | Partition | State | Elapsed | AllocTRES | GPU-h |
|---:|---|---|---|---|---|---|---:|
| 1 | **607564** | Phase 1 (CPU) | stingy | COMPLETED | 00:01:05 | cpu=4, mem=16G | **0** |
| 2 | **607594** | scorer check (CPU) | stingy | COMPLETED | 00:00:01 | cpu=2, mem=8G | **0** |
| 3 | **607595** `_0` | miflu L=24 | stingy | COMPLETED | 00:03:36 | gres/gpu:a100=1 | 0.0600 |
| 4 | **607602** `_1` | miflu L=36 | stingy | COMPLETED | 00:02:29 | gres/gpu:a100=1 | 0.0414 |
| 5 | **607605** `_2` | miflu L=48 | stingy | COMPLETED | 00:02:25 | gres/gpu:a100=1 | 0.0403 |
| 6 | **607608** `_3` | miflu L=60 | stingy | COMPLETED | 00:02:21 | gres/gpu:a100=1 | 0.0392 |
| 7 | **607613** `_4` | notext L=24 | stingy | COMPLETED | 00:01:06 | gres/gpu:a100=1 | 0.0183 |
| 8 | **607617** `_5` | notext L=36 | stingy | COMPLETED | 00:01:02 | gres/gpu:a100=1 | 0.0172 |
| 9 | **607623** `_6` | notext L=48 | stingy | COMPLETED | 00:01:02 | gres/gpu:a100=1 | 0.0172 |
| 10 | **607624** `_7` | notext L=60 | stingy | COMPLETED | 00:00:59 | gres/gpu:a100=1 | 0.0164 |
| 11 | **607631** | Phase 3 (first attempt) | stingy | COMPLETED | 00:04:59 | cpu=4, mem=16G | **0** |
| 12 | **607671** | Phase 3 (re-run after fixes) | stingy | COMPLETED | 00:05:05 | cpu=4, mem=16G | **0** |
| 13 | **607691** | Phase 3c (text probes) | stingy | COMPLETED | 00:00:41 | cpu=4, mem=16G | **0** |

**Every job COMPLETED. No failures, no cancellations, no retries of GPU work.**

**Queue**: one job at a time throughout (`MaxSubmit=1` / `MaxJobsPU=1` honoured — each
array element submitted as `--array=i-i`).

---

## 2. GPU budget

| | GPU-h |
|---|---:|
| authorization | **0.60000** |
| **consumed (8 GPU fits, from `sacct`)** | **0.25000** |
| **remaining** | **0.35000** |
| within cap? | ✅ **YES** |
| CPU-only jobs (5) | 0.00000 — no `gres/gpu` in any of their `AllocTRES` |

Consumption was **42 % of the projection** (0.25 vs 0.426 base) because the fits ran
faster than the 192 s estimate: MIFlu averaged 2:53 and no-text only ~1:02 (the no-text
arm skips the 317-token text prefix, so its attention span is ~7.5× shorter).

---

## 3. Results — per model, per horizon (MSE / MAE, z-space)

| model | L=24 | L=36 | L=48 | L=60 | **avg4L (MSE)** |
|---|---|---|---|---|---|
| **notext** *(LLM unimodal)* | 1.8085 / 0.8805 | 1.6354 / 0.8571 | 1.7545 / 0.9238 | 2.3498 / 1.0277 | **1.8870** |
| **nlinear** *(dedicated)* | 2.0857 / 0.9479 | 2.0423 / 0.9515 | 2.0278 / 0.9577 | 1.9846 / 0.9565 | **2.0351** |
| **miflu** *(LLM multimodal)* | 2.4695 / 1.0471 | 1.8422 / 0.9156 | 1.7091 / 0.8796 | 2.1728 / 0.9767 | **2.0484** |
| seasonal_naive *(reference)* | 2.5638 / 1.0042 | 2.2655 / 0.9568 | 2.1425 / 0.9413 | 1.9174 / 0.9392 | 2.2223 |
| **dlinear** *(dedicated)* | 2.3434 / 1.0853 | 2.2291 / 1.0543 | 2.3471 / 1.0969 | 2.4890 / 1.1308 | 2.3521 |
| last_value_naive *(reference)* | 6.2133 / 1.6222 | 7.7138 / 1.9059 | 7.8513 / 1.9521 | 6.8849 / 1.7884 | 7.1658 |

**Per-horizon winners**: L=24 → notext · L=36 → notext · L=48 → **miflu** ·
L=60 → seasonal_naive. **The winner changes with the horizon.**

---

## 4. The required categorical answers

| Question | Answer |
|---|---|
| **best LLM-based multimodal** | **miflu** — avg4L **2.0484** (it is the only multimodal entry) |
| **best LLM-based unimodal** | **notext** — avg4L **1.8870** (matched no-text MIFlu, GPT-2 backbone retained) |
| **best dedicated/non-LLM** | **nlinear** — avg4L **2.0351** |
| **best naive reference** | **seasonal_naive** — avg4L 2.2223 |
| **overall lowest in this pilot** | **notext 1.8870** |

**Corrected MIFlu vs matched no-text**: `miflu − notext` = **+0.1614**, t = **+0.87**,
notext wins **2/4** cells — **indistinguishable at one seed**. The direction is the same
as in the earlier A2-basis result (no-text lower), but with only four paired cells and
one seed this is **not** evidence that removing text helps.

---

## 5. Required wording

> **Under the one-seed A2-F pilot contract, `notext` achieved the lowest four-horizon
> average MSE (1.8870), followed by `nlinear` (2.0351) and `miflu` (2.0484).**

**Prohibited**: "notext is proven to be the best model", "LLMs are worse than non-LLMs",
"the text pathway hurts MIFlu", any significance claim, any seed-robustness claim.

Why: one seed, four paired cells, and `miflu` wins the L=48 horizon outright. A single
draw cannot separate models whose mean difference is 0.16 with t = 0.87.

---

## 6. Gate results — F1 marked COMPLETE on all eight gates

| Gate | Result |
|---|---|
| G1 all six models present | ✅ PASS |
| G2 all four horizons present | ✅ PASS |
| G3 no rejected artefacts | ✅ PASS |
| **G3b no duplicate keys** | ✅ PASS *(added during execution — see §8 D2)* |
| G4 forecast keys consistent | ✅ PASS — **0 violations** |
| G5 single pilot seed | ✅ PASS — seed 42 only |
| G6 no missing cells | ✅ PASS — 24/24 |
| G7 pairwise partition invariant | ✅ PASS — every row satisfies `wins_A+wins_B+ties==n` |

**Artefacts**: 24 accepted, 0 rejected, 0 missing. Storage: 2.5 GB.

---

## 7. Forecast-key validation

- **24 artefacts for 24 expected (model, horizon) cells**, one seed.
- **0 forecast-key violations**: `var_cols` are identical across all six models — the
  seven CDC channel names from `configs.VAR_COLS`.
- **Origin counts match the recorded strict-containment contract exactly**:
  L=24 → 170, L=36 → 158, L=48 → 146, L=60 → 134
  (`score_test_stage5.py::EXPECTED` asserts this, and the naive runner independently
  produced the same counts).
- No duplicate `(model, L, seed)` keys.

---

## 8. Text-path verification (Phase 3c)

Run on **each of the four F1 corrected-MIFlu checkpoints** with the deterministic
equal-length intervention probe, using **StandardScaler-space input** (the corrected
form — v1's raw-input form inflated magnitudes by 5–10 orders).

| L | ckpt sha256 (head) | ckpt load | diff prompt `max\|Δ\|` | row-permuted `max\|Δ\|` | `\|grad_text\|` | verdict |
|---|---|---|---|---|---|---|
| 24 | `242dfa175db1edcc` | missing 0 / unexpected 0 | 4.053e-04 | 9.970e-02 | 0.05706 | **text_active** |
| 36 | `0972589622386984` | missing 0 / unexpected 0 | 1.793e-04 | 6.653e-02 | 0.02371 | **text_active** |
| 48 | `8ed02c036cfd0dd5` | missing 0 / unexpected 0 | 7.352e-04 | 1.269e-01 | 0.03832 | **text_active** |
| 60 | `ea84b6a713f4f65d` | missing 0 / unexpected 0 | 9.061e-04 | 3.879e-02 | 0.00885 | **text_active** |

**4/4 `text_active`.** The corrected MIFlu's text pathway demonstrably reaches the
forecast. (`missing 0 / unexpected 0` also confirms the F1 checkpoints load cleanly —
unlike the older A2 checkpoint, which lacked 12 mask buffers.)

Therefore the `miflu` vs `notext` contrast in §4 **is a genuine text-content contrast**,
not a difference caused by sequence length or an inactive pathway.

---

## 9. Failures, defects and corrections

**No GPU job failed and none was retried.** Five defects were found and fixed — three of
them *because the gate and the first Phase-3 run exposed them*, which is the gate working
as intended.

| # | Defect | Found by | Fix |
|---|---|---|---|
| **D1** | **premature `exit` before the text-path block** — Phase 3b never ran (`grep` returned 0 lines) | inspecting the first Phase-3 log | moved the `exit` to the end of the script |
| **D2** | **duplicate prediction keys**: `score_test_stage5.py` dumps its **own leaky** naive baselines, colliding with the leakage-safe ones. The aggregator **mixed** them, producing a meaningless `seasonal_naive = 2.245545` | counting artefacts (32 vs 24 expected) | learner dump moved to `preds_learned/`; a curated 24-artefact `preds_final/` assembled; **`G3b_no_duplicate_keys` gate added** and unit-tested. Corrected `seasonal_naive = 2.222290` |
| **D3** | **text probe chose the wrong dataset** — the author's `a0_replay` copy has numeric headers (`date,1,2,…,OT`), giving `KeyError: '% WEIGHTED ILI'` | Phase 3c failure | probe now validates each candidate for the CDC column names before use |
| **D4** | **scorer path resolution broke on HPC** (`dirname×3` → `$HOME`, so it looked for `/gpfs1/home/scripts/…`) | Phase-1 scorer check failed | multi-candidate resolution + `F1_CODE_ROOT` env var |
| **D5** | **the launcher's budget tracker reported 0** — `sacct -o AllocTRES` is truncated, so the GPU-count grep returned empty | reading the ledger (`cumulative_used=0h`) | diagnosed; budget now computed with `AllocTRES%80`. Because the true usage (0.25) was well under the cap, the guard never needed to fire — but it would not have fired correctly |

Also noted: the storage projection of 3.9 MB/checkpoint was wrong — actual checkpoints are
**329 MB** each (2.5 GB total), because `train_miflu.py` stores the full `state_dict`
rather than the filtered set. Still far inside the 23 GB headroom.

---

## 10. Reproducibility and preservation

| Item | Value |
|---|---|
| **output directory** | `/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/` (local copy: `hpc_results/official_repo_reproduction_20261006/f1_execution_20261006/`) |
| dataset | author 966-row file, SHA-256 `2a96dfed…ebfe5`, verified at every GPU job start (exit 4 on mismatch) |
| code root | `/scratch/sychan552/a2_stage5` (READ-ONLY) |
| contract | A2-F corrected fair-comparison contract — 7 channels, StandardScaler, strict containment, validation-only selection, Test once, predictions saved, independent scoring |
| scratch output | **none** — every path under `$HOME` |

### Confirmations

| Confirmation | Evidence |
|---|---|
| **no Historical Track B artifact modified** | no F1 script references any `innovation_deploy_root_v3_*` path; the 19 directories remain **19**, untouched; all 66 pre-existing deliverables remain byte-identical |
| **total F1 GPU use within 0.60** | **0.25000 GPU-h**, independently recomputed from `sacct` per job |
| no login-node computation | all compute ran on compute nodes; the login node only ran `sbatch`/`squeue`/`sacct` |
| no quota carried over | the previous round's 0.05639 was not added to the 0.60 |

---

## 11. What this pilot does and does not support

| Supported | Not supported |
|---|---|
| F1 is executable and the contract held end to end | that `notext` is the best model |
| forecast keys are identical across all six models | any significance claim (one seed, 4 paired cells) |
| the independent scorer is correct and complete | seed robustness |
| the corrected MIFlu text pathway is active (4/4) | final LLM-vs-non-LLM superiority |
| a **preliminary** one-seed ordering | that the ranking would survive F2 |
| model-level cost at pilot scale | — |

**Any "best model" statement requires at least F2 (3 seeds)** — see
`../f1_preflight_20261006/F1_POST_PILOT_EXPANSION_PLAN.md` §2, which sets the minimum
seed count for each claim. F2 would cost ~0.85 GPU-h incremental at the **measured**
0.0533 h/fit; at the observed faster rate (0.25 for 8 fits) it would be less.