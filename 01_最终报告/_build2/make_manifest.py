#!/usr/bin/env python3
"""Measure all eight current bilingual reports."""
from pathlib import Path
import json,hashlib,fitz
from docx import Document
ROOT=Path(__file__).resolve().parents[2]
def build(patch_only=False):
 rows=[]
 for kind in ['report_internal','progress_report','ieee_manuscript','record_for_journal']:
  for lang in ['en','zh']:
   stem=f'{kind}_{lang}';p=ROOT/'01_最终报告'/stem;d=Document(p.with_suffix('.docx'))
   row={'stem':stem,'pages':len(fitz.open(p.with_suffix('.pdf'))),'tables':len(d.tables),'figures':len(d.inline_shapes),'qa_items':sum(p.text.startswith('Q') and p.text[1:3].isdigit() for p in d.paragraphs)}
   for ext in ['docx','pdf']:
    b=p.with_suffix('.'+ext).read_bytes();row[ext+'_bytes']=len(b);row[ext+'_sha256']=hashlib.sha256(b).hexdigest()
   rows.append(row)
 (ROOT/'audit/ARTIFACT_INVENTORY.json').write_text(json.dumps(rows,indent=2)+'\n')
 lines=['# Current integrated artefacts — revision 8','','Historical scientific snapshot: 3 November. Execution: dated 5 November 00:15 HKT owner handoff; no live read. See README.md, audit/EXECUTION_STATUS.md and audit/CHANGES.md.','','| Report | PDF pages | Tables | Figures | Q&A |','|---|---:|---:|---:|---:|']
 lines += [f"| {r['stem']} | {r['pages']} | {r['tables']} | {r['figures']} | {r['qa_items']} |" for r in rows]
 lines += ['','All eight DOCX/PDF pairs are integrated current documents. Internal and journal records preserve Q01–Q25 and 25 references. Original historical scientific tables are preserved, except explicitly declared operational-status cells. Journal records add an evidence register and update policy. The older pre-audit journal files remain in archive/journal_record_before_audit.','','Core artefacts 160/160; national ledger 117/1120 and later owner report 141/1120. Supplied fixed-weight CPU assertions: 3 passed, zero skipped; not rerun here. Ablation queue 60/60 DONE, aggregate analysis pending. No harmonised new leaderboard is claimed.','','PDFs rendered with LibreOffice using Carlito/Noto CJK substitutions. Native Office and human rehearsal not executed. Presentation has 13 slides, native chart workbooks and a 606-word/300-second planned script. Full and compact archive hashes are in the external DELIVERY_MANIFEST.json.']
 (ROOT/'01_最终报告/MANIFEST.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(rows,indent=2));return rows
if __name__=='__main__':build()
