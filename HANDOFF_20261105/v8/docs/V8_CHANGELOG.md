# V8 changelog — v7 → v8 (2026-11-06; re-synced 2026-11-07 HKT / 2026-11-06 UTC)

TASK 7 documentation change log. Companion to `V8_SCIENTIFIC_ADDENDUM.md`.
This is a **v8-owned** file; `HANDOFF_20261105/TASK_LOG.md`, `v7/*` and `final/*`
were NOT edited. Frozen CSVs in `02_数字表格/`, raw predictions, checkpoints and the
owner-edited PPTX were not touched.

## 1. Task-level changes (T1–T8)

> **NOTE (2026-11-07 sync).** The T2 and T6 rows below are the 2026-11-06 T7-build
> state and are **SUPERSEDED by §5** (`T2 → COMPLETED_WITH_DOCUMENTED_SCOPE`,
> `T6 → PARTIAL (IMPROVED)`). They are kept verbatim as the historical record, NOT
> silently overwritten.

| Task | v7 / pre-v8 claim | v8 verified state | What changed |
|---:|---|---|---|
| T1 | "walk-forward 802/1020 valid, 218 no NPZ"; "partial / invalid"; regional 51/53 or 473/1020 in older v7 text | **COMPLETED 1020/1020 `ok`** | Job 743850 reran 218 SKIPPED cells (rc=0); 744334 recomputed from raw NPZ. `WF_RECOMPUTED.csv` sha256 `53d0e0cb…`, means sha256 `c0e72f35…`. Baseline diff: recovered 218, changed 0, lost 0, missing 0. Legacy 5-fold N=3 panel, NOT the 1120 national panel. |
| T2 | "not implemented/pinned in this run" | **BLOCKED** with full provenance **[SUPERSEDED 2026-11-07 → §5.1: `COMPLETED_WITH_DOCUMENTED_SCOPE`; FINAL → §6 V8C: `COMPLETED, 80/80 cells`]** | Pinned repos/revisions/licences in `FOUNDATION_ROSTER.csv` + `FOUNDATION_MODEL_PROVENANCE.md`; no weights/env/pilot/80-cell matrix; named checkpoints UNIVARIATE; TimesFM 3.0 non-commercial; 11 frozen encoders NOT substitutes. Separate roster. |
| T3 | "TODO / idle-no-work / no output" | **COMPLETED** | **[SUPERSEDED V8C]** Real `BENCH_MSE_BY_MODEL_L.csv` (sha256 `2e03b510…`) from 386 readable legacy cells; 2 corrupt NPZs quarantined (not deleted). **FINAL (§6): job 744884 restored both → 388/388 readable, table `a7d98ad8…e46`.** Legacy analysis-tree table, not the 1120 panel. |
| T4 | "not reconstructed; peaks are retrospective" | **COMPLETED** (corrected 2026-11-06) | ERRONEOUS earlier `PARTIAL/BLOCKED` verdict superseded: `02_数字表格/` was never inspected and ALREADY held a complete CDC ILINet vintage reconstruction — frozen `cdc_vintage_raw.csv` (7192 rows), `cdc_vintage.csv` (848 rows), `cdc_vintage_report.md`, `cdc_peak_revintage.csv` (18 seasons, 7 peak weeks moved=38.9%), builder `05_程序代码/cdc_vintage_build.py`, all from the SAME Delphi `fluview` endpoint. Record `v8/cdc_vintage/T4_CORRECTION.md`. Retained limits: Delphi proxy (NOT a CDC official revision number), reference-peak-only re-scoring, retrospective 1120-cell model peak metrics, no 2002 real-time vintage. |
| T5 | "UNVERIFIED / not re-verified against live selector" | **COMPLETED** (dated record) | 14 pp incl. supplementary, ≤250-word abstract, double-column single-spaced, embedded figures/tables, AI disclosure, APC US$2,800 (2026) all VERIFIED. Template class-file UNVERIFIED (404 / WAF 418 / 302→502). `submission-ready: NO`. |
| T6 | "NOT EXECUTED / no measured table" | **PARTIAL** **[SUPERSEDED 2026-11-07 → §5.2: `PARTIAL (IMPROVED)`, MIFlu VRAM 4816 MiB]** | `RESOURCE_MEASUREMENTS.csv`: real wall times (MIFlu 581 s, NLinear 6 s, PatchTST 7 s, Qwen-1.5B 24 s), real NPZ scoring-path latency 0.0287–0.0297 ms (NOT a forward), versions Python 3.9.25 / numpy 2.0.1 / pandas 2.3.3 / torch 2.5.1. `peak_vram_mib` NOT_MEASURED; Chronos/TimesFM BLOCKED; every row `subset_only_not_full_1120`. |
| T7 | "v7 reports NOT UPDATED / only addendum + map" | **COMPLETED** | v8 DOCX/PDF (3 documents), this changelog, addendum, `DOCUMENT_UPDATE_MAP.csv`, `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`, `T7_VERDICT.md`. |
| T8 | n/a (new) | **COMPLETED (PRELIMINARY PACKAGING PASS)** | `RETURN_TO_CHATGPT.zip` / `RAW_EVIDENCE.zip` rebuilt; validator `PASS` but `scientific_readiness: NOT_ASSESSED`; `T8_VERDICT.md` explicitly notes T7 docs + T1-updated WF CSV were not folded in yet. |

