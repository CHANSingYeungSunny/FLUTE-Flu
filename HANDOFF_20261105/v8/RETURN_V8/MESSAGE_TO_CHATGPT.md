# Message to ChatGPT — v8 evidence handoff (2026-11-06)

**This is a PRELIMINARY packaging pass, not a finished manuscript.** TASK 7 DOCX/PDF
(`01_最终报告/v8/`) and the T1-updated `final/WF_RECOMPUTED.csv` may land AFTER this
package. See `packaging/T8_PREP_NOTES.md` for the single re-run command. Do NOT call the
manuscript submission-ready: `manuscript_submission_ready: NO` (`T5_VERDICT.md`). A
validator `integrity_status: PASS` is STRUCTURAL ONLY and MUST be read together with
`scientific_readiness: NOT_ASSESSED` (`RETURN_V8/VALIDATION_RESULT.json`).

Authoritative v8 verdicts: `v8/TASK_LOG.md`, `v8/foundation/T2_VERDICT.md`,
`v8/cdc_vintage/T4_VERDICT.md`, `v8/T5_VERDICT.md`, `v8/T6_VERDICT.md`,
`v8/T8_VERDICT.md`. The v7 baseline message is `audit/v7/MESSAGE_TO_CHATGPT.md`.

---

## 1. Explicit old / new separation (AGENTS.md RULE 4)

- **Old 28-arm frozen snapshot**: the historical frozen CSVs under `02_数字表格/*.csv`
  (28 arms, Holm 0/136 from `p_raw` with forward cumulative maximum, NLinear–PatchTST
  0.1172, 4/16 aggregate cells). These are old-snapshot facts, are NOT part of this
  return, and were never overwritten.
- **New 1120 panel**: the harmonised national panel (28 models × 4 L × 10 seeds
  2021–2030) scored tables are under `final/` (`CELL_METRICS.csv`, `MODEL_L_PANEL.csv`,
  `PAIRED_HOLM_NEW.csv`, `PEAK_*`, `ABLATION_*`, `REGIONAL_*`, `WF_*`,
  `FINAL_RESULTS.md`, `SCIENTIFIC_AUDIT.md`). The new panel is NEVER merged into the
  old 28-arm snapshot — they are separate files with separate denominators.
- **Foundation models on a SEPARATE ROSTER**: numerical foundation models
  (Chronos / TimesFM) are NOT the 11 frozen language encoders and are NOT merged into
  the 28-arm family. They live only on `foundation/FOUNDATION_ROSTER.csv` +
  `foundation/FOUNDATION_MODEL_PROVENANCE.md` and are currently **BLOCKED** (§3).
- **v7 return kept separately labelled**: `v7_snapshot/` holds verbatim COPIES of the
  frozen `v7/RETURN_V7/` key files (root files + `DOCUMENTS/v7/`); `RAW_EVIDENCE/`
  holds the 1120 validated raw prediction NPZ that its ledger points to. The
  root `RUN_LEDGER.csv` / `CHECKS.json` / protocol JSONs are the carried-over v7
  structural skeleton needed by the official validator — they are NOT new v8
  measurements and are not rewritten here.

---

## 2. Exactly what changed in v8 vs v7

v7 left these NOT done (see `audit/v7/MESSAGE_TO_CHATGPT.md`): foundation models, CDC
vintage, JBHI guidance, resource measurements; v7 DOCX/PDF rebuild; strict
`RETURN_TO_CHATGPT.zip` rebuild; walk-forward 473/1020 valid.

v8 (T1–T8 of `NEXT_DEEPSEEK_PROMPT.md`, per `v8/TASK_LOG.md`) changes:

