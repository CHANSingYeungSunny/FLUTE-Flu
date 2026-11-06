# START HERE — context pack for the MLFlu handoff

This pack is a **curated subset** of the project, sized so an assistant with no prior context can
read all of it. The full repository (with raw predictions, HPC logs and the 165 MB archive) is a
separate file, `PROJECT_HANDOFF.zip`; ask for it only if you need to inspect raw `pred_*.npz`.

## What this project is

An independent reproduction of **MIFlu** (Moon et al., *IEEE JBHI* 2025) on the CDC national
influenza series (966 weekly rows × 7 channels), plus a **28-model benchmark** under one protocol,
scored twice: once on accuracy (MSE) and once on the epidemiological acceptance criterion of
Kramer & Shaman (peak-timing error ≤ 1 week **and** peak-intensity error ≤ 25 %).

The owner is Sunny, an FYP student at CityU EE; supervisor Prof. Katie Chan. The two marked
deliverables this semester are the **FYP progress report** (FYP InfoNet, 20 Nov 2026 23:59) and a
**Week 12 presentation** (16–20 Nov, to supervisor *and* assessor; failure = zero).

## Read in this order

| # | File | What it gives you |
|---|---|---|
| 1 | `chatgpt_prompt.md` | **the instructions**: verification, claim audit, innovation decision, research, per-document rewrite, repo audit, grade readiness, deck + script |
| 2 | `MANIFEST.md` | page/table/figure counts, what is complete vs in progress |
| 3 | `docs/report_internal_en.pdf` | the long-form technical report (source of truth) |
| 4 | `docs/progress_report_en.pdf` | current school-template report |
| 5 | `docs/ieee_manuscript_en.pdf` | current journal draft (single-column review draft) |
| 6 | `data/DATA_DICTIONARY.md` | every CSV, its columns and what they mean |
| 7 | `code/CODE_MAP.md` | how the repo is organised, which files are entry points |
| 8 | `docs/Requirements_ProjectProgressReport_2627A.pdf` | **report template only**: PART A + PART B 1,2,3,4,6,7,8 |
| 9 | `docs/Appendix_II.pdf` | **presentation rubric only**: four areas, 0–4 each |

The two PDFs have different jobs. The email of 30 Oct 2026 defines *deadlines and penalties*
(no submission / no presentation = zero; late = sub-grade per day) — it does **not** define
A-range criteria. A-range must be argued from the template plus the rubric.

## The numbers you must not get wrong

- Reproduction: 1.4995 vs paper 1.4355 (**+4.5 %**), sign crossover 2–2 (L24/L36 better, L48/L60 worse); MAE 0.8043 vs 0.7452.
- 28-arm accuracy: **MIFlu 1.5574** < PatchTST 1.6621 < NLinear 1.8716 < DNN 2.1415 … CNN 5.6155; spread 3.6×.
- Peak skill (K&S): **NLinear 4/16** (all step 0, PIE 3.2 %), **MIFlu 4/16** (3 step-0 + L48 step 1, PIE 18.3–24.8 %), **PatchTST 0/16** (PIE 32.8 %).
- Rank associations: ρ(MSE, mean PIE) = **+0.74**; ρ(MSE, K&S passes) = **−0.43** (p = 0.023).
- Efficiency: slope **+0.1171**, R² **0.0223** (11 parametric arms); Pareto {NLinear 2,520; PatchTST 531,878} = **211×** for **11.2 %**.
- Significance: 136 pairs, 109 significant; NLinear–PatchTST **p(Holm) = 0.1143** (rank 117/136).
- Encoders: 11 frozen arms, best 4.7374, worst 5.2049 = 3.04–3.34× MIFlu; **0/16** passes; all worse than a decision tree (4.3198).
- Ablation ladder: **27/60** cells at the 3 Nov snapshot; **no trend claimed**. `--no-text` is bit-identical (masked text branch) — a structural check, not an effect.

Do **not** write: “NLinear is the only arm that passes”, “MSE and peak skill are decoupled”,
“60/60, monotonic”, “p = 0.114 means no difference”, “we beat the paper”, “16 arms”.

## What is in this pack, and what is not

Included: the six PDFs (EN + ZH), all 83 CSVs, the six key figures, the methodology and hygiene
notes, the document-generator source (`code/dlv/*.py`), the peak-skill plot script, the report
template and the presentation rubric.

Not included: raw `pred_*.npz` (≈1 GB), the 165 MB archive, the full `05_程序代码` tree, HPC job
logs, the stale 2 November prompt. If you need any of them, say which file and why.

## What to return

Follow `chatgpt_prompt.md` §15: `CLAIM_AUDIT.md`, `INNOVATION_DECISION.md`,
`LITERATURE_REVIEW.md`, `DOC_REVIEW.md`, `REPO_AUDIT.md`, `GRADE_READINESS.md`, the revised
documents, `build_deck.py` + `deck_spec.json` + the PPTX, `TALKING_SCRIPT.md`, `QA_SHEET.md`,
`CHANGES.md`. Mark anything you could not run or verify; never invent a number, a citation or a
venue fact.

## One-paragraph summary you can trust

The reproduction is honest and within 4.5 % of the paper on the four-horizon mean, with a
horizon-dependent sign. Under one protocol, MIFlu wins on MSE but not on calibration; PatchTST
is second on MSE and fails every K&S cell; NLinear is third on MSE, passes every horizon one week
ahead, and is 211× smaller than PatchTST. Frozen LLM encoders do not transfer. Size does not
predict accuracy. The scientific story is “the deployment ordering is not the accuracy ordering”,
supported by a rank correlation and a frontier inversion — not by “MSE is useless”.
