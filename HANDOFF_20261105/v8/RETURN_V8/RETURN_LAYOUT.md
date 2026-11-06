# RETURN_V8 layout and old/new separation (structural note)

This file describes the package layout. It is NOT a scientific result.

- `final/` — the NEW 1120-panel scored CSVs + audit docs, copied from
  `HANDOFF_20261105/final/` (COPY; sources untouched).
- `foundation/`, `cdc_vintage/`, `resource_logs/`, `evidence/`, `scripts/` —
  v8 task evidence (T1–T7 text files), mirroring `v8/` subdirectories.
- `audit/v7/` — the v7 addendum/audit documents, kept separate.
- `v7_snapshot/` — the FROZEN v7 RETURN_V7 key files (root files +
  `DOCUMENTS/v7/`), COPIED verbatim and SEPARATELY LABELLED. The NPZ raw
  predictions that its ledger points to live at `RAW_EVIDENCE/`.
- `RAW_EVIDENCE/` — the 1120 validated raw prediction NPZ (old 28-arm
  snapshot / previous return era), carried over unchanged for the ledger.
- `logs/EXECUTION_LOG.md` — referenced by the root `CHECKS.json`.
- Root `RUN_LEDGER.csv`, `CHECKS.json`, `RETURN_SUMMARY.md`, protocol/plan
  JSON etc. are the carried-over v7 structural skeleton needed by the
  official validator; they are NOT new v8 measurements.
- `DOCUMENTS/v8/` — v8 DOCX/PDF only if `01_最终报告/v8/` existed at build
  time. It did NOT exist at the time of this build (see T8_PREP_NOTES.md).

## Old / new separation (AGENTS.md RULE 4)

The frozen 28-arm historical snapshot (`02_数字表格/*.csv`, Holm 0/136,
NLinear–PatchTST 0.1172, 4/16 aggregate cells) is a SEPARATE old-snapshot
fact and is NOT part of this return. The NEW 1120-panel tables are under
`final/` and are never merged into that old snapshot. The numerical
foundation models (Chronos / TimesFM) live on a SEPARATE ROSTER
(`foundation/FOUNDATION_ROSTER.csv`) and are NOT merged into the 28-arm
family; they remain BLOCKED (see `foundation/T2_VERDICT.md`).

A validator `integrity_status: PASS` is STRUCTURAL ONLY and MUST be read
with `scientific_readiness: NOT_ASSESSED`.
