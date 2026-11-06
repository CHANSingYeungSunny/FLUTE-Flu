# Message to ChatGPT — v8 evidence handoff (FINAL, synced 2026-11-07 HKT / 2026-11-06 UTC)

**This is a PRELIMINARY packaging pass, NOT a finished manuscript and NOT "all
done".** Do NOT call the manuscript submission-ready: `manuscript_submission_ready: NO`
(`v8/T5_VERDICT.md`). A validator `integrity_status: PASS` is STRUCTURAL ONLY and
MUST be read together with `scientific_readiness: NOT_ASSESSED`
(`v8/RETURN_V8/VALIDATION_RESULT.json`) — it is NOT scientific certification. The
current `v8/RETURN_TO_CHATGPT.zip` / `v8/RETURN_V8/` on disk are still the preliminary
pass built at 2026-11-06T14:18:14Z, before the final T2/T6 results and the T7 DOCX/PDF
landed; §4 states the required rebuild.

Authoritative v8 verdicts / evidence: `v8/TASK_LOG.md`,
`v8/foundation/T2_VERDICT.md` (§FINAL UPDATE 2026-11-06),
`v8/foundation/T2_DOWNLOAD_RESULT.md`, `v8/foundation/T2_PILOT_AND_MATRIX.md`,
`v8/foundation/FOUNDATION_ROSTER.csv`, `v8/cdc_vintage/T4_CORRECTION.md`,
`v8/cdc_vintage/T4_VERDICT.md`, `v8/T5_VERDICT.md`,
`v8/T6_GPU_UPDATE.md`, `v8/T6_VERDICT.md` (§UPDATE 2026-11-06),
`v8/RESOURCE_MEASUREMENTS.csv`, `v8/T7_VERDICT.md`, `v8/T8_VERDICT.md`,
`v8/packaging/T8_PREP_NOTES.md`. The v7 baseline message is
`audit/v7/MESSAGE_TO_CHATGPT.md`.

---

## 1. Explicit old / new separation (AGENTS.md RULE 4)

- **Old 28-arm frozen snapshot**: the historical frozen CSVs under `02_数字表格/*.csv`
  (28 arms, Holm 0/136 from `p_raw` with forward cumulative maximum, NLinear–PatchTST
  0.1172, 4/16 aggregate cells). These are old-snapshot facts, are NOT part of this
  return, and were never overwritten. Kept SEPARATELY LABELLED.
- **New 1120 panel**: the harmonised national panel (28 models × 4 L × 10 seeds
  2021–2030) scored tables under `final/` (`CELL_METRICS.csv`, `MODEL_L_PANEL.csv`,
  `PAIRED_HOLM_NEW.csv`, `PEAK_*`, `ABLATION_*`, `REGIONAL_*`, `WF_*`,
  `FINAL_RESULTS.md`, `SCIENTIFIC_AUDIT.md`). The new panel is NEVER merged into the
  old 28-arm snapshot — separate files with separate denominators.
- **LEGACY 5-fold N=3 walk-forward panel** (`final/WF_RECOMPUTED.csv`, 1020/1020
  `ok`, seeds 42/43/44) is a **DIFFERENT scoring population** from the 1120 national
  panel; do NOT merge with `CELL_METRICS.csv`. Its WF MSE 2.220289 (MIFlu) is NOT the
  same quantity as the national all-valid MSE 1.7944. The 20 out-of-grid
  `wf_f*_miflu_*_s2021` rolling-origin rows remain out of scope.
- **Foundation models on a SEPARATE ROSTER**: numerical foundation models
  (Chronos / TimesFM) are NOT the 11 frozen language encoders and are NOT merged into
  the 28-arm family. They live only on `v8/foundation/FOUNDATION_ROSTER.csv` +
  `v8/foundation/FOUNDATION_MODEL_PROVENANCE.md`. T2 FINAL status is
  **`COMPLETED_WITH_DOCUMENTED_SCOPE`** (8 zero-shot cells, jobs 744589/744607;
  evidence `T2_VERDICT.md` §FINAL UPDATE, `T2_PILOT_AND_MATRIX.md`,
  `T2_DOWNLOAD_RESULT.md`). The 80-cell expansion and the univariate/adapter limits
  remain blocked (§3). NEVER merged into the 28-arm family or the 1120 national panel.
