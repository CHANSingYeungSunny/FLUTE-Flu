# Scientific audit — FINAL v8 status (synced 2026-11-07 HKT / 2026-11-06 UTC)

v8 copy of `final/SCIENTIFIC_AUDIT.md`, updated to reflect the **FINAL v8 status of
all 8 tasks** after T1–T8. It does not overwrite the frozen historical CSVs or the
v7/final source audits (`AGENTS.md` RULE 4). All claims below are tied to on-disk
evidence re-checked 2026-11-06, then **re-synced on 2026-11-07 (HKT) with the FINAL
T2 and T6 results** (verified against `v8/foundation/T2_VERDICT.md` §FINAL UPDATE,
`T2_PILOT_AND_MATRIX.md`, `T2_DOWNLOAD_RESULT.md`, `FOUNDATION_ROSTER.csv`,
`v8/T6_VERDICT.md` §UPDATE 2026-11-06, `T6_GPU_UPDATE.md`, and
`v8/RESOURCE_MEASUREMENTS.csv`). A structural validator `PASS` is
`scientific_readiness: NOT_ASSESSED`. **The manuscript is NOT submission-ready.**

**Sync note — old/new separation (which old claim is superseded).** The earlier
`T2 status: BLOCKED / no weights / no env / no pilot / no cells` and the earlier
`T6 peak_vram_mib: NOT_MEASURED for all 6 rows` statements in prior versions of
this audit are **SUPERSEDED, not silently erased**: T2 is now
`COMPLETED_WITH_DOCUMENTED_SCOPE` (8 zero-shot cells executed, jobs 744589/744607)
and T6 is now `PARTIAL (IMPROVED)` (MIFlu peak VRAM 4816 MiB measured in job
744532; the other 5 rows remain `NOT_MEASURED`). The `NOT_EXECUTED_BY_PROTOCOL`
80-cell item is **STILL blocked** and is kept explicitly below.

Old-snapshot / new-panel separation is mandatory: the frozen `02_数字表格/` 28-arm
snapshot, the new 1120-cell national panel, the legacy 5-fold N=3 walk-forward panel,
the legacy `final_llm_import` analysis tree, the frozen CDC ILINet vintage
reconstruction in `02_数字表格/` (a Delphi proxy; TASK 4 now COMPLETED — corrected
2026-11-06, see `v8/cdc_vintage/T4_CORRECTION.md`) and the foundation roster are
**separate populations**. See `v8/docs/V8_SCIENTIFIC_ADDENDUM.md` §0.

---

## Supported (verified)

