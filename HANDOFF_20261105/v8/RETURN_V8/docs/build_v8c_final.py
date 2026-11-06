# -*- coding: utf-8 -*-
"""v8c rebuild: put the FINAL T2/T3/T5/T6 results in the DOCX bodies, then
convert to PDF and verify page counts. Old claims are marked SUPERSEDED."""
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

EN_T2 = ("6. Numerical foundation models (v8c, T2 — COMPLETED: 80/80 valid cells; "
         "the v8b 8-cell and earlier BLOCKED statements are SUPERSEDED). Job 744886 "
         "produced FOUNDATION_80_CELLS.csv with 80/80 `ok`, all finite predictions and "
         "80 real NPZ (2 models x 4 horizons L=24/36/48/60 x 10 replicates). Both "
         "checkpoints are FROZEN ZERO-SHOT with no training seed dimension, so the 10 "
         "replicates are 10 DISTINCT FORECAST ORIGINS (rows 773-782), each with its own "
         "context and target; `seed_semantics=NOT_APPLICABLE`, "
         "`replicate_kind=rolling_origin`. The literal 10-seed expansion remains "
         "NOT_EXECUTED_BY_PROTOCOL. Four pinned weight tars (5,024,901,120 B) were "
         "downloaded locally on Windows, transferred to HPC, and all remote SHA-256 "
         "values verified inside job 744607. Isolated env jobs 744574/744576; pilot "
         "744589 passed. Measured resources: peak VRAM 2608 MiB (51 samples), wall "
         "50.71 s, Chronos 10.229 +/- 1.074 ms and TimesFM 50.906 +/- 4.459 ms "
         "(warm-up 1 / repeated). Both checkpoints are UNIVARIATE: the 7 channels were "
         "forecast as a batch of 7 independent series (per-channel adapter), which "
         "DISCARDS cross-channel dependence and is NOT information-set matched to the "
         "multivariate arms. Each model applies its own internal scaling; zero-shot, no "
         "training. Labels `foundation_chronos` / `foundation_timesfm` are a SEPARATE "
         "ROSTER, never merged into the 28-arm family. No full-1120 comparison.")

EN_T6 = ("8. Resource measurements (v8c, T6 — COMPLETED for all 6 representative "
         "models; the v8b PARTIAL statement is SUPERSEDED). Jobs 744897 "
         "(`t6_final_sweep`) and 744899 (`t6_miflu_fix`) on an A100-SXM4-80GB measured "
         "peak VRAM: MIFlu 4816 MiB (46+63 samples), NLinear 558 (36), PatchTST 720 (7), "
         "GPT-2 frozen encoder 1070 (11), Chronos 596 (6), TimesFM 2594 (11). "
         "Warm-up + repeated REAL model-forward latencies: GPT-2 6.98 +/- 0.097 ms "
         "(1/10), Chronos 9.854 +/- 0.337 ms (1/20), TimesFM 48.273 +/- 3.531 ms (1/10). "
         "Real full-job walls: MIFlu 7-channel cell export 62.94 s, NLinear 20-epoch "
         "training+export 35.73 s, PatchTST 6.86 s. Isolated single-forward latency for "
         "MIFlu/NLinear/PatchTST is explicitly NOT_MEASURED; the old NPZ scoring-path "
         "numbers (0.0287-0.0297 ms) are retained in dedicated CSV columns labelled "
         "NOT a model forward. All rows `scope=subset_only_not_full_1120`; NO full-1120 "
         "Pareto claim. Cross-checked by jobs 744532 and 744886.")

EN_T3 = ("T3 legacy `final_llm_import` (v8c — SUPERSEDED the 386-cell caveat). "
         "Job 744884 COPY-restored the two corrupt NPZ from their existing valid "
         "7-channel copies and validated 388/388 NPZ as readable, correctly shaped "
         "(W,7,L) and finite; the exact final_llm_import task then ran with all three "
         "scripts rc=0. BENCH_MSE_BY_MODEL_L.csv is now "
         "sha256 a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46 "
         "(69 lines). The original corrupt files remain archived, not deleted. "
         "This is a LEGACY analysis-tree table, a different scoring population from "
         "the 1120 national panel and the LEGACY 5-fold WF panel.")

