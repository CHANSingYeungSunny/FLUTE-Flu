# Scientific audit — FINAL v8 status (synced 2026-11-07 HKT / 2026-11-06 UTC; FINAL T2/T3/T5/T6 sync)

v8 copy of `final/SCIENTIFIC_AUDIT.md`, updated to reflect the **FINAL v8 status of
all 8 tasks** after T1–T8. It does not overwrite the frozen historical CSVs or the
v7/final source audits (`AGENTS.md` RULE 4). All claims below are tied to on-disk
evidence re-checked 2026-11-06, then **re-synced on 2026-11-07 (HKT) with the FINAL
T2/T3/T5/T6 results** (verified against `v8/foundation/T2_FULL80.md`,
`FOUNDATION_80_CELLS.csv`, `FOUNDATION_80_REPORT.json`, `v8/T3_RESTORE.md`,
`v8/PAPER_TO_CODE.md`, `v8/JBHI_PROVENANCE_PATCH.md`,
`v8/packaging/build_v8_return.py`, `v8/T6_FINAL_SWEEP.md`,
`v8/T6_VERDICT.md` §FINAL UPDATE, `v8/RESOURCE_MEASUREMENTS.csv`). A structural
validator `PASS` is `scientific_readiness: NOT_ASSESSED`. **The manuscript is NOT
submission-ready.** No training, download, HPC job or SSH was run for this sync.

**Sync note — old/new separation (which old claim is SUPERSEDED).** This is the
**second** 2026-11-07 sync. It SUPERSEDES (but does NOT silently erase) the earlier
2026-11-07 sync statements below, each of which is retained as a labelled historical
record:

| Earlier claim | FINAL state (2026-11-07 second sync) |
|---|---|
| "T2 `COMPLETED_WITH_DOCUMENTED_SCOPE`: only 8 zero-shot cells executed (jobs 744589/744607); 80-cell expansion `NOT_EXECUTED`" | **SUPERSEDED**: T2 is now **FULLY COMPLETED with 80 valid cells** (job **744886** `t2_fm_full80`); 80/80 `ok`, all finite, 80 real NPZ. The 10 replicates are **10 distinct forecast origins** (rows 773–782), not 10 seeds. The **literal 10-seed** dimension stays `NOT_EXECUTED_BY_PROTOCOL` with the exact frozen-zero-shot reason. |
| "T3 `COMPLETED` with a 2-NPZ quarantine caveat; table reflects 386 readable cells, hash `2e03b510…`" | **SUPERSEDED / RESOLVED**: job **744884** COPY-restored the 2 NPZ; validation **388/388 readable, 0 unreadable**; `final_llm_import` re-run rc=0 / `ok=true`; `BENCH_MSE_BY_MODEL_L.csv` hash now **`a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`** (69 lines). The 2 original corrupt files remain archived (not deleted). |
| "T5 provenance patch not applied / `JBHI_PROVENANCE_PATCH.md` must be pasted by the owner" | **SUPERSEDED**: T5 step 4 is DONE — `v8/PAPER_TO_CODE.md` created with the dated JBHI guidance verification applied, `v8/packaging/build_v8_return.py` patched to prefer the v8 copy, v7 original byte-identical, patch marked applied. Official template class file **remains UNVERIFIED**. |
| "T6 `PARTIAL (IMPROVED)`: only MIFlu VRAM 4816 MiB measured; other 5 rows `NOT_MEASURED`; Chronos/TimesFM resource rows BLOCKED" | **SUPERSEDED**: T6 is now **COMPLETED for all 6 representative models** (jobs **744897** / **744899**). All 6 peak VRAM values measured. Only the **3 isolated single-forward latencies** (MIFlu / NLinear / PatchTST) remain `NOT_MEASURED`. |

The earlier `T2 status: BLOCKED / no weights / no env / no pilot / no cells` and
`T6 peak_vram_mib: NOT_MEASURED for all 6 rows` statements from prior versions are
likewise SUPERSEDED, not erased. Nothing here is called "all done".

