> Review note, 2026-11-04: use audit/ and the rebuilt corpus for current conclusions. The actual paired CSV includes MIFlu and excludes DLinear. The no-text archive is statically inspectable; its runtime results were not executed in this review.

# HANDOFF PROMPT — verify, review and regenerate the MLFlu deliverables

**Version:** 2026-11-03. Supersedes the 2 November version, archived at
`99_旧文件存档/chatgpt_prompt_20261102.md` (that file still says 16 arms and 60/60 ablation).
**For:** ChatGPT (or any capable writing/verification agent)
**Project:** independent reproduction of MIFlu (Moon et al., IEEE JBHI 2025) + a 28-model
influenza-forecasting benchmark on the CDC national series
**Owner:** Sunny (FYP, CityU EE), supervisor Prof. Katie Chan

> **How to use this file.** Attach **`PROJECT_HANDOFF.zip`** (the complete snapshot; it uploads and
> the assistant can read across its ~1,500 files) and paste this file. Tell it to start at
> **`00_START_HERE.md`** in the zip root, then follow this prompt. A lighter
> `CHATGPT_CONTEXT_PACK.zip` (6.9 MB) exists as a fallback if an upload limit is hit: it carries
> the six PDFs, all CSVs, the key figures, the notes, the document generator and both school PDFs,
> but not the raw `pred_*.npz` or the full training tree. Then say: *“Follow §16 (online research)
> → §17 (per-document optimisation, including the repo README) → §13/§14 (innovation decision and,
> if needed, code) → §20/§21 (repo audit, A-range) → §18 (deck + talking script). Do not skip the
> research pass; return the §15 deliverables.”* The agent cannot run the local LibreOffice build or
> the HPC jobs; it returns revised sources, a buildable deck and CPU code, and the owner
> rebuilds/executes.

---

## 0.1 Hard constraints from the EE FYP Director (email of 30 October 2026)

These are non-negotiable and override any stylistic preference:

- **Progress Report submission:** via **FYP InfoNet**, on or before **20 November 2026, 11:59 pm**.
  A sub-grade deduction applies **per day** for late submission; **no submission = zero mark**.
- **Progress Presentation:** in **Week 12 (16–20 November 2026)**, to **both the supervisor and
  the assessor**. **Failure to present = zero mark.**
- The student must **proactively arrange the presentation appointment** with both parties by the
  proposed deadline; assume the deck is sent to them as a PDF beforehand and that both attend.
- The report must follow the attached template `Requirements_ProjectProgressReport_2627A (1).pdf`
  exactly: **PART A** + **PART B sections 1, 2, 3, 4, 6, 7, 8** (there is no section 5).
- The presentation is graded with `Appendix II.pdf` (four rubric areas, 0–4 each).

Consequence for your output: the progress report and the 5-minute talk are the two artefacts
that carry marks this semester. Optimise them for those two rubrics first; the journal
manuscript is secondary until after 20 November.

---

## 0. What you are asked to do

You are the academic writing and verification agent for this project. Work only from the
artefacts in `PROJECT_HANDOFF.zip`. Your job is, in this order:

1. **Verify** every number in the six documents against the CSVs (§3). Report any mismatch.
2. **Audit the external advice** quoted in §12: which claims are true, partly true or false, and
   whether the evidence is enough *as an evaluation paper*.
3. **Decide whether an innovation/mechanism is needed** (§13) for JBHI, a CCF-B venue or a short
   paper — and, if so, produce the plan **and the complete code** (§14), CPU-first, with only
   the HPC training left to the owner.
4. **Research online** (§16) before rewriting: the K&S thresholds, the 2023–26 LLM/foundation-model
   time-series literature, evaluation-critique work, calibration/conformal methods, and the
   current venue scope, ranks and deadlines. Cite only sources you have actually read.
5. **Review and optimise every document** (§17) — internal report, FYP progress report, IEEE
   manuscript, the two READMEs and the MANIFEST — informed by that research.
6. **Regenerate** the FYP progress report strictly to the school template
   (`Requirements_ProjectProgressReport_2627A (1).pdf`, §6).
7. **Regenerate** the IEEE JBHI manuscript (English; Chinese mirror optional).
8. **Build the actual presentation file** (§18): `build_deck.py` + `deck_spec.json` +
   `Week12_Progress_Presentation.pptx` with speaker notes, a 5:00 word-for-word talking script,
   a Q&A sheet, and a rubric map. An outline is not a deliverable.
9. **Audit the codebase and decide whether it needs refactoring** (§20): structure, hygiene,
   tests, reproducibility, licence — then a fix-now / fix-after / leave-alone decision.
10. **Estimate whether this is A-range** for the FYP report and the talk, and whether it is
    publishable at IEEE JBHI or a CCF-B venue (§21), with the three fixes that move it up.

**Hard rule:** you may rewrite prose, reorder sections and improve tables. You may **not**
invent a number, an experiment, a result, a citation or a venue fact. Every number you write
must be traceable to a CSV or to a value stated in §2; every citation must come from a source
you actually opened in §16. If something is not measured or not verifiable, write
"not measured / in progress / unverified" and say why.

---

## 1. Read these first, in this order

| # | Path inside the zip | Why |
|---|---|---|
| 1 | `01_最终报告/MANIFEST.md` | inventory: page counts, tables, figures, what is complete |
| 2 | `01_最终报告/report_internal_en.pdf` (and `_zh`) | the long-form source of truth |
| 3 | `01_最终报告/progress_report_en.pdf` | current school-template report |
| 4 | `01_最终报告/ieee_manuscript_en.pdf` | current journal draft |
| 5 | `02_数字表格/*.csv` | the only source of numbers |
| 6 | `04_详细说明文档/METHODOLOGY_METRICS_AND_SPLIT.md` | metric definitions, split, leakage guard |
| 7 | `04_详细说明文档/REPO_HYGIENE.md` §4 | evidence map |
| 8 | `Requirements_ProjectProgressReport_2627A (1).pdf` | the school template you must follow |
| 9 | `Appendix II.pdf` | the presentation rubric you must satisfy |
| 10 | `05_程序代码/plot_peak_skill.py` | how the 28-arm heat map is generated |
| 11 | `tests_archive/test_miflu_ablations.py` | the ablation-flag invariant (bit-identity of `--no-text`), archived for inspection |

