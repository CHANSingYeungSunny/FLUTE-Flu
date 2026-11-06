#!/usr/bin/env python3
"""Integrate the verified 5 November execution update into six v6 reports and two journal records.
Only stored historical scientific results are used. No model runs or new aggregation.
"""
from pathlib import Path
import json,hashlib,copy,re,zipfile,os
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'source_snapshots/v6';OUT=ROOT/'01_最终报告'
PATCH=json.loads((ROOT/'scripts/status_patch_v7/V7_STATUS_PATCH.json').read_text());AUD=ROOT/'audit';AUD.mkdir(exist_ok=True)
TEXT={
'en':{
 'heading':'Execution update at 5 November 2026 00:15 HKT',
 'status':'The returned core Track B artefacts are complete for 160/160 cells: MIFlu, NLinear, PatchTST and DLinear, four forecast lengths and ten seeds (2021–2030). The national 28-arm expansion remains in progress. Its packaged ledger records 117 completed and 1003 queued at 4 November 23:35 HKT; a later supplied report records 139, and the owner reports 141/1120 at 5 November 00:15 HKT. These are different capture times, not conflicting estimates of one frozen snapshot. This review did not connect to Burgundy.',
 'tests':'The supplied JUnit and runtime log record three fixed-weight CPU no-text assertions passed with zero skips. This supports the inspected evaluation path, not equality of independently trained trajectories or text/LoRA gradient reachability. Whole-archive collection still fails. The supplied queue records 60/60 additional ablation cells DONE; their per-variant seven-channel aggregate trend remains unverified. Job 722968 is a historical cancelled job.',
 'limits':'A common ten-seed result is not yet available. MIFlu stored metrics use cropped windows, while other supplied models use all valid windows; the complete seven-channel MIFlu prediction tensors were not attached. Scores must be harmonised before a common ranking. The submitted protocol still has frozen:false and no lock timestamp, so these comparisons remain retrospective/exploratory. The two data profiles have different byte hashes; the supplied aligned seven-channel comparison reports maximum numeric difference 0.0, which is not byte identity or independent verification of upstream provenance.',
 'operations':'At the 00:15 handoff the owner reports 13 empty decision_tree partial directories and two pending gpu_a100 lanes. Table VI (19 TODO) and walk-forward (170 TODO) have not started in the v2 successor chain, although earlier legacy DONE rows exist. One earlier summary lists 9 regional TODOs; execution-end status must reconcile the dates and skip counts. Storage is owner-reported at approximately 306/300 GB soft, with ten-day grace and 1024 GB hard; the source quota log uses KB units. These are dated reports, not current live readings.',
 'proof':'Independent review confirms both uploaded ZIP hashes, all manifest-listed file hashes, core 160/160 artefact completeness and national snapshot 117/1120. Recalculation matches 237 seven-channel NPZ cells and the ILITOTAL metrics of 40 MIFlu CSV cells at each recorded scoring panel. The as-received package validator flags one unlisted temporary prediction file; quarantining it in an extracted review copy yields PASS. Original uploads and the manifest were not rewritten. No full scientific validation follows from that integrity PASS.',
 'pending':'Pending work is to complete or account for every national cell, export all seven MIFlu channels, harmonise both scoring panels, aggregate peak/ablation results and use dependence-aware statistics. Regional/rolling-origin and numerical-foundation controls, real CDC calendar/vintage, full resource measurements and official-source method fidelity remain unresolved even after national completion. Existing tables remain the audited historical results.',
 'short':'Execution update (5 November 2026 00:15 HKT). Core artefacts: 160/160 complete. The national 1120 matrix is in progress: packaged ledger 117 completed, later owner report 141. Supplied CPU no-text record: 3 passed, 0 skipped. Ablation queue: 60/60 DONE, aggregate trend pending. These execution records do not replace the historical results below.',
 'method':'A ten-seed expansion (2021–2030) is underway. Returned artefacts cover 160/160 core cells, including DLinear controls outside the historical 28-arm roster. The national ledger contains 117/1120 complete cells at 4 November 23:35 HKT; the owner reports 141 at 5 November 00:15 HKT. These are execution counts rather than a completed new evaluation. All result tables in this manuscript retain the historical protocols.',
 'threat':'The new expansion still mixes stored scoring panels: cropped MIFlu metrics versus full-window metrics for other models. Complete seven-channel MIFlu exports are needed before harmonised comparison. PROTOCOL_LOCK.json remains unfrozen after submission; nothing is backdated or described as prospective confirmation. Supplied CPU no-text passes do not establish training-time causal effects. Queue-reported ablation completion does not establish a depth/LoRA effect.',
 'journal_title':'MIFlu research evidence and journal preparation record',
 'journal_sub':'Full research record with Q01–Q25, source-linked reasoning and execution evidence',
 'j13':'13 Evidence register for journal preparation',
 'j14':'14 Reproducible commands and source boundaries',
 'j15':'15 Continuing updates when more results arrive',
 'jintro':'This record supersedes the older pre-audit journal archive. It carries the complete current explanatory report and its 25 questions, then records the evidence needed for later manuscript decisions. The earlier file is preserved under archive/journal_record_before_audit for provenance. Its 16-arm, unique peak-winner, speculative runtime-cost and overbroad encoder narratives are not current scientific conclusions.',
 'policy':'At every new result handoff, verify archive hashes, per-run completeness, resolved configs and raw predictions before changing conclusions. Recompute common tables and uncertainty, distinguish historical and new protocols, and revise the internal report, FYP progress report, IEEE manuscript, this journal record, README, presentation and talking notes together. Preserve Q01–Q25 and their named-paper reasoning. Update methods, results, abstract, limitations and conclusions wherever the new evidence changes them; do not force new results to match the old ranking or p-values. New data must be provided or explicitly made accessible; this instruction does not create unattended HPC monitoring.',
 'jref':'Evidence paths: handoffs/20261105_return, audit/return_review_20261105, PROTOCOL_LOCK.json and its recorded deviation, RUN_LEDGER.csv, HPC_VALIDATED_CELLS.tsv, tests/no_text_runtime.xml, and AGGREGATION/TRACKB_PEAK_PARTIAL.csv. The returned prediction_ili is the ILITOTAL export. The partial peak table is neither full-panel evidence nor completed event-level matched/missed-peak analysis.'
},
'zh':{
 'heading':'截至 2026 年 11 月 5 日 00:15 HKT 的执行更新',
 'status':'回传 Track B 核心产物满足 160/160 完整性检查：MIFlu、NLinear、PatchTST、DLinear，四个预测长度与十种子（2021–2030）。全国 28 模型扩展仍在进行。11 月 4 日 23:35 HKT 的打包账本为 117 完成、1003 排队；稍后所附报告为 139，用户在 11 月 5 日 00:15 HKT 报告 141/1120。这些对应不同采集时刻，不是同一冻结快照的矛盾估计。本次未连接 Burgundy 实时状态。',
 'tests':'所附 JUnit 及运行日志记录三项固定权重 CPU no-text 断言通过，零跳过。它支持已检查评估路径，不证明独立训练轨迹相等或文本、LoRA 梯度可达性。整个归档测试的收集仍失败。回传队列记录新增消融 60/60 为 DONE，但逐变体七通道聚合趋势仍未核实。作业 722968 是历史已取消作业。',
 'limits':'目前还没有完整共同十种子结果。MIFlu 的所存指标采用裁剪窗口，其他已附模型采用全部有效窗口；未附完整七通道 MIFlu 预测张量，须先统一评分再建立共同排名。已提交协议仍为 frozen:false、锁定时间为空，因此比较属于回顾性、探索性。两个数据 profile 的字节哈希不同；所附七通道对齐比较报告最大数值差为 0.0，这不等于字节身份或独立核实上游来源。',
 'operations':'00:15 交接时用户报告 13 个空 decision_tree 部分目录、两个 gpu_a100 通道待调度。Table VI（19 TODO）及滚动原点（170 TODO）在 v2 后继链尚未开始，但旧链已有 DONE 行。较早摘要另写区域 9 TODO，执行端须核对日期与跳过数。存储为用户报告约 306/300 GB 软配额、宽限十天、硬配额 1024 GB；原配额日志采用 KB。这些均是带日期报告，不是本次实时读取。',
 'proof':'本次独立核查证实两个 ZIP 哈希、所有 manifest 列出的文件哈希、核心 160/160 产物完整性及全国快照 117/1120。对 237 个七通道 NPZ 单元及 40 个 MIFlu CSV 单元的 ILITOTAL 指标，按各自所存评分面板重算一致。原样 validator 因一个未列入清单的临时预测文件报 FAIL；在解压审阅副本隔离该文件后为 PASS。原上传及 manifest 未改写；完整性 PASS 不能替代科学验证。',
 'pending':'待完成的是逐项交代全国所有计划单元，补齐 MIFlu 七通道导出，统一两个评分面板，聚合峰值与消融，并使用处理依赖的统计。区域、滚动原点、数值时序基础模型控制、真实 CDC 日历与数据版本、完整资源测量及方法来源，即使全国完成后仍须核实。现有科学表保持经审计的历史结果。',
 'short':'执行更新（2026 年 11 月 5 日 00:15 HKT）：核心产物 160/160 完整；全国 1120 矩阵仍在进行，打包账本为 117 完成，稍后用户报告 141。所附 CPU no-text 记录为 3 通过、0 跳过；消融队列为 60/60 DONE，聚合趋势待完成。这些执行状态不替换下列历史科学结果。',
 'method':'共同十种子（2021–2030）扩展正在进行。核心回传产物为 160/160，含不属于历史 28 模型名单的 DLinear 控制。全国账本在 11 月 4 日 23:35 HKT 有 117/1120 完成，用户在 11 月 5 日 00:15 HKT 报告 141。这些是执行计数，不是已完成的新评估；本稿所有科学表保留历史协议结果。',
 'threat':'新扩展的所存评分面板尚不一致：MIFlu 为裁剪窗口，其他模型为全窗口。须补齐 MIFlu 七通道预测后才能共同评分。PROTOCOL_LOCK.json 在提交后仍未冻结，不能倒填时间或称作前瞻确认。所附 CPU no-text 通过不证明训练时因果作用；队列消融完成也不证明深度或 LoRA 收益。',
 'journal_title':'MIFlu 研究证据与期刊准备记录',
 'journal_sub':'含 Q01–Q25 文献论证及执行证据的完整研究记录',
 'j13':'13 期刊准备证据登记',
 'j14':'14 可复跑命令与来源边界',
 'j15':'15 新结果到达后的持续更新',
 'jintro':'本记录替代审计前的旧期刊档案。先保留当前完整解释报告及 25 组问答，再记录后续手稿决策所需的证据。旧文件保存在 archive/journal_record_before_audit，供来源追踪；其中 16 模型、唯一峰值赢家、未经测量的算力费用及扩大编码器结论等叙述不作为当前科学结论。',
 'policy':'每次有新结果交接时，先核 ZIP 哈希、逐运行完整性、实际配置与原始预测，再修改结论。重算共同表与不确定性，区分历史和新增协议，同时修订内部报告、FYP 进度报告、IEEE 稿、本记录、README、PPT 及讲稿。保留 Q01–Q25 与具名论文论证；证据改变之处应同步重写方法、结果、摘要、局限和结论，不强迫新结果符合旧排名或 p 值。新数据须由用户交付或明确提供访问途径；这项持续指示不等于无人值守的 HPC 监控。',
 'jref':'证据路径：handoffs/20261105_return、audit/return_review_20261105、PROTOCOL_LOCK.json 及偏离记录、RUN_LEDGER.csv、HPC_VALIDATED_CELLS.tsv、tests/no_text_runtime.xml、AGGREGATION/TRACKB_PEAK_PARTIAL.csv。prediction_ili 是 ILITOTAL 导出；部分峰值表不等于完整面板或已完成的逐事件匹配、漏检分析。'
}}