- **v7 return kept separately labelled**: `v7_snapshot/` holds verbatim COPIES of the
  frozen `v7/RETURN_V7/` key files (root files + `DOCUMENTS/v7/`); `RAW_EVIDENCE/`
  holds the 1120 validated raw prediction NPZ that its ledger points to. The
  root `RUN_LEDGER.csv` / `CHECKS.json` / protocol JSONs are the carried-over v7
  structural skeleton needed by the official validator — they are NOT new v8
  measurements and are not rewritten here.

---

## 2. Exactly what changed in v8 vs v7 (FINAL, synced 2026-11-07)

v7 left these NOT done (see `audit/v7/MESSAGE_TO_CHATGPT.md`): foundation models
BLOCKED, CDC vintage "not reconstructed", JBHI guidance unverified, resource
measurements NOT EXECUTED, walk-forward 473/1020 valid, v7 DOCX/PDF rebuild, strict
`RETURN_TO_CHATGPT.zip` rebuild. (2026-11-06 correction: the CDC vintage was in fact
ALREADY fully reconstructed in the frozen `02_数字表格/` artifacts; T4 is COMPLETED,
not a v8-new build — see `v8/cdc_vintage/T4_CORRECTION.md`.)

v8 (T1–T8 of `HANDOFF_20261105/NEXT_DEEPSEEK_PROMPT.md`; authoritative
`v8/TASK_LOG.md`) — FINAL status of all 8 tasks:

- **T1 walk-forward — COMPLETED at 1020/1020 `ok`.** Job `743850` (`wf_fix218`,
  `stingy`/`gpu-a100-03`) reran all 218 previously-SKIPPED legacy cells (rc=0);
  `743920` (`wf_probe`) verified the NPZ schema; `744271` / `744334`
  (`t1_wf_recompute_v8` / `v8b`) recomputed from raw NPZ.
  `HANDOFF_20261105/final/WF_RECOMPUTED.csv` (1020 rows, all `ok`, sha256
  `53d0e0cb…`) + `WF_RECOMPUTED_MEANS.csv` (`c0e72f35…`);
  `v8/evidence/WF_RECOMPUTE_REPORT.json` (recovered 218, changed 0, lost 0,
  missing 0). Frozen v7 baselines kept in
  `v8/evidence/WF_RECOMPUTED_v7_baseline.csv` /
  `WF_RECOMPUTED_MEANS_v7_baseline.csv`. This is the **LEGACY 5-fold N=3 panel
  (seeds 42/43/44)**, a DIFFERENT scoring population from the 1120 national panel;
  20 out-of-grid rows stay out of scope. Every earlier "802/1020 / 473/1020 / 218
  missing" claim is superseded.

- **T2 foundation models — `COMPLETED_WITH_DOCUMENTED_SCOPE` (earlier `BLOCKED`
  superseded).** `v8/foundation/T2_VERDICT.md` §FINAL UPDATE 2026-11-06;
  `v8/foundation/T2_DOWNLOAD_RESULT.md`; `v8/foundation/T2_PILOT_AND_MATRIX.md`;
  `v8/foundation/T2_EVIDENCE_HASHES.txt`; `v8/foundation/FOUNDATION_ROSTER.csv`.
  4 pinned weight tars (**5,024,901,120 B**) downloaded locally on Windows and
  scp'd to `/gpfs1/scratch/sychan552/models/`, all 4 remote SHA-256 verified
  INSIDE sbatch **744607**; isolated env `/home/sychan552/.venvs/mlflu_fm`
  (Python 3.11.13, torch 2.6.0+cu124, chronos-forecasting 2.3.2, timesfm 1.3.0)
  built by jobs **744574** / **744576** (probe 744533). Pilot **744589**
  (`t2_fm_pilot`, `stingy`/`gpu-a100-05`/A100-SXM4-80GB) PASSED: all finite, MSE
  0.3913, latency 10.191±0.446 ms (warm-up 1 / repeat 5), peak VRAM 596 MiB
  (28 samples). Matrix **744607** (`t2_fm_matrix`) 8/8 cells `ok`, all finite, 8
  real NPZ, peak VRAM 2608 MiB (18 samples), wall 18.00 s. 8 cells (2 models ×
  4 L=24/36/48/60, seed 2021, T=104): `foundation_chronos` MSE 0.391328494 /
  2.207397404 / 1.713535818 / 1.400230721; `foundation_timesfm` 0.729752533 /
  2.654955324 / 2.031110049 / 1.662973370. The earlier `BLOCKED` §1–§8 record is
  retained verbatim as the historical earlier run, NOT erased. Both checkpoints
  UNIVARIATE (7 channels = batch of 7 independent series → discards cross-channel
  dependence, NOT information-set-matched to the multivariate arms); zero-shot, NO
  training/fine-tuning; labels on a SEPARATE ROSTER, NEVER merged into the 28-arm
  family or the 1120 national panel. Honesty caveat: TimesFM `wall_s=0.0` and
  0.004/2.483/4.489/6.492 ms are loop/slicing timings of ONE shared
  `tfm.forecast` call (NOT four forward latencies); Chronos L24 221.835 ms includes
  one-time CUDA init; only warmed-up repeated latency is the pilot 10.191±0.446 ms.