**Which document governs what.** `Requirements_ProjectProgressReport_2627A (1).pdf` governs
**only the progress report** (PART A + PART B 1,2,3,4,6,7,8; no section 5). `Appendix II.pdf`
governs **only the presentation** (four rubric areas, 0–4 each). The 30 October email (§0.1)
governs deadlines and the zero-mark rules — it does **not** define A-range criteria, so the
grade estimate in §21 must be derived from the template plus the rubric.

Key CSV files: `BENCH_MSE_BY_MODEL_L.csv` (28 models × 4 horizons), `BENCH_PTE_PIE_BY_STEP.csv`
(28 × 4 × 4 K&S cells), `BENCH_EFFICIENCY.csv` (parameters, Pareto flags, slope, R²),
`BENCH_PAIRED_TESTS.csv` (136 Holm-corrected pairs), `ESSAY_VS_REPRODUCTION_TABLE_V.csv`
(the Table V reproduction), `BENCH_SEASONAL_NAIVE.csv`, `BENCH_GPU_PROVENANCE.csv`.

Do **not** use `01_最终报告/chatgpt_prompt.md` for numbers: it is the 2 November prompt and
still says the ablation is 60/60 complete.

---

## 2. Ground truth (verified 2026-11-03; use exactly these)

### 2.1 Data and protocol
- 966 weekly rows × 7 channels, bit-identical to the author's file (max|diff| = 0).
- Chronological split 676 / 97 / 193 (70/10/20); strict containment guard; min test target-start row 773.
- Evaluation windows `(W//16)*16` = **160/144/144/128** at L = 24/36/48/60, shared by all 28 arms.
- Reproduction protocol: **10 seeds** (2021–2030), validation-selected checkpoint, 7-variable
  aggregate MSE.
- Benchmark protocol: **3 seeds** (42/43/44), same windows, same checkpoint rule.
- Two disclosed deviations: validation checkpoint (fixes test-set leakage) and the 7-variable
  metric (fixes the original test loader covering 1 of 7 variables).

### 2.2 Reproduction (paper's Table V)
| Horizon | Ours (10-rep mean) | Paper | Δ MSE | Ours MAE | Paper MAE |
|---|---|---:|---:|---:|---:|
| L=24 | 1.3045 ± 0.0883 | 1.542 | −15.4 % | 0.7482 | 0.726 |
| L=36 | 1.3561 ± 0.1603 | 1.422 | −4.6 % | 0.7712 | 0.779 |
| L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | 0.8381 | 0.757 |
| L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | 0.8596 | 0.719 |
| 4-horizon | **1.4995** | 1.4355 | **+4.5 %** | **0.8043** | 0.7452 (+7.9 %) |

Sign crossover 2–2. Never claim superiority over the paper.

### 2.3 Benchmark (28 arms, 3 seeds, 7-variable z-space MSE)
MIFlu **1.5574** < PatchTST **1.6621** < NLinear **1.8716** < DNN 2.1415 < TimeCMA 2.6081 <
Gradient Boosting 3.6645 < KNN 3.7854 < Random Forest 3.8901 < iTransformer 3.9945 <
Decision Tree 4.3198 < … < CNN 5.6155. Spread = **3.6×**. Seasonal naive = **6.2132**.

### 2.4 Peak skill (Kramer & Shaman: PTE ≤ 1 week AND PIE ≤ 25 % in the same cell)
| Arm | Passes | mean PTE | mean PIE | step-0 PIE |
|---|---:|---:|---:|---:|
| NLinear | **4/16** (all step 0) | 1.677 wk | 9.477 % | **3.2 %** |
| MIFlu | **4/16** (3 step-0 + L48 step 1) | 1.128 wk | 26.846 % | 18.9 % |
| PatchTST | **0/16** | 1.240 wk | 32.755 % | 30.6 % |

MIFlu's passing cells have PIE 18.3–24.8 % (against the 25 % boundary) and it fails L=48 at
step 0 (PTE 1.22 wk). All other 25 arms pass 0/16.

### 2.5 Rank associations (28 arms)
- Spearman ρ(MSE, mean PIE) = **+0.736**, p < 1e-4 → better MSE *does* go with better calibration.
- Spearman ρ(MSE, K&S passes) = **−0.429**, p = 0.023 → the acceptance verdict does **not** follow MSE.

### 2.6 Efficiency
- Slope of MSE on log10(parameters), 11 parametric arms: **+0.1171**; R² = **0.0223**.
- Pareto set = {NLinear, 2,520 params; PatchTST, 531,878 params} = **211×** for **11.2 %** lower MSE.

### 2.7 Significance (12 matched horizon×seed cells, **17 models** → 136 pairs)
- The paired-test CSV covers the **17 non-encoder arms** (13 conventional + 4 LLM-based including MIFlu), not all 28 models. 136 = C(17, 2).
- **Holm must be recomputed from `p_raw`.** The exported `p_holm` column was produced with a reverse
  cumulative minimum, which is not a valid Holm adjustment. Corrected values: **0 of 136** pairs
  survive at 0.05 (128 of 136 are significant before correction), because with n = 12 the smallest
  attainable raw p is 0.00049 and m = 136 makes the smallest attainable adjusted p 0.066.
- NLinear vs PatchTST: mean Δ MSE +0.2095 (PatchTST lower), NLinear lower in 2/12 cells,
  raw p = 0.0059, **adjusted p = 0.1172**, Cohen's d = 1.15. This pair is the **117th smallest**
  of 136 p-values — a "strongest six" table would omit it.
- Consequence: report the effect size and CI; do not claim family-wise significance, and do not say
  "most pairs are cleanly separated".