EN_T5 = ("T5 JBHI provenance (v8c — step 4 now APPLIED). The dated JBHI guidance "
         "verification has been written into `v8/PAPER_TO_CODE.md`, and the v8 package "
         "builder now prefers that copy over the frozen v7 skeleton; the v7 original "
         "remains byte-identical. The official template class file itself stays "
         "UNVERIFIED (selector 404 / WAF 418 / API 302->502). The manuscript is NOT "
         "submission-ready.")

ZH_T2 = ("6. 基础模型（v8c，T2 — COMPLETED：80/80 有效单元；v8b 的 8 格与早期 BLOCKED 声明已被取代）。"
         "作业 744886 产出 FOUNDATION_80_CELLS.csv：**80/80 ok、全有限、80 个真实 NPZ**"
         "（2 模型 × 4 个 L=24/36/48/60 × 10 次重复）。两个检查点皆为冻结零样本模型，"
         "无训练 seed 维度，因此 10 次重复改用 **10 个不同预测起点**（行 773–782），"
         "各有自己的 context 与 target；`seed_semantics=NOT_APPLICABLE`、"
         "`replicate_kind=rolling_origin`。字面的 10-seed 扩展仍为 NOT_EXECUTED_BY_PROTOCOL。"
         "四个固定权重 tar（5,024,901,120 B）在本机下载后传至 HPC，744607 内核验远端 SHA 全数一致；"
         "隔离环境 744574/744576、pilot 744589 通过。实测：峰值显存 2608 MiB（51 采样）、"
         "wall 50.71 s、Chronos 10.229±1.074 ms、TimesFM 50.906±4.459 ms（预热+重复）。"
         "两检查点均为单变量，7 通道以 batch 逐通道独立预测，丢弃跨通道依赖、与多变量臂"
         "信息集不对等；各模型有自身内部归一化；零样本无训练。标签 "
         "foundation_chronos / foundation_timesfm 为独立 roster，未并入 28-arm；"
         "无 full-1120 对比。")

ZH_T6 = ("8. 资源实测（v8c，T6 — 6 个代表性模型全部完成；v8b 的 PARTIAL 声明已被取代）。"
         "作业 744897（t6_final_sweep）与 744899（t6_miflu_fix）在 A100-SXM4-80GB 实测"
         "峰值显存：MIFlu 4816 MiB（46+63 采样）、NLinear 558（36）、PatchTST 720（7）、"
         "GPT-2 冻结编码器 1070（11）、Chronos 596（6）、TimesFM 2594（11）。"
         "预热+重复的真实模型前向延迟：GPT-2 6.98±0.097 ms（1/10）、"
         "Chronos 9.854±0.337 ms（1/20）、TimesFM 48.273±3.531 ms（1/10）。"
         "真实完整作业墙钟：MIFlu 七通道 cell 汇出 62.94 s、NLinear 20 epoch 训练+汇出 "
         "35.73 s、PatchTST 6.86 s。MIFlu/NLinear/PatchTST 的隔离单次前向延迟明确为 "
         "NOT_MEASURED；旧的 NPZ 评分路径数值（0.0287–0.0297 ms）已移至专用栏并标明不是模型前向。"
         "每行 scope=subset_only_not_full_1120，不声称 full-1120 Pareto。")

ZH_T3 = ("T3 legacy final_llm_import（v8c — 386 格限制已解除）。作业 744884 以 COPY "
         "从既有有效七通道成品还原 2 个损坏 NPZ，并在 sbatch 内验证 388/388 可读、"
         "形状 (W,7,L)、全有限；随后精确重跑 final_llm_import，三步全 rc=0。"
         "BENCH_MSE_BY_MODEL_L.csv 现为 sha256 "
         "a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46（69 行）。"
         "原损坏档仍归档保留、未删除。此表属 LEGACY analysis tree，与 1120 全国面板及 "
         "LEGACY 五折 WF 面板为不同总体。")

