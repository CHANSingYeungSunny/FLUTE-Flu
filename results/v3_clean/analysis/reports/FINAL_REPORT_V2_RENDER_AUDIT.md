# FINAL REPORT v2 — RENDER AUDIT

Generated 2026-10-07. Repository commit `5304f9473e8f67b97c23abda1b31775439d5a353`.

**Verdict: PASS — 19 pages, 0 flagged, 0 blank pages, 0 margin overruns, 0 missing
figures, 0 missing captions, 0 broken table rows.**

| | |
|---|---|
| DOCX | `MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_v2.docx` |
| DOCX SHA-256 | `d9f14d3a45a4da88c08fc1d018edea0c8331643aaa919f895c3f4387b33cbd68` |
| DOCX size | 670,113 bytes |
| PDF | `render_v2/…_v2.pdf` |
| PDF SHA-256 | `c017673c383e9774460faf60256ad3f89c792231b006710239a91bcdf4735838` |
| PDF size | 5,172,055 bytes |
| Pages | **19** (Word `ComputeStatistics(2)`) |
| Words | 5,143 |
| Tables | 18 |
| Inline figures | 11 |
| Page size | A4 portrait, 21.0 × 29.7 cm |
| Text frame | 2.3 / 2.3 / 2.2 / 2.2 cm |

---

## 1. Pipeline

```
scripts/build_final_report_v2.py   ->  regenerates all 18 tables and 11 figures
                                       from the frozen CSVs, builds the DOCX
scripts/finalize_docx_v2.py        ->  Word COM: updates TOC + all fields,
                                       saves the DOCX, exports PDF,
                                       renders every page to PNG at 110 dpi
scripts/audit_render_v2.py         ->  per-page ink coverage + content bbox,
                                       flags blank pages and margin overruns
```

The TOC is a real Word field. It is **populated in the shipped DOCX** (the
finalize step calls `TablesOfContents.Update()` and `Fields.Update()` then
saves), so the delivered file does not require the reader to press F9.

---

## 2. Per-page measurements

`ink%` is the share of non-white pixels. `left/right/top/bottom` are the
distances in cm from the page edge to the outermost content pixel.

| page | ink % | left | right | top | bottom | flag |
|---:|---:|---:|---:|---:|---:|---|
| 01 cover | 7.16 | 2.08 | 2.10 | 4.64 | 1.45 | OK |
| 02 TOC (a) | 4.32 | 2.29 | 2.33 | 2.45 | 1.45 | OK |
| 03 TOC (b) | 1.78 | 2.29 | 2.33 | 2.33 | 1.43 | OK |
| 04 §1 + 表1-1 | 10.14 | 2.08 | 2.10 | 2.42 | 1.45 | OK |
| 05 §2–§3 + 图3-1/3-2 | 9.18 | 2.29 | 3.65 | 2.42 | 1.43 | OK |
| 06 §3.1–§3.4 | 9.56 | 2.08 | 2.10 | 2.33 | 1.43 | OK |
| 07 §4.1 + 表4-1 | 14.92 | 2.08 | 2.10 | 2.33 | 1.45 | OK |
| 08 §4.2 + 表4-2 + 图4-1 | 10.56 | 2.08 | 2.10 | 2.42 | 1.43 | OK |
| 09 §4.3 + 表4-3 | 10.61 | 2.08 | 2.10 | 2.42 | 1.43 | OK |
| 10 §5 + 表5-1 | 14.31 | 2.08 | 2.10 | 2.42 | 1.43 | OK |
| 11 §6–§8 + 表7-1/8-1 | 13.07 | 2.08 | 2.10 | 2.19 | 1.45 | OK |
| 12 §9 + 图9-1 | 12.15 | 2.08 | 2.10 | 2.45 | 1.45 | OK |
| 13 §10 + 表10-1 + 图10-1 | 11.30 | 2.08 | 2.10 | 2.38 | 1.43 | OK |
| 14 表10-2 + 图10-2 | 16.51 | 2.08 | 2.10 | 2.31 | 1.45 | OK |
| 15 §10.1–10.2 + 表10-3/10-4 | 11.22 | 2.08 | 2.10 | 2.19 | 1.43 | OK |
| 16 §11–§13 + 表11-1/12-1/13-1 | 14.17 | 2.08 | 2.10 | 2.38 | 1.43 | OK |
| 17 §14–§15 + 表14-1 | 6.14 | 2.29 | 2.40 | 2.42 | 1.45 | OK |
| 18 §16 + 附录 A + 表A-1 | 6.87 | 2.08 | 2.10 | 2.42 | 1.43 | OK |
| 19 附录 B + 表B-1 | 5.72 | 2.08 | 2.10 | 2.42 | 1.43 | OK |

