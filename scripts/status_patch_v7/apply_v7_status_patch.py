#!/usr/bin/env python3
"""Apply hash-guarded status edits to six v6 DOCX reports and append v7 evidence.
Requires python-docx. Does not run models, modify source PDFs or generate results.
"""
from pathlib import Path
import argparse,json,hashlib,zipfile,os
from docx import Document
HERE=Path(__file__).resolve().parent

def apply(base,out):
 base=Path(base).resolve();out=Path(out).resolve()
 if base==out:raise ValueError('Use a separate output folder; v6 is preserved')
 patch=json.loads((HERE/'V7_STATUS_PATCH.json').read_text(encoding='utf-8'));content=json.loads((HERE/'ADDENDUM_CONTENT.json').read_text(encoding='utf-8'))
 for item in patch['files']:
  p=base/item['filename']
  if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Baseline hash differs: '+str(p))
 out.mkdir(parents=True,exist_ok=True);records=[]
 for item in patch['files']:
  src=base/item['filename'];d=Document(src);original=Document(src)
  before_tables=[[ [c.text for c in row.cells] for row in t.rows] for t in d.tables]
  q_before=[p.text for p in d.paragraphs if len(p.text)>3 and p.text[0]=='Q' and p.text[1:3].isdigit()]
  for change in item['paragraphs']:
   p=d.paragraphs[change['index']]
   if p.text!=change['old']:raise ValueError('Paragraph anchor differs '+item['filename'])
   p.clear();p.add_run(change['new'])
  edited=set()
  for change in item['cells']:
   cell=d.tables[change['table']].rows[change['row']].cells[change['col']]
   if cell.text!=change['old']:raise ValueError('Cell anchor differs '+item['filename'])
   cell.text=change['new'];edited.add((change['table'],change['row'],change['col']))
  for ti,t in enumerate(d.tables):
   for ri,row in enumerate(t.rows):
    for ci,cell in enumerate(row.cells):
     if (ti,ri,ci) not in edited and cell.text!=before_tables[ti][ri][ci]:raise ValueError('Protected table changed')
  assert q_before==[p.text for p in d.paragraphs if len(p.text)>3 and p.text[0]=='Q' and p.text[1:3].isdigit()]
  lang='zh' if src.stem.endswith('_zh') else 'en';c=content[lang]
  d.add_page_break();d.add_heading(c['title'],1);d.add_paragraph(c['subtitle']);d.add_paragraph(c['opening']);d.add_heading(c['h1'],2)
  for label,text in c['rows']:
   p=d.add_paragraph();p.add_run(label+'. ').bold=True;p.add_run(text)
  d.add_paragraph(c['last1']);d.add_heading(c['h2'],2)
  for p in c['p2']:d.add_paragraph(p)
  d.add_heading(c['h3'],2);d.add_paragraph(c['intro3'])
  for cmd in c['commands']:d.add_paragraph(cmd)
  for i,p in enumerate(c['wait'],1):d.add_paragraph(str(i)+'. '+p)
  d.add_paragraph(c['end']);d.add_paragraph(c['sources']);target=out/src.name;temporary=out/(src.name+'.tmp');d.save(temporary)
  with zipfile.ZipFile(temporary) as archive:
   if archive.testzip() is not None:raise ValueError('Output DOCX CRC failure')
  os.replace(temporary,target)
  check=Document(target)
  assert len(check.tables)==len(before_tables)
  assert q_before==[p.text for p in check.paragraphs if len(p.text)>3 and p.text[0]=='Q' and p.text[1:3].isdigit()]
  records.append({'filename':src.name,'base_sha256':item['sha256'],'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'paragraph_status_edits':len(item['paragraphs']),'progress_status_cell_edits':len(item['cells']),'q_headings_preserved':len(q_before),'old_scientific_tables_preserved':True,'scope':'status edits and appended addendum only; full updated DOCX/PDF layout requires local render review'})
 (out/'PATCH_APPLICATION_REPORT.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return records
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 for row in apply(a.base,a.out):print(row['filename'],row['paragraph_status_edits'],'paragraph status edits; protected tables and Q headings preserved')
