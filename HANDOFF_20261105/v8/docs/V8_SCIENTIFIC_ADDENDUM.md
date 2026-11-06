# V8 scientific addendum — final v8 verified state (synced 2026-11-07 HKT / 2026-11-06 UTC)

**Sync 2026-11-07.** This addendum has been re-synced with the FINAL T2
(`COMPLETED_WITH_DOCUMENTED_SCOPE`) and T6 (`PARTIAL (IMPROVED)`) results. The
earlier BLOCKED T2 section (§B) and the earlier "VRAM NOT_MEASURED for all rows"
T6 section (§F) are **retained verbatim as the historical earlier-run record, NOT
erased**, and are each explicitly **SUPERSEDED** by new §B.1 / §F.1 that state which
old claim is superseded. The `NOT_EXECUTED_BY_PROTOCOL` 80-cell item REMAINS blocked.
No training, download or HPC job was re-run for this sync. Nothing here calls the
manuscript submission-ready.

**Scope.** This is the TASK 7 document of `HANDOFF_20261105/NEXT_DEEPSEEK_PROMPT.md`.
It records the **final v8 status of T1–T8** using ONLY verified results. It supersedes
the *execution-status* claims in `final/FINAL_RESULTS.md`, `final/SCIENTIFIC_AUDIT.md`,
`v7/V7_SCIENTIFIC_ADDENDUM.md` and `v7/BLOCKED_AND_UNVERIFIED.md`. It does **not**
overwrite any frozen CSV, raw prediction, checkpoint or owner-edited PPTX
(`AGENTS.md` RULE 4). All numbers below were re-checked against the on-disk files on
2026-11-06 (see §I evidence index). A validator `PASS` is structural only; nothing here
calls the manuscript submission-ready.

**Provenance rule (RULE 4).** Historical frozen CSVs in `02_数字表格/` are
**old-snapshot facts** and are kept byte-identical. The new 1120-cell national panel,
the legacy walk-forward panel, the legacy analysis-tree table, the frozen CDC ILINet
vintage reconstruction (`02_数字表格/cdc_vintage*.csv`, a Delphi proxy; TASK 4 now
COMPLETED — corrected 2026-11-06) and the foundation roster are **separate scoring
populations**. They must NOT be merged, averaged or compared naively.

---

## 0. V8 — old snapshot vs new panels (explicit separation)

Three distinct populations coexist. Confusing them is the single largest
scientific-provenance risk in this project.

| Label | Population | Protocol | Where it lives | Status in v8 |
|---|---|---|---|---|
| **OLD** — frozen 28-arm snapshot | 28 arms, historical Holm/K&S/aggregate tables | historical rev-9.2 scoring; Holm 0/136 from `p_raw` with forward cumulative maximum; NLinear–PatchTST 0.1172; 4/16 aggregate cells; old NLinear K&S champion | `02_数字表格/*.csv` (FROZEN, byte-identical) | intact, **labelled old**, never overwritten |
| **NEW** — 1120-cell national common panel | 28 models × 4 lengths × 10 seeds (2021–2030) = 1120 cells | T=104, seven-channel z-space, all-valid + crop panels | `HANDOFF_20261105/final/CELL_METRICS.csv` and friends | COMPLETE; leading order MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782 (all-valid) |
| **LEGACY** — 5-fold N=3 walk-forward panel | 5 folds × 204 cells = 1020 cells, 17 models, seeds 42/43/44 | legacy rolling-origin, `mse = mean((pred-target)^2)` in standardized z-space | `HANDOFF_20261105/final/WF_RECOMPUTED.csv` | **1020/1020 `ok`** (v8 T1 complete); a DIFFERENT scoring population from `CELL_METRICS.csv` |
| **LEGACY** — `final_llm_import` bench table | 386 readable legacy cells **[SUPERSEDED V8C: now 388/388]** | legacy analysis-tree `analysis_expanded.py` | HPC `paper_tables/BENCH_MSE_BY_MODEL_L.csv` | real table, **legacy**, not the 1120 panel |
| **FROZEN** — CDC ILINet vintage (Delphi proxy) | 7192 `(epiweek, issue)` rows / 848 epiweek summaries / 18 re-scored seasons | Delphi Epidata fluview `issue` proxy; builder `05_程序代码/cdc_vintage_build.py` | `02_数字表格/cdc_vintage_raw.csv`, `cdc_vintage.csv`, `cdc_vintage_report.md`, `cdc_peak_revintage.csv` | **COMPLETED** (corrected 2026-11-06); earlier `PARTIAL/BLOCKED` verdict erroneous — see `T4_CORRECTION.md` |
| **SEPARATE ROSTER** — numerical foundation models | 8 pinned candidate rows; 2 checkpoints executed (`PILOT_AND_4L_COMPLETED`), 8 zero-shot cells | frozen zero-shot, 2 models × 4 L (24/36/48/60), seed 2021, T=104; univariate per-channel-independent adapter | `v8/foundation/FOUNDATION_ROSTER.csv`, `T2_PILOT_AND_MATRIX.md`, `T2_DOWNLOAD_RESULT.md` | **T2 `COMPLETED_WITH_DOCUMENTED_SCOPE`** (jobs 744574/744576/744589/744607); 80-cell expansion `NOT_EXECUTED_BY_PROTOCOL`; NEVER merged into the 28-arm family or the 1120 national panel; no 1120-panel comparison |
| **SUBSET** — T6 resource measurements | 6 model rows, 1 representative cell each (MIFlu L=36/s2023 GPU forward) | `nvidia-smi` sampling + `/usr/bin/time -v` + NPZ scoring-path latency | `v8/RESOURCE_MEASUREMENTS.csv`, `v8/resource_logs/` | **PARTIAL (IMPROVED)**: MIFlu peak VRAM 4816 MiB measured (job 744532); other 5 rows NOT_MEASURED; Chronos/TimesFM resource rows BLOCKED; `scope=subset_only_not_full_1120`, no full-1120 Pareto |

