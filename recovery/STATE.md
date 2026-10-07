# Recovery STATE — resumable status

Updated 2026-09-26 22:00 Asia/Hong_Kong (= 2026-09-26 14:00 UTC).
Track: A = author-data reproduction · B = refreshed-data benchmark · C = holdout generalization.

> **A2 is COMPLETE. Stage 6 is COMPLETE and REPORTED.** A2: 36/36 learned fits,
> 8/8 baselines, 36 checkpoints locked before any Test inference, 44/44 unified
> Test evaluations, primary metric independently recomputed (max 4.44e-16, PASS).
> Stage 6: A0 GPU minimal diagnostic executed (text pathway **conflicts with the
> Stage 2 CPU audit — unresolved**), 72 new fits, 108 checkpoints locked, 116
> unified Test evaluations, primary metric independently recomputed (max
> 8.9e-16, PASS). See `recovery/stage6/results_report_zh.md`.

## Stage 6 — A0 / A1 / eight-model comparison (COMPLETE 2026-09-26)

**GPU used: 1.10 GPU-h COMPLETED (plus 0.1 on FAILED attempts) against a 2.3 GPU-h
cap. ~1.1 GPU-h deliberately unspent.**

| Step | Status | Evidence |
| --- | --- | --- |
| Phase-0 preservation: 36 A2 checkpoints copied out of scratch and verified | **DONE** | job 586934; `archive verify: ok=36 sha_fail=0 missing=0`; `hpc_results/stage5_a2/` + `/home/sychan552/stage5_a2_durable/checkpoints/` (7.4 G) |
| A0 released-code CPU audit (deps, assets, imports, split arithmetic) | **DONE** | job 586942; three concrete import blockers found |
| A0 blocker analysis + `embed.py` recovery from the author's own `.pyc` | **DONE** | jobs 586945 / 586947; all 8 classes recovered; `recovery/a0/a0_compat.py` |
| A0 executable diagnostic (CPU) | **DONE** | job 587002: text→output Δ exactly `0.000e+00`, text grad norm `0.000e+00`; 6/12 GPT-2 blocks; LoRA never applied; `freeze` a no-op; Test covers `feat_id=[0]` only; Test used for checkpoint selection |
| **A0 GPU minimal diagnostic** | **PARTIAL — CONFLICTS WITH THE ABOVE** | jobs 587091 (mode 0) / 587068 (mode 1): Test MSE **0.9685 vs 0.8581** — on GPU the author's text pathway **does** change the output. **The contradiction with the CPU audit is NOT resolved and no cause is claimed.** Evidence: `hpc_results/stage6/a0_gpu/` |
| A1 paper-vs-repo-vs-A2 evidence table | **DONE** | `recovery/a1/a1_evidence_table_zh.md`; paper's own token-order dimension annotations are mutually inconsistent (L205 vs L219 vs L225) |
| Eight-model runner + protocol-identity proof | **DONE** | `scripts/train_backbone_966.py`; job 586942: `reuses the SAME objects: True True True`; window counts match the frozen table for all four L |
| Six-backbone architecture self-check with REAL frozen backbones | **DONE** | job 587011; qwen 370,376 / calf 1,981,608 / timecma 1,391,016 trainable — identical to the B-track |
| Eight-model run matrix + cost + reuse determination | **DONE** | `recovery/stage6/cost_and_matrix_zh.md`; 96 fits = 24 reused + 72 new |
| **72 new fits (6 backbones × 4 L × 3 seeds)** | **72/72 COMPLETED** | `results/stage6/logs/run_ledger.csv` — 74 rows, all `exit=0` |
| **Four pipeline defects found and fixed** | **DONE** | `--export` string-splicing the script path (silent submit failure), `say` polluting stdout inside `$( )` (broken `wait_done`), `pipefail` mis-handling, over-eager BAD-SUBMISSION kill. All four were reproduced offline with a fake `sbatch` before the fix |
| **108 checkpoints locked before any Test inference** | **DONE** | `hpc_results/stage6/scoring/CHECKPOINT_LOCK.{csv,json}` |
| **116 unified Test evaluations (108 learned + 8 baselines)** | **DONE** | job 587385 → `score_matrix.csv`, `score_summary.csv`, `average_mse_4L.csv` |
| **Independent recomputation from artefacts** | **PASS** | `recovery/stage6/recompute_eight.py`; max Δ `8.9e-16`; log `results/stage6/logs/recompute_verify.out` |
| Paired statistics on the 12 shared (L, seed) cells | **DONE** | `recovery/stage6/paired_stats.py` → `hpc_results/stage6/scoring/paired_stats.txt` |
| Durable archive | **DONE** | `/home/sychan552/stage5_a2_durable/stage6/` (185 files, 20 MB, `STAGE6_SHA256SUMS.txt`); local `hpc_results/stage6/` (57 files) |
| Chinese reports | **DONE** | `recovery/stage6/results_report_zh.md`, `supervisor_brief_zh.md` |