### 2.8 Frozen LLM encoders (11 arms, 132/156 cells)
Best Hunyuan-1.8B **4.7374**, worst Qwen2.5-1.5B **5.2049** = 3.04×–3.34× MIFlu; every one is
worse than a decision tree (4.3198); **none** passes K&S in any cell.

### 2.9 Ablation ladder (called Table VIII in the project plan)
5 variants (no_lora; K = 2/4/8/12) × 4 horizons × 3 seeds = **60 cells**, reference = the K=6
arm already in the benchmark. At the 3 Nov 2026 snapshot **27/60** cells were complete
(driver job 722968) and no per-variant export had been pulled → **no depth trend may be claimed**.
One result is established: the text tokens sit behind the causal mask and the head reads only
the time patches, so `--no-text` is **bit-identical** to the full arm (asserted by
`tests_archive/test_miflu_ablations.py`): a structural verification, not an ablation effect.

---

## 3. Verification task (do this before rewriting anything)

1. Recompute the 28-arm ranking from `BENCH_MSE_BY_MODEL_L.csv`; confirm MIFlu 1.5574 first,
   PatchTST 1.6621 second, NLinear 1.8716 third, and the 3.6× spread.
2. Recompute the pass counts from `BENCH_PTE_PIE_BY_STEP.csv`; confirm NLinear 4/16, MIFlu 4/16,
   PatchTST 0/16 and the PIE values above.
3. Recompute slope and R² from `BENCH_EFFICIENCY.csv` (11 non-null parameter rows).
4. Recompute Holm from `p_raw` in `BENCH_PAIRED_TESTS.csv`; confirm 0/136 survive and NLinear–PatchTST adjusts to 0.1172. Do **not** trust the exported `p_holm` column (reverse cumulative minimum bug).
5. Confirm the reproduction table against `ESSAY_VS_REPRODUCTION_TABLE_V.csv` (MSE **and** MAE;
   the 4-horizon MAE is 0.8043, not 0.7597).
6. Confirm the encoder range and that every encoder exceeds the decision-tree MSE.
7. Report: a table of "claim → value → file → status (match / mismatch)", then a list of any
   sentence in the six documents that is not supported by these values.

---

## 4. Claims you must NOT make (they are false or unsupported)

| Do not write | Write instead |
|---|---|
| "NLinear is the only arm that passes K&S" | NLinear **and** MIFlu each pass 4/16, by different routes: NLinear all four step-0 cells with PIE 3.2 %; MIFlu three step-0 cells at PIE 18.3–24.8 % plus L48 step 1 |
| "NLinear crushes / beats the MSE champion on peak skill" | NLinear is the **calibration** champion (PIE 9.5 % vs 26.8 %); MIFlu has the better mean PTE (1.13 vs 1.68 wk). It is a trade-off, not domination |
| "MSE and peak skill are decoupled / unrelated" | They are positively rank-correlated across 28 arms (ρ = +0.74); what fails is the **ordering of the frontier** (calibration order is inverted at both ends among the three lowest-MSE arms) and the acceptance verdict (ρ = −0.43 with passes) |
| "PatchTST's 211× buys nothing" | The benchmark **does not establish** an accuracy advantage for the 211× cost (p_holm = 0.117); that is a failure to reject equality, not proof of equivalence (d = 1.15, PatchTST lower in 10/12 cells) |
| "Ablation complete at 60/60, monotonic depth trend" | 27/60 at the snapshot; design + status only; no trend |
| "We beat / outperform the original paper" | Reproduced within 4.5 % on the 4-horizon MSE mean, with a horizon-dependent sign |
| "16-arm benchmark" | 28 arms (13 conventional + 4 LLM-based, MIFlu and 3 published + 11 frozen encoders) |
| "PatchTST is the accuracy champion" | MIFlu is (1.5574) |
| "Parameter count is pure noise" | Slope is positive and R² = 0.0223: size explains ~2 % of the variance and its sign is unfavourable |
| "The text branch contributes to accuracy" | In this implementation it cannot change a prediction (masked out); the multimodal claim is unsupported as shipped |

Also keep these caveats visible: K&S thresholds are attributed to Kramer & Shaman (2019) but
marked **[to verify]**; the peak detector is the project's engineering choice; one dataset,
one country; n = 12 for the tests.

---

## 5. The three findings the documents must carry (after the relevant table)

The user wants each benchmark section to end with an explicit, bolded **conclusion** block.
Use these labels and keep them after the corresponding result table:

- **F0 — accuracy alone does not identify a deployable model** (after the 28-arm accuracy table).
- **F1 — the deployment ordering is not the accuracy ordering** (after the peak-skill tables):
  frontier inversion + ρ(passes) = −0.43.
- **F2 — parameter count is not a proxy for accuracy** (after the Pareto table): +0.1171, R² 0.0223.
- **F3 — the 211× cost is not statistically distinguishable from noise** (after the paired table):
  p_holm 0.117, with the equivalence caveat.
- **F4 — frozen LLM representations do not transfer** (after the encoder table): 3.04–3.34×,
  0/16 passes, worse than a decision tree.
- **F5 (provisional) — the multimodal claim is unsupported as shipped** (after the ablation
  table): masked text branch; depth/LoRA open at 27/60.

---

## 6. Task A — FYP progress report (strict school template)

Source: `Requirements_ProjectProgressReport_2627A (1).pdf`. The template has **PART A**
(identity) and **PART B sections 1, 2, 3, 4, 6, 7, 8 — there is no section 5**. Number the
headings exactly 1,2,3,4,6,7,8 and do not renumber them.

