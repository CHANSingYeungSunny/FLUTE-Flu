# -*- coding: utf-8 -*-
"""TASK 7 v8 Chinese Q&A companion builder.

Mirrors HANDOFF_20261105/build_v7_qa.py: copy the original 25-question
companion (Q01-Q25 preserved verbatim), add a page break and a clearly-labelled
"V8 — old snapshot vs new panels" separation section plus a superseded-claims
index. No old answer is silently overwritten; the appended section states which
claims are superseded and by what verified v8 result. Frozen CSVs / predictions /
checkpoints / PPTX are not touched.
"""
import shutil
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

SRC = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\report_internal_qa_zh.docx")
OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_qa_zh_v8.docx")
OUT.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(SRC, OUT)
d = Document(OUT)


def set_zh(run, size=9, bold=False):
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def p(t, b=False, size=9):
    par = d.add_paragraph()
    r = par.add_run(t)
    set_zh(r, size, b)
    return par


d.add_page_break()
h = d.add_heading("V8 — 旧快照 vs 新面板（明确标注的分离章节）", level=1)
for r in h.runs:
    set_zh(r, 13, True)

p("本附录不删除、不改写原 Q01–Q25 的题目与原有答案文本；它明确列出在 V8 已验证"
  "状态下被取代的旧声明，并给出新面板的正确答案索引。旧结论不被静默覆盖。"
  "证据见 HANDOFF_20261105/v8/docs/V8_SCIENTIFIC_ADDENDUM.md、"
  "HANDOFF_20261105/v8/SCIENTIFIC_AUDIT.md、HANDOFF_20261105/v8/"
  "BLOCKED_AND_UNVERIFIED.md。", True)

p("【V8 分离原则】冻结旧快照（02_数字表格/，28 arms，Holm 0/136 由 p_raw 前向"
  "累积最大，NLinear–PatchTST 0.1172，4/16 聚合单元，旧 NLinear K&S 冠军）、"
  "新 1120 单元全国十种子（2021–2030）面板、LEGACY 五折 N=3 walk-forward 面板"
  "（seeds 42/43/44）、LEGACY final_llm_import 分析树、Delphi CDC 代理 vintage、"
  "以及基础模型 SEPARATE roster 是六个不同的评分总体，禁止合并、平均或朴素比较。"
  "V8 已把这些面板分开报告。", True)

p("一、被明确取代的旧声明（SUPERSEDED，逐条对应）", True)
p("1. 旧「NLinear 为 K&S 峰值冠军（4/16）」→ 在新 1120 面板不复现：step-level "
  "通过数 MIFlu 252/1680（15.0%）、PatchTST 215/1680（12.8%）、NLinear 57/1680"
  "（3.4%）。旧 16 单元表与新 1680 step rows 不是同一总体，须标注为旧快照。")
p("2. 旧「单调深度趋势」→ 60 格阶梯非单调：K4 1.4989 最佳、K6 1.5457（n=10）、"
  "K2 1.5813、K8 1.6124、no_lora 1.6330、K12 1.7604 最差。删除任何单调趋势说法。")
p("3. 旧「walk-forward partial / 802 of 1020 有效 / 218 缺 NPZ / 473 of 1020 / "
  "invalid」→ V8 T1 已完成：final/WF_RECOMPUTED.csv 为 1,020/1,020 status=ok"
  "（sha256 53d0e0cb…），218 格补回、0 个已有 ok 值被改动、0 lost、0 still_missing。"
  "5 折 × 204 单元、17 模型、每模型 n=60；全面板每模型均值（n=60）：miflu 2.220289、"
  "patchtst 3.039638、nlinear 3.211592、dnn 3.648969、gradient_boosting 3.915091、"
  "timecma_llm 3.924265、random_forest 3.925170、knn 3.967265、itransformer 3.977386、"
  "calf_llm 4.391592、svr 4.412095、decision_tree 4.514915、cnn 4.515521、"
  "lstm 4.655853、gru 4.742699、rnn 4.785940、qwen_time_llm 4.826157。"
  "但这是 LEGACY 五折 N=3 面板（seeds 42/43/44），不是 1120 全国面板，禁止与 "
  "CELL_METRICS.csv 合并。20 个网格外 wf_f*_miflu_*_s2021 rolling-origin 行仍不在范围内。")
p("4. 旧「Table VI 缺 2 格 / 51/53」→ 53/53 有效 mse_z 聚合行（补跑 L13/s2030 与 "
  "L15/s2026 后）；仍为 10 变量区域聚合，不可与七通道全国均值混算。")
p("5. 旧「final_llm_import TODO / idle-no-work / 无输出」→ T3 已产出真实 "
  "BENCH_MSE_BY_MODEL_L.csv（sha256 2e03b510…），基于 386 个可读 legacy 单元，"
  "2 个损坏 MIFlu NPZ 已隔离（未删除）。这是 LEGACY 分析树表，不是 1120 面板。")
