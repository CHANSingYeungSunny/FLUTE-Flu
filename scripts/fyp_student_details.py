"""Apply owner-provided FYP details without changing scientific content."""
from pathlib import Path
from copy import deepcopy
import json,argparse
from docx import Document
from docx.oxml.ns import qn
DEFAULT=Path(__file__).with_name('FYP_STUDENT_DETAILS.json')

def set_cell(cell,text):
 p=cell.paragraphs[0];rpr=deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
 for child in list(p._p):
  if child.tag!=qn('w:pPr'):p._p.remove(child)
 run=p.add_run(text)
 if rpr is not None:run._r.insert(0,rpr)
 for extra in cell.paragraphs[1:]:extra._element.getparent().remove(extra._element)

def apply_details(d,lang,details_path=DEFAULT):
 v=json.loads(Path(details_path).read_text());t=d.tables[0]
 # Labels work both on the original v8 files and an already updated report.
 labels={
  'en':['Name of Student','Student ID','Programme Major','Project Code and Title','Name of Supervisor','Name of Assessor','Meetings with supervisor and assessor','Average weekly project hours'],
  'zh':['学生姓名','学生编号','课程主修','项目编号与题目','导师姓名','评阅人姓名','与导师及评阅人会面次数','每周平均项目时数']}
 original=labels[lang]
 values={original[0]:v['student_name'],original[1]:v['student_number'],original[2]:v.get('programme_major') or '____________________',original[3]:v['project_code']+'\n'+v['project_title'],original[4]:v['supervisor'],original[5]:v['assessor']}
 for row in t.rows:
  if row.cells[0].text in values:set_cell(row.cells[1],values[row.cells[0].text])
 # Keep the two fields that appear explicitly on page 2 of the school template.
 for row in t.rows:
  if row.cells[0].text in [original[6],'Number of meetings with supervisor / assessor','与导师 / 评阅人会面次数']:
   set_cell(row.cells[0],'Number of meetings with supervisor / assessor' if lang=='en' else '与导师 / 评阅人会面次数')
   set_cell(row.cells[1],'______ / ______')
  if row.cells[0].text in [original[7],'Average weekly project hours']:
   set_cell(row.cells[1],'______ hours/week')
 # Supplementary contact/category information supplied by the owner.
 for label,value,after_label in [
  ('CityU Email' if lang=='en' else 'CityU 电邮',v['cityu_email'],original[1]),
  ('Course' if lang=='en' else '课程编号',v.get('course') or '____________________',original[2]),
  ('Academic Year / Term' if lang=='en' else '学年 / 学期',v.get('academic_year_term') or '____________________','Course' if lang=='en' else '课程编号'),
  ('Remark' if lang=='en' else '备注',v['remark'],original[5])]:
  existing=next((r for r in t.rows if r.cells[0].text==label),None)
  if existing is None:
   anchor=next(r for r in t.rows if r.cells[0].text==after_label)
   xml=deepcopy(t.rows[0]._tr);anchor._tr.addnext(xml)
   from docx.table import _Row
   existing=_Row(xml,t)
  set_cell(existing.cells[0],label);set_cell(existing.cells[1],value)
 d.core_properties.author=v['student_name']
 d.core_properties.comments='Revision 9.1 student metadata confirmed against the owner-supplied summary; meetings and hours retained blank as required by the progress-report template; scientific content unchanged.'
 return d

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reports-dir',type=Path,required=True);p.add_argument('--out-dir',type=Path);a=p.parse_args();out=a.out_dir or a.reports_dir;out.mkdir(parents=True,exist_ok=True)
 for lang in ['en','zh']:
  name=f'progress_report_{lang}.docx';src=a.reports_dir/name;d=Document(src)
  body=[p.text for p in d.paragraphs];tables=[[[c.text for c in r.cells] for r in t.rows] for t in d.tables[1:]];images=len(d.inline_shapes)
  apply_details(d,lang)
  assert body==[p.text for p in d.paragraphs]
  assert tables==[[[c.text for c in r.cells] for r in t.rows] for t in d.tables[1:]]
  assert images==len(d.inline_shapes)
  d.save(out/name);print(name,'student/project details updated; all body paragraphs, scientific tables and figures unchanged')
