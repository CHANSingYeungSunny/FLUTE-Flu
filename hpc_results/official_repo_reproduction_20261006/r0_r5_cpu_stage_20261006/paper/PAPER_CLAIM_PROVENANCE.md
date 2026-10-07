# PAPER_CLAIM_PROVENANCE.md

**Paper:** Moon, Shim, Kim, Hwang, *"MIFlu: Large Language Model-Based Multimodal Influenza
Forecasting Scheme"*, IEEE J. Biomed. Health Inform., vol. 29, no. 10, pp. 7790–7801, Oct. 2025.
**PDF SHA-256:** `7735a4388145dd2aced536417f7a4f50dafe21ed0d4fca64baa2b20f2e27885c` (12 pages).

Every important **numeric claim** in the main text, its source, and whether the number is
**author-generated** or **quoted from a cited paper**. Quotes are verbatim from the PDF text
layer; page numbers are the journal page numbers (5-digit) with the PDF page in brackets.

Legend for the *provenance* column:

- **AUTHOR** — produced by the MIFlu authors in this paper.
- **CITED** — taken from / about another paper or a third party (refs [1], [9], [14], [18], …).
- **SPEC** — a method/dataset specification statement, not a measured result.

---

## 1. Headline performance claims

### 1.1 "up to 26.2%" improvement over SOTA — AUTHOR
> "In extensive experiments using public national/regional influenza datasets, MIFlu outperforms
> other predictive models, improving prediction performance by up to 26.2% compared to
> state-of-the-art models." — *Abstract, p.7790 [PDF 1]*

Restated in the regional results (p.7798 [PDF 9]):
> "MIFlu improves on the forecasting accuracy of GPT4TS and achieves a relative performance gain
> compared to the SOTA model of up to 26.2%."

Source of the number: a relative gain computed from **Table VI** (regional RMSE), against the
**cited** GPT4TS column. The *derivation* is the authors'; the *anchor* is a cited baseline.

### 1.2 "up to 43.0%" gain over ReILIF — AUTHOR (anchor cited)
> "Before we applied GPT4TS in regional ILI forecasting, SOTA model for regional ILI forecasting
> was ReILIF and we achieves a relative gain compared to ReILIF of up to 43.0%." — *p.7798 [PDF 9]*

### 1.3 MIFlu wins everywhere except MSE at L=24 — AUTHOR
> "MIFlu outperforms the other models in all cases except for the MSE at L = 24." — *p.7797 [PDF 8]*

Direct reading of **Table V** (image-verified): at L=24 the best MSE is **PatchTST 1.319**, not
MIFlu (1.542). This claim is the key consistency check for any reproduction.

### 1.4 ReILIF RMSE 2431.7 / PCC 0.596 — **CITED**
> "the proposed MIFlu model achieves excellent forecasting accuracy, outperforming the SOTA model
> ReILIF, which has an RMSE of 2431.7 and a PCC of 0.596." — *p.7799 [PDF 10]*

This is the **Table VI L=20 ReILIF cell** — a value belonging to ref [14]. It must **not** be
treated as an author-generated result even though it is quoted in MIFlu's own prose.

### 1.5 Few-shot — **VISUAL ONLY**
> "Fig. 7(a) and (b) present the normalized forecasting results when using the first 50% (L = 48)
> and 10% (L = 24) time steps of training data, respectively." — *p.7799 [PDF 10]*

The paper states the analysis is done **"in a qualitative manner"**; no numeric few-shot result
is reported.

---

## 2. Training-cost claim

> "Considering the training time of ReILIF is 130 minutes, MIFlu took less time despite being a
> larger model." — *p.7799 [PDF 10]*

| Quantity | Value | Provenance |
|---|---|---|
| ReILIF regional training time | **130 min** | CITED (baseline, Table IX) |
| MIFlu regional training time | **119 min** | AUTHOR (Table IX) |

Hardware: "We implement the proposed model using Python 3.9.18 with PyTorch 2.1.0 and a
GeForce RTX 3090." — *p.7796 [PDF 7]*. Wall-clock is hardware-dependent, so only the
**relative** comparison (119 < 130) is meaningfully reproducible.

---

## 3. Claims about the cited baselines

> "LLaMA2-7B has 7 billion parameters compared to only 110 million for BERT, while LLaMA2-7B is
> pre-trained on about 600 times more dataset tokens." — *p.7798 [PDF 9]* — **CITED** (facts about
> the backbone models in Table VII's comparison).