p("6. 旧「资源/效率表 NOT EXECUTED」→ T6 为 PARTIAL：真实训练墙钟 MIFlu 581 s、"
  "NLinear 6 s、PatchTST 7 s、DeepSeek-R1-Distill-Qwen-1.5B 24 s；NPZ 评分路径"
  "延迟 0.0287–0.0297 ms（明确非模型前向）；版本 Python 3.9.25 / numpy 2.0.1 / "
  "pandas 2.3.3 / torch 2.5.1。peak_vram_mib 全部 NOT_MEASURED；每行 "
  "scope=subset_only_not_full_1120，不声称 full-1120 Pareto。")
p("7. 旧「JBHI 模板/费用/AI 披露 UNVERIFIED / 未复核」→ T5 带日期校验记录已核实 "
  "14/16 页含补充材料、摘要 ≤250 词、单倍行距双栏、图表嵌入、AI 使用披露、"
  "APC US$2,800（2026）。仅官方模板类文件仍 UNVERIFIED（404 / WAF 418 / 302→502）。"
  "submission-ready: NO。")
p("8. 旧「CDC vintage 未重建，峰值回顾性」→ 细化为 PARTIAL/BLOCKED：已建 20 行 "
  "真实抓取的 Delphi 代理 cdc_vintage.csv（cdc_official_revision_id=NOT_AVAILABLE），"
  "但 CDC 官方发布日历/修订号不存在、峰值重评分 BLOCKED（缺 step → MMWR epiweek "
  "映射）。峰值仍是回顾性最终 vintage，不作实时/临床声明。")
p("9. 旧「v7 DOCX/PDF NOT EXECUTED」→ v7 DOCX/PDF 已存在；V8 三个 DOCX/PDF 已"
  "更新正文（不只是附录）并含本分离章节。")

p("二、需按 V8 更新的答案索引（保留 Q01–Q25 题号与引用）", True)
p("峰值题：改为 MIFlu/PatchTST 领先、NLinear 不复现冠军；明确旧 16 单元表为不同"
  "总体。MSE 排名题：新 all-valid MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782；"
  "crop 1.4994/1.6352/1.9027；旧 1.4995/1.6621/1.8716 属旧快照，不能与新面板混写。"
  "消融题：非单调，删除单调深度说法。Walk-forward / 外部效度题：LEGACY 面板 "
  "1,020/1,020 ok 但仍是不同总体；Table VI 53/53；不能写成 1120 泛化验证完成。"
  "统计题：378 对 Wilcoxon + Holm 349/378 拒绝、cluster bootstrap 359/378，均为"
  "探索性（cell 共享同一序列与重叠目标），不得称确认性显著。复现题：MIFlu crop "
  "1.4994 重现旧 1.4995；新 all-valid 1.7944 是不同 panel。")
p("新增题类（V8）：基础模型题答 BLOCKED（无权重/环境/pilot；具名 Chronos/TimesFM "
  "检查点为单变量，7 通道需丢弃跨通道依赖的逐通道适配器；TimesFM 3.0 非商业；"
  "11 个冻结编码器不是替代品；SEPARATE roster 不并入 28-arm）。资源题答 PARTIAL "
  "子集、NOT_MEASURED 的 VRAM/前向、scope=subset_only_not_full_1120。CDC vintage "
  "题答代理表 + 官方 id NOT_AVAILABLE + 峰值回顾性。JBHI 题答带日期已核实但模板 "
  "UNVERIFIED、submission-ready NO。数值溯源题答旧快照 / 新 1120 / LEGACY WF / "
  "LEGACY 分析树 / PROXY CDC / SEPARATE foundation 六个总体分开。")

p("三、仍然 BLOCKED / NOT_MEASURED / UNVERIFIED 的项（不得写成已完成）", True)
p("T2 基础模型（无完整权重 model.safetensors / TimesFM checkpoint、无 tar+scp、"
  "无隔离 HPC 环境、无 1-cell pilot、无 80 单元矩阵）；T4 CDC 官方发布日历/修订"
  "号与峰值重评分；T5 官方模板类文件；T6 全部 peak_vram_mib 与真实模型前向延迟、"
  "Chronos/TimesFM 资源行、full-1120 Pareto；T3 两个隔离的损坏 legacy MIFlu NPZ；"
  "依赖感知/确认性统计。T8 包校验 PASS 仅结构性（scientific_readiness: "
  "NOT_ASSESSED）。每项精确证据与最小下一步见 v8/BLOCKED_AND_UNVERIFIED.md。")

p("完整证据：v8/docs/V8_SCIENTIFIC_ADDENDUM.md、v8/docs/V8_CHANGELOG.md、"
  "v8/SCIENTIFIC_AUDIT.md、v8/BLOCKED_AND_UNVERIFIED.md、"
  "final/WF_RECOMPUTED.csv、final/WF_RECOMPUTED_MEANS.csv、"
  "final/PEAK_BY_STEP.csv、v8/RESOURCE_MEASUREMENTS.csv、"
  "v8/JBHI_VERIFICATION_20261106.md。本文不把稿件称为投稿就绪。")

d.save(OUT)

NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
pdf = OUT.with_suffix(".pdf")
if pdf.exists():
    pdf.unlink()
r = subprocess.run([NODE, CLI, "convert", "--input", str(OUT), "--output", str(pdf)],
                   capture_output=True, text=True, errors="replace")
print("report_internal_qa_zh_v8", OUT.stat().st_size,
      pdf.stat().st_size if pdf.exists() else 0, r.returncode)