ZH_T5 = ("T5 JBHI provenance（v8c — 第 4 步已套用）。带日期的 JBHI 指引核验已写入 "
         "`v8/PAPER_TO_CODE.md`，打包器优先采用此 v8 版本；v7 原件保持逐字节不变。"
         "官方模板 class 档仍 UNVERIFIED（404 / WAF 418 / API 302→502）。稿件非 submission-ready。")

QA_T2 = ("已取代（V8C）：v8b 的「8 格最小忠实子集 / 80 格 NOT_EXECUTED」与早期 "
         "「基础模型题答 BLOCKED」。更正：T2 **COMPLETED，80/80 有效单元**，作业 744886；"
         "2 模型 × 4 L × 10 个不同预测起点（行 773–782），各有独立 context/target，"
         "80 个真实 NPZ。`seed_semantics=NOT_APPLICABLE`；字面的 10-seed 扩展仍为 "
         "NOT_EXECUTED_BY_PROTOCOL（冻结零样本无训练 seed 维度）。峰值显存 2608 MiB、"
         "Chronos 10.229±1.074 ms、TimesFM 50.906±4.459 ms。独立 roster，未并入 28-arm；"
         "单变量逐通道 adapter 丢弃跨通道依赖、信息集不对等；无训练/微调、无 full-1120 对比。")

QA_T3 = ("已取代（V8C）：「T3 两个隔离 NPZ 未重建 / 386 格」。更正：作业 744884 以 COPY "
         "还原，388/388 NPZ 可读，final_llm_import 三步 rc=0，"
         "BENCH_MSE_BY_MODEL_L.csv → a7d98ad8…e46。")

QA_T6 = ("已取代（V8C）：「T6 其余 5 行显存 NOT_MEASURED / PARTIAL」。更正：744897 与 "
         "744899 实测 6 个模型峰值显存 MIFlu 4816、NLinear 558、PatchTST 720、"
         "GPT-2 1070、Chronos 596、TimesFM 2594 MiB；GPT-2 6.98±0.097、"
         "Chronos 9.854±0.337、TimesFM 48.273±3.531 ms（预热+重复真实前向）。"
         "仍 NOT_MEASURED：MIFlu/NLinear/PatchTST 的隔离单次前向延迟；"
         "scope=subset_only_not_full_1120，无 full-1120 Pareto。")

QA_T5 = ("已取代（V8C）：「JBHI provenance 补丁未套用」。更正：`v8/PAPER_TO_CODE.md` "
         "已套用，打包器优先采用；v7 原件逐字节不变。官方模板 class 档仍 UNVERIFIED。")

QA_REMAIN = ("V8C 最终仍 BLOCKED / NOT_EXECUTED / UNVERIFIED：字面 10-seed 扩展"
             "（NOT_EXECUTED_BY_PROTOCOL）、多变量原生基础模型检查点、full-1120 对比、"
             "官方 JBHI 模板 class 档（UNVERIFIED）、三个模型的隔离单次前向延迟"
             "（NOT_MEASURED）、确认性依赖感知统计、回顾性模型面板峰值。"
             "稿件非 submission-ready；结构验证 PASS = scientific_readiness: NOT_ASSESSED。")