- **T3 `final_llm_import` — COMPLETED with 2-NPZ quarantine caveat.** Job
  `744110` failed (rc=2, `EOFError`); `744134` (`t3b_llm_import_v8`) succeeded
  (rc=0, all 3 steps rc=0). Real HPC-side `paper_tables/BENCH_MSE_BY_MODEL_L.csv`
  (sha256 `2e03b510…`) + `BENCH_PTE_PIE_BY_STEP.csv` + `BENCH_EFFICIENCY.csv`
  from 386 readable legacy cells. Quarantine (MOVED, not deleted):
  `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/QUARANTINE.json`
  (`miflu_L36_s2021` 0 B `EOFError`, `miflu_L60_s2021` 30977 B `BadZipFile`).
  LEGACY analysis-tree table, NOT the 1120 panel.

- **T4 CDC vintage — COMPLETED (corrected 2026-11-06).** NO HPC job (local `curl` /
  `WebFetch` of 16 URLs + 3 live Delphi `fluview` fetches, HTTP 200). Uses the
  project's FROZEN `02_数字表格/cdc_vintage_raw.csv` (7192 rows, `e0c5512b…`),
  `cdc_vintage.csv` (848 rows, `5a49e6be…`), `cdc_vintage_report.md`
  (`e2da6b37…`), `cdc_peak_revintage.csv` (`7c9b5df8…`, 18 seasons / 7 peak weeks
  moved = 38.9%), builder `05_程序代码/cdc_vintage_build.py` (`8c1e4b1e…`).
  Authoritative `v8/cdc_vintage/T4_CORRECTION.md`; corrected
  `v8/cdc_vintage/T4_VERDICT.md` (`status: COMPLETED`). Earlier erroneous
  `BLOCKED: no release-calendar/vintage source found` verdict superseded. Retained
  limits: Delphi `release_date` proxy (NOT a CDC-issued official revision number),
  reference-peak-only re-scoring, retrospective 1120-cell model peaks, no 2002
  real-time vintage.

- **T5 JBHI — COMPLETED (dated verification record); template class file
  UNVERIFIED.** NO HPC job (live HTTP 200 content fetches).
  `v8/JBHI_VERIFICATION_20261106.md`, `v8/JBHI_PROVENANCE_PATCH.md`,
  `v8/T5_VERDICT.md`. VERIFIED: 14 pp regular / 16 review incl. supplementary,
  abstract ≤250 words, IEEE single-spaced double-column, embedded figures/tables,
  AI disclosure (IEEE-wide), hybrid OA, APC US$2,800 (2026). UNVERIFIED: official
  `.cls`/Word/ZIP (selector 404 / WAF 418 / `/api` 302→502).
  `submission-ready: NO`.