**Do NOT merge or compare naively:** the legacy WF panel (seeds 42/43/44, 5 folds)
and the 1120 national panel (seeds 2021–2030, 10 seeds) have different scoring
populations, different seed sets and different window/lead conventions. A WF MSE of
2.220289 for MIFlu is NOT the same quantity as the national all-valid MSE of 1.7944.
The 20 out-of-grid `wf_f*_miflu_*_s2021` rolling-origin rows remain explicitly
**out of scope** and were not run or counted.

---

## A. T1 — WALK-FORWARD: now COMPLETE (verified 1020/1020)

Job `743850` (`stingy`, `gpu-a100-03`) reran all **218 previously-SKIPPED legacy
cells** with `rc=0`; job `744334` recomputed from raw NPZ via
`v8/scripts/wf_recompute.py`. Baseline copies of the old partial result are preserved
in `v8/evidence/WF_RECOMPUTED_v7_baseline.csv` and
`WF_RECOMPUTED_MEANS_v7_baseline.csv`.

- `HANDOFF_20261105/final/WF_RECOMPUTED.csv` — **1020 / 1020 `ok`**, sha256
  `53d0e0cb36e726db46c29066101be316bbf9e0de7ea1a228bf84ba7f885ef80b`.
- `HANDOFF_20261105/final/WF_RECOMPUTED_MEANS.csv` — sha256
  `c0e72f35f29d4df32762b9c0a03f69df576405ead495e91a43320dc0774d5813`.
- Baseline diff (`v8/evidence/WF_RECOMPUTE_REPORT.json`, independently reproduced):
  `recovered_218_count=218`, `changed_existing_ok_values=0`, `lost_existing_ok=0`,
  `still_missing=0`. **No existing `ok` value was altered; the 218 were recovered, not
  invented.**
- Grid: **5 folds × 204 cells each = 1020**; 17 models, **n=60 cells per model**.

**New full-panel per-model means (n=60 each), recomputed from the raw 1020 rows:**

| Model | n | mean MSE | Model | n | mean MSE |
|---|---:|---:|---|---:|---:|
| miflu | 60 | 2.220289 | calf_llm | 60 | 4.391592 |
| patchtst | 60 | 3.039638 | svr | 60 | 4.412095 |
| nlinear | 60 | 3.211592 | decision_tree | 60 | 4.514915 |
| dnn | 60 | 3.648969 | cnn | 60 | 4.515521 |
| gradient_boosting | 60 | 3.915091 | lstm | 60 | 4.655853 |
| timecma_llm | 60 | 3.924265 | gru | 60 | 4.742699 |
| random_forest | 60 | 3.925170 | rnn | 60 | 4.785940 |
| knn | 60 | 3.967265 | qwen_time_llm | 60 | 4.826157 |
| itransformer | 60 | 3.977386 | | | |

**CRITICAL PROVENANCE.** This is the **LEGACY 5-fold N=3 walk-forward panel**
(seeds 42/43/44), **NOT** the new 28-arm national 10-seed (2021–2030) panel. The 20
out-of-grid `wf_f*_miflu_*_s2021` rolling-origin rows remain out of scope. It is a
different scoring population from `CELL_METRICS.csv`; do NOT merge or compare naively
with the 1120 national panel.

**Superseded v7 claims:** "walk-forward 802/1020 valid, 218 no NPZ", "218 have no
NPZ", "walk-forward is partial/invalid", "473/1020 valid" — all downgraded to the
verified v8 state above.

---

## B. T2 — FOUNDATION MODELS: BLOCKED (no weights, no env, no pilot, no 80-cell matrix)

> **[SUPERSEDED 2026-11-06 V8C — see the "V8C FINAL UPDATE" section at the end.]**
> T2 is now COMPLETED with **80/80 valid cells** (job 744886). This section is the
> historical 2026-11-06 interim record, retained verbatim, NOT the current status.

> **SUPERSEDED (synced 2026-11-07 HKT / 2026-11-06 UTC).** The `status: BLOCKED`
> text in this section is the **earlier-run record** (2026-11-06T13:21:18Z–
> 13:39:51Z, metadata-only probes, no HPC) and is retained verbatim as the historical
> record, NOT erased. It is **SUPERSEDED** by §B.1 below: T2 FINAL status is
> `COMPLETED_WITH_DOCUMENTED_SCOPE` (4 pinned tars + scp + remote SHA verification,
> isolated env, pilot 744589, matrix 744607 = 8 faithful zero-shot cells). The
> `NOT_EXECUTED_BY_PROTOCOL` 80-cell item, the univariate/adapter limits and the
> separate-roster rule REMAIN in force.

