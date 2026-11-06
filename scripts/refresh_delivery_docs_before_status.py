#!/usr/bin/env python3
"""Refresh report inventories and complete paragraph/table diffs after regeneration."""
from pathlib import Path
import json,hashlib,difflib,re,sys,ast
import fitz
from docx import Document
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'01_最终报告';A=ROOT/'audit'
sys.path.insert(0,str(OUT/'_build2'))
from make_manifest import build

def refresh():
 inventory=build();original=json.loads((A/'DOCUMENT_TEXT_INVENTORY.json').read_text());deltas=[]
 for q in inventory:
  name=q['stem'];d=Document(OUT/(name+'.docx'));new=[]
  for i,p in enumerate(d.paragraphs):
   if p.text:new.append(f'p{i} {p.text}')
  for j,t in enumerate(d.tables):
   for i,row in enumerate(t.rows):new.append(f'table{j+1}/row{i+1} '+' | '.join(c.text for c in row.cells))
  old=[v['location']+' '+v['text'] for v in original[name+'.docx']]
  deltas.extend(difflib.unified_diff(old,new,fromfile=name+' corrected upload',tofile=name+' reviewed revision 4',lineterm=''))
 (A/'DOCUMENT_DIFFS.md').write_text('# Full paragraph and table diffs against the corrected upload\n\nDeleted lines are historical source claims, not current assertions. Q01–Q25 restore the explanatory function of the original internal report.\n\n```diff\n'+'\n'.join(deltas)+'\n```\n')
 roles={'report_internal':'导师交流用完整解释与 Q01–Q25','progress_report':'学校进度报告，保留规定 PART A 与 1、2、3、4、6、7、8','ieee_manuscript':'单栏期刊审阅草稿，尚未达到投稿状态'}
 lines=['# 当前六份报告阅读说明','','修订版 4 为全部 25 组问答加入具名论文依据、具体阅读位置、选择理由和导师简答，并同步讲稿追问资料；保留本人修正的 PPT。实验状态仍是所附 2026 年 11 月 3 日快照，没有新增训练或 HPC 结果。','','| 文件 | PDF 页数 | Word 表格 | Word 图片 | 用途 |','|---|---:|---:|---:|---|']
 for q in inventory:lines.append(f"| {q['stem']}.docx / .pdf | {q['pages']} | {q['tables']} | {q['figures']} | {roles[q['stem'].rsplit('_',1)[0]]} |")
 lines+=['','建议先读学校进度报告；需要向导师解释为何两张表分数不同、为何选择某个协议时，查内部报告对应位置的 Q01–Q25。英文与中文问答含义相同，均保留证据位置。问答是内部报告的必要部分，不能为了精简而删除。','','presentation/Presentation_Notes_EN_ZH.docx / .pdf 提供逐页英文讲稿、中文理解及追问答案。TALKING_SCRIPT.md 只把英文部分计入 300 秒预算；实际口头排练未执行。QA_SHEET.md 为十个现场问答，SUPERVISOR_EXPLANATION_GUIDE.md 对应内部报告的完整 25 问。','','重建顺序：','','```bash','python 01_最终报告/_build2/build_revised.py --tables-json','python 01_最终报告/_build2/to_pdf.py','python presentation/build_pareto_figure.py','python presentation/make_deck_spec.py','python presentation/build_deck.py','python presentation/build_notes.py','python presentation/render_presentation.py','python 01_最终报告/_build2/verify_docs.py','python presentation/verify_presentation.py','python scripts/refresh_delivery_docs.py','```','','PDF 转换需要 LibreOffice 与可用 CJK 字体。本次采用 Noto CJK 替代 Word 声明的 SimSun / Microsoft YaHei；原生 Office 行为未执行。归档模型测试与实时 HPC 未执行，精确命令见 audit/EXECUTION_STATUS.md 与 audit/NO_TEXT_VERIFICATION.md。O1 仍为默认，O2 条件与费用边界见 audit/INNOVATION_DECISION.md。','','历史 record_for_journal 文件和带日期的旧笔记不属于当前六份修订报告。学校 PART A 的私人记录、原始计划依据及签名仍需本人完成。']
 (OUT/'README_报告说明.md').write_text('\n'.join(lines)+'\n')
 p=A/'DOC_REVIEW.md';text=p.read_text()
 for q in inventory:
  marker='## '+q['stem']+'\n';start=text.find(marker)
  if start>=0:
   stop=text.find('\n## ',start+3);stop=len(text) if stop<0 else stop;part=text[start:stop]
   part=re.sub(r'\*\*Final inventory:\*\* \d+ PDF pages, \d+ tables, \d+ figures\.',f"**Final inventory:** {q['pages']} PDF pages, {q['tables']} tables, {q['figures']} figures.",part);text=text[:start]+part+text[stop:]
 marker='## Revision 2 explanatory restoration'
 if marker in text:text=text[:text.index(marker)]
 text+='''## Revision 2 explanatory restoration

The internal report must serve supervision as well as formal reporting. The earlier cut removed useful teaching explanations. Q01–Q25 are now embedded beside the relevant tables in both languages. QA_RESTORATION_MAP.md maps the six original explicit questions and the expanded surrounding explanations. Unsupported upstream allegations, universal seed conventions, MAE crossover and noise/equivalence assertions remain corrected. No question is silently dropped to shorten the internal report.

The accepted presentation title is Re-evaluating Multimodal LLMs for Influenza Forecasting, with a subtitle naming all four axes. It does not claim demonstrated decoupling or an isolated causal multimodal benefit. The original paper’s coverage of the four axes remains unverified beyond the stated reading depth. Two editable charts and a model-keyed pass grid replace dense or potentially misattributed illustrations. The presentation-specific Pareto plot retains all eleven measured points and enlarges frontier labels. Internal-report plots and complete tables remain available.

The deck has thirteen slides and a 300-second budget. Preparation notes separate the verbatim English script, Chinese explanation, follow-up answer and evidence locator. The notes are also supplied as DOCX/PDF. The ten-question live sheet complements the internal twenty-five-question guide.

## Revision 3 owner correction

The exact owner-edited PowerPoint is the current master, restored with a checksum-verified copy rather than reauthoring. Its cover author is CHAN Sing Yeung and its closing school-deadline line is removed. The six report pairs and notes use the corrected formal author. Report scientific content, table values, Q01–Q25 and the planned script are unchanged. Written school requirements remain in the planning section.

## Presentation rubric map

| Slide | Appendix II areas | Contribution |
|---|---|---|
| 1 | I, III | Accepted research title and bounded scope. |
| 2 | I, II, III | Four evaluation questions with 28/28/11/17 coverage. |
| 3 | I, II | Separate protocols, seed budgets and shared-window contract. |
| 4 | I, II | Reproduction MSE/MAE directions and unresolved causes. |
| 5 | I, III | Editable leading-three accuracy chart with implementation scope. |
| 6 | I, II | Timing/height metrics and adapted joint mean-error screen. |
| 7 | I, II | Passing-cell locations and actual ordering at both ends. |
| 8 | I, II | Measured subset frontier with parameter/runtime distinction. |
| 9 | I, II | Correct Holm, resolution limit and no-equivalence explanation. |
| 10 | I, II | Restricted frozen-feature negative result. |
| 11 | I, II | Static token-order hypothesis versus unexecuted runtime. |
| 12 | II, III | Accepted O1 priorities and conditional O2 cost. |
| 13 | I, III, IV | Qualified conclusion and supervision decision; deadline line removed by owner. |

Area IV still needs actual rehearsal. A pacing budget, readable slides and preparation material cannot establish live delivery performance or an A-range grade.
'''
 text=text.replace('## Presentation rubric map','## Revision 4 paper-backed explanations\n\nAll Q01–Q25 now connect a direct local answer with a named-paper argument, a specific reading location and a short supervisor response. QA_CITATION_MAP.md/.json records every link. The complete supervisor guide mirrors both languages, and the external notes/live Q&A carry matching paper support. Seven methodological references extend the internal list to 25. School and manuscript report pairs, the owner-edited PPTX/PDF and the planned English speech remain unchanged.\n\nThe original split rationale is strengthened by Tan et al. §3.3 (Illness 70/10/20) and iTransformer Appendix A.1 (chronological separation). The original three-seed citation is corrected: PatchTST A.6.1 and iTransformer A.2/Table 5 report five-seed robustness. PatchTST A.6.2 also reports ILI sensitivity to model settings. These passages explain why a three-seed compute compromise and a cross-model parameter regression do not settle robustness or tuning importance.\n\nThe added methods explain leakage, measurement scale, Holm, equivalence, causal masking and forecast evaluation. Tashman is used only at publisher-indexed abstract depth; direct publisher access was blocked. No unseen upstream defect or unexecuted model outcome is promoted to fact. This is a literature/explanation revision, with no new training or HPC result.\n\n'+'## Presentation rubric map')
 p.write_text(text)
 p=A/'CHANGES.md';s=p.read_text();marker='## Revision 2'
 if marker in s:s=s[:s.index(marker)]
 s+='''\n## Revision 2: four-axis presentation and restored internal teaching material

- Restored the six explicit original explanations and added surrounding support as Q01–Q25, in both internal reports beside their evidence. Exact mapping is in QA_RESTORATION_MAP.md. The complete current paragraph/table differences are in DOCUMENT_DIFFS.md.
- Retained all corrected science: proper Holm 0/136, raw 128/136, frontier p 0.1172, 13+4+11 roster, MIFlu in the 17-model paired family, bounded frozen-feature result, and no-text runtime marked not executed.
- Rebuilt the entire thirteen-slide deck around four axes with different model coverage. The new cover uses the accepted title and avoids an unproved decoupling claim.
- Added editable reproduction/accuracy charts and an actual source-derived passing-cell grid. Enlarged Pareto labels on a separate presentation-specific figure while retaining all eleven measured points.
- Regenerated the planned five-minute script, embedded bilingual preparation notes, ten-question sheet, complete supervisor guide and bilingual notes DOCX/PDF. Actual human delivery remains not executed.
- Added Q01–Q25 retention checks and actual notes/chart-data checks, and normalised embedded chart workbook metadata for deterministic repeat builds.
- Corrected a malformed MIFlu DOI link in LITERATURE_REVIEW.md to 10.1109/JBHI.2025.3561214. The source ledger and manuscript citation already carried the correct DOI.
- Refreshed every report PDF/DOCX pair, counts, inventories, README instructions and both delivery archives. All frozen input CSV hashes remain unchanged.
''';s+='\n## Revision 3: owner-corrected PowerPoint synchronisation\n\n- Preserved the uploaded PowerPoint byte for byte, including user formatting and the resized cover author box. The cover now says CHAN Sing Yeung; the closing deadline line is removed. Slide footers remain exactly as uploaded.\n- Updated formal authorship across all six DOCX/PDF report pairs, report metadata, README and bilingual notes. The scientific slide text, native chart values, 300-second script and all 25 internal-report questions are unchanged.\n- Retained the verified school deadline in written planning sections; its removal from the slide is not treated as cancellation.\n- Made build_deck.py restore the checksum-verified owner master. The original programmatic alternative is retained separately and does not overwrite manual changes.\n- Updated the root CITATION.cff author, obsolete reproduction abstract and MIFlu given names against the existing verified ledger; repository URLs and licence handles are unchanged.\n- Refreshed PDF exports, inventories, current verification records and both delivery archives. No source CSV or forecast data changed.\n';s+='\n'+'## Revision 4 paper-backed explanations\n\nAll Q01–Q25 now connect a direct local answer with a named-paper argument, a specific reading location and a short supervisor response. QA_CITATION_MAP.md/.json records every link. The complete supervisor guide mirrors both languages, and the external notes/live Q&A carry matching paper support. Seven methodological references extend the internal list to 25. School and manuscript report pairs, the owner-edited PPTX/PDF and the planned English speech remain unchanged.\n\nThe original split rationale is strengthened by Tan et al. §3.3 (Illness 70/10/20) and iTransformer Appendix A.1 (chronological separation). The original three-seed citation is corrected: PatchTST A.6.1 and iTransformer A.2/Table 5 report five-seed robustness. PatchTST A.6.2 also reports ILI sensitivity to model settings. These passages explain why a three-seed compute compromise and a cross-model parameter regression do not settle robustness or tuning importance.\n\nThe added methods explain leakage, measurement scale, Holm, equivalence, causal masking and forecast evaluation. Tashman is used only at publisher-indexed abstract depth; direct publisher access was blocked. No unseen upstream defect or unexecuted model outcome is promoted to fact. This is a literature/explanation revision, with no new training or HPC result.\n\n';p.write_text(s)
 files=list(ROOT.rglob('*.py'));errors=[]
 for f in files:
  try:ast.parse(f.read_text(encoding='utf-8-sig'))
  except Exception as ex:errors.append({'file':str(f.relative_to(ROOT)),'error':str(ex)})
 (A/'STATIC_SCAN.json').write_text(json.dumps({'python_files':len(files),'parse_errors':errors},indent=2)+'\n');assert not errors
 p=A/'REPO_AUDIT.md';s=p.read_text();s=re.sub(r'Static Python syntax scan: \d+ files inspected',f'Static Python syntax scan: {len(files)} files inspected',s);p.write_text(s)
 frozen=json.loads((A/'INPUT_SHA256.json').read_text());assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
 print('Refreshed six-report metadata, complete diffs, QA restoration and source hash check.')
if __name__=='__main__':refresh()