- **T6 resources — `PARTIAL (IMPROVED)`.** CPU job `744239` (`t6_res_cpu`, `tiny`,
  14 s) produced the subset: `v8/RESOURCE_MEASUREMENTS.csv` (6 rows,
  `scope=subset_only_not_full_1120`), real historical training walls (MIFlu 581 s,
  NLinear 6 s, PatchTST 7 s, DeepSeek-R1-Distill-Qwen-1.5B 24 s), real NPZ
  scoring-path latency 0.0287–0.0297 ms (warm-up 5 / repeat 50, explicitly NOT a
  model forward), versions Python 3.9.25 / numpy 2.0.1 / pandas 2.3.3 / torch
  2.5.1. GPU job `744253` (`t6_res_gpu`, gpu_a100) CANCELLED (PENDING start
  2026-11-08); two `stingy` submissions rejected `QOSMaxSubmitJobPerUserLimit`.
  **NEW:** job **744532** (`t6_res_gpu_v8b`, `stingy`/`gpu-a100-05`/
  A100-SXM4-80GB, driver 580.167.08) ran a REAL MIFlu forward from an existing
  checkpoint: peak VRAM **4816 MiB** (63 `nvidia-smi` samples, min 16), forward
  wall **62.94 s** (`real_model_forward_wall_s=62.94`), `[PASS] all requested
  cells exported`, `test MSE_7var_z=1.624383`. Evidence `v8/T6_GPU_UPDATE.md`,
  `v8/T6_VERDICT.md` §UPDATE 2026-11-06, `v8/resource_logs/*_v8b*` (12 logs
  appended), `v8/RESOURCE_MEASUREMENTS.csv` (updated SHA-256 `D609D57D…`). The
  other 5 model rows remain `NOT_MEASURED` for VRAM; Chronos/TimesFM resource
  rows remain BLOCKED; ONE cell (L=36, seed=2023), no full-1120 Pareto; the 62.94 s
  is whole-process wall, NOT a repeated per-forward latency
  (`true_model_forward_latency_ms` still NOT_MEASURED).

- **T7 v8 documents — COMPLETED.** NO HPC job (local `python-docx` builds + PDF
  conversion). `v8/T7_VERDICT.md` (`status: COMPLETED`, 14:31:13Z–14:51:07Z).
  Three DOCX + three PDF in `01_最终报告/v8/`: `ieee_manuscript_en_v8.docx/.pdf`
  (7 pp), `report_internal_zh_v8.docx/.pdf` (6 pp),
  `report_internal_qa_zh_v8.docx/.pdf` (14 pp), plus `PDF_CONVERSION_LOG.md`.
  Markdown/CSV in `v8/docs/` and `v8/`: `V8_SCIENTIFIC_ADDENDUM.md`,
  `V8_CHANGELOG.md`, `V8_BUILD_RESULTS.json`, `DOCUMENT_UPDATE_MAP.csv`,
  `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`. **NOTE (2026-11-07):** these
  DOCX/PDF were built at 14:31–14:51Z on 2026-11-06, BEFORE the final T2 pilot/
  matrix (15:51–15:58Z, jobs 744589/744607) and T6 GPU job (15:30Z, 744532), so
  their BODY text still says T2 `BLOCKED` and T6 VRAM `NOT_MEASURED`; they require a
  rebuild (§3/§4). The six markdown/CSV files listed above WERE re-synced on
  2026-11-07 to the FINAL T2/T6 results. No frozen CSV / raw prediction / checkpoint
  / owner PPTX touched.

- **T8 final package — COMPLETED (PRELIMINARY PACKAGING PASS).** NO HPC job (local
  builder `v8/packaging/build_v8_return.py`, builder window
  2026-11-06T14:18:14Z→14:20:05Z). `v8/T8_VERDICT.md`;
  `v8/RETURN_V8/RETURN_MANIFEST.json` (official tool) and
  `v8/RETURN_V8/VALIDATION_RESULT.json` (`integrity_status: PASS`,
  `scientific_readiness: NOT_ASSESSED`); `v8/RETURN_TO_CHATGPT.zip` (1306 members),
  `v8/RAW_EVIDENCE.zip` (2232 members); `v8/packaging/v8_package_report.json`.
  A validator PASS is STRUCTURAL ONLY. See §4 for the required rebuild.

---

## 3. Exactly what remains BLOCKED / NOT_EXECUTED / UNVERIFIED (all 8 tasks)