`v8/foundation/T2_VERDICT.md` records `status: BLOCKED` **[SUPERSEDED V8C — the FINAL UPDATE at the end of that file records 80/80 valid cells]**. All commands exited 0 and
no network failure occurred; the block is a **documented missing-input condition**,
not a fabricated error. Exact missing inputs and pinned repo/revision/licence are in
`v8/foundation/FOUNDATION_ROSTER.csv` and
`v8/foundation/FOUNDATION_MODEL_PROVENANCE.md`.

- Pinned: Chronos `amazon-science/chronos-forecasting` v2.3.2 commit
  `0aba28e9360b6355d5a919596c90b16c25939f02` (Apache-2.0); TimesFM
  `google-research/timesfm` `timesfm 3.0.2` PyPI, v3.0.0 commit
  `331c6d33cb1ac2611de3056d0ac7164aab6301eb` (Apache-2.0 source); `google/timesfm-2.0-500m`
  (the bare id in the prompt) is INVALID → HTTP 401; `google/timesfm-3.0-pytorch` rev
  `43046b85ec22d584a13f8098c2ed39c889e129c2` is `timesfm-non-commercial-license-v1.0`
  → excluded.
- **Named Chronos T5/Bolt and TimesFM 1.0/2.0 checkpoints are UNIVARIATE.** Seven
  channels would require a documented per-channel adapter that **discards
  cross-channel dependence** — not a faithful multivariate control. Chronos-2 is
  natively multivariate but was not executed.
- **The 11 frozen language encoders are NOT substitutes** for numerical foundation
  models. No measured pilot, no 80-cell matrix, no wall time / VRAM / predictions
  exist. `NOT_EXECUTED`.
- **Keep a SEPARATE roster; do NOT merge into the 28-arm family.**

**Smallest next action:** download the full pinned weights locally (Windows) →
tar + SHA-256 → `scp` to `/gpfs1/scratch/sychan552/models/` → isolated env
`/home/sychan552/.venvs/mlflu_fm` created inside an `sbatch` job → 1-cell A100 pilot →
only then 80 cells under `FOUNDATION_ROSTER.csv`. (T2 §8 gives the exact
`snapshot_download` call.) — **SUPERSEDED: all of these steps were executed on
2026-11-06 UTC (§B.1); only the 80-cell expansion remains `NOT_EXECUTED_BY_PROTOCOL`.**

### B.1 — FINAL T2 UPDATE 2026-11-06 (synced 2026-11-07): `COMPLETED_WITH_DOCUMENTED_SCOPE`

