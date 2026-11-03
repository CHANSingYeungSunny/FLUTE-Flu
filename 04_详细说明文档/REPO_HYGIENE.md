# Repository hygiene — what to ignore, what is authoritative, what must never be deleted

**What this is.** The one page that tells a new agent (or a reviewer) which files in this repository
are *evidence*, which are *generated*, which are *scratch*, and which must never be deleted. It also
records the state of the 2026-11-02 hygiene pass.

**When to read it.** Before deleting or moving anything, before adding a file to version control,
and before quoting a number from a file whose status you are unsure of.

**What it points to.** `05_程序代码/clean_junk.py` (the executable rule) · `.gitignore` (so the junk
cannot return) · `04_详细说明文档/STORAGE_PLAN.md` (cluster-side deletion policy) · `AGENTS.md` §2 rules 10–12
(the two-protocol and full-artefact rules that make the protected list non-negotiable).

---

## 1. The rule

> Remove `_*.out`, `_*.err`, `*.tmp`, `*.bak.*` **older than 24 hours** from the repository root and
> any non-source location.

It is implemented as a script, so it is reproducible and cannot silently widen:

```powershell
python 05_程序代码/clean_junk.py                    # report only (default)
python 05_程序代码/clean_junk.py --apply            # delete what is eligible
python 05_程序代码/clean_junk.py --hours 48         # stricter window
```

The script refuses to touch the protected directories (§3) and any `pred_*.npz`. The 24-hour window
exists because a *running* job writes its `_*.out` / `_*.err` in real time; deleting a file that is
still open truncates live debug output and makes a failure undiagnosable.

### 1.1 State of the 2026-11-02 pass (measured, not assumed)

| Quantity | Value |
|---|---|
| Files matching `_*.out` / `_*.err` / `*.tmp` / `*.bak.*` anywhere outside the protected dirs | **217** (76.9 KiB total) |
| Older than 24 h at 2026-11-02 19:13 (cutoff 2026-11-01 19:13) | **0** |
| **Deleted** | **0** |
| Youngest / oldest match | `_t71.out` 18:31 · `AGENTS.md.bak.20261102T022344` 00:27 |

The whole scratch set was produced by the working sessions of 1–2 November and was between 0.7 and
18.7 hours old at the time of the pass, so **the rule deleted nothing** — applying it literally is the
correct outcome, not a skipped step. Every one of the 217 files becomes eligible on
2026-11-03 at the corresponding hour; run `python 05_程序代码/clean_junk.py --apply` then.

## 2. What to ignore (regenerable, or pure noise)

| Pattern | Why it exists | Safe to delete? |
|---|---|---|
| `_*.out`, `_*.err` (repo root) | PowerShell redirects of one-off probe commands | yes, after 24 h |
| `_*.log` (`_evalwindow_*.log`, `_pytest_final.log`) | captured console output of analysis runs whose *results* are in `02_数字表格/` | yes, but they are the audit trail for a run that produced a table — prefer keeping the ones whose table is quoted |
| `*.tmp`, `*.bak.*`, `*.bak` | atomic-write leftovers and pre-edit backups | yes, after 24 h |
| `01_最终报告/_build/` | the **aborted** first attempt at the document build (its Chinese string literals are mojibaked — do not reuse it) | yes |
| `01_最终报告/.dsh-office-*/` | temporary page renders used for visual inspection | yes |
| `__pycache__/`, `.pytest_cache/` | interpreter/pytest caches | yes |
| `checkpoints/`, `*.pth` | trained weights (5.0 GB). Every number is re-derivable from `pred_*.npz`, so the weights are not evidence | yes, if space is needed |
| `.quarantine/` | artefacts moved aside because they failed a gate (629 MB) | no — it is the record of what was rejected and why |
| `_tmp_*`, `_nlinear_stage/`, `_pull_queue/`, `_dryrun/` | scratch staging areas from earlier passes | case by case; nothing in `02_数字表格/` depends on them |

## 3. What must NEVER be deleted

These are the only re-derivation source for every published number. Deleting any of them turns a
measured table into an unsupported claim.

- `03_预测数据_证据/**` — in particular every `pred_*.npz` (per-window predictions, 7 variables)
- `expanded_runs/**` — the 204 benchmark cells
- `02_数字表格/*.csv` — every table the documents quote
- `04_详细说明文档/**` — the memory, the ledger, the postmortem, the methodology
- `05_程序代码/**` — the analysis chain and the verification gates
- any `pred_*.npz`, anywhere

`05_程序代码/clean_junk.py` enforces this list in code (`PROTECTED_DIRS`, `NEVER_DELETE`), so a future
session cannot accidentally widen the rule into evidence.

## 4. What is authoritative (quote from here)

