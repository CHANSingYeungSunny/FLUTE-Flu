# ROADMAP — 下一步路线图

> Goal: innovate on top of MIFlu and reach top-tier-journal quality. 三个阶段，
> 每阶段有明确的完成标准。**Constraints from `START_HERE.md` apply at every phase.**

## Phase A — Optimize the current benchmark（先优化现有基准）

Target: make the existing 8-model, strict-966 benchmark *cleaner, stronger, and more
defensible* before adding anything new.

1. **Reproducibility hardening**
   - One unified runner (train → predict → canonical score) used by all 8 models;
     per-model code paths documented; single command reproduces the championship table.
   - Pin and document every hyperparameter (mirror paper Table IV where applicable);
     record repo-default vs paper-setting differences explicitly.
   - Re-run with more seeds (e.g. 5–10) to tighten SDs and enable significance tests
     (paired tests on matched seed–horizon cells).
2. **Resolve or formally bound the text-path contradiction**
   - Design one decisive experiment (same code path, same device, gradient probe +
     ablation on identical seeds) that can settle "does the text path change predictions?".
   - If it cannot be settled, document the boundary conditions under which each behavior
     appears (keep the honest "unresolved" verdict until then).
3. **Statistical & reporting upgrades**
   - Confidence intervals; per-horizon and per-seed breakdowns; effect sizes;
     error bars on all figures.
   - Peak analysis: report per-season peak hits, and the COVID-period sensitivity.
4. **Code quality**
   - Type hints + docstrings on the core pipeline; a small test suite for the scorer and
     the strict-containment/split logic; `requirements.txt` with pinned versions.

**Done when**: a fresh reader can reproduce the championship table with one command, the
uncertainty is quantified, and the text-path question is either settled or rigorously bounded.

## Phase B — Extend the model set（再扩展模型）

1. Add models **under the same frozen contract** (same data, split, seeds, horizons,
   canonical scorer) — comparability is non-negotiable.
   Candidates worth adding: modern long-term TSF baselines (e.g. iTransformer variants,
   TimesNet, PatchTST variants, TiDE, ModernTCN), stronger LLM-based ones (e.g. GPT4TS
   reimplemented exactly, Time-LLM, GPT4TS+prompt variants), and simple seasonal baselines
   (SARIMA/Prophet) as sanity anchors.
2. Include the **notext** ablation for every LLM-side model (text contribution must remain
   an explicit, measured column — reported neutrally per constraint #2).
3. Regional task (US-Region) if the author artifact becomes available.

**Done when**: ≥4 new models scored under the identical contract with the same reporting
template, and group-level conclusions are re-evaluated.

## Phase C — Innovate（创新，面向顶刊）

1. **Prompt-as-knowledge study**: systematically vary what expert knowledge goes into the
   prompt (statistics only vs trend/peak descriptors vs external events), measuring the
   effect under the settled Phase-A protocol.
2. **Fusion architecture alternatives**: cross-attention between text and time tokens,
   gated fusion, per-variable prompts; ablate each component.
3. **Reliability & clinical framing**: calibration, prediction intervals, peak-warning
   utility (decision-relevant metrics beyond MSE), COVID-regime robustness.
4. **Publication packaging**: reproducible repo, pre-registration-style frozen contracts,
   figure style guide (`docs/FIGURE_STYLE_GUIDE.md`), bilingual README, artifact DOI plan.

**Done when**: one clear novel contribution with rigorous baselines + ablations + honest
limitations, written up at submission quality.

## Non-negotiables for every phase / 每阶段不可违反

1. A-track vs B-track numbers never compared; always state track + seeds + space.
2. Text-path effectiveness stays "unresolved" until one decisive experiment settles it.
3. Peak metrics: literature criterion only (PTE≤1wk & PIE≤25%).
4. Paper comparison: the unified pair 1.4355 ↔ 1.8652 only.
5. One authoritative report at a time (`CURRENT_OFFICIAL_REPORT.txt` is the pointer).
6. Official data = author 966 rows (sha 2a96dfed…); never mix vintages.
7. MSE and peak accuracy reported separately.