| Claim | Evidence |
|---|---|
| National 1120-cell common panel is complete | `final/CELL_METRICS.csv` 2240 rows (1120 cells × 2 panels); 40/40 MIFlu seven-channel NPZ targets exactly equal NLinear targets |
| New leading MSE order (all-valid) | MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782; crop 1.4994 / 1.6352 / 1.9027 |
| Crop reproduces the old MIFlu mean | MIFlu crop 1.4994 vs historical 1.4995 |
| MIFlu / PatchTST lead step-level peak passes | MIFlu 252/1680 (15.0%), PatchTST 215/1680 (12.8%), NLinear 57/1680 (3.4%) |
| Event detection separates from timing/height | iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8%, PIE 30.4% |
| No monotonic depth trend | K4 1.4989 best, K12 1.7604 worst, K6 reference n=10 partial |
| Regional Table VI is COMPLETE | 53/53 valid `mse_z` rows after rerunning L13/s2030 and L15/s2026; 10-variable regional, NOT the 7-channel national metric |
| **Walk-forward is COMPLETE on the LEGACY panel** | `final/WF_RECOMPUTED.csv` = **1020/1020 `ok`**, sha256 `53d0e0cb…`; means sha256 `c0e72f35…`; 5 folds × 204 cells; 17 models n=60 each; MIFlu 2.220289. This LEGACY 5-fold N=3 panel is a DIFFERENT scoring population from the 1120 national panel |
| WF recovery changed nothing pre-existing | `v8/evidence/WF_RECOMPUTE_REPORT.json`: recovered_218_count=218, changed_existing_ok_values=0, lost_existing_ok=0, still_missing=0 |
| `final_llm_import` produced a real table | `BENCH_MSE_BY_MODEL_L.csv` sha256 `2e03b510…` from 386 readable legacy cells; 2 corrupt NPZs quarantined (not deleted) |
| **CDC ILINet vintage is COMPLETE (TASK 4 `COMPLETED`, corrected 2026-11-06)** | Frozen `02_数字表格/cdc_vintage_raw.csv` (7192 rows, sha256 `e0c5512b…`), `02_数字表格/cdc_vintage.csv` (848 rows, sha256 `5a49e6be…`), `02_数字表格/cdc_vintage_report.md` (sha256 `e2da6b37…`), `02_数字表格/cdc_peak_revintage.csv` (sha256 `7c9b5df8…`; 18 seasons scored, 7 peak weeks moved = 38.9%), builder `05_程序代码/cdc_vintage_build.py` (sha256 `8c1e4b1e…`). The earlier `PARTIAL / BLOCKED` verdict is SUPERSEDED by `v8/cdc_vintage/T4_CORRECTION.md`. Delphi `release_date` remains a proxy, NOT a CDC-issued official revision number |
| JBHI guidance verified (dated) | `v8/JBHI_VERIFICATION_20261106.md`: 14/16 pp incl. supplementary, ≤250-word abstract, double-column single-spaced, embedded figures/tables, AI disclosure, APC US$2,800 (2026) |
| Resource subset measured + ONE real GPU MIFlu forward (T6 FINAL: `PARTIAL (IMPROVED)`) | `v8/RESOURCE_MEASUREMENTS.csv`: MIFlu 581 s, NLinear 6 s, PatchTST 7 s, Qwen-1.5B 24 s wall; NPZ scoring-path latency 0.0287–0.0297 ms (NOT a forward). Job **744532** (`t6_res_gpu_v8b`, `stingy`/`gpu-a100-05`/`A100-SXM4-80GB`, driver 580.167.08) ran a REAL MIFlu forward from an existing checkpoint: peak VRAM **4816 MiB** (63 `nvidia-smi` samples, min 16), whole-process forward wall **62.94 s** (`real_model_forward_wall_s=62.94`), `[PASS] all requested cells exported`, `test MSE_7var_z=1.624383`. The other 5 model rows remain `NOT_MEASURED` for VRAM; Chronos/TimesFM resource rows remain BLOCKED; all rows `scope=subset_only_not_full_1120`, ONE cell (L=36, seed=2023), no full-1120 Pareto claim. Python 3.9.25 / numpy 2.0.1 / pandas 2.3.3 / torch 2.5.1 |
| Foundation zero-shot executed (T2 FINAL: `COMPLETED_WITH_DOCUMENTED_SCOPE`) | `v8/foundation/T2_VERDICT.md` §FINAL UPDATE + `T2_PILOT_AND_MATRIX.md` + `T2_DOWNLOAD_RESULT.md` + `FOUNDATION_ROSTER.csv`: 4 pinned weight tars (**5,024,901,120 B**) downloaded locally on Windows and scp'd to `/gpfs1/scratch/sychan552/models/`, all 4 remote SHA-256 verified INSIDE sbatch **744607**; isolated env `/home/sychan552/.venvs/mlflu_fm` (Python 3.11.13, torch 2.6.0+cu124, chronos-forecasting 2.3.2, timesfm 1.3.0) built by jobs **744574/744576**; pilot **744589** PASSED (all finite, MSE 0.3913, latency 10.191±0.446 ms warm-up 1/repeat 5, peak VRAM 596 MiB / 28 samples); matrix **744607** 8/8 cells `ok`, all finite, 8 real NPZ, peak VRAM 2608 MiB / 18 samples, wall 18.00 s. 8 cells = 2 models × 4 L (24/36/48/60), seed 2021, T=104: `foundation_chronos` MSE 0.391328494 / 2.207397404 / 1.713535818 / 1.400230721; `foundation_timesfm` MSE 0.729752533 / 2.654955324 / 2.031110049 / 1.662973370. Labels are a SEPARATE ROSTER, never merged into the 28-arm family or the 1120 national panel; both checkpoints UNIVARIATE, zero-shot, no fine-tuning |