## 2. Old claims explicitly SUPERSEDED (stated, not silently overwritten)

1. **"Walk-forward partial / invalid / 802 of 1020 / 473 of 1020 / 218 with no NPZ".**
   → Superseded by verified v8 state: **1020/1020 `ok`** on the LEGACY 5-fold N=3
   panel. Still NOT the 1120 national panel; the two populations must stay separate.
2. **"Table VI 2 of 53 regional cells missing"** (old `final/SCIENTIFIC_AUDIT.md`)
   and **"Table VI 51/53"** (older v7 Q&A text).
   → Superseded by **53/53 valid `mse_z` rows** (v7 onward, after rerunning
   L13/s2030 and L15/s2026); still 10-variable regional aggregates, not comparable
   to the 7-channel national means.
3. **"final_llm_import TODO / idle-no-work / no output".**
   → Superseded by a **real rebuilt table** (with the 386-cell quarantine caveat).
4. **"NLinear is the K&S peak champion (4/16)"** (old frozen snapshot).
   → Superseded on the NEW 1120 panel: MIFlu 252/1680, PatchTST 215/1680,
   NLinear 57/1680 step passes. Old 16-unit table is a different population.
5. **"monotonic depth trend"** → superseded: non-monotonic, K4 1.4989 best,
   K12 1.7604 worst.
6. **"resource / efficiency table NOT EXECUTED"** → superseded by a PARTIAL
   measured subset (no VRAM, no full-1120 Pareto). **FURTHER SUPERSEDED 2026-11-07
   for MIFlu only**: job 744532 measured peak VRAM 4816 MiB (§5.2); the other 5
   rows remain NOT_MEASURED; T6 stays `PARTIAL (IMPROVED)`.
7. **"JBHI template/fees/AI disclosure UNVERIFIED / not re-verified"** → superseded
   by a dated VERIFIED record; template class-file remains UNVERIFIED.
8. **"CDC vintage not reconstructed" / v8 `PARTIAL/BLOCKED`** → **SUPERSEDED by
   COMPLETED (corrected 2026-11-06)**: a complete frozen CDC ILINet vintage
   reconstruction and re-scored season peaks ALREADY existed in `02_数字表格/`; the
   earlier `BLOCKED: no release-calendar/vintage source found` verdict was erroneous
   (20-row sample only, `02_数字表格/` never inspected). Authoritative record
   `v8/cdc_vintage/T4_CORRECTION.md`. Retained scientific limits: Delphi `release_date`
   is a proxy, NOT a CDC-issued official revision number; only the REFERENCE peak
   assignment is re-scored on as-of data — 1120-cell model peak metrics remain
   retrospective; no 2002 real-time vintage. Peaks for the MODEL panel stay
   retrospective; no real-time/clinical claim.
9. **"v7 DOCX/PDF reports NOT EXECUTED"** → superseded by v7 DOCX/PDF and now by
   the v8 DOCX/PDF with updated BODY (not only an appendix). NOTE (2026-11-07): the
   **[SUPERSEDED V8C — the DOCX/PDF were rebuilt again as v8c and now carry the final results]** v8 DOCX/PDF predate the FINAL T2/T6 results and still say T2 `BLOCKED` / T6 VRAM
   `NOT_MEASURED` (§5.3).