**Which old claim is superseded:** §B above ("`status: BLOCKED`; no full weights,
no tar/scp, no isolated env, no pilot, no 80-cell matrix; `NOT_EXECUTED`") and the
earlier v8 audit/table rows that said "T2 simply BLOCKED / no weights / no pilot /
no cells". The earlier `BLOCKED` verdict applied to a missing-input condition that
has since been **eliminated by verified work** (download / tar / scp / env / pilot /
matrix all executed 2026-11-06 UTC). The §1–§8 `BLOCKED` text of
`v8/foundation/T2_VERDICT.md` is likewise retained verbatim as the historical
earlier run, NOT erased (`T2_VERDICT.md` §FINAL UPDATE 2026-11-06). No training,
download or HPC job was re-run to produce this sync.

**Verified chain (JOB IDs; evidence in `v8/foundation/`):**

| item | value | evidence |
|---|---|---|
| 4 pinned weight tars | downloaded locally on Windows, total **5,024,901,120 B**; scp'd to `/gpfs1/scratch/sychan552/models/`; all **4 remote SHA-256 verified INSIDE sbatch 744607** and EXACTLY match local | `T2_DOWNLOAD_RESULT.md` §1/§2/§4/§5; `T2_EVIDENCE_HASHES.txt` (`CROSS_VERIFY=ALL_MATCH`) |
| isolated env | `/home/sychan552/.venvs/mlflu_fm` — Python 3.11.13, torch 2.6.0+cu124, chronos-forecasting 2.3.2, timesfm 1.3.0 (pandas 2.3.3, transformers 5.22.1, numpy 2.4.6) | jobs **744574** / **744576** (probe 744533); `T2_DOWNLOAD_RESULT.md` §6 |
| pilot **744589** `t2_fm_pilot` | `stingy` / `gpu-a100-05` / `NVIDIA A100-SXM4-80GB`; **PASSED**: all finite, MSE **0.3913**, only warmed-up repeated latency **10.191±0.446 ms** (warm-up 1 / repeat 5), peak VRAM **596 MiB** (28 `nvidia-smi` samples), wall 27.35 s | `T2_PILOT_AND_MATRIX.md` §2 |
| matrix **744607** `t2_fm_matrix` | `stingy` / `gpu-a100-05` / A100-SXM4-80GB; **8/8 cells `ok`**, all finite, **8 real NPZ**, peak VRAM **2608 MiB** (18 samples), wall **18.00 s** | `T2_PILOT_AND_MATRIX.md` §3/§4 |

**8 executed cells — real numbers (seed 2021, T=104, `scope=foundation_zero_shot_subset_not_1120_panel`):**

| label | L=24 | L=36 | L=48 | L=60 |
|---|---:|---:|---:|---:|
| `foundation_chronos` MSE_7var_z | 0.391328494 | 2.207397404 | 1.713535818 | 1.400230721 |
| `foundation_timesfm` MSE_7var_z | 0.729752533 | 2.654955324 | 2.031110049 | 1.662973370 |

(2 models × 4 L = 8 cells; full-precision values + NPZ paths + SHA-256 in
`T2_PILOT_AND_MATRIX.md` §4. Models: `amazon/chronos-bolt-tiny` @
`a0e552de…` (chronos-forecasting 2.3.2) and `google/timesfm-2.0-500m-pytorch` @
`dc244379…` (timesfm 1.3.0); both Apache-2.0, frozen zero-shot, **NO training /
fine-tuning**.)

**80-cell expansion `NOT_EXECUTED_BY_PROTOCOL` — STILL blocked (exact reason).**
`FOUNDATION_MATRIX_REPORT.json`: `"requested_80_cells":"NOT_EXECUTED_BY_PROTOCOL"`,
`"reason":"no training seed dimension in a frozen zero-shot model; 10 seeds would
produce 10 identical predictions"`. The originally-scoped `2×4×10=80` cells assume
a training seed; for a frozen zero-shot model a fixed (model, L, input) is
deterministic, so 10 seeds would duplicate predictions rather than add information.
The smallest faithful, non-duplicated subset (`2 models × 4 L = 8 cells`) was run
instead. This is a documented protocol decision, **not** a failure and **not** a
claim that 80 cells were run.

**Adapter limits / separate roster (REMAIN in force).** Both executed checkpoints
are **UNIVARIATE**; the 7 benchmark channels were passed as a **batch of 7 independent
series** (per-channel independent adapter) which **DISCARDS cross-channel dependence**
and is **NOT information-set-matched** to the multivariate arms — never describe it
as multivariate. Benchmark z-space was passed through (each model applies its own
internal normalization); TimesFM `freq_indicator=1` (weekly), `horizon_len=128`
sliced to L. Labels `foundation_chronos` / `foundation_timesfm` are a **SEPARATE
ROSTER** (`FOUNDATION_ROSTER.csv`), **never merged** into the frozen 28-arm family
or the 1120 national panel. No full-1120-panel comparison; Chronos-2 (natively
multivariate) tar downloaded but checkpoint NOT executed; TimesFM 3.0 excluded on
`timesfm-non-commercial-license-v1.0` grounds; `chronos-t5-small` and
`timesfm-1.0-200m` tars NOT executed.

**Latency honesty caveat (REMAINS in force).** `T2_PILOT_AND_MATRIX.md` §5.1:
TimesFM `wall_s=0.0` and the `0.004 / 2.483 / 4.489 / 6.492` ms values are
**loop/slicing timings of ONE shared `tfm.forecast` call**, NOT four independent
forward latencies; Chronos L24 `221.835` ms includes one-time CUDA init; the **only**
warm-up+repeated inference latency in TASK 2 is the pilot's **10.191±0.446 ms**.
No `FOUNDATION_CELLS.csv` latency / `wall_s` value may be presented as a repeated
measured inference latency.

---

## C. T3 — `final_llm_import`: COMPLETED (real table; LEGACY analysis-tree only)

A real `BENCH_MSE_BY_MODEL_L.csv` was written (HPC-side `paper_tables/`), sha256
`2e03b5109db03cfd4e1b9e89bd8e6069468fd4f7cd3671b367f7f632a0b6be29`, by job
`744134` (`ok: true`, all three steps `analysis_expanded.py`, `plot_bench.py`,
`plot_pareto.py` rc=0). Companion tables: `BENCH_PTE_PIE_BY_STEP.csv` sha256
`32307527610db542c0382adc8f3d09c9bd8052b103db90590063d6bf7d2d2890`,
`BENCH_EFFICIENCY.csv` sha256
`dfd1ff3524837b205f24ae65ab1083022e62989a9bbe2f5bf25dab8e220c63a7`.

- **[SUPERSEDED V8C: built from 388/388 readable cells after job 744884 restored both]** Built from **386 readable legacy cells** after **2 corrupt NPZs were quarantined
  (moved, NOT deleted)** in
  `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/QUARANTINE.json`:
  `miflu_L36_s2021` (0 B, `EOFError`) and `miflu_L60_s2021` (30977 B, `BadZipFile`).
  First run `744110` failed with `EOFError: No data left in file` (rc=2,
  `BRANCH=d.no-table`); the retry after quarantine succeeded. `gate=n_cells=386;n_arms=17`.
- **This is a LEGACY analysis-tree table, not the new 1120 panel.** The frozen
  `02_数字表格/BENCH_MSE_BY_MODEL_L.csv` is a DIFFERENT file (sha256
  `614232aabcd0d2b1109fed1cb2a9ba164628b81a334f8cff3e6e565aabf35653`) and must not be
  confused with the rebuilt HPC-side table.
- **Remaining:** the two quarantined corrupt legacy MIFlu NPZs must be regenerated or
  explicitly excluded before any claim based on that legacy analysis tree. No table
  was faked.

---

## D. T4 — CDC vintage: COMPLETED (corrected 2026-11-06)

**ERROR CORRECTION.** The earlier `PARTIAL / BLOCKED` verdict for T4 was **WRONG** and
is SUPERSEDED. A previous run fetched only 20 sample `(epiweek, issue)` rows from the
Delphi Epidata `fluview` endpoint and declared `BLOCKED: no release-calendar/vintage
source found` with peak re-scoring `BLOCKED`, without inspecting the project's own
`02_数字表格/` directory. That directory **ALREADY contained a complete CDC ILINet
vintage reconstruction and re-scored season peaks**, built by
`05_程序代码/cdc_vintage_build.py` from the **SAME** Delphi `fluview` endpoint. The
project owner caught the error. Authoritative dated record:
`v8/cdc_vintage/T4_CORRECTION.md`; corrected verdict `v8/cdc_vintage/T4_VERDICT.md`
(`status: COMPLETED`). The 20-row `v8/cdc_vintage/cdc_vintage.csv` is a verification
sample only, NOT a replacement for the frozen 7192-row table.

**Frozen artifacts (read + SHA-256 verified 2026-11-06, NOT modified):**

| Artifact | SHA-256 |
|---|---|
| `02_数字表格/cdc_vintage_raw.csv` (7192 data rows) | `e0c5512b2b6889780f345927708fee3ac3006ff59d78881dc6b55fa31fc7e9c8` |
| `02_数字表格/cdc_vintage.csv` (848 data rows) | `5a49e6be748aed251e82084a2b83d8c2f92ca23ef72ef8f442b10481c611b2c9` |
| `02_数字表格/cdc_vintage_report.md` | `e2da6b377abc318a311535cd593180d5ea62cd11ee03c31c3ee3fb2e67afd2d7` |
| `02_数字表格/cdc_peak_revintage.csv` | `7c9b5df808a1f78cb2e097aec114b3a735b075f6c2a991c24ae3db3883d7a504` |
| `05_程序代码/cdc_vintage_build.py` (builder) | `8c1e4b1e31a4339e8d30d6c8f9e62fc181996d47fcea1cb9a5f2d2bceb2a079f` |

- **1025** panel epiweeks; **848** with weekly release records; 177 without;
  **7192** `(epiweek, issue)` rows (`lag<=8`); **836/848** revised (98.6%);
  |ILITOTAL revision| p10 5.2% / median 21.8% / p90 51.8%.
- Season peaks re-scored AS-OF (first print) vs FINAL: **18 seasons scored,
  7 peak weeks move = 38.9%** (`cdc_peak_revintage.csv`).
- Archived `06_原始数据集/raw/national_illness_raw.csv` has only 8 distinct annual bulk
  snapshot `release_date` values and is NOT a vintage.

**Retained scientific limits (do NOT overclaim):** Delphi `release_date` is a
Delphi-ingest proxy, NOT a CDC-issued official revision number; no official CDC
release calendar / revision id is claimed. The reconstruction re-scores the **REFERENCE**
peak assignment on as-of data and does NOT re-score the 1120-cell model panel —
**model peak metrics remain retrospective**; no real-time / clinical claim. 2002
weeks have no real-time vintage. The Delphi URL/status evidence is retained as
provenance in `v8/cdc_vintage/CDC_VINTAGE_REPORT.md`.

---

## E. T5 — JBHI: dated verification record COMPLETED (submission-ready: NO)

`v8/JBHI_VERIFICATION_20261106.md` (sha256
`24e2f553c17977d67f0743b811ea7f1d6699a22bdbacb86001395967ac3f9259`),
`v8/JBHI_PROVENANCE_PATCH.md`, `v8/T5_VERDICT.md`.

- **VERIFIED (live HTTP 200 + verbatim quotes):** 14 pages regular / 16 review
  INCLUDING supplementary (original + revised); abstract ≤ 250 words; IEEE
  single-spaced double-column with embedded figures/tables; AI-use disclosure is
  IEEE-wide policy (acknowledgments; grammar/editing exception), NOT a JBHI clause;
  hybrid OA; APC **US$2,800 (2026)**; IEEE Member 5% / Society 20% discounts
  (non-combinable); $110/$250/$350 voluntary/overlength page-charge tiers.
- **UNVERIFIED:** official template class-file download (`.cls` / Word / ZIP) —
  selector `404` with browser UA / WAF `418` with full python-requests default
  header profile / `/api` `302` → `502`. The `418` is a UA/header-profile-dependent
  WAF bot block, NOT a missing page. Third-party mirror version drift (outdated
  12/14-page limit) recorded, not used.
- **`submission-ready: NO`.** The owner must obtain the template in a human browser
  session, pin filename + SHA-256, and paste `JBHI_PROVENANCE_PATCH.md` into
  `PAPER_TO_CODE.md` / manuscript provenance.

---

## F. T6 — RESOURCES: PARTIAL (measured subset; no full-1120 Pareto)

> **PARTIAL (IMPROVED) — synced 2026-11-07 HKT / 2026-11-06 UTC.** The
> "`peak_vram_mib = NOT_MEASURED` for **all** rows" text in this section is the
> **pre-744532 record** and is retained verbatim as the earlier state, NOT erased.
> It is **SUPERSEDED for MIFlu only** by §F.1: job 744532 measured MIFlu peak VRAM
> **4816 MiB** and a real forward wall 62.94 s. The other 5 rows remain
> `NOT_MEASURED`; the Chronos/TimesFM resource rows remain BLOCKED; overall T6
> stays `PARTIAL (IMPROVED)`.

`v8/RESOURCE_MEASUREMENTS.csv` (sha256
`bde9031f4fb2b91aa0321f71fc285cbe3df8f254d2f2f631379d4eb2f73252cd`), 6 rows × 24
columns, `v8/T6_VERDICT.md`, 36 raw logs in `v8/resource_logs/`.

- **REAL training wall times** (from queue-log `wall=` fields with line numbers;
  historical, not re-timed): MIFlu **581 s**, NLinear **6 s**, PatchTST **7 s**,
  DeepSeek-R1-Distill-Qwen-1.5B **24 s**.
- **REAL NPZ scoring-path latency** 0.0287–0.0297 ms (warm-up 5 / repeat 50, on
  `(170,7,24)` float32) — **explicitly NOT a model forward pass**.
- Software versions measured INSIDE sbatch job `744239` on `cpunode-034`:
  Python **3.9.25**, numpy **2.0.1**, pandas **2.3.3**, torch **2.5.1**, GNU time 1.9.
- `peak_vram_mib = NOT_MEASURED` for **all** rows: no GPU was allocated (tiny job);
  GPU job `744253` (`t6_res_gpu`) was PENDING with predicted start 2026-11-08 and was
  cancelled; two `stingy` submissions were rejected with
  `QOSMaxSubmitJobPerUserLimit`. No VRAM number invented.
- Chronos / TimesFM rows = `BLOCKED / NOT_EXECUTED` (T2 prerequisite missing).
- **Every row `scope=subset_only_not_full_1120` — no full-1120 Pareto claim.**

**Smallest next action:** re-run `t6_res_gpu.sbatch` when an A100 is allocatable and
QOS allows (with `--exclude=gpu-a100-03`), then complete T2 to unblock the two
foundation rows. — **SUPERSEDED IN PART:** job 744532 already ran a REAL MIFlu GPU
forward (§F.1); only the other 5 models' VRAM and the two foundation resource rows
remain outstanding.

### F.1 — FINAL T6 UPDATE 2026-11-06 (synced 2026-11-07): `PARTIAL (IMPROVED)`

**Which old claim is superseded:** §F above and `T6_VERDICT.md` §4/§6 (original
verdict, retained verbatim) said `peak_vram_mib = NOT_MEASURED for ALL 6 rows` and
"no GPU job ever started". That is **SUPERSEDED for MIFlu only** by the UPDATE
2026-11-06 section of `v8/T6_VERDICT.md` and `v8/T6_GPU_UPDATE.md`. T6 is still
`PARTIAL (IMPROVED)`, not `COMPLETED`.

| item | value | evidence |
|---|---|---|
| job | **744532** `t6_res_gpu_v8b` — `stingy` / `gpu-a100-05` / `NVIDIA A100-SXM4-80GB`, driver **580.167.08**; START/END 2026-11-06T15:30:57Z / 15:32:01Z; Slurm COMPLETED | `v8/T6_GPU_UPDATE.md` §1/§3 |
| what ran | a **REAL MIFlu forward from an existing checkpoint** (`export_miflu_all7.py --cells 36:2023 --ckpt …/best_miflu_L36.pth --device cuda`) inside sbatch on the compute node; `[PASS] all requested cells exported` | `v8/T6_GPU_UPDATE.md` §2/§3 |
| peak VRAM | **4816 MiB** (`nvidia-smi memory.used`), **63** samples, min **16 MiB**, `status=MEASURED` | `peak_vram_v8b.txt`, `nvidia_smi_sample_v8b.csv`, `t6_gpu_v8b_744532.out` |
| forward wall | **62.94 s** (`/usr/bin/time -v`, `1:02.94`) → `real_model_forward_wall_s=62.94` (new clearly-labelled column, MIFlu row only) | `time_v_gpu_forward_v8b.txt`, `v8/RESOURCE_MEASUREMENTS.csv` |
| model result | `test MSE_7var_z = 1.624383` | `gpu_forward_v8b.out` |

**Explicit limits (NOT silently changed):**
- ONE cell (L=36, seed=2023), NOT the full 1120-cell panel; every row
  `scope=subset_only_not_full_1120`; **no full-1120 Pareto claim**.
- The 62.94 s is the **whole-process wall clock for ONE cell's export** (data +
  checkpoint load + GPU forward + writing), **NOT** a repeated per-forward inference
  latency; `true_model_forward_latency_ms` stays `NOT_MEASURED` for every row; the
  existing `inference_latency_*` values remain **NPZ scoring-path latency ONLY,
  explicitly "NOT a model forward pass"**.