| Question | Authoritative file |
|---|---|
| What is the benchmark MSE of model *m* at horizon *L*? | `02_数字表格/BENCH_MSE_BY_MODEL_L.csv` |
| What are the PTE/PIE and the K&S pass flags? | `02_数字表格/BENCH_PTE_PIE_BY_STEP.csv` |
| Which model is on the Pareto frontier, and what is the slope? | `02_数字表格/BENCH_EFFICIENCY.csv` |
| On what hardware did each cell run? | `02_数字表格/BENCH_GPU_PROVENANCE.csv` (204/204 A100-SXM4-80GB, `stingy`) |
| What is the reproduction's per-seed oracle? | `04_详细说明文档/LEDGER.md` (2026-11-01 rows) + `05_程序代码/verify_miflu_oracle.py` |
| What was the paper's Table V? | `02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv` and `reference_papers/MIFlu_..._Scheme.md` Table V |
| What is true *now*, and what is still missing? | `04_详细说明文档/STATE.md`, `04_详细说明文档/WORK_BREAKDOWN.md` §7/§11/§13 |
| Why is a number what it is (history)? | `04_详细说明文档/LEDGER.md` (append-only) |
| What broke, and what did it cost? | `04_详细说明文档/BUG_POSTMORTEM_20261102.md` |

### 4.1 Frozen reference files — read-only by design

`02_数字表格/*.pre_evalwindow16.csv` and `*.post_evalwindow16.csv` are **frozen snapshots**, not
live tables:

- `*.post_evalwindow16*.csv` is the bit-identity baseline that `05_程序代码/verify_bench_unchanged.py`
  compares against (384 + 512 + 512 exact comparisons). **Never edit these to make a check pass.**
- `*.pre_evalwindow16.csv` is the pre-ruling (170-window) state, kept so the effect of the window
  ruling can be measured. Historical only.
- `*.pre_miflu.csv` is the pre-MIFlu-merge snapshot. Historical only.

The live table is the un-suffixed file. If a live table and a frozen snapshot disagree, the snapshot
is right about *history* and the live table is right about *now*; the difference must be explained
in `04_详细说明文档/LEDGER.md`, never silenced by re-freezing.

### 4.2 Two protocols, two directories

`author_runs/L{L}_s2021_pred/` is the **reproduction** protocol (1 repetition per horizon, seed
2021). `03_预测数据_证据/expanded_runs/<model>_L<L>_s<seed>/` is the **benchmark** protocol (seeds
42/43/44). Mixing them in one table invalidates it (`AGENTS.md` §2 rule 10). Do not "fill a gap" in
one from the other.

## 5. Encoding hygiene — the rule this project learned twice

This repository has been corrupted twice by text round-tripping through PowerShell. The symptoms are
mojibake (`ç»™`, `æ–‡ä»¶`, `Ã¤`) or replacement characters (`U+FFFD`), and they are silent: the file
still opens, it just says the wrong thing.

Rules that produced the current, clean state:

1. **Never** write project text through `Out-File` / `>` / `Set-Content` without an explicit
   `-Encoding utf8`. Prefer the file tools over shell redirection.
2. Every `.md`, `.py`, `.json` and `.csv` in this repository is **UTF-8 without BOM**. A BOM breaks
   `sbatch` (`"This does not look like a batch script"`) and some CSV readers.
3. Check before committing:

   ```powershell
   python 05_程序代码/repair_mojibake.py --check      # report only
   python 05_程序代码/repair_mojibake.py --apply      # repair the reversible cases
   ```

4. Generated DOCX/PDF are verified after the build: the text is extracted back out, the CJK ratio
   must exceed 0.30, and no `U+FFFD` / `Ã` / `â€` sequence may appear
   (`python 01_最终报告/_build2/verify_docs.py`).

## 6. Generated artefacts and their generators

| Artefact | Generator | Regenerable? |
|---|---|---|
| `01_最终报告/report_internal_{en,zh}.docx` | `python 01_最终报告/_build2/build_docs.py` | yes (figures + `02_数字表格/` are inputs) |
| `01_最终报告/progress_report_{en,zh}.docx` | same | yes |
| `01_最终报告/ieee_manuscript_{en,zh}.docx` | same | yes |
| the six `.pdf` | `python 01_最终报告/_build2/to_pdf.py` | yes (LibreOffice kit) |
| `01_最终报告/figures/*.png` | `01_最终报告/_build/../_build2` figures were produced from `pred_*.npz` by the previous session's `make_figures.py`; **kept as-is** and reused | yes, from the npz files |
| `01_最终报告/MANIFEST.md` | `python 01_最终报告/_build2/make_manifest.py` | yes |
| `01_最终报告/PROJECT_HANDOFF.zip` | `python 01_最终报告/_build2/make_zip.py` | yes |
| `02_数字表格/*.csv` | the analysis chain (`analysis_expanded.py → analysis_postprocess.py → seasonal_naive_baseline.py → plot_bench.py → plot_pareto.py`) | yes, from `pred_*.npz` — but only after the two verification gates pass |

`01_最终报告/_build/` is the **aborted** first build (see §2): it is excluded from version control
and must not be reused — several of its Chinese literals are mojibaked. The current generator is
`01_最终报告/_build2/`, whose `dlv/data.py` asserts the headline numbers so that a drifting CSV
fails the build instead of silently changing a document.
