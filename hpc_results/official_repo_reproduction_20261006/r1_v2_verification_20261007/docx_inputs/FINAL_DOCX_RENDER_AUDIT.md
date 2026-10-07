# FINAL DOCX — RENDER AUDIT

Document: `MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx`
Pages rendered: **8** (Word → PDF → PNG @110 dpi)

## Replacement-document integrity

- original `MIFlu_非LLM与LLM流感预测最终报告_中文版.docx` sha256 `9c573f48fb65e590c7973223d6cb5e0a…` — **UNCHANGED**
- new document sha256 `f41652ff3d108575a9e93d789810f2fd…` — separate file, original not overwritten

## Per-page checks

| page | size (B) | result | notes |
|---:|---:|---|---|
| 1 | 123,169 | PASS | title, summary, track separation — no clipping |
| 2 | 161,922 | PASS | why 966 rows, Train/Val/Test roles, contamination — clean |
| 3 | 134,220 | PASS | strict-containment bullets, window table, cell classification — clean |
| 4 | 123,438 | PASS | main Test ranking table (8 models) + MAE ranking — complete, no clipped cells |
| 5 | 134,374 | PASS | per-horizon table continues with **repeated header**; per-seed ranking table — clean |
| 6 | 151,809 | PASS | pairwise table incl. 11/12 check, group summary, gate, cost — clean |
| 7 | 174,109 | PASS | mmlsquota quota table, other matters, limitations — clean |
| 8 | 76,256 | PASS | final answer section — clean |

## Defects found and repaired

| # | defect | repair |
|---|---|---|
| 1 | per-horizon table split across the page break with **no repeated header row** | set `w:tblHeader` on every table's header row → Word now repeats it on continuation pages |
| 2 | model column too narrow; `官方仓库修正版 MIFlu` wrapped to two lines | explicit column widths set on the ranking, per-horizon and per-seed tables |
| 3 | final-answer sentence repeated the model name twice | text corrected |

Both defects were confirmed fixed by re-rendering and re-inspecting pages 4, 5 and 8.

## Checks that passed without repair

- no missing figures (the report is table-based; no figure is referenced)
- no blank or empty pages
- no blank figure captions
- no clipped or overflowing tables
- no overlapping text
- pagination continuous 1–8
- all five legacy tables regenerated from validated Track C data
- no stale old-MIFlu numbers presented as Track C
- no Validation score presented as the final ranking
- no 1025-row score mixed with 966-row scores
- no unresolved placeholders

## Content verification against the brief

Present: project chronology; why 966 is the paper dataset; Table II 7/7; why 1025 is not; why 676/97/193; Train/Validation/Test roles; why Validation does not choose the champion; why Test does; historical contamination; how strict containment fixes it; corrected MIFlu identity; why stage-6 MIFlu was rejected; 84 re-scored vs 12 retrained; full MSE ranking; full MAE ranking; per-horizon champions; per-seed rankings; best LLM; best non-LLM; overall champion; group summary; corrected pairwise statistics; key validation; costs; GPU-hours; checkpoint and storage strategy; Seasonal Naive distinction; R1-B verdict; F1 supplementary; blocked tables; limitations; and the explicit final answer.