Old-snapshot / new-panel separation is mandatory: the frozen `02_数字表格/` 28-arm
snapshot, the new 1120-cell national panel, the LEGACY 5-fold N=3 walk-forward panel,
the LEGACY `final_llm_import` analysis tree (now 388/388 cells), the frozen CDC ILINet
vintage reconstruction in `02_数字表格/` (a Delphi proxy; TASK 4 COMPLETED — corrected
2026-11-06, see `v8/cdc_vintage/T4_CORRECTION.md`) and the foundation roster (80 cells)
are **separate scoring populations**. See `v8/docs/V8_SCIENTIFIC_ADDENDUM.md` §0.

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
| **`final_llm_import` table now built from 388/388 restored cells (T3 FINAL)** | `v8/T3_RESTORE.md`: job **744884** COPY-restored `miflu_L36_s2021` / `miflu_L60_s2021` from their valid `author_runs/L##_all7/` 7-channel copies; in-sbatch validation **388/388 readable, 0 unreadable, `(W,7,L)`, all finite**; exact `final_llm_import` re-run: all 3 scripts rc=0, `ok=true`; `BENCH_MSE_BY_MODEL_L.csv` `2e03b510…` → **`a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`** (69 lines). The 2 original corrupt files remain archived (not deleted) in `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/` |
| **CDC ILINet vintage is COMPLETE (TASK 4 `COMPLETED`, corrected 2026-11-06)** | Frozen `02_数字表格/cdc_vintage_raw.csv` (7192 rows, sha256 `e0c5512b…`), `02_数字表格/cdc_vintage.csv` (848 rows, sha256 `5a49e6be…`), `02_数字表格/cdc_vintage_report.md` (sha256 `e2da6b37…`), `02_数字表格/cdc_peak_revintage.csv` (sha256 `7c9b5df8…`; 18 seasons scored, 7 peak weeks moved = 38.9%), builder `05_程序代码/cdc_vintage_build.py` (sha256 `8c1e4b1e…`). The earlier `PARTIAL / BLOCKED` verdict is SUPERSEDED by `v8/cdc_vintage/T4_CORRECTION.md`. Delphi `release_date` remains a proxy, NOT a CDC-issued official revision number |
| JBHI guidance verified (dated) + **T5 step 4 applied** | `v8/JBHI_VERIFICATION_20261106.md`: 14/16 pp incl. supplementary, ≤250-word abstract, double-column single-spaced, embedded figures/tables, AI disclosure, APC US$2,800 (2026). `v8/PAPER_TO_CODE.md` (v8 copy, dated guidance applied) + `v8/packaging/build_v8_return.py` patched to prefer it over the frozen v7 skeleton; v7 original byte-identical; `v8/JBHI_PROVENANCE_PATCH.md` marked applied. Official template class file UNVERIFIED |
| **T6 resources COMPLETED for all 6 representative models** | `v8/T6_FINAL_SWEEP.md`, `v8/T6_VERDICT.md` §FINAL UPDATE, `v8/RESOURCE_MEASUREMENTS.csv` (sha256 `9574eeff6f0e39ddba6488b2e8fe8ef09b763c90fdd27223d7960b8f886b1117`). Jobs **744897** `t6_final_sweep` + **744899** `t6_miflu_fix` (stingy / A100-SXM4-80GB, driver 580.167.08): peak VRAM MIFlu **4816 MiB** (46 + 63 samples), NLinear **558** (36), PatchTST **720** (7), GPT-2 frozen encoder **1070** (11), Chronos **596** (6), TimesFM **2594** (11). Warm-up+repeated REAL model-forward latencies: GPT-2 **6.98 ± 0.097 ms** (1/10), Chronos **9.854 ± 0.337 ms** (1/20), TimesFM **48.273 ± 3.531 ms** (1/10). Full-job walls: MIFlu 7-channel cell export **62.94 s**, NLinear 20-epoch training+export **35.73 s**, PatchTST **6.86 s**. Representative frozen encoder = GPT-2 from the local HF cache; the earlier DeepSeek-R1-Distill-Qwen-1.5B 24 s queue-log wall is a DIFFERENT encoder retained only as context. All rows `scope=subset_only_not_full_1120`; NO full-1120 Pareto claim |
| **T2 foundation matrix FULLY COMPLETED — 80 valid cells** | `v8/foundation/T2_FULL80.md`, `v8/foundation/t2_hpc_evidence/full80_out/`: job **744886** `t2_fm_full80` (stingy / A100-SXM4-80GB); `FOUNDATION_80_CELLS.csv` sha256 `627826765ee56f0ea84bac17aa2e073c86f833f0718bc4aa6e0cd7ca0cd192cf`, `FOUNDATION_80_REPORT.json` sha256 `07654f2652d2c3d72cf022f7e836ea78a893db0971210b6da092bf315a683e84`; **80/80 `ok`, all finite, 80 real prediction NPZ**. Matrix = 2 models × 4 L (24/36/48/60) × 10 replicates; because both checkpoints are FROZEN ZERO-SHOT (10 seeds would give 10 identical predictions), the 10 replicates are **10 distinct forecast origins (rows 773–782)** with their own context and target; `seed_semantics=NOT_APPLICABLE`, `replicate_kind=rolling_origin`. Peak VRAM **2608 MiB** (51 samples), wall **50.71 s**, Chronos **10.229 ± 1.074 ms** (warm-up 1 / repeat 10), TimesFM **50.906 ± 4.459 ms** (warm-up 1 / repeat 5). Labels `foundation_chronos` / `foundation_timesfm` are a SEPARATE ROSTER, never merged into the 28-arm family / 1120 panel. Both checkpoints UNIVARIATE; 7 channels as a batch of 7 independent series (discards cross-channel dependence, NOT information-set-matched); each model applies its own internal scaling; zero-shot, no training; TimesFM `cell_wall_ms` is one shared forecast call per origin (4 L slices NOT four independent forwards) |

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
   exists; the 386-cell / 2-quarantine caveat is **RESOLVED (SUPERSEDED)** by the
   388/388 restore and hash `a7d98ad8…` (T3 FINAL above).
