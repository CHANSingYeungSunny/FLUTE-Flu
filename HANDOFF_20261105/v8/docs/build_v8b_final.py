# -*- coding: utf-8 -*-
"""v8b rebuild: replace stale T2/T4/T6 paragraphs in the 3 v8 DOCX bodies and
append a final-results section. Old claims are explicitly marked SUPERSEDED.
Then convert DOCX->PDF via the LibreOffice-kit CLI and verify page counts.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.shared import Pt

ROOT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu")
OUT = ROOT / "01_最终报告" / "v8"
DOCS = ROOT / "HANDOFF_20261105" / "v8" / "docs"
NODE = Path(r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
            r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = Path(r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
           r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")

T2_EN = ("6. Numerical foundation models (v8b, T2 — COMPLETED_WITH_DOCUMENTED_SCOPE; "
         "the earlier BLOCKED statement is SUPERSEDED). Two source-pinned numerical "
         "foundation controls were executed as a SEPARATE roster, never merged into the "
         "28-arm family. Four pinned weight tars (5,024,901,120 B) were downloaded locally "
         "on Windows, transferred to the HPC scratch, and all four remote SHA-256 values "
         "were verified inside sbatch job 744607 to match exactly. An isolated Python 3.11.13 "
         "environment (torch 2.6.0+cu124, chronos-forecasting 2.3.2, timesfm 1.3.0) was built "
         "by jobs 744574/744576. Pilot 744589 on an A100-SXM4-80GB passed with finite "
         "predictions, MSE 0.3913, inference latency 10.191 +/- 0.446 ms (warm-up 1, repeat 5) "
         "and peak VRAM 596 MiB (28 samples). Matrix 744607 produced 8/8 valid cells with real "
         "prediction files and peak VRAM 2608 MiB (18 samples). Full-panel zero-shot MSE over "
         "the 7-channel z-space: Chronos L24/36/48/60 = 0.3913 / 2.2074 / 1.7135 / 1.4002; "
         "TimesFM = 0.7298 / 2.6550 / 2.0311 / 1.6630. The requested 80-cell (2 x 4 L x 10 "
         "seeds) expansion is NOT_EXECUTED_BY_PROTOCOL: a frozen zero-shot model has no "
         "training seed dimension, so 10 seeds would yield identical predictions; the smallest "
         "faithful subset (8 cells) was run. Both checkpoints are UNIVARIATE, so the seven "
         "channels were forecast as a batch of seven independent series. This documented "
         "per-channel adapter DISCARDS cross-channel dependence and is NOT information-set "
         "matched to the multivariate arms; each model also applies its own internal scaling. "
         "No training or fine-tuning was performed. The TimesFM per-L wall/latency values in "
         "FOUNDATION_CELLS.csv are loop/slicing timings of one shared forecast call, not four "
         "independent forward passes.")

T4_EN = ("7. CDC vintage and real-time claims (v8b, T4 — COMPLETED, corrected; the earlier "
         "PARTIAL/BLOCKED statement is SUPERSEDED). The project ALREADY contained a complete "
         "frozen CDC ILINet vintage reconstruction in 02_数字表格/: cdc_vintage.csv (848 "
         "epiweeks), cdc_vintage_raw.csv (7,192 (epiweek, issue) rows) and "
         "cdc_vintage_report.md, built by 05_程序代码/cdc_vintage_build.py from the Delphi "
         "Epidata fluview endpoint. The report re-scores season peaks on as-of first-print "
         "versus final data: 18 seasons scored, 7 peak weeks move (38.9%). An archived final "
         "CSV is NOT a vintage (only 8 annual bulk-snapshot dates). Delphi release_date/issue "
         "are a reproducible PROXY, not a CDC-issued revision number; 2002 weeks have no "
         "real-time vintage. Model-panel peak metrics remain retrospective.")

T6_EN = ("8. Resource measurements (v8b, T6 — PARTIAL (IMPROVED); the earlier "
         "'all VRAM NOT_MEASURED' statement is SUPERSEDED). Job 744532 ran a REAL MIFlu "
         "forward from an existing checkpoint on gpu-a100-05 (A100-SXM4-80GB, driver "
         "580.167.08): peak VRAM 4,816 MiB from 63 nvidia-smi samples, forward wall 62.94 s, "
         "test MSE_7var_z = 1.624383, [PASS] all requested cells exported. The MIFlu row of "
         "RESOURCE_MEASUREMENTS.csv now carries this measured VRAM and wall time. The other "
         "five model rows remain NOT_MEASURED for VRAM, and Chronos/TimesFM resource rows "
         "remain BLOCKED. Every row keeps scope=subset_only_not_full_1120; NO full-1120 "
         "Pareto claim is made. Real training wall times from queue logs: MIFlu 581 s, "
         "NLinear 6 s, PatchTST 7 s, DeepSeek-R1-Distill-Qwen-1.5B 24 s.")

T2_ZH = ("6. 基础模型（v8b，T2 — COMPLETED_WITH_DOCUMENTED_SCOPE；早期 BLOCKED 声明已被取代）。"
         "两个来源固定的数值基础模型对照已作为独立 roster 执行，未并入 28-arm 家族。"
         "四个固定权重 tar（共 5,024,901,120 B）在本机 Windows 下载后传至 HPC，并在 sbatch "
         "744607 内核验四个远端 SHA-256 与本地完全一致。隔离环境（Python 3.11.13、torch "
         "2.6.0+cu124、chronos-forecasting 2.3.2、timesfm 1.3.0）由 744574/744576 建立。"
         "Pilot 744589（A100-SXM4-80GB）通过：预测全有限、MSE 0.3913、推理延迟 10.191±0.446 ms"
         "（预热 1 / 重复 5）、峰值显存 596 MiB（28 采样）。Matrix 744607 产出 8/8 有效单元与"
         "真实预测文件，峰值显存 2608 MiB（18 采样）。七通道 z 空间 MSE：Chronos "
         "L24/36/48/60 = 0.3913 / 2.2074 / 1.7135 / 1.4002；TimesFM = 0.7298 / 2.6550 / "
         "2.0311 / 1.6630。要求的 80 格（2×4L×10 seeds）扩展为 NOT_EXECUTED_BY_PROTOCOL："
         "冻结零样本模型没有训练 seed 维度，10 个种子只会产生相同预测，故执行最小忠实子集 8 格。"
         "两个检查点均为单变量，7 个通道以 batch 逐通道独立预测；此 adapter 丢弃跨通道依赖、"
         "与多变量臂并非信息集对等，且各模型有自身内部归一化。未做任何训练或微调。"
         "FOUNDATION_CELLS.csv 中 TimesFM 的各 L 计时是单次共享 forecast 调用的切片计时，"
         "不是四次独立前向延迟。")

T4_ZH = ("7. CDC vintage 与实时声明（v8b，T4 — COMPLETED，已纠正；早期 PARTIAL/BLOCKED "
         "声明已被取代）。项目本来就有完整的冻结 CDC ILINet vintage 重建，位于 "
         "02_数字表格/：cdc_vintage.csv（848 epiweeks）、cdc_vintage_raw.csv（7192 行）、"
         "cdc_vintage_report.md，由 05_程序代码/cdc_vintage_build.py 从 Delphi Epidata "
         "fluview 端点生成。报告以 as-of 首印值对比最终值重评季节峰值：18 季中 7 季峰值周移动"
         "（38.9%）。归档最终 CSV 不是 vintage（只有 8 个年度批量快照日期）。Delphi 的 "
         "release_date/issue 是可复现代理，不是 CDC 官方修订号；2002 年各周无实时 vintage。"
         "模型面板峰值指标仍为回顾性。")

T6_ZH = ("8. 资源实测（v8b，T6 — PARTIAL (IMPROVED)；早期『显存全部 NOT_MEASURED』声明已被取代）。"
         "作业 744532 在 gpu-a100-05（A100-SXM4-80GB，驱动 580.167.08）以既有检查点跑了真实 "
         "MIFlu 前向：峰值显存 4816 MiB（63 次 nvidia-smi 采样）、前向墙钟 62.94 s、"
         "test MSE_7var_z=1.624383、[PASS]。RESOURCE_MEASUREMENTS.csv 的 MIFlu 行已填入实测值；"
         "其余 5 个模型行显存仍 NOT_MEASURED，Chronos/TimesFM 资源行仍 BLOCKED。"
         "每行 scope=subset_only_not_full_1120，不声称 full-1120 Pareto。")

EXTRA = {
    "ieee_manuscript_en_v8.docx": ("V8B FINAL-RESULTS UPDATE (2026-11-06 UTC)", [
        ("SUPERSEDED: the earlier statement that T2 foundation models were BLOCKED / "
         "no weights / no pilot / no cells. CORRECTED: T2 is "
         "COMPLETED_WITH_DOCUMENTED_SCOPE with 8 valid zero-shot cells (2 models x 4 L), "
         "pilot 744589 and matrix 744607, all remote weight hashes verified.", "en"),
        ("SUPERSEDED: the earlier statement that all peak_vram_mib were NOT_MEASURED. "
         "CORRECTED: MIFlu peak VRAM = 4816 MiB (63 samples), forward 62.94 s, job 744532; "
         "other five rows remain NOT_MEASURED.", "en"),
        ("SUPERSEDED: the earlier statement that T4 CDC vintage was PARTIAL / BLOCKED. "
         "CORRECTED: the project's frozen 02_数字表格/cdc_vintage*.csv is a complete "
         "vintage with as-of re-scored season peaks (18 seasons, 7 peak weeks move).", "en"),
        ("The 80-cell (2 models x 4 horizons x 10 seeds) expansion remains "
         "NOT_EXECUTED_BY_PROTOCOL: frozen zero-shot models have no training seed dimension. "
         "The smallest faithful subset (8 cells) was executed on a SEPARATE ROSTER.", "en"),
        ("This manuscript is NOT submission-ready. A structural validator PASS means "
         "scientific_readiness: NOT_ASSESSED.", "en"),
    ]),
    "report_internal_zh_v8.docx": ("V8B 最终结果更新（2026-11-06 UTC）", [
        ("已取代：早期『基础模型 BLOCKED / 无权重 / 无 pilot / 无单元』。更正：T2 为 "
         "COMPLETED_WITH_DOCUMENTED_SCOPE，8 个有效零样本单元（2 模型 × 4 L），pilot 744589、"
         "matrix 744607，四个权重哈希已核验。", "zh"),
        ("已取代：早期『全部 peak VRAM NOT_MEASURED』。更正：MIFlu 峰值显存 4816 MiB"
         "（63 采样）、前向 62.94 s，作业 744532；其余 5 行仍 NOT_MEASURED。", "zh"),
        ("已取代：早期『T4 PARTIAL/BLOCKED』。更正：项目冻结的 "
         "02_数字表格/cdc_vintage*.csv 已是完整 vintage，含 as-of 峰值重评分"
         "（18 季、7 季峰值周移动）。", "zh"),
        ("80 格（2×4L×10 seeds）扩展仍为 NOT_EXECUTED_BY_PROTOCOL：冻结零样本模型无训练 "
         "seed 维度；已执行最小忠实子集 8 格，使用独立 roster，未并入 28-arm。", "zh"),
        ("稿件仍非 submission-ready；结构验证 PASS 等于 scientific_readiness: NOT_ASSESSED。", "zh"),
    ]),
    "report_internal_qa_zh_v8.docx": ("V8B 最終結果更新（2026-11-06 UTC）— 取代索引", [
        ("已取代：Q&A 索引第 6 条『资源表 PARTIAL、无 peak VRAM』。更正：744532 实测 "
         "MIFlu 峰值显存 4816 MiB（63 采样）、前向 62.94 s；其余 5 行仍 NOT_MEASURED。", "zh"),
        ("已取代：第 8 条『CDC vintage PARTIAL/BLOCKED』。更正：项目冻结 "
         "02_数字表格/cdc_vintage*.csv（848 epiweeks / 7192 行 / 18 季 as-of 峰值重评分）"
         "已是完整 vintage，T4 为 COMPLETED。", "zh"),
        ("已取代：『基础模型题答 BLOCKED（无权重/环境/pilot）』与第二节所有把 T2 写为 "
         "BLOCKED 的段落。更正：T2 = COMPLETED_WITH_DOCUMENTED_SCOPE；4 个 tar "
         "5,024,901,120 B 已上传且远端 SHA 全数一致；env 744574/744576；pilot 744589 通过；"
         "matrix 744607 产出 8/8 有效单元（Chronos MSE 0.3913/2.2074/1.7135/1.4002；"
         "TimesFM 0.7298/2.6550/2.0311/1.6630），峰值显存 596 / 2608 MiB。", "zh"),
        ("仍然 BLOCKED / NOT_EXECUTED：80 格 10-seed 扩展（NOT_EXECUTED_BY_PROTOCOL，"
         "冻结零样本无训练 seed 维度）；T5 官方模板 class 文件（UNVERIFIED）；"
         "T6 其余 5 个模型的 peak VRAM 与真实前向延迟；T3 两个隔离 NPZ 的重建；"
         "确认性（依赖感知）统计。", "zh"),
        ("适配器限制：两个检查点均为单变量，7 通道按 batch 逐通道独立预测，丢弃跨通道依赖、"
         "与多变量臂信息集不对等；标签 foundation_chronos / foundation_timesfm 为独立 "
         "roster，未并入 28-arm。TimesFM 各 L 计时为单次共享 forecast 的切片计时，"
         "非四次独立前向；唯一预热重复延迟为 pilot 的 10.191±0.446 ms。", "zh"),
        ("本附录不删除、不改写原 Q01–Q25 题目与原有答案；上述条目明确标注旧声明已被取代。"
         "稿件仍非 submission-ready。", "zh"),
    ]),
}

REPL_EN = [
    ("6. Numerical foundation models (v8, T2", T2_EN),
    ("No numerical foundation model (Chronos/TimesFM) was run", T2_EN),
    ("7. CDC vintage and real-time claims (v8, T4", T4_EN),
    ("v8/cdc_vintage/cdc_vintage.csv contains 20 genuinely-fetched", T4_EN),
    ("v8/RESOURCE_MEASUREMENTS.csv reports a measured SUBSET only", T6_EN),
]
REPL_ZH = [
    ("6. 基础模型（T2", T2_ZH),
    ("Chronos/TimesFM 数值基础模型未运行", T2_ZH),
    ("7. CDC vintage 与实时声明（T4", T4_ZH),
    ("v8/cdc_vintage/cdc_vintage.csv 含 20 行", T4_ZH),
    ("v8/RESOURCE_MEASUREMENTS.csv 仅为子集", T6_ZH),
]
REPL_QA = [
    ("6. 旧「资源/效率表 NOT EXECUTED」", None),   # handled by append-only index; keep original
]


def set_paragraph(p, text):
    """Replace paragraph text preserving the first run's formatting."""
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(cmd, timeout=480):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def main():
    results = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "documents": {}, "commands": []}
    for name, (heading, bullets) in EXTRA.items():
        path = OUT / name
        d = Document(path)
        repl = REPL_ZH if name == "report_internal_zh_v8.docx" else (
            [] if name == "report_internal_qa_zh_v8.docx" else REPL_EN)
        changed = 0
        for p in d.paragraphs:
            for key, new in repl:
                if key in p.text:
                    set_paragraph(p, new)
                    changed += 1
                    break
        # Q&A: mark the stale index paragraphs as superseded in place
        if name == "report_internal_qa_zh_v8.docx":
            for p in d.paragraphs:
                t = p.text
                if ("新增题类（V8）：基础模型题答 BLOCKED" in t
                        or "T2 基础模型（无完整权重" in t
                        or "旧「资源/效率表 NOT EXECUTED」" in t
                        or "旧「CDC vintage 未重建" in t):
                    set_paragraph(p, "[已被 V8B 更新取代 — 见文末 V8B 最終結果更新] " + t)
                    changed += 1
        d.add_page_break()
        d.add_heading(heading, level=1)
        for text, _lang in bullets:
            par = d.add_paragraph(text)
            for r in par.runs:
                r.font.size = Pt(9)
        d.save(path)
        print(f"[docx] {name} paragraphs_replaced={changed} sha256={sha(path)}")

        pdf = OUT / (name[:-5] + ".pdf")
        # The converter refuses to overwrite. These PDFs are OUR OWN v8 outputs
        # (not frozen CSVs, not owner-edited files), so replacing them is intended.
        if pdf.exists():
            pdf.unlink()
        cmd = [NODE, CLI, "convert", "--input", path, "--output", pdf]
        rc, so, se = run(cmd)
        results["commands"].append({"cmd": " ".join(str(x) for x in cmd), "rc": rc,
                                    "stdout": so.strip()[:400], "stderr": se.strip()[:400]})
        print(f"[pdf] {pdf.name} convert_rc={rc} stdout={so.strip()[:160]}")
        if rc != 0:
            print("FATAL convert failed", se[:500])
            sys.exit(2)
        pages = None
        tmp = OUT / ("_pages_" + name[:-5])
        cmd2 = [NODE, CLI, "render", "--input", pdf, "--output-dir", tmp,
                "--pages", "1", "--dpi", "36"]
        rc2, so2, se2 = run(cmd2)
        results["commands"].append({"cmd": " ".join(str(x) for x in cmd2), "rc": rc2,
                                    "stdout": so2.strip()[:400], "stderr": se2.strip()[:400]})
        try:
            pages = json.loads(so2).get("pageCount")
        except Exception:
            import re
            m = re.search(r'"pageCount"\s*:\s*(\d+)', so2)
            pages = int(m.group(1)) if m else None
        print(f"[pages] {pdf.name} rc={rc2} pageCount={pages}")
        results["documents"][name] = {
            "docx_sha256": sha(path), "docx_bytes": path.stat().st_size,
            "pdf_sha256": sha(pdf), "pdf_bytes": pdf.stat().st_size,
            "convert_rc": rc, "page_count": pages,
            "paragraphs_replaced": changed,
        }
    (DOCS / "V8B_BUILD_RESULTS.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("V8B_BUILD_RESULTS_WRITTEN")
    return results


if __name__ == "__main__":
    main()
