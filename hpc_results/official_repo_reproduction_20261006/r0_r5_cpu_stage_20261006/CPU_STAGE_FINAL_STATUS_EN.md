# CPU STAGE — FINAL STATUS (English)

Generated 2026-10-06. **CPU/lightweight stage only. No GPU job was submitted.**

Output directory: `hpc_results/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/`
(45 files, all hashed in `CPU_STAGE_FILE_MANIFEST.csv`).

---

## 1. Paper identity and three-source cross-check

| Source | SHA-256 | Role |
|---|---|---|
| PDF | `7735a4388145dd2aced536417f7a4f50dafe21ed0d4fca64baa2b20f2e27885c` | source of record, 12 pages |
| **Markdown (new)** | `6488a76b564d0b587ec01902848371d054b00bf2b941e289b2cd5d2483e39edd` | primary structured source: 466 lines, 27 headings, **all 10 tables** |
| old `MIFlu_paper.md` | — | superseded (omits Table IV and every table value) |

### Structural finding

**Every table value in the PDF is an image.** `find_tables()` returns **0 tables on all 12
pages**, and `1.542`, `1.422`, `1.414`, `1.364`, `1.4355`, `0.74525`, `0.726` each occur
**0 times** in the text layer. All cell values must therefore be read from renders.

| Item | PDF image | new Markdown | old transcription | Verdict |
|---|---|---|---|---|
| Table V (8 MIFlu cells) | ✅ | ✅ | ✅ | **`MARKDOWN_PDF_CROSS_VERIFIED`** |
| Table VIII (14 ablation cells) | ✅ | ✅ | ✅ | cross-verified |
| **Table IV hyperparameters** | ✅ **only source** | ❌ disclaimed | ❌ absent | **`PDF_VISUALLY_VERIFIED`** |
| Tables II / III | ❌ never rendered | ❌ disclaimed | ❌ absent | **`UNREADABLE`** |

### ⚠️ Table IV corrects an earlier wrong conclusion

PDF page 7's Table IV (national block) gives **Epochs 20 · Batch 16 · Learning rate 0.0005 ·
T 104**. Earlier rounds concluded the paper discloses neither epochs nor learning rate and
dismissed the project's 20 / 5e-4 as a sourceless reconstruction. **That was wrong**: the
source is Table IV. Neither Markdown carries these values — the new one explicitly says the
table was not extractable.

**Corrected**: epochs, batch, lr and T are **`PAPER_EXPLICIT` via Table IV**. Still
genuinely `UNRECOVERED`: **optimizer, scheduler, seed list, checkpoint rule, pooling axes**.

---

## 2. Paper numbering

**Table II, IV, V, VI, VII, VIII, IX, X and Figures 3, 5, 6, 7 all exist as expected.** Two
additional items the brief did not list: **Table I** (prompt template) and **Table III**
(US-Region statistics). Figures are cited as `Fig. N`; the literal word "Figure" occurs
0 times. National split is **70:10:20** (matches the code); **US-Region is 50:10:40**.

**CORRECTED 2026-10-07**: Tables II and III are fully available as markdown transcriptions. Table II re-verified 7/7 against the 966-row file (max deviation 0.03%).

---

## 3. Inventory

**10 tables · 7 figures · 301 cells inventoried · 299 `IMAGE_MANUALLY_VERIFIED` · 2 `UNREADABLE`.**

**Table V has exactly one author-generated column — MIFlu's (8 cells). The other 11 columns
(88 cells) are `CITED_BASELINE_RESULT`**, because the paper states its results are taken
from refs [9] and [14]. Reproducing quoted baselines is `NOT_APPLICABLE`.

---

## 4. R1-B implementation

