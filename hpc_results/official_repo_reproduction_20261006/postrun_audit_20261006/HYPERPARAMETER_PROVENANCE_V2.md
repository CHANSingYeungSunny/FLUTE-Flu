# HYPERPARAMETER PROVENANCE — V2

Generated 2026-10-06. Append-only. Supersedes nothing; it refines
`../HYPERPARAMETER_PROVENANCE.md` and applies the classification legend required by the
continuation brief.

Legend: `PAPER_EXPLICIT` · `CODE_EXPLICIT` · `README_EXPLICIT` · `CONFIG_EXPLICIT` ·
`LOG_INFERRED` · `USER_CONFIRMED` · `RECONSTRUCTED_ASSUMPTION` · `CONFLICTING_EVIDENCE` ·
`UNRECOVERED`

> **Note on `README_EXPLICIT`**: the author's released tree contains **no README, no
> LICENSE, no requirements file and no config file** (`recovery/author_repo/` holds only
> `main_ILI_lora.py`, `models/`, `data_provider/`, `utils/`, `dataset/`,
> `text_emb.ipynb`, `.vscode/`). `README_EXPLICIT` therefore **cannot** be a source for
> the author contract and is not used below.

---

## 1. Master table

| Parameter | Paper | Released code default | Project A1 run used | Classification | Direct source |
|---|---|---|---|---|---|
| epochs | **not disclosed** | `1` | `20` | `UNRECOVERED` (paper) / `CONFIG_EXPLICIT` (default) / `RECONSTRUCTED_ASSUMPTION` (used) | paper-md L298; `main_ILI_lora.py` L58 |
| learning rate | **not disclosed** | `1e-4` | `5e-4` | `UNRECOVERED` / `CONFIG_EXPLICIT` / `RECONSTRUCTED_ASSUMPTION` | paper-md L298; `main_ILI_lora.py` L55 |
| optimizer | **not disclosed** | Adam | Adam | `UNRECOVERED` / `CODE_EXPLICIT` | `main_ILI_lora.py` |
| scheduler | **not disclosed** | `lradj=type1`, `cos=0` → `adjust_learning_rate` **is** called | same | `UNRECOVERED` (paper) / `LOG_INFERRED` (behaviour) | `main_ILI_lora.py` L230-234 |
| decay factor | **not disclosed** | `type1` uses a **hard-coded 0.9 from epoch 4**; `--decay_fac 0.75` is **inert** on that path | same | `CODE_EXPLICIT` | `utils/tools.py` L26-27 |
| batch size | **not disclosed** | `16` | `16` | `UNRECOVERED` / `CONFIG_EXPLICIT` | `main_ILI_lora.py` L56 |
| dropout | **not disclosed** | `0.2` | `0.2` | `UNRECOVERED` / `CONFIG_EXPLICIT` | `main_ILI_lora.py` L69 |
| early stopping | **not mentioned** | instantiated, **call commented out** | same (inert) | `CODE_EXPLICIT` | `main_ILI_lora.py` L235-236 |
| repetitions | **10, arithmetic mean** | `itr=1` | `itr=1` | `PAPER_EXPLICIT` (rule) / `CONFIG_EXPLICIT` (default) | paper-md L306; `main_ILI_lora.py` L255-258 |
| seeds | **not disclosed** | `fix_seed=2021`, set **once**, never reseeded in the loop | same | `UNRECOVERED` (paper) / `CODE_EXPLICIT` (harness) | `main_ILI_lora.py` L27-30 |
| checkpoint rule | **not disclosed** | **Test MSE selects the best epoch**, every epoch | same | `UNRECOVERED` (paper) / `CODE_EXPLICIT` (code) | `main_ILI_lora.py` L211 L225 L264 |
| backbone layers K | **6** (national) | `6` | `6` | `PAPER_EXPLICIT` + default agrees | paper-md L299; L62 |
| LoRA rank r | **4** | `4` | `4` | `PAPER_EXPLICIT` + default agrees | paper-md L300; L46 |
| LoRA target modules | "multi-head attention layer" | `["c_attn"]` (a **list**) | the author's list default | `PAPER_EXPLICIT` (prose) / `CONFIG_EXPLICIT` (code) | paper-md L214; L47 |
| PEFT enabled? | LoRA is part of the method | `PEFT=0` → **LoRA never applied** | `PEFT=1` | `CONFLICTING_EVIDENCE` | L48; L74-90 |
| freeze policy | "only PE and layer-normalization typically fine-tuned" | loop only ever sets `requires_grad = True` → **no-op** | same | `CONFLICTING_EVIDENCE` | paper-md L214; L58-61 |
| patch length Lp | **24** | `24` | `24` | `PAPER_EXPLICIT` + default agrees | paper-md L301; L72 |
| stride S | **2** | `2` | `2` | `PAPER_EXPLICIT` + default agrees | paper-md L301; L79 |
| seq_len T | 104 ("previous 104 steps") | `104` | `104` | `PAPER_EXPLICIT` (prose) + default agrees | L50 |
| text embedder | full GPT-2 | `gpt2` | `gpt2` | `PAPER_EXPLICIT` + default agrees | paper-md L303; L64 |
| split | 70:10:20 | integer rule → 676/97/193 | same | `PAPER_EXPLICIT` + `CODE_EXPLICIT` agree | paper-md L238; `data_loader.py` |
| environment | Python 3.9.18, PyTorch 2.1.0, RTX 3090 | — | Python 3.9, torch 2.5.1, **A100** | `PAPER_EXPLICIT` (paper) — **not matched** | paper-md L306 |
| metric space | standardized | standardized | standardized | **agree** | `metrics.py` L18-19 |

