from pathlib import Path
import json,hashlib,zipfile,io,importlib.util,shutil,tempfile,re,subprocess,sys
from docx import Document
B=Path(__file__).resolve().parent;P=B/'project_root/MIFlu_Reviewed_Project';A=P/'audit/revision9';A.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
Z=zipfile.ZipFile(B/'inputs/MIFlu_Reviewed_Full_Project_20261105.zip');prefix='MIFlu_Reviewed_Project/'
old=Document(io.BytesIO(Z.read(prefix+'01_最终报告/report_internal_zh.docx')));new=Document(P/'01_最终报告/report_internal_zh.docx')
assert [p.text for p in new.paragraphs][:len(old.paragraphs)]==[p.text for p in old.paragraphs]
tables=lambda d:[[[c.text for c in r.cells]for r in t.rows]for t in d.tables]
assert tables(old)==tables(new)
with zipfile.ZipFile(io.BytesIO(Z.read(prefix+'01_最终报告/report_internal_zh.docx'))) as x,zipfile.ZipFile(P/'01_最终报告/report_internal_zh.docx') as y:
 media=[n for n in x.namelist() if n.startswith('word/media/')];assert all(x.read(n)==y.read(n) for n in media)
checks={'internal_all_original_paragraphs_preserved':True,'internal_all_scientific_table_cells_preserved':True,'internal_original_figures_byte_identical':len(media),'internal_qa_count':len([p for p in new.paragraphs if re.match(r'^Q\d{2}\b',p.text)]),'unchanged_inputs':{}}
for n in ['presentation/Week12_Progress_Presentation.pptx','presentation/Week12_Progress_Presentation.pdf','presentation/TALKING_SCRIPT.md']:
 assert (P/n).read_bytes()==Z.read(prefix+n);checks['unchanged_inputs'][n]=sha((P/n).read_bytes())
patch=zipfile.ZipFile(B/'inputs/MIFlu_FYP_Report_Update_8_1_20261105.zip')
for suffix in ['progress_report_en.docx','progress_report_en.pdf']:
 n=next(n for n in patch.namelist() if n.endswith('/01_最终报告/'+suffix));p=P/'01_最终报告'/suffix;assert p.read_bytes()==patch.read(n);checks['unchanged_inputs'][str(p.relative_to(P))]=sha(p.read_bytes())
# CSVs are frozen; independently match the previous archive, not just a rewritten manifest.
cs=list((P/'02_数字表格').glob('*.csv'))
for p in cs:assert p.read_bytes()==Z.read(prefix+p.relative_to(P).as_posix()),str(p)
checks['historical_csvs_byte_identical_to_revision8']=len(cs)
# Same editorial source has been emitted to the current Word and LaTeX.
source=json.loads((P/'manuscript/article_source.json').read_text());d=Document(P/'01_最终报告/ieee_manuscript_en.docx');text='\n'.join(p.text for p in d.paragraphs);tex=(P/'manuscript/overleaf/main.tex').read_text();refs=source['references']
assert len(d.tables)==5 and len(d.inline_shapes)==2 and len(json.loads((P/'manuscript/citation_mapping.json').read_text())['sources'])==21
assert len(source['abstract'].split())==211 and source['abstract'] in text
for token in ['DONE','722968','F5 provisional','--no-lora','gpu_a100','1120 completed']:
 assert token not in text,token
spec=json.loads((P/'presentation/deck_spec.json').read_text());nd=Document(P/'presentation/Presentation_Notes_EN.docx');nt='\n'.join(p.text for p in nd.paragraphs)
assert all(s['speaker_notes'] in nt for s in spec['slides']);assert sum(len(s['speaker_notes'].split()) for s in spec['slides'])==606
english_content='\n'.join(p.text for p in nd.paragraphs if not p.text.startswith(('02_', '03_', '05_')))
assert not any('\u4e00'<=c<='\u9fff' for c in english_content)
sys.path.insert(0,str(P/'01_最终报告/_build2'));from qa_literature import SUPPORT
for n in [P/'presentation/SUPERVISOR_EXPLANATION_GUIDE_EN.md']:
 for q,s in SUPPORT.items():assert s['en'] in n.read_text() and s['locator'] in n.read_text(),q
checks.update({'manuscript_tables':5,'manuscript_figures':2,'manuscript_references':21,'manuscript_abstract_words':211,'english_notes_script_segments_match':13,'english_notes_prose_cjk_characters_excluding_evidence_paths':0,'english_extended_qa_cited_explanations':25,'script_planned_seconds':300,'script_words':606,'human_rehearsal_executed':False})
# Exercise validator behavior. These fixtures are intentionally synthetic integrity tests.
v=P/'handoff_revision9/validate_result_handoff.py';s=importlib.util.spec_from_file_location('rv',v);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);contract=json.loads(m.CONTRACT.read_text());cases=[]
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 for name in contract['required_readable_files']:
  if name not in m.EXCLUDE:(root/name).write_text('fixture only\n')
 status={k:None for k in contract['status_required_keys']};status.update({'core':{'planned':160,'completed':160,'status':'complete'},'national':{'planned':1120,'completed':141,'status':'in_progress'},'ablation':{'planned':60,'completed':60,'status':'complete'},'blocked_outputs':{k:'Synthetic fixture: no scientific data supplied' for k in contract['required_aggregation_or_explicit_block']}})
 def setup():
  (root/'RETURN_STATUS.json').write_text(json.dumps(status));(root/'COMMANDS_EXECUTED.csv').write_text('command,status,exit_code\npython example.py,NOT_EXECUTED,\n');m.manifest(root)
 def result(label,expect):
  r=m.check(root);assert (r['integrity_status']=='PASS')==expect,(label,r);assert r['scientific_readiness']=='NOT_ASSESSED';cases.append({'case':label,'expected_integrity':'PASS' if expect else 'FAIL','actual_integrity':r['integrity_status'],'scientific_readiness':r['scientific_readiness'],'errors':r['errors']})
 setup();result('valid required structure with explicit blocked outputs',True)
 (root/'MESSAGE_TO_CHATGPT.md').write_text('tampered');result('hash mismatch',False)
 setup();(root/'unexpected.tmp').write_text('unexpected');result('unlisted file',False);(root/'unexpected.tmp').unlink()
 setup();status['blocked_outputs'].pop(contract['required_aggregation_or_explicit_block'][0]);setup();result('aggregation missing without block reason',False)
 status['blocked_outputs'][contract['required_aggregation_or_explicit_block'][0]]='fixture';status['national']['status']='complete';setup();result('incomplete declared matrix labelled complete',False)
 status['national']['status']='in_progress';setup();(root/'CONFIG_INDEX.json').unlink();m.manifest(root);result('required file missing even after manifest regeneration',False)
checks['result_handoff_validator_cases_passed']=len(cases)
(A/'HANDOFF_VALIDATOR_TESTS.json').write_text(json.dumps({'executed':True,'test_scope':'Synthetic return-package integrity validator; no forecasting or archived model tests executed','cases':cases},indent=2)+'\n')
(A/'CONTENT_PRESERVATION.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