# (filename, heading, bullets, replacements)
CFG = {
    "ieee_manuscript_en_v8.docx": (
        "V8C FINAL UPDATE (2026-11-06 UTC)",
        [EN_T2, EN_T3, EN_T5, EN_T6,
         "This document is NOT submission-ready. A structural validator PASS means "
         "scientific_readiness: NOT_ASSESSED."],
        [("6. Numerical foundation models (v8b", EN_T2),
         ("Named Chronos T5/Bolt and TimesFM 1.0/2.0 checkpoints are UNIVARIATE", EN_T2),
         ("8. Resource measurements (v8b", EN_T6),
         ("Table 6. v8 resource subset (PARTIAL). Latency is the NPZ scoring path", EN_T6),
         ("8. Resource measurements (v8, T6", "[SUPERSEDED by §8 v8c] 8. Resource measurements (v8, T6 — PARTIAL)")]),
    "report_internal_zh_v8.docx": (
        "V8C 最终结果更新（2026-11-06 UTC）",
        [ZH_T2, ZH_T3, ZH_T5, ZH_T6,
         "稿件仍非 submission-ready；结构验证 PASS 等于 scientific_readiness: NOT_ASSESSED。"],
        [("6. 基础模型（v8b", ZH_T2),
         ("8. 资源实测（v8b", ZH_T6),
         ("表 5. V8 资源子集（PARTIAL）", ZH_T6),
         ("8. 资源测量（T6，PARTIAL）", "[已被 V8C 取代] 8. 资源测量（T6，PARTIAL）"),
         ("单一全国序列；四个跨度复用观测", ZH_T6)]),
    "report_internal_qa_zh_v8.docx": (
        "V8C 最終結果更新（2026-11-06 UTC）— 取代索引",
        [QA_T2, QA_T3, QA_T5, QA_T6, QA_REMAIN,
         "本附录不删除、不改写原 Q01–Q25 题目与原有答案；上述条目明确标注旧声明已被取代。"],
        [("已取代：Q&A 索引第 6 条", QA_T6),
         ("已取代：『基础模型题答 BLOCKED", QA_T2)]),
}


def set_paragraph(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd, timeout=480):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def main():
    res = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "documents": {}, "commands": []}
    for name, (heading, bullets, repl) in CFG.items():
        path = OUT / name
        d = Document(path)
        changed = 0
        for p in d.paragraphs:
            for key, new in repl:
                if key in p.text:
                    set_paragraph(p, new)
                    changed += 1
                    break
        d.add_page_break()
        d.add_heading(heading, level=1)
        for text in bullets:
            par = d.add_paragraph(text)
            for r in par.runs:
                r.font.size = Pt(9)
        d.save(path)
        print(f"[docx] {name} replaced={changed} sha256={sha(path)}", flush=True)

        pdf = OUT / (name[:-5] + ".pdf")
        if pdf.exists():
            pdf.unlink()          # converter refuses to overwrite
        cmd = [NODE, CLI, "convert", "--input", path, "--output", pdf]
        rc, so, se = run(cmd)
        res["commands"].append({"cmd": " ".join(str(x) for x in cmd), "rc": rc,
                                "stdout": so.strip()[:300], "stderr": se.strip()[:300]})
        print(f"[pdf] {pdf.name} rc={rc}", flush=True)
        if rc != 0:
            print("FATAL", se[:400]); sys.exit(2)
        pages = None
        tmp = OUT / ("_pages_v8c_" + name[:-5])
        cmd2 = [NODE, CLI, "render", "--input", pdf, "--output-dir", tmp,
                "--pages", "1", "--dpi", "36"]
        rc2, so2, se2 = run(cmd2)
        res["commands"].append({"cmd": " ".join(str(x) for x in cmd2), "rc": rc2})
        import re
        m = re.search(r'"pageCount"\s*:\s*(\d+)', so2)
        pages = int(m.group(1)) if m else None
        print(f"[pages] {pdf.name} rc={rc2} pageCount={pages}", flush=True)
        res["documents"][name] = {"docx_sha256": sha(path), "docx_bytes": path.stat().st_size,
                                  "pdf_sha256": sha(pdf), "pdf_bytes": pdf.stat().st_size,
                                  "convert_rc": rc, "page_count": pages,
                                  "paragraphs_replaced": changed}
    (DOCS / "V8C_BUILD_RESULTS.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("V8C_BUILD_RESULTS_WRITTEN")
    return res


if __name__ == "__main__":
    main()
