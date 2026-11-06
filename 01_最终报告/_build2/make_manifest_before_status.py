#!/usr/bin/env python3
"""Measure the six current report pairs; never restore legacy scientific prose.

Run from any directory. --patch is accepted for legacy command compatibility;
both modes measure the actual current files. Archive digests belong outside the
archives to avoid self-referential hashes.
"""
from pathlib import Path
import argparse
import hashlib
import json

import fitz
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '01_最终报告'
AUDIT = ROOT / 'audit'
NAMES = [f'{kind}_{lang}' for kind in
         ('report_internal', 'progress_report', 'ieee_manuscript')
         for lang in ('en', 'zh')]


def measure():
    rows = []
    for stem in NAMES:
        word = OUT / (stem + '.docx')
        pdf = OUT / (stem + '.pdf')
        document = Document(word)
        with fitz.open(pdf) as rendered:
            pages = len(rendered)
        rows.append(dict(
            stem=stem, pages=pages, tables=len(document.tables),
            figures=len(document.inline_shapes),
            qa_items=sum(bool(__import__("re").match(r"^Q\d{2}\b", p.text)) for p in document.paragraphs),
            docx_bytes=word.stat().st_size, pdf_bytes=pdf.stat().st_size,
            docx_sha256=hashlib.sha256(word.read_bytes()).hexdigest(),
            pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest()))
    return rows


def build(patch_only=False):
    rows = measure()
    AUDIT.mkdir(exist_ok=True)
    (AUDIT / 'ARTIFACT_INVENTORY.json').write_text(
        json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    lines = [
        '# Reviewed artefact manifest', '',
        'Experimental status: supplied 3 November 2026 snapshot; review based on '
        'the corrected 4 November upload. Counts and hashes below are measured '
        'from the current files whenever this command runs.', '',
        '| File stem | PDF pages | Tables | Figures | DOCX bytes | PDF bytes | DOCX SHA-256 | PDF SHA-256 |',
        '|---|---:|---:|---:|---:|---:|---|---|',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(str(row[k]) for k in (
            'stem', 'pages', 'tables', 'figures', 'docx_bytes', 'pdf_bytes',
            'docx_sha256', 'pdf_sha256')) + ' |')
    lines += [
        '', '## Evidence and execution status', '',
        'Source CSVs remain frozen; hashes are in audit/INPUT_SHA256.json. '
        'The exported adjusted-p column is defective. The separately recomputed '
        'Holm result is 0/136 rejections (128/136 before correction), minimum '
        'adjusted p about 0.0664, and NLinear–PatchTST 0.1172. This is a '
        'resolution/power limitation, not equivalence. The actual 17-model '
        'paired family includes MIFlu and excludes DLinear and all 11 frozen '
        'encoders. The complete roster is 13 conventional + 4 LLM-based + '
        '11 frozen encoders.', '',
        'Archived no-text assertions are present and statically inspected. '
        'Their runtime outcomes are not executed. Archive collection failed; '
        'no reliable archive total or passing suite is claimed. Seven separate '
        'new CPU audit tests passed. Live HPC status and GPU training were not '
        'executed. Exact commands and limitations are in '
        'audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.', '',
        'DOCX/PDF checks and measured counts are recorded in '
        'audit/DOCUMENT_VERIFICATION.json. Chinese PDFs were rendered with '
        'Noto CJK substitutions for requested SimSun/Microsoft YaHei fonts. '
        'Actual glyphs and embedded fonts were checked; '
        'audit/VISUAL_QA.md records the visual review. Native Microsoft Office '
        'inspection is not executed.', '',
        '## Research and document roles', '',
        'The internal report contains twelve continuous sections and twenty-five embedded explanatory questions in each language. Those questions are required supervision material and must not be removed during optimisation. Each now contains paper-based reasoning, an exact reading locator and a supervisor short answer; see QA_CITATION_MAP.md. The school '
        'progress report retains PART A and sections 1, 2, 3, 4, 6, 7, 8. '
        'The manuscript is a single-column review draft with eight tables; '
        'it is not submission-ready. Historical record_for_journal files and '
        'dated operational notes are retained as history.', '',
        'audit/LITERATURE_REVIEW.md records twenty-five primary sources '
        'at explicit reading depths, with URLs and access dates. Unresolved '
        'JBHI/JCR and next-cycle venue facts remain unverified. '
        'audit/DOC_REVIEW.md covers every report and README/manifest role. '
        'audit/GRADE_READINESS.md separates school readiness from '
        'publishability. O1 is the accepted default; optional O2 costs and '
        'conditions are in audit/INNOVATION_DECISION.md.', '',
        '## Presentation', '',
        'presentation/ contains the exact owner-corrected PPTX master, checksum restore command, separate python-pptx alternative, deck_spec.json, '
        'thirteen-slide PPTX and rendered PDF, TALKING_SCRIPT.md and '
        'QA_SHEET.md, Presentation_Notes_EN_ZH.docx/.pdf and the complete supervisor explanation guide. The accepted title names multimodal LLM re-evaluation for influenza forecasting, with four evaluation axes and 28/28/11/17 coverage. The per-slide pacing budget totals 300 seconds. '
        'Speaker notes are embedded. The restored deck is byte-identical to the owner upload. The cover author is CHAN Sing Yeung and the closing deadline line is removed; uploaded slide footers remain unchanged. '
        'Actual human speaking time and native PowerPoint behaviour are '
        'not executed.', '',
        '## Delivery archives', '',
        'The full reviewed project includes frozen data, predictions and the '
        'test archive. The compact bundle contains the reviewed documents, '
        'audits, deck, source CSVs and rebuild code, with raw predictions '
        'excluded. Exact ZIP byte counts, members and SHA-256 are in the '
        'sibling DELIVERY_MANIFEST.json generated after packaging. The '
        'manifest is intentionally outside the ZIPs whose hashes it records.', '',
        '## Rebuild', '', '```bash',
        'python 01_最终报告/_build2/build_revised.py',
        'python 01_最终报告/_build2/to_pdf.py',
        'python 01_最终报告/_build2/verify_docs.py',
        'python 01_最终报告/_build2/make_manifest.py',
        'python presentation/make_deck_spec.py',
        'python presentation/build_deck.py',
        'python presentation/build_notes.py',
        'python presentation/render_presentation.py',
        'python presentation/verify_presentation.py',
        'python scripts/refresh_delivery_docs.py', '```', '',
    ]
    (OUT / 'MANIFEST.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(rows, indent=2))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', action='store_true',
                        help='Compatibility flag; remeasure all current files.')
    args = parser.parse_args()
    build(patch_only=args.patch)