10. **"T2 foundation models BLOCKED — no weights / no tar / no scp / no env / no
    pilot / no cells"** (§1 T2 row, `T2_VERDICT.md` §1–§8) → **SUPERSEDED by
    `COMPLETED_WITH_DOCUMENTED_SCOPE`** (§5.1): 4 tars + scp + remote SHA-256 in
    744607, env 744574/744576, pilot 744589 PASSED, matrix 744607 ran 8 faithful
    zero-shot cells. The 80-cell expansion remains `NOT_EXECUTED_BY_PROTOCOL` and
    the separate-roster / univariate-adapter limits remain in force.

## 3. New files written by TASK 7 (v8 scope only)

`HANDOFF_20261105/v8/docs/`
- `V8_SCIENTIFIC_ADDENDUM.md` (A–G + old/new separation + final 8-task status)
- `V8_CHANGELOG.md` (this file)
- `build_v8_manuscript.py`, `build_v8_internal_zh.py`, `build_v8_qa.py`,
  `build_v8_verify.py` (builders, v7 pattern)
- `V8_BUILD_RESULTS.json` (machine-readable hashes / page counts)

`HANDOFF_20261105/v8/`
- `DOCUMENT_UPDATE_MAP.csv`, `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`,
  `T7_VERDICT.md`

`01_最终报告/v8/`
- `ieee_manuscript_en_v8.docx` / `.pdf`
- `report_internal_zh_v8.docx` / `.pdf`
- `report_internal_qa_zh_v8.docx` / `.pdf`
- `PDF_CONVERSION_LOG.md` (exact commands, exit codes, errors, page counts)

## 4. Integrity notes

- No frozen CSV, raw prediction, checkpoint or owner-edited PPTX was modified.
- **2026-11-07 sync.** `v8/MESSAGE_TO_CHATGPT.md`, `v8/SCIENTIFIC_AUDIT.md`,
  `v8/BLOCKED_AND_UNVERIFIED.md`, `v8/DOCUMENT_UPDATE_MAP.csv`,
  `v8/docs/V8_SCIENTIFIC_ADDENDUM.md` and this `V8_CHANGELOG.md` WERE re-synced to
  the FINAL T2/T6 results. `v8/TASK_LOG.md`, `v8/T2_*`, `v8/T5_*`, `v8/T6_*`,
  `v8/T7_*`, `v8/T8_*`, `v8/foundation/*`, `v8/cdc_vintage/*`, `v8/packaging/*`,
  `v8/RETURN_V8/*`, `v8/RESOURCE_MEASUREMENTS.csv`, `01_最终报告/*`,
  `HANDOFF_20261105/final/*`, `HANDOFF_20261105/v7/*`, `02_数字表格/*` and
  `AGENTS.md` were NOT edited. No training, download or HPC job was re-run.
- Builder PDF conversion uses the prepared LibreOffice-kit CLI; a `PASS` is
  structural only. The manuscript is **NOT** called submission-ready.
- All numbers come from the verified v8 result set; nothing was fabricated.

## 5. FINAL T2 / T6 sync — 2026-11-07 (HKT) / 2026-11-06 (UTC)

Re-synced with the FINAL T2 and T6 results. **Nothing below silently overwrites an
old claim**; each subsection states exactly which old claim is superseded and keeps
the earlier record separately labelled (§1/§2 above). No training, download or HPC
job was re-run for this sync.

### 5.1 T2 — old `BLOCKED` superseded by `COMPLETED_WITH_DOCUMENTED_SCOPE`

**Old claim (superseded, kept verbatim in §1 T2 row, §2 item 10 and
`v8/foundation/T2_VERDICT.md` §1–§8):** "T2 BLOCKED — no full pinned weights, no
tar/scp, no isolated HPC env, no 1-cell pilot, no 80-cell matrix; `NOT_EXECUTED`".
The `BLOCKED` verdict applied to a missing-input condition that was subsequently
**eliminated by verified work** on 2026-11-06 UTC. `T2_VERDICT.md` §FINAL UPDATE
2026-11-06 records `status: COMPLETED_WITH_DOCUMENTED_SCOPE`; its §1–§8 `BLOCKED`
text is retained verbatim as the earlier run, NOT erased.

**New verified facts (evidence `v8/foundation/`):**

