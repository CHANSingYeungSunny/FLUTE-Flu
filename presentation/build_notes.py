#!/usr/bin/env python3
"""Build timed script, ten-question sheet and bilingual notes DOCX from the deck spec."""
from pathlib import Path
import json,sys
from docx.shared import Pt,RGBColor
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'01_最终报告/_build2'))
from dlv.render import Doc
from build_revised import final_styles
from internal_qa import QA
from qa_literature import SUPPORT
from build_revised import SOURCES, refline

def stamp(n):return f'{n//60}:{n%60:02d}'
def build():
 spec=json.loads((HERE/'deck_spec.json').read_text());elapsed=0
 lines=['# Talking script for a planned five-minute presentation','',spec['title'],spec['subtitle'],'',f"Revision 8: {len(spec['slides'])} segments total 300 seconds. The spoken script contains {spec['spoken_script_whitespace_words']} whitespace-delimited words; speaking numbers aloud can add words. Actual human delivery is not executed. Rehearse with slide changes against 5:00 ±20 seconds. Chinese guidance and follow-up answers are preparation material outside this pacing budget.",'']
 d=Doc('zh',font_size=11.5,margin_cm=2.0,footer_left='Presentation notes revision 8')
 d.title('Presentation script and preparation notes',sub='五分钟英文逐字讲稿与中文理解说明')
 d.p(spec['title'],size=14,bold=True);d.p(spec['subtitle'],size=12)
 d.p('作者 CHAN Sing Yeung。科学结果保留 2026 年 11 月 3 日快照；执行状态更新到 11 月 5 日 00:15 的用户交接，未实时查询 HPC。')
 d.p('英文逐字讲稿计划共 5:00；实际口头排练未执行。中文说明与追问答案只用于准备，不计入五分钟。先理解每页的证据，再按英文讲稿排练；遇到打断可使用下列短句。')
 d.p('Interruption response 1: Both MIFlu and NLinear pass four cells. The difference is their timing–height trade-off, not a claim of NLinear dominance.')
 d.p('Interruption response 2: Correct Holm gives no rejection at this resolution. That does not establish equivalence. I will return to the paired design in the questions.')
 timing=[]
 for q in spec['slides']:
  q['planned_start_seconds']=elapsed;end=elapsed+q['duration_seconds'];timing.append([str(q['id']),stamp(elapsed)+'–'+stamp(end),q['title']]);elapsed=end
 d.table({'caption':{'en':'Slide timing budget','zh':'逐页时间预算'},'cols':['Slide','Time','Topic'],'rows':timing,'widths':[1.2,2.7,12.1],'fs':9.5,'note':{'en':'','zh':''}})
 note_questions={1:24,2:10,3:4,4:9,5:10,6:13,7:14,8:15,9:19,10:21,11:22,12:25,13:25}
 note_refs=set()
 for q in spec['slides']:
  start=q['planned_start_seconds'];end=start+q['duration_seconds'];heading=f"[{stamp(start)}–{stamp(end)}] Slide {q['id']} {q['title']}"
  lines += ['## '+heading,'',q['speaker_notes'],'']
  d.page_break();d.h(1,f"Slide {q['id']}  {q['title']}")
  d.p(f"Planned time {stamp(start)}–{stamp(end)} ({q['duration_seconds']} seconds).",bold=True)
  d.h(2,'English script  英文逐字讲稿');d.p(q['speaker_notes'])
  d.h(2,'中文理解与讲解重点');d.p(q['preparation_zh'])
  d.h(2,'Likely follow-up  可能追问');d.p(q['follow_up_question'],bold=True);d.p(q['follow_up_answer'])
  support=SUPPORT[note_questions[q['id']]];note_refs.update(support['refs'])
  d.h(2,'Paper basis for the follow-up  追问的论文依据');d.p(support['oral_en'],size=10.5);d.p(support['oral_zh'],size=10.5);d.p(support['locator'],size=9.2)
  d.h(2,'Evidence locator  证据位置')
  for source in q['sources']:d.p(source,size=9.2)
  d.p('Status: planned pacing only. Native PowerPoint and actual human delivery not executed.',size=9.2,italic=True)
 lines += ['## If interrupted','', '**At the peak comparison:** Both MIFlu and NLinear pass four cells. The difference is their timing–height trade-off, not a claim of NLinear dominance.','', '**At the statistical result:** Correct Holm gives no rejection at this resolution. That does not establish equivalence. I will return to the paired design in the questions.','', '## Delivery check','', 'Not executed: an uninterrupted spoken rehearsal. Record the complete talk including slide changes, measure elapsed time, and adjust pauses before changing any scientific caveat. The slide durations are a budget, not measured speech.','']
 (HERE/'TALKING_SCRIPT.md').write_text('\n'.join(lines))
 d.page_break();d.h(1,'References for preparation  准备材料参考文献')
 for source in SOURCES:
  if source['id'] in note_refs:d.p(refline(source,'en'),size=9.2)
 final_styles(d);d.doc.core_properties.author=spec['author'];d.save(str(HERE/'Presentation_Notes_EN_ZH.docx'))
 qas=[
 ('Is this just a reproduction, or are the four axes novel?',
  'The contribution is a specific influenza protocol audit and a broader four-axis evaluation. Earlier work already examines simple baselines and LLM-removal controls. We have not verified that the original MIFlu paper contains only the first two axes, and we do not claim first-ever novelty.', '重点是更全面、可审计的再评估，不能把增加图表数量等同方法创新。','Q24'),
 ('Why ten seeds for reproduction and three for the benchmark?',
  'They are separate protocols: the supplied reproduction table uses ten repetitions and the broader benchmark three. Three keeps the historical retained matrix at 336 cells and reflects its compute budget. A new common ten-seed expansion is underway, with completion and scoring limitations stated separately.', '三种子属于旧基准；新的共同十种子矩阵仍在进行。','Q04'),
 ('Why does MIFlu have both 1.4995 and 1.5574?',
  'The first is the ten-seed reproduction mean, compared with the paper table. The second is the three-seed benchmark mean, compared with other implementations. They aggregate different run sets, so their difference cannot be attributed to a single controlled change.', '先指出两张表回答不同问题，再解释种子集合。','Q07'),
 ('MIFlu also passes 4/16. What is the finding?',
  'Both pass four aggregated cells, but at different horizon/lead positions. NLinear has lower mean peak-height error while MIFlu has lower mean timing error and MSE. This is a trade-off, and the denominator is not 16 independent seasons.', '不要把 NLinear 说成全面优于 MIFlu。','Q12–Q13'),
 ('Does the changed peak ranking demonstrate decoupling?',
  'The leading-three MSE and PIE orders differ, with ordering inverted at both ends. Overall MSE–PIE correlation is +0.736 and MSE–pass-count correlation −0.429, both in expected accuracy directions. This supports a local objective mismatch, not statistical independence.', '局部顺序变化与整体相关可以同时存在。','Q14'),
 ('Why is MIFlu absent from the Pareto graph?',
  'The efficiency export has parameter counts for 11 arms, excluding MIFlu and the encoders. The graph therefore shows that subset’s frontier. The 211× ratio is parameter count, not a measured runtime or energy ratio.', '缺失参数不是零，也不能把 MIFlu 说成无参数。','Q15–Q17'),
 ('Does p≈0.1172 mean NLinear and PatchTST are equivalent?',
  'No. PatchTST retains 11.2% lower observed MSE and wins 10/12 matched cells. Proper Holm rejects 0/136 pairs at this exact-test resolution. Equivalence would require a prespecified acceptable margin and an appropriate design.', '未拒绝不等于等价，更不能直接说增益是噪声。','Q18–Q20'),
 ('Do frozen encoders prove LLM forecasting is ineffective?',
  'The result concerns frozen language features with a trained linear readout. It does not cover generation, prompting, fine-tuning or numerical time-series foundation models. Possible causes are not separated by this comparison.', '只评价实际测过的流程，不能扩大为整个 LLM 家族失败。','Q21'),
 ('Why might text have no effect, and did the tests pass?',
  'In the inspected default path, time positions precede text, causal attention blocks later information and the head reads time positions. The supplied JUnit and CPU log record three named fixed-weight assertions passed with zero skips. They were not rerun in this review. Other fusion paths and independent training trajectories need separate checks.', '区分执行端三项通过与本次日志核查；不扩大到训练轨迹。','Q22–Q23'),
 ('What would you do with one more month or one more GPU?',
  'I would first harmonise cropped and full-window scoring and recover complete MIFlu exports, then prioritise rolling origins, regions and modern numerical controls under O1. A spare GPU does not fix a flawed inference design. Optional O2 needs auditable validation predictions before fitting. Its additional wall time or GPU budget should follow a pilot, not an invented estimate.', '先补最影响结论的证据，再决定是否投入新机制。','Q24–Q25')]
 qlines=['# Ten assessor questions and concise answers','','English answers are for live follow-up. Chinese lines are preparation aids. Internal-report Q01–Q25 supply the longer explanations and evidence locators.','']
 sheet_questions=[24,4,7,12,14,15,20,21,22,24]
 sheet_refs=set()
 for i,(question,answer,zh,locator) in enumerate(qas,1):
  support=SUPPORT[sheet_questions[i-1]];sheet_refs.update(support['refs']);answer += '\n\n**Paper basis and connection.** '+support['en']+'\n\n**Read:** '+support['locator']
  qlines += [f'## {i}. {question}','',answer,'',f'中文提示：{zh} 详细说明：内部报告 {locator}。','']
 qlines += ['## References','']+[refline(source,'en')+'\n' for source in SOURCES if source['id'] in sheet_refs]
 (HERE/'QA_SHEET.md').write_text('\n'.join(qlines))
 guide=['# Supervisor explanation guide','','This mirrors the Q01–Q25 material embedded beside the tables in both internal reports. Use the DOCX/PDF for the complete figures, tables and context.','']
 for qid,sec,en,zh,ea,za,source in QA:
  support=SUPPORT[qid]
  guide += [f'## Q{qid:02d}  §{sec}  {en}','',zh,'','**Answer and local evidence / 直接回答与本地证据**','',ea,'',za,'','**Paper-based reasoning / 文献依据与选择理由**','',support['en'],'',support['zh'],'','**Supervisor short answer / 导师简答**','',support['oral_en'],'',support['oral_zh'],'','Reading locator / 论文位置: '+support['locator'],'','Project evidence / 本地证据: '+source,'']
 guide += ['## References','']+[refline(source,'en')+'\n' for source in SOURCES]
 (HERE/'SUPERVISOR_EXPLANATION_GUIDE.md').write_text('\n'.join(guide))
 print('Notes DOCX, timed script, ten-question sheet and supervisor guide built; 300 planned seconds.')
if __name__=='__main__':build()
