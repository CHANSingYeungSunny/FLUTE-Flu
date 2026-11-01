# docs/WORK_BREAKDOWN.md — definition of done, every requested item, next actions

> **What this is:** the planning/status file, moved verbatim out of `AGENTS.md` — §11 definition of done, §13 the A–F work-breakdown tables, then §7 next actions and §8 open questions. A reconciliation note records where §11 and §13 disagreed *at the time of the move*, without overwriting either text.
> **When to read it:** when choosing the next action, when reporting status ("is X done?"), and before marking anything ✅ — `R4` says ✅ requires an artefact on disk plus a command that reproduces it.
> **What it points to:** `docs/STATE.md` (the numbers being tracked), `docs/LEDGER.md` (the history of each item), `docs/MIFLU_MERGE_BLOCKED_20261101.md` (the one blocked row), `docs/HPC_RUNBOOK.md` (how to execute the GPU items), `LOOP_ENGINEERING.md` §6 (the iteration queue that mirrors §13).
> **Depends on:** `AGENTS.md` (`R4`, §2 rules 9–13 constrain how an item can be closed), `docs/STATE.md`, `docs/LEDGER.md`.
> **Chain:** `AGENTS.md` → **this file** → `docs/LEDGER.md` → the evidence file named for that item.

---

## 11. DEFINITION OF DONE (progress targets)

**Reproduction** — ✅ **DONE**: 4-horizon mean within 5% (achieved +4.5%); L24–60 all
have 10-rep means; deviations disclosed in §3.
**Still required to *claim* it in the paper**: the K&S cells for MIFlu (its predictions
are only ILITOTAL CSVs) so it appears as a row in the peak table.

**Benchmark** — 🟡 **70%**:
- ✅ 13 non-LLM + 3 LLM arms, 4 horizons × 3 seeds, MSE + MAE + PTE/PIE + 64 figures
- ✅ relative-improvement + efficiency columns (enables one cross-scale table) — efficiency in `BENCH_EFFICIENCY.csv`, relative-to-seasonal-naive in `BENCH_EFFICIENCY.csv::rel_improve_vs_seasonal_pct`
- ✅ paired significance tests (Holm-corrected) — `paper_tables/BENCH_PAIRED_TESTS.csv`, exact sign-flip over 12 (L, seed) cells, 10k percentile bootstrap CI, n=12 floor p≈0.00049
- ✅ CRPS / WIS / log score (parametric from validation residuals) — `paper_tables/BENCH_CRPS_WIS.csv`, σ floor 0.05 sd documented, log score diagnostic only
- ⬜ MIFlu merged into the champion tables — **blocked 2026-11-01**: HPC down (3/3 ssh timeouts) and all three local MIFlu exports contradict §1.1 (2.4439 / 1.9686 / ILITOTAL-only vs 1.3045 at L24). Converter + NaN-tolerant analysis are ready (`scripts/import_miflu_predictions.py`, `scripts/verify_bench_unchanged.py`); see `docs/MIFLU_MERGE_BLOCKED_20261101.md`
- ⬜ rolling-origin (5 folds) and regional (Table VI)
- 🟡 the new LLM arms actually trained — **the code-level blocker is GONE (2026-11-01)**: `scripts/llm_encoder_backbone.py` + `--backbone llm_encoder` is the frozen-encoder + shared-head adapter (unit-tested on CPU, dry-run proven), so the roster can now produce cells. **Still ⬜:** per-model checkpoints/revisions, the per-model venv, the A100-asserting wrapper + 12-cell loop (L=24/36/48/60 × seeds 42/43/44), and the frozen feature table — enumerated per model in `docs/LLM_ARMS.md` §7.1. No LLM arm has a benchmark row yet

**Innovation** — ⬜ not started (must build on a frozen reproduction + benchmark).

**Publication gate** — ✅ reproduction claim, ✅ two-champion finding,
✅ documented author-code defects; ⬜ probabilistic skill, ⬜ rolling origin,
⬜ paired tests. The last three are what separate "workshop" from "top-tier".

---

## 13. WORK BREAKDOWN — status of every requested item (as of 2026-11-01 17:00)

Legend: ✅ done & on disk · 🟡 partial / needs a fix · ❌ not started

