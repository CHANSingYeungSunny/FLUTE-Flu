# -*- coding: utf-8 -*-
"""TASK 7 v8 Chinese internal report builder.

Mirrors HANDOFF_20261105/build_v7_internal_zh.py (python-docx + LibreOffice-kit
CLI convert) but rebuilds the BODY with the final v8 verified results and an
explicit V8 old-snapshot-vs-new-panels separation section. Frozen CSVs /
predictions / checkpoints / PPTX are not touched.
"""
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8")
OUT.mkdir(parents=True, exist_ok=True)
doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Inches(0.8)
    s.left_margin = s.right_margin = Inches(0.9)
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style.font.size = Pt(10)


def set_zh(run, size=10, bold=False):
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def h(t, l=1):
    pgh = doc.add_heading(t, level=l)
    for r in pgh.runs:
        set_zh(r, 14 if l == 1 else 11, True)


def p(t, size=10, bold=False):
    par = doc.add_paragraph()
    r = par.add_run(t)
    set_zh(r, size, bold)
    return par


def table(head, rows, cap):
    p(cap, 9, True)
    t = doc.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    for i, x in enumerate(head):
        c = t.rows[0].cells[i]
        c.text = str(x)
        for r in c.paragraphs[0].runs:
            set_zh(r, 8, True)
    for row in rows:
        cs = t.add_row().cells
        for i, x in enumerate(row):
            cs[i].text = str(x)
    doc.add_paragraph()


p("MIFlu 与 27 个流感预测实现的共同十种子重评（V8 中文技术报告）",
  15, True).alignment = WD_ALIGN_PARAGRAPH.CENTER
p("CHAN Sing Yeung｜香港城市大学电子工程学系｜2026-11-06｜草稿，非投稿就绪",
  8).alignment = WD_ALIGN_PARAGRAPH.CENTER
p("旧 revision-9.2 冻结 28-arm 快照、新 1120 单元全国面板、legacy 五折 walk-forward "
  "面板为三个不同评分总体，分开报告，禁止混算。", 8).alignment = WD_ALIGN_PARAGRAPH.CENTER

h("摘要")
p("我们在 966 周全国 ILI 序列上，用同一协议（T=104，L=24/36/48/60，seeds "
  "2021–2030，28 个实现）完成 1,120 个单元。从检查点恢复七通道预测，在 all-valid "
  "与历史 crop 两个相同目标总体面板上重算：all-valid 领先 MSE 为 MIFlu 1.7944、"
  "PatchTST 1.9521、NLinear 2.0782；crop 为 1.4994/1.6352/1.9027，重现旧值 "
  "1.4995。峰值结论改变：MIFlu 252/1680（15.0%）、PatchTST 215/1680（12.8%）、"
  "NLinear 57/1680（3.4%）。60 格深度/LoRA 阶梯非单调：K4 最佳 1.4989，K12 最差 "
  "1.7604。V8 关键更新：LEGACY 五折 N=3 walk-forward 面板现已完成——1,020/1,020 "
  "从原始 NPZ 重算为 ok（补回 218 格，0 个已有 ok 值被改动），全面板每模型均值 "
  "n=60（MIFlu 2.220289、PatchTST 3.039638、NLinear 3.211592）。该 legacy 面板与 "
  "1120 全国面板是不同评分总体，禁止与 CELL_METRICS.csv 合并。数值基础模型 "
  "Chronos/TimesFM 仍 BLOCKED（无权重/环境/pilot，具名检查点为单变量）；CDC 官方发布"
  "日历/修订号不存在且峰值重评分 BLOCKED，峰值仍是回顾性最终 vintage；资源为 PARTIAL "
  "子集（真实训练墙钟与 NPZ 评分路径延迟，明确非模型前向，peak VRAM NOT_MEASURED）；"
  "JBHI 有日期校验记录（14 页、≤250 词、双栏、APC US$2,800 2026 已核实），但模板"
  "类文件 UNVERIFIED，submission-ready: NO。新面板与冻结旧快照分开保留。")

