# -*- coding: utf-8 -*-
"""TASK 7 v8 verification: convert + page-count + hash + log.

Re-runs the exact LibreOffice-kit CLI `convert` command (same pattern as
build_v7_*.py) with full stdout/stderr capture so any PDF-conversion failure is
logged with the EXACT error. Counts PDF pages with the same kit's `render`
subcommand (`--pages 1` returns the total `pageCount` via pdfium). Computes
SHA-256 for all six outputs, validates each DOCX with python-docx, and writes:
  - 01_最终报告/v8/PDF_CONVERSION_LOG.md
  - HANDOFF_20261105/v8/docs/V8_BUILD_RESULTS.json
Nothing outside these v8 paths is written; no frozen file is touched.
"""
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from docx import Document

ROOT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu")
OUT = ROOT / "01_最终报告" / "v8"
DOCS = ROOT / "HANDOFF_20261105" / "v8" / "docs"
NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")

NAMES = ["ieee_manuscript_en_v8", "report_internal_zh_v8", "report_internal_qa_zh_v8"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


results = {}
for name in NAMES:
    docx = OUT / (name + ".docx")
    pdf = OUT / (name + ".pdf")
    entry = {"docx": str(docx.relative_to(ROOT)).replace("\\", "/"),
             "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/")}

    # DOCX structural validation (python-docx 1.2.0).
    if docx.exists():
        d = Document(docx)
        entry["docx_bytes"] = docx.stat().st_size
        entry["docx_sha256"] = sha256(docx)
        entry["docx_paragraphs"] = len(d.paragraphs)
        entry["docx_tables"] = len(d.tables)
        entry["docx_headings"] = sum(
            1 for p in d.paragraphs if p.style.name.startswith("Heading"))
    else:
        entry["docx_bytes"] = 0
        entry["docx_sha256"] = None
        entry["error"] = "DOCX_MISSING"

    # Exact convert command, full capture (same CLI pattern as v7 builders).
    cmd = [NODE, CLI, "convert", "--input", str(docx), "--output", str(pdf)]
    if pdf.exists():
        pdf.unlink()
    conv = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    entry["convert_command"] = " ".join(cmd)
    entry["convert_rc"] = conv.returncode
    entry["convert_stdout"] = conv.stdout.strip()
    entry["convert_stderr"] = conv.stderr.strip()
    entry["convert_exit_code"] = conv.returncode

    if pdf.exists():
        entry["pdf_bytes"] = pdf.stat().st_size
        entry["pdf_sha256"] = sha256(pdf)
        # Authoritative page count via the same kit (pdfium render --pages 1).
        render_dir = Path(tempfile.gettempdir()) / ("mlflu_v8_pages_" + name)
        if render_dir.exists():
            shutil.rmtree(render_dir, ignore_errors=True)
        rcmd = [NODE, CLI, "render", "--input", str(pdf),
                "--output-dir", str(render_dir), "--pages", "1", "--dpi", "36"]
        rr = subprocess.run(rcmd, capture_output=True, text=True, errors="replace")
        entry["pagecount_command"] = " ".join(rcmd)
        entry["pagecount_rc"] = rr.returncode
        try:
            rj = json.loads(rr.stdout)
            entry["pdf_pages"] = rj.get("pageCount")
            entry["pagecount_backend"] = rj.get("rasterEngine")
            entry["pagecount_source_sha256"] = rj.get("sourceSha256")
        except Exception:
            entry["pdf_pages"] = None
            entry["pagecount_error"] = (rr.stdout + " | " + rr.stderr).strip()
        shutil.rmtree(render_dir, ignore_errors=True)
    else:
        entry["pdf_bytes"] = 0
        entry["pdf_sha256"] = None
        entry["pdf_pages"] = 0
        entry["convert_failed"] = True
        entry["exact_error"] = (conv.stdout + " | " + conv.stderr).strip() or \
            "convert rc=%d, no PDF produced" % conv.returncode

    results[name] = entry