### Stage 6 headline result

`average_MSE_4L`: no-text **1.922** (control) < MIFlu **2.042** ≈ NLinear **2.050** <
DLinear 2.348 < TimeCMA-LLM 2.670 < PatchTST 3.920 ≈ iTransformer 3.985 <
Qwen-Time-LLM 5.220 < CaLF-LLM 5.515.

Paired over the 12 shared (L, seed) cells: **MIFlu − NLinear is not resolvable
(t = −0.11, 5/12)** — the strongest verifiable finding is that the text pathway
buys MIFlu nothing over a plain linear baseline. no-text beats NLinear
(t = −2.28, 11/12) but **not** MIFlu significantly (t = −1.50), so "removing text
is better" is **not** a supported claim. All three LLM backbones are significantly
worse than the linear baseline. **This is a corrected-reconstruction retrospective
comparison, not a reproduction verdict.**

### Not executed, therefore NOT claimed

A0 full replay (paper-level config, 4 L × 3 seeds) · ten reps instead of 3 seeds ·
the 2×2 text/LoRA matrix (160 fits) · canonical PatchTST · regional / few-shot
study · any new backbone or dataset. Stage C remains **incomplete and currently
impossible**: no unseen interval exists, and an old interval must not be renamed
to fake a holdout.

## Three-track identities (frozen)

- **A** author-data reproduction — author 966-row vintage (MMWR 2002w40–2021w13).
- **B** refreshed-data benchmark — project July-2026 snapshot (1,025 rows). Existing v3_clean
  results are B/C; already frozen and preserved.
- **C** extended holdout generalization — original holdout result (exposed) + any future
  untouched interval (none identified yet).

## Completed (evidence)

| Step | Status | Evidence |
| --- | --- | --- |
| Read 3 prompt docs completely | DONE | — |
| Pin author repo | DONE | `recovery/author_repo/` @ `6ed2101` |
| Author CSV identity (966 rows, identical values, synthetic dates) | PASS | `data_identity_report.md` §1-2 |
| paper_exact == author values | PASS | `data_identity_report.md` §2 |
| Project snapshot coverage (1025 rows, 19-week hole) | PASS | `data_identity_report.md` §3 |
| Overlap + revision audit (author vs July snapshot) | PASS | `data_identity_report.md` §4, `overlap_differences.csv` |
| Variable mapping + OT denominator identity | PASS | `data_identity_report.md` §5, `feature_mapping.csv` |

Machine outputs: `dataset_manifest.json`, `feature_mapping.csv`, `coverage_audit.csv`,
`overlap_differences.csv`, `data_identity_report.md`, `preprocessing_lineage.md`.

## Completed — Stage 2 (implementation audit, read-only + dev smoke checks)

| Step | Status | Evidence |
| --- | --- | --- |
| Author code path read (entry → loader → model → evaluator) | DONE | `main_ILI_lora.py`, `data_provider/*`, `models/GPT4TS_lora.py`, `utils/*`, `text_emb.ipynb` |
| Text-visibility smoke check (deterministic CPU) | PASS (bit-identical prefix) | `smoke_text_visibility.py` → max diff 0.0e+00 |
| Nine concrete risks verified | DONE | `implementation_audit.md` §Consolidated risk register |
| Window/split arithmetic | DONE | `window_manifest.json` (`audit_windows.py`) |
| Existing-result disposition | DONE | `result_disposition.csv` |
| Project implementation compared to author code | DONE | `implementation_audit.md` §8 |