h("1. 数据与协议")
p("数据为 966 行、七通道，按 676/97/193 切分（边界 0/676/773/966），T=104，"
  "L=24/36/48/60，strict containment，seeds 2021–2030。28 个实现 = 13 个传统模型 "
  "+ 4 个 LLM 预测器 + 11 个冻结语言编码器加共享线性读出。名义 28×4×10=1,120 个"
  "单元；确定性拟合按有效重复数单列。LEGACY walk-forward 是不同协议（五折、"
  "seeds 42/43/44、N=3），见第 5 节。")

h("2. 评分面板")
p("all-valid 使用全部有效测试窗口（170/158/146/134）；crop 使用前 (W//16)×16 个"
  "窗口（160/144/144/128），即历史 complete-batch 规则。MSE/MAE 为七通道 z-space "
  "均值；峰值用 ILITOTAL 患者数，按 train-fit scaler 反归一化。峰检测 "
  "find_peaks(prominence=0.15×range, distance=15)，±8 周一对一匹配，PTE≤1 周且 "
  "PIE≤25% 记为通过。")

h("3. 结果（新 1120 全国面板）")
table(["模型", "MSE all-valid", "MSE crop", "MAE all-valid"],
      [["MIFlu", "1.7944", "1.4994", "0.8529"],
       ["PatchTST", "1.9521", "1.6352", "0.9244"],
       ["NLinear", "2.0782", "1.9027", "0.9652"],
       ["DNN", "2.2802", "2.1173", "1.0401"],
       ["TimeCMA", "2.6255", "2.5765", "1.0879"]],
      "表 1. 两个共同面板的领先平均误差（28 模型，十种子，四跨度）。")
p("两个面板领先顺序一致：MIFlu < PatchTST < NLinear。crop 的 MIFlu 1.4994 与旧 "
  "1.4995 一致，验证七通道恢复；all-valid 提高所有误差但不改变前三名。")

table(["模型", "平均 PTE（周）", "平均 PIE（%）", "通过 / 1680"],
      [["PatchTST", "0.707", "34.41", "215（12.8%）"],
       ["MIFlu", "0.964", "30.09", "252（15.0%）"],
       ["NLinear", "2.013", "42.35", "57（3.4%）"],
       ["DNN", "1.690", "51.54", "0"]],
      "表 2. step-level Kramer–Shaman 结果（每模型 10 seeds × 168 leads）。")
p("事件级检测与幅度分离：iTransformer 检测 99.1% 但 PIE 71.2%；MIFlu 98.8% 且 "
  "PIE 30.4%；PatchTST 97.6% 且 PIE 34.6%；NLinear 92.6% 且 PIE 40.6%。旧"
  "「NLinear 峰值冠军」在新面板不成立；旧 16 单元表与新 1680 step rows 不是同一总体。")

table(["变体", "单元", "平均 MSE"],
      [["K4", "12", "1.4989"], ["K6 参考", "10", "1.5457"],
       ["K2", "12", "1.5813"], ["K8", "12", "1.6124"],
       ["no_lora", "12", "1.6330"], ["K12", "12", "1.7604"]],
      "表 3. 深度/LoRA 阶梯，七通道 z-space MSE。")
p("深度非单调：K4 最佳，K12 最差；不得再声称单调深度趋势。")

h("4. 外部效度、统计与已完成项")
p("区域 Table VI：53/53 有效 mse_z 聚合行（补跑 L13/s2030 与 L15/s2026 后）；为 "
  "10 变量区域聚合，不可与七通道全国均值混算。旧「Table VI 缺 2 格 / 51/53」"
  "说法已被 53/53 取代。`final_llm_import`（T3）已产出真实 "
  "BENCH_MSE_BY_MODEL_L.csv（sha256 2e03b510…），基于 386 个可读 legacy 单元，"
  "2 个损坏 MIFlu NPZ 已隔离（未删除）——这是 LEGACY 分析树表，不是 1120 面板。")