| item | value |
|---|---|
| 4 pinned weight tars | downloaded locally on Windows, **5,024,901,120 B** total; scp'd to `/gpfs1/scratch/sychan552/models/`; all **4 remote SHA-256 verified INSIDE sbatch 744607** and EXACTLY match local (`T2_DOWNLOAD_RESULT.md` §2/§5, `T2_EVIDENCE_HASHES.txt` `CROSS_VERIFY=ALL_MATCH`) |
| isolated env | `/home/sychan552/.venvs/mlflu_fm` — Python 3.11.13, torch 2.6.0+cu124, chronos-forecasting 2.3.2, timesfm 1.3.0; built by jobs **744574** / **744576** (probe 744533) |
| pilot **744589** `t2_fm_pilot` | `stingy` / `gpu-a100-05` / A100-SXM4-80GB; **PASSED**: all finite, MSE **0.3913**, only warmed-up repeated latency **10.191±0.446 ms** (warm-up 1 / repeat 5), peak VRAM **596 MiB** (28 samples), wall 27.35 s |
| matrix **744607** `t2_fm_matrix` | `stingy` / `gpu-a100-05` / A100-SXM4-80GB; **8/8 cells `ok`**, all finite, **8 real NPZ**, peak VRAM **2608 MiB** (18 samples), wall **18.00 s** |

**8 cells (2 models × 4 L = 24/36/48/60, seed 2021, T=104) — real MSE_7var_z:**
`foundation_chronos` 0.391328494 / 2.207397404 / 1.713535818 / 1.400230721;
`foundation_timesfm` 0.729752533 / 2.654955324 / 2.031110049 / 1.662973370.
(Full precision, NPZ paths + SHA-256: `T2_PILOT_AND_MATRIX.md` §4.)

**STILL blocked / limited (not "all done"):**
- 80-cell (2×4×10 seeds) expansion `NOT_EXECUTED_BY_PROTOCOL` — exact reason: frozen
  zero-shot models have **NO training seed dimension**, so 10 seeds would produce
  **10 identical predictions**; the smallest faithful subset (8 cells) was executed
  instead (`FOUNDATION_MATRIX_REPORT.json`).
- Both executed checkpoints are **UNIVARIATE**; the 7 channels were passed as a
  **batch of 7 independent series** (per-channel independent adapter) which
  **DISCARDS cross-channel dependence** and is **NOT information-set-matched** to the
  multivariate arms; benchmark z-space passed through; TimesFM `freq_indicator=1`,
  `horizon_len=128` sliced to L; **zero-shot, NO training / fine-tuning**.
- Labels `foundation_chronos` / `foundation_timesfm` are a **SEPARATE ROSTER**
  (`FOUNDATION_ROSTER.csv`), **never merged** into the frozen 28-arm family or the
  1120 national panel; no full-1120-panel comparison; Chronos-2 tar downloaded but
  checkpoint NOT executed; TimesFM 3.0 excluded on non-commercial-licence grounds.
- **Latency honesty caveat:** TimesFM `wall_s=0.0` and `0.004/2.483/4.489/6.492` ms
  are loop/slicing timings of ONE shared `tfm.forecast` call, NOT four independent
  forward latencies; Chronos L24 `221.835` ms includes one-time CUDA init; the only
  warm-up+repeated latency is the pilot's `10.191±0.446` ms.

### 5.2 T6 — old "VRAM entirely NOT_MEASURED" superseded for MIFlu only

**Old claim (superseded, kept verbatim in §1 T6 row, §2 item 6 and
`T6_VERDICT.md` §4/§6):** "`peak_vram_mib` NOT_MEASURED for ALL 6 rows; no GPU job
ever started; `subset_only_not_full_1120`". **Superseded for MIFlu only** by the
UPDATE 2026-11-06 section of `v8/T6_VERDICT.md` and `v8/T6_GPU_UPDATE.md`. T6 stays
**`PARTIAL (IMPROVED)`**, NOT `COMPLETED`.

**New verified facts (job 744532 `t6_res_gpu_v8b`, `stingy`/`gpu-a100-05`/
A100-SXM4-80GB, driver 580.167.08):** a **REAL MIFlu forward from an existing
checkpoint** ran inside sbatch; peak VRAM **4816 MiB** (63 `nvidia-smi` samples,
min 16, `status=MEASURED`); forward wall **62.94 s** → new
`real_model_forward_wall_s=62.94` column (MIFlu row only); `[PASS] all requested
cells exported`; `test MSE_7var_z=1.624383`. ONE cell (L=36, seed=2023).