## Contradicted / not reproduced (superseded claims stated explicitly)

1. **Historical "NLinear is the K&S peak champion" (4/16).** On the new harmonised
   1120 panel NLinear has 57/1680 step passes (3.4%) vs MIFlu 252 and PatchTST 215.
   The historical 16-unit table is a different scoring population — **superseded, not
   silently replaced**.
2. **Historical "monotonic depth trend".** The 60-cell ladder is non-monotonic
   (K4 best, K12 worst) — **superseded**.
3. **"Walk-forward partial / invalid / 802 of 1020 / 473 of 1020 / 218 missing".**
   Downgraded to the verified v8 state: **1020/1020 `ok`**. This is the LEGACY 5-fold
   N=3 panel (seeds 42/43/44), NOT the 1120 national panel — **superseded**.
4. **"Table VI: 2 of 53 regional cells missing" / "51/53".** Downgraded to
   **53/53 valid** (v7 onward) — **superseded**.
5. **"`final_llm_import` TODO / idle-no-work / no output".** A real rebuilt table now
   exists (386-cell quarantine caveat) — **superseded**.
6. **"Resource / efficiency table NOT EXECUTED".** A PARTIAL measured subset now
   exists — **superseded**. A further 2026-11-06 update **supersedes** the earlier
   "peak VRAM is NOT_MEASURED for all 6 rows": job 744532 measured MIFlu at
   **4816 MiB** (other 5 rows still `NOT_MEASURED`); T6 is now
   `PARTIAL (IMPROVED)`. Still no full-1120 Pareto.
7. **"JBHI template/fees/AI disclosure UNVERIFIED".** A dated VERIFIED record now
   exists; only the template class-file download remains UNVERIFIED — **partly
   superseded**.
8. **"v7 DOCX/PDF NOT EXECUTED".** v7 DOCX/PDF and now the v8 DOCX/PDF with updated
   BODY exist — **superseded**. (These DOCX/PDF predate the FINAL T2/T6 results —
   see the blocked table below.)
9. **"T2 foundation models BLOCKED — no full weights / no tar / no scp / no isolated
   env / no pilot / no cells"** (`T2_VERDICT.md` §1–§8, earlier verdict; the earlier
   v8 audit row). **SUPERSEDED** by `T2_VERDICT.md` §FINAL UPDATE 2026-11-06
   (`status: COMPLETED_WITH_DOCUMENTED_SCOPE`): 4 pinned tars (5,024,901,120 B)
   scp'd and SHA-verified in sbatch 744607; env built by 744574/744576; pilot 744589
   PASSED; matrix 744607 ran the 8 faithful zero-shot cells. The §1–§8 `BLOCKED`
   record is retained verbatim as the historical earlier run, NOT erased. The
   80-cell expansion remains `NOT_EXECUTED_BY_PROTOCOL` (below).
10. **"T6 peak VRAM entirely NOT_MEASURED".** **SUPERSEDED for MIFlu only**: job
    744532 measured 4816 MiB; the other 5 rows remain `NOT_MEASURED`, the
    Chronos/TimesFM resource rows remain BLOCKED, and T6 stays `PARTIAL (IMPROVED)`.

## Partial / exploratory (unchanged caveats)

- Paired Wilcoxon + Holm on 28 models (378 pairs): 349 rejections, min adjusted
  p ≈ 6.9e-10. Cells share one national series and overlapping targets —
  **exploratory**, not independent-sample confirmation. A dependence-aware/blocked
  analysis is NOT done.
