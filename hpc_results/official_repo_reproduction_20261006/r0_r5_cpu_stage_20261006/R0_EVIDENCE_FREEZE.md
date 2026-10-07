# R0 — EVIDENCE FREEZE

Generated 2026-10-06. **Read-only with respect to every existing artifact.** This document
freezes the identities that all later stages depend on.

---

## 1. The paper (primary target source)

| Item | Value |
|---|---|
| path | `reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.pdf` |
| **SHA-256** | **`7735a4388145dd2aced536417f7a4f50dafe21ed0d4fca64baa2b20f2e27885c`** |
| size | 2,956,545 bytes |
| pages | **12** |
| text layer | present on all 12 pages; 55,606 characters extracted |
| journal | IEEE J. Biomed. Health Inform., Vol. 29, No. 10, October 2025 |
| download stamp | "Authorized licensed use limited to: CITY UNIV OF HONG KONG. Downloaded on June 29,2026 at 12:56:06 UTC from IEEE Xplore" |

### 1.1 The structural finding that changes how the paper must be read

**All table cell values are images, not text.**

| Probe | Result |
|---|---|
| `fitz` `page.find_tables()` | **0 tables detected on every one of the 12 pages** |
| occurrences of `1.542` in the text layer | **0** |
| occurrences of `1.422`, `1.414`, `1.364` | **0 each** |
| occurrences of `1.4355`, `0.74525`, `0.726` | **0 each** |
| pages containing images | 7 (pages 1, 4, 6, 8, 9, 10, 11) |
| table/figure **captions and cross-references** | **present** in the text layer |
| figure reference style | `Fig. N` (14 occurrences); the literal word "Figure" appears **0** times |

**Consequence**: the paper's table **structure and captions** can be read from text, but
every **numeric cell** must be read from a rendered page image. Pages 3, 4, 6, 7, 8, 9, 10
and 11 have been rendered at 200 dpi into `paper/page_NN.png` for that purpose.

### 1.2 Alternate copies in the project, and why they are not substitutes

| Copy | Relation | Defect |
|---|---|---|
| `MIFlu_paper.md` | a **project transcription**, not byte-identical | **it omits Table IV's numeric rows entirely** — see §5 |
| `audit_20260930/paper_text.txt` | a text-layer extraction from an earlier round | contains no table values, for the same structural reason |

**Neither alternate copy may be treated as the primary source.** The brief's instruction
"do not rely solely on previous manual transcriptions" is directly vindicated by §5.

---

## 2. The official repository

| Item | Value |
|---|---|
| local path | `recovery/author_repo/` |
| remote | `https://github.com/Jmoon3108/MIFlu.git` ✅ the author's own |
| commit | `6ed210150b8819313947cf607eb1821c87b1bee3` (2025-03-21) |
| clone timestamp | **2026-09-24T09:54:29+08:00** — the lineage boundary |
| HPC checkout | `/scratch/sychan552/a0_replay`, same commit |
| tree contents | `main_ILI_lora.py`, `models/`, `data_provider/`, `utils/`, `dataset/`, `text_emb.ipynb`, `.vscode/` |
| **absent** | no README, no LICENSE, no requirements file, no config file, **no `embed.py`** (only a stale `.pyc`) |

---

## 3. Datasets

| Path | Rows | SHA-256 | Role |
|---|---:|---|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | 966 | `2a96dfed…ebfe5` | the file the released code loads by default |
| `recovery/author_repo/dataset/illness/national_illness_orig.csv` | 966 | `8594cecb…e395` | the author's other copy |
| `data/raw/national_illness_raw_paper_exact.csv` | 966 | `31ffc169…b87a` | the A2/F1 analysis file (CDC column names) |
| `data/raw/national_illness_raw.csv` | 1025 | (July snapshot) | **Historical Track B only — never mixed** |

---

## 4. The historical project

