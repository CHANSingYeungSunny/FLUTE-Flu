# -*- coding: utf-8 -*-
"""Build 01_最终报告/CHATGPT_CONTEXT_PACK.zip — a small, curated handoff.

The full repo is 165 MB and cannot be read by a chat assistant in one go.  This
pack carries everything needed to reason about the project: the six PDFs, all
CSVs, the key figures, the methodology notes, the document generator, the
plotting script, the two school PDFs, the prompt, and a generated data
dictionary.  Raw predictions and the full training tree stay in
PROJECT_HANDOFF.zip.

    python 01_最终报告/_build2/make_context_pack.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "01_最终报告", "CHATGPT_CONTEXT_PACK.zip")

DOCS = [
    ("01_最终报告/report_internal_en.pdf", "docs/report_internal_en.pdf"),
    ("01_最终报告/report_internal_zh.pdf", "docs/report_internal_zh.pdf"),
    ("01_最终报告/progress_report_en.pdf", "docs/progress_report_en.pdf"),
    ("01_最终报告/progress_report_zh.pdf", "docs/progress_report_zh.pdf"),
    ("01_最终报告/ieee_manuscript_en.pdf", "docs/ieee_manuscript_en.pdf"),
    ("01_最终报告/ieee_manuscript_zh.pdf", "docs/ieee_manuscript_zh.pdf"),
    ("Requirements_ProjectProgressReport_2627A (1).pdf",
     "docs/Requirements_ProjectProgressReport_2627A.pdf"),
    ("Appendix II.pdf", "docs/Appendix_II.pdf"),
]

FIGURES = [
    "fig_pte_pie_heatmap.png", "fig_ks_ranking.png", "fig_pareto_frontier.png",
    "fig_forecast_miflu_L24.png", "fig_forecast_patchtst_L24.png",
    "fig_forecast_nlinear_L24.png",
]

NOTES = [
    ("04_详细说明文档/METHODOLOGY_METRICS_AND_SPLIT.md", "notes/METHODOLOGY_METRICS_AND_SPLIT.md"),
    ("04_详细说明文档/REPO_HYGIENE.md", "notes/REPO_HYGIENE.md"),
    ("04_详细说明文档/REPRODUCTION_BENCHMARK_COMPARISON.md",
     "notes/REPRODUCTION_BENCHMARK_COMPARISON.md"),
    ("04_详细说明文档/HPC_RESULTS_ROUND3.md", "notes/HPC_RESULTS_ROUND3.md"),
]

CODE = [
    ("01_最终报告/_build2/build_docs.py", "code/build_docs.py"),
    ("01_最终报告/_build2/to_pdf.py", "code/to_pdf.py"),
    ("01_最终报告/_build2/verify_docs.py", "code/verify_docs.py"),
    ("01_最终报告/_build2/make_manifest.py", "code/make_manifest.py"),
    ("01_最终报告/_build2/make_zip.py", "code/make_zip.py"),
    ("01_最终报告/_build2/dlv/data.py", "code/dlv/data.py"),
    ("01_最终报告/_build2/dlv/tables.py", "code/dlv/tables.py"),
    ("01_最终报告/_build2/dlv/render.py", "code/dlv/render.py"),
    ("01_最终报告/_build2/dlv/text_internal.py", "code/dlv/text_internal.py"),
    ("01_最终报告/_build2/dlv/text_progress.py", "code/dlv/text_progress.py"),
    ("01_最终报告/_build2/dlv/text_ieee.py", "code/dlv/text_ieee.py"),
    ("05_程序代码/plot_peak_skill.py", "code/plot_peak_skill.py"),
    ("05_程序代码/plot_pareto.py", "code/plot_pareto.py"),
    ("tests_archive/test_miflu_ablations.py", "tests_archive/test_miflu_ablations.py"),
    ("tests_archive/README.md", "tests_archive/README.md"),
]

MISC = [
    ("01_最终报告/chatgpt_prompt.md", "chatgpt_prompt.md"),
    ("01_最终报告/MANIFEST.md", "MANIFEST.md"),
    ("README.md", "README_root.md"),
    ("01_最终报告/README_报告说明.md", "README_reports_zh.md"),
    ("01_最终报告/_build2/context/00_START_HERE.md", "00_START_HERE.md"),
    ("01_最终报告/_build2/context/CODE_MAP.md", "code/CODE_MAP.md"),
]

KEY_COLUMNS = """\
| Column | Meaning |
|---|---|
| `mse_7var_z` / `mae_7var_z` | 7-variable aggregate MSE/MAE in standardised (z) space; the accuracy metric |
| `PTE_wk` | peak-timing error in weeks (K&S half 1; pass ≤ 1) |
| `PIE_pct` | peak-intensity error as % of the observed peak (K&S half 2; pass ≤ 25) |
| `kramer_shaman_pass` | True only if BOTH halves hold in the same (model, horizon, step) cell |
| `p_holm` | Holm–Bonferroni corrected p over all 136 model pairs |
| `effect_d` | Cohen's d for the paired difference |
| `on_pareto` | True if no other model has both lower MSE and fewer parameters |
| `params` | trained parameter count (blank for classical learners and MIFlu) |
| `rel_improve_vs_seasonal_pct` | % MSE improvement over the 52-week seasonal-naive baseline |
"""


def data_dictionary(pt_dir):
    lines = ["# DATA_DICTIONARY — every CSV in `02_数字表格/`", "",
             "One row per file: rows × columns and the column names. All files are UTF-8 CSV with a",
             "header. `02_数字表格/README.md` (in the full repo) describes the older exports.", "",
             "## Key columns", "", KEY_COLUMNS, "## Files", "",
             "| File | Rows | Cols | Columns |", "|---|---:|---:|---|"]
    for fn in sorted(os.listdir(pt_dir)):
        if not fn.lower().endswith(".csv"):
            continue
        p = os.path.join(pt_dir, fn)
        try:
            df = pd.read_csv(p)
        except Exception as exc:                       # pragma: no cover
            lines.append(f"| `{fn}` | — | — | unreadable: {exc} |")
            continue
        cols = ", ".join(f"`{c}`" for c in df.columns[:14])
        if len(df.columns) > 14:
            cols += f", … (+{len(df.columns) - 14})"
        lines.append(f"| `{fn}` | {len(df):,} | {len(df.columns)} | {cols} |")
    lines += ["", "## Provenance", "",
              "Every value is re-derivable from the raw predictions in",
              "`03_预测数据_证据/expanded_runs/**/pred_*.npz` (not in this pack), except the",
              "reproduction table, which is gated against the per-seed oracle at |Δ| ≤ 1e-5 by",
              "`05_程序代码/verify_miflu_oracle.py`.", ""]
    return "\n".join(lines)


def main() -> int:
    missing = []
    for src, _ in DOCS + NOTES + CODE + MISC:
        if not os.path.exists(os.path.join(ROOT, src)):
            missing.append(src)
    if missing:
        print("missing inputs:")
        for m in missing:
            print("  ", m)
        return 1

    stage = tempfile.mkdtemp(prefix="ctxpack_")
    pack = os.path.join(stage, "CHATGPT_CONTEXT_PACK")
    os.makedirs(pack)

    def copy(src, dst):
        full = os.path.join(pack, dst)
        os.makedirs(os.path.dirname(full) or pack, exist_ok=True)
        shutil.copy2(os.path.join(ROOT, src), full)

    for src, dst in DOCS + NOTES + CODE + MISC:
        copy(src, dst)
    for fn in FIGURES:
        copy(f"01_最终报告/figures/{fn}", f"figures/{fn}")
    for fn in sorted(os.listdir(os.path.join(ROOT, "02_数字表格"))):
        if fn.lower().endswith(".csv"):
            copy(f"02_数字表格/{fn}", f"data/{fn}")
    with open(os.path.join(pack, "data", "DATA_DICTIONARY.md"), "w", encoding="utf-8") as fh:
        fh.write(data_dictionary(os.path.join(ROOT, "02_数字表格")))

    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dirpath, _, files in os.walk(pack):
            for fn in sorted(files):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, stage).replace(os.sep, "/")
                z.write(full, arcname=rel)

    size = os.path.getsize(OUT)
    with zipfile.ZipFile(OUT) as z:
        n = len(z.namelist())
        bad = z.testzip()
    print(f"wrote {OUT}")
    print(f"  {size:,} bytes ({size / 1024 / 1024:.1f} MB), {n} entries, CRC {'OK' if bad is None else 'BAD'}")
    shutil.rmtree(stage, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