- Seed-cluster bootstrap (1,000 resamples): 359/378 95% CIs exclude zero; addresses
  seed-level dependence but not overlapping lengths/targets. Still not confirmatory.
- Regional means are 10-variable `mse_z`, not comparable to 7-channel national means.
- The two quarantined corrupt legacy MIFlu NPZs (T3) remain unresolved for any claim
  based on that legacy analysis tree.
- Peak evaluation of the **1120-cell model panel** is **RETROSPECTIVE final-vintage**
  — no real-time / clinical claim. The frozen CDC vintage re-scores only the
  **REFERENCE** peak assignment on as-of data (18 seasons, 7 peak weeks moved = 38.9%);
  it does NOT re-score the model panel, whose peak metrics remain retrospective.

## Blocked / NOT_MEASURED / UNVERIFIED (exact evidence + smallest next action)

| Item | Status | Exact evidence | Smallest next action |
|---|---|---|---|
| Numerical foundation models (Chronos/TimesFM) | **COMPLETED_WITH_DOCUMENTED_SCOPE** (earlier `BLOCKED` superseded) | `v8/foundation/T2_VERDICT.md` §FINAL UPDATE; `T2_PILOT_AND_MATRIX.md`; `T2_DOWNLOAD_RESULT.md`; `FOUNDATION_ROSTER.csv`. 4 tars (5,024,901,120 B) + scp + remote SHA-256 inside 744607; env 744574/744576; pilot 744589 PASSED (MSE 0.3913, 10.191±0.446 ms, 596 MiB); matrix 744607 8/8 `ok`, 8 NPZ, 2608 MiB, 18.00 s. SEPARATE roster, never merged into 28-arm family / 1120 panel; both checkpoints UNIVARIATE, 7 channels as a batch of 7 independent series (discards cross-channel dependence, NOT information-set-matched); zero-shot, no fine-tuning | Keep the separate roster; if a multivariate-native Apache-2.0 checkpoint is needed run Chronos-2 (natively multivariate, tar downloaded but NOT executed) with an information-set-matched adapter. Do NOT present the 8 cells as the 1120 panel or as an 80-cell panel |
| T2 80-cell expansion (2 models × 4 L × 10 seeds) | **NOT_EXECUTED_BY_PROTOCOL — STILL BLOCKED** | `v8/foundation/T2_PILOT_AND_MATRIX.md` §6/§7; `FOUNDATION_MATRIX_REPORT.json`: `"requested_80_cells":"NOT_EXECUTED_BY_PROTOCOL"`. Exact reason: frozen zero-shot models have NO training seed dimension, so 10 seeds would produce 10 IDENTICAL predictions; the smallest faithful subset (2×4 L = 8 cells) was executed instead. This is a documented protocol decision, NOT a failure and NOT a claim that 80 cells ran | Do not pad the panel with duplicates. Only if a genuinely stochastic/trained zero-shot variant exists would a seed dimension be meaningful; otherwise keep the 8-cell subset explicitly labelled |
| T2 foundation latency honesty caveat | **LIMIT (not blocked)** | `T2_PILOT_AND_MATRIX.md` §5.1: TimesFM `wall_s=0.0` and `0.004/2.483/4.489/6.492` ms are loop/slicing timings of ONE shared `tfm.forecast` call, NOT four independent forward latencies; Chronos L24 `221.835` ms includes one-time CUDA init; the ONLY warmed-up repeated latency is the pilot's `10.191±0.446` ms (warm-up 1 / repeat 5) | Quote only the pilot latency as a measured inference latency; never present the `FOUNDATION_CELLS.csv` latency/wall_s columns as repeated measurements |
| CDC official release calendar / revision id | **NOT CLAIMED (scientific limit, not a blocker)** | Delphi `release_date` is a Delphi-ingest proxy, NOT a CDC-issued official revision number; no official CDC release calendar exists. TASK 4 is COMPLETED on the frozen Delphi vintage (`v8/cdc_vintage/T4_CORRECTION.md`); the earlier `BLOCKED: no release-calendar/vintage source found` verdict was erroneous (it never inspected `02_数字表格/`) | Retain the proxy caveat in any write-up; do NOT claim an official CDC revision id |
| CDC peak re-scoring (as-of) | **COMPLETED (reference assignment)** | `02_数字表格/cdc_peak_revintage.csv` (sha256 `7c9b5df8…`): 18 seasons scored, 7 peak weeks move = 38.9%; re-scores the REFERENCE peak assignment on AS-OF first print vs FINAL. Earlier `BLOCKED` claim was erroneous (it confused this with the 1120-cell model panel). Model peak metrics remain retrospective | None for the reference assignment; model-panel re-scoring (not part of TASK 4) would still need the `step → MMWR epiweek` alignment |
| JBHI template class-file download | **UNVERIFIED** | `v8/JBHI_VERIFICATION_20261106.md` §1 rows 9–11, §2–§3: selector `404` (browser UA) / WAF `418` (pyreq headers) / `/api` `302`→`502` | Human browser session at `https://template-selector.ieee.org/`, pin filename + SHA-256, apply `JBHI_PROVENANCE_PATCH.md` |
| `peak_vram_mib` (resource rows) | **PARTIAL (IMPROVED)** — MIFlu **MEASURED = 4816 MiB**; other 5 rows **NOT_MEASURED** | `v8/RESOURCE_MEASUREMENTS.csv` (MIFlu row), `v8/T6_VERDICT.md` §UPDATE 2026-11-06, `v8/T6_GPU_UPDATE.md`: job **744532** `t6_res_gpu_v8b` (`stingy`/`gpu-a100-05`/`A100-SXM4-80GB`, driver 580.167.08) ran a REAL MIFlu forward from an existing checkpoint; 63 `nvidia-smi` samples, min 16, `status=MEASURED`; forward wall 62.94 s. No GPU measurement job ran for NLinear / PatchTST / DeepSeek-R1-Distill-Qwen-1.5B / Chronos / TimesFM → those 5 rows remain `NOT_MEASURED` ("no GPU measurement job ran for this model"). All rows `scope=subset_only_not_full_1120`; ONE cell (L=36, seed=2023), no full-1120 Pareto | Re-run a GPU measurement job for the remaining 5 models if a full subset picture is needed; do NOT invent VRAM for them |
| True model-forward / per-forward inference latency (all 6 rows) | **NOT_MEASURED** | `v8/T6_GPU_UPDATE.md` §4.2/§8: job 744532's **62.94 s** is the whole-process wall clock for ONE cell's export (data + checkpoint load + GPU forward + writing), NOT a repeated per-forward inference latency; `true_model_forward_latency_ms` stays `NOT_MEASURED` for every row. Existing `inference_latency_*` values are NPZ scoring-path latency ONLY (0.0287–0.0297 ms), explicitly "NOT a model forward pass". No warm-up/repeat neural-forward timing was performed | Warm-up + repeated timing of an actual neural forward pass, per model, if needed |
| Chronos / TimesFM resource rows (T6 `RESOURCE_MEASUREMENTS.csv`) | **BLOCKED / NOT_EXECUTED — STILL** | `v8/RESOURCE_MEASUREMENTS.csv` rows 5–6 and `v8/T6_VERDICT.md` §UPDATE "STILL NOT MEASURED" item 3: every resource field `NOT_MEASURED`, no T6 GPU measurement job ran for these two models. NOTE: the verbatim reason string in those files ("TASK 2 is BLOCKED — no full pinned weights, no isolated HPC env, no 1-cell pilot") predates T2's FINAL `COMPLETED_WITH_DOCUMENTED_SCOPE` and is the earlier-run record, not a current T2 fact. The T2 foundation execution (jobs 744589/744607) lives on the SEPARATE `FOUNDATION_ROSTER.csv` and was NOT merged into these T6 resource rows, the 28-arm family or the 1120 national panel | Keep them BLOCKED until a dedicated T6 GPU measurement job runs for the foundation checkpoints; do NOT copy the T2 pilot/matrix VRAM (596/2608 MiB) into these rows |
| Full 1120-cell / 28-arm Pareto | **NOT CLAIMED** | Every resource row `scope=subset_only_not_full_1120`; only 4 of 6 subset models measured on 1 cell each | Extend subset if a full picture is needed |
| 2 quarantined legacy MIFlu NPZ | **UNRESOLVED** | `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/QUARANTINE.json` | Regenerate or explicitly exclude before any legacy analysis-tree claim |