| Item | Value |
|---|---|
| root | `C:\Users\Asus\Desktop\FYP code\MLFlu` |
| git HEAD | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51`, branch `recovery-stage4`, **single commit** |
| git status | 179 `??` / 49 `M` / 9 `D` |
| historical comparison | `results/v3_clean/` (2026-09-21), `results/innovation/` (2026-09-19) |
| deployment family | `innovation_deploy_root_v3_*` — 19 directories on HPC, `UNSAFE_TO_DELETE`, latest mtime 2026-09-21 |
| **all predate** | the 2026-09-24 clone → **filesystem-proven Track B** |

Detail is in the R5 deliverables.

---

## 5. ⚠️ CORRECTION: Table IV gives the training hyperparameters — an earlier conclusion was wrong

**This is the most consequential finding of this round.**

Reading **page 7 as an image** (Table IV, "A List of Comparative Models and Hyperparameters
Used") yields a settings block that is **absent from the project's markdown transcription**:

| Setting | **National ILI** | Regional ILI |
|---|---|---|
| L | **24, 36, 48, 60** | 2, 3, 5, 10, 13, 15, 20 |
| **Epochs** | **20** | 50 |
| **Batch size** | **16** | 32 |
| **Learning rate** | **0.0005** | 0.0005 |
| T | **104** | 20 |

Source: `paper/page_07.png`, Table IV bottom block. Extraction label
`IMAGE_MANUALLY_VERIFIED`.

### What this overturns

Earlier rounds concluded — and wrote into `HYPERPARAMETER_PROVENANCE.md`,
`HYPERPARAMETER_PROVENANCE_V2.md` and `STATUS_CORRECTION_ADDENDUM.md` — that:

1. "the paper discloses **no** epochs or learning rate" — **wrong**;
2. "20 epochs / lr 5e-4 **has no source** and is a `RECONSTRUCTED_ASSUMPTION`" — **wrong**;
3. the recovery plan's line `"Paper: 20 epochs, batch size 16, learning rate 0.0005"`
   was a **mislabel** — **it was correct**.

### Why the error happened

The reasoning ran: the prose says *"We set the number of training epochs and the learning
rate for MIFlu empirically because the hyperparameters vary depending on the base model"*
(page 7, bottom-left), therefore no values are given. **The prose is about MIFlu
specifically; Table IV's settings block gives the values used.** The markdown transcription
omitted Table IV's numeric rows, so the values were invisible to a reader working from the
transcription alone.

### Corrected classification

| Setting | Correct classification |
|---|---|
| epochs (national) | **`PAPER_EXPLICIT` via Table IV = 20** |
| batch size (national) | **`PAPER_EXPLICIT` via Table IV = 16** |
| learning rate (national) | **`PAPER_EXPLICIT` via Table IV = 0.0005`** |
| T | **`PAPER_EXPLICIT` via Table IV = 104** |

**The project's A2/F1 choice of 20 epochs / 5e-4 / batch 16 was therefore paper-supported
all along.** It is not a `RECONSTRUCTED_ASSUMPTION`.

### What is still genuinely undisclosed

| Item | Status |
|---|---|
| optimizer | **not stated anywhere** (Table IV gives no optimizer) — `UNRECOVERED` |
| scheduler | **not stated** — `UNRECOVERED` |
| seed list | **not stated** — `UNRECOVERED` |
| checkpoint-selection rule | **not stated** — `UNRECOVERED` |
| pooling axes (Q12) | **not stated** — `UNRECOVERED` |
| whether Table V's MIFlu column is quoted | **not stated** — `UNRECOVERED` |

So the corrected picture is: **fewer reconstructed assumptions than previously believed, but
the same core blockers remain.**

**No earlier file has been modified.** This correction is recorded here and must be carried
into `R1_HYPERPARAMETER_EVIDENCE.csv` and the paper-wide reports.

---

## 6. Freeze manifest

A SHA-256 manifest of every frozen artifact is in `R0_EVIDENCE_HASH_MANIFEST.csv`.
Nothing in §1–§4 was moved, renamed, compressed, truncated or overwritten.