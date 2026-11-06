#!/usr/bin/env python3
"""Apply the Artifact Tool-authored status edit plan to the owner PPTX package.
Retains native charts/workbooks, masters, geometry and all unrelated source parts.
"""
from pathlib import Path
import json,copy,zipfile,hashlib,os,argparse,posixpath,re
from io import BytesIO
from lxml import etree
HERE=Path(__file__).resolve().parent
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}

def set_body(body,text):
 ps=body.findall('a:p',NS);template=copy.deepcopy(ps[0])
 for p in ps:body.remove(p)
 for line in text.replace('\\n','\n').split('\n'):
  p=copy.deepcopy(template);runs=p.findall('a:r',NS)
  run=copy.deepcopy(runs[0]) if runs else etree.Element('{'+NS['a']+'}r')
  for child in list(p):
   if etree.QName(child).localname not in ['pPr','endParaRPr']:p.remove(child)
  t=run.find('a:t',NS)
  if t is None:t=etree.SubElement(run,'{'+NS['a']+'}t')
  t.text=line
  end=p.find('a:endParaRPr',NS)
  if end is not None:p.insert(p.index(end),run)
  else:p.append(run)
  body.append(p)

def build(out):
 source=HERE/'source/Week12_User_Corrected.pptx';binding=json.loads((HERE/'source/USER_CORRECTIONS.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==binding['sha256']
 plan=json.loads((HERE/'STATUS_EDIT_PLAN.json').read_text());changed={};repairs=[]
 with zipfile.ZipFile(source) as z:
  for e in plan['edits']:
   part=f"ppt/slides/slide{e['slide']}.xml"
   if part not in changed:changed[part]=etree.fromstring(z.read(part))
   root=changed[part];matches=[s for s in root.findall('.//p:sp',NS) if s.find('p:nvSpPr/p:cNvPr',NS).get('name')==e['shape']];assert len(matches)==1,(part,e['shape'])
   body=matches[0].find('p:txBody',NS);actual='\n'.join(body.xpath('.//a:t/text()',namespaces=NS));assert actual==e['old'],(part,e['shape'],repr(actual),repr(e['old']))
   set_body(body,e['new'])
  for n in plan['notes']:
   part=f"ppt/notesSlides/notesSlide{n['slide']}.xml";root=etree.fromstring(z.read(part));changed[part]=root
   bodies=[s.find('p:txBody',NS) for s in root.findall('.//p:sp',NS) if (ph:=s.find('p:nvSpPr/p:nvPr/p:ph',NS)) is not None and ph.get('type')=='body'];assert len(bodies)==1,part
   set_body(bodies[0],n['text'])
  # Schema-compatible unsigned axis IDs retain the same chart-axis graph and data.
  for part in z.namelist():
   if part.startswith('ppt/charts/') and part.endswith('.xml'):
    root=etree.fromstring(z.read(part));fixed=False
    for e in root.iter():
     if etree.QName(e).localname in ['axId','crossAx'] and e.get('val') and int(e.get('val'))<0:
      old=e.get('val');e.set('val',str(int(old)+(1<<32)));repairs.append({'part':part,'old':old,'new':e.get('val')});fixed=True
    if fixed:changed[part]=root
  # Source charts contain insignificant Excel serialization differences in numeric
  # caches. Refresh their literal cache lexemes from unchanged workbook cells.
  cns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
  sns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
  for part in z.namelist():
   if not re.fullmatch(r'ppt/charts/chart\d+\.xml',part):continue
   root=changed.get(part,etree.fromstring(z.read(part)))
   relpart=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')
   relroot=etree.fromstring(z.read(relpart));target=next(e.get('Target') for e in relroot if '/package' in e.get('Type',''))
   book=posixpath.normpath(posixpath.join(posixpath.dirname(part),target))
   with zipfile.ZipFile(BytesIO(z.read(book))) as wb:
    ws=etree.fromstring(wb.read('xl/worksheets/sheet1.xml'));cells={c.get('r'):c.find('s:v',sns).text for c in ws.findall('.//s:c',sns) if c.find('s:v',sns) is not None}
   for ref in root.findall('.//c:numRef',cns):
    formula=ref.find('c:f',cns).text;match=re.search(r'!\$([A-Z]+)\$(\d+):\$([A-Z]+)\$(\d+)',formula)
    if not match:continue
    col,start,last,end=match.groups();assert col==last
    for pt in ref.findall('c:numCache/c:pt',cns):
     v=pt.find('c:v',cns);new=cells[col+str(int(start)+int(pt.get('idx')))];old=v.text
     assert abs(float(old)-float(new))<1e-12
     if old!=new:v.text=new;repairs.append({'part':part,'kind':'unchanged_workbook_numeric_cache_lexeme','old':old,'new':new})
   changed[part]=root
  out=Path(out);out.parent.mkdir(exist_ok=True,parents=True);tmp=out.with_suffix('.tmp')
  with zipfile.ZipFile(tmp,'w') as archive:
   for item in z.infolist():
    payload=etree.tostring(changed[item.filename],xml_declaration=True,encoding='UTF-8',standalone=True) if item.filename in changed else z.read(item.filename)
    archive.writestr(item,payload)
 with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
 os.replace(tmp,out);return {'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'edited_parts':list(changed),'axis_encoding_repairs':repairs,'scope':'status text/notes; unsigned axis IDs and workbook-matched numeric cache serialization; displayed science and embedded workbook bytes preserved'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=HERE/'Week12_Progress_Presentation.pptx');a=p.parse_args();print(json.dumps(build(a.out),indent=2))