# Machine-readable results for T7_VERDICT.
payload = {"generated_utc": utc(),
           "python_docx": "1.2.0",
           "node_cli": "libreoffice-kit cli.js (DeepSeek Harness)",
           "convert_command_pattern": "node cli.js convert --input <docx> --output <pdf>",
           "pagecount_method": "node cli.js render --input <pdf> --output-dir <fresh> --pages 1 --dpi 36 -> JSON pageCount (pdfium)",
           "documents": results}
(DOCS / "V8_BUILD_RESULTS.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

# Human-readable conversion log.
lines = [
    "# V8 PDF conversion log — TASK 7 (2026-11-06)",
    "",
    "Exact toolchain: `python-docx 1.2.0` builds the DOCX; the prepared "
    "LibreOffice-kit CLI converts DOCX->PDF; the same kit's `render` "
    "subcommand (pdfium) reports the total `pageCount` even with `--pages 1`. "
    "Conversion was re-run here with full stdout/stderr capture so any failure "
    "is logged with the exact error. A structural validator PASS is "
    "`scientific_readiness: NOT_ASSESSED`.",
    "",
    "- NODE: `" + NODE + "`",
    "- CLI: `" + CLI + "`",
    "- convert command pattern: `node cli.js convert --input <docx> --output <pdf>`",
    "- page-count command pattern: "
    "`node cli.js render --input <pdf> --output-dir <fresh-dir> --pages 1 --dpi 36`",
    "- generated_utc: " + payload["generated_utc"],
    "",
    "## Per-document results",
    "",
]
for name in NAMES:
    e = results[name]
    lines += [
        "### " + name,
        "",
        "- DOCX: `" + e["docx"] + "` — bytes " + str(e["docx_bytes"]) +
        ", sha256 `" + str(e["docx_sha256"]) + "`, paragraphs " +
        str(e.get("docx_paragraphs")) + ", tables " + str(e.get("docx_tables")) +
        ", headings " + str(e.get("docx_headings")),
        "- convert command: `" + e["convert_command"] + "`",
        "- convert exit code: **" + str(e["convert_rc"]) + "**; stdout: `" +
        e["convert_stdout"] + "`; stderr: `" + e["convert_stderr"] + "`",
    ]
    if e.get("convert_failed"):
        lines += ["- **PDF CONVERSION FAILED — EXACT ERROR:** " + e["exact_error"]]
    else:
        lines += [
            "- PDF: `" + e["pdf"] + "` — bytes " + str(e["pdf_bytes"]) +
            ", sha256 `" + str(e["pdf_sha256"]) + "`",
            "- page-count command: `" + e["pagecount_command"] + "`",
            "- **PDF page count: " + str(e["pdf_pages"]) + "** (backend " +
            str(e.get("pagecount_backend")) + ", rc=" + str(e["pagecount_rc"]) + ")",
        ]
        if e.get("pagecount_error"):
            lines += ["- page-count parse error: " + e["pagecount_error"]]
    lines.append("")

lines += [
    "## Summary",
    "",
    "| Document | DOCX bytes | PDF bytes | convert rc | PDF pages |",
    "|---|---:|---:|---:|---:|",
]
for name in NAMES:
    e = results[name]
    lines.append("| " + name + " | " + str(e["docx_bytes"]) + " | " +
                 str(e["pdf_bytes"]) + " | " + str(e["convert_rc"]) + " | " +
                 str(e.get("pdf_pages", e.get("pdf_pages", 0))) + " |")
lines += [
    "",
    "No PDF was faked. If a conversion had failed, the exact error above would "
    "name the reason and no PDF page count would be reported. The manuscript is "
    "NOT called submission-ready.",
]
(OUT / "PDF_CONVERSION_LOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({"generated_utc": payload["generated_utc"],
                  "pages": {n: results[n].get("pdf_pages") for n in NAMES},
                  "convert_rc": {n: results[n]["convert_rc"] for n in NAMES}},
                 ensure_ascii=False))