6. **"Resource / efficiency table NOT EXECUTED".** A measured subset now exists —
   **superseded**. The later "MIFlu-only 4816 MiB / other 5 NOT_MEASURED" and
   the "T6 PARTIAL (IMPROVED)" statements are **SUPERSEDED** by the FINAL
   COMPLETED-for-6-models sweep (T6 above). The earlier "peak VRAM is NOT_MEASURED
   for all 6 rows" is likewise superseded.
7. **"JBHI template/fees/AI disclosure UNVERIFIED".** A dated VERIFIED record now
   exists — **partly superseded**. The "provenance patch not applied / owner must
   paste" note is **SUPERSEDED** (step 4 DONE); only the official template class-file
   download remains UNVERIFIED.
8. **"v7 DOCX/PDF NOT EXECUTED".** v7 DOCX/PDF and now the v8 DOCX/PDF with updated
   BODY exist — **superseded**. (These DOCX/PDF bodies predate the FINAL T2/T3/T5/T6
   results — see the blocked table below.)
9. **"T2 foundation models BLOCKED — no full weights / no tar / no scp / no isolated
   env / no pilot / no cells"** (`T2_VERDICT.md` §1–§8) and its 2026-11-07 successor
   **"T2 `COMPLETED_WITH_DOCUMENTED_SCOPE`: 8 cells only; 80-cell expansion
   `NOT_EXECUTED`"** (`T2_VERDICT.md` §FINAL UPDATE 2026-11-06). **BOTH SUPERSEDED**
   by `v8/foundation/T2_FULL80.md`: job 744886 produced **80/80 valid cells** via
   10 distinct forecast origins (rows 773–782). The §1–§8 `BLOCKED` record and the
   §FINAL UPDATE 8-cell record are retained verbatim as the historical earlier runs,
   NOT erased. The **literal 10-seed expansion** remains `NOT_EXECUTED_BY_PROTOCOL`
   (below).
