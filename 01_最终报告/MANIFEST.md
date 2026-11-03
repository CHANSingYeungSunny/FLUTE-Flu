# MANIFEST — 01_最终报告, page counts, digests, and the handoff archive

**What this is.** The inventory of everything produced on 2026-11-02, with the exact byte size,
PDF page count and SHA-256 (first 16 hex digits) of each file, plus the contents and exclusions of
`PROJECT_HANDOFF.zip`.

**When to read it.** Before opening the archive, before quoting a page count, and before deciding
which file is authoritative for a number (`04_详细说明文档/REPO_HYGIENE.md` §4 has the full evidence map).

---

## 1. The six documents

| Document | Language | DOCX bytes | PDF bytes | **Pages** | SHA-256 (DOCX) | Role |
|---|---|---:|---:|---:|---|---|
| `report_internal_en` | EN | 4,235,284 | 1,968,384 | **19** | `b18874dc188e5d8a` | long-form source of truth |
| `report_internal_zh` | ZH | 4,236,204 | 2,280,725 | **20** | `b1649d1016be4df6` | the same report in Simplified Chinese |
| `progress_report_en` | EN | 570,690 | 488,583 | **7** | `a10612eed18b19bd` | school template, PART A + PART B 1,2,3,4,6,7,8 |
| `progress_report_zh` | ZH | 570,574 | 656,040 | **8** | `55a296c521d663cc` | the same progress report in Simplified Chinese |
| `ieee_manuscript_en` | EN | 646,102 | 651,634 | **7** | `8ed4b91803e95082` | two-column IEEEtran structure, innovation §TODO |
| `ieee_manuscript_zh` | ZH | 646,886 | 937,080 | **8** | `0c5e7413e1ed24fd` | the same prototype in Simplified Chinese |

Page counts are counted from the PDF (`/Type /Page` objects), not estimated. The internal report
is 18 pages in English and 19 in Chinese; the difference is CJK line-breaking, not different
content — both editions carry the same 13 tables, 8 figures and 17 sections.

## 2. Figures

| File | Bytes | What it shows |
|---|---:|---|
| `figures/fig_forecast_miflu_L24.png` | 146,378 | MIFlu, L=24: ground truth vs steps 0–3, ILITOTAL in patients |
| `figures/fig_forecast_miflu_L60.png` | 136,164 | MIFlu, L=60 |
| `figures/fig_forecast_patchtst_L24.png` | 143,529 | PatchTST, L=24 |
| `figures/fig_forecast_patchtst_L60.png` | 132,314 | PatchTST, L=60 |
| `figures/fig_forecast_nlinear_L24.png` | 142,936 | NLinear, L=24 |
| `figures/fig_forecast_nlinear_L60.png` | 134,741 | NLinear, L=60 |
| `figures/fig_pareto_frontier.png` | 167,545 | Accuracy–efficiency Pareto frontier, 11 parametric arms |
| `figures/fig_pte_pie_heatmap.png` | 187,468 | Per-step PTE/PIE heat map, 16 arms, K&S pass boxes |
| `figures/figure_captions.json` | 10,520 | EN/ZH captions for all 8 figures, each stating metric, window rule and hardware |

All eight figures were produced by the previous session and are **reused unchanged**. Their axes
were verified before reuse: y is ILITOTAL de-normalised to patient counts (train-fit scaler,
mean 9,439.84, sd 9,003.15), x is the test-set week, and each panel carries the ground truth plus
one curve per fixed step 0/1/2/3. No figure was regenerated.

## 3. Text and prompt artefacts

- `chatgpt_prompt.md` — 13,668 bytes — the handoff prompt: context, hard numbers, the "not yet available" register, and the LaTeX/venue/innovation brief
- `MANIFEST.md` — 8,254 bytes — this file

## 4. The "not yet available" register (also §6 of `chatgpt_prompt.md`)

| # | Item | State at 2026-11-02 19:00 |
|---|---|---|
| 1 | Table VIII — ablation | running, **~27 / 60 cells**, driver job **722968** |
| 2 | Table VI — regional evaluation | **not started** (gated behind Table VIII) |
| 3 | Table IX — regional training time | **gated** on Table VI |
| 4 | Rolling-origin 5-fold | code ready, **not run** (1020 cells, 155–360 A100-h) |
| 5 | Per-arm MSE/PTE/PIE for the 11 LLM encoders | 132 cells complete on the cluster, **aggregation not pulled** |
| 6 | MIFlu benchmark row | 12 cells exist, **not merged** (oracle gate) → the benchmark table has 16 rows |
| 7 | Aggregate MAE at L=48/L=60 | **not in the pulled artefact set** → the 4-horizon MAE 0.7597 is partial |
| 8 | Cross-dataset validation | **not started** |

