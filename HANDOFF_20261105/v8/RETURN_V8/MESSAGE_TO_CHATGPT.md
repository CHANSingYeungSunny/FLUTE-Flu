# Message to ChatGPT — v8 final handoff (2026-11-07 HKT / 2026-11-06 UTC, FINAL T2/T3/T5/T6 sync)

Authoritative new-results note: `v8/docs/V8_SCIENTIFIC_ADDENDUM.md`.
Execution log: `v8/TASK_LOG.md`. Full audit: `v8/SCIENTIFIC_AUDIT.md`; blocked items:
`v8/BLOCKED_AND_UNVERIFIED.md`; document map: `v8/DOCUMENT_UPDATE_MAP.csv`.
Final task records: `v8/foundation/T2_FULL80.md`, `v8/T3_RESTORE.md`,
`v8/PAPER_TO_CODE.md`, `v8/T6_FINAL_SWEEP.md`, `v8/T6_VERDICT.md` (FINAL UPDATE),
`v8/foundation/T2_VERDICT.md` (FINAL UPDATE, now SUPERSEDED by `T2_FULL80.md`),
`v8/RESOURCE_MEASUREMENTS.csv`.

**Old / new separation (hard rule).** The frozen historical 28-arm snapshot
(`02_数字表格/*.csv`; Holm 0/136 from `p_raw` with forward cumulative maximum;
NLinear–PatchTST 0.1172; 4/16 aggregate cells) is an OLD-SNAPSHOT fact and is
NOT replaced. The NEW 1120-cell national panel (28 models x 4 L x 10 seeds
2021–2030) is a separate panel. The LEGACY 5-fold N=3 walk-forward panel
(seeds 42/43/44, 1020/1020 `ok`) is a THIRD, distinct scoring population and must
never be merged with the 1120 national panel. The `final_llm_import` bench table is
a fourth, LEGACY analysis-tree population (now 388/388 cells). The two numerical
foundation models live on a SEPARATE ROSTER (80 cells via 10 forecast origins),
never merged into the 28-arm family. Do NOT merge, average or compare these
populations naively.

## 1. Exactly what changed in v8 vs v7 — FINAL 8-task table