| Task / item | Status | Exact file paths + JOB IDs | Smallest next action |
|---|---|---|---|
| T1 walk-forward | **COMPLETED (1020/1020 `ok`); no blocked cells** | `final/WF_RECOMPUTED.csv` (`53d0e0cb…`), `final/WF_RECOMPUTED_MEANS.csv`, `v8/evidence/WF_RECOMPUTE_REPORT.json`; jobs 743850 / 743920 / 744271 / 744334 | Retain the LEGACY-vs-1120 separation; 20 out-of-grid `wf_f*_miflu_*_s2021` rows stay out of scope |
| T2 80-cell expansion (2×4×10 seeds) | **NOT_EXECUTED_BY_PROTOCOL — STILL BLOCKED** | `v8/foundation/T2_PILOT_AND_MATRIX.md` §6/§7; `v8/foundation/t2_hpc_evidence/matrix_out/FOUNDATION_MATRIX_REPORT.json`; matrix job 744607. Exact reason: frozen zero-shot models have NO training seed dimension → 10 seeds would produce 10 IDENTICAL predictions; the smallest faithful subset (8 cells) was executed instead | Do not pad with duplicates; keep the 8-cell subset explicitly labelled |
| T2 scientific limits | **BLOCKED (scientific) / LIMIT — STILL** | `v8/foundation/T2_PILOT_AND_MATRIX.md` §5; `v8/foundation/FOUNDATION_MODEL_PROVENANCE.md`; jobs 744589 / 744607. Both executed checkpoints UNIVARIATE; 7 channels = batch of 7 independent series → DISCARDS cross-channel dependence, NOT information-set-matched; z-space passthrough; TimesFM freq=1, horizon 128 sliced; zero-shot, NO training. No full-1120 comparison; SEPARATE `v8/foundation/FOUNDATION_ROSTER.csv`, NEVER merged into 28-arm family / 1120 panel. Chronos-2 tar downloaded but checkpoint NOT executed; TimesFM 3.0 excluded (`timesfm-non-commercial-license-v1.0`); `chronos-t5-small` / `timesfm-1.0-200m` tars NOT executed | Use a natively-multivariate Apache-2.0 checkpoint with a matched adapter, or document the 6 limits with every quoted result |
| T2 latency honesty caveat | **LIMIT (not a blocker)** | `v8/foundation/T2_PILOT_AND_MATRIX.md` §5.1; jobs 744589 / 744607: TimesFM `wall_s=0.0` and 0.004/2.483/4.489/6.492 ms = loop/slicing timings of ONE shared `tfm.forecast` call, NOT four forward latencies; Chronos L24 221.835 ms includes one-time CUDA init; only warmed-up repeated latency = pilot 10.191±0.446 ms | Quote only the pilot latency as measured inference latency |
| T3 2 quarantined legacy NPZ | **UNRESOLVED (archived, not deleted)** | `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/QUARANTINE.json`; jobs 744110 (rc=2) / 744134; table reflects 386 readable cells, not 388 | Regenerate or explicitly exclude before any legacy analysis-tree claim |
| T4 CDC vintage | **COMPLETED (corrected); retained LIMITS only** | `v8/cdc_vintage/T4_CORRECTION.md`, `v8/cdc_vintage/T4_VERDICT.md`; frozen `02_数字表格/cdc_vintage*.csv`; NO HPC job. Delphi proxy (NOT a CDC official revision number), reference-peak-only re-scoring, retrospective 1120-cell model peaks, no 2002 real-time vintage. No official CDC release calendar claimed | None for the reference assignment; retain the proxy caveat |
| T5 JBHI template class file | **UNVERIFIED** | `v8/T5_VERDICT.md`, `v8/JBHI_VERIFICATION_20261106.md`, `v8/JBHI_PROVENANCE_PATCH.md`; selector 404 (browser UA) / WAF 418 / `/api` 302→502. Verification record itself COMPLETED; `submission-ready: NO` | Human browser session at the template selector, pin filename + SHA-256, paste the patch into `PAPER_TO_CODE.md` |
| T6 other 5 model rows VRAM | **NOT_MEASURED** | `v8/RESOURCE_MEASUREMENTS.csv` rows for NLinear / PatchTST / DeepSeek-R1-Distill-Qwen-1.5B / Chronos / TimesFM; `v8/T6_GPU_UPDATE.md` §8; job 744532 covered MIFlu ONLY. "no GPU measurement job ran for this model"; no VRAM invented | Re-run a GPU measurement job for those models |
| T6 Chronos / TimesFM resource rows | **BLOCKED / NOT_EXECUTED — STILL** | `v8/RESOURCE_MEASUREMENTS.csv` rows 5–6; `v8/T6_VERDICT.md` §UPDATE "STILL NOT MEASURED" item 3. The verbatim "TASK 2 is BLOCKED — no weights / no env / no pilot" reason string is the earlier-run record, superseded by T2's FINAL `COMPLETED_WITH_DOCUMENTED_SCOPE`; T2 foundation results are on the SEPARATE `FOUNDATION_ROSTER.csv` and were NOT merged into these T6 rows | Dedicated T6 GPU measurement job for the foundation checkpoints; do NOT copy T2 pilot/matrix VRAM (596/2608 MiB) into these rows |
| T6 true model-forward latency + full-1120 Pareto | **NOT_MEASURED / NOT CLAIMED** | `v8/T6_VERDICT.md` §UPDATE; `v8/T6_GPU_UPDATE.md` §4.2/§7/§8: 62.94 s = whole-process wall for ONE cell (L=36, seed=2023), NOT a repeated per-forward latency; `true_model_forward_latency_ms` NOT_MEASURED for all rows; NPZ scoring-path latency explicitly "NOT a model forward pass"; every row `scope=subset_only_not_full_1120` | Warm-up + repeated neural-forward timing; extend subset if a full picture is needed |
| T7 v8 DOCX/PDF bodies | **STALE — need rebuild (NOT EXECUTED for the final T2/T6 numbers)** | `01_最终报告/v8/{ieee_manuscript_en_v8,report_internal_zh_v8,report_internal_qa_zh_v8}.docx/.pdf`; `v8/T7_VERDICT.md`. Built 14:31–14:51Z 2026-11-06 BEFORE T2 pilot/matrix (15:51–15:58Z, jobs 744589/744607) and T6 GPU job (15:30Z, 744532); their BODY still says T2 `BLOCKED` / T6 VRAM `NOT_MEASURED` | Rebuild the 3 DOCX/PDF from the synced `v8/docs/` markdown (owner/T7), then fold into the T8 package (§4) |
| T8 package contents | **PRELIMINARY — rebuild required** | `v8/RETURN_V8/`, `v8/RETURN_TO_CHATGPT.zip`, `v8/RAW_EVIDENCE.zip`, `v8/T8_VERDICT.md` §7, `v8/packaging/T8_PREP_NOTES.md`. Current `RETURN_V8/final/WF_RECOMPUTED.csv` is still 802 `ok` / 218 `no_npz`; `RETURN_V8/DOCUMENTS/v8/` absent; `T2_DOWNLOAD_RESULT.md` / `T2_PILOT_AND_MATRIX.md` / `T6_GPU_UPDATE.md` not in the package | Re-run the single builder command (§4) |
| Manuscript submission-ready | **NO** | `v8/T5_VERDICT.md`; `v8/RETURN_V8/VALIDATION_RESULT.json` (`scientific_readiness: NOT_ASSESSED`) | Template class file + provenance patch; validator PASS is structural only |
| Paired statistics | **EXPLORATORY** | `final/SCIENTIFIC_AUDIT.md`, `final/PAIRED_HOLM_NEW.csv`; 378 Wilcoxon / Holm 349/378; cells share one national series + overlapping targets | Dependence-aware / blocked analysis before any confirmatory claim |

