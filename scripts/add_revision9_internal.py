#!/usr/bin/env python3
"""Append the current editorial/handoff analysis without deleting the 25 cited questions."""
from pathlib import Path
import json,hashlib
from docx import Document
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'01_最终报告';TITLE='修订 9 更新与后续科学改写'

def build():
 p=OUT/'report_internal_zh.docx';d=Document(p)
 if any(x.text==TITLE for x in d.paragraphs):print('Revision 9 addendum already present');return
 old_tables=[[[c.text for c in r.cells] for r in t.rows] for t in d.tables];old_q=[p.text for p in d.paragraphs if p.text.startswith('Q') and p.text[1:3].isdigit()]
 d.add_page_break();d.add_heading(TITLE,1)
 for title,text in [
 ('英文论文的角色已重整','英文稿现按期刊论文的研究问题、方法、结果、讨论与局限组织，去除作业编号、队列 DONE 状态和 F0–F5 等内部审计标签。训练消融的逐变体结果仍未核实，不能把 60/60 队列完成写成已证明深度或 LoRA 效应。三项固定权重 CPU 检查仅支持所测前向路径的不变性，不能扩展为训练轨迹相同或语言预训练没有作用。原有科学数值保持历史快照，不因文字润色而改变。'),
 ('版式核实的范围','2026 年 11 月 5 日直接读取 IEEE JBHI 作者指南，已核实单倍行距、双栏、正文嵌入图表、摘要不超过 250 词；常规论文上限为 14 页，含补充材料。官方页面将模板指向 IEEE 选择器，但选择器本次返回 HTTP 418。新的英文 PDF 使用 IEEE EMBS 官方页面所链接的 ieeecolor 期刊类在本地编译；不能声称已经在 Overleaf 网站执行或核实为选择器当前下载的同一文件。当前指南原文链接与模板哈希见 manuscript/TEMPLATE_PROVENANCE.json。'),
 ('保留给导师的解释','本报告原有 Q01–Q25、文献推理、阅读位置、科学表格及图形全部保留。英文期刊稿的参考文献按首次引用重新编号，不能把其编号直接套用到本报告问答。英文演讲准备稿另提供完整论文理由，逐字讲稿仍为计划 5:00；真人排练未执行。'),
 ('下一份结果的优先级','O1 仍为默认：先取得 MIFlu 完整七通道预测，统一裁剪窗口与全部有效窗口评分，再完成共同矩阵、匹配基线的逐变体消融，以及区域、滚动原点和数值时序基础模型对照。核心 160/160 产物完成不能替代共同评分；117 打包记录与 141 用户报告均为既有采集时刻，不是本次实时计数。不要重复汇总核心与全国重叠单元。'),
 ('O2 与后续改写','O2 仅作可选的验证集拟合峰高校正；只有合规的验证与测试导出已齐备时，才可说不需新增 GPU 训练，CPU 时间仍须测量。每次新交接先核查原始预测、配置、哈希、分母及依赖单位，再同步改写论文、内部报告、FYP、期刊记录、README、PPT 与讲稿。新证据可以改变原排名或结论，不能强迫其维持旧数值。PROMPT_TO_DEEPSEEK.md 与 RETURN_CONTRACT.json 规定应交回的材料。')]:
  d.add_heading(title,2);d.add_paragraph(text)
 d.core_properties.comments='Revision 9 editorial and return-analysis addendum; original questions and scientific content preserved.';d.save(p)
 assert old_tables==[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
 assert old_q==[p.text for p in d.paragraphs if p.text.startswith('Q') and p.text[1:3].isdigit()]
 print('Chinese internal addendum built; 25 questions and all scientific table cells preserved.')
if __name__=='__main__':build()