### A. Cross-scale methodology (①+③ as mechanism, ② as column)
| item | status | evidence / gap |
|---|---|---|
| ③ shared head + frozen base | ✅ | already the architecture (`Linear(·,L)` shared by every arm) |
| ① Pareto frontier **table** | ✅ | `BENCH_EFFICIENCY.csv` — Pareto set = {PatchTST, NLinear} |
| ① Pareto frontier **figure** | ✅ | `results/bench_figures/pareto_frontier.png` — `scripts/plot_pareto.py`, dpi 200, 11 parametrised models, Pareto set {NLinear, PatchTST} as a step line; slope/R² re-derived and **asserted** equal to `BENCH_EFFICIENCY.csv`. **Re-derived 2026-11-01 on the shared evaluation windows**: slope **+0.1171**, R² **0.0223**, PatchTST 211× params for **11.2%** lower MSE, and the figure prints the window counts 160/144/144/128 |
| ② relative to **seasonal-naive** | ✅ | `paper_tables/BENCH_SEASONAL_NAIVE.csv` (`scripts/seasonal_naive_baseline.py`, 52-week lag, same A2 protocol) + column `rel_improve_vs_seasonal_pct` in `BENCH_EFFICIENCY.csv`. Naive MSE z-7var = **5.5768 / 6.9446 / 6.5842 / 5.7471** at L=24/36/48/60 (re-derived on 160/144/144/128 windows); **all 16 arms beat it on the 4-horizon mean** — PatchTST +73.17%, NLinear +69.62%, DNN +65.06%, CNN only +8.46% (CALF −0.85% at L60 and CNN −10.83% at L60, so the per-horizon claim is weaker than the mean). The 5–6.5 magnitude itself (rather than the ~2.2–3.0 once assumed) is explained in `docs/LEDGER.md` 2026-11-01: the test block is far out of the training range |
| two rankings (absolute / efficiency) | ✅ | tables produced |
| the exact paper sentence | ❌ | not yet written into `docs/` |

### B. Reproducibility protocol
| item | status |
|---|---|
| pin `revision=<sha>` | ❌ |
| per-model manifest JSON (repo, revision, sha256, tokenizer, lib versions) | ❌ |
| freeze feature table (~2.4 MB) + hash | ❌ |

### C. Three upgrades
| # | item | status |
|---|---|---|
| 1 | relative improvement + efficiency | ✅ efficiency (Pareto + slope) and relative-to-naive (`BENCH_EFFICIENCY.csv::rel_improve_vs_seasonal_pct`, `scripts/seasonal_naive_baseline.py`) |
| 2 | paired significance (12 cells, sign-flip + Holm) | ✅ `BENCH_PAIRED_TESTS.csv` (bootstrap CI, n=12 floor p≈0.00049) |
| 3 | CRPS / WIS / log score | ✅ `BENCH_CRPS_WIS.csv` (σ floor 0.05 documented; log score diagnostic only) |
| 4 | national 5-fold rolling origin | ❌ needs retraining |
| 5 | regional HHS-10 (Table VI) | ❌ needs retraining |

### D. Tables VI / VIII / IX
| table | status |
|---|---|
| IX training time | ❌ **CORRECTED 2026-11-01**: an earlier entry here claimed "easy, from existing logs" — that was **wrong**. Table IX reports **regional** model training time and therefore requires the **Table VI** run configuration (T=20, L∈{2,3,5,10,13,15,20}, K=4, 50 ep, batch 32) to be actually executed and timed first. A *national* timing table (Table IV/V config) can be produced now, but it is a different table and must not be labelled Table IX |
| VIII ablation | 🟡 `notext` exists from the old Track-C protocol, **not** re-run under the reproduction protocol; w/o-LoRA, w/o-multimodality, K-sweep, embedder-swap all ❌ |
| VI regional | ❌ separate config (T=20, L∈{2,3,5,10,13,15,20}, K=4, 50 ep, batch 32) |