## FINAL v8 status of all 8 tasks

| Task | Status |
|---:|---|
| T1 Walk-forward | **COMPLETED** — 1020/1020 `ok` (LEGACY 5-fold N=3 panel, a DIFFERENT scoring population from the 1120 national panel) |
| T2 Foundation models | **COMPLETED_WITH_DOCUMENTED_SCOPE** — 8/8 zero-shot cells (jobs 744589/744607), 4 tars + remote SHA verify, isolated env 744574/744576; 80-cell expansion `NOT_EXECUTED_BY_PROTOCOL`; separate roster, never merged |
| T3 `final_llm_import` | **COMPLETED** — real legacy table (386 cells) with a 2-NPZ quarantine caveat |
| T4 CDC vintage | **COMPLETED** (corrected 2026-11-06) — frozen 7192/848-row reconstruction + 18-season/7-peak-week re-scoring; earlier `BLOCKED` verdict erroneous |
| T5 JBHI | **COMPLETED** — dated record; template UNVERIFIED; `submission-ready: NO` |
| T6 Resources | **PARTIAL (IMPROVED)** — MIFlu peak VRAM 4816 MiB + real forward wall 62.94 s (job 744532); other 5 rows NOT_MEASURED; Chronos/TimesFM resource rows BLOCKED; no full-1120 Pareto |
| T7 v8 documents | **COMPLETED** — 3 DOCX/PDF + markdown/CSV/verdict; NOTE: the DOCX/PDF bodies predate the FINAL T2/T6 results and need a rebuild |
| T8 Final package | **COMPLETED (PRELIMINARY PACKAGING PASS)** — validator `PASS`, `scientific_readiness: NOT_ASSESSED`; package rebuild required (see `MESSAGE_TO_CHATGPT.md`) |