Every one of these appears in the documents as *not yet available* / *尚未获得*. None has been
filled with a fabricated number, and none is described as done.

## 5. Encoding verification (the proof the Chinese documents are really Chinese)

The Chinese text is extracted back out of each DOCX by **two independent paths** — python-docx, and
a LibreOffice text re-export of the same file — and compared. A CJK ratio above 0.30 with no
`U+FFFD` and no `Ã`/`â€`-style sequence is the pass condition. All three Chinese documents pass.

| Document | CJK ratio (python-docx) | CJK ratio (LibreOffice re-export) | 20-char proof |
|---|---|---|---|
| `report_internal_zh.docx` | 0.314 | 0.314 | `ader只覆盖7个变量中的1个（bug）` |
| `progress_report_zh.docx` | 0.309 | 0.308 | `lu代表LLM方法：用LoRA适配器在C` |
| `ieee_manuscript_zh.docx` | 0.311 | 0.311 | `文献的默认排序指标仍是MSE，模型选择也` |

The Chinese PDFs additionally embed `SimSun` (body) and `MicrosoftYaHei-Bold` (headings) subsets:
the glyphs are in the file, not requested from the reader's machine.

## 6. The handoff archive

- `PROJECT_HANDOFF.zip` — **181,882,561 bytes (173.5 MB), 1,585 entries**, CRC-checked OK, built in 11.9 s at 2026-11-03 05:13:53
- uncompressed input 321,080,273 bytes (306.2 MB)

**Excluded, and why.**

| Path | Reason |
|---|---|
| `.git/` | required by the brief; the archive is a snapshot, not a clone |
| `__pycache__/`, `node_modules/`, `*.tmp`, `*.bak.*` | required by the brief; regenerable or scratch |
| `01_最终报告/_build/` | required by the brief; the **aborted** first document build, whose Chinese literals are mojibaked |
| `checkpoints/` | 5.0 GB of trained weights; every number is re-derivable from `pred_*.npz` |
| `.quarantine/` | 629 MB of artefacts that failed a gate (the rejection record stays in `04_详细说明文档/LEDGER.md`) |
| `results/v3_clean/final/`, `results/v3_clean/test_eval/` | 1.2 GB of >100 MB artefacts already git-ignored |
| `_tmp_*/`, `.pytest_cache/`, `old_wrong_reports/` | scratch staging |
| `01_最终报告/.dsh-office-*/` | temporary page renders used for visual inspection |

**Never excluded** (all present in the archive): `03_预测数据_证据/` (1,155 entries), `expanded_runs/` (inside `03_预测数据_证据/`), `02_数字表格/` (86 CSVs), `04_详细说明文档/` (39 files), `05_程序代码/` (241 files), `01_最终报告/figures/` (9 files).

Sizes are quoted to 0.1 MB. This file is inside the archive, so the archive is rebuilt once after
it is written; the byte-exact size can differ from the figure above by a few dozen bytes.

## 7. How to regenerate

```
python 01_最终报告/_build2/build_docs.py     # 6 DOCX  (asserts every headline number)
python 01_最终报告/_build2/to_pdf.py         # 6 PDF   (LibreOffice kit; prints page counts)
python 01_最终报告/_build2/verify_docs.py    # round-trip + crossover + claim checks
python 01_最终报告/_build2/make_manifest.py  # this file
python 01_最终报告/_build2/make_zip.py       # the archive
```

The generator never writes to `02_数字表格/` or `03_预测数据_证据/`: those are read-only inputs.
`01_最终报告/_build2/dlv/06_原始数据集.py` asserts the headline facts (1.4995 vs 1.4355; PatchTST 1.6621;
NLinear 4/16 passes with PTE 1.677 / PIE 9.477; slope +0.1171, R² 0.0223; 211×/11.2 %; 204/204
A100 cells), so a drifting CSV fails the build instead of silently changing a document.

## 8. Open items and who does what next

| Item | Owner |
|---|---|
| Table VIII → Table VI → Table IX, then rolling origin | next execution agent (HPC) |
| Pull the 132 LLM cells and aggregate per arm | next execution agent (HPC) |
| Merge the MIFlu benchmark row through the oracle gate | next execution agent |
| Complete volumes/pages/DOIs in the reference lists | writing agent |
| The innovation section (currently `TODO`) and the venue decision | writing agent |
| Scratch cleanup (`python 05_程序代码/clean_junk.py --apply`) | whoever runs next, after 2026-11-03 |

---

_Generated 2026-11-03 05:27 by `01_最终报告/_build2/make_manifest.py`._
