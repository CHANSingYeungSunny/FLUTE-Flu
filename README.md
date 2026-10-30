# MIFlu Reproduction & Benchmark — MLFlu

Reproduction of **MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme**
(Moon et al., **IEEE JBHI 2025**, DOI 10.1109/JBHI.2025.3561214) on the author's 966-row US
National-Illness dataset, plus a strict **8-model benchmark** (4 non-LLM vs 4 LLM-side),
paper-reproduction study, and peak-accuracy audit. Goal: innovate on top of MIFlu
(final-year project → top-tier journal).

> **New here? Read [`START_HERE.md`](START_HERE.md) first** — 10-minute zero-foundation entry
> (bilingual), including the seven hard constraints for citing any number in this project.

## Current authoritative result / 当前权威结果

**One source of truth**: `reports/concise_final/MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx`
(SHA-256 and authority label in [`CURRENT_OFFICIAL_REPORT.txt`](CURRENT_OFFICIAL_REPORT.txt)).

| Headline | Value |
|----------|-------|
| Paper target (avg MSE, Table V) | 1.4355 |
| Our MIFlu final Test `average_MSE_4L` | **1.8652** (SD 0.0916) |
| Reproduction verdict | **PARTIAL_REPRODUCTION** (+29.9%, 5% band not met) |
| 8-model champion | **MIFlu 1.8652** (best non-LLM = MIFlu; best LLM-side = TimeCMA-LLM 2.6700) |
| Group means | non-LLM 3.0756 < LLM-side 3.8175 |
| Peak accuracy (literature PTE≤1wk & PIE≤25%) | NLinear 36/36 (peak champion) vs MIFlu 15/36 |

**MSE is not accuracy** — the MSE champion and the peak champion are different models;
they are reported separately.

## Protocol / 实验协议

Author 966 rows · Train/Val/Test = 676/97/193 (70:10:20) · strict containment · Train-only
scaler · z-space canonical scorer · seeds 42/43/44 · horizons L = 24/36/48/60 · Test scored
once after checkpoint selection · peak metrics per peak under the literature criterion.

## Repository layout / 目录导航

| Path | What |
|------|------|
| [`START_HERE.md`](START_HERE.md) | zero-foundation entry point |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | current results, verdicts, open issues |
| [`docs/01_paper/`](docs/01_paper/) | paper explained + author repo explained |
| [`docs/GLOSSARY.md`](docs/GLOSSARY.md) · [`docs/DIRECTORY_MAP.md`](docs/DIRECTORY_MAP.md) · [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) | terminology · where things are · where numbers come from |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phase A optimize benchmark → B add models → C innovate |
| `reports/concise_final/` | ★ authoritative report + manifest |
| `results/v3_clean/analysis/peak_criteria/` | ★ benchmark results + PTE/PIE peak audit |
| `hpc_results/official_repo_reproduction_20261006/` | paper-reproduction evidence (R1-C) |
| `audit_20260930/` | independent audit |
| `data/` | datasets (author 966-row copy + 1025-row snapshot) |
| `recovery/author_repo/` | the author's GitHub repo clone (`github.com/Jmoon3108/MIFlu`) |
| `scripts/`, `tests/` | runnable code |
| `handoff/` | bilingual handoff package for an AI collaborator (zip) |
| `archive/`, `docs/paper_and_analysis/`, `docs/planning/` | historical prompts, drafts & analyses |

## Honest limitations / 诚实披露

1. Reproduction gap of +29.9% remains; optimizer/scheduler/seeds not fully disclosed by the
   paper/repo (repo defaults differ from paper Table IV).
2. The text-path mechanism question is **unresolved** (GPU vs CPU replay contradict; ablations
   disagree) — reported as such, never as "works" or "does nothing".
3. 3 seeds only; 4 horizons are correlated; LLM-side baselines (TimeCMA/Qwen/CALF) are informed
   simplifications; regional (US-Region) part not reproduced (author artifact unavailable).
4. Older 1025-row-era results are superseded and must not be compared with the 966-row track
   (different data vintage, seed count, and metric convention).

Details and evidence pointers: [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md).