### E. Operational
| item | status |
|---|---|
| move Qwen3.8 load test off congested `gpu_a100` | ✅ **DONE 2026-11-01 (job 718976, `stingy`)**: loads and runs. The original failure (job 718448) is fully resolved — separate env `mlflu_llm` (Python 3.11.13, transformers 5.22.1, torch 2.6.0+cu124) recognises `qwen3_5` (job 718928) and the GPU test returned `ALL_OK`: 27.3567 B params, 54.73 GB VRAM after load, forward 2.385 s cold / 0.136 s warm, peak 55.10 GB of 85.1 GB. **Caveat that changes the plan**: on an A100 the fp8 is dequantised to **bf16** by transformers (sm_80 < sm_89), so the model needs ~55 GB (only the 80 GB cards work) and true fp8 compute needs an H100. `mlflu_hpc` untouched (4.57.6, job 718946) | jobs 718976 / 718928 / 718946 |
| Qwen3.8-27B usable as a benchmark arm? | 🟡 **technically yes, but expensive and dtype-qualified.** It fits one A100-80GB in bf16 with ~30 GB headroom, but it is a 64-layer **multimodal** `Qwen3_5ForConditionalGeneration` (vision tower loaded even for text-only use) and needs `causal_conv1d` + `flash-linear-attention` for usable speed. Any LLM-arm row for it must state **bf16, A100-80GB**, and must not be mixed with fp8 timings | job 718976 |
| `mlflu_hpc` protection (16 benchmark arms depend on it) | ✅ **verified unchanged after the env work**: transformers **4.57.6**, torch 2.5.1, and `lib/python3.9/site-packages/transformers/__init__.py` mtime still **2026-08-06 18:34:41**. The new env is a completely separate tree (`/home/sychan552/.venvs/mlflu_llm`); no `pip install`/`conda` command ever targeted `mlflu_hpc` | job 718946 |
| clean scratch (353 GB → keep < 100 MB) | ❌ not executed |
| **merge MIFlu into the champion tables** | 🟡 **in progress (2026-11-01 21:10), 18/40 cells verified** - source decided: the **reproduction protocol** (10 reps, seeds 2021-2030), 7-variable. 719030 was **preempted** (not a wall-guard stop) and had two silent-corruption defects (`find_ckpt` trust order; a cell list that omitted 36:2024 / 48:2021 / 60:2025 and included 60:2021), both fixed. The new controller (`code/miflu_controller_v2.py` + `miflu_a100_controller_v3.sh`) enumerates all 40 cells, accepts one only when its npz reproduces the per-seed oracle <=1e-5 on the `(W//16)*16` windows, and re-verifies every pre-existing cell. **18/40 verified** (all L24; L36 2021-2026; L48 2021; L60 2025); the 4 export-only cells give 1.240157 / 1.154099 / 1.482299 / 1.410785 with |d| <= 3.7e-07. **Bottleneck measured:** stingy preempted every generation (36:55, 04:33, 01:01, 01:30, 17:39) and `train_miflu` has no per-epoch checkpoint, so a 27-min 3-worker retrain could never finish; switched to **1 worker** (8 min/cell). `gpu_a100` probed as the same A100-SXM4-80GB but will not backfill a long job. **At 21:10 the HPC login node went down again (gotcha 11: TCP/22 up, banner never arrives)**, so the remaining 22 cells are running unattended in Slurm and cannot be fetched or merged until access returns. Not merged; `verify_miflu_oracle` is still SKIPPED for the table half. **UPDATE 2026-11-01 21:50 (HPC back after the 21:10 outage): still exactly 18/40, re-measured.** The pending 719538 (`gpu_a100`, 2 h) was cancelled and driver 719534 stopped, because it would have resubmitted to `gpu_a100` — which cannot start anything tonight: a 2 h job, a **45 min** job and a **20 min** job were all given `StartTime` 02:50–03:35 with 20/20 GPUs allocated, so short walls do **not** backfill. Controller **719715** now sits on **`stingy`** with `MIFLU_WORKERS=1`, `--exclude=gpu-a100-05`, 4 h wall, budget **12 600 s** (sized to fit all 22 cells in one window), `MIFLU_MAXGEN=1`, and watcher **719716** (`tiny`, `MIFLU_PART=stingy`, capped at 3 submits / 10 h) resubmits after a CANCEL-preemption. **The wall-time/backfill hypothesis was tested and FALSIFIED**: on `gpu_a100` a 2 h job, a 45 min probe (719655), a 25 min controller (719695) and a 12 min controller (719712) **all** got `StartTime 02:50:39` — shrinking the wall 10× changed nothing, because **all 20 gpu_a100 GPUs are allocated** and gpu-a100-09 is `DOWN+DRAIN+NOT_RESPONDING`. The "not saturated" reading came from CityU's `squeue`, which is **user-scoped**; `scontrol show node … AllocTRES` is the authoritative view. **Its `StartTime` is 2026-11-02T03:28:28** because every healthy stingy A100 is allocated (719208 on 03/06, 719397+705753 on 04, 719593+719356 on 05); the idle 4th GPU on gpu-a100-05 is the CUDA-dead node. **Therefore no cell can land before ~03:28 and the 22 remaining cells cannot finish tonight**, although the queued entry costs nothing and 22 × ~8.5 min ≈ 3.1 h of compute would be done by ~06:35 if it starts and is not preempted. The 8 min/cell figure for 1 worker is still a **prediction** (24 s/epoch × 20 epochs) — no 1-worker cell has ever completed | `code/miflu_controller_v2.py`, `code/miflu_a100_controller_v3.sh`, `code/miflu_chain_driver4.sh`, `miflu_a100_chain.log`, `docs/LEDGER.md` |
| **hardware provenance of the existing cells** | ✅ **CONFOUND CLOSED (2026-11-01)**: `paper_tables/BENCH_GPU_PROVENANCE.csv` = **204 cells, 204 A100-SXM4-80GB, 0 non-A100** — 192 from job 715984 (`gpu-a100-05`) + the 12 NLinear cells re-run in job **719191** (`gpu-a100-04`, `stingy`, COMPLETED 00:00:53). The V100 set is preserved in `hpc_results/expanded_runs_v100_nlinear/` and the delta is `paper_tables/BENCH_NLINEAR_A100_DELTA.csv`: MSE 4-horizon mean 1.8715832975 -> 1.8715832984, PTE 1.677 wk, PIE 9.4766 %, **pass/16 4 -> 4 (unchanged)**, and the "only NLinear satisfies K&S" claim re-verified over all 16 arms (1 of 16 arms has a passing cell). `verify_bench_unchanged.py` PASSES after the baseline re-freeze; the V100-era contract is kept as `BENCH_*.post_evalwindow16_v100nlinear.csv` | `paper_tables/BENCH_GPU_PROVENANCE.csv`, `paper_tables/BENCH_NLINEAR_A100_DELTA.csv`, `scripts/compare_nlinear_a100.py` |
| DeepSeek-32B download | 🟡 started on login node, completion unverified |