**Minimum ink coverage is 1.78 %** (TOC continuation page), which is normal for
a sparse page. **No page is blank.**

> **Note on the 2.08 / 2.10 columns.** Word indents a table 0.19 cm into the
> gutter by default so that cell *text* lines up with body text. The table
> border therefore sits 0.19 cm closer to the page edge than the declared text
> margin on every table-bearing page. That is standard Word behaviour, not an
> overflow, and the audit tolerance (0.25 cm) accommodates it. All tables are
> also explicitly set to 100 % of the text frame width with a fixed layout, so
> no column can force the table past the margin.

---

## 3. Defects found and fixed during the audit

Four rounds were rendered and inspected. Defects found, with the fix:

| # | defect | page(s) | fix |
|---:|---|---|---|
| 1 | TOC field rendered empty | 3 | `finalize_docx_v2.py` now calls `TablesOfContents.Update()` + `Fields.Update()` and **saves** the DOCX |
| 2 | cover note spilled to a near-blank page 2 | 2 | cover whitespace reduced (2 blank paragraphs before title, 2 after) |
| 3 | cover title wrapped, orphaning 「告」 | 1 | title reduced 26 pt → 20 pt |
| 4 | 图 3-2 title overlapped the column headers | 5 | figure y-limit raised, header row moved, title `pad=24` |
| 5 | 表 10-1 total width 17.0 cm > frame | 13 | widths reduced to 15.6 cm, then converted to frame-relative percentages |
| 6 | 附录 B table broke, leaving a 1-row page | 20 (old) | explicit page break before 附录 B |
| 7 | long SHA-256 strings forced cells wider, table bled past the right margin | 4, 8, 18 | zero-width break opportunities inserted every 16 chars (`brk()`) |
| 8 | document page size was Letter (21.59 cm), not A4 | all | `page_width/page_height` set to 21.0 × 29.7 cm |
| 9 | tables could still bleed when content could not wrap | all | `tblW = 100 %` + fixed layout + proportional `tcW` per column |

After fix 9, the audit reports **0 flagged pages**.

---

## 4. Required QA checklist

| # | requirement | result |
|---:|---|---|
| 1 | render DOCX to PDF and PNG | ✅ 19 pages at 110 dpi |
| 2 | inspect every page | ✅ all 19 measured programmatically; 6 inspected visually (1, 3, 5, 12, 19 and the pre-fix 2) |
| 3 | fix clipping | ✅ none detected |
| 4 | fix table overflow | ✅ 0 tables exceed the frame |
| 5 | fix broken rows | ✅ 附录 B given its own page; headers repeat via `w:tblHeader` |
| 6 | fix blank pages | ✅ minimum ink 1.78 %; no blank page |
| 7 | fix missing captions | ✅ 18 tables + 11 figures all carry a numbered caption |
| 8 | fix missing figures | ✅ 11/11 inline shapes present |
| 9 | fix duplicated text | ✅ none detected |
| 10 | fix incorrect page breaks | ✅ page breaks only at cover / TOC / §16 / 附录 B |
| 11 | fix glyph / font issues | ✅ 微软雅黑 (eastAsia) applied to every run; figures use English labels to avoid CJK glyph dependency |
| 12 | re-render and repeat until clean | ✅ 4 rounds; final round is clean |

---

## 5. Honest limitations of this audit

- The margin/blank-page checks are **geometric**, from rasterised pages. They
  cannot detect semantic problems such as a wrong number in a correct-looking
  table; those are covered by the fact that every value is regenerated from a
  frozen CSV (see `FINAL_REPORT_V2_SOURCE_MANIFEST.csv`).
- Six pages were additionally **viewed** as images (1, 3, 5, 12, 19, and page 2
  of the pre-fix build). The remaining pages were verified by measurement, not
  by eye.
- The audit assumes the declared A4 geometry. If the DOCX is opened on a system
  that substitutes a different default page size, pagination will change.
