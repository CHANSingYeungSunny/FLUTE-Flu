# -*- coding: utf-8 -*-
"""TASK 7 v8 English manuscript builder.

Mirrors HANDOFF_20261105/build_v7_manuscript.py (python-docx + LibreOffice-kit
CLI convert) but updates the manuscript BODY with the final v8 verified results:
complete legacy walk-forward panel, foundation models BLOCKED, resource subset,
CDC vintage, JBHI verification, and an explicit old-snapshot-vs-new-panels
separation section. Frozen CSVs / predictions / checkpoints / PPTX are not touched.
"""
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8")
OUT.mkdir(parents=True, exist_ok=True)
doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Inches(0.8)
    s.left_margin = s.right_margin = Inches(0.9)

style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(10)


def h(text, level=1):
    pgh = doc.add_heading(text, level=level)
    for r in pgh.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13 if level == 1 else 11)
    return pgh


def p(text, bold=False, italic=False, size=10, align=None):
    par = doc.add_paragraph()
    r = par.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    if align:
        par.alignment = align
    return par


def table(headers, rows, caption, widths=None):
    p(caption, bold=True, size=9)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, x in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = str(x)
        for r in c.paragraphs[0].runs:
            r.bold = True
            r.font.size = Pt(8)
    for row in rows:
        cells = t.add_row().cells
        for i, x in enumerate(row):
            cells[i].text = str(x)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph()