10. **"T6 peak VRAM entirely NOT_MEASURED" / "PARTIAL (IMPROVED) — other 5 rows
    NOT_MEASURED" / "Chronos / TimesFM resource rows BLOCKED".** **SUPERSEDED** by
    `v8/T6_FINAL_SWEEP.md` and `v8/T6_VERDICT.md` §FINAL UPDATE: all 6 models'
    peak VRAM measured by jobs 744897/744899. The `RESOURCE_MEASUREMENTS.csv` CSV
    sha256 is now `9574eeff…` (the older `D609D57D…` / `bde9031f…` values are
    historical).
11. **"T3 has 2 quarantined NPZ / 386 readable cells / table hash `2e03b510…`".**
    **SUPERSEDED / RESOLVED** by `v8/T3_RESTORE.md` (388/388, hash `a7d98ad8…`).

## Partial / exploratory (unchanged caveats)

- Paired Wilcoxon + Holm on 28 models (378 pairs): 349 rejections, min adjusted
  p ≈ 6.9e-10. Cells share one national series and overlapping targets —
  **exploratory**, not independent-sample confirmation. A dependence-aware/blocked
  analysis is NOT done.
- Seed-cluster bootstrap (1,000 resamples): 359/378 95% CIs exclude zero; addresses
  seed-level dependence but not overlapping lengths/targets. Still not confirmatory.
- Regional means are 10-variable `mse_z`, not comparable to 7-channel national means.
- The T3 legacy `final_llm_import` table is a LEGACY analysis-tree product (388/388
  restored cells), NOT the 1120 national panel and NOT the LEGACY 5-fold N=3 WF panel.
- Peak evaluation of the **1120-cell model panel** is **RETROSPECTIVE final-vintage**
  — no real-time / clinical claim. The frozen CDC vintage re-scores only the
  **REFERENCE** peak assignment on as-of data (18 seasons, 7 peak weeks moved = 38.9%);
  it does NOT re-score the model panel, whose peak metrics remain retrospective.
  Delphi `release_date` is a proxy, NOT a CDC-issued official revision number.

## Blocked / NOT_MEASURED / UNVERIFIED (exact evidence + smallest next action)