> "The original small GPT2 model has 12 layers" — *p.7798 [PDF 9]* — **SPEC** (base-model fact
> that motivates the K sweep in Fig. 6; K is the number of layers taken from GPT2).

> "the World Health Organization (WHO) estimating that influenza causes 3 to 5 million severe
> symptomatic illnesses and 290,000 to 650,000 deaths every year [1]" — *p.7790 [PDF 1]* — **CITED**
> (explicitly attributed to ref [1]).

---

## 4. Dataset claims (DATASET_DESCRIPTION)

> "National-Illness [25]: This dataset includes seven variables for national ILIs that occurred in
> the United States (US) between 2002 and 2021 …" — *p.7795 [PDF 6]*
> "Following previous studies [9], [21], we split the data into training, validation, and test set
> at a ratio of 70:10:20."

> "US-Region [25]: … This dataset contains ILI in those 10 HHS regions from week 40, 1997, to
> week 18, 2020. Following [14] and our previous work [5], we divide the data into training,
> validation, and test set at a ratio of 50:10:40."

Both datasets come from ref [25] (CDC). The split ratios are **reused from prior work**, so the
"70:10:20" and "50:10:40" choices are not novel method contributions.

> "weekly patient counts would provide only about 520 data points after 10 years of data
> collection" — *p.7794 [PDF 5]* — **AUTHOR** motivating arithmetic (~52 weeks x 10 years).

---

## 5. Method / protocol specifications (SPEC)

> "Here, K is set at 6 for national ILI forecasting following [9], while K is set at 4 for regional
> ILI forecasting based on the results presented in Section VI-D. In these layers, we set low-rank
> dimension r to 4 following [36]." — *p.7796 [PDF 7]*

> "for national ILI forecasting, we set Lp and S to 24 and 2, respectively, according to [9], and
> for regional ILI forecasting, we set them to 4 and 2 based on the ratio of T and Lp and S in
> national ILI prediction." — *p.7796 [PDF 7]*

> "We assess the forecasting performance by calculating the mean of 10 repetitions of the
> forecasting results." — *p.7796 [PDF 7]*

> "We set the number of training epochs and the learning rate for MIFlu empirically because the
> hyperparameters vary depending on the base model." — *p.7796 [PDF 7]*

These are the reimplementation-critical numbers: national **K=6, Lp=24, S=2, r=4, epochs 20,
batch 16, lr 0.0005, T=104**; regional **K=4, Lp=4, S=2, r=4, epochs 50, batch 32, lr 0.0005, T=20**
(the epoch/batch/lr/T values are read from Table IV, image-verified).

---

## 6. Where the baselines come from — the pivotal provenance sentence

> "The results for the national and regional ILI forecasting models are taken from [9] and [14],
> respectively." — *p.7796 [PDF 7]*

This single sentence governs the whole result table set:

| Table | Author-generated portion | Cited-baseline portion |
|---|---|---|
| **V** (national MSE/MAE) | the **MIFlu** column only (8 cells) | the other **11 columns** (88 cells) from refs [9] |
| **VI** (regional RMSE/PCC) | the **MIFlu** column only (7 cells) | the other **7 columns** (49 cells) from refs [14] |
| **VII** (embedder comparison) | all rows — the `X (GPT4TS)` control is the authors' own run | none (but `X` numerically equals Table V's cited GPT4TS column) |
| **VIII** (ablation) | all 14 cells | none |
| **IX** (training time) | the MIFlu row | the ReILIF row |

---

## 7. Claims that could NOT be verified

| Claim / item | Status | Reason |
|---|---|---|
| Table II descriptive statistics | **UNREADABLE** | PDF page 5 (journal p7794) was never rendered; values are images absent from the text layer. |
| Table III descriptive statistics | **UNREADABLE** | Same page/blocker as Table II. |
| Fig. 5 and Fig. 6 numeric values | **VISUAL ONLY** | Only plotted; no table. Prose gives only the qualitative direction ("T = 40" best; "K = 4" best). |
| Fig. 4 and Fig. 7 numeric values | **VISUAL ONLY** | No tabulated counterpart; would need the model's test predictions. |
| Any page 12 content | Not inspectable | No render exists for PDF page 12 (journal p7801); the PDF text layer for that page contains **references only** ([7]–[37]), with no table or figure caption. |