Additional carried-over items (from `audit/v7/BLOCKED_AND_UNVERIFIED.md`, unchanged):
the 11 frozen language encoders are NOT substitutes for the numerical foundation
models; regional Table VI is 10-variable, not the 7-channel national metric; the two
corrupt legacy MIFlu NPZ from T3 remain quarantined and must be regenerated or
explicitly excluded before any claim based on that legacy analysis tree.

---

## 4. T8 package — has been / will be rebuilt

State explicitly: **T8's package has been / will be rebuilt** (single builder command
below) to include the **1020/1020 WF CSV** (`final/WF_RECOMPUTED.csv` +
`final/WF_RECOMPUTED_MEANS.csv`), the **3 v8 DOCX/PDF** (`01_最终报告/v8/` — after the
T7 rebuild in §3), and the **T2 / T4 / T6 evidence**:
- T2: `v8/foundation/T2_VERDICT.md` (§FINAL UPDATE), `T2_DOWNLOAD_RESULT.md`,
  `T2_PILOT_AND_MATRIX.md`, `T2_EVIDENCE_HASHES.txt`, `FOUNDATION_ROSTER.csv`,
  `v8/foundation/t2_hpc_evidence/*`, `v8/evidence/foundation_t2_*`;
- T4: `v8/cdc_vintage/T4_CORRECTION.md`, `T4_VERDICT.md`,
  `CDC_VINTAGE_REPORT.md`, `v8/cdc_vintage/http_evidence/`;