## Bottom line

The new 1120-cell national panel is real and scores differently from the frozen
historical snapshot, especially on peak skill. The LEGACY walk-forward panel is now
complete at 1020/1020 but is a **different scoring population** and must never be
merged with the national panel or with `CELL_METRICS.csv`. **TASK 4 (CDC vintage) is now
COMPLETED** on the frozen `02_数字表格/` reconstruction (corrected 2026-11-06: the earlier
`BLOCKED: no release-calendar/vintage source found` verdict was erroneous because
`02_数字表格/` was never inspected). Retained limits — Delphi proxy (NOT a CDC-issued
official revision number), reference-peak-only re-scoring, retrospective model peak
metrics, no 2002 real-time vintage — still apply. T2 foundation models are now
**COMPLETED_WITH_DOCUMENTED_SCOPE** (8 executed zero-shot cells on a SEPARATE
roster; the 80-cell expansion is STILL `NOT_EXECUTED_BY_PROTOCOL`, the
per-channel-independent adapter discards cross-channel dependence and is NOT
information-set-matched, and no training was done); T6 is **PARTIAL (IMPROVED)**
with MIFlu peak VRAM 4816 MiB measured (job 744532) while the other 5 rows and the
Chronos/TimesFM resource rows remain NOT_MEASURED / BLOCKED. The JBHI template
download, true model-forward latency, the T3 2-NPZ quarantine and the rebuild of the
3 v8 DOCX/PDF remain honestly UNVERIFIED / NOT_MEASURED / UNRESOLVED with exact
evidence and next actions. The manuscript is **not** submission-ready; the T8
validator PASS is structural only (`scientific_readiness: NOT_ASSESSED`).
