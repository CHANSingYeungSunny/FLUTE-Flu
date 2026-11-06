# CODE_MAP — how the repository is organised

The full repo is `PROJECT_HANDOFF.zip` (≈165 MB). This pack carries only the files below; the map
tells you what exists elsewhere and where a change would go.

## Top level

```
MLFlu/
  01_最终报告/            deliverable documents, figures, MANIFEST, handoff prompt
  02_数字表格/            every number used in the documents (83 CSVs, this pack has all)
  03_预测数据_证据/       raw predictions (pred_*.npz), per-cell logs, run manifests
  04_详细说明文档/        methodology, ledger, HPC notes, repository hygiene
  05_程序代码/            training/eval/plot scripts (the full tree is in the handoff zip)
  06_原始数据集/           CDC series + scaler_miflu_author966.json
  hpc_experiments/        one-off queue/ops scripts (mostly historical)
  tests/                  pytest suite (≈500 tests; some archived duplicates error on collection)
  Requirements_ProjectProgressReport_2627A (1).pdf   report template
  Appendix II.pdf                                    presentation rubric
```

## The document generator (what produced the six PDFs)

```
01_最终报告/_build2/
  build_docs.py           entry point: writes 6 DOCX, asserts every headline number
  to_pdf.py               DOCX -> PDF via the bundled LibreOffice kit
  verify_docs.py          round-trip + sign-crossover + claim checks (must print FAILURES: 0)
  make_manifest.py        regenerates MANIFEST.md
  make_zip.py             rebuilds the handoff archive
  dlv/
    data.py               SINGLE SOURCE OF NUMBERS; reads 02_数字表格/*.csv; asserts them
    tables.py             every table, built from data.py
    render.py             DOCX rendering kit (styles, tables, figures, auto table numbering)
    text_internal.py      internal report content (12 sections, F0-F5 conclusions)
    text_progress.py      FYP progress report content (sections 1,2,3,4,6,7,8)
    text_ieee.py          manuscript content (sections I-IX, TABLE I-VIII)
```

**Rule:** never type a number into the text. Add/read it in `data.py`, then use it in
`tables.py` / `text_*.py`. The build fails if a headline value drifts.

## Where the numbers come from

```
02_数字表格/
  BENCH_MSE_BY_MODEL_L.csv     28 models x 4 horizons, mse_7var_z / mae_7var_z
  BENCH_PTE_PIE_BY_STEP.csv    28 models x 4 horizons x 4 steps: PTE_wk, PIE_pct, pass
  BENCH_EFFICIENCY.csv         params, Pareto flag, slope, R2
  BENCH_PAIRED_TESTS.csv       136 pairs, sign-flip + Holm
  ESSAY_VS_REPRODUCTION_TABLE_V.csv   the paper's Table V vs ours (MSE and MAE)
  BENCH_SEASONAL_NAIVE.csv     the naive reference (6.2132)
  BENCH_GPU_PROVENANCE.csv     204 A100 cells with job ids
  ... (see data/DATA_DICTIONARY.md)
```

Raw per-window predictions (the ultimate provenance) are `03_预测数据_证据/expanded_runs/**/pred_*.npz`.
They are not in this pack.

## Plotting / analysis entry points (subset)

```
05_程序代码/plot_peak_skill.py    the 28-arm PTE/PIE heat map (this pack includes it)
05_程序代码/plot_pareto.py        Pareto + log-parameter regression
05_程序代码/plot_bench.py         per-model 2x2 forecast panels
05_程序代码/verify_miflu_oracle.py   re-derives the 40 reproduction runs (|Δ| ≤ 1e-5)
05_程序代码/eval_windows.py       the (W//16)*16 window rule
```

## How to rebuild (on the owner's machine, not in this chat)

```
python 01_最终报告/_build2/build_docs.py
python 01_最终报告/_build2/to_pdf.py
python 01_最终报告/_build2/verify_docs.py      # must print FAILURES: 0
python 01_最终报告/_build2/make_manifest.py
python 01_最终报告/_build2/make_zip.py
```

## What is intentionally absent from this pack

- `03_预测数据_证据/**/pred_*.npz` — ≈1 GB of raw predictions; ask for specific cells if needed.
- `05_程序代码/{v3,v3_clean,innovation,...}` — the full training stack; the pack has the document
  generator and the plotting scripts only.
- HPC job logs and queue state — they live on Burgundy, summarised in `04_详细说明文档/LEDGER.md`.
- The 2 November prompt — archived, superseded, and it contains stale numbers.