### F. Reproduction
| item | status |
|---|---|
| Table V, 4 horizons, 10 reps | ✅ 1.4995 vs 1.4355 (+4.5%) |
| K&S cells for MIFlu | 🟡 **predictions exist and are computable** (`hpc_results/stage5_a2/scoring/predictions/pred_miflu_L*_s{42,43,44}.npz` and the `strict966` 7-var CSVs both carry ILITOTAL on the benchmark windows), but they are **not merged**, so no MIFlu row exists in the peak table yet — same blocker as §13.E |

### G. Evaluation-window uniformity (user ruling 2026-11-01, non-negotiable)
| item | status | evidence / gap |
|---|---|---|
| one shared definition of the evaluation set | ✅ | `scripts/eval_windows.py` — `eval_slice(W, batch=16) = (W//16)*16`, docstring cites `train_miflu.train_L`'s `drop_last=True`; imported by `analysis_expanded.py`, `analysis_postprocess.py`, `plot_bench.py`, `seasonal_naive_baseline.py`, `plot_pareto.py`, `verify_*.py`. The literal 160 appears only in docstrings/explanatory text, never in executable code — every slice is computed by `eval_slice` |
| per-horizon counts | ✅ | available 170/158/146/134 → evaluated **160/144/144/128** (discarded 10/14/2/6) |
| every table + figure on that set | ✅ | MSE/step/PTE-PIE, CRPS/WIS, paired tests, efficiency, seasonal-naive, Pareto and the 64 four-panel figures are all cropped on the window axis (axis 0 of `(W,7,L)`, asserted by `check_cell_layout`) |
| `n_eval_windows` on every row | ✅ | `BENCH_MSE_BY_MODEL_L` (160/144/144/128, uniform across all 16 arms), `BENCH_MSE_BY_STEP`, `BENCH_PTE_PIE_BY_STEP`, `BENCH_CRPS_WIS`, `BENCH_SEASONAL_NAIVE`; `BENCH_EFFICIENCY` carries `n_eval_windows_L24…L60`. Asserted three times: in the analysis, in `verify_bench_unchanged.py`, and in `verify_miflu_oracle.py` |
| rollback + bit-identity references | ✅ | `paper_tables/BENCH_*.pre_evalwindow16.csv` (old 170-window values) and `…post_evalwindow16.csv` (new reference for future re-runs) |
| re-derivation executed | ✅ | `analysis_expanded.py` → `analysis_postprocess.py` → `seasonal_naive_baseline.py` → `plot_bench.py` → `plot_pareto.py`, all exit 0; 64 figures + Pareto regenerated; `verify_bench_unchanged.py` PASS |
| new rankings recomputed (old claims retired) | ✅ | **MSE champion PatchTST 1.6621** (was 1.9613); full 16-arm order **unchanged**; **K&S champion NLinear 4/16 unchanged**, PTE 1.68 / PIE 9.5 (was 1.62 / 10.1); PatchTST PTE≤1wk 6 (was 7), mean PTE 1.24 (was 1.09); per-model full-170/first-N ratio 0.9887–1.1800 (mean 1.0204) |
| MIFlu row lands on the reproduction values | 🟡 | arithmetic half verified now (`scripts/verify_miflu_oracle.py`: oracle means 1.304538/1.356079/1.654271/1.682862 == §1.1 to 5e-5, on 160/144/144/128 windows). The npz re-derivation is **skipped** — no MIFlu cell is on disk yet (job 719030); the check auto-runs after `import_miflu_predictions.py` |