# ----------------------------------------------------------------------------
p("A common ten-seed re-evaluation of influenza forecasting: MIFlu, twenty-seven "
  "comparators, peak skill, depth ablation, and a complete legacy walk-forward panel",
  bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
p("CHAN Sing Yeung", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
p("Department of Electrical Engineering, City University of Hong Kong",
  size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
p("Draft v8 — 6 November 2026. Not submission-ready. The frozen revision-9.2 "
  "28-arm snapshot, the new 1120-cell national panel and the legacy 5-fold "
  "walk-forward panel are separate scoring populations and are reported separately.",
  italic=True, size=8, align=WD_ALIGN_PARAGRAPH.CENTER)

h("Abstract", 1)
p("We re-evaluate national influenza-like-illness forecasting on a 966-week CDC "
  "series with a single common protocol: input length 104 weeks, four forecast "
  "horizons (24/36/48/60), ten seeds (2021–2030), and 28 model implementations. "
  "The 1,120-cell matrix is complete. Recovering all seven channels from the "
  "trained MIFlu checkpoints lets every model be scored on two identical target "
  "populations: all valid windows and the historical complete-batch crop. On the "
  "all-valid panel the leading mean squared errors are MIFlu 1.7944, PatchTST "
  "1.9521 and NLinear 2.0782; the crop panel gives 1.4994, 1.6352 and 1.9027, "
  "reproducing the historical MIFlu mean. Peak skill changes the ranking: MIFlu "
  "passes 252 of 1,680 step-level Kramer–Shaman cells (15.0%), PatchTST 215 "
  "(12.8%) and NLinear 57 (3.4%). A 60-cell depth/LoRA ladder is non-monotonic "
  "(K4 best 1.4989, K12 worst 1.7604). In v8 the LEGACY five-fold N=3 "
  "walk-forward panel is now complete: 1,020 of 1,020 cells recomputed as ok "
  "from raw NPZ (218 recovered, no existing value changed), with full-panel "
  "per-model means over n=60 cells each (MIFlu 2.220289, PatchTST 3.039638, "
  "NLinear 3.211592). This legacy panel is a different scoring population from "
  "the 1120-cell national panel and must not be merged with CELL_METRICS.csv. "
  "Numerical foundation models (Chronos/TimesFM) remain BLOCKED (no weights, "
  "environment or pilot; named checkpoints are univariate). CDC official release "
  "calendar/revision id does not exist and peak re-scoring is BLOCKED, so peaks "
  "remain retrospective final-vintage. A PARTIAL resource subset reports real "
  "training wall times and NPZ scoring-path latency (explicitly not a model "
  "forward), with peak VRAM NOT_MEASURED. A dated JBHI verification confirms the "
  "14-page, 250-word, double-column, APC US$2,800 (2026) guidance but the "
  "template class file is UNVERIFIED; the manuscript is NOT submission-ready. "
  "We report all new results as separate panels, not as a replacement for the "
  "frozen historical snapshot.")
p("Keywords: influenza forecasting; multimodal LLM; MIFlu; peak skill; ablation; "
  "walk-forward; foundation models; scientific provenance; reproducible evaluation",
  size=9, italic=True)

h("1. Introduction", 1)
p("Influenza forecasting models are often compared across different windows, "
  "seeds and target definitions. A model that wins on mean squared error can lose "
  "on peak timing or peak height, and a checkpoint selected on one window set "
  "can reverse a ranking. This paper asks a narrow question: with one data split, "
  "one input length, one seed list and one scoring population, how do the 28 "
  "implementations used in this project compare on accuracy, peak skill and "
  "depth, and which legacy validations can now be considered complete?")
p("The contribution is evidence, not a new predictor. We (i) recover the missing "
  "seven-channel MIFlu predictions from existing checkpoints, (ii) score all "
  "1,120 cells on both an all-valid and a historical crop panel, (iii) recompute "
  "peak metrics from raw predictions with pre-specified detector parameters, "
  "(iv) align a 60-cell depth/LoRA ladder to a matched K=6 reference, (v) complete "
  "the legacy walk-forward recomputation from raw NPZ, and (vi) separate what is "
  "supported from what remains partial, blocked or explicitly superseded. v8 "
  "updates the manuscript body itself; the frozen historical snapshot is not "
  "overwritten.")

h("2. Data and protocol", 1)
p("The national series has 966 weekly rows and seven channels. The split is "
  "chronological 676/97/193 (train/validation/test), with boundaries 0/676/773/966. "
  "Input length is T=104 and horizons are L=24/36/48/60. Training uses strict "
  "containment: the whole target block of a window must lie inside its split. "
  "Seeds are 2021–2030. The 28 implementations are 13 conventional models, 4 "
  "LLM-based forecasters and 11 frozen language encoders with a shared linear "
  "read-out. The nominal matrix is 28 × 4 × 10 = 1,120 cells; deterministic fits "
  "are reported as effective replications rather than copied ten times. The "
  "legacy walk-forward panel is a DIFFERENT protocol (five folds, seeds 42/43/44, "
  "N=3) and is described in Section 4.4.")

h("3. Scoring panels and metrics", 1)
p("We use two panels with identical target populations. The all-valid panel keeps "
  "every valid test window (170/158/146/134 at L=24/36/48/60). The crop panel "
  "keeps the first (W//16)×16 windows (160/144/144/128), which is the historical "
  "complete-batch rule. MSE and MAE are seven-channel z-space means; peak metrics "
  "use ILITOTAL in patient units, reconstructed with the train-fit scaler.")
p("Peaks are detected with scipy.signal.find_peaks(prominence=0.15×range, "
  "distance=15) and matched one-to-one within ±8 weeks. A step passes when "
  "peak-time error (PTE) ≤ 1 week and peak-intensity error (PIE) ≤ 25%. "
  "Event-level outcomes distinguish matched, missed and false-alarm events; the "
  "pass fraction is not a probability and is not calibrated.")

h("4. Results", 1)
table(["Model", "MSE all-valid", "MSE crop", "MAE all-valid"],
      [["MIFlu", "1.7944", "1.4994", "0.8529"],
       ["PatchTST", "1.9521", "1.6352", "0.9244"],
       ["NLinear", "2.0782", "1.9027", "0.9652"],
       ["DNN", "2.2802", "2.1173", "1.0401"],
       ["TimeCMA", "2.6255", "2.5765", "1.0879"],
       ["GradientBoosting", "3.6547", "3.6645", "1.2636"],
       ["KNN", "3.7791", "3.7854", "1.3369"],
       ["RandomForest", "3.8817", "3.8888", "1.2872"],
       ["iTransformer", "4.0631", "4.0704", "1.3681"],
       ["DecisionTree", "4.2905", "4.2940", "1.3842"]],
      "Table 1. Leading mean errors on the two common panels (28 models; ten seeds; "
      "four horizons).")

p("The leading order is identical on both panels: MIFlu < PatchTST < NLinear. "
  "The crop panel reproduces the historical MIFlu mean of 1.4995 at 1.4994, "
  "which validates the seven-channel recovery; the all-valid panel raises every "
  "error but does not reorder the leaders. The full 28-model table is in the "
  "supplement.")
p("Peak skill does not follow the MSE order. Table 2 reports step-level passes. "
  "MIFlu has the largest number of passing cells; PatchTST has the lowest mean "
  "PTE but a slightly higher PIE. NLinear, the peak champion of the historical "
  "16-unit snapshot, passes only 3.4% of step cells on the new panel.")

table(["Model", "mean PTE (wk)", "mean PIE (%)", "passes / 1680"],
      [["PatchTST", "0.707", "34.41", "215 (12.8%)"],
       ["MIFlu", "0.964", "30.09", "252 (15.0%)"],
       ["NLinear", "2.013", "42.35", "57 (3.4%)"],
       ["DNN", "1.690", "51.54", "0"],
       ["TimeCMA", "1.588", "61.51", "0"],
       ["Qwen-Time", "4.632", "67.47", "1"]],
      "Table 2. Step-level Kramer–Shaman outcomes (ten seeds × 168 leads per model).")

p("Event-level matching separates detection from magnitude. iTransformer detects "
  "99.1% of ground-truth events but has PIE 71.2%; MIFlu detects 98.8% with PIE "
  "30.4%; PatchTST 97.6% with PIE 34.6%; NLinear 92.6% with PIE 40.6%. A model "
  "can find the peak week and still misstate its height.")
p("The depth ladder is non-monotonic. K4 has the lowest mean MSE (1.4989), "
  "followed by the matched K6 reference (1.5457, 10/12 cells), K2 (1.5813), "
  "K8 (1.6124), no-LoRA (1.6330) and K12 (1.7604). The historical claim of a "
  "monotonic depth trend is not supported.")

table(["Variant", "cells", "mean MSE"],
      [["K4", "12", "1.4989"], ["K6 reference", "10", "1.5457"],
       ["K2", "12", "1.5813"], ["K8", "12", "1.6124"],
       ["no-LoRA", "12", "1.6330"], ["K12", "12", "1.7604"]],
      "Table 3. Depth/LoRA ladder, seven-channel z-space MSE.")

h("4.4 The completed LEGACY walk-forward panel (v8, T1)", 2)
p("In v8 the legacy five-fold N=3 walk-forward recomputation is COMPLETE. Job "
  "743850 reran all 218 previously-SKIPPED legacy cells with rc=0; job 744334 "
  "recomputed from raw NPZ via v8/scripts/wf_recompute.py. "
  "HANDOFF_20261105/final/WF_RECOMPUTED.csv now has 1,020 of 1,020 rows with "
  "status ok (sha256 53d0e0cb36e726db46c29066101be316bbf9e0de7ea1a228bf84ba7f885ef80b) "
  "and WF_RECOMPUTED_MEANS.csv has sha256 "
  "c0e72f35f29d4df32762b9c0a03f69df576405ead495e91a43320dc0774d5813. The baseline "
  "diff is recovered_218_count=218, changed_existing_ok_values=0, "
  "lost_existing_ok=0, still_missing=0: no existing ok value was altered. The grid "
  "is five folds × 204 cells = 1,020, covering 17 models with n=60 cells each.")
table(["Model", "n", "full-panel mean MSE", "Model", "n", "full-panel mean MSE"],
      [["miflu", "60", "2.220289", "calf_llm", "60", "4.391592"],
       ["patchtst", "60", "3.039638", "svr", "60", "4.412095"],
       ["nlinear", "60", "3.211592", "decision_tree", "60", "4.514915"],
       ["dnn", "60", "3.648969", "cnn", "60", "4.515521"],
       ["gradient_boosting", "60", "3.915091", "lstm", "60", "4.655853"],
       ["timecma_llm", "60", "3.924265", "gru", "60", "4.742699"],
       ["random_forest", "60", "3.925170", "rnn", "60", "4.785940"],
       ["knn", "60", "3.967265", "qwen_time_llm", "60", "4.826157"],
       ["itransformer", "60", "3.977386", "", "", ""]],
      "Table 4. Legacy walk-forward full-panel per-model means (n=60 each), "
      "recomputed from the 1,020 raw cells. NOT the 1120-cell national panel.")
p("CRITICAL PROVENANCE. This is the LEGACY five-fold N=3 walk-forward panel "
  "(seeds 42/43/44), NOT the new 28-arm national 10-seed (2021–2030) panel. The "
  "20 out-of-grid wf_f*_miflu_*_s2021 rolling-origin rows remain out of scope. "
  "It is a different scoring population from CELL_METRICS.csv; do NOT merge or "
  "compare naively with the 1120 national panel. A walk-forward MSE of 2.220289 "
  "for MIFlu is not the same quantity as the national all-valid MSE of 1.7944. "
  "The earlier v7 claims of 802/1,020 valid rows and 218 missing NPZ are "
  "explicitly superseded by the 1,020/1,020 ok result above.")
p("External validity is otherwise partial. Regional Table VI yields 53 valid "
  "aggregate rows out of 53 (leads 2–20) after rerunning the two missing cells; "
  "these are ten-variable regional aggregates and are not comparable to the "
  "seven-channel national means. The old 'Table VI: 2 of 53 missing' claim is "
  "superseded by the 53/53 valid state.")

h("5. V8 — old snapshot vs new panels (separation of scoring populations)", 1)
p("CLEARLY-LABELLED V8 SEPARATION SECTION. Three distinct populations coexist "
  "in this project and must never be merged, averaged or compared naively. "
  "This section states the separation explicitly and lists every superseded "
  "old claim; no old claim is silently overwritten.", bold=True)
table(["Label", "Population / protocol", "Where", "v8 status"],
      [["OLD frozen snapshot", "28 arms; Holm 0/136 from p_raw with forward "
        "cumulative maximum; NLinear–PatchTST 0.1172; 4/16 aggregate cells; old "
        "NLinear K&S champion", "02_数字表格/*.csv (FROZEN)", "intact, labelled old"],
       ["NEW national panel", "28 models × 4 L × 10 seeds 2021–2030 = 1120 cells; "
        "seven-channel z-space; MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782",
        "final/CELL_METRICS.csv", "COMPLETE, separate"],
       ["LEGACY walk-forward", "5 folds × 204 cells = 1020; seeds 42/43/44; "
        "MIFlu 2.220289", "final/WF_RECOMPUTED.csv", "1020/1020 ok, separate"],
       ["LEGACY bench tree", "386 readable cells; final_llm_import",
        "HPC paper_tables/BENCH_MSE_BY_MODEL_L.csv", "real, legacy, separate"],
       ["PROXY CDC vintage", "20 Delphi issue rows; NOT_AVAILABLE official id",
        "v8/cdc_vintage/cdc_vintage.csv", "PARTIAL / BLOCKED"],
       ["SEPARATE foundation roster", "8 pinned candidates, 0 executed",
        "v8/foundation/FOUNDATION_ROSTER.csv", "BLOCKED, separate"]],
      "Table 5. V8 old-snapshot vs new-panels separation (RULE 4 provenance).")
p("Superseded claims now stated explicitly: (1) 'NLinear is the K&S peak "
  "champion (4/16)' — not reproduced on the new 1120 panel (MIFlu 252/1680, "
  "PatchTST 215/1680, NLinear 57/1680); the old 16-unit table is a different "
  "population. (2) 'monotonic depth trend' — superseded by the non-monotonic "
  "ladder (K4 best, K12 worst). (3) 'walk-forward partial / 802 of 1020 / 218 "
  "missing / 473 of 1020' — superseded by 1,020/1,020 ok on the LEGACY panel. "
  "(4) 'Table VI 2 of 53 missing / 51 of 53' — superseded by 53/53 valid. "
  "(5) 'final_llm_import TODO / no output' — superseded by a real rebuilt "
  "legacy table (386-cell quarantine caveat). (6) 'resource table NOT "
  "EXECUTED' — superseded by a PARTIAL measured subset. (7) 'JBHI "
  "UNVERIFIED' — superseded by a dated verification record, though the "
  "template class file remains UNVERIFIED. (8) 'v7 DOCX/PDF NOT EXECUTED' — "
  "superseded by the v7 and v8 documents. The frozen 02_数字表格 CSVs are "
  "kept byte-identical.", italic=True)

h("6. Numerical foundation models (v8, T2 — BLOCKED)", 1)
p("No numerical foundation model (Chronos/TimesFM) was run; T2 is BLOCKED with "
  "exact evidence. v8/foundation/FOUNDATION_ROSTER.csv and "
  "FOUNDATION_MODEL_PROVENANCE.md pin the exact repo ids, revisions and licences "
  "(Chronos amazon-science/chronos-forecasting v2.3.2 commit 0aba28e… "
  "Apache-2.0; TimesFM google-research/timesfm timesfm 3.0.2 / v3.0.0 commit "
  "331c6d33… Apache-2.0 source). Exact missing inputs: no full model weights "
  "(model.safetensors / TimesFM checkpoint), no tar + scp to "
  "/gpfs1/scratch/sychan552/models/, no isolated HPC env "
  "/home/sychan552/.venvs/mlflu_fm, no 1-cell pilot and no 80-cell matrix. "
  "All commands exited 0; the block is a documented missing-input condition, "
  "not a network error.")
p("Named Chronos T5/Bolt and TimesFM 1.0/2.0 checkpoints are UNIVARIATE; seven "
  "channels would require a documented per-channel adapter that DISCARDS "
  "cross-channel dependence, which is not a faithful multivariate control. "
  "TimesFM 3.0 self-hosted weights are non-commercial "
  "(timesfm-non-commercial-license-v1.0) and google/timesfm-2.0-500m (the bare "
  "id) returns HTTP 401. The 11 frozen language encoders are NOT substitutes. "
  "These candidates are kept on a SEPARATE roster and are NOT merged into the "
  "28-arm family. Smallest next action: download full pinned weights locally, "
  "tar + SHA-256 + scp, create the isolated env inside an sbatch job, run a "
  "1-cell A100 pilot, and only then the 80-cell matrix.")

h("7. CDC vintage and real-time claims (v8, T4 — PARTIAL / BLOCKED)", 1)
p("v8/cdc_vintage/cdc_vintage.csv contains 20 genuinely-fetched Delphi Epidata "
  "proxy rows with release_date, issue and affected weeks; every row has "
  "cdc_official_revision_id = NOT_AVAILABLE. CDC publishes no official release "
  "calendar and no revision/version identifier for ILINet (verified on the CDC "
  "past-reports, fluview index and stacks.cdc.gov pages); archived final CSVs "
  "are not a vintage. Peak re-scoring with as-of data is BLOCKED because the "
  "step → absolute row → CDC MMWR epiweek mapping is missing (frozen peak "
  "tables are step-indexed and the scoring scripts are not in the Windows "
  "tree). No mapping was invented and no peak CSV was rewritten. Peaks therefore "
  "remain RETROSPECTIVE final-vintage: this work makes NO real-time or clinical "
  "claim. Smallest next action: recover the test_window → absolute row → date "
  "alignment from the HPC return package and confirm the epiweek convention.")

h("8. Resource measurements (v8, T6 — PARTIAL)", 1)
p("v8/RESOURCE_MEASUREMENTS.csv reports a measured SUBSET only, with every row "
  "scope=subset_only_not_full_1120; no full-1120 Pareto is claimed. REAL training "
  "wall times from queue logs: MIFlu 581 s, NLinear 6 s, PatchTST 7 s, and one "
  "frozen encoder DeepSeek-R1-Distill-Qwen-1.5B 24 s. REAL NPZ scoring-path "
  "latency is 0.0287–0.0297 ms (warm-up 5 / repeat 50 on (170,7,24) float32); "
  "this is explicitly NOT a model forward pass. Software versions measured "
  "inside the sbatch job: Python 3.9.25, numpy 2.0.1, pandas 2.3.3, "
  "torch 2.5.1. peak_vram_mib = NOT_MEASURED for all rows: no GPU was allocated "
  "(tiny CPU job); the GPU job was cancelled (predicted start 2026-11-08) and "
  "stingy submissions were rejected with QOSMaxSubmitJobPerUserLimit. Chronos / "
  "TimesFM rows are BLOCKED / NOT_EXECUTED (T2 prerequisite). No VRAM or true "
  "forward latency was invented. Smallest next action: re-run t6_res_gpu.sbatch "
  "when an A100 is allocatable and QOS allows.")
table(["Subset model", "training wall (s)", "NPZ scoring-path latency (ms)", "peak VRAM"],
      [["MIFlu", "581", "0.029084", "NOT_MEASURED"],
       ["NLinear", "6", "0.029651", "NOT_MEASURED"],
       ["PatchTST", "7", "0.028653", "NOT_MEASURED"],
       ["DeepSeek-R1-Distill-Qwen-1.5B", "24", "0.028685", "NOT_MEASURED"],
       ["Chronos", "NOT_MEASURED", "NOT_MEASURED", "NOT_MEASURED (BLOCKED)"],
       ["TimesFM", "NOT_MEASURED", "NOT_MEASURED", "NOT_MEASURED (BLOCKED)"]],
      "Table 6. v8 resource subset (PARTIAL). Latency is the NPZ scoring path, "
      "NOT a model forward pass; scope = subset_only_not_full_1120.")

h("9. Statistical analysis", 1)
p("We report paired Wilcoxon signed-rank tests on the 40 (length, seed) cells "
  "for all 378 model pairs, with Holm adjustment. The exploratory analysis "
  "rejects 349 of 378 pairs (minimum adjusted p ≈ 6.9×10⁻¹⁰). A seed-cluster "
  "bootstrap (1,000 resamples over the ten seeds) gives 95% confidence "
  "intervals excluding zero for 359 of 378 pairs. These intervals address "
  "seed-level dependence but not the overlap between lengths and targets within "
  "a seed; they are not confirmatory inference. No claim of independence or "
  "equivalence is made from non-significance. A dependence-aware / blocked "
  "analysis remains pending.")

h("10. JBHI compliance verification (v8, T5 — dated record)", 1)
p("A dated verification record (v8/JBHI_VERIFICATION_20261106.md, 2026-11-06) "
  "VERIFIED from live HTTP 200 responses and verbatim quotes: page limit 14 "
  "regular / 16 review INCLUDING supplementary (original + revised), abstract "
  "≤ 250 words, IEEE single-spaced double-column with embedded figures/tables, "
  "IEEE-wide AI-use disclosure (acknowledgments; grammar/editing exception), "
  "hybrid open access, and APC US$2,800 for 2026 (IEEE Member 5% / Society "
  "Member 20% discounts, non-combinable). The official template class-file "
  "download is UNVERIFIED: the selector returns 404 with a browser UA, a WAF "
  "418 with the full python-requests default header profile, and the API path "
  "302 → 502. The 418 is a client-profile bot block, not a missing page. "
  "manuscript_submission_ready: NO. The manuscript is a draft; obtaining the "
  "template in a human browser session and pinning its SHA-256 remains open.")

h("11. Discussion and limitations", 1)
p("Three findings change the narrative. First, peak skill is not a rescaling of "
  "MSE: MIFlu and PatchTST lead peak passes while NLinear leads neither panel. "
  "Second, the depth ladder is not monotonic, so a deeper or LoRA-free model is "
  "not automatically better. Third, the historical peak conclusion was computed "
  "on a different scoring population; replacing it silently would be wrong, so "
  "Section 5 lists every superseded claim explicitly.")
p("Limitations are explicit. The series is one national ILI series; the four "
  "horizons reuse observations; ten seeds improve repeated-training precision "
  "but are not ten epidemics. The CDC release calendar and vintage are not "
  "reconstructed, so peak evaluation is retrospective. The 11 frozen encoders "
  "test only frozen features plus a linear read-out. Numerical foundation models "
  "are BLOCKED, not run. Resource measurements are a subset with no peak VRAM "
  "and no model-forward latency. The legacy walk-forward panel is complete but "
  "is a different population from the 1120 national panel. The JBHI template "
  "class file is UNVERIFIED. The T8 package validator PASS is structural only "
  "(scientific_readiness: NOT_ASSESSED). The manuscript is a draft, NOT a "
  "submission-ready article.")

h("12. Conclusion", 1)
p("On a complete 1,120-cell common panel, MIFlu has the lowest seven-channel "
  "MSE, PatchTST the best mean peak timing, and MIFlu the most step-level peak "
  "passes. The historical NLinear peak-champion claim is not reproduced. Depth "
  "is non-monotonic. In v8 the LEGACY five-fold walk-forward panel is complete "
  "at 1,020/1,020 ok, but it is a separate scoring population from the national "
  "panel and must not be merged with it. Foundation models, official CDC "
  "vintage/peak re-scoring, GPU peak VRAM and the JBHI template remain honestly "
  "BLOCKED / NOT_MEASURED / UNVERIFIED. All new results are offered as separate, "
  "explicitly labelled panels; the frozen historical snapshot remains intact.")

h("References", 1)
for ref in [
    "Moon, S. et al. MIFlu: multimodal influenza forecasting with LLM-based text and time-series fusion. IEEE J. Biomed. Health Inform., 2025.",
    "Nie, Y. et al. A time series is worth 64 words: long-term forecasting with transformers. ICLR, 2023.",
    "Zeng, A. et al. Are transformers effective for time series forecasting? AAAI, 2023.",
    "Kramer, A. M. and Shaman, J. Development and evaluation of influenza peaks. PLoS Comput. Biol., 2017.",
    "Ansari, A. F. et al. Chronos: learning the language of time series. TMLR, 2024.",
    "Das, A. et al. A decoder-only foundation model for time-series forecasting. ICML, 2024.",
]:
    p(ref, size=8)

p("Supplement. All 1,120 raw NPZ, harmonised cell metrics, peak-step and event "
  "tables, the 1,020-cell legacy walk-forward recomputation, the Delphi proxy "
  "vintage, the foundation roster and the resource subset logs are supplied in "
  "the v8 return package. Historical revision-9.2 numbers and frozen CSVs are "
  "NOT overwritten. See HANDOFF_20261105/v8/docs/V8_SCIENTIFIC_ADDENDUM.md.",
  size=8, italic=True)

src = OUT / "ieee_manuscript_en_v8.docx"
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
print("ieee_manuscript_en_v8", src.stat().st_size,
      pdf.stat().st_size if pdf.exists() else 0, r.returncode)