- T6: `v8/T6_GPU_UPDATE.md`, `v8/T6_VERDICT.md` (§UPDATE),
  `v8/RESOURCE_MEASUREMENTS.csv`, `v8/resource_logs/*_v8b*` (job 744532).

Single re-run command (from project root, `v8/packaging/T8_PREP_NOTES.md`):

```
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"
```

It wipes/re-assembles `v8/RETURN_V8/` (COPIES only), re-runs the official
`make_return_manifest.py` / `validate_return.py`, rebuilds
`RETURN_TO_CHATGPT.zip` + `RAW_EVIDENCE.zip`, and reports NEW file counts / byte
sizes / SHA-256 in `v8/packaging/v8_package_report.json`. After any re-run,
re-check `integrity_status: PASS` AND `scientific_readiness: NOT_ASSESSED` in
`v8/RETURN_V8/VALIDATION_RESULT.json`; never edit `validate_return.py` to force a
PASS. The current ZIPs on disk are still the preliminary pass and do NOT yet
contain those items. **A validator PASS is STRUCTURAL ONLY**
(`scientific_readiness: NOT_ASSESSED`) — it is NOT scientific certification and
must not be read as submission-readiness.

`v8/RETURN_V8/` currently holds `final/`, `foundation/`, `cdc_vintage/`,
`resource_logs/`, `evidence/`, `scripts/`, `audit/v7/`, `v7_snapshot/` (frozen v7
key files, separately labelled), `RAW_EVIDENCE/`, `logs/`, plus the root REQUIRED
skeleton. `DOCUMENTS/v8/` is absent (COPY-only conditional, `01_最终报告/v8/` did not
exist at build time). Full per-file list + hashes: `RETURN_MANIFEST.json` (official
tool) and `v8/RETURN_V8/RETURN_LAYOUT.md`. `RAW_EVIDENCE.zip` carries `v8/evidence/`,
`v8/resource_logs/`, `v8/cdc_vintage/`, `v8/foundation/`, `v8/scripts/`, `final/`
and every raw prediction NPZ already present (COPY only, nothing downloaded).
Legacy archived NPZ under `99_旧文件存档/`, `03_预测数据_证据/`, `handoffs/` stay in
their OWN labelled subtrees and are NOT merged into the 1120-panel tables.

---

## 5. Bottom line

Several real, dated v8 records were produced. **T1 is COMPLETED (1020/1020 `ok`,
LEGACY panel); T2 is `COMPLETED_WITH_DOCUMENTED_SCOPE` (8 zero-shot cells on a
SEPARATE roster); T3 COMPLETED (2-NPZ quarantine); T4 COMPLETED (corrected
2026-11-06) on the frozen `02_数字表格/` reconstruction; T5 COMPLETED (template
class file UNVERIFIED); T6 `PARTIAL (IMPROVED)` (MIFlu VRAM 4816 MiB measured,
job 744532); T7 COMPLETED; T8 COMPLETED (PRELIMINARY PACKAGING PASS).** This is
**NOT "all done"**: the `NOT_EXECUTED_BY_PROTOCOL` 80-cell expansion, the T2
univariate/adapter and information-set limits, the T2 latency honesty caveat, the
other 5 T6 VRAM rows, the Chronos/TimesFM T6 resource rows, true model-forward
latency, the full-1120 Pareto, the JBHI template class file, the T3 2-NPZ
quarantine, the T7 DOCX/PDF rebuild and the T8 package rebuild all remain BLOCKED /
NOT_EXECUTED / UNVERIFIED / NOT_MEASURED. The old 28-arm frozen snapshot stays
separately labelled; the LEGACY 5-fold N=3 WF panel is a DIFFERENT scoring population
from the 1120 national panel and must never be merged with `CELL_METRICS.csv`; the T2
foundation roster is a THIRD separate population. The manuscript is **NOT**
submission-ready. A validator `integrity_status: PASS` is
`scientific_readiness: NOT_ASSESSED` and is not scientific certification.