| Task | Final status | What changed (with evidence) |
|---|---|---|
| T1 Walk-forward | **COMPLETED** | `743850` (stingy / gpu-a100-03) reran 218/218 SKIPPED legacy cells rc=0; `743920` wf_probe, `744271` wf_recompute, `744334` recomputed from raw NPZ: **1020/1020 `ok`**, 218 recovered, 0 existing values changed, 0 lost. `final/WF_RECOMPUTED.csv` sha256 `53d0e0cb36e726db46c29066101be316bbf9e0de7ea1a228bf84ba7f885ef80b`; means `c0e72f35f29d4df32762b9c0a03f69df576405ead495e91a43320dc0774d5813`. Full-panel means (n=60 each): MIFlu 2.220289 < PatchTST 3.039638 < NLinear 3.211592. LEGACY 5-fold N=3 panel, NOT the 1120 national panel. |
| T2 Chronos / TimesFM | **COMPLETED — FULLY COMPLETED with 80 valid cells** (via 10 DISTINCT forecast origins) | Earlier "8 cells only / 80-cell expansion NOT EXECUTED" is **SUPERSEDED**. Job `744886` `t2_fm_full80` (stingy / A100-SXM4-80GB) produced `FOUNDATION_80_CELLS.csv` with **80/80 `ok`, all finite, 80 real prediction NPZ** under `v8/foundation/t2_hpc_evidence/full80_out/`. Matrix = 2 models x 4 L (24/36/48/60) x 10 replicates. Both checkpoints are FROZEN ZERO-SHOT (no training seed dimension, so 10 seeds would give 10 identical predictions), so the 10 replicates are **10 distinct forecast origins (rows 773–782)**, each with its own context and target; `seed_semantics=NOT_APPLICABLE`, `replicate_kind=rolling_origin`. The literal 10-seed expansion remains `NOT_EXECUTED_BY_PROTOCOL` with that exact reason. Peak VRAM **2608 MiB** (51 nvidia-smi samples), wall **50.71 s**, Chronos latency **10.229 ± 1.074 ms** (warm-up 1 / repeat 10), TimesFM **50.906 ± 4.459 ms** (warm-up 1 / repeat 5). Labels `foundation_chronos` / `foundation_timesfm` are a SEPARATE ROSTER, never merged into the 28-arm family. Both checkpoints UNIVARIATE; 7 channels passed as a batch of 7 independent series (per-channel adapter DISCARDING cross-channel dependence, NOT information-set matched); each model applies its own internal scaling; zero-shot, no training. TimesFM `cell_wall_ms` is one shared forecast call per origin — the 4 L slices are NOT four independent forwards. Record: `v8/foundation/T2_FULL80.md`. |
| T3 `final_llm_import` | **COMPLETED — FULLY RESTORED, 388/388** | Earlier "2 quarantined NPZ / 386 readable cells" is **SUPERSEDED / RESOLVED**. Job `744884` `t3_restore_final` (tiny) COPY-restored the two corrupt NPZ from their existing valid 7-channel copies (`author_runs/L36_all7/pred_miflu_L36_seed2021.npz` → `expanded_runs/miflu_L36_s2021/pred_miflu_L36_s2021.npz`, same for L60). Validation inside sbatch: **388/388 NPZ readable, 0 unreadable, `(W,7,L)`, all finite**. Re-ran the exact `final_llm_import` task: all 3 scripts rc=0, `ok=true`, `BENCH_MSE_BY_MODEL_L.csv` changed from `2e03b5109db03cfd4e1b9e89bd8e6069468fd4f7cd3671b367f7f632a0b6be29` to **`a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`** (69 lines). The two original corrupt files remain archived (not deleted) in `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/`. Record: `v8/T3_RESTORE.md`. LEGACY analysis-tree table, not the 1120 panel. |
| T4 CDC vintage | **COMPLETED (corrected 2026-11-06)** | An earlier verdict wrongly said BLOCKED because it did not inspect the project's own `02_数字表格/`. The project ALREADY had `cdc_vintage.csv` (848 epiweeks), `cdc_vintage_raw.csv` (7192 rows), `cdc_vintage_report.md` and `05_程序代码/cdc_vintage_build.py`, built from the Delphi Epidata `fluview` endpoint, with as-of season-peak re-scoring (18 seasons, 7 peak weeks move = 38.9%). `v8/cdc_vintage/T4_CORRECTION.md` records the correction. Retained limits: Delphi `release_date` is a proxy, NOT a CDC-issued official revision number; only the REFERENCE peak assignment is re-scored; model-panel peak metrics remain retrospective; no 2002 real-time vintage. |
| T5 JBHI | **COMPLETED — step 4 DONE** (official template class file UNVERIFIED) | **T5 step 4 is now DONE**: `v8/PAPER_TO_CODE.md` was created with the dated JBHI guidance verification applied, and `v8/packaging/build_v8_return.py` was patched so `RETURN_V8/PAPER_TO_CODE.md` prefers this v8 copy over the frozen v7 skeleton. The v7 original stays byte-identical. `v8/JBHI_PROVENANCE_PATCH.md` is now marked applied (the earlier "patch not applied / must be pasted by the owner" note is SUPERSEDED). The official template class file itself remains UNVERIFIED (selector 404 / WAF 418 / API 302→502). Dated verification record: 14 pages incl. supplementary / 16 review, abstract ≤250 words, single-spaced double-column, embedded figures/tables, AI-use disclosure (IEEE-wide policy), APC US$2,800 for 2026, page charges $110/$250/$350. `submission-ready: NO`. |
| T6 Resources | **COMPLETED for all 6 representative models** | Earlier "PARTIAL (IMPROVED) / five VRAM rows NOT_MEASURED / Chronos–TimesFM resource rows BLOCKED" is **SUPERSEDED**. Jobs `744897` `t6_final_sweep` + `744899` `t6_miflu_fix` (stingy / A100-SXM4-80GB, driver 580.167.08) measured peak VRAM for MIFlu **4816 MiB** (46 + 63 samples), NLinear **558** (36), PatchTST **720** (7), **GPT-2 frozen encoder 1070** (11), Chronos **596** (6), TimesFM **2594** (11). Warm-up+repeated REAL model-forward latencies: GPT-2 **6.98 ± 0.097 ms** (1/10), Chronos **9.854 ± 0.337 ms** (1/20), TimesFM **48.273 ± 3.531 ms** (1/10). Full-job walls: MIFlu real 7-channel cell export **62.94 s**, NLinear 20-epoch training+export **35.73 s**, PatchTST **6.86 s**. MIFlu/NLinear/PatchTST isolated single-forward latency remains explicitly `NOT_MEASURED` (measured quantity was a full cell export / training job); old NPZ scoring-path numbers (0.0287–0.0297 ms) moved to `npz_scoring_path_latency_ms_*` columns and labelled NOT a model forward. Representative frozen encoder measured is GPT-2 from the local HF cache; the earlier DeepSeek-R1-Distill-Qwen-1.5B 24 s queue-log wall belongs to a DIFFERENT encoder and is retained only as context. `RESOURCE_MEASUREMENTS.csv` sha256 `9574eeff6f0e39ddba6488b2e8fe8ef09b763c90fdd27223d7960b8f886b1117`. All rows `scope=subset_only_not_full_1120`; NO full-1120 Pareto claim. Record: `v8/T6_FINAL_SWEEP.md`. |
| T7 v8 documents | **COMPLETED** | English manuscript body, Chinese internal report and Q&A were rebuilt once (v8b) with the earlier T2/T4/T6 results; old claims explicitly marked SUPERSEDED, Q01–Q25 preserved. PDF page counts 9 / 9 / 15, all conversions rc=0. `v8/docs/V8B_REBUILD_LOG.md`. NOTE: the DOCX/PDF bodies predate the FINAL T2/T3/T5/T6 results above and would need another rebuild to quote them; they are not called final. |
| T8 Final package | **COMPLETED (packaging pass)** | Validator `PASS` + `scientific_readiness: NOT_ASSESSED` (structural only). The current `RETURN_V8/` / ZIPs are the pass built before the FINAL T2/T3/T5/T6 results landed; **the package will be rebuilt once more by the main agent** after these audit/document files are synced (§4). No "all done" claim. |