p("统计：378 对 Wilcoxon + Holm，349/378 拒绝，最小校正 p≈6.9e-10；按 seed 的 "
  "cluster bootstrap 有 359/378 的 95% CI 排除 0。但同一 seed 内 L 与目标重叠，"
  "仍是探索性，不是确认性推断；依赖感知/blocked 分析仍未做。")

h("5. LEGACY walk-forward 面板已完成（T1，V8）")
p("Job 743850（stingy / gpu-a100-03）以 rc=0 补跑全部 218 个此前 SKIPPED 的 "
  "legacy 单元；Job 744334 用 v8/scripts/wf_recompute.py 从原始 NPZ 重算。"
  "HANDOFF_20261105/final/WF_RECOMPUTED.csv 现为 1,020/1,020 行 status=ok"
  "（sha256 53d0e0cb36e726db46c29066101be316bbf9e0de7ea1a228bf84ba7f885ef80b），"
  "WF_RECOMPUTED_MEANS.csv sha256 "
  "c0e72f35f29d4df32762b9c0a03f69df576405ead495e91a43320dc0774d5813。基线差异："
  "recovered_218_count=218、changed_existing_ok_values=0、lost_existing_ok=0、"
  "still_missing=0——没有任何已有 ok 值被改动。网格为 5 折 × 204 单元 = 1,020，"
  "17 个模型，每模型 n=60。")
table(["模型", "n", "全面板均值 MSE", "模型", "n", "全面板均值 MSE"],
      [["miflu", "60", "2.220289", "calf_llm", "60", "4.391592"],
       ["patchtst", "60", "3.039638", "svr", "60", "4.412095"],
       ["nlinear", "60", "3.211592", "decision_tree", "60", "4.514915"],
       ["dnn", "60", "3.648969", "cnn", "60", "4.515521"],
       ["gradient_boosting", "60", "3.915091", "lstm", "60", "4.655853"],
       ["timecma_llm", "60", "3.924265", "gru", "60", "4.742699"],
       ["random_forest", "60", "3.925170", "rnn", "60", "4.785940"],
       ["knn", "60", "3.967265", "qwen_time_llm", "60", "4.826157"],
       ["itransformer", "60", "3.977386", "", "", ""]],
      "表 4. LEGACY walk-forward 全面板每模型均值（n=60），由 1,020 原始单元重算。"
      "不是 1120 全国面板。")
p("关键溯源：这是 LEGACY 五折 N=3 walk-forward 面板（seeds 42/43/44），不是新 "
  "28-arm 全国十种子（2021–2030）面板。20 个网格外的 wf_f*_miflu_*_s2021 "
  "rolling-origin 行仍不在范围内。它与 CELL_METRICS.csv 是不同评分总体，禁止"
  "合并或朴素比较：MIFlu 的 WF 2.220289 与全国 all-valid 1.7944 不是同一量。"
  "旧 v7「802/1020 有效、218 缺 NPZ / partial / invalid / 473/1020」说法均被"
  "1,020/1,020 ok 明确取代。")

h("6. 基础模型（T2，BLOCKED）")
p("Chronos/TimesFM 数值基础模型未运行，T2 为 BLOCKED 且有精确证据。"
  "v8/foundation/FOUNDATION_ROSTER.csv 与 FOUNDATION_MODEL_PROVENANCE.md 固定了"
  "仓库/revision/licence。精确缺失输入：无完整权重（model.safetensors / TimesFM "
  "checkpoint）、无 tar+scp 到 /gpfs1/scratch/sychan552/models/、无隔离 HPC 环境"
  "/home/sychan552/.venvs/mlflu_fm、无 1-cell pilot、无 80 单元矩阵；所有命令 rc=0，"
  "是文档化的缺失输入条件而非网络错误。具名 Chronos T5/Bolt 与 TimesFM 1.0/2.0 "
  "检查点为单变量，7 通道需文档化逐通道适配器且会丢弃跨通道依赖，不是忠实的"
  "多变量对照；TimesFM 3.0 权重为非商业许可，google/timesfm-2.0-500m 返回 HTTP 401。"
  "11 个冻结语言编码器不是替代品。保留 SEPARATE roster，绝不并入 28-arm 家族。")