**The trainer now exists**: `r1b/r1b_model.py` (subclasses the author's GPT4TS) and
`r1b/r1b_train.py`. **The author's source tree is unmodified** — `git diff --stat` shows one
regenerated `.pyc`, 0 insertions, 0 deletions.

| Correction | Class | Measured effect |
|---|---|---|
| B-1 seven-channel windows | paper-required | output → **(B, L, 7)** |
| **B-2 functional text pathway** | **repairs a released defect** | `max\|Δ\|` **0.0 → 5.88e-02**; `\|grad_text\|` **0 → 1.04e-03**; **`text_inert` → `text_active`** |
| B-3 `PEFT=1` | paper-required | **pending HPC** (no local peft); `--target_modules` must NOT be passed |
| **B-4 effective freeze** | **repairs a released defect** | trainable **100 % → 1.93 %** (1,599,768 / 82,705,944) |
| B-5 validation-only selection | clean evaluation | Test unread during the fit |
| B-6 persisted predictions | clean evaluation | NPZ schema matches the audited scorer |
| B-7 declared configuration | **`PAPER_EXPLICIT` (Table IV)** | 20 epochs / 5e-4 / batch 16 |

**Acceptance: 27 PASS / 3 NOT_YET_RUN / 0 FAIL.** The three are the two LoRA checks (need
`peft`) and a checkpoint reload.

# R1-B verdict: `NOT_READY_CONTRACT_UNRESOLVED`

**Not an engineering failure.** The blockers are three unresolved contract items — pooling
axes (permanently unrecoverable), checkpoint rule, and optimizer/scheduler. Next action
needs **no GPU**: a CPU-only HPC job to close T19/T20/T29, then re-issue.

---

## 5. Historical 4-vs-4

**Exact model strings (confirmed, not assumed)**: LLM = `gpt2_miflu`, `qwen_time_llm`,
`calf_llm`, `timecma_llm`; non-LLM = `nlinear`, `dlinear`, `patchtst`, `itransformer`.

**Historical MIFlu** = `scripts/miflu_model.py::MIFlu`, wrapped by
`gpt2_miflu_adapter.py` as `gpt2_miflu` — the **project's own from-scratch
re-implementation**, not the author's code.

**Five stages** (kept separate): A `early_ili_july2026` · B `innovation_v2_screening` ·
**C `wave1_validation_v3clean`** (the 4-vs-4 validation ranking) ·
**D `final_test_holdout_v3clean`** (one-time Test) · E `a2_author966_stage5/stage6` (post-clone).

**A verification reversal**: `gpt2_miflu` **won** Wave-1 validation (0.771) but **lost** the
one-time Test (3.0505 vs nlinear 2.7389). Both stages must be evaluated.

---

## 6. Replacement compatibility

# `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED`

The historical contract is **1025 rows / 717-102-206**; R1-B is **966 rows / 676-97-193**.
The data contracts are incompatible, so **an author-data MIFlu metric must never be inserted
into the 1025-row ranking**.

| # | Question | Answer |
|---|---|---|
| 1 | which entry is replaced? | **`gpt2_miflu`** |
| 2 | can the author-data result be inserted directly? | **NO** |
| 3 | can official predictions be scored on historical keys? | **NO**, not as-is |
| 4 | can the seven others stay unchanged? | **YES** |
| 5 | do they need re-scoring? | no — only re-aggregated under one scorer |
| 6 | do any need retraining? | **NO** |
| 7 | must MIFlu be retrained on the 1025-row contract? | **YES** |
| 8 | is it still interpretable as a controlled intervention? | **YES**, if only MIFlu changes |

The replacement run must be labelled **"official-repository-based MIFlu transferred to the
historical comparison contract"** — **never** "the paper reproduction".

---

## 7. Seasonal-naive leakage

**Two implementations exist; only one leaks.**

| | safe | leaky |
|---|---|---|
| file | `results/v3_clean/.../clean_metrics.py` | `scripts/train_naive_966.py` |
| formula | `src=(T-1)+(k+1)-52`, clamped | `ref = ts + s - 52`, unclamped |
| reads the future at L=60? | **no** | **yes — 8 leads, rows `ts+0..ts+7`** |

| Track | Affected? |
|---|---|
| **C/D — the historical 4-vs-4** | **NO** (safe formula) |
| **E — author-966 A2/stage-5/6** | **YES, at L=60 only** |
| F1 | already corrected |

Value change on the affected track: L=60 **2.1035 → 1.9174**, four-horizon mean
**2.26880 → 2.22229**. **No rank change** (still 5th), but any quoted L=60 value or mean
must be updated.

> **The controlled MIFlu replacement does not inherit this defect.**

---

## 8. GPU authorizations required (none granted)

core R1-B pilot · 10-repetition expansion · paper-wide Tier-2 · historical replacement
experiment. **The F1 0.35 GPU-h remainder and the older 0.05639 remainder are sealed and
were not used.**

---

## 9. Confirmations

- **No GPU job submitted** — highest job owned is still **607691**; queue empty
- **F2 not started**, and cancelled
- **F1 frozen** — 29/29 artefacts byte-identical
- **Nothing deleted or modified** — 66/66 deliverables + 5 trees + author source verified
- **Original Chinese DOCX report untouched**

**Not done, and not presented as done**: Tables II/III values (need a render of PDF page 5);
the 3 HPC-only R1-B gates; Tier-2/Tier-3 paper experiments; the historical replacement run;
the new DOCX (its preconditions are unmet).