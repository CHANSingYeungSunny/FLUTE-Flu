from pathlib import Path
import shutil

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "01_最终报告"
V8_REPORTS = REPORTS / "v8"
PRESENTATION = ROOT / "presentation"


def append_section(source: Path, destination: Path, heading: str, paragraphs: list[str]) -> None:
    document = Document(source)
    document.add_heading(heading, level=1)
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    document.save(destination)


def main() -> None:
    V8_REPORTS.mkdir(parents=True, exist_ok=True)
    append_section(
        REPORTS / "progress_report_en.docx",
        V8_REPORTS / "progress_report_en_v8.docx",
        "V8 evidence update (2026-11-07)",
        [
            "The verified national common panel is complete: 1,120/1,120 cells across 28 arms, four horizons, and ten seeds (2021-2030). All-valid MSE means are MIFlu 1.7944, PatchTST 1.9521, and NLinear 2.0782; the crop panel is 1.4994, 1.6352, and 1.9027 respectively.",
            "The legacy five-fold walk-forward panel is a separate population and is complete at 1,020/1,020 valid cells (seeds 42/43/44), with MIFlu 2.2203, PatchTST 3.0396, and NLinear 3.2116. It must not be pooled with the national panel.",
            "Foundation models are a separate zero-shot roster: Chronos and TimesFM have 80/80 valid rolling-origin cells (ten origins, not training seeds). Their univariate per-channel adapter discards cross-channel dependence, so they are not part of the 28-arm or 1,120-cell comparison.",
            "The ablation is non-monotonic (K4 1.4989 best; K12 1.7604 worst). Resource evidence covers six representative models, not a full-1,120-cell Pareto analysis. CDC vintage analysis is a retrospective final-vintage reconstruction, not real-time validation.",
            "Risks and remaining verification items: the literal foundation 10-seed expansion is not executed by protocol; the information-set-matched multivariate foundation control, dependence-aware confirmatory inference, isolated MIFlu/NLinear/PatchTST forward latency, full-panel resource Pareto, and exact JBHI template class remain blocked or unverified. Validator PASS is structural only (scientific_readiness: NOT_ASSESSED).",
        ],
    )
    append_section(
        PRESENTATION / "Presentation_Notes_EN.docx",
        PRESENTATION / "Presentation_Notes_EN_v8.docx",
        "Proposed V8 update (notes only; owner PPTX unchanged)",
        [
            "Replace the headline result with the new common national panel: MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782 (all-valid). Keep the revision-9.2 table explicitly labelled as the old frozen snapshot.",
            "For peak skill, state the new step-level counts—MIFlu 252/1680, PatchTST 215/1680, NLinear 57/1680—and do not call NLinear the current champion.",
            "Mention the legacy walk-forward result only with its separate five-fold, three-seed provenance. Describe Chronos/TimesFM as a separate zero-shot rolling-origin roster, not as 28-arm or ten-seed evidence.",
            "State that ablation depth is non-monotonic, CDC vintage results are retrospective, resources are representative-subset measurements, and the exact JBHI template class remains unverified. Do not claim submission readiness or scientific certification.",
            "Validator PASS is structural only (scientific_readiness: NOT_ASSESSED).",
        ],
    )


if __name__ == "__main__":
    main()