Also corrected: the earlier claim "walk-forward partial / 802 of 1020" → 1020/1020;
"Table VI 51/53" → 53/53; "NLinear K&S champion 4/16" → MIFlu 252 / PatchTST 215 /
NLinear 57 of 1680 step rows; "monotonic depth trend" → non-monotonic (K4 1.4989 best,
K12 1.7604 worst). Paired Wilcoxon/Holm (349/378) remains EXPLORATORY.

## 2. Exactly what remains BLOCKED / NOT EXECUTED / UNVERIFIED

1. **Literal 10-seed (rather than 10-origin) foundation expansion — `NOT_EXECUTED_BY_PROTOCOL`.**
   Exact reason: "no training seed dimension in a frozen zero-shot model; 10 seeds
   would produce 10 identical predictions"; `seed_semantics=NOT_APPLICABLE`.
   The **80 cells ARE now done** as `replicate_kind=rolling_origin` (10 distinct
   forecast origins, rows 773–782, each with its own context and target). Also
   retained: no multivariate-native checkpoint (Chronos-2 / TimesFM-3.0); both
   executed checkpoints UNIVARIATE; the 7 channels were forecast as a batch of 7
   independent series, which DISCARDS cross-channel dependence and is NOT
   information-set-matched to the multivariate arms; each model applies its own
   internal scaling; no z-space de-standardisation; zero-shot, no training; no
   full-1120 comparison; no merge into the 28-arm family.
