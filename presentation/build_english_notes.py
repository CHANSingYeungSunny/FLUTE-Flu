#!/usr/bin/env python3
"""English-only preparation notes from the current owner-layout deck and verified Q&A."""
from pathlib import Path
import json,sys,re
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'01_最终报告/_build2'))
from qa_literature import SUPPORT
from internal_qa import QA

def stamp(n):return f'{n//60}:{n%60:02d}'
def build():
 spec=json.loads((HERE/'deck_spec.json').read_text());doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.8)
 for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
  st=doc.styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0);st.font.size=Pt(10.5);st.paragraph_format.space_after=Pt(5)
 doc.styles['Title'].font.size=Pt(23);doc.styles['Heading 1'].font.size=Pt(15);doc.styles['Heading 2'].font.size=Pt(11);doc.styles['Heading 1'].paragraph_format.space_before=Pt(8)
 doc.add_paragraph('Presentation Script and Evidence Notes','Title');doc.add_paragraph(spec['title'],'Heading 1');doc.add_paragraph(spec['subtitle']);doc.add_paragraph('CHAN Sing Yeung')
 doc.add_paragraph('The English script has 606 whitespace-delimited words and a planned duration of 5:00. Read only the script paragraphs during the timed talk. Follow-up answers, paper explanations and references are preparation material outside that budget. Human rehearsal has not been executed.')
 doc.add_paragraph('Scientific results retain the audited historical snapshot. Execution counts are dated to the owner handoff at 5 November 2026 00:15 HKT, not a live cluster reading. This edition changes the preparation language and expands the cited explanations; it adds no experiment result.')
 tb=doc.add_table(rows=1,cols=3);tb.style='Light Shading Accent 1'
 for c,t in zip(tb.rows[0].cells,['Slide','Time','Topic']):c.text=t
 elapsed=0
 for s in spec['slides']:
  start=elapsed;elapsed+=s['duration_seconds'];r=tb.add_row().cells
  for c,t in zip(r,[str(s['id']),stamp(start)+'–'+stamp(elapsed),s['title']]):c.text=t
  for c in r:
   for p in c.paragraphs:
    for run in p.runs:run.font.size=Pt(8.5)
 mapping={1:24,2:10,3:4,4:9,5:10,6:13,7:14,8:15,9:19,10:21,11:22,12:25,13:25};refs=set();elapsed=0
 for s in spec['slides']:
  doc.add_page_break();doc.add_paragraph(f"Slide {s['id']}  {s['title']}",'Heading 1');start=elapsed;elapsed+=s['duration_seconds']
  doc.add_paragraph(f"Planned timing {stamp(start)}–{stamp(elapsed)} ({s['duration_seconds']} seconds)")
  doc.add_paragraph('Spoken script','Heading 2');doc.add_paragraph(s['speaker_notes'])
  doc.add_paragraph('Likely follow-up','Heading 2');p=doc.add_paragraph();p.add_run(s['follow_up_question']).bold=True;doc.add_paragraph(s['follow_up_answer'])
  support=SUPPORT[mapping[s['id']]];refs.update(support['refs'])
  doc.add_paragraph('Paper basis and interpretation','Heading 2');doc.add_paragraph(support['en']);doc.add_paragraph('Reading locator: '+support['locator'])
  doc.add_paragraph('Local evidence','Heading 2')
  for source in s['sources']:
   p=doc.add_paragraph(source)
   for run in p.runs:run.font.size=Pt(8.5)
 doc.add_page_break();doc.add_paragraph('References for preparation','Heading 1')
 doc.add_paragraph('Reference numbers follow the internal report and slide preparation notes. The rewritten journal manuscript has its own citation order.')
 original=Document(ROOT/'01_最终报告/report_internal_en.docx');ref_text={int(m[1]):m[2] for p in original.paragraphs if (m:=re.match(r'^\[(\d+)\]\s*(.*)',p.text))}
 for n in sorted(refs):
  p=doc.add_paragraph(f'[{n}] '+ref_text[n])
  for run in p.runs:run.font.size=Pt(9)
 footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT;footer.add_run('English preparation notes 9   ')
 field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
 doc.core_properties.author=spec['author'];doc.core_properties.title='English presentation script and evidence notes';doc.save(HERE/'Presentation_Notes_EN.docx')
 # English live questions retain full paper arguments and reference locators.
 qa=(HERE/'QA_SHEET.md').read_text();qa='\n'.join(x for x in qa.splitlines() if not re.search('[\u4e00-\u9fff]',x));qa=qa.replace('Chinese lines are preparation aids. ','')
 (HERE/'QA_SHEET_EN.md').write_text(qa+'\n')
 guide=['# English supervisor explanation guide','','Reference numbering follows the internal report. Each answer retains its named-paper reasoning and reading locator.','']
 for qid,section,en,zh,ea,za,source in QA:
  s=SUPPORT[qid];guide += [f'## Q{qid:02d}  {en}','','**Answer and local evidence.** '+ea,'','**Paper-based reasoning.** '+s['en'],'','**Supervisor short answer.** '+s['oral_en'],'','Reading locator: '+s['locator'],'','Local evidence: '+source,'']
 guide += ['## References','']+[f'[{n}] '+ref_text[n] for n in sorted(ref_text)]
 (HERE/'SUPERVISOR_EXPLANATION_GUIDE_EN.md').write_text('\n'.join(guide)+'\n')
 assert elapsed==300 and sum(len(s['speaker_notes'].split()) for s in spec['slides'])==606
 print('English notes built; script 606 words, 300 planned seconds; 25 full English explanations retained.')
if __name__=='__main__':build()