h("7. CDC vintage 与实时声明（T4，PARTIAL/BLOCKED）")
p("v8/cdc_vintage/cdc_vintage.csv 含 20 行真实抓取的 Delphi Epidata 代理行"
  "（release_date + issue + affected weeks），每行 cdc_official_revision_id="
  "NOT_AVAILABLE。CDC 不发布官方发布日历或修订号；归档最终 CSV 不是 vintage。"
  "按 as-of 数据的峰值重评分 BLOCKED：缺少 step → absolute row → CDC MMWR "
  "epiweek 映射（冻结峰值表为 step 索引，评分脚本不在 Windows 树中）。未发明映射、"
  "未改写峰值 CSV。峰值仍为回顾性最终 vintage：本报告不作实时/临床声明。")

h("8. 资源测量（T6，PARTIAL）")
p("v8/RESOURCE_MEASUREMENTS.csv 仅为子集，每行 scope=subset_only_not_full_1120，"
  "不声称 full-1120 Pareto。真实训练墙钟（队列日志）：MIFlu 581 s、NLinear 6 s、"
  "PatchTST 7 s、冻结编码器 DeepSeek-R1-Distill-Qwen-1.5B 24 s。真实 NPZ 评分"
  "路径延迟 0.0287–0.0297 ms（warm-up 5 / repeat 50），明确不是模型前向。"
  "sbatch 内实测版本：Python 3.9.25、numpy 2.0.1、pandas 2.3.3、torch 2.5.1。"
  "所有行 peak_vram_mib=NOT_MEASURED（无 GPU 分配，GPU 作业取消 / stingy 被 "
  "QOSMaxSubmitJobPerUserLimit 拒绝）。Chronos/TimesFM 行 BLOCKED/NOT_EXECUTED。"
  "未发明任何 VRAM 或前向延迟。")
table(["子集模型", "训练墙钟 (s)", "NPZ 评分路径延迟 (ms)", "peak VRAM"],
      [["MIFlu", "581", "0.029084", "NOT_MEASURED"],
       ["NLinear", "6", "0.029651", "NOT_MEASURED"],
       ["PatchTST", "7", "0.028653", "NOT_MEASURED"],
       ["DeepSeek-R1-Distill-Qwen-1.5B", "24", "0.028685", "NOT_MEASURED"],
       ["Chronos", "NOT_MEASURED", "NOT_MEASURED", "NOT_MEASURED (BLOCKED)"],
       ["TimesFM", "NOT_MEASURED", "NOT_MEASURED", "NOT_MEASURED (BLOCKED)"]],
      "表 5. V8 资源子集（PARTIAL）。延迟是 NPZ 评分路径，不是模型前向。")

h("9. JBHI 校验（T5，带日期记录）")
p("v8/JBHI_VERIFICATION_20261106.md（2026-11-06）实时 HTTP 200 + 逐字引用核实："
  "14 页 regular / 16 页 review 含补充材料、摘要 ≤250 词、IEEE 单倍行距双栏、"
  "图表嵌入、IEEE 全局 AI 使用披露（致谢；语法/编辑例外）、混合 OA、APC "
  "US$2,800（2026）。官方模板类文件 UNVERIFIED：选择器浏览器 UA 返回 404、完整 "
  "python-requests 默认头返回 WAF 418、API 路径 302→502。418 是客户端画像的 "
  "WAF 拦截，不是缺页。manuscript_submission_ready: NO；本文为草稿。")

h("10. V8 — 旧快照 vs 新面板（明确标注的分离章节）")
p("明确标注的 V8 分离章节。三个不同总体共存，禁止合并、平均或朴素比较；本节"
  "逐条列出被取代的旧声明，绝不静默覆盖旧结论。", bold=True)