**STILL not measured / unchanged:**
- The other **5 model rows** (NLinear, PatchTST, DeepSeek-R1-Distill-Qwen-1.5B,
  Chronos, TimesFM) remain `NOT_MEASURED` for VRAM ("no GPU measurement job ran for
  this model"); no VRAM invented.
- **Chronos / TimesFM resource rows remain `BLOCKED / NOT_EXECUTED`** in
  `v8/RESOURCE_MEASUREMENTS.csv` (their verbatim "TASK 2 is BLOCKED" reason string
  is the earlier-run record; T2's FINAL results live on the SEPARATE
  `FOUNDATION_ROSTER.csv` and were NOT merged into the T6 resource rows).
- `true_model_forward_latency_ms` remains `NOT_MEASURED` for every row: the 62.94 s
  is the whole-process wall clock for ONE cell's export, NOT a repeated per-forward
  inference latency; NPZ scoring-path latency stays explicitly "NOT a model forward
  pass".
- Every row `scope=subset_only_not_full_1120`; **no full-1120 Pareto claim**; CUDA
  toolkit/runtime version NOT_MEASURED (only driver 580.167.08).
- The 12 raw `*_v8b*` logs were appended (append-only) to `v8/resource_logs/`;
  `SHA256SUMS.txt` original 36 lines byte-identical; updated CSV SHA-256
  `D609D57DCEB5FCBA6656A40A4576D87971F5371AC46AD6589754515C95BFCFCC`.

### 5.3 Old/new separation preserved

- The **OLD 28-arm frozen snapshot** (`02_数字表格/*.csv`) stays byte-identical and
  separately labelled (§1/§2, `V8_SCIENTIFIC_ADDENDUM.md` §0/§G).
- The **LEGACY 5-fold N=3 walk-forward panel** (1020/1020 `ok`, seeds 42/43/44)
  stays a **DIFFERENT scoring population** from the 1120-cell national panel; do NOT
  merge with `CELL_METRICS.csv`. The T2 foundation 8-cell subset is a THIRD,
  separate roster, never merged into either.
- T4 (CDC vintage) stays COMPLETED (corrected 2026-11-06); T1 COMPLETED at
  1020/1020; T3 COMPLETED with the 2-NPZ quarantine caveat; T5 COMPLETED with the
  template class file UNVERIFIED; T7 COMPLETED (the 3 v8 DOCX/PDF need a rebuild —
  §2 item 9); T8 COMPLETED (PRELIMINARY PACKAGING PASS) with the package rebuild
  and `scientific_readiness: NOT_ASSESSED` still outstanding.
- The manuscript is **NOT** submission-ready; a validator PASS is structural only.


---

## 6. V8C final sync (2026-11-06 UTC) — supersedes §5's interim statuses

§5 recorded `T2 -> COMPLETED_WITH_DOCUMENTED_SCOPE (8 cells)` and
`T6 -> PARTIAL (IMPROVED)`; both are now SUPERSEDED by these final states:

| Task | Final status | Evidence |
|---|---|---|
| T2 | **COMPLETED — 80/80 valid cells** | job `744886`; `v8/foundation/T2_FULL80.md`; 80 NPZ; 10 rolling origins; peak VRAM 2608 MiB |
| T3 | **COMPLETED — 388/388 NPZ** | job `744884`; `v8/T3_RESTORE.md`; table `a7d98ad8...e46` |
| T5 | **COMPLETED — provenance applied** | `v8/PAPER_TO_CODE.md`; builder prefers v8 copy; template class file UNVERIFIED |
| T6 | **COMPLETED — 6 models measured** | jobs `744897`/`744899`; `v8/T6_FINAL_SWEEP.md`; CSV sha256 `9574eeff...1117` |
| T7 | **COMPLETED — v8c rebuild** | `v8/docs/V8C_REBUILD_LOG.md` |
| T8 | **COMPLETED — final package** | `v8/packaging/FINAL_HASHES.txt`, `v8/T8_VERDICT.md` |

T1 (1020/1020 WF), T4 (frozen CDC vintage + as-of peaks) and T5's dated
verification record are unchanged. Old 28-arm snapshot, the 1120 national panel
and the LEGACY 5-fold N=3 WF panel remain three separately labelled populations.
Still NOT EXECUTED / UNVERIFIED / NOT_MEASURED: the literal 10-seed expansion,
the official JBHI template class file, isolated single-forward latency for three
models, confirmatory dependence-aware statistics, and any full-1120 Pareto claim.