| Item | Status | Exact evidence | Smallest next action |
|---|---|---|---|
| Numerical foundation models (Chronos / TimesFM) | **COMPLETED — 80/80 valid cells** | `v8/foundation/T2_FULL80.md`, `FOUNDATION_80_CELLS.csv`, `FOUNDATION_80_REPORT.json`, `full80_out/` 80 NPZ: job 744886, 2 models × 4 L × 10 **forecast origins** (rows 773–782). SEPARATE roster, never merged into the 28-arm family / 1120 panel; both checkpoints UNIVARIATE, 7 channels as a batch of 7 independent series (discards cross-channel dependence, NOT information-set-matched); each model applies its own internal scaling; zero-shot, no training; TimesFM `cell_wall_ms` = one shared forecast call per origin (NOT 4 independent forwards) | Keep the separate roster; if a multivariate-native Apache-2.0 checkpoint is needed, run Chronos-2 with an information-set-matched adapter. Do NOT present the 80 cells as the 1120 panel |
| **Literal 10-seed (rather than 10-origin) foundation expansion** | **`NOT_EXECUTED_BY_PROTOCOL` — STILL BLOCKED** | `FOUNDATION_80_REPORT.json`: `literal_10_seed_expansion = NOT_EXECUTED_BY_PROTOCOL`, `seed_semantics = NOT_APPLICABLE`, `replicate_kind = rolling_origin`. Exact reason: **"no training seed dimension in a frozen zero-shot model; 10 seeds would produce 10 identical predictions"** (same string in `FOUNDATION_MATRIX_REPORT.json` reason field). The 80 cells ARE done via 10 distinct origins (rows 773–782), each with its own context/target; the literal seed dimension is not | Do not pad the panel with duplicates. Only if a genuinely stochastic/trained zero-shot variant exists would a seed dimension be meaningful; keep `seed_semantics=NOT_APPLICABLE` |
| No multivariate-native checkpoint / no full-1120 comparison / univariate adapter limits | **BLOCKED (scientific), STILL** | `T2_FULL80.md` §Adapter; `FOUNDATION_80_REPORT.json` `adapter_limits`: discards cross-channel dependence; NOT information-set matched to the multivariate arms; model applies its own internal scaling, benchmark z-space passed through. No full-1120-panel comparison; no merge into the 28-arm family | Run a natively-multivariate Apache-2.0 checkpoint with an information-set-matched adapter, or quote the limits with every result |
| T2 foundation latency / wall-time honesty caveat | **LIMIT (not blocked)** | `T2_FULL80.md`: Chronos **10.229 ± 1.074 ms** (warm-up 1 / repeat 10), TimesFM **50.906 ± 4.459 ms** (warm-up 1 / repeat 5) are the warmed-up repeated forward latencies; TimesFM `cell_wall_ms` is ONE shared `forecast` call per origin, the 4 L slices are NOT four independent forwards. Earlier pilot-only numbers (10.191 ± 0.446 ms; `221.835` ms with one-time CUDA init; TimesFM loop/slicing 0.004/2.483/4.489/6.492 ms) belong to the SUPERSEDED 8-cell run | Quote only the full80 warmed-up latencies as repeated inference latencies; never present the 4 L slices as independent forwards |
| CDC official release calendar / revision id | **NOT CLAIMED (scientific limit, not a blocker)** | Delphi `release_date` is a Delphi-ingest proxy, NOT a CDC-issued official revision number; no official CDC release calendar exists. TASK 4 is COMPLETED on the frozen Delphi vintage (`v8/cdc_vintage/T4_CORRECTION.md`) | Retain the proxy caveat in any write-up; do NOT claim an official CDC revision id |
| CDC peak re-scoring (as-of) | **COMPLETED (reference assignment)** | `02_数字表格/cdc_peak_revintage.csv` (sha256 `7c9b5df8…`): 18 seasons scored, 7 peak weeks move = 38.9%; re-scores the REFERENCE peak assignment on AS-OF first print vs FINAL. Model peak metrics remain retrospective | None for the reference assignment; model-panel re-scoring would still need the `step → MMWR epiweek` alignment |
| JBHI official template class-file download | **UNVERIFIED** | `v8/JBHI_VERIFICATION_20261106.md`, `v8/PAPER_TO_CODE.md`: selector `404` (browser UA) / WAF `418` (pyreq headers) / `/api` `302`→`502`. T5 step 4 (provenance patch) IS applied; no template class file was obtained | Human browser session at `https://template-selector.ieee.org/`, pin filename + SHA-256. `manuscript_submission_ready: NO` |
| `peak_vram_mib` (resource rows) | **COMPLETED for all 6 representative models** | `v8/T6_FINAL_SWEEP.md`, `v8/RESOURCE_MEASUREMENTS.csv` sha256 `9574eeff…`: MIFlu 4816 (46+63), NLinear 558 (36), PatchTST 720 (7), GPT-2 frozen encoder 1070 (11), Chronos 596 (6), TimesFM 2594 (11) MiB; jobs 744897/744899 on A100-SXM4-80GB, driver 580.167.08. All rows `scope=subset_only_not_full_1120`; NO full-1120 Pareto claim. Earlier "5 rows NOT_MEASURED / Chronos–TimesFM BLOCKED" SUPERSEDED | Extend the subset only if a full-1120 picture is needed; do NOT invent a full Pareto |
| **MIFlu / NLinear / PatchTST isolated warm-up+repeated single-forward latency** | **`NOT_MEASURED` — STILL** | `v8/T6_FINAL_SWEEP.md` §範圍, `v8/RESOURCE_MEASUREMENTS.csv`: the measured quantity was a real full 7-channel cell export (62.94 s) / 20-epoch training+export job (35.73 s / 6.86 s), NOT an isolated neural forward. Old NPZ scoring-path numbers (0.0287–0.0297 ms) moved to `npz_scoring_path_latency_ms_*` columns and labelled NOT a model forward. GPT-2 / Chronos / TimesFM DO have warmed-up repeated forward latencies (6.98 / 9.854 / 48.273 ms) | Warm-up + repeated timing of an isolated neural forward pass for these 3 models, if needed |
| Full 1120-cell / 28-arm Pareto | **NOT CLAIMED** | Every resource row `scope=subset_only_not_full_1120`; the 6 measured models are a representative subset, not the full 1120 panel | Extend subset if a full picture is needed |
| 2 quarantined legacy MIFlu NPZ (T3) | **RESOLVED — SUPERSEDED** | `v8/T3_RESTORE.md`: job 744884 COPY-restored both from valid 7-channel copies; 388/388 readable, 0 unreadable; `final_llm_import` rc=0 / `ok=true`; new table hash `a7d98ad8…` (69 lines). The 2 original corrupt files remain archived (not deleted) in `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/`. The earlier "386 readable / 2 quarantined" caveat is RESOLVED | None for the legacy table; keep the LEGACY analysis-tree label |
| T5 provenance patch (step 4) | **APPLIED — SUPERSEDED** | `v8/PAPER_TO_CODE.md` (v8 copy with dated JBHI guidance verification applied), `v8/packaging/build_v8_return.py` patched to prefer it over the frozen v7 skeleton; v7 original byte-identical; `v8/JBHI_PROVENANCE_PATCH.md` marked applied. Earlier "not applied / owner must paste" is SUPERSEDED | Only the official template class file remains UNVERIFIED |
| Confirmatory dependence-aware statistics | **NOT DONE (exploratory)** | Paired Wilcoxon/Holm 349/378, seed-cluster bootstrap 359/378; cells share one national series and overlapping targets → not independent-sample confirmation | Run a dependence-aware / blocked analysis before any confirmatory significance claim |
| Model-panel peak metrics | **RETROSPECTIVE (scientific limit)** | Delphi vintage is a proxy, NOT CDC-issued revision ids; frozen CDC re-scores only the REFERENCE peak assignment, not the 1120-cell model panel; no 2002 real-time vintage | Retain retrospective wording; no real-time/clinical claim |
| 3 v8 DOCX/PDF bodies vs FINAL T2/T3/T5/T6 results | **STALE — NEEDS REBUILD (NOT EXECUTED)** | The v8b rebuild (`v8/docs/V8B_REBUILD_LOG.md`) folded in the earlier 8-cell T2 / 1-VRAM T6 state; the FINAL 80-cell T2, 388/388 T3, T5 step 4 and 6-model T6 results landed afterwards. `v8/T7_VERDICT.md` | Rebuild the 3 DOCX/PDF from the synced `v8/docs/` markdown (owner/T7), then fold into the T8 package |
| T8 structural validator PASS | **NOT scientific certification / package rebuild pending** | `v8/T8_VERDICT.md`: `integrity_status: PASS`, `scientific_readiness: NOT_ASSESSED`; current `RETURN_V8/` / ZIPs predate the FINAL T2/T3/T5/T6 results. ZIP hashes are in `v8/packaging/FINAL_HASHES.txt` (OUTSIDE `RETURN_V8/` deliberately — the package mirrors its own docs, so ZIP hashes change on rebuild); do NOT hard-code them | Re-run the single T8 builder (owned by the main agent), then re-check `PASS` AND `NOT_ASSESSED` |