def write(p,text):
 p.clear();lead=text.split('. ',1)
 if len(lead)==2 and len(lead[0])<36 and not text.startswith('['):p.add_run(lead[0]+'. ').bold=True;p.add_run(lead[1])
 else:p.add_run(text)
def after(anchor,text,style=None):
 new=anchor.insert_paragraph_before(text,style=style);anchor._p.addnext(new._p);return new

def apply_base(item):
 src=BASE/item['filename'];assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256'];d=Document(src)
 for row in item['paragraphs']:p=d.paragraphs[row['index']];assert p.text==row['old'];write(p,row['new'])
 for row in item['cells']:
  c=d.tables[row['table']].rows[row['row']].cells[row['col']];assert c.text==row['old'];c.text=row['new']
 return d

def save(d,path):
 # Font aliases are rendering choices; the document retains the source's named font families.
 d.core_properties.author='CHAN Sing Yeung';d.core_properties.comments='Integrated execution update 5 November 2026; historical scientific results retained.'
 tmp=path.with_suffix('.docx.tmp');d.save(tmp)
 with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
 os.replace(tmp,path)

def build():
 OUT.mkdir(exist_ok=True);records=[]
 for item in PATCH['files']:
  stem=Path(item['filename']).stem;lang=stem[-2:];c=TEXT[lang];d=apply_base(item)
  before=Document(BASE/item['filename']);old_q=[p.text for p in before.paragraphs if re.match(r'^Q\d{2}\b',p.text)]
  if stem.startswith('report_internal'):
   import sys
   sys.path.insert(0,str(ROOT/'01_最终报告/_build2'))
   from qa_literature import SUPPORT
   # Preserve all named-paper reasoning while synchronising its runtime status.
   for qid,support in SUPPORT.items():
    pars=d.paragraphs;qi=next(i for i,p in enumerate(pars) if re.match(f'^Q{qid:02d}\\b',p.text))
    write(pars[qi+2],('Paper-based reasoning. ' if lang=='en' else '文献依据与选择理由。 ')+support[lang])
    write(pars[qi+3],('Say to the supervisor. ' if lang=='en' else '向导师简答。 ')+support['oral_'+lang])
   anchor=next(p for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('9 '));anchor=after(anchor,c['heading'],'Heading 2')
   for key in ['status','tests','limits','operations']:anchor=after(anchor,c[key])
   a=next(p for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('11 '));a=after(a,c['proof']);after(a,c['pending'])
  elif stem.startswith('progress_report'):
   a=next(p for p in d.paragraphs if p.text.startswith(('Progress against plan.','对照计划的进度。')));a=after(a,c['short']);a=after(a,c['limits']);after(a,c['operations'])
  else:
   a=next(p for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('V.'));a=after(a,c['method'])
   a=next(p for p in d.paragraphs if p.style.name=='Heading 1' and p.text.startswith('VII.'));after(a,c['threat'])
  if stem.startswith('progress_report'):
   from fyp_student_details import apply_details
   apply_details(d,lang)
  save(d,OUT/item['filename']);assert old_q==[p.text for p in d.paragraphs if re.match(r'^Q\d{2}\b',p.text)]
  # Exactly the declared progress-status cells may change in the old tables.
  edits={(v['table'],v['row'],v['col']) for v in item['cells']}
  for ti,t in enumerate(before.tables):
   if stem.startswith('progress_report') and ti==0:continue  # Part A owner metadata; scientific tables remain asserted below
   for ri,row in enumerate(t.rows):
    for ci,cell in enumerate(row.cells):
     if (ti,ri,ci) not in edits:assert cell.text==d.tables[ti].rows[ri].cells[ci].text,(stem,ti,ri,ci)
  records.append({'file':item['filename'],'q_headings':len(old_q),'scientific_tables_preserved':True,'figures':len(d.inline_shapes)})
 for lang,c in TEXT.items():
  d=Document(OUT/f'report_internal_{lang}.docx');write(d.paragraphs[0],c['journal_title']);write(d.paragraphs[1],c['journal_sub'])
  d.add_page_break();d.add_heading(c['j13'],1);d.add_paragraph(c['jintro'])
  for key in ['status','tests','limits','operations','proof','pending','jref']:d.add_paragraph(c[key])
  d.add_heading(c['j14'],1)
  for cmd in ['python scripts/verify_snapshot.py --raw-smoke','python scripts/build_current_documents.py','python presentation/build_notes.py','python cellok.py count all/export all/cells_all.tsv','python aggregate_core.py','python aggregate_peak.py']:
   p=d.add_paragraph(cmd);p.runs[0].font.name='Consolas';p.runs[0].font.size=Pt(9)
  d.add_paragraph('The cell/aggregation commands are execution-end commands, not model runs performed in this review. See handoffs/20261105_return and audit/EXECUTION_STATUS.md for scope.' if lang=='en' else '单元与聚合命令属于执行端命令，本次未运行模型。范围见 handoffs/20261105_return 与 audit/EXECUTION_STATUS.md。')
  d.add_heading(c['j15'],1);d.add_paragraph(c['policy']);save(d,OUT/f'record_for_journal_{lang}.docx')
  records.append({'file':f'record_for_journal_{lang}.docx','q_headings':25,'basis':'complete audited internal report plus journal evidence register','figures':len(d.inline_shapes)})
 (AUD/'INTEGRATED_DOCUMENT_BUILD.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(records,indent=2))
if __name__=='__main__':build()