- **Other 5 model rows** (NLinear, PatchTST, DeepSeek-R1-Distill-Qwen-1.5B,
  Chronos, TimesFM) remain `NOT_MEASURED` for VRAM ("no GPU measurement job ran for
  this model"). No VRAM was invented for them.
- **Chronos / TimesFM resource rows remain `BLOCKED / NOT_EXECUTED`** in
  `v8/RESOURCE_MEASUREMENTS.csv`. The verbatim blocker string there ("TASK 2 is
  BLOCKED — no full pinned weights, no isolated HPC env, no 1-cell pilot") is the
  earlier-run record; T2 is now `COMPLETED_WITH_DOCUMENTED_SCOPE` but its foundation
  results live on the SEPARATE `FOUNDATION_ROSTER.csv` and were NOT merged into
  these T6 resource rows.
- CUDA toolkit / runtime version NOT logged (only driver 580.167.08) → NOT_MEASURED.
- The MIFlu row of `RESOURCE_MEASUREMENTS.csv` now carries real VRAM + the new
  `real_model_forward_wall_s=62.94` column; the other 5 rows' original fields are
  unchanged (`T6_GPU_UPDATE.md` §9, append-only `SHA256SUMS.txt`; updated CSV
  SHA-256 `D609D57DCEB5FCBA6656A40A4576D87971F5371AC46AD6589754515C95BFCFCC`).

---

## G. OLD 28-ARM SNAPSHOT MUST STAY SEPARATE

- **Historical frozen CSVs** in `02_数字表格/` remain byte-identical.
- **Historical numbers (OLD):** 28 arms; Holm **0/136** from `p_raw` with forward
  cumulative maximum (never the exported `p_holm`); NLinear–PatchTST **0.1172**;
  **4/16** aggregate cells; **old NLinear K&S champion**.
- **New 1120-panel leading order (NEW):** MIFlu **1.7944** < PatchTST **1.9521** <
  NLinear **2.0782** (all-valid); crop **1.4994 / 1.6352 / 1.9027**.
- Step passes (new): MIFlu **252/1680**, PatchTST **215/1680**, NLinear **57/1680**.
- Ablation (new) **non-monotonic**: K4 **1.4989** best, K12 **1.7604** worst.
- Paired Wilcoxon **exploratory** 349/378 (cells share one national series and
  overlapping targets; not confirmatory).
- The historical "NLinear peak champion" and "monotonic depth trend" conclusions are
  **not reproduced** on the new panel and must be stated as superseded, not silently
  replaced. The old 16-unit peak table and the new 1680 step rows are different
  scoring populations.

---

## H. FINAL v8 status of all 8 tasks

| Task | Title | Final v8 status | One-line evidence |
|---:|---|---|---|
| T1 | Walk-forward missing 218 cells | **COMPLETED** | 1020/1020 `ok`, sha256 `53d0e0cb…`; 218 recovered, 0 changed, 0 lost, 0 missing |
| T2 | Numerical foundation models | **COMPLETED_WITH_DOCUMENTED_SCOPE** | 4 tars (5,024,901,120 B) + scp + remote SHA-256 in 744607; env 744574/744576; pilot 744589 PASSED; matrix 744607 8/8 cells; 80-cell expansion `NOT_EXECUTED_BY_PROTOCOL`; separate `FOUNDATION_ROSTER.csv`, never merged |
| T3 | Legacy `final_llm_import` | **COMPLETED** | real `BENCH_MSE_BY_MODEL_L.csv` sha256 `2e03b510…` from 386 readable cells (2 quarantined) |
| T4 | CDC calendar / vintage | **COMPLETED** (corrected 2026-11-06) | frozen 7192-row `cdc_vintage_raw.csv` / 848-row `cdc_vintage.csv` / `cdc_peak_revintage.csv` (18 seasons, 7 peak weeks moved=38.9%) in `02_数字表格/`; earlier `BLOCKED` verdict erroneous; see `T4_CORRECTION.md`. Retained limits: Delphi proxy, reference-peak-only, retrospective model peaks |
| T5 | JBHI verification | **COMPLETED** | dated record; 14 pp / ≤250 words / double-column / APC US$2,800 VERIFIED; template UNVERIFIED; `submission-ready: NO` |
| T6 | Resource measurements | **PARTIAL (IMPROVED)** | MIFlu peak VRAM 4816 MiB + real forward wall 62.94 s (job 744532); other 5 rows NOT_MEASURED; Chronos/TimesFM resource rows BLOCKED; `subset_only_not_full_1120` |
| T7 | v8 documents | **COMPLETED** | this addendum + 3 DOCX/PDF + map/audit/blocked copies + `T7_VERDICT.md` |
| T8 | Final package | **COMPLETED (PRELIMINARY PACKAGING PASS)** | validator `PASS` / `scientific_readiness: NOT_ASSESSED`; `T8_VERDICT.md` notes T7 docs and the T1-updated WF CSV were not yet folded in |

No task is falsely marked "all done". **T2 is now COMPLETED_WITH_DOCUMENTED_SCOPE**
and **T6 PARTIAL (IMPROVED)** — neither is "all done": the T2 80-cell expansion
(`NOT_EXECUTED_BY_PROTOCOL`), the univariate / per-channel-independent adapter and
information-set mismatch, the T2 latency honesty caveat, the other 5 T6 VRAM rows,
the Chronos/TimesFM T6 resource rows, true model-forward latency, the JBHI template
download, the T3 2-NPZ quarantine and the rebuild of the 3 v8 DOCX/PDF (which
predate §B.1/§F.1) remain genuinely BLOCKED / NOT_MEASURED / UNVERIFIED with exact
evidence and next actions. **T4 is now COMPLETED** (corrected 2026-11-06) on the
frozen `02_数字表格/` reconstruction; its earlier `BLOCKED` verdict was erroneous.

---

## I. Evidence index (all re-checked 2026-11-06)

- `HANDOFF_20261105/final/WF_RECOMPUTED.csv`, `WF_RECOMPUTED_MEANS.csv`
- `HANDOFF_20261105/v8/evidence/WF_RECOMPUTE_REPORT.json`,
  `WF_RECOMPUTED_v8.csv`, `WF_RECOMPUTED_MEANS_v8.csv`,
  `WF_RECOMPUTED_v7_baseline.csv`, `WF_RECOMPUTED_MEANS_v7_baseline.csv`
- `HANDOFF_20261105/v8/foundation/{T2_VERDICT.md,FOUNDATION_ROSTER.csv,FOUNDATION_MODEL_PROVENANCE.md,T2_DOWNLOAD_RESULT.md,T2_PILOT_AND_MATRIX.md,T2_EVIDENCE_HASHES.txt}` + `v8/foundation/t2_hpc_evidence/` (pilot 744589 / matrix 744607)
- `HANDOFF_20261105/v8/{T6_GPU_UPDATE.md,RESOURCE_MEASUREMENTS.csv}` + `v8/resource_logs/*_v8b*` (job 744532)
- `HANDOFF_20261105/v8/cdc_vintage/{T4_VERDICT.md,CDC_VINTAGE_REPORT.md,cdc_vintage.csv,T4_CORRECTION.md}`
- `02_数字表格/{cdc_vintage_raw.csv,cdc_vintage.csv,cdc_vintage_report.md,cdc_peak_revintage.csv}` + `05_程序代码/cdc_vintage_build.py` (frozen, T4 COMPLETED)
- `HANDOFF_20261105/v8/{T5_VERDICT.md,T6_VERDICT.md,T8_VERDICT.md,JBHI_VERIFICATION_20261106.md,JBHI_PROVENANCE_PATCH.md,RESOURCE_MEASUREMENTS.csv,TASK_LOG.md}`
- `HANDOFF_20261105/final/{CELL_METRICS.csv,MODEL_MEANS_BY_PANEL.csv,PEAK_BY_STEP.csv,ABLATION_MEANS.csv,SCIENTIFIC_AUDIT.md,FINAL_RESULTS.md}`

**Bottom line (synced 2026-11-07).** v8 upgrades the walk-forward from partial to
complete on the LEGACY panel, delivers a real legacy analysis-tree table, a dated
JBHI record, a **COMPLETED frozen CDC ILINet vintage reconstruction (TASK 4,
corrected 2026-11-06)**, **T2 foundation models COMPLETED_WITH_DOCUMENTED_SCOPE
(8 zero-shot cells on a SEPARATE roster, jobs 744589/744607)** and **T6
PARTIAL (IMPROVED) with MIFlu peak VRAM 4816 MiB measured (job 744532)**. Still
honestly BLOCKED / NOT_MEASURED / UNVERIFIED: the `NOT_EXECUTED_BY_PROTOCOL` 80-cell
expansion, the univariate/adapter and information-set limits, the T2 latency honesty
caveat, the other 5 T6 VRAM rows, the Chronos/TimesFM T6 resource rows, true
model-forward latency, the JBHI template download, the T3 2-NPZ quarantine and the
rebuild of the 3 v8 DOCX/PDF / T8 package. Retained CDC limits: Delphi proxy (not a
CDC official revision number), reference-peak-only re-scoring, retrospective model
peak metrics, no 2002 real-time vintage. Old snapshot, new national panel, the
LEGACY 5-fold N=3 WF panel and the separate foundation roster are kept strictly
separate. The manuscript is **not** submission-ready.


---

## V8C FINAL UPDATE (2026-11-06 UTC) — supersedes the v8b sections above

The v8b text above recorded the *interim* state. All four items below are now
final; the earlier statements are SUPERSEDED, not silently overwritten.

1. **T2 — 80 valid cells, not 8.** Job `744886` produced
   `FOUNDATION_80_CELLS.csv` with **80/80 `ok`, all finite, 80 real NPZ**
   (`v8/foundation/t2_hpc_evidence/full80_out/`). Because both checkpoints are
   frozen zero-shot with no training seed dimension, the 10 replicates are
   **10 distinct forecast origins** (rows 773-782), not 10 seeds;
   `seed_semantics=NOT_APPLICABLE`. The literal 10-seed expansion remains
   `NOT_EXECUTED_BY_PROTOCOL`. Peak VRAM 2608 MiB; Chronos 10.229 +/- 1.074 ms
   and TimesFM 50.906 +/- 4.459 ms (warm-up + repeated). See `v8/foundation/T2_FULL80.md`.
2. **T3 — 388/388 NPZ readable.** Job `744884` COPY-restored the two corrupt
   files from existing valid 7-channel copies and re-ran `final_llm_import`;
   `BENCH_MSE_BY_MODEL_L.csv` is now `a7d98ad8...e46`. The quarantine caveat is
   resolved. See `v8/T3_RESTORE.md`.
3. **T5 — provenance applied.** `v8/PAPER_TO_CODE.md` carries the dated JBHI
   guidance verification and the builder now prefers it. The official template
   class file is still UNVERIFIED.
4. **T6 — all 6 representative models measured.** Jobs `744897` / `744899`:
   peak VRAM MIFlu 4816, NLinear 558, PatchTST 720, GPT-2 1070, Chronos 596,
   TimesFM 2594 MiB. Warm-up+repeated real forward latencies for GPT-2
   6.98 +/- 0.097, Chronos 9.854 +/- 0.337, TimesFM 48.273 +/- 3.531 ms.
   Isolated single-forward latency for MIFlu/NLinear/PatchTST remains explicitly
   NOT_MEASURED. See `v8/T6_FINAL_SWEEP.md`.

Still blocked / unverified: the literal 10-seed expansion; multivariate-native
foundation checkpoints; full-1120 comparisons; the univariate adapter's
information-set mismatch; official JBHI template class file; confirmatory
dependence-aware statistics; retrospective model-panel peak metrics.
No full-1120 Pareto claim. The manuscript is NOT submission-ready; a structural
validator PASS means `scientific_readiness: NOT_ASSESSED`.
