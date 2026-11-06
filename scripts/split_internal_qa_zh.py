#!/usr/bin/env python3
"""Split the Chinese report's 25 cited Q&A blocks into a standalone companion.
Run after build_current_documents.py and add_revision9_internal.py.
Scientific tables, figures, and non-Q&A results remain in the main report.
"""
from pathlib import Path
from copy import deepcopy
from collections import OrderedDict
import re,json,hashlib,shutil
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'01_最终报告';MAIN=OUT/'report_internal_zh.docx';QA=OUT/'report_internal_qa_zh.docx'
PREFIXES=['直接回答与本地证据。','文献依据与选择理由。','向导师简答。','论文位置。','证据。']
def rewrite(p,text):
 if p.runs:
  p.runs[0].text=text
  for run in p.runs[1:]:run.text=''
 else:p.add_run(text)
def build():
 d=Document(MAIN);pars=list(d.paragraphs);indices=[i for i,p in enumerate(pars) if re.match(r'^Q\d{2}\b',p.text)]
 if not indices:
  if QA.exists():print('Chinese main report and Q&A are already separated');return
  raise RuntimeError('No Q&A in main report and no companion exists')
 assert len(indices)==25
 archive=ROOT/'archive/internal_with_qa_revision9';archive.mkdir(exist_ok=True,parents=True)
 for ext in ['docx','pdf']:
  p=MAIN.with_suffix('.'+ext)
  if p.exists() and not (archive/p.name).exists():shutil.copyfile(p,archive/p.name)
 groups=OrderedDict();blocks=[];section='';nodes=[]
 for i,p in enumerate(pars):
  if p.style.name=='Heading 1':section=p.text
  if i not in indices:continue
  block=pars[i:i+6];assert all(p.text.startswith(prefix) for p,prefix in zip(block[1:],PREFIXES)),p.text
  qid=int(re.match(r'^Q(\d{2})',p.text)[1]);assert qid==len(blocks)+1
  row={'id':qid,'section':section,'paragraphs':[x.text for x in block],'styles':[x.style.name for x in block]};blocks.append(row);groups.setdefault(section,[]).append(row);nodes.extend(x._p for x in block)
 refs=[p for p in pars if re.match(r'^\[\d+\]',p.text)];assert len(refs)==25
 scientific_tables=[[[c.text for c in row.cells] for row in t.rows] for t in d.tables[1:]];figures=len(d.inline_shapes)
 qdoc=Document(MAIN)
 for e in list(qdoc.element.body):
  if e.tag!=qn('w:sectPr'):qdoc.element.body.remove(e)
 qdoc.add_paragraph('MIFlu 研究问答与文献依据','Title')
 qdoc.add_paragraph('导师讨论与答辩准备手册')
 qdoc.add_paragraph('CHAN Sing Yeung    58324980    配套文件修订 9.2')
 qdoc.add_paragraph('本册集中收录原中文内部报告的 Q01–Q25。每题保留直接回答、具名论文依据、导师简答、论文阅读位置与本地证据，供汇报准备和深入讨论使用。实验结果与执行状态沿用有日期的历史快照，不表示已取得新的运行结果。')
 qdoc.add_paragraph('配套正文为 report_internal_zh.docx / .pdf。问答中的表号、F0–F5 结论及章节说明指向该报告；其科学表格和图形仍保留在正文中。参考文献编号与原报告一致，不能直接套用英文期刊稿按首次引用重新编排的编号。')
 qdoc.add_heading('问答目录',1)
 for title,items in groups.items():qdoc.add_paragraph(title+'    '+f"Q{items[0]['id']:02d}"+(('–Q'+f"{items[-1]['id']:02d}") if len(items)>1 else ''))
 qdoc.add_page_break()
 for title,items in groups.items():
  h=qdoc.add_heading(title,1);h.paragraph_format.page_break_before=False
  for item in items:
   original=next(p for p in pars if p.text==item['paragraphs'][0]);i=pars.index(original)
   for p in pars[i:i+6]:qdoc.element.body.insert(len(qdoc.element.body)-1,deepcopy(p._p))
 qdoc.add_heading('参考文献',1)
 qdoc.add_paragraph('以下 25 项文献沿用原报告编号，方便对应每题的论文依据与阅读位置。')
 for p in refs:qdoc.element.body.insert(len(qdoc.element.body)-1,deepcopy(p._p))
 # Remove unused image relationships inherited from the source report.
 for rel in list(qdoc.part.rels.values()):
  if rel.reltype==RT.IMAGE:qdoc.part.drop_rel(rel.rId)
 for sec in qdoc.sections:
  for footer in [sec.footer]:
   for p in footer.paragraphs:
    for run in p.runs:
     if 'MIFlu audit' in run.text:run.text=run.text.replace('MIFlu audit 3 November 2026','MIFlu 问答与文献依据')
 qdoc.core_properties.title='MIFlu 研究问答与文献依据';qdoc.core_properties.author='CHAN Sing Yeung';qdoc.core_properties.comments='Revision 9.2 standalone Chinese Q&A; all 150 original question/answer paragraphs and 25 references preserved verbatim.'
 qdoc.save(QA)
 # Main report: remove exactly the identified Q&A paragraphs.
 for e in nodes:e.getparent().remove(e)
 rewrite(d.paragraphs[1],'内部技术报告')
 for row in d.tables[0].rows:
  if row.cells[0].text=='阅读说明':
   p=row.cells[1].paragraphs[0];rewrite(p,'四个评价维度；导师问答另见独立配套文件')
 for p in d.paragraphs:
  if p.text.startswith('阅读目的。'):
   rewrite(p,'阅读目的。 本报告集中呈现数据约定、复现结果、四维评测、统计审计及后续工作。精度与峰值覆盖 28 个模型，参数导出覆盖 11 个，配对检验覆盖 17 个。Q01–Q25 及完整文献解释另见 report_internal_qa_zh.docx / .pdf。')
  elif p.text.startswith('本报告原有 Q01–Q25'):
   rewrite(p,'原有 Q01–Q25、文献推理、论文阅读位置与导师简答已移入独立配套问答册 report_internal_qa_zh.docx / .pdf。科学表格及图形继续保留在本报告。两份中文文件沿用相同参考文献编号；英文期刊稿按首次引用另行编号。英文演讲准备稿也提供论文理由，逐字讲稿仍为计划 5:00；真人排练未执行。')
 # Keep compact comparison tables together after the removed text changes page flow.
 for table in d.tables[1:]:
  if len(table.rows)<=4:
   for row in table.rows:
    for cell in row.cells:
     for p in cell.paragraphs:p.paragraph_format.keep_with_next=True
   previous=table._tbl.getprevious()
   if previous is not None and previous.tag==qn('w:p'):Paragraph(previous,d).paragraph_format.keep_with_next=True
 d.core_properties.comments='Revision 9.2 concise Chinese internal report; Q01–Q25 preserved in the separate companion; scientific table cells and all original figures unchanged.';d.save(MAIN)
 assert not any(re.match(r'^Q\d{2}\b',p.text) for p in d.paragraphs)
 assert scientific_tables==[[[c.text for c in row.cells] for row in t.rows] for t in d.tables[1:]] and figures==len(d.inline_shapes)
 qpars=list(qdoc.paragraphs)
 for item in blocks:
  i=next(i for i,p in enumerate(qpars) if p.text==item['paragraphs'][0]);assert [p.text for p in qpars[i:i+6]]==item['paragraphs']
 assert [p.text for p in qpars if re.match(r'^\[\d+\]',p.text)]==[p.text for p in refs]
 source=ROOT/'qa';source.mkdir(exist_ok=True);(source/'INTERNAL_QA_ZH.json').write_text(json.dumps({'revision':'9.2','question_blocks':blocks,'references':[p.text for p in refs],'source_report_archive':'archive/internal_with_qa_revision9/report_internal_zh.docx','preservation':'All 150 Q&A paragraphs and all 25 reference entries preserved verbatim'},ensure_ascii=False,indent=2)+'\n')
 a=ROOT/'audit/revision9_2';a.mkdir(exist_ok=True,parents=True);(a/'QA_SPLIT_VERIFICATION.json').write_text(json.dumps({'main_question_headings':0,'companion_questions':25,'question_answer_paragraphs_verbatim':150,'references_verbatim':25,'scientific_tables_preserved':len(scientific_tables),'figures_preserved':figures,'new_scientific_results':False},indent=2)+'\n')
 print('Chinese internal report split: 25 complete cited Q&As preserved separately; scientific tables and figures unchanged.')
if __name__=='__main__':build()