2. **T5 official JBHI template class file (`.cls` / Word / ZIP): UNVERIFIED**
   (selector 404 / WAF 418 / API 302→502). Step 4 provenance patch is applied, but
   no template class file was obtained; `submission-ready: NO`.
3. **MIFlu / NLinear / PatchTST isolated warm-up+repeated single-forward latency:
   `NOT_MEASURED`.** The measured quantity was a real full 7-channel cell export
   (62.94 s) / 20-epoch training+export job (35.73 s / 6.86 s), NOT an isolated
   neural forward. The old NPZ scoring-path numbers (0.0287–0.0297 ms) were moved to
   `npz_scoring_path_latency_ms_*` and labelled NOT a model forward. All resource rows
   keep `scope=subset_only_not_full_1120`; NO full-1120 Pareto claim.
4. **Confirmatory dependence-aware statistics: not done.** Paired inference
   (Wilcoxon/Holm 349/378, seed-cluster bootstrap 359/378 95% CIs excluding zero)
   remains EXPLORATORY: cells share one national series and overlapping targets.
5. **Model-panel peak metrics remain retrospective.** Delphi `release_date` / vintage
   is a reproducible PROXY, not CDC-issued official revision ids; no official CDC
   release calendar; 2002 weeks have no real-time vintage; no real-time/clinical claim.
6. **The manuscript is NOT submission-ready.** A structural validator `PASS` is
   `scientific_readiness: NOT_ASSESSED`, not scientific certification.

Documentation / package sync (not scientific blockers): the 3 v8 DOCX/PDF bodies
predate the FINAL T2/T3/T5/T6 results (§1 T7), and the T8 package will be rebuilt
once more by the main agent (§4). No "all done" claim is made.

## 3. HPC job IDs (all COMPLETED; no training, download, HPC job or SSH was run for this sync)

`743850` (T1 rerun of 218 SKIPPED cells), `743920` (T1 wf_probe),
`744110` (T3 first `final_llm_import`, rc=2 `EOFError`),
`744134` (T3 `final_llm_import` after quarantine, `ok=true`),
`744271` (T1 wf_recompute), `744334` (T1 wf_recompute_v8b, 1020/1020),
`744532` (T6 first real MIFlu GPU forward, 4816 MiB),
`744533` (T2 env reachability probe), `744574` (T2 venv install),
`744576` (T2 env finish), `744589` (T2 1-cell pilot),
`744607` (T2 8-cell matrix + remote tar SHA verification),
`744884` (T3 restore of 2 NPZ + exact `final_llm_import` re-run),
`744886` (T2 full80 80-cell matrix via 10 origins),
`744897` (T6 final sweep, 6 models), `744899` (T6 MIFlu fix).

All model work ran via `sbatch` on compute nodes; nothing heavy on the login node.

## 4. FINAL package (authoritative)

ZIP byte sizes and SHA-256 are in `v8/packaging/FINAL_HASHES.txt`
(and `v8/packaging/v8_package_report.json`). **They are kept OUTSIDE `RETURN_V8/`
deliberately**: the package mirrors its own documentation, so editing any mirrored
document changes the two ZIP SHA-256 values on the next rebuild. Therefore **no ZIP
hash is hard-coded in this message** — always read the report, never a hash copied
into a chat message.

The current `RETURN_V8/` and the two ZIPs are the packaging pass built before the
FINAL T2/T3/T5/T6 results landed. **The package will be rebuilt once more by the main
agent** after the 6 audit/document files are synced; the ZIP hashes will change on
that rebuild. Re-run command (owner: main agent):

```
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"
```

Validator `PASS` is structural only (`scientific_readiness: NOT_ASSESSED`). Details:
`v8/T8_VERDICT.md`, `v8/packaging/T8_PREP_NOTES.md`. The manuscript is **not**
submission-ready.
