#!/usr/bin/env python3
"""Portable verification of the revised DOCX/PDF text, sections and key values.
Visual review is separate. No claim that this replaces the original model tests.
"""
from pathlib import Path
import re,json
from docx import Document
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'01_最终报告'
def main():
 try:import fitz
 except ImportError:raise SystemExit('Install pymupdf for independent PDF text verification.')
 checks=[];fail=[]
 for kind in ['report_internal','progress_report','ieee_manuscript','record_for_journal']:
  for lang in ['en','zh']:
   name=f'{kind}_{lang}';d=Document(OUT/(name+'.docx'));txt='\n'.join([p.text for p in d.paragraphs]+[c.text for t in d.tables for row in t.rows for c in row.cells]);pdf=fitz.open(OUT/(name+'.pdf'));pdftext='\n'.join(x.get_text() for x in pdf)
   cjk=lambda s:sum('\u4e00'<=x<='\u9fff' for x in s)/max(1,len(''.join(s.split())))
   if 'CHAN Sing Yeung Sunny' in txt or d.core_properties.author!='CHAN Sing Yeung':fail.append(name+' old formal author')
   if 'CHAN Sing Yeung' not in txt or 'CHAN Sing Yeung' not in pdftext:fail.append(name+' corrected author absent')
   row={'document':name,'pages':len(pdf),'tables':len(d.tables),'figures':len(d.inline_shapes),'cjk_ratio_docx':cjk(txt),'cjk_ratio_pdf':cjk(pdftext)}
   for token in ['1.4995','1.4355','0.8043','0.7452','1.5574','1.6621','1.8716','0.1172','60/60']:
    if token=='60/60' and name=='ieee_manuscript_en':continue
    if token not in txt:fail.append(name+' missing DOCX '+token)
   for token in ['1.4995','1.5574','0.1172']:
    if token not in pdftext:fail.append(name+' missing PDF '+token)
   if lang=='zh' and (cjk(txt)<=.30 or cjk(pdftext)<=.30):fail.append(name+' CJK ratio below .30 or missing glyphs')
   fonts=sorted({f[3] for page in pdf for f in page.get_fonts()});row['embedded_font_names']=fonts
   if lang=='zh' and not any(re.search(r'CJK|SimSun|YaHei|DroidSansFallback|SourceHan',f,re.I) for f in fonts):fail.append(name+' no embedded CJK font; extraction alone is insufficient')
   if any(x in txt for x in ['109 of 136','0.1143','exactly reversed','pure noise','asserted by tests/test_miflu_ablations']):fail.append(name+' stale claim')
   if kind=='progress_report':
    nums=[int(x.group(1)) for p in d.paragraphs if p.style.name.startswith('Heading') and (x:=re.match(r'^(\d+)\.',p.text))]
    if nums!=[1,2,3,4,6,7,8]:fail.append(name+' template numbering '+str(nums))
    if not 7<=len(pdf)<=9:fail.append(name+' outside 7–9 page target')
   if kind in ['report_internal','record_for_journal']:
    nums=[int(x.group(1)) for p in d.paragraphs if p.style.name=='Heading 1' and (x:=re.match(r'^(\d+)\s',p.text))]
    if nums!=list(range(1,16) if kind=='record_for_journal' else range(1,13)):fail.append(name+' internal sections '+str(nums))
    qd=d;qt=txt;qp=pdftext
    if name=='report_internal_zh':
     main_questions=[p.text for p in d.paragraphs if re.match(r'^Q\d{2}\b',p.text)]
     if main_questions:fail.append(name+' Q&A not separated')
     qd=Document(OUT/'report_internal_qa_zh.docx');qt='\n'.join(p.text for p in qd.paragraphs)
     with fitz.open(OUT/'report_internal_qa_zh.pdf') as qpdf:qp='\n'.join(p.get_text() for p in qpdf);row['qa_companion_pages']=len(qpdf)
    questions=[int(m.group(1)) for p in qd.paragraphs if p.style.name=='Heading 3' and (m:=re.match(r'^Q(\d{2})\b',p.text))]
    row['qa_items']=0 if name=='report_internal_zh' else len(questions)
    if name=='report_internal_zh':row['qa_companion_items']=len(questions)
    from qa_literature import SUPPORT
    refs_present={int(m.group(1)) for p in qd.paragraphs if (m:=re.match(r'^\[(\d+)\]',p.text))}
    row['literature_backed_questions']=0
    for qid,support in SUPPORT.items():
     if support[lang] not in qt or support['locator'] not in qt:fail.append(name+f' missing paper reasoning or locator Q{qid:02d}')
     elif not set(support['refs'])<=refs_present:fail.append(name+f' unresolved citation Q{qid:02d}')
     else:row['literature_backed_questions']+=1
    if refs_present!=set(range(1,26)):fail.append(name+' incomplete 25-reference list')
    if ('Paper-based reasoning.' if lang=='en' else '文献依据与选择理由。') not in qp:fail.append(name+' missing PDF paper reasoning')
    if questions!=list(range(1,26)):fail.append(name+' restored Q01–Q25 order/coverage '+str(questions))
    for question in range(1,26):
     if f'Q{question:02d}' not in qp:fail.append(name+f' missing PDF Q{question:02d}')
   if kind=='ieee_manuscript':
    if len(d.tables)!=(5 if lang=='en' else 8):fail.append(name+' scientific table count')
    if lang=='en':
     par=d.paragraphs;abstract=next((p.text.split('—',1)[1] for p in par if p.text.startswith('Abstract—')),None)
     if abstract is None:
      idx=next(i for i,p in enumerate(par) if p.text=='Abstract');abstract=par[idx+1].text
     words=len(abstract.split());row['abstract_words']=words
     if words>250:fail.append(name+' long abstract')
   checks.append(row)
 (ROOT/'audit/DOCUMENT_VERIFICATION.json').write_text(json.dumps({'checks':checks,'failures':fail,'scope':'DOCX and independently extracted PDF text; English manuscript PDF is local LaTeX, other report PDFs are LibreOffice; visual review is separate'},ensure_ascii=False,indent=2))
 for c in checks:print(c)
 print('FAILURES:',len(fail))
 for x in fail:print(x)
 return bool(fail)
if __name__=='__main__':raise SystemExit(main())