**Next three actions (strict order):** (1) MIFlu merge → champion tables + figures;
(2) ✅ seasonal-naive baseline + relative-improvement column (done 2026-11-01);
(3) Pareto figure.
Then: reproducibility protocol, Table IX, rolling origin, Table VI, LLM arms.

---

### H. Overnight queue v2 (2026-11-01 23:30) — F1–F5, per-model env, measured cost, single writer

The v1 queue could train and stop. It is replaced by a queue whose *tasks* include
the analysis that turns cells into tables. Everything below is measured on the
cluster, not designed on paper.

| # | Item | Status | Evidence |
|---|---|---|---|
| H1 | **F1–F5 are real queue kinds**, executed by the same runner under the same timeout/attempt rules | ✅ | `f1_import_miflu` `f2_miflu_oracle` `f3_analysis_chain` `f4_verify` `f5_llm_import` rows in `master_queue.tsv`; `queue/finalise/*.log` |
| H2 | **Re-armed repeatedly**: after every `QUEUE_FINALISE_EVERY=4` completed cells, on drain, and once at the end | ✅ | `queue_events.log` "re-armed F1-F5 finalisation", `FINALISATION PASS` |
| H3 | **F3 provably rewrites a table** (not "the line exists") | ✅ | `analysis/paper_tables/BENCH_MSE_BY_MODEL_L.csv` mtime **22:49:37 → 23:06:24 → 23:09:59 → 23:11:17**; `analysis/results/bench_figures/` 0 → **69** |
| H4 | **Partial data tolerated**: every table the data supports is emitted with `n_cells`/`n_arms`, a missing arm never aborts | ✅ | gate strings `n_cells=222;n_arms=17`; `branch=d.partial-mode` |
| H5 | **`env` column is explicit and authoritative** (`hpc` \| `llm`), backfilled on every row; missing interpreter ⇒ `SKIPPED env-missing`, no retry | ✅ | 212 rows: `hpc` 188 / `llm` 24 / empty 0; `--selftest` `env=bogus` → `skip.env-missing` |
| H6 | **Only `qwen3_5` uses `mlflu_llm`** (tr 5.22.1); all other arms `mlflu_hpc` (tr 4.57.6); arch failure escalates once (`w.arch-fallback`) | ✅ | `arms_registry.json` `venv`; `master_task.py` `ENVS`/`ENV_ALT` |
| H7 | **Measured LLM cost → projection → logged degradation** (keep P0, keep P1, then smallest-first; `DEFERRED_COST` carries the arithmetic; re-admitted if a later measurement fits) | ✅ | `cost_model.py`; `queue/queue_state.tsv` `_cost_*` rows; `queue/cost_projection.txt` |
| H8 | **Atomic per-task claim** (`O_EXCL` lock with PID + job id; stale-owner stealing) | ✅ | two concurrent `--claim-test` → `CLAIMED` rc 0 / `ALREADY-CLAIMED` rc 5 |
| H9 | **Queue store survives concurrent writers** | ✅ | 2 processes × 10 updates on different rows → 8/8 rows present, exactly 2 `DONE` |
| H10 | **Single writer of results**: only the `writer.sh` lane (`QUEUE_WRITE_ONLY=1`) may run F1–F5; GPU lanes are cell producers only | ✅ | stripe-1 lane given an F3 row: state stayed `TODO`, 0 starts, 0 finalisation passes |
| H11 | **Exhaustive branch log**: every task records `BRANCH=<name>` in `queue_state.tsv` and `queue_events.log` | ✅ | branches seen: `ok.done` `ok.already-done` `ok.finalise` `ok.no-new-cells` `skip.env-missing` `sched.claim-busy` `sched.stale-running` `sched.preempted` `train.oracle-mismatch` `train.oracle-mismatch-retry` `skip.attempts-exhausted` `d.refreeze` `d.partial-mode` `d.miflu-row-partial` `hw.not-a100` `hw.oom-halved` `hw.cuda-busy` `retry.generic` |
| H12 | **Termination branches**: `HALT` → finalise once, exit 0; drained → finalise, exit 0; only BLOCKED/SKIPPED/DEFERRED left → finalise + summary; nothing runnable → `IDLE_NO_WORK`, exit 0; no successor → `CHAIN_DEAD` | ✅ | `master_controller.sh` main loop; `queue/CHAIN_DEAD` written only on a real failure |
| H13 | **MIFlu cells audited against the per-seed oracle before import** | ✅ | 36 npz re-derived on `(W//16)*16`, **all PASS, max abs Δ 6.6e-7, 0 deleted** (`queue/miflu_audit.json`) |
| H14 | **MIFlu table row is still a PARTIAL mean** at 3 of 4 horizons (18/40 cells) and must not be quoted | ⬜ **open** | F2 `branch=d.miflu-row-partial`: L36 1.354068 vs 1.356079, L48 1.482299 vs 1.654271, L60 1.410785 vs 1.682862. L24 is exact (1.304538) |
| H15 | **Two queued compute jobs hold the early slots but carry spooled v1 code** which cannot parse the 11-column queue (their STATE field reads `hpc`) | ⚠️ **risk** | `719833` (stingy 02:36:32), `719835` (gpu_a100 02:50:39); live-file demonstration in `_slot_swap.sh` section A |

