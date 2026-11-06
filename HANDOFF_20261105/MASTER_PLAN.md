# Master plan and execution status — 2026-11-06

Goal: finish every remaining ChatGPT-required deliverable without fabricating results.

## Phase status

| Phase | Work | Status |
|---|---|---|
| P0 | 1120 cells, 7ch schema/target equality, fix40, legacy finalisation | **DONE** |
| P1 | harmonised MSE/MAE panels, event-level peaks | **DONE** |
| P2 | paired exploratory statistics | **DONE (exploratory)** |
| P3 | ablation ladder aggregation | **DONE (K6 ref 10/12)** |
| P4 | Table VI / walk-forward validity and aggregation | **IN PROGRESS / NOT VALIDATED** |
| P5 | v7 manuscript/internal/FYP/Q&A | **NOT STARTED** |
| P6 | return ZIP + manifest + validator + audit | **NOT STARTED** |
| P7 | blocked items (foundation models, CDC vintage, JBHI, resources) | **NOT STARTED** |

## P0 evidence

- `cellok.py count all/export all/cells_all.tsv` = **1120/1120**.
- 7ch MIFlu = **40/40**; all 40 targets equal NLinear targets exactly
  (shape, `target`, `target_start_row`, max diff 0.0).
- fix40: **40/40 rc=0, validated=yes**.
- Legacy queue: only `f5_llm_import` TODO; lanes returned `idle-no-work`.

## P1 evidence

- `scoring/CELL_METRICS.csv` 2240 rows (1120 × 2 panels).
- `scoring/MODEL_L_PANEL.csv` 224 rows.
- `scoring/PEAK_BY_STEP.csv` 47,040 rows.
- `scoring/PEAK_EVENTS.csv` 181,868 event rows.
- Leading MSE order (all-valid): MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782.
- Crop reproduces old mean: MIFlu 1.4994.
- Peak step passes: MIFlu 252/1680 (15.0%), PatchTST 215/1680 (12.8%),
  NLinear 57/1680 (3.4%) — historical NLinear peak champion is not reproduced.
- Event success: iTransformer 99.1%, MIFlu 98.8%, PatchTST 97.6%, NLinear 92.6%.

## P2 evidence

- 28 models, 378 pairs, Wilcoxon on 40 (L,seed) cells, Holm:
  **349/378 rejections**, min adjusted p ≈ 6.9e-10.
- **Exploratory only**: overlapping targets and shared series; dependence-aware
  blocked/bootstrap analysis not yet done.

## P3 evidence

- `ABLATION_MEANS.csv`: K4 1.4989, K6 1.5457 (n=10), K2 1.5813, K8 1.6124,
  no_lora 1.6330, K12 1.7604.
- No monotonic depth trend; K4 best, K12 worst.

## Remaining

1. **P4**: validate Table VI 51 DONE / 40 SKIPPED and WF 451+300+51 DONE rows by
   finite metrics, prediction files and target arrays; do not treat DONE labels as valid.
2. **P5**: v7 manuscript, Chinese internal report + separate Q&A, FYP progress report,
   journal record, README/PPT/notes; preserve historical numbers as old snapshot and add
   the new panel as a separately labelled result.
3. **P6**: rebuild `RETURN_TO_CHATGPT.zip` / `RAW_EVIDENCE.zip`, manifest, validator,
   `SCIENTIFIC_AUDIT.md`, `MESSAGE_TO_CHATGPT.md`; structural PASS must say
   `scientific_readiness: NOT_ASSESSED`.
4. **P7**: numerical-foundation models (Chronos/TimesFM), CDC calendar/vintage,
   JBHI guidance, resource measurements — mark BLOCKED/UNVERIFIED with exact reasons if
   not executable.