Headline Stage 2 result: the **released author code** is materially buggy (text inert, feature-0
Test, Test-in-loop, freeze no-op, PEFT off, 1 epoch default), and the **project's own MIFlu** is a
corrected reconstruction (text-first, 7-channel, proper LoRA/freeze, validation selection).

**Correction (2026-09-24):** the project *has* already run track-A data with its corrected model —
966-row job 514859 (L24 MSE_All 2.238) and control966 (L24 1.379) — plus the 1025-row paper-window
run (MSE_All 2.593/3.341/3.237/3.559). What remains genuinely undone is **A0** (replay the released
author code verbatim) and a **coherent A2 matrix** (corrected MIFlu / no-text / NLinear on 966 rows
under one protocol). See `hpc_results/paper_exact/REPLICATION_VERDICT.md`.

## Completed — Stage 3 (preparation only, no GPU)

| Step | Status | Evidence |
| --- | --- | --- |
| Corrected Stage-2 claim (project DID run 966-row + 1025-row) | DONE | `implementation_audit.md` §8, `manifest.json`, `STATE.md`, `result_disposition.csv` |
| Calendar-gap consequence (corrected; 1 real gap, 20 train origins) | CHECKED | `stage3/gap_consequence_check.py` (output captured) |
| Rerun spec + matrix + configs + commands + patch + resources + brief | PREPARED | `recovery/stage3/*` |

## Completed — Stage 4 (implementation + CPU preflight; no GPU)

| Step | Status | Evidence |
| --- | --- | --- |
| Adapter applied in isolation (illustrative patch did not apply; implemented directly) | DONE | `recovery/stage4/adapter.diff`, `applied_code_diff.md` |
| `--profile` threaded through `train_miflu.py` + `train_ablation.py` | DONE | both `load_and_normalize()` return 676/773 for author_966, 717/819 for project_1025 |
| NLinear thin runner (`train_nlinear_966.py`) | DONE | `--self-check` max abs err 0.0e+00 vs reference NLinear |
| Naive runner (`train_naive_966.py`) | DONE | future-leak guard over leads 0..59; clamped=0 on dense 966 |
| CPU preflight (split/scaler/leak/shape; no Test scoring) | PASS | `recovery/stage4/preflight_report.md` |
| Reuse map vs completed runs (514859 / control966 / 8-17) | DONE | `recovery/stage4/reuse_map.csv` (44 NEW_FIT, 1 BLOCKED) |
| Reduced execution matrix + commands | DONE | `recovery/stage4/reduced_run_matrix.csv`, `commands.md` |

**Reuse finding:** job 514859 (TSLib 966, split 676/96/194, 10 reps,
fixed-20-epoch), control966 (snapshot-truncated 966), and the 8-17 1025-row run
are all *data-leg landmarks*, not matches for the proposed A2 protocol
(paper_exact 966, 676/97/193, 3 seeds × 1 rep, val-based selection). Their
`mse_all` values (2.238 / 1.379 / 2.593…) are not interchangeable with A2 and
cannot be re-evaluated locally (checkpoints excluded from the repo; only
ILI-channel predictions stored). ⇒ all 44 A2 rows are `NEW_FIT`.

## In progress / next

- **No stage is mid-flight.** A2 (Stage 5) and Stage 6 are both complete and
  reported; no GPU job is queued. `D-split`, `D-target`, `D-compute` and
  `D-holdout` were resolved by the Stage-5 protocol freeze; `D-a0-env` is partially
  resolved (the replay environment works — see the Stage-6 A0 rows) but the
  Stage 2 / A0 contradiction is still open.

## Unresolved scientific decisions (carried forward — need supervisor input, do not block read-only work)