**Operator entry points (v2):** `make_queue.py [--migrate|--force|--backfill-env]` ·
`master_controller.sh --dry-run|--selftest|--writer-once` · `writer.sh` (the only
F1–F5 executor) · `cost_model.py --apply` · `audit_miflu_cells.py --apply` ·
`submit_night.sh` · `watchdog.sh`. State files: `queue/master_queue.tsv` (11 cols),
`queue/queue_state.tsv` (state, attempts, wall, gate, **branch**, updated),
`queue/queue_events.log` (append-only), `queue/finalise_status.json` (per-cycle:
markers, cells, table mtime, last error, cycle).

---


### I. PART-TWO RUNNERS (2026-11-01 23:50 - code delivered; cells NOT run)

This section exists because the part-two experiments were blocked on **absent
code**, not on GPU. It records what exists now, what each artefact proves, and
what is still missing. Full row specification: **`docs/QUEUE_ROWS_PART2.md`**.

| item | status | evidence / gap |
|---|---|---|
| **rolling origin — splitter** | ✅ | `scripts/walk_forward.py`: `Fold(index,train_end,val_end,test_end)`, `make_folds(n_rows,k=5)`, `resolve_fold/resolve_split`, `restrict_data`, `add_fold_argument`; `assert_folds` enforces disjoint + strictly-ordered + expanding + 20 % test block + feasible windows + last fold reaches the last row. Geometry on 966 rows: f1 394→241/75/78, f2 493→320/75/98, f3 617→419/75/123, f4 772→540/78/154, **f5 966→676/97/193 = the published split**; test windows L24 55/75/100/131/170. A **pure** 70/10/20 K=5 is impossible at L≥36 (39-row validation block = 4 windows at L=36, −20 at L=60; `drop_last=True` needs 16) → `val_floor_rows=75` widens folds 1–3 backwards only, test blocks untouched; `make_folds(966,k=5,val_floor_rows=0)` raises with that arithmetic |
| rolling origin — `--fold` hook | ✅ | `--fold` on `scripts/train_miflu.py`, `scripts/train_backbone_966.py`, `hpc_experiments/train_classical_966.py`; default `0` = the existing split. Fold cells go to `hpc_results/walk_forward/f<F>/…` and are **refused** under `expanded_runs` (rule 10); npz gains `fold`/`fold_test_end`; a manifest is written for every fold cell. Proof the default is unchanged: the NLinear L24 s42 cell is **bit-identical** before vs after the change (same arrays, same 10 npz keys) |
| rolling origin — **cells** | ❌ | 200 MIFlu cells (40 runs × 5 folds) and 960 arm cells (§2a/§2b of QUEUE_ROWS_PART2) need an A100. Cost ≈ 120–270 A100-h for MIFlu alone at 10 reps, ≈ 35–90 h for the arms at 3 seeds. Recommended first tranche: MIFlu 1 seed (20 cells, ≈12–27 h) + the 11 neural arms 1 seed (220 cells, ≈4–12 h), both **exploratory** — rule 9 forbids an incomplete seed grid in a comparison table |
| **Table VI — regional harness** | ✅ code / ❌ cells | `scripts/train_regional.py` reuses `REGIONAL_CONFIG` (T=20, L∈{2,3,5,10,13,15,20}, K=4, 50 ep, batch 32, 10 HHS channels), `train_nlinear_966.build_windows`, `train_backbone_966.build_model`, `miflu_model.MIFlu` and `eval_windows.eval_slice`; per cell it writes `(W,V,L)` npz + CSV twin + per-region results in z **and** patients + checkpoint + manifest (GPU/partition/node/job id/wall/ckpt sha256/data sha256/split) under `hpc_results/regional/<region>/<model>_L<L>_s<S>/`. 21 MIFlu cells ≈ 1 A100-h (2–3 min/cell, ESTIMATE); 336 cells for all 16 arms ≈ 6–15 h |
| Table VI — regional data | ✅ | already on disk and now **checked, not re-downloaded**: `python scripts/download_us_region.py --check` → `10/10 regions usable -> ALREADY PRESENT` (1119 rows, 1084 weeks in 199740–202018). The downloader no-ops unless `--force` |
| **Table VIII — ablation flags** | ✅ flags / ❌ cells | `train_miflu.py` gained `--no-lora`, `--no-text`, `--num-layers K`, `--text-embedder {author_file,prompt,none}`, `--ablation-label`; the variant is recorded in a per-run manifest (`ablation_variant`, `use_lora`, `use_text`, `num_layers`, `text_embedder`, `is_default_config`). Defaults unchanged (`resolve_variant` with no flags == `CONFIG`). 12 cells per variant ≈ 1–1.6 h; K-sweep (4 values) 48 cells ≈ 3–6 h |
| Table VIII — **`no_text` caveat** | ⚠ | measured: with `author_faithful=True` the text tokens sit **after** the time patches behind a **causal** mask, and the head reads the first `num_patches` positions, so `use_text=False` is **bit-identical** to the full arm (and the default arm is independent of the text tensor). The `no_text` row is a structural verification only; a text branch that can move a number needs `gated_inject`, which the runner does not expose. Asserted by `tests/test_miflu_ablations.py` |
| **Table IX — training time** | ✅ aggregator / ❌ gate | `scripts/build_table_ix.py` reads the regional cell manifests (`wall_seconds` + rule-12 hardware block) and writes `paper_tables/TABLE_IX_REGIONAL_TRAINING_TIME{.csv,_MEANS.csv}`; it **exits 3** while nothing is measured, and excludes `probe_only` / un-timed cells with a reason. The row may only become `TODO` when the Table VI rows are `DONE` |
| **LLM weights** | 🟡 running | jobs **720175** (6 small arms) and **720176** (4 large + DeepSeek-32B) on `tiny`; pinned revisions, sizes, config sha256 and a CPU hidden-state probe per arm in `weights_manifest_A/_B.json` (merge with `weights_worker.py merge`). First verdict: `tencent/Penguin-Encoder` = **UNSUPPORTED, `requires_trust_remote_code`** |
| LLM readiness probe | 🟡 running | job **720218** (`tiny`): (1) `measure_llm_forward.py` on `Qwen/Qwen2.5-1.5B` → the first **measured** s/prompt and per-cell cost (replaces the 900 s guess in `cost_model.py`); (2) one `--probe-only` cell each for `Qwen/Qwen2.5-1.5B` and `DeepSeek-R1-Distill-Qwen-1.5B` (8 train / 4 val windows) under `$R/llmprobe/_probe/`, proving the adapter on real checkpoints |
| LLM lane specs | ✅ generator | `hpc_experiments/make_llm_lanes.py` emits one 12-cell `llm_lane_<slug>.sh` per **OK** arm (env routing, pinned revision, `--encoder-batch-size`, memory `params_b×2.5 GB` with `mem ≤ cpus×1024`, A100 assert, `SKIP <model>: <reason>` otherwise). Verified on a synthetic manifest (3 lanes, 11 skips, `bash -n` clean) |
| 168 LLM cells | ❌ | need `stingy`/`gpu_a100` and a SUPPORTED verdict per arm; env routing `qwen3_5 → mlflu_llm`, everything else → `mlflu_hpc` |