---

## 2. The two provenance errors this V2 confirms

### E-1 — "Paper: 20 epochs, learning rate 0.0005"

`EE4080_MIFlu_Research_Recovery_Plan.md` L161 and `CodeBuddy_MIFlu_Recovery_Prompt.md` L63
both attach the label **"Paper:"** to 20 epochs and lr 0.0005. The paper discloses
**neither**. `MIFlu_paper.md` L298 and `paper_text.txt` L601-603 say only:

> "We set the number of training epochs and the learning rate for MIFlu empirically
> because the hyperparameters vary depending on the base model."

**Classification: `CONFLICTING_EVIDENCE`.** 20 / 5e-4 are
`RECONSTRUCTED_ASSUMPTION` values that **originate in the project's own configuration**
(`scripts/configs.py`), not in the paper and not in the released defaults (1 / 1e-4).

### E-2 — the decay constant is not `decay_fac`

The project's derived tables label the A1 schedule
`"type1 exponential decay, decay_fac=0.75"`. On the `type1` path the implementation
applies a **hard-coded 0.9** decay from epoch 4; `--decay_fac 0.75` is passed but never
read. Arithmetic confirmation from the observed log value:

```
observed  = 0.00019371024450000004
5e-4 * 0.9^9  = 1.9371024450e-4   exact match
5e-4 * 0.75^9 = 3.7523e-5         ~5x off
```

The *existence* of a schedule is real and does not depend on which constant is used.

---

## 3. What remains genuinely unrecovered

| Item | Why unrecovered | Could it be recovered? |
|---|---|---|
| epochs actually used by the authors | paper discloses nothing; no launch script, CI config or log in the released tree | only by author inquiry |
| initial learning rate actually used | same | only by author inquiry |
| optimizer / scheduler actually used | same | only by author inquiry |
| the 10 seeds | paper discloses no seed list; the harness fixes one seed | by author inquiry, or replaced by a declared list |
| checkpoint-selection rule used for Table V | paper silent | only by author inquiry |
| Table V pooling axes | paper silent | only by author inquiry |
| whether Table V's MIFlu column is quoted or re-run | §V-C states the *baseline* columns are taken from [9]/[14]; MIFlu's own column is unstated | only by author inquiry |
| PEFT=1 trainable-parameter count for the four runs | no artefact records it | **recoverable** from a saved checkpoint on the HPC |

---

## 4. Consequences for reconstruction policy

1. Any A1-P run must carry a per-parameter provenance label, and every
   `RECONSTRUCTED_ASSUMPTION` cell must be marked in the reporting table.
2. **No parameter may be selected because it moves the result toward 1.4355.** A single
   declared reconstruction, recorded before the run, is the only admissible procedure.
3. The released defaults (1 epoch, 1e-4) are **not** the paper's values either, so
   "run the defaults and call it the paper configuration" is equally inadmissible.
4. Where the paper is silent and the code is explicit (metric space, four-horizon
   averaging, split), the code is the better guide and the two agree.
5. Where paper and code **conflict** (multivariate vs univariate windows; LoRA applied vs
   not; freeze effective vs no-op), the conflict is the finding. It must be reported as a
   conflict, not silently resolved in whichever direction produces a nicer number.

---

## 5. Related

- `PAPER_EVALUATION_CONTRACT_AUDIT.md` (Q7–Q9, Q14) — the primary-source derivation
- `TABLE_V_METRIC_PROVENANCE.csv` — per-item status with sources
- `../HYPERPARAMETER_PROVENANCE.md` — the first-round version (unchanged)
- `STATUS_CORRECTION_ADDENDUM.md` C-1, C-3 — the downstream corrections