1. Reproduction scope: national only, or regional/few-shot/baseline too?
2. Acceptability of a documented partial reproduction.
3. Corrected text-path variant naming (distinct from released MIFlu).
4. Primary target: 7 standardized outputs vs weighted ILI vs ILITOTAL.
5. Claim scope: all eight models vs validation-selected representatives.
6. Availability of a genuinely untouched future interval.
7. Retrospective accuracy vs as-of operational claim.
8. Refit policy (train-only checkpoint vs train+validation refit).
9. Tuning budget / GPU-hour cap / reproduction tolerance / equivalence margin.
10. Author inquiry authorization.
11. Canonical PatchTST in core suite?
12. Optional modern-Qwen/DeepSeek study exclusion (recommended: yes).
13. **Did the author's code actually use the text pathway?** Stage 2 (CPU) and
    Stage 6 A0 (GPU) disagree; unresolvable without a dedicated experiment.

## Blockers (superseded 2026-09-26)

- ~~**GPU/authorized training:** the minimal 36-fit matrix is a proposal, not approval.~~
  **RESOLVED** — the user authorized A2 (36 fits + 8 baselines + unified Test scoring +
  verification + report) under a cumulative 2 GPU-hour cap. Executed 2026-09-25/26; see
  the Stage-5 section below and `recovery/stage5/execution_ledger.md`.
- **No untouched holdout identified** — old Test is exposed; a fresh future interval must be
  declared before inspecting outcomes. Still open.

## Completed — Stage 5 (A2 EXECUTED 2026-09-25/26; GPU used, training done, Test scored)

| Step | Status | Evidence |
| --- | --- | --- |
| Reuse map / classification fixed (36 NEW_FIT + 8 NEW_EVAL; A0 separate BLOCKED) | DONE | `recovery/stage5/final_run_matrix.csv`, `recovery/stage5/a0_diagnostic_record.csv` |
| Protocol frozen: D-split 676/97/193, D-target average_MSE_4L, D-holdout retrospective-only | RECORDED | `recovery/stage5/frozen_protocol_stage5.md` |
| Window-containment defect found and fixed (D-windows, `--containment strict`) | DONE | `recovery/stage5/window_counts_verify.md`; counts match the Stage-5 table for all L |
| Full SHA-256 for code / data / protocol configs | DONE | `recovery/stage5/hashes_stage5.json` |
| Compute-node preflight script prepared (check #7 + resources) | PREPARED | `recovery/stage5/preflight_compute_node.py`, `preflight_sbatch.sh` |
| Launch commands for all 44 rows prepared | PREPARED | `recovery/stage5/launch_commands.md` |
| **D-compute authorized** (2 GPU-h cumulative cap, stingy / 1×A100 / ≤1 running + ≤1 pending) | **GRANTED by user** | `recovery/stage5/execution_ledger.md` |
| Compute-node preflight (job 584886) | **PASS** | A100-SXM4-80GB, py3.9.25/torch 2.5.1, local GPT-2, output (4,7,24), trainable 1,030,056 / frozen 81,106,176, LoRA present, ckpt round-trip tensor-identical, text-swap output Δ≈1.6e-3, peak VRAM ≈1.43 GB |
| 36 learned fits (MIFlu / no-text / NLinear × 4L × 3 seeds) | **36/36 COMPLETED** | jobs 585794/585798/585802/585813 (MIFlu), 585821/585823/585825/585827 + 585865/585874/585875/585876 (no-text), 585828/585830/585832/585833 (NLinear); ledger `results/stage5/logs/run_ledger.csv` |
| 8 deterministic baselines (Last Value / Seasonal Naive × 4L) | **8/8 COMPLETED** | job 585836; `results/stage5/author_966/naive/metrics.csv` |
| Resume-guard defect found and fixed (no-text seeds 43/44 were being silently skipped) | **DONE** | `scripts/train_ablation.py` resume key `(L,rep,seed)` + per-seed checkpoint existence; only the 8 missing fits were re-run, seed 42 reused unchanged |
| Checkpoint lock (SHA-256 + validation-selection evidence for all 36) | **36/36 LOCKED** | `hpc_results/stage5_a2/scoring/CHECKPOINT_LOCK.{json,csv}`, written 2026-09-25T16:13:29Z — **before any Test inference**; first copy kept as `CHECKPOINT_LOCK_first_20260925T161329Z.json` |
| Unified Test scoring (36 ckpts + 8 baselines, one metric path) | **44/44 COMPLETED** | job 585883 → `score_matrix.csv`, `score_summary.csv`, `average_mse_4L.csv` |
| Independent recomputation from artefacts (no model code imported) | **PASS** | `recovery/stage5/recompute_from_artifacts.py`; max Δ 4.44e-16; self-tested positive + negative |
| Chinese reports | **DONE with numeric results** | `recovery/stage5/results_report_zh.md`, `supervisor_brief_zh.md`, `results_tables_zh.md` |

**Status: `A2_COMPLETE` / `REPORTED`.**

Headline (`average_MSE_4L`, 7-var standardized Test MSE, lower better):
no-text **1.922158** < MIFlu **2.041519** < NLinear **2.049550** < Seasonal Naive **2.268799** ≪ Last Value **7.165831**.
MIFlu ≈ Nlinear is not resolvable at 3 seeds; the text pathway shows no confirmed
benefit and the paired sign flips across L. **This is a corrected-reconstruction
retrospective control experiment, not a reproduction of the paper (A0 still unrun).**

### Deviations recorded (full list in `results_report_zh.md` §5.1)

1. `--containment strict` replaces target-start window assignment (the old rule let
   L=60 validation targets cross into Test — a real contamination of checkpoint selection).
2. Naive-baseline Test numbers were produced before no-text seeds 43/44 were fitted
   (not the protocol's literal order), but no learned-model Test number existed at that
   time; the unified scoring job recomputed all 8 baselines after the full lock and
   reproduced them digit-for-digit, so the reported baseline values come from after the lock.
3. Scoring job 585878 failed after locking (`NLinear` has no `.device`); fixed minimally,
   rerun as 585883, metric path unchanged.
4. `best_epoch` is not recoverable for no-text / NLinear (log truncation / never recorded);
   the selection quantity `best_val` is present and locked for all 36.
5. A0 unrun *at the time of Stage 5* (a minimal GPU diagnostic has since run in
   Stage 6 — see the Stage-6 table; the full replay still has not). No new holdout
   opened. No compute on the login node.

### Blocking

- **Stage 2 vs A0 contradiction on the author's text pathway — UNRESOLVED.** The CPU
  audit (job 587002) measured exactly zero text→output difference; the GPU replay
  (jobs 587091/587068) measured 0.9685 vs 0.8581. No cause is claimed. This must be
  settled before any verdict on "did the author actually use text".
- **A0 full replay not done** — only the 1-epoch minimal diagnostic ran. A0-01 is
  `PARTIAL`, no longer `BLOCKED`.
- **No untouched holdout identified** — old Test is exposed; this round is retrospective only.

## Resource state

- **Round 1 (A2) cap 2.0 GPU-hours; used 1.1536** (4153 GPU-s, `sacct -X`, 38 jobs, 1×A100 each).
- **Round 2 (Stage 6) cap 2.3 GPU-hours; used 1.10 COMPLETED + ~0.1 on FAILED attempts;
  ~1.1 deliberately unspent.** Measured by `sacct -X` over `s6_*` + `a0_gpu` jobs only.
- Superseded-but-charged jobs (585540, 585544, 585555, 585581, 585843–585846) = 0.4400 GPU-h.
- A2 checkpoints (5.0 GB) archived to `/home/sychan552/stage5_a2_durable/checkpoints/`
  (7.4 GB with the local copy), re-verified 36/36 against the first lock; scratch originals kept.
- Stage-6 artefacts archived to `/home/sychan552/stage5_a2_durable/stage6/`
  (185 files, 20 MB, SHA-256 manifest) and locally to `hpc_results/stage6/` (57 files).
- Not counted anywhere: job 586949 `diaggen-visual` — a different job on the same account,
  not part of A0/A1/A2/Stage 6.

## Next executable action

**A2 and Stage 6 are both finished and reported. Do not re-run them and do not add
seeds / models / data without a new authorization.** No further GPU work is queued.

The only open items need a human decision, not compute:

1. Settle the Stage 2 / A0 contradiction on the author's text pathway.
2. Decide whether to authorize the A0 full replay (~1 GPU-h; the round-2 balance covers it).
3. Decide whether "8 models, 3 seeds, `average_MSE_4L`" is the final comparison scope,
   or whether canonical PatchTST / more seeds are required (much more expensive).

Full per-job accounting: `recovery/stage5/execution_ledger.md`.