## FINAL v8 status of all 8 tasks

| Task | Status |
|---:|---|
| T1 Walk-forward | **COMPLETED** — 1020/1020 `ok` (LEGACY 5-fold N=3 panel, a DIFFERENT scoring population from the 1120 national panel) |
| T2 Foundation models | **COMPLETED — 80/80 valid cells** via 10 distinct forecast origins (rows 773–782), job 744886; `seed_semantics=NOT_APPLICABLE`, `replicate_kind=rolling_origin`; literal 10-seed expansion `NOT_EXECUTED_BY_PROTOCOL` with exact reason; separate roster, never merged; univariate adapter limits retained |
| T3 `final_llm_import` | **COMPLETED — FULLY RESTORED** — 388/388 readable cells, 0 unreadable; `BENCH_MSE_BY_MODEL_L.csv` hash `a7d98ad8…` (69 lines); 2 original corrupt files archived (not deleted) |
| T4 CDC vintage | **COMPLETED** (corrected 2026-11-06) — frozen 7192/848-row reconstruction + 18-season/7-peak-week re-scoring; earlier `BLOCKED` verdict erroneous; Delphi proxy / retrospective model peaks |
| T5 JBHI | **COMPLETED — step 4 DONE** — dated record + `PAPER_TO_CODE.md` v8 copy + builder patch; template class file UNVERIFIED; `submission-ready: NO` |
| T6 Resources | **COMPLETED for all 6 representative models** — jobs 744897/744899; all 6 peak VRAM measured; 3 isolated single-forward latencies `NOT_MEASURED`; `scope=subset_only_not_full_1120`; no full-1120 Pareto |
| T7 v8 documents | **COMPLETED** — 3 DOCX/PDF + markdown/CSV/verdict; NOTE: the DOCX/PDF bodies predate the FINAL T2/T3/T5/T6 results and need a rebuild |
| T8 Final package | **COMPLETED (packaging pass)** — validator `PASS`, `scientific_readiness: NOT_ASSESSED`; package will be rebuilt once more by the main agent; ZIP hashes in `v8/packaging/FINAL_HASHES.txt`, not hard-coded |

