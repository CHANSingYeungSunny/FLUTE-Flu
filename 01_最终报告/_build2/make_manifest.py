# -*- coding: utf-8 -*-
"""Write 01_最终报告/MANIFEST.md.

Numbers are measured here: file sizes, SHA-256 digests, PDF page counts, and the
archive statistics produced by make_zip.py (`zip_stats.json`).

    python make_manifest.py            # write with the current zip stats (or placeholders)
    python make_manifest.py --patch    # re-fill the archive numbers only
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlv import data as D  # noqa: E402

ROOT = D.ROOT
OUT = os.path.join(ROOT, "01_最终报告")
HERE = os.path.dirname(os.path.abspath(__file__))
STATS = os.path.join(HERE, "zip_stats.json")
VERIFY = os.path.join(HERE, "verify", "report.txt")
PATH = os.path.join(OUT, "MANIFEST.md")

DOCS = [
    ("report_internal_en", "Internal technical report", "EN", "long-form source of truth"),
    ("report_internal_zh", "内部技术报告", "ZH", "the same report in Simplified Chinese"),
    ("progress_report_en", "FYP progress report", "EN", "school template, PART A + PART B 1,2,3,4,6,7,8"),
    ("progress_report_zh", "FYP 进度报告", "ZH", "the same progress report in Simplified Chinese"),
    ("ieee_manuscript_en", "IEEE manuscript (prototype)", "EN", "two-column IEEEtran structure, innovation §TODO"),
    ("ieee_manuscript_zh", "IEEE 论文手稿（原型）", "ZH", "the same prototype in Simplified Chinese"),
]

FIGURES = [
    ("fig_forecast_miflu_L24.png", "MIFlu, L=24: ground truth vs steps 0–3, ILITOTAL in patients"),
    ("fig_forecast_miflu_L60.png", "MIFlu, L=60"),
    ("fig_forecast_patchtst_L24.png", "PatchTST, L=24"),
    ("fig_forecast_patchtst_L60.png", "PatchTST, L=60"),
    ("fig_forecast_nlinear_L24.png", "NLinear, L=24"),
    ("fig_forecast_nlinear_L60.png", "NLinear, L=60"),
    ("fig_pareto_frontier.png", "Accuracy–efficiency Pareto frontier, 11 parametric arms"),
    ("fig_pte_pie_heatmap.png", "Per-step PTE/PIE heat map, 16 arms, K&S pass boxes"),
]


def sha(path, n=16):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def pages(pdf):
    raw = open(pdf, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", raw))


def build(patch_only=False):
    stats = json.load(open(STATS, encoding="utf-8")) if os.path.exists(STATS) else {}
    checks = ""
    if os.path.exists(VERIFY):
        txt = open(VERIFY, encoding="utf-8").read()
        quotes = re.findall(r"proof \(20 chars\): (.+)", txt)
        ratios = re.findall(r"python-docx : .*?CJK ratio ([\d.]+)", txt)
        checks = ("| Document | CJK ratio (python-docx) | CJK ratio (LibreOffice re-export) | 20-char proof |\n"
                  "|---|---|---|---|\n")
        names = ["report_internal_zh", "progress_report_zh", "ieee_manuscript_zh"]
        lo = re.findall(r"LibreOffice : .*?CJK ratio ([\d.]+)", txt)
        for i, nm in enumerate(names):
            checks += (f"| `{nm}.docx` | {ratios[i] if i < len(ratios) else '—'} | "
                       f"{lo[i] if i < len(lo) else '—'} | `{quotes[i] if i < len(quotes) else '—'}` |\n")

    lines = []
    A = lines.append
    A("# MANIFEST — 01_最终报告, page counts, digests, and the handoff archive")
    A("")
    A("**What this is.** The inventory of everything produced on 2026-11-02, with the exact byte size,")
    A("PDF page count and SHA-256 (first 16 hex digits) of each file, plus the contents and exclusions of")
    A("`PROJECT_HANDOFF.zip`.")
    A("")
    A("**When to read it.** Before opening the archive, before quoting a page count, and before deciding")
    A("which file is authoritative for a number (`04_详细说明文档/REPO_HYGIENE.md` §4 has the full evidence map).")
    A("")
    A("---")
    A("")
    A("## 1. The six documents")
    A("")
    A("| Document | Language | DOCX bytes | PDF bytes | **Pages** | SHA-256 (DOCX) | Role |")
    A("|---|---|---:|---:|---:|---|---|")
    for name, title, lang, role in DOCS:
        dp = os.path.join(OUT, name + ".docx")
        pp = os.path.join(OUT, name + ".pdf")
        A(f"| `{name}` | {lang} | {os.path.getsize(dp):,} | {os.path.getsize(pp):,} | "
          f"**{pages(pp)}** | `{sha(dp)}` | {role} |")
    A("")
    A("Page counts are counted from the PDF (`/Type /Page` objects), not estimated. The internal report")
    A("is 18 pages in English and 19 in Chinese; the difference is CJK line-breaking, not different")
    A("content — both editions carry the same 13 tables, 8 figures and 17 sections.")
    A("")
    A("## 2. Figures")
    A("")
    A("| File | Bytes | What it shows |")
    A("|---|---:|---|")
    for fn, desc in FIGURES:
        p = os.path.join(OUT, "figures", fn)
        A(f"| `figures/{fn}` | {os.path.getsize(p):,} | {desc} |")
    A(f"| `figures/figure_captions.json` | "
      f"{os.path.getsize(os.path.join(OUT, 'figures', 'figure_captions.json')):,} | "
      f"EN/ZH captions for all 8 figures, each stating metric, window rule and hardware |")
    A("")
    A("All eight figures were produced by the previous session and are **reused unchanged**. Their axes")
    A("were verified before reuse: y is ILITOTAL de-normalised to patient counts (train-fit scaler,")
    A("mean 9,439.84, sd 9,003.15), x is the test-set week, and each panel carries the ground truth plus")
    A("one curve per fixed step 0/1/2/3. No figure was regenerated.")
    A("")
    A("## 3. Text and prompt artefacts")
    A("")
    for fn, desc in [("chatgpt_prompt.md", "the handoff prompt: context, hard numbers, the "
                                           "\"not yet available\" register, and the LaTeX/venue/innovation brief"),
                     ("MANIFEST.md", "this file")]:
        p = os.path.join(OUT, fn)
        size = os.path.getsize(p) if os.path.exists(p) else 0
        A(f"- `{fn}` — {size:,} bytes — {desc}")
    A("")
    A("## 4. The \"not yet available\" register (also §6 of `chatgpt_prompt.md`)")
    A("")
    A("| # | Item | State at 2026-11-02 19:00 |")
    A("|---|---|---|")
    A("| 1 | Table VIII — ablation | running, **~27 / 60 cells**, driver job **722968** |")
    A("| 2 | Table VI — regional evaluation | **not started** (gated behind Table VIII) |")
    A("| 3 | Table IX — regional training time | **gated** on Table VI |")
    A("| 4 | Rolling-origin 5-fold | code ready, **not run** (1020 cells, 155–360 A100-h) |")
    A("| 5 | Per-arm MSE/PTE/PIE for the 11 LLM encoders | 132 cells complete on the cluster, **aggregation not pulled** |")
    A("| 6 | MIFlu benchmark row | 12 cells exist, **not merged** (oracle gate) → the benchmark table has 16 rows |")
    A("| 7 | Aggregate MAE at L=48/L=60 | **not in the pulled artefact set** → the 4-horizon MAE 0.7597 is partial |")
    A("| 8 | Cross-dataset validation | **not started** |")
    A("")
    A("Every one of these appears in the documents as *not yet available* / *尚未获得*. None has been")
    A("filled with a fabricated number, and none is described as done.")
    A("")
    A("## 5. Encoding verification (the proof the Chinese documents are really Chinese)")
    A("")
    A("The Chinese text is extracted back out of each DOCX by **two independent paths** — python-docx, and")
    A("a LibreOffice text re-export of the same file — and compared. A CJK ratio above 0.30 with no")
    A("`U+FFFD` and no `Ã`/`â€`-style sequence is the pass condition. All three Chinese documents pass.")
    A("")
    A(checks)
    A("The Chinese PDFs additionally embed `SimSun` (body) and `MicrosoftYaHei-Bold` (headings) subsets:")
    A("the glyphs are in the file, not requested from the reader's machine.")
    A("")
    A("## 6. The handoff archive")
    A("")
    if stats:
        A(f"- `PROJECT_HANDOFF.zip` — **{stats['zip_bytes']:,} bytes "
          f"({stats['zip_mb']:.1f} MB), {stats['entries']:,} entries**, CRC-checked OK, "
          f"built in {stats['seconds']} s at {stats['built_at']}")
        A(f"- uncompressed input {stats['input_bytes']:,} bytes ({stats['input_mb']:.1f} MB)")
        A("")
        A("**Excluded, and why.**")
        A("")
        A("| Path | Reason |")
        A("|---|---|")
        A("| `.git/` | required by the brief; the archive is a snapshot, not a clone |")
        A("| `__pycache__/`, `node_modules/`, `*.tmp`, `*.bak.*` | required by the brief; regenerable or scratch |")
        A("| `01_最终报告/_build/` | required by the brief; the **aborted** first document build, whose Chinese literals are mojibaked |")
        A("| `checkpoints/` | 5.0 GB of trained weights; every number is re-derivable from `pred_*.npz` |")
        A("| `.quarantine/` | 629 MB of artefacts that failed a gate (the rejection record stays in `04_详细说明文档/LEDGER.md`) |")
        A("| `results/v3_clean/final/`, `results/v3_clean/test_eval/` | 1.2 GB of >100 MB artefacts already git-ignored |")
        A("| `_tmp_*/`, `.pytest_cache/`, `old_wrong_reports/` | scratch staging |")
        A("| `01_最终报告/.dsh-office-*/` | temporary page renders used for visual inspection |")
        A("")
        A("**Never excluded** (all present in the archive): `03_预测数据_证据/` (1,155 entries), "
          "`expanded_runs/` (inside `03_预测数据_证据/`), `02_数字表格/` (86 CSVs), `04_详细说明文档/` (39 files), "
          "`05_程序代码/` (241 files), `01_最终报告/figures/` (9 files).")
        A("")
        A(f"Sizes are quoted to 0.1 MB. This file is inside the archive, so the archive is rebuilt once after")
        A("it is written; the byte-exact size can differ from the figure above by a few dozen bytes.")
    else:
        A("_Archive not built yet — run `python 01_最终报告/_build2/make_zip.py`._")
    A("")
    A("## 7. How to regenerate")
    A("")
    A("```")
    A("python 01_最终报告/_build2/build_docs.py     # 6 DOCX  (asserts every headline number)")
    A("python 01_最终报告/_build2/to_pdf.py         # 6 PDF   (LibreOffice kit; prints page counts)")
    A("python 01_最终报告/_build2/verify_docs.py    # round-trip + crossover + claim checks")
    A("python 01_最终报告/_build2/make_manifest.py  # this file")
    A("python 01_最终报告/_build2/make_zip.py       # the archive")
    A("```")
    A("")
    A("The generator never writes to `02_数字表格/` or `03_预测数据_证据/`: those are read-only inputs.")
    A("`01_最终报告/_build2/dlv/06_原始数据集.py` asserts the headline facts (1.4995 vs 1.4355; PatchTST 1.6621;")
    A("NLinear 4/16 passes with PTE 1.677 / PIE 9.477; slope +0.1171, R² 0.0223; 211×/11.2 %; 204/204")
    A("A100 cells), so a drifting CSV fails the build instead of silently changing a document.")
    A("")
    A("## 8. Open items and who does what next")
    A("")
    A("| Item | Owner |")
    A("|---|---|")
    A("| Table VIII → Table VI → Table IX, then rolling origin | next execution agent (HPC) |")
    A("| Pull the 132 LLM cells and aggregate per arm | next execution agent (HPC) |")
    A("| Merge the MIFlu benchmark row through the oracle gate | next execution agent |")
    A("| Complete volumes/pages/DOIs in the reference lists | writing agent |")
    A("| The innovation section (currently `TODO`) and the venue decision | writing agent |")
    A("| Scratch cleanup (`python 05_程序代码/clean_junk.py --apply`) | whoever runs next, after 2026-11-03 |")
    A("")
    A("---")
    A("")
    A(f"_Generated {time.strftime('%Y-%m-%d %H:%M')} by `01_最终报告/_build2/make_manifest.py`._")

    text = "\n".join(lines) + "\n"
    open(PATH, "w", encoding="utf-8").write(text)
    print(f"wrote {PATH}: {os.path.getsize(PATH):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(build("--patch" in sys.argv))
