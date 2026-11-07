# Handoff prompt to ChatGPT — v8 (2026-11-06/07)

Use the two ZIPs together; unzip both into the same directory.

- `RETURN_TO_CHATGPT.zip` — 199,883,696 B — SHA-256 `5433e8d8a799c418c4fd55db1e8884b1ec1f4b141f98790f0f51cdd39887ad03`
- `RAW_EVIDENCE.zip` — 345,006,379 B — SHA-256 `550977437230dafc257cb3a36b02837764afec411e90f286b41d3f3c3d083f75`

Validator: **PASS**, 1,432 files hashed, 1,120 completed, errors `[]`, `scientific_readiness: NOT_ASSESSED`.
Structural/hash PASS is not scientific certification.

---

## Message for ChatGPT (copy below)

You are updating the MIFlu / FLUTE-Flu FYP documents from the v8 evidence package.

### Current verified state

1. **National 28-arm panel: 1120/1120 cells.** Ten seeds 2021–2030, L=24/36/48/60, T=104.
2. **MIFlu seven-channel recovery: 40/40**, targets exactly equal the NLinear targets.
3. **Table VI regional: 53/53 valid** (`mse_z`, ten-variable regional aggregates).
4. **Legacy walk-forward: 1020/1020 valid** after filling the 218 previously skipped cells.
   This is a separate legacy 5-fold panel (seeds 42/43/44), **not** the 10-seed national panel.
5. **Foundation models: 80/80 valid** — Chronos 40 + TimesFM 40, zero-shot rolling-origin
   (10 origins), `seed_semantics=NOT_APPLICABLE`. Separate roster; do not merge into the 28 arms.
6. **Ablation: 60 cells + K=6 reference**; non-monotonic.
7. **Resource measurements** for 6 representative models (peak VRAM and measured timings).
8. **CDC vintage:** project reconstruction exists (`cdc_vintage.csv`, 848 epiweeks); this is
   retrospective final-vintage, not real-time release validation.
9. **JBHI:** 14-page limit, 250-word abstract, double-column, AI disclosure and APC verified;
   the exact template class file remains **UNVERIFIED** (404/418/502).

### New results that must replace old claims

- National all-valid MSE: **MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782**.
  Crop panel: **1.4994 / 1.6352 / 1.9027**; MIFlu crop 1.4994 reproduces the old 1.4995.
- Peak: **MIFlu 252/1680 (15.0%)**, **PatchTST 215/1680 (12.8%)**, **NLinear 57/1680 (3.4%)**.
  The historical “NLinear is the peak champion” is **not reproduced**; the old 16-unit table is a
  different scoring population.
- Ablation: **K4 1.4989 best, K6 1.5457 (n=10), K2 1.5813, K8 1.6124, no_lora 1.6330,
  K12 1.7604 worst** — no monotonic depth trend.
- Foundation zero-shot (separate protocol): Chronos mean MSE by L24/36/48/60 =
  2.1786 / 2.4102 / 1.8598 / 1.5746; TimesFM = 2.3076 / 2.4624 / 1.9075 / 1.6519.
  Do not compare these directly with the 1,120-cell national means; label the protocol.
- Legacy WF means (separate 5-fold panel): MIFlu 2.2203, PatchTST 3.0396, NLinear 3.2116.

### What to change

Apply `DOCUMENT_UPDATE_MAP.csv` and `V8_SCIENTIFIC_ADDENDUM.md` to:

1. English manuscript body (not only an appendix).
2. Chinese internal report and the separate Q&A companion (preserve Q01–Q25 identities).
3. English FYP progress report.
4. README, slides/notes (slides: propose changes, do not overwrite owner-edited PPTX).
5. Journal record and `PAPER_TO_CODE.md` (T4/T5 provenance).

Keep the historical revision-9.2 values as a labelled old snapshot. Do not overwrite frozen CSVs.

### What not to claim

- Do **not** call the manuscript submission-ready or predict acceptance.
- Do **not** say the foundation models are part of the 28-arm family or the 10-seed panel.
- Do **not** claim monotonic depth, real-time CDC vintage, or a verified JBHI template class.
- Do **not** treat the validator PASS as scientific certification.

### Deliverables requested from you

1. Updated DOCX/PDF for the manuscript, Chinese report, Q&A companion and FYP report.
2. `CHANGES.md` keyed to files and sections, listing every changed claim and its evidence.
3. A short list of items that remain BLOCKED/UNVERIFIED and must not be written as results.
4. No fabricated numbers; if a claim has no source file in the package, leave it out or mark it
   unverified.

### Package map

- `DOCUMENTS/v8/` — v8 manuscript, Chinese report, Q&A companion
- `final/` — national scoring, peak events, ablation, regional/WF, dependence bootstrap
- `foundation/` — T2 80-cell evidence and reports
- `evidence/` — T1/T3/T4 evidence, WF recomputation
- `resource_logs/` + `RESOURCE_MEASUREMENTS.csv` — T6
- `JBHI_VERIFICATION_20261106.md`, `T5_VERDICT.md` — T5
- `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`, `TASK_LOG.md` — status and caveats
