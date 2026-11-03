# -*- coding: utf-8 -*-
"""Append one row to 04_详细说明文档/LEDGER.md (append-only, R2/R3). ASCII-safe: no arrows/em dashes."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "04_详细说明文档", "LEDGER.md")

ROW = (
    "| 2026-11-02 19:25 | **SIX DELIVERABLES BUILT FROM THE MEASURED TABLES, AND A HANDOFF ARCHIVE.** "
    "Generated (not hand-written) by `01_最终报告/_build2/`: `report_internal_{en,zh}.docx/.pdf` "
    "(**18 / 19 pages**), `progress_report_{en,zh}` (**5 / 5**, following "
    "`Requirements_ProjectProgressReport_2627A` PART A + PART B 1,2,3,4,6,7,8 - the template has no "
    "section 5), `ieee_manuscript_{en,zh}` (**5 / 5**, two-column, innovation section an explicit "
    "`% TODO(innovation)` block), plus `01_最终报告/chatgpt_prompt.md`, `MANIFEST.md`, "
    "`PROJECT_HANDOFF.zip` (**2,260,882,336 B = 2,156.1 MB, 5,093 entries, CRC ok**) and "
    "`04_详细说明文档/REPO_HYGIENE.md` + `.gitignore` extensions. Every number is read at build time from "
    "`02_数字表格/*.csv` and asserted in `dlv/06_原始数据集.py` (1.4995 vs 1.4355; PatchTST 1.6621; NLinear "
    "4/16 pass, PTE 1.677 / PIE 9.477; slope +0.1171, R2 0.0223; 211x for 11.2 pct; 204/204 A100), so a "
    "drifting CSV fails the build. **CORRECTION to `04_详细说明文档/HANDOFF_20261102.md` section 2:** its 'paper' "
    "column (1.2946 / 1.4321 / 1.4695 / 1.5457) is wrong; the paper's own Table V "
    "(`reference_papers/MIFlu_..._Scheme.md` lines 249-261, and `02_数字表格/"
    "ESSAY_VS_REPRODUCTION_TABLE_V.csv`) gives **1.542 / 1.422 / 1.414 / 1.364**, which is the only set "
    "that both averages to 1.4355 AND produces the documented 2-2 sign crossover (win L24 -15.4 pct, win "
    "L36 -4.6 pct, lose L48 +17.0 pct, lose L60 +23.4 pct). The handoff's set implies a loss at L24, so it "
    "cannot be the paper's and is superseded here. **Also corrected in the documents:** the aggregate MAE "
    "for L48/L60 is not in the pulled artefact set, so the 4-horizon MAE 0.7597 is reported as partial "
    "(L24/L36 only), and the MIFlu benchmark row is written as *not yet available* rather than approximated "
    "from the reproduction. The 11 LLM arms have no per-arm aggregation in this repo, so Table 8 reports "
    "roster + completion and quotes no accuracy number. Chinese text verified by two independent paths "
    "(python-docx and a LibreOffice re-export): 28,594 / 5,329 / 10,806 chars, CJK ratio 0.488 / 0.607 / "
    "0.416, zero `U+FFFD`, zero mojibake markers; the three Chinese PDFs embed SimSun + MicrosoftYaHei-Bold "
    "subsets. Junk cleanup was a **no-op by rule**: 217 files match `_*.out`/`_*.err`/`*.tmp`/`*.bak.*` but "
    "the oldest is 18.7 h old against a 24 h cutoff, so nothing was deleted; `05_程序代码/clean_junk.py` "
    "implements the rule and refuses the protected directories. No figure was regenerated: all 8 in "
    "`01_最终报告/figures/` were inspected (axes = de-normalised ILITOTAL patients, x = test-set week, GT + "
    "steps 0-3) and reused unchanged. | `01_最终报告/_build2/{build_docs.py,to_pdf.py,verify_docs.py,"
    "make_manifest.py,make_zip.py}`, `_build2/verify/report.txt` (0 failures), `_build2/zip_stats.json`, "
    "`01_最终报告/MANIFEST.md`, `04_详细说明文档/REPO_HYGIENE.md`, `05_程序代码/clean_junk.py`, this file |"
)


def main():
    txt = io.open(P, encoding="utf-8").read()
    if ROW[:40] in txt:
        print("already present; nothing to do")
        return 0
    if not txt.endswith("\n"):
        txt += "\n"
    io.open(P, "w", encoding="utf-8", newline="\n").write(txt + ROW + "\n")
    print("appended 1 row to 04_详细说明文档/LEDGER.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
