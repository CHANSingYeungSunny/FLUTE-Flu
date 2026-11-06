# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

OUT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v7")
OUT.mkdir(parents=True, exist_ok=True)
doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Inches(0.8)
    s.left_margin = s.right_margin = Inches(0.9)

style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(10)

def h(text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13 if level == 1 else 11)
    return p

def p(text, bold=False, italic=False, size=10, align=None):
    par = doc.add_paragraph()
    r = par.add_run(text)
    r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    if align: par.alignment = align
    return par

def table(headers, rows, caption, widths=None):
    p(caption, bold=True, size=9)
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    for i, x in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = str(x)
        for r in c.paragraphs[0].runs: r.bold = True; r.font.size = Pt(8)
    for row in rows:
        cells = t.add_row().cells
        for i, x in enumerate(row): cells[i].text = str(x)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows: row.cells[i].width = Inches(w)
    doc.add_paragraph()

p("A common ten-seed re-evaluation of influenza forecasting: MIFlu, twenty-seven comparators, peak skill and depth ablation", bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
p("CHAN Sing Yeung", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
p("Department of Electrical Engineering, City University of Hong Kong", size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
p("Draft v7 — 6 November 2026. Not submission-ready; historical revision-9.2 numbers remain a separate snapshot.", italic=True, size=8, align=WD_ALIGN_PARAGRAPH.CENTER)

h("Abstract", 1)
p("We re-evaluate national influenza-like-illness forecasting on a 966-week CDC series with a single common protocol: input length 104 weeks, four forecast horizons (24/36/48/60), ten seeds (2021–2030), and 28 model implementations. The 1,120-cell matrix is complete. Because the original MIFlu export carried only ILITOTAL, we recover all seven channels from the trained checkpoints and score every model on two identical target populations: all valid windows and the historical complete-batch crop. On the all-valid panel the leading mean squared errors are MIFlu 1.7944, PatchTST 1.9521 and NLinear 2.0782; the crop panel gives 1.4994, 1.6352 and 1.9027, reproducing the historical MIFlu mean. Peak skill changes the ranking: MIFlu passes 252 of 1,680 step-level Kramer–Shaman cells (15.0%), PatchTST 215 (12.8%) and NLinear 57 (3.4%). Event-level detection is high for several models but height errors differ sharply. A 60-cell depth/LoRA ladder is non-monotonic: K4 is best (1.4989) and K12 worst (1.7604). Regional Table VI is complete at 53 of 53 cells; walk-forward is valid for 802 of 1,020 rows after direct seven-channel recomputation from raw NPZ, with 218 rows lacking NPZ. We report these as a new panel, not as a replacement for the frozen historical snapshot.")
p("Keywords: influenza forecasting; multimodal LLM; MIFlu; peak skill; ablation; reproducible evaluation", size=9, italic=True)

h("1. Introduction", 1)
p("Influenza forecasting models are often compared across different windows, seeds and target definitions. A model that wins on mean squared error can lose on peak timing or peak height, and a checkpoint selected on one window set can reverse a ranking. This paper asks a narrow question: with one data split, one input length, one seed list and one scoring population, how do the 28 implementations used in this project compare on accuracy, peak skill and depth?")
p("The contribution is evidence, not a new predictor. We (i) recover the missing seven-channel MIFlu predictions from existing checkpoints, (ii) score all 1,120 cells on both an all-valid and a historical crop panel, (iii) recompute peak metrics from raw predictions with pre-specified detector parameters, (iv) align a 60-cell depth/LoRA ladder to a matched K=6 reference, and (v) separate what is supported from what remains partial or blocked.")

h("2. Data and protocol", 1)
p("The national series has 966 weekly rows and seven channels. The split is chronological 676/97/193 (train/validation/test), with boundaries 0/676/773/966. Input length is T=104 and horizons are L=24/36/48/60. Training uses strict containment: the whole target block of a window must lie inside its split. Seeds are 2021–2030. The 28 implementations are 13 conventional models, 4 LLM-based forecasters and 11 frozen language encoders with a shared linear read-out. The nominal matrix is 28 × 4 × 10 = 1,120 cells; deterministic fits are reported as effective replications rather than copied ten times.")

h("3. Scoring panels and metrics", 1)
p("We use two panels with identical target populations. The all-valid panel keeps every valid test window (170/158/146/134 at L=24/36/48/60). The crop panel keeps the first (W//16)×16 windows (160/144/144/128), which is the historical complete-batch rule. MSE and MAE are seven-channel z-space means; peak metrics use ILITOTAL in patient units, reconstructed with the train-fit scaler.")
p("Peaks are detected with scipy.signal.find_peaks(prominence=0.15×range, distance=15) and matched one-to-one within ±8 weeks. A step passes when peak-time error (PTE) ≤ 1 week and peak-intensity error (PIE) ≤ 25%. Event-level outcomes distinguish matched, missed and false-alarm events; the pass fraction is not a probability and is not calibrated.")

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
      "Table 1. Leading mean errors on the two common panels (28 models; ten seeds; four horizons).")

p("The leading order is identical on both panels: MIFlu < PatchTST < NLinear. The crop panel reproduces the historical MIFlu mean of 1.4995 at 1.4994, which validates the seven-channel recovery; the all-valid panel raises every error but does not reorder the leaders. The full 28-model table is in the supplement.")
p("Peak skill does not follow the MSE order. Table 2 reports step-level passes. MIFlu has the largest number of passing cells; PatchTST has the lowest mean PTE but a slightly higher PIE. NLinear, the peak champion of the historical 16-unit snapshot, passes only 3.4% of step cells on the new panel.")

table(["Model", "mean PTE (wk)", "mean PIE (%)", "passes / 1680"],
      [["PatchTST", "0.707", "34.41", "215 (12.8%)"],
       ["MIFlu", "0.964", "30.09", "252 (15.0%)"],
       ["NLinear", "2.013", "42.35", "57 (3.4%)"],
       ["DNN", "1.690", "51.54", "0"],
       ["TimeCMA", "1.588", "61.51", "0"],
       ["Qwen-Time", "4.632", "67.47", "1"]],
      "Table 2. Step-level Kramer–Shaman outcomes (ten seeds × 168 leads per model).")

p("Event-level matching separates detection from magnitude. iTransformer detects 99.1% of ground-truth events but has PIE 71.2%; MIFlu detects 98.8% with PIE 30.4%; PatchTST 97.6% with PIE 34.6%; NLinear 92.6% with PIE 40.6%. A model can find the peak week and still misstate its height.")
p("The depth ladder is non-monotonic. K4 has the lowest mean MSE (1.4989), followed by the matched K6 reference (1.5457, 10/12 cells), K2 (1.5813), K8 (1.6124), no-LoRA (1.6330) and K12 (1.7604). The historical claim of a monotonic depth trend is not supported.")

table(["Variant", "cells", "mean MSE"],
      [["K4", "12", "1.4989"], ["K6 reference", "10", "1.5457"],
       ["K2", "12", "1.5813"], ["K8", "12", "1.6124"],
       ["no-LoRA", "12", "1.6330"], ["K12", "12", "1.7604"]],
      "Table 3. Depth/LoRA ladder, seven-channel z-space MSE.")

p("External validity is partial. Regional Table VI yields 53 valid aggregate rows out of 53 (leads 2–20) after rerunning the two missing cells, but these are ten-variable regional aggregates and are not comparable to the seven-channel national means. Walk-forward yields 802 valid rows out of 1,020 directories after direct recomputation from raw NPZ; 218 rows have no NPZ. We therefore do not claim complete rolling-origin validation.")

h("5. Statistical analysis", 1)
p("We report paired Wilcoxon signed-rank tests on the 40 (length, seed) cells for all 378 model pairs, with Holm adjustment. The exploratory analysis rejects 349 of 378 pairs (minimum adjusted p ≈ 6.9×10⁻¹⁰). A seed-cluster bootstrap (1,000 resamples over the ten seeds) gives 95% confidence intervals excluding zero for 359 of 378 pairs. These intervals address seed-level dependence but not the overlap between lengths and targets within a seed; they are not confirmatory inference. No claim of independence or equivalence is made from non-significance.")

h("6. Discussion and limitations", 1)
p("Three findings change the narrative. First, peak skill is not a rescaling of MSE: MIFlu and PatchTST lead peak passes while NLinear leads neither panel. Second, the depth ladder is not monotonic, so a deeper or LoRA-free model is not automatically better. Third, the historical peak conclusion was computed on a different scoring population; replacing it silently would be wrong.")
p("Limitations are explicit. The series is one national ILI series; the four horizons reuse observations; ten seeds improve repeated-training precision but are not ten epidemics. The CDC release calendar and vintage are not reconstructed, so peak evaluation is retrospective. The 11 frozen encoders test only frozen features plus a linear read-out. Regional and walk-forward results are partial. No numerical foundation model (Chronos/TimesFM) was run. Resource measurements are not reported. The manuscript is a draft, not a submission-ready article.")

h("7. Conclusion", 1)
p("On a complete 1,120-cell common panel, MIFlu has the lowest seven-channel MSE, PatchTST the best mean peak timing, and MIFlu the most step-level peak passes. The historical NLinear peak-champion claim is not reproduced. Depth is non-monotonic. These results are offered as a new, separately labelled panel; the frozen historical snapshot remains intact.")

h("References", 1)
for ref in [
    "Moon, S. et al. MIFlu: multimodal influenza forecasting with LLM-based text and time-series fusion. IEEE J. Biomed. Health Inform., 2025.",
    "Nie, Y. et al. A time series is worth 64 words: long-term forecasting with transformers. ICLR, 2023.",
    "Zeng, A. et al. Are transformers effective for time series forecasting? AAAI, 2023.",
    "Kramer, A. M. and Shaman, J. Development and evaluation of influenza peaks. PLoS Comput. Biol., 2017.",
]:
    p(ref, size=8)

p("Supplement. All 1,120 raw NPZ, harmonised cell metrics, peak-step and event tables, ablation and legacy validation CSVs are supplied in the v7 return package. Historical revision-9.2 numbers are not overwritten.", size=8, italic=True)

src = OUT / "V7_MANUSCRIPT_EN.docx"; doc.save(src)
NODE = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
pdf = src.with_suffix(".pdf")
if pdf.exists(): pdf.unlink()
r = subprocess.run([NODE, CLI, "convert", "--input", str(src), "--output", str(pdf)],
                   capture_output=True, text=True, errors="replace")
print(src.stat().st_size, pdf.stat().st_size if pdf.exists() else 0, r.returncode)