table(["标签", "总体 / 协议", "位置", "V8 状态"],
      [["OLD 冻结快照", "28 arms；Holm 0/136（p_raw 前向累积最大）；"
        "NLinear–PatchTST 0.1172；4/16 聚合单元；旧 NLinear K&S 冠军",
        "02_数字表格/*.csv（冻结）", "保留，标注旧"],
       ["NEW 全国面板", "28 模型×4 L×10 seeds 2021–2030=1120；"
        "MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782",
        "final/CELL_METRICS.csv", "COMPLETE，分开"],
       ["LEGACY walk-forward", "5 折×204=1020；seeds 42/43/44；MIFlu 2.220289",
        "final/WF_RECOMPUTED.csv", "1020/1020 ok，分开"],
       ["LEGACY 分析树", "386 可读单元；final_llm_import",
        "HPC paper_tables/BENCH_MSE_BY_MODEL_L.csv", "真实，legacy，分开"],
       ["PROXY CDC vintage", "20 行 Delphi issue；官方 id NOT_AVAILABLE",
        "v8/cdc_vintage/cdc_vintage.csv", "PARTIAL / BLOCKED"],
       ["SEPARATE 基础模型 roster", "8 个固定候选，0 执行",
        "v8/foundation/FOUNDATION_ROSTER.csv", "BLOCKED，分开"]],
      "表 6. V8 旧快照 vs 新面板分离（RULE 4 溯源）。")
p("被明确取代的旧声明：(1)「NLinear 为 K&S 峰值冠军（4/16）」在新 1120 面板"
  "不复现（MIFlu 252/1680、PatchTST 215/1680、NLinear 57/1680），旧 16 单元表是"
  "不同总体；(2)「单调深度趋势」被非单调阶梯取代（K4 最佳、K12 最差）；"
  "(3)「walk-forward partial / 802/1020 / 218 缺失 / 473/1020」被 1,020/1,020 ok "
  "取代（LEGACY 面板）；(4)「Table VI 缺 2 格 / 51/53」被 53/53 有效取代；"
  "(5)「final_llm_import TODO / 无输出」被真实重建 legacy 表取代（386 单元隔离"
  "注意项）；(6)「资源表 NOT EXECUTED」被 PARTIAL 实测子集取代；"
  "(7)「JBHI UNVERIFIED」被带日期校验记录取代（模板类文件仍 UNVERIFIED）；"
  "(8)「v7 DOCX/PDF NOT EXECUTED」被 v7 与 v8 文档取代。冻结 CSV 保持逐字节不变。")

h("11. 限制")
p("单一全国序列；四个跨度复用观测；十种子不是十个独立流行季；CDC 发布日历/"
  "vintage 未重建，峰值是回顾性；11 个编码器只测冻结特征+线性读出；"
  "数值基础模型 BLOCKED 未运行；资源是子集，无 peak VRAM、无模型前向延迟；"
  "LEGACY walk-forward 已完成但与 1120 全国面板是不同总体；JBHI 模板类文件 "
  "UNVERIFIED；T8 包校验 PASS 仅结构性（scientific_readiness: NOT_ASSESSED）。"
  "本文是 v8 草稿，不是投稿就绪版本。")

h("12. 结论")
p("在完整 1,120 单元共同面板上，MIFlu 七通道 MSE 最低，PatchTST 平均峰值时间"
  "最好，MIFlu step-level 峰值通过最多；旧 NLinear 峰值冠军不复现；深度非单调。"
  "V8 中 LEGACY 五折 walk-forward 面板以 1,020/1,020 ok 完成，但它是与全国面板"
  "分离的评分总体，禁止合并。基础模型、CDC 官方 vintage/峰值重评分、GPU peak "
  "VRAM 与 JBHI 模板仍如实标为 BLOCKED / NOT_MEASURED / UNVERIFIED。所有新结果"
  "作为独立、明确标注的面板给出；冻结的旧快照保持完整。")

src = OUT / "report_internal_zh_v8.docx"
doc.save(src)
NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
pdf = src.with_suffix(".pdf")
if pdf.exists():
    pdf.unlink()
r = subprocess.run([NODE, CLI, "convert", "--input", str(src), "--output", str(pdf)],
                   capture_output=True, text=True, errors="replace")
print("report_internal_zh_v8", src.stat().st_size,
      pdf.stat().st_size if pdf.exists() else 0, r.returncode)