**What is still missing (nothing here can be papered over).** No rolling-origin,
Table VI, Table VIII or Table IX **cell** exists on disk; every `❌`/`🟡` above is
a compute/entitlement gap, not a code gap, except: the `no_text` ablation cannot
move a number under the current fusion (documented), and an arm that the CPU
probe marks `UNSUPPORTED` cannot become a row at all.

---

## Reconciliation note (§11 ↔ §13) — recorded at the move, 2026-11-01

Both blocks above are kept **verbatim**, so the two places where they disagree are still visible. Per `R3` nothing is overwritten; this note only states which text the evidence supports.

1. **MIFlu row.** §11 says "⬜ MIFlu merged into the champion tables — **blocked 2026-11-01**: HPC down (3/3 ssh timeouts) and all three local MIFlu exports contradict §1.1". §13.E says the same item is 🟡 **in progress (2026-11-01 19:00)**, HPC recovered, source decided, A100-only controller **job 719030** running. The §11 sentence was true when written; the later §13.E state supersedes it. The blocking analysis itself is in `docs/MIFLU_MERGE_BLOCKED_20261101.md`, and the HPC recovery is a dated row in `docs/LEDGER.md`.
2. **Publication gate.** §11's closing "Publication gate" paragraph still lists "⬜ probabilistic skill … ⬜ paired tests", while §11's own Benchmark bullets and §13.C mark **CRPS / WIS / log score** and **paired significance tests** ✅ with named artefacts (`paper_tables/BENCH_CRPS_WIS.csv`, `paper_tables/BENCH_PAIRED_TESTS.csv`). The ✅ form is the one backed by files on disk; the gate sentence was written before the 2026-11-01 reconciliation row in `docs/LEDGER.md` ("§11 reconciled with §13.C").