Required content per section:
1. **Project objectives** — problem statement (MIFlu's leak, thin baselines, single seed) and a
   numbered list of objectives (reproduce; benchmark 28; decide deployment; test LLM transfer).
2. **Original project planning chart** — timeline with tasks and milestones, annotated with
   actual status (reproduction done; benchmark done; ablation 27/60; Table VI/IX pending).
3. **Background study** — technical background **and** contemporary/societal context
   (post-COVID investment, WHO/CDC use of forecasts, reproducibility critique, the
   metric-versus-decision gap).
4. **Methodology** — two protocols, deviations, metrics (PTE/PIE definitions, thresholds
   [to verify]), peak detector, windows; **design impact in a broad, global and societal
   context** (why splitting accuracy from deployment value matters; auditable provenance).
6. **Progress** — actual progress against §2, reproduction table + F-block, benchmark table +
   F0, peak table + F1, efficiency/significance + F2/F3, encoders + F4, ablation + F5,
   and problems encountered (leak, single-variable loader, seed/snapshot defects, queue slip).
7. **Summary of objectives addressed and results achieved** — table: objective / addressed
   (yes/no) / percentage achieved. Keep the percentages honest (ablation 45 %, rolling origin 15 %,
   manuscript 70 %).
8. **Work schedule and expected results for the next one to two months** — dated table
   (16 Nov ladder; 20 Nov submission + presentation; 30 Nov Table VI + IX; 31 Dec rolling
   origin; Jan–Apr 2027 JBHI submission), risks and mitigation, signature line.

Length target 7–9 pages, A4. Keep the current visual style (title block, PART A table).

---

## 7. Task B — presentation (Week 12, 16–20 Nov 2026) + talking script

Build a **5-minute** talk (plus 2–3 min Q&A) for the supervisor and assessor. It must satisfy
the four rubric areas of `Appendix II.pdf`:

- **I. Technical content — relevance & accuracy**: every number correct; no overclaim.
- **II. Technical knowledge — depth & breadth**: explain *why* the criterion differs from MSE,
  why the frontier inverts, why frozen encoders fail.
- **III. Delivery — organisation & preparation**: clear narrative arc, signposted.
- **IV. Style, pacing, time management**: 5:00 ± 20 s, ~12 slides, no reading.

Suggested arc (adjust if you have a better one):
1. Title + one-sentence claim (the forecast exists for a decision, not for MSE).
2. The problem: MIFlu's protocol (test-set checkpoint, one seed, two baselines).
3. What we did: leak-free reproduction + 28-arm benchmark (one protocol).
4. Reproduction result: 1.4995 vs 1.4355, sign crossover (never "we beat it").
5. Accuracy ranking: MIFlu 1.5574, PatchTST 1.6621, NLinear 1.8716.
6. Peak skill: the K&S criterion and the pass grid (NLinear 4/16, MIFlu 4/16, PatchTST 0/16).
7. Finding F1: the frontier is ordered backwards (ρ = +0.74 overall, −0.43 for passes).
8. Finding F2/F3: 211× for 11.2 %, p_holm = 0.117, "not established".
9. Finding F4: 11 frozen encoders, 3× worse, none passes.
10. Ablation: 27/60, design and status, the masked text branch.
11. Threats & what is next (Table VI, rolling origin, JBHI).
12. One-slide summary of the three findings + the deployment recommendation.

Deliverables: (a) slide-by-slide outline with the exact numbers on each slide; (b) speaker
notes per slide; (c) a **word-for-word talking script** with timings; (d) 10 likely Q&A
questions with short, accurate answers (include the "why 3 seeds vs 10?", "is p=0.117
equivalence?", "isn't MIFlu also 4/16?", "why is the text branch useless?" questions).

---

## 8. Task C — IEEE JBHI manuscript

Keep the current structure (I Introduction, II Related Work, III Data, IV Method, V Experiments,
VI Results A–G, VII Threats to Validity, VIII Conclusion, IX References; Appendix A panels).
Improve:
- **Abstract ≤ 250 words**, no spliced sentences, ending with the deployment recommendation.
- **Contributions**: four numbered items (leak-free reproduction; 28-arm benchmark; frontier
  inversion finding; parameter/significance analysis), each with the one number that supports it.
- **Tables I–VIII** in the current order; keep the notes that explain *why* a table shows what
  it shows (especially the paired-test table).
- **Threats**: single dataset; n = 12 and the p floor; non-significance ≠ equivalence; K&S
  attribution [to verify]; frozen-feature-only encoder axis; ablation incomplete.
- **References**: complete volumes/pages/DOIs where known; keep `[to verify]` where not.
- The draft is **single-column for review** (10-column tables are unreadable in two columns);
  say so in the cover note, and provide LaTeX-ready table captions/notes for the final
  two-column typesetting.

Do not add a "new method" section. The contribution is the empirical evaluation; say that
plainly in the Introduction and do not apologise for it.

---

## 9. Stale or superseded material

- `99_旧文件存档/chatgpt_prompt_20261102.md` — the 2 November handoff (not in the zip). It says
  the ablation is 60/60 and still uses the old "decoupling" wording. **Do not copy numbers from it.**
- `04_详细说明文档/REPRODUCTION_BENCHMARK_COMPARISON.md` — claims the ladder is 60/60 and
  monotonic; no artefact supports this. Treat 27/60 as the state.
- `01_最终报告/ieee_manuscript_*.pdf` was two-column until 3 Nov; it is now a single-column
  review draft. Do not "restore" the two-column layout without re-typesetting the tables.
- `PROJECT_HANDOFF.zip` inside the zip is excluded by construction; the zip you received is
  the current snapshot.

---

## 10. Style and format constraints

- Bilingual: English and Simplified Chinese editions of every document. The Chinese edition
  uses SimSun body / Microsoft YaHei headings; keep CJK ratio > 0.30 (the build checks it).
- Plain, direct academic English. Short sentences. Define PTE/PIE at first use.
- Tables are numbered automatically per document; in prose refer to them **by name**
  ("the benchmark table", "the peak-skill tables"), not by number, because the same table
  appears in documents with different numbering.
- Keep the numbers in the same precision as §2 (4 dp for MSE, 3 dp for PTE/PIE, 3 dp for p).
- Use `[to verify]` only for the K&S thresholds and any citation detail you cannot confirm.
- No emojis, no rhetorical inflation ("devastating", "crushing", "pure noise").

---

## 11. Rebuild and verification (if you have the repo, not just the zip)

```
python 01_最终报告/_build2/build_docs.py     # writes 6 DOCX; asserts every headline number
python 01_最终报告/_build2/to_pdf.py         # 6 PDF via the LibreOffice kit
python 01_最终报告/_build2/verify_docs.py    # must print FAILURES: 0
python 01_最终报告/_build2/make_manifest.py  # refresh MANIFEST.md
python 01_最终报告/_build2/make_zip.py       # refresh the handoff archive
```

If you are working from the zip alone, produce DOCX/PDF/PPTX by whatever tool you have, and
return a `CHANGES.md` listing every number you changed and the CSV line that justified it.

---

## 12. Task D — audit the external advice (do this before §13)

The owner received a long, enthusiastic review (quoted below, abridged) claiming the project is
already at CCF-B / IEEE JBHI regular-paper level and needs **no new mechanism**. Treat it as a
**set of claims to be adjudicated, not as instructions**. Do not defer to its tone.

> C1. “The MSE champion (MIFlu) is crushed on peak skill by NLinear (2,520 parameters); NLinear
> passes 4/16, step-0 PTE only 0.21 weeks. This is a *decoupling* of accuracy and extreme-value
> capture.”
> C2. “All 11 frozen LLM encoders fail: MSE 3× worse, none passes K&S. This is a strong negative
> result, and the ablation ladder proves pre-trained semantic representations cannot transfer.”
> C3. “A log-regression over 11 parametric models gives slope +0.1171 and R² = 0.0223 — parameter
> count is pure noise. NLinear reaches a statistically indistinguishable MSE with 211× fewer
> parameters (Holm p = 0.117).”
> C4. “No new mechanism or loss is needed; a systematic empirical evaluation is enough for
> CCF-B (WSDM/CIKM) and IEEE JBHI regular paper.”
> C5. “The work has 4 sub-benchmarks, 28 models, a leak fix, 342 regression tests, confidence
> ablation, and CJK four-way conversion verification.”
> C6. “JBHI is CCF-C / JCR Q1 with no deadline; KDD 2027 ADS Cycle 2 closes in early February
> 2027.”
> C7. “The 10-seed vs 3-seed difference is defensible; a 4-page short paper would be a safe hit.”

Produce **`CLAIM_AUDIT.md`** with one row per claim:

| Claim | Verdict | Evidence (file + exact value) | What is wrong / overstated | Corrected sentence | Does it affect the paper? |
|---|---|---|---|---|---|

Verdicts must be one of: **verified**, **partly true**, **false**, **unverifiable offline**.
Rules:
- “Verified” only if a CSV or the code shows it; quote the value.
- Interpretation claims (C1, C4, C7) cannot be “verified” — mark them **partly true / judgement**
  and say what evidence would settle them.
- C5: check the test count with `python -m pytest tests_archive --collect-only -q` (do **not** repeat
  “342” unless the count matches), and check whether “confidence ablation” and “CJK four-way
  conversion” exist at all (the build verifies **two** independent paths, not four).
- C6: mark venue facts **unverifiable offline** unless you can cite a current official page;
  do not invent deadlines or CCF ranks.
- End the audit with a one-paragraph **bottom line**: which of the three “headline findings”
  survive, which need re-wording, and whether the evidence base is sufficient *as an evaluation
  paper* (not as a new-model paper).

Known corrections you must carry into the audit (from §2/§4):
- C1: MIFlu also passes 4/16; NLinear wins on PIE (9.5 % vs 26.8 %) but loses on mean PTE
  (1.68 vs 1.13 wk). “Crushed” is false; “calibration champion with a trade-off” is correct.
- C3: the numbers are right; “pure noise” is an over-reading of R² = 0.0223, and p = 0.117 is
  a failure to reject, not proof of equality (d = 1.15, PatchTST lower in 10/12 cells).

---

## 13. Task E — do we need an innovation / mechanism? (decision, not advocacy)

Produce **`INNOVATION_DECISION.md`**. Answer the question the owner actually has: *given the
verified evidence, is an evaluation-only paper enough for each target, or is a mechanism
needed — and if so, what is the cheapest one that would change a reviewer's verdict?*

Required content:

1. **What each venue rewards.** One short paragraph each, from your own knowledge (mark
   uncertain statements):
   - IEEE JBHI regular: clinical/public-health utility, validation, deployment relevance,
     methodological soundness; tolerance for benchmark/audit papers.
   - CCF-B conferences (WSDM, CIKM): novelty of insight or method; benchmark papers are
     accepted but usually need either broad coverage + a prescriptive rule, or a new method.
   - KDD ADS: deployed application, system, real-world evaluation.
   - A 4-page short paper: what can and cannot fit.
2. **Honest bar assessment** for the current artefact: for each target, give
   (a) desk-reject risk, (b) “reviewer asks for a method” risk, (c) what single missing piece
   would most raise acceptance probability. Distinguish *evidence gaps* (rolling origin,
   regional, more seeds) from *contribution gaps* (no mechanism).
3. **Three options**, each with cost and expected effect:
   - **O1 — evaluation only.** No new training. Strengthen with the analyses already planned
     (rolling origin, regional, calibration decomposition, decision-curve analysis). Target:
     JBHI regular or CCF-B short. State what would still be missing.
   - **O2 — post-hoc mechanism, CPU only.** Reuses the existing `pred_*.npz` / CSVs; no GPU.
     Candidates to evaluate (pick, don’t just list): a calibration-aware model-selection rule;
     peak-height recalibration (isotonic/linear/quantile mapping) fitted on validation seasons;
     a hybrid NLinear+PatchTST blend or switch; conformal prediction intervals for peak height
     and timing; a decision-theoretic selection rule with an explicit cost matrix.
     Each must be falsifiable on the existing 12 matched cells and report MSE, PTE, PIE, K&S
     passes, and a Holm-corrected comparison against NLinear and PatchTST.
   - **O3 — trained mechanism (HPC).** Peak-weighted / asymmetric loss, gated text injection,
     peak-aware fine-tuning, or a small peak head. Requires retraining; give A100-hour estimates
     and the exact cells.
4. **Recommendation.** Choose one option and justify it against the 20 November deadline and the
   JBHI target. If O1 is genuinely enough, say so plainly — do not invent a mechanism to look
   innovative. If O2 is needed, say exactly which mechanism and why it is the minimum that
   changes the verdict.
5. **A “minimum publishable unit” per target**: the smallest set of results that makes each
   target defensible, with a checklist.

---

## 14. Task F — if a mechanism is needed: plan + complete code

Do this only if §13 recommends O2 or O3. Produce three artefacts.

### 14.1 `EXPERIMENT_PLAN.md`
- 2–4 candidate directions, each tied to a finding (F1 frontier inversion, F2 parameter cost,
  F4 encoder failure), with: hypothesis, mechanism, why it is cheap, what result would falsify
  it, expected effect size, compute in A100-hours, risk.
- Rank by (novelty × feasibility × compute). State the ranking rule explicitly.
- For the chosen direction: phases, cells (model × horizon × seed), metrics (MSE, MAE, PTE, PIE,
  K&S pass count, calibration slope/intercept), statistical tests (paired sign-flip + Holm,
  bootstrap CI, effect size), acceptance gates, stop rules, and what to do if the gate fails.
- A **negative-result contingency**: if the mechanism does not beat NLinear on PTE without
  losing K&S, what does the paper report? (A negative result is acceptable; a fabricated gain is not.)

### 14.2 Code (complete, runnable, CPU-first)
Write real files, not pseudocode. Constraints:
- Python 3.9; only libraries already in the repo (`numpy`, `pandas`, `scipy`, `torch`,
  `matplotlib`, `python-docx`).
- **Read-only inputs**: `02_数字表格/*.csv`, `03_预测数据_证据/expanded_runs/**/pred_*.npz`,
  `06_原始数据集/`. Never modify an existing file.
- **New outputs only**: `02_数字表格/INNOV_*.csv`, `03_预测数据_证据/innov_*/`. Fixed, documented
  schemas (one row per model × horizon × seed, with a `variant` column).
- New code under `05_程序代码/innov_<name>/` (package) plus a thin CLI
  `05_程序代码/run_innov.py`, with `--dry-run`, `--limit`, deterministic seeds, and logging.
- A **sanity gate**: the code must first reproduce one existing number from the CSVs (e.g.
  MIFlu 1.5574 or NLinear PTE 1.677) and abort if it does not match to 1e-4.
- Unit tests under `tests/test_innov_*.py` (pure functions: calibration fit/apply, selection
  rule, metric recomputation), plus a CPU smoke test on a 2-model × 1-horizon subset that runs
  in < 2 minutes.
- If a component genuinely needs GPU/HPC, isolate it behind a flag, provide the `sbatch`
  template and the exact command, and make the CPU path still runnable (with the GPU step
  marked `SKIPPED (HPC)`).
- `RUN_ME.md`: exact commands, expected console output, expected output files, and acceptance
  criteria. Also a short “what Sunny must run on Burgundy” section with the job script.

### 14.3 Manuscript integration
- If O2/O3 is adopted: add a **Method** subsection, a **Results** subsection with `[TO FILL]`
  cells keyed to the new CSV columns, and a **Threats** paragraph on the post-hoc nature of the
  mechanism (fitted on validation, evaluated on test; no test leakage).
- If O1 is adopted: add a **Decision rule** paragraph that turns F1 into a prescriptive
  recommendation (select on K&S/PTE/PIE subject to an MSE budget), with the cost matrix and the
  exact rule, and update the abstract/contributions accordingly.
- Update the contribution list to say which of the four contributions is new.

---

## 15. Deliverables

Return, at minimum:

| File | Content |
|---|---|
| `CLAIM_AUDIT.md` | §12 table + bottom line |
| `INNOVATION_DECISION.md` | §13 options, recommendation, minimum publishable unit |
| `LITERATURE_REVIEW.md` | §16 sourced review (≥ 15 verified sources) and what it changes |
| `EXPERIMENT_PLAN.md` | only if O2/O3; phases, cells, gates, compute |
| `code/` (complete files) + `RUN_ME.md` | only if O2/O3; runnable, CPU-first, tests included |
| `DOC_REVIEW.md` | §17 per-document review: what changed, why, and the diff |
| `REPO_AUDIT.md` | §20 codebase/structure audit and the refactor decision |
| `GRADE_READINESS.md` | §21 FYP A-range check for the report and the talk |
| regenerated DOCX/PDF | internal report, progress report, manuscript (EN + ZH) |
| `build_deck.py` + `deck_spec.json` + `Week12_Progress_Presentation.pptx` | §18: a real, buildable deck |
| `TALKING_SCRIPT.md` | §18: word-for-word, timed to 5:00 |
| `QA_SHEET.md` | §18: 10 questions with short accurate answers |
| `CHANGES.md` | every number/sentence changed, with the CSV line that justified it |

---

## 16. Task G — online research first (do this before §17)

Do a real literature and venue check, not a memory dump. If you have no web access, say so in
the first line of `LITERATURE_REVIEW.md` and mark every external fact **unverified**; do not
invent a citation, a DOI, a deadline or a CCF rank.

Cover at least these threads (2022–2026 unless a classic):

1. **The source paper and its protocol** — MIFlu (Moon et al., IEEE JBHI 2025): what it claims,
   what it compares against, whether the checkpoint/loader issues we found are acknowledged in
   any later correction or follow-up.
2. **The K&S criterion** — Kramer & Shaman (2019, *PLOS Comput. Biol.* 15(2):e1006742): confirm
   the exact PTE/PIE definitions and the 1-week / 25 % thresholds, or record what the paper
   actually says. This closes our `[to verify]`.
3. **LLM / foundation models for time series** — Time-LLM, CALF, TimeCMA, Chronos, TimesFM,
   Moirai, Lag-Llama, and any 2025–26 follow-up: do any of them report peak skill, calibration,
   or epidemiological evaluation? This is the Related Work we must not miss.
4. **Evaluation critique and reproducibility** — papers arguing that MSE is an incomplete
   criterion (LTSF critiques, benchmark/reproduction tracks, "evaluation is broken" work),
   and any prior benchmark of influenza forecasters that we should cite or differentiate from.
5. **Calibration / conformal / decision analysis for time series** — the methods an O2 mechanism
   would build on (isotonic/quantile recalibration, conformal prediction, cost-sensitive
   selection), including what has already been done so we do not re-invent it.
6. **Venues** — IEEE JBHI scope, article types and typical length; WSDM/CIKM/KDD ADS scope and
   the current CCF rank; actual deadlines for the next cycles. Cite the official page and the
   date you accessed it; if a fact cannot be confirmed from an official page, mark it
   **unverifiable** rather than guessing.

`LITERATURE_REVIEW.md` format: a table
`topic | source (authors, year, venue) | DOI/URL | accessed | one-line finding | which section it changes`,
then:
- **Top 5 papers we must cite and why** (one line each);
- **Claims in our draft that are now outdated or already published elsewhere** (be blunt if our
  "first" claims are not first);
- **What we should NOT cite** (papers we have not read, or that do not support the sentence).

Only verified entries may enter the manuscript's reference list. Add a `[source: URL, accessed
YYYY-MM-DD]` note in your working file, not in the final references.

---

## 17. Task H — review and optimise every document (research-informed)

For each file below, produce a short review in `DOC_REVIEW.md` (audience, what is good, what is
weak, what you changed) and the revised file. "Optimise" means: correct, tighter, better
organised, and informed by §16 — not longer for its own sake.

| Document | Audience | What "better" means here |
|---|---|---|
| `01_最终报告/report_internal_en.docx` / `_zh` | supervisor, assessor, next agent | every claim traceable; F0–F5 after the right table; 12-section TOC; literature context in §1–2 and §10; no stale numbers |
| `01_最终报告/progress_report_en.docx` / `_zh` | supervisor + assessor, school template | exactly PART A + 1,2,3,4,6,7,8; problem statement and objectives; planning chart with status; societal context; methodology incl. design impact; progress vs plan; summary table; schedule + signature |
| `01_最终报告/ieee_manuscript_en.docx` / `_zh` | JBHI reviewers (or another top-tier target) | scope/venue fit — state whether the target is **IEEE JBHI, KDD ADS, WSDM or CIKM** and why; abstract ≤ 250 words; four contributions; Related Work refreshed from §16; Threats; references complete; tables I–VIII legible |
| `README.md` (repo root) | a stranger landing on the repo | one-paragraph what/why; headline results table (reproduction, 28-arm ranking, peak skill, encoders); repo map; 3-command quickstart; data availability; honest caveats (ablation 27/60, K&S to verify, single dataset); citation and licence. No hype, no emojis |
| `01_最终报告/README_报告说明.md` | the owner | accurate page counts, table counts, which file to read when, how to rebuild |
| `01_最终报告/MANIFEST.md` | the owner / auditor | inventory stays true after your edits (sizes, page counts, table/figure counts, zip stats) |

Rules: never change a number to make a sentence nicer; when you cut a claim, say in
`DOC_REVIEW.md` why; when you add a citation, it must come from §16 and be marked verified.

**Per-document research record (mandatory).** For **every row above — including `README.md`** —
write in `DOC_REVIEW.md`:
(a) which §16 threads you used for that document;
(b) the 3–5 strongest sources with DOI/URL and access date;
(c) the exact sentences or sections you changed because of them;
(d) anything you could not verify.
A document "review" that cites nothing is not a research-informed review; it is a spell-check.

---

## 18. Task I — generate the presentation file and the talking script

Deliver a **real deck**, not only an outline. Build it from code so it is reproducible:

- `build_deck.py` — python-pptx, 16:9 (13.333 × 7.5 in), a small palette, one message per
  slide, the exact numbers from §2, figures copied from `01_最终报告/figures/`
  (`fig_ks_ranking.png`, `fig_pte_pie_heatmap.png`, `fig_pareto_frontier.png`, and one forecast
  panel), speaker notes embedded per slide.
- `deck_spec.json` — slide titles, bullets, numbers, figure file, speaker note; `build_deck.py`
  reads it. The deck must rebuild byte-for-byte from the spec (no manual editing).
- `Week12_Progress_Presentation.pptx` — 11–13 slides, 5:00 ± 20 s:
  1 title + one-sentence claim · 2 the decision problem · 3 what MIFlu did and the leak ·
  4 what we ran (two protocols, 28 arms) · 5 reproduction result (sign crossover) ·
  6 accuracy ranking (MIFlu 1.5574) · 7 the K&S criterion and the pass grid ·
  8 F1: the frontier is ordered backwards · 9 F2/F3: 211× for 11.2 %, p = 0.117 not established ·
  10 F4: 11 frozen encoders · 11 ablation 27/60 + the masked text branch · 12 threats and next
  steps · 13 the ask / summary.
  Adjust the count if you merge slides, but keep 11–13 and the 5:00 timing.
- `TALKING_SCRIPT.md` — word-for-word, `[0:00–0:20]` style timings per slide, the exact sentence
  to say when a number appears, transitions, and two “if the assessor interrupts here” lines.
  British spelling, short sentences, no reading of bullet lists.
- `QA_SHEET.md` — 10 questions with 2–4 sentence answers, including the hostile ones:
  “MIFlu also passes 4/16 — so what is your finding?”, “p = 0.117 means no difference, right?”,
  “why 3 seeds and not 10?”, “isn't this just a reproduction?”, “why is the text branch useless?”,
  “what would you do with one more month / one more GPU?”.
- `HANDOUT.pdf` (optional, 2 pages): the 13-slide deck compressed to a leave-behind.
- A **rubric map** in `DOC_REVIEW.md`: slide → Appendix II area (I content accuracy,
  II technical depth, III organisation, IV style/pacing/time), with one line on how the slide
  earns that point.

If python-pptx is not available, ship `deck_spec.json` + a `build_deck.py` that documents the
exact API calls, and say so; do not ship a hand-waved “outline” and call it a deck.

---

## 20. Task J — inspect the codebase and decide whether it needs refactoring

Do a real repository audit, not a glance at the tree. Produce `REPO_AUDIT.md`.
If your environment cannot execute the repo (no torch, no GPU, no LibreOffice), do a **static**
audit and mark every "run" item as *not executed*, with the exact command the owner should run;
do not guess the output.

**Structure and hygiene**
- Map the tree at depth 2 (`01_最终报告`, `02_数字表格`, `03_预测数据_证据`, `04_详细说明文档`,
  `05_程序代码`, `06_原始数据集`, `hpc_experiments`, `tests`). Say what each is for and which
  files are entry points.
- Flag: duplicated or one-off scripts (e.g. the `hpc_experiments/*_fix*.py` family), dead code,
  hard-coded absolute paths, machine-specific assumptions, leftover scratch files, oversized
  artefacts committed by accident, secrets or personal paths.
- Check the "clean checkout" story: can a stranger reproduce one number with the documented
  commands? Run `python -m pytest tests_archive --collect-only -q` and report the count and any
  collection errors; run the smoke path you can run on CPU.

**Code quality and risk**
- Entry points and their CLI contracts; config vs constants; error handling; determinism
  (seeds); logging; where a silent failure could corrupt a published number.
- Test coverage by area (data / eval / model / analysis), not a single percentage.
- Data provenance: every headline number traceable to a CSV or npz; which are computed at
  build time and which are transcribed.
- Licence and third-party weights: is redistribution of the LLM checkpoints an issue? Is the
  repo's licence compatible with the paper's code-release statement?

**Refactor decision (the point of the audit)**
Give a table: `issue | severity (blocker / high / medium / low) | fix now or after 20 Nov |
effort (hours) | risk of changing a published number`. Then a clear recommendation:
- **Refactor now** only if it blocks the 20 November submission or reproducibility;
- **Refactor after submission** for structure, naming, deduplication, CI;
- **Do not touch** anything that would move a number before the deadline.
Explicitly answer: *is the current codebase good enough to support an IEEE JBHI submission
(code/data availability, one-command reproduction), or would a reviewer reject on
reproducibility grounds?* Give the three concrete things that would most improve that answer.

---

## 21. Task K — would this be an A-range FYP report and talk?

Produce `GRADE_READINESS.md`. Be honest and specific; do not inflate.

**What the email actually says.** The 30 October email defines *deadlines and penalties* (FYP
InfoNet by 20 Nov 23:59; late = sub-grade deduction per day; no submission = zero; present to
both supervisor and assessor in Week 12; no presentation = zero). It does **not** define
A-range criteria. So derive the A-range judgement from the two documents that do:
the **progress-report template** (`Requirements_ProjectProgressReport_2627A (1).pdf`) for
completeness, and **`Appendix II.pdf`** for the presentation rubric (four areas, 0–4).

**Progress report check** — one row per required section (PART A; 1 objectives; 2 planning
chart; 3 background; 4 methodology; 6 progress; 7 summary; 8 schedule):
`section | present? | complete? | accurate? | what an A-range reader expects | gap | fix`.
Then a band estimate (A / B / C) with the evidence, and the **three fixes with the largest
marginal gain**.

**Presentation check** — score each `Appendix II` area 0–4 with evidence from the deck and the
script:
- I. Technical content — relevance and accuracy (every number correct, no overclaim);
- II. Technical knowledge — depth and breadth (can explain *why* MSE ≠ deployment, why the
  frontier inverts, why frozen encoders fail);
- III. Delivery — organisation and preparation (narrative arc, signposting, slides that carry
  the argument);
- IV. Style, pacing, body language, time (5:00, no reading, confident).
Give the total /16 and the band; list the three fixes that would move it up one band.

**Publishability check (separate from the grade)** — for IEEE JBHI and for a CCF-B venue, give
a one-paragraph verdict with the three strongest and three weakest points, and say which of
O1/O2 (§13) the verdict depends on. Do not confuse "good FYP" with "publishable"; state both.

**Bottom line**: one paragraph — is this A-range now, what are the three things to do before
20 November, and what is the single biggest risk of not getting there.

---

## 22. Final acceptance

- [ ] every number in §2 appears identically in every document;
- [ ] no sentence from the “do not write” table survives;
- [ ] each benchmark section ends with its F-block (F0–F5);
- [ ] internal report TOC is 1..12 with no jump; progress report is 1,2,3,4,6,7,8;
- [ ] IEEE abstract ≤ 250 words and has no spliced sentence;
- [ ] ablation is 27/60 with no trend;
- [ ] `CLAIM_AUDIT.md` marks C1–C7 with evidence, and does not repeat “342 tests” or
      “CJK four-way” unless verified;
- [ ] `INNOVATION_DECISION.md` gives a clear O1/O2/O3 recommendation with costs;
- [ ] if O2/O3: the code runs on CPU with `--dry-run`, passes its tests, and its sanity gate
      reproduces an existing number before producing anything new;
- [ ] `LITERATURE_REVIEW.md` has ≥ 15 verified sources with DOI/URL and access dates, zero
      invented citations, and a list of what changed in Related Work;
- [ ] `DOC_REVIEW.md` covers **all six documents plus `README.md`**, and `README.md` is rewritten
      for a public audience with the honest caveats;
- [ ] `REPO_AUDIT.md` maps the tree, reports the real `pytest` count, and gives a
      fix-now / fix-after / leave-alone decision with effort and number-risk;
- [ ] `GRADE_READINESS.md` checks the report section by section and scores the talk on the four
      `Appendix II` areas, with a band, the three highest-gain fixes, and a publishability verdict
      kept separate from the grade;
- [ ] the deck rebuilds from `build_deck.py` + `deck_spec.json`, has 11–13 slides, speaker notes,
      and the talking script times to 5:00;
- [ ] every `[to verify]` item (K&S thresholds and any venue fact) is listed in one place at the
      end of your report, with what would settle it.