- **T1 walk-forward — IN PROGRESS, final CSV NOT landed.** The frozen v7 baseline was
  preserved byte-for-byte as `evidence/WF_RECOMPUTED_v7_baseline.csv` +
  `WF_RECOMPUTED_MEANS_v7_baseline.csv`. The current `final/WF_RECOMPUTED.csv`
  (1020 rows) reflects the seven-channel recomputation from raw NPZ: **802 `ok`,
  218 `no_npz`** (not v7's 473/1020). All 218 are `SKIPPED` in
  `evidence/master_queue.tsv` / `evidence/queue_state.tsv` (attempts=2, last_job
  729729, CUDA busy), mapped 1:1 by `evidence/wf_fix218_todo.tsv`. They use the
  LEGACY N=3 seeds 42/43/44 protocol, so no `protocol-mismatch` was invented. Probe
  743920 reproduced the frozen MSE exactly; `scripts/wf_recompute.py` and
  `scripts/wf_fix218*.sbatch` exist. Job 743850 (`wf_fix218`) was RUNNING and
  744271 (`wf_recompute`) PENDING at the time of `TASK_LOG.md`; **no claim that the
  218 are COMPLETED** is made, and the updated WF CSV/means are still pending.
- **T2 foundation — BLOCKED, but provenance + separate roster COMPLETED.**
  `foundation/T2_VERDICT.md`: source-pinned provenance (Chronos v2.3.2 commit
  `0aba28e9…`, TimesFM 3.0.2 / v3.0.0 commit `331c6d33…`, exact HF revisions +
  licences + exact HTTP codes), `FOUNDATION_ROSTER.csv` (8 rows, separate roster),
  and 3 local pinned `snapshot_download` probes (config/README only) are real.
  End-to-end T2 acceptance (pilot + 80 cells) is **BLOCKED** — no full weights, no
  isolated HPC env, no `sbatch`; see §3.
- **T3 `final_llm_import` — COMPLETED with a documented quarantine.** Real output
  tables `paper_tables/BENCH_MSE_BY_MODEL_L.csv`, `BENCH_PTE_PIE_BY_STEP.csv`,
  `BENCH_EFFICIENCY.csv` were rebuilt (job 744134, rc=0). Two corrupt legacy MIFlu
  NPZ (0 B `EOFError`, `BadZipFile`) were MOVED to a quarantine dir with provenance;
  the rebuilt table reflects 386 readable cells, not 388. No table was faked.
- **T4 CDC vintage — PARTIAL, primary goal BLOCKED.** `cdc_vintage/T4_VERDICT.md`
  + `cdc_vintage/CDC_VINTAGE_REPORT.md`: a real Delphi-proxy `cdc_vintage.csv`
  (20 `(epiweek, issue)` rows, `cdc_official_revision_id = NOT_AVAILABLE`, affected
  weeks 201449…201501) was built from 3 live HTTP-200 fetches; 16 URLs checked;
  raw bodies/status TSVs under `cdc_vintage/http_evidence/`. The ACTUAL CDC
  release calendar / revision id is not reconstructable → retained label
  `BLOCKED: no release-calendar/vintage source found`; peak re-scoring BLOCKED
  (missing `step → absolute row → CDC MMWR epiweek` mapping + official release
  date). No peak CSV rewritten, no mapping invented.
- **T5 JBHI — COMPLETED dated verification record, template UNVERIFIED.**
  `JBHI_VERIFICATION_20261106.md` + `T5_VERDICT.md`: verified live 2026-11-06 that
  JBHI is 14 pages regular / 16 review INCLUDING supplementary, abstract ≤250
  words, IEEE single-spaced double-column with embedded figures/tables, hybrid OA,
  APC US$2,800 (2026), IEEE-wide AI disclosure (not a JBHI clause). The official
  `.cls`/Word class file could NOT be downloaded (template selector: 404, WAF 418,
  302→502) → `template_download_status: UNVERIFIED`. `JBHI_PROVENANCE_PATCH.md`
  is paste-ready text only; `PAPER_TO_CODE.md` / manuscript provenance were NOT
  edited. `submission-ready: NO`.
- **T6 resources — PARTIAL, subset only.** `RESOURCE_MEASUREMENTS.csv` (6 rows,
  24 cols, `scope=subset_only_not_full_1120`) + 36 raw logs in `resource_logs/`:
  REAL historical training wall times (MIFlu 581 s, NLinear 6 s, PatchTST 7 s,
  DeepSeek-R1-Distill-Qwen-1.5B 24 s) and REAL NPZ **scoring-path** latency
  0.0287–0.0297 ms (warm-up 5 / repeat 50, explicitly NOT a model forward).
  `peak_vram_mib = NOT_MEASURED` for ALL rows (no GPU allocated; job 744253
  CANCELLED, two stingy submissions rejected by `QOSMaxSubmitJobPerUserLimit`).
  Chronos/TimesFM rows BLOCKED/NOT_EXECUTED. No full-1120 Pareto claimed.
- **T7 v8 documents — NOT EXECUTED in this pass.** `01_最终报告/v8/` does NOT exist
  at build time, so no v8 DOCX/PDF were bundled. The English manuscript body,
  Chinese internal report/Q&A, `DOCUMENT_UPDATE_MAP.csv`, `SCIENTIFIC_AUDIT.md`,
  `BLOCKED_AND_UNVERIFIED.md` were NOT rebuilt/updated by T8 (out of write scope).
- **T8 package — this pass.** `RETURN_V8/` assembled, `RETURN_MANIFEST.json` written
  only by the official tool, validator run, `RETURN_TO_CHATGPT.zip` and
  `RAW_EVIDENCE.zip` rebuilt with SHA-256. See `T8_VERDICT.md`.

---

## 3. Exactly what remains BLOCKED / NOT_EXECUTED / UNVERIFIED

| Item | Status | Verdict file / evidence |
|---|---|---|
| Chronos / TimesFM pilot + 80-cell matrix | **BLOCKED** — no full pinned weights (`model.safetensors`, TimesFM `checkpoint_1100000/*`), no tar/scp, no isolated `/home/sychan552/.venvs/mlflu_fm`, no pilot. **NOT_EXECUTED**: no wall time / VRAM / finite predictions. | `foundation/T2_VERDICT.md` §6–§8; `evidence/foundation_*`; `foundation/FOUNDATION_ROSTER.csv` |
| CDC actual release date / revision id | **BLOCKED: no release-calendar/vintage source found**; peak re-scoring **BLOCKED** (missing step→MMWR epiweek mapping). `cdc_official_revision_id = NOT_AVAILABLE`. | `cdc_vintage/T4_VERDICT.md` §A/§E; `CDC_VINTAGE_REPORT.md` |
| JBHI official template class file | **UNVERIFIED** (404 / WAF 418 / 302→502). Verification record itself is COMPLETED. | `T5_VERDICT.md`; `JBHI_VERIFICATION_20261106.md` |
| Peak VRAM + true model-forward latency (all 6 resource rows) | **NOT_MEASURED** — no GPU job ever started; `nvidia-smi` sampling never executed. | `T6_VERDICT.md` §4/§6; `resource_logs/` |
| Chronos / TimesFM resource rows | **BLOCKED / NOT_EXECUTED** (T2 prerequisite missing). | `T6_VERDICT.md` §5; `RESOURCE_MEASUREMENTS.csv` |
| Full 1120-cell / 28-arm Pareto from resources | **NOT claimed / NOT measured** — `scope=subset_only_not_full_1120`. | `T6_VERDICT.md` §6 |
| T1 218 `no_npz` walk-forward cells + updated `WF_RECOMPUTED.csv` / means | **IN PROGRESS / NOT landed** — job 743850 RUNNING, 744271 PENDING at `TASK_LOG.md`; baseline CSVs preserved in `evidence/`. NO DONE claim. | `TASK_LOG.md` (T1); `evidence/wf_fix218_todo.tsv`; `final/WF_RECOMPUTED.csv` (802/218) |
| v8 DOCX/PDF + manuscript body/internal report/Q&A rebuild; `DOCUMENT_UPDATE_MAP.csv` / `SCIENTIFIC_AUDIT.md` / `BLOCKED_AND_UNVERIFIED.md` updates | **NOT EXECUTED** in this pass — `01_最终报告/v8/` absent. | `TASK_LOG.md`; `T8_VERDICT.md`; `packaging/T8_PREP_NOTES.md` |
| Manuscript submission-ready | **NO**. Guidance verification only; template class file UNVERIFIED. | `T5_VERDICT.md` |
| Paired statistics | **EXPLORATORY** — cells share one series / overlapping targets; no dependence-aware confirmation. | `final/SCIENTIFIC_AUDIT.md`; `audit/v7/BLOCKED_AND_UNVERIFIED.md` |

Additional carried-over items (from `audit/v7/BLOCKED_AND_UNVERIFIED.md`, unchanged):
the 11 frozen language encoders are NOT substitutes for the numerical foundation
models; regional Table VI is 10-variable, not the 7-channel national metric; the two
corrupt legacy MIFlu NPZ from T3 remain quarantined and must be regenerated or
explicitly excluded before any claim based on that legacy analysis tree.

---

## 4. Package structure (`RETURN_V8/`)

`final/` (new 1120-panel scored CSVs + audit docs), `foundation/`, `cdc_vintage/`,
`resource_logs/`, `evidence/`, `scripts/` (v8 task evidence + official tool copies),
`audit/v7/` (v7 addendum/audit docs), `v7_snapshot/` (frozen v7 key files,
separately labelled), `RAW_EVIDENCE/` (1120 raw NPZ), `logs/`, `DOCUMENTS/v8/`
(only if `01_最终报告/v8/` existed — it did not), plus the root REQUIRED skeleton.
Full per-file list + hashes: `RETURN_MANIFEST.json` (written by the official tool)
and `RETURN_V8/RETURN_LAYOUT.md`. `VALIDATION_RESULT.json` is the validator output.

`RAW_EVIDENCE.zip` carries `v8/evidence/`, `v8/resource_logs/`, `v8/cdc_vintage/`,
`v8/foundation/`, `v8/scripts/`, `final/` and every raw prediction NPZ already
present in the project (COPY only, nothing downloaded). Legacy archived NPZ under
`99_旧文件存档/`, `03_预测数据_证据/`, `handoffs/` stay in their OWN labelled
subtrees and are NOT merged into the 1120-panel tables.

**Bottom line:** several real, dated v8 records were produced, but T2 (pilot/matrix),
T4 (actual vintage + peak re-scoring), T5 (template class file), T6 (VRAM/true
forward), T1 (218 cells + final WF CSV) and T7 (v8 DOCX/PDF + document updates)
remain BLOCKED / NOT_EXECUTED / UNVERIFIED / NOT landed. This package is a
PRELIMINARY structural snapshot; a validator PASS is `scientific_readiness:
NOT_ASSESSED` and is not scientific certification.