## Bottom line

The new 1120-cell national panel is real and scores differently from the frozen
historical snapshot, especially on peak skill. The LEGACY walk-forward panel is now
complete at 1020/1020 but is a **different scoring population** and must never be
merged with the national panel or with `CELL_METRICS.csv`; the LEGACY
`final_llm_import` analysis tree (388/388 cells) and the foundation roster are
likewise separate. **TASK 4 (CDC vintage) is COMPLETED** on the frozen
`02_数字表格/` reconstruction, with retained limits (Delphi proxy, NOT a CDC-issued
official revision number; reference-peak-only re-scoring; retrospective model peak
metrics; no 2002 real-time vintage).

**T2 foundation models are now FULLY COMPLETED with 80/80 valid cells** (job 744886,
2 models × 4 L × 10 distinct forecast origins, rows 773–782, each with its own
context and target) on a SEPARATE roster; the **literal 10-seed** expansion stays
`NOT_EXECUTED_BY_PROTOCOL` with the exact reason "no training seed dimension in a
frozen zero-shot model; 10 seeds would produce 10 identical predictions"; the
per-channel-independent univariate adapter discards cross-channel dependence and is
NOT information-set-matched; no multivariate-native checkpoint, no full-1120
comparison, no training. **T3 is fully restored** (388/388, hash `a7d98ad8…`, 69
lines). **T5 step 4 is DONE** (v8 `PAPER_TO_CODE.md` + builder patch; v7 original
byte-identical) while the official JBHI template class file remains UNVERIFIED.
**T6 is COMPLETED for all 6 representative models** (jobs 744897/744899, all 6 peak
VRAM values measured), with the 3 isolated single-forward latencies (MIFlu / NLinear
/ PatchTST) still `NOT_MEASURED`, no full-1120 Pareto claim, and the DeepSeek
24 s wall retained only as context for a DIFFERENT encoder.

Still honestly UNVERIFIED / NOT_MEASURED / NOT DONE: the official JBHI template
class file, the 3 isolated single-forward latencies, confirmatory dependence-aware
statistics (paired inference remains exploratory), retrospective model-panel peak
metrics, the 3 v8 DOCX/PDF rebuild and the T8 package rebuild. The manuscript is
**not** submission-ready; the T8 validator PASS is structural only
(`scientific_readiness: NOT_ASSESSED`). Nothing is called "all done".
