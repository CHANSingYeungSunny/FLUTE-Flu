#!/usr/bin/env python3
"""Check the actual deck, two chart workbooks, notes, script and restored QA coverage."""
from pathlib import Path
import json,hashlib,re,argparse,zipfile,math
from pptx import Presentation
from docx import Document
import fitz
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent

def verify(repeat=None):
 spec=json.loads((HERE/'deck_spec.json').read_text());path=HERE/'Week12_Progress_Presentation.pptx';prs=Presentation(path);fail=[]
 if len(prs.slides)!=13:fail.append('slide count')
 if sum(s['duration_seconds'] for s in spec['slides'])!=300:fail.append('timing budget')
 if sum(len(s['speaker_notes'].split()) for s in spec['slides'])!=spec['spoken_script_whitespace_words']:fail.append('spoken word count')
 script=(HERE/'TALKING_SCRIPT.md').read_text();note_doc=Document(HERE/'Presentation_Notes_EN_ZH.docx');note_text='\n'.join(p.text for p in note_doc.paragraphs)
 charts=[]
 for q,slide in zip(spec['slides'],prs.slides):
  notes=slide.notes_slide.notes_text_frame.text
  for name in ['speaker_notes','preparation_zh','follow_up_question','follow_up_answer']:
   if q[name] not in notes:fail.append(f"slide {q['id']} missing {name}")
  if q['speaker_notes'] not in script or q['speaker_notes'] not in note_text:fail.append(f"script/notes mismatch {q['id']}")
  for shape in slide.shapes:
   if shape.has_chart:charts.append({'slide':q['id'],'series':[list(s.values) for s in shape.chart.series],'categories':[c.label for c in shape.chart.plots[0].categories]})
 if [c['slide'] for c in charts]!=[4,5]:fail.append('native chart locations')
 else:
  q=spec['slides'][3]
  if any(len(x)!=len(y) or any(not math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(x,y)) for x,y in zip(charts[0]['series'],[q['ours'],q['paper']])):fail.append('reproduction native chart values')
  q=spec['slides'][4]
  if len(charts[1]['series'][0])!=len(q['leaders']) or any(not math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(charts[1]['series'][0],[v['mse'] for v in q['leaders'][::-1]])):fail.append('accuracy native chart values')
 with zipfile.ZipFile(path) as z:
  workbooks=[n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]
  if len(workbooks)!=2:fail.append('embedded chart workbooks')
 for lang in ['en','zh']:
  d=Document(ROOT/'01_最终报告'/('report_internal_qa_zh.docx' if lang=='zh' else 'report_internal_en.docx'));ids=[int(m.group(1)) for p in d.paragraphs if (m:=re.match(r'^Q(\d{2})\b',p.text))]
  if ids!=list(range(1,26)):fail.append('internal Q01–Q25 '+lang)
 with fitz.open(HERE/'Week12_Progress_Presentation.pdf') as pdf:
  if len(pdf)!=13:fail.append('deck PDF count')
 with fitz.open(HERE/'Presentation_Notes_EN_ZH.pdf') as pdf:
  fonts=sorted({f[3] for p in pdf for f in p.get_fonts()});notes_pages=len(pdf);extracted='\n'.join(p.get_text() for p in pdf)
  if not any(re.search(r'CJK|SimSun|YaHei|SourceHan',f,re.I) for f in fonts):fail.append('notes PDF CJK fonts')
  for token in ['中文理解','English script','Slide 13']:
   if token not in extracted:fail.append('notes PDF token '+token)
 qa_count=len(re.findall(r'^## \d+\.',(HERE/'QA_SHEET.md').read_text(),re.M))
 if qa_count!=10:fail.append('ten assessor questions')
 repeated=None
 if repeat is not None:
  repeated=path.read_bytes()==Path(repeat).read_bytes()
  if not repeated:fail.append('repeat bytes differ')
 for rel,sha in spec['source_csv_sha256'].items():
  if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=sha:fail.append('source CSV changed '+rel)
 owner=json.loads((HERE/'source/USER_CORRECTIONS.json').read_text())
 owner_match=hashlib.sha256((HERE/'source'/owner['filename']).read_bytes()).hexdigest()==owner['sha256']
 if not owner_match:fail.append('archived user master changed')
 if 'CHAN Sing Yeung' not in prs.slides[0].shapes[5].text:fail.append('owner cover name')
 if any('School deadline:' in getattr(sh,'text','') for sh in prs.slides[-1].shapes):fail.append('removed closing deadline restored')
 import sys
 sys.path.insert(0,str(ROOT/'01_最终报告/_build2'))
 from qa_literature import SUPPORT
 guide=(HERE/'SUPERVISOR_EXPLANATION_GUIDE.md').read_text();sheet=(HERE/'QA_SHEET.md').read_text()
 for qid,support in SUPPORT.items():
  if support['en'] not in guide or support['zh'] not in guide or support['locator'] not in guide:fail.append(f'guide paper evidence Q{qid:02d}')
 for qid in [24,4,7,12,14,15,20,21,22]:
  if SUPPORT[qid]['en'] not in sheet:fail.append(f'live sheet paper evidence Q{qid:02d}')
 for token in ['Paper basis for the follow-up','References for preparation']:
  if token not in note_text:fail.append('notes missing '+token)
 from io import BytesIO
 from openpyxl import load_workbook
 with zipfile.ZipFile(path) as z:
  workbook_rows={name:list(load_workbook(BytesIO(z.read(name)),data_only=True).active.values) for name in workbooks}
 expected_books=[list(zip(['L'+x for x in spec['slides'][3]['horizons']],spec['slides'][3]['ours'],spec['slides'][3]['paper'])),list(zip([v['name'] for v in spec['slides'][4]['leaders'][::-1]],[v['mse'] for v in spec['slides'][4]['leaders'][::-1]]))]
 for expected in expected_books:
  if not any(len(rows[1:])==len(expected) and all(len(row)==len(want) and all((math.isclose(x,y,rel_tol=0,abs_tol=1e-12) if isinstance(x,(int,float)) and isinstance(y,(int,float)) else x==y) for x,y in zip(row,want)) for row,want in zip(rows[1:],expected)) for rows in workbook_rows.values()):fail.append('embedded workbook values mismatch')
 with zipfile.ZipFile(HERE/'source'/owner['filename']) as original, zipfile.ZipFile(path) as current:
  for name in workbooks:
   if original.read(name)!=current.read(name):fail.append('source workbook bytes changed '+name)
 result={'original_user_master_preserved':owner_match,'current_deck_is_authorised_status_edit':True,'embedded_workbook_values_checked':True,'embedded_workbook_absolute_tolerance':1e-12,'slides':len(prs.slides),'native_charts':charts,'embedded_chart_workbooks':len(workbooks),'matching_bilingual_speaker_notes':13,'planned_seconds':300,'script_whitespace_words':spec['spoken_script_whitespace_words'],'assessor_questions':qa_count,'questions_per_language':25,'qa_location_by_language':{'en':'internal report','zh':'standalone companion'},'literature_backed_internal_questions_per_language':25,'notes_pdf_pages':notes_pages,'notes_pdf_fonts':fonts,'pptx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'repeat_byte_identical':repeated,'failures':fail,'not_executed':['native PowerPoint/Word','actual human rehearsal','independent model-test rerun here','GPU training/live HPC here']}
 (ROOT/'audit/PRESENTATION_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['notes_pdf_fonts','native_charts']},indent=2));return bool(fail)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repeat',type=Path);raise SystemExit(verify(p.parse_args().repeat))
