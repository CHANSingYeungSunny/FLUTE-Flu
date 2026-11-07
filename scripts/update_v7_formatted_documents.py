from pathlib import Path
import shutil

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
REPORT = next(p for p in ROOT.iterdir() if p.name.startswith("01_"))
V7 = REPORT / "v7"
OUT = REPORT / "v7"


UPDATES = {
    "manuscript": (
        "V8 evidence correction — supersedes earlier result claims",
        [
            "This v7-formatted manuscript retains the earlier draft for provenance. The following v8 body update is authoritative wherever it conflicts with the earlier text. The frozen revision-9.2 values remain an OLD snapshot and are not overwritten.",
            "The new national common panel is complete: 1,120/1,120 cells (28 arms, L=24/36/48/60, ten seeds 2021–2030). All-valid MSE means are MIFlu 1.7944, PatchTST 1.9521, and NLinear 2.0782. The historical crop means are 1.4994, 1.6352, and 1.9027. These are new common-panel results, not replacements for frozen CSVs.",
            "Peak step passes on the new panel are MIFlu 252/1680 (15.0%), PatchTST 215/1680 (12.8%), and NLinear 57/1680 (3.4%). The historical statement that NLinear is the current peak champion is therefore superseded; it remains only as an old-snapshot claim.",
            "The legacy walk-forward panel is complete at 1,020/1,020 valid cells, using five folds and seeds 42/43/44. Its means are MIFlu 2.2203, PatchTST 3.0396, and NLinear 3.2116. It is a different scoring population from the national 1,120-cell panel and must not be pooled with it.",
            "The ablation is non-monotonic: K4 1.4989 is best, K6 1.5457, K2 1.5813, K8 1.6124, no_lora 1.6330, and K12 1.7604 worst. No monotonic depth claim is supported.",
            "Chronos and TimesFM comprise a separate zero-shot foundation roster with 80/80 valid rolling-origin cells. The ten replicates are distinct origins, not training seeds; the literal ten-seed expansion is not executed by protocol. The univariate per-channel adapter discards cross-channel dependence, so these results are not part of the 28-arm or national panel.",
            "CDC vintage evidence is a retrospective final-vintage reconstruction, not real-time validation. Resource evidence covers six representative models and does not establish a full-panel Pareto result. Validator PASS is structural only (scientific_readiness: NOT_ASSESSED).",
            "Remaining blocked or unverified items are the information-set-matched multivariate foundation control, literal foundation ten-seed expansion, isolated MIFlu/NLinear/PatchTST forward latency, dependence-aware confirmatory inference, full-panel resource Pareto, and exact JBHI template class. This work is not submission-ready or acceptance-certified.",
        ],
    ),
    "internal": (
        "V8 科学证据更新——以下内容覆盖旧结果表述",
        [
            "本文件保留 v7 排版及原文，作为审计 provenance。凡与以下 v8 更新冲突的旧数字或结论均标记为旧快照，不得继续作为当前结果引用。",
            "新的全国共同协议面板已完成 1120/1120 格：28 个模型、L=24/36/48/60、种子 2021–2030。all-valid MSE 均值为 MIFlu 1.7944、PatchTST 1.9521、NLinear 2.0782；crop 面板为 1.4994、1.6352、1.9027。",
            "新面板逐步 peak pass 为 MIFlu 252/1680（15.0%）、PatchTST 215/1680（12.8%）、NLinear 57/1680（3.4%）。因此“当前 NLinear 为 peak 冠军”的旧结论已被覆盖，只能保留为旧快照说明。",
            "独立的 legacy 五折 walk-forward 面板已完成 1020/1020 格，使用 seeds 42/43/44；均值为 MIFlu 2.2203、PatchTST 3.0396、NLinear 3.2116。该面板与 1120 格全国面板不是同一 scoring population，不能合并或直接比较。",
            "消融深度呈非单调：K4=1.4989 最佳，K6=1.5457，K2=1.5813，K8=1.6124，no_lora=1.6330，K12=1.7604 最差。不得声称深度单调改善。",
            "Chronos/TimesFM 是独立的 zero-shot foundation roster，共 80/80 个 rolling-origin 格；十次重复是不同 forecast origins，不是训练 seeds。其逐频道 univariate adapter 丢失跨频道依赖，因此不属于 28-arm 或 1120 格全国面板。",
            "CDC vintage 是 retrospective final-vintage reconstruction，不是 real-time validation；资源结果只覆盖六个代表模型，不构成全面 Pareto。Validator PASS 仅为结构检查，scientific_readiness=NOT_ASSESSED。",
            "仍 BLOCKED/UNVERIFIED：信息集匹配的多变量 foundation 对照、literal 10-seed foundation expansion、MIFlu/NLinear/PatchTST 独立 forward latency、依赖感知 confirmatory inference、全面资源 Pareto、以及 JBHI exact template class。本项目不声称 submission-ready 或 acceptance。",
        ],
    ),
    "progress": (
        "V8 证据更新（2026-11-07）",
        [
            "本中文进度报告保留 v7 版式与历史叙述；以下 v8 更新覆盖冲突的旧数字。全国共同协议面板为 1120/1120，all-valid MSE 排序为 MIFlu 1.7944、PatchTST 1.9521、NLinear 2.0782，crop 排序为 1.4994、1.6352、1.9027。",
            "Legacy 五折 walk-forward 面板为 1020/1020，有独立的 seeds 42/43/44，不能与全国面板合并。Foundation 模型为独立 zero-shot rolling-origin roster（80/80），不是 28-arm 或十 seed 证据。",
            "消融不呈单调深度趋势（K4 最佳 1.4989，K12 最差 1.7604）；CDC vintage 是 retrospective；资源结果是六模型代表子集。Validator PASS 仅为结构检查，scientific_readiness=NOT_ASSESSED。",
            "未解决事项包括 literal foundation 10-seed expansion、多变量信息集匹配、依赖感知统计、三模型 isolated forward latency、全 panel 资源 Pareto 与 JBHI exact template class。会议及每周小时等空白栏保持空白。",
        ],
    ),
}


def insert_notice(document: Document, title: str) -> None:
    body = document._element.body
    first = body[0]
    paragraph = document.add_paragraph()
    paragraph.style = "Title"
    paragraph.add_run("V8 UPDATE — READ BEFORE USING THIS DOCUMENT")
    body.remove(paragraph._p)
    body.insert(body.index(first), paragraph._p)
    paragraph = document.add_paragraph(
        "This v7-formatted file retains historical material for provenance. "
        "The v8 section at the end is authoritative for current evidence and "
        "explicitly supersedes conflicting old claims."
    )
    body.remove(paragraph._p)
    body.insert(body.index(first) + 1, paragraph._p)


def append_update(source: Path, destination: Path, title: str, paragraphs: list[str]) -> None:
    shutil.copy2(source, destination)
    document = Document(destination)
    insert_notice(document, title)
    document.add_page_break()
    document.add_heading(title, level=1)
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    document.save(destination)


def main() -> None:
    append_update(V7 / "ieee_manuscript_en.docx", V7 / "ieee_manuscript_en_v8_formatted.docx", *UPDATES["manuscript"])
    append_update(V7 / "report_internal_zh.docx", V7 / "report_internal_zh_v8_formatted.docx", *UPDATES["internal"])
    append_update(V7 / "progress_report_zh.docx", V7 / "progress_report_zh_v8_formatted.docx", *UPDATES["progress"])


if __name__ == "__main__":
    main()