---

## 7. NEXT ACTIONS (in order)

1. **Post-processing (no GPU needed) — do first:**
   - `BENCH_RELATIVE_AND_EFFICIENCY.csv`: % improvement vs seasonal-naive +
     performance ÷ parameters (enables the single cross-scale table)
   - `BENCH_PAIRED_TESTS.csv`: paired sign-flip / Wilcoxon over 12 (L, seed) cells,
     Holm correction, effect sizes + CI. State n=12 and ~48 peak events → low power.
   - `BENCH_CRPS_WIS.csv`: Gaussian predictive distribution from **validation**
     residuals → closed-form CRPS, 23-quantile WIS, log score. Label as parametric.
   - ✅ relative-to-seasonal-naive done 2026-11-01 (`scripts/seasonal_naive_baseline.py`).
     **Run it AFTER `analysis_postprocess.py`** — the latter REGENERATES
     `BENCH_EFFICIENCY.csv` from scratch and would drop the added column.
2. **Merge MIFlu into the champion tables** — 🟡 **machinery done, row withheld 2026-11-01**
   (`docs/MIFLU_MERGE_BLOCKED_20261101.md`). The converter
   `scripts/import_miflu_predictions.py` handles the ILITOTAL-only CSV (writes
   `partial=True`, 6 channels NaN, so the 7-var metric can never be forged), the
   7-var 13-column CSV, and an npz passthrough, and refuses to write unless the
   windows + ground truth match an existing cell. **Next action: retry the HPC**
   (`author_runs/L*_s2021/predictions_miflu_L*_paper_protocol.csv`) and first
   reconcile §1.1 (1.4995) with the stage-5 A2 arm (2.0415) — same data, same split,
   so the gap is a training-config difference and decides which MIFlu is "row 0".
3. **Clean scratch aggressively** (keep `expanded_runs/**/pred_*.npz` 33 MB,
   `author_runs/L*_s2021/*.csv` 2 MB, `paper_tables/`, `results/bench_figures/`;
   delete old `hpc_results/` trees, `ckpt_*`, and HF weights after feature extraction).
4. **Then**: national 5-fold rolling origin (needs retraining).
5. **Then**: Table VI (regional, *different config*: T=20, L∈{2,3,5,10,13,15,20},
   K=4, 50 epochs, batch 32), Table VIII (ablations; `notext` already exists),
   Table IX (training time — available from logs now).

---

## 8. Open questions / decisions still pending

- Whether to run the LLM arms as **frozen-encoder only** or also
  **with-inference** (autoregressive decode) — the latter is a different cost class
  and must be labelled separately.
- Whether `WeMM-Embedding-*` (a genuine embedding model) should replace the
  "instruct-tuned LLM as encoder" framing for the LLM block.
- Regional Table VI scope: 7 horizons × 10 HHS regions × several models is
  effectively a second paper's worth of experiments.
