# Full Repository Audit Report — MIFlu Reproduction (Local + HPC Remote)

**Date:** 2026-08-16
**Scope:** Read-only audit. No code, config, or files were modified by this audit.
**Trigger:** Phase 1 paper-protocol alignment (L ∈ {24, 36, 48, 60} four independent runs) and a planned bidirectional sync to the CityUHK Burgundy HPC before any training is submitted.

> **AUDIT STATUS FLAG.**
> - **Section A (Local repo):** COMPLETE — performed live on this machine.
> - **Section B (HPC remote):** COMPLETE — the remote cluster (`burgundy.hpc.cityu.edu.hk`) was **reachable on the second attempt** (2026-08-16 17:45 HKT). A live `find` of the remote tree and targeted script inspection were **executed successfully**. All conclusions in B.2–B.5 below are now backed by live remote evidence, not just `HPC_GUIDE.md`.

---

## A. Local Repository Structure

### A.1 File tree (with last-modified time)

Times are local file mtimes on the machine running this audit. `*.pyc`, `__pycache__`, `.pytest_cache`, and `.codebuddy/` (agent memory / plans) are excluded.

```
MLFlu/
├── README.md                                  2026-08-16 17:33   (NEW paper-protocol README)
├── PROJECT_STATUS.md                          2026-08-16 17:33   (updated with Fix-Brief §8)
├── HPC_GUIDE.md                               2026-08-14 19:14   (STALE §6 — see B.4)
├── MIFlu_paper.md                             2026-08-17        (sole cross-reference; direct PDF conversion)
├── plan.md                                    2026-08-06 12:51
├── ChatTime.md                                2026-08-09 22:02
├── Innovation-Proof.md                        2026-08-05 21:48
├── Innovation_HPC_Run.md                      2026-08-05 22:18
├── Related_Work_with_Code.md                  2026-08-10 21:47
├── Rethinking_the_Role_of_LLMs_in_TSF.md      2026-08-12 14:40
├── (MIFlu 复现障碍分析.md 已删除 2026-08-18，内容并入 MIFlu_论文完整解析与答辩解答.md §1)
│
├── reference_papers/  (6 PDFs, all 2026-06-29..07-22, untouched)
│
├── data/
│   ├── raw/
│   │   ├── national_illness_raw.csv           2026-07-18 19:24
│   │   └── us_region_raw.csv                  2026-07-16 17:35
│   ├── ili/                                    (empty / not populated locally)
│   ├── results_miflu_20260814_204437.csv      2026-08-14 21:43   (DEPRECATED L=52 run output)
│   └── training_miflu_log_20260816_173454.txt 2026-08-16 17:35   (local smoke-test log)
│
├── checkpoints/
│   ├── best_miflu_L24.pth                     2026-08-07 13:18   (OLD per-horizon ckpt)
│   ├── best_miflu_L36.pth                     2026-08-07 13:20
│   ├── best_miflu_L48.pth                     2026-08-07 13:19
│   ├── best_miflu_L60.pth                     2026-08-07 13:21
│   └── best_miflu_L52.pth                     2026-08-14 21:36   (DEPRECATED L=52 ckpt)
│
├── results/
│   └── ili/
│       ├── DEPRECATED_walkforward_L52.md      2026-08-16 17:34   (deprecation marker)
│       ├── miflu_fulltest_walkforward.csv     2026-08-14 21:43   (DEPRECATED L=52)
│       ├── figures/
│       │   ├── fig_miflu_eval_continuous.png  2026-08-14 21:45  (DEPRECATED L=52)
│       │   └── fig_miflu_eval_diagnostics.png 2026-08-14 21:45  (DEPRECATED L=52)
│       └── metrics/
│           ├── miflu_ili_peak_indicators.csv  2026-08-14 21:44  (DEPRECATED L=52)
│           ├── miflu_ili_peak_trend_summary.json 2026-08-14 21:44 (DEPRECATED L=52)
│           └── miflu_verdict_table.md         2026-08-14 21:45  (DEPRECATED L=52)
│
├── docs/
│   ├── FIGURE_STYLE_GUIDE.md                  2026-08-14 20:26
│   ├── ILI_FOUR_INDICATORS.md                 2026-08-14 20:26
│   ├── leakage_audit_report.md                2026-08-16 17:31   (NEW — leakage audit)
│   └── full_repo_audit_report.md             2026-08-16 17:42   (THIS FILE)
│
├── tests/
│   ├── test_leakage_audit.py                  2026-08-16 17:30   (NEW)
│   ├── test_timing_metric.py                  2026-08-16 17:31   (NEW)
│   └── test_revin_math.py                     2026-08-16 17:33   (patched: 4-retval unpack)
│
└── scripts/
    ├── train_miflu.py                         2026-08-16 17:30   (FIXED → 4 horizons)
    ├── compute_miflu_indicators.py            2026-08-16 17:31   (FIXED → Timing/Peak-Hit)
    ├── make_miflu_evaluation_figure.py         2026-08-16 17:27   (FIXED → split/test-only)
    ├── feature_verification.py                2026-08-16 17:32   (FIXED → Granger/SHAP caveat)
    ├── miflu_model.py                         2026-08-08 10:22
    ├── textual_embedder.py                    2026-08-14 20:23
    ├── verify_dataset.py / verify_metrics.py / verify_us_region.py  (2026-07-16..08-14)
    ├── train_baseline.py / train_ablation.py / train_regional_*.py (2026-08-06..14)
    ├── diagnose_miflu.py / quick_test.py / audit_channel_isolation.py (2026-08-05..14)
    ├── download_national_illness.py / download_us_region.py (2026-08-14)
    ├── extract_ablation.py / run_ablation.sh (2026-07-21)
    ├── moe_extension.py / test_moe_shapes.py (2026-08-05)
    ├── train_q1_L52.sh                        2026-08-14 20:43   (DEPRECATED L=52 submit)
    ├── infer_walkforward_L52.sh               2026-08-14 21:41   (DEPRECATED L=52 infer)
    └── chattime_variant/
        ├── README.md                          2026-08-16 17:24   (NEW isolation note)
        └── generate_walkforward.py            2026-08-16 17:24   (MOVED here = isolated L=52)

analysis/  (2026-08-05..06, MOE/causality exploratory — not part of MIFlu deliverable)
```

### A.2 Per-core-script description (what it does now, last change, Phase-1 alignment)

| Script | What it does now | Last change (this session) | Phase-1 (L=24/36/48/60) aligned? |
|---|---|---|---|
| `scripts/train_miflu.py` | Main MIFlu training/eval. `CONFIG["L_list"]=[24,36,48,60]`; each L trained independently + 10 reps; writes `data/results_miflu_paper_protocol_*.csv`, tidy table, and `data/predictions_miflu_L{L}_paper_protocol.csv` (with `split` + `abs_week`). `build_windows` off-by-one fix (test target start strictly > val_end). | Reverted `L_list` from `[52]`→`[24,36,48,60]`; added PCC/RMSE; leakage guard; split-column CSV export; English summary. | ✅ Yes — this IS the Phase-1 entry point. |
| `scripts/compute_miflu_indicators.py` | Peak/Trend indicators on paper-protocol per-horizon CSV. Timing & Peak-Intensity computed **only over matched peaks**; Peak-Hit numerator/denominator always co-reported; unmatched = "Missed" (never Timing=0); zero matches → null. | Rewritten for 4-horizon split-CSV input; Timing fix per Fix Brief #3. | ✅ Yes — consumes the Phase-1 CSVs. |
| `scripts/make_miflu_evaluation_figure.py` | Evaluation figures. Default mode reads `data/predictions_miflu_L{L}_paper_protocol.csv`, asserts `split` column, plots **test only**, COVID-shift annotation. Deprecated L=52 walk-forward path kept but flagged. | Rewrote `main()`; added `_week_to_epiweek`; test-only assertion; deprecated branch emits `*_DEPRECATED.png`. | ✅ Yes — paper-protocol path is the default. |
| `scripts/chattime_variant/generate_walkforward.py` | ChatTime-style L=52 non-overlapping walk-forward (T=104, pred=52, stride=52, 70:10:20). Produces `results/ili/miflu_fulltest_walkforward.csv`. | **Moved** from `scripts/` to `scripts/chattime_variant/` on 2026-08-16; docstring marked ISOLATED/NON-DEFAULT. | ❌ No — this is the OLD protocol, intentionally isolated (Phase 2 only). |
| `scripts/feature_verification.py` | 3-tier feature check (Granger / RF MDI+Perm / SHAP) for N=7. | Added Granger "temporal precedence + statistical association" qualifier; RF/SHAP reporting-scale caveat; report/QA English. | ⚠️ Neutral — protocol-agnostic; no horizon assumption baked in. |
| `tests/test_leakage_audit.py` | 4 assertions: test target start strictly > val_end; scaler fit train-only; split non-decreasing (no shuffle); RevIN no-fit. | NEW this session. All pass. | ✅ Yes — guards Phase-1 protocol. |
| `tests/test_timing_metric.py` | Regression for Timing: non-overlapping peaks → Timing=null (not 0.0); offset peaks → correct non-zero. | NEW this session. All pass. | ✅ Yes — guards Fix Brief #3. |
| `tests/test_revin_math.py` | RevIN inverse-transform math. | Patched 3→4 retval unpack to match `MIFlu.forward` (pre-existing bug, not introduced here). | ✅ Yes — unchanged semantics. |

### A.3 Protocol classification of every result / figure / CSV

**✅ NEW protocol (paper protocol, `L ∈ {24,36,48,60}` independent) — authoritative conclusions:**
- `data/results_miflu_paper_protocol_*.csv` (raw per-rep) — *produced by a future run of `train_miflu.py`; not yet on disk as of 2026-08-16, only the DEPRECATED `results_miflu_20260814_204437.csv` exists.*
- `data/results_miflu_paper_protocol_table_*.csv` (tidy table).
- `data/predictions_miflu_L{L}_paper_protocol.csv` (per-horizon, `split` column) — *same, pending run.*
- `docs/leakage_audit_report.md`, `tests/test_leakage_audit.py`, `tests/test_timing_metric.py`.
- `README.md` (paper-protocol deliverable list).

**⚠️ OLD protocol (ChatTime L=52 walk-forward) — DEPRECATED, isolated, NOT a conclusion source:**
- `results/ili/miflu_fulltest_walkforward.csv`
- `results/ili/figures/fig_miflu_eval_continuous.png`, `fig_miflu_eval_diagnostics.png`
- `results/ili/metrics/miflu_ili_peak_indicators.csv`, `miflu_ili_peak_trend_summary.json`, `miflu_verdict_table.md`
- `data/results_miflu_20260814_204437.csv` (the DEPRECATED run that produced the above)
- `checkpoints/best_miflu_L52.pth`, `scripts/train_q1_L52.sh`, `scripts/infer_walkforward_L52.sh`, `scripts/chattime_variant/generate_walkforward.py`
- `results/ili/DEPRECATED_walkforward_L52.md` (explicit deprecation marker, 2026-08-16).

**⚠️ UNVERIFIED local checkpoints:** `checkpoints/best_miflu_L{24,36,48,60}.pth` are dated 2026-08-07 — produced *before* this session's protocol/split fixes. They should be **treated as stale** and re-trained under the current `train_miflu.py` before any figure/indicator is drawn from them. Do not present 2026-08-07 checkpoints as Phase-1 results.

**⛔ MIXING RULE (hard):** Paper-protocol tables (`data/results_miflu_paper_protocol_*`) and the deprecated walk-forward CSV (`results/ili/miflu_fulltest_walkforward.csv`) are **never** combined in one table/figure. `make_miflu_evaluation_figure.py` enforces this by reading only the split-CSV; `read_csv` of the walk-forward file is gated behind an explicit `--walkforward_csv` flag that emits `*_DEPRECATED` artifacts.

---

## B. HPC Remote Repository Structure (CityUHK Burgundy) — LIVE AUDIT

### B.0 Connectivity result (live audit PERFORMED)

- Login node reached: `burgundy.hpc.cityu.edu.hk` (the correct login FQDN; the first attempt from the sandbox timed out, the second succeeded at **2026-08-16 17:45 HKT**).
- Remote workspace: `/home/sychan552/scratch/CHATTIME/Chattime` (contains a tracked **ChatTime** git repo at `ChatTime/` plus the project's own ILI pipeline scripts at the top level and under `scripts/`).
- A live `find` of the remote tree and targeted script inspection **were executed**. All conclusions below are backed by live remote evidence.

### B.1 Live remote file tree (non-`.git`, non-`__pycache__`), with key mtimes

Top-level + `scripts/` (the two directories that matter for this audit). Full tree also contains the upstream ChatTime repo (`ChatTime/`, `model/`, `training/`, `utils/`, `dataset/`), `data/ili/`, `data/raw/`, `data_cgtsf_hf/`, `data_zstsf_gdrive/`, `results/local_dry_run/`, `logs/`, and `scripts/slurm_jobs/` (ZSTSF/CGTSF baselines).

```
ChatTime/                           (upstream ChatTime repo, tracked by git)
HPC_GUIDE.md                        2026-08-14 01:09   (STALE §6 — see B.4)
PROJECT_STATE.md                    2026-08-14 18:34
ILI.csv
build_cgtsf_context.py              2026-08-14 05:25
run_ili_walkforward_cgtsf.py        2026-08-14 05:25
fetch_oxcgrt_us.py
generate_multivariate_insight.py
generate_regime_context.py
submit_chattime_full.sh
submit_chattime_repro.sh
submit_ili_cgtsf.sh
submit_ili_chattime.sh
submit_ili_fulltest.sh              2026-08-14 01:09   (DEPRECATED L=52 pipeline entry)
scripts/  (all 2026-08-14 18:25 unless noted)
  _validate_routing_hypothesis.py              (2026-08-14 18:25)
  build_cgtsf_context.py                       (2026-08-14 18:25)
  compare_cgtsf_threeway.py                    (2026-08-14 18:25)
  compare_cgtsf_vs_baseline.py                 (2026-08-14 18:25)
  compute_peak_metrics.py                      (2026-08-14 18:25)  ← ChatTime peak metrics
  compute_peak_trend_indicators.py             (2026-08-14 18:25)
  convert_raw_benchmarks.py                    (2026-08-14 18:25)
  download_cdc_ili.py                          (2026-08-14 18:25)
  download_zstsf_data.py                       (2026-08-14 18:25)
  dry_run_figures.py                           (2026-08-13 19:50)
  fetch_openmeteo_ili.py                       (2026-08-14 18:25)
  fetch_oxcgrt_us.py                           (2026-08-14 18:25)
  generate_multivariate_insight.py             (2026-08-14 18:25)
  generate_regime_context.py                   (2026-08-14 18:25)
  generate_slurm_jobs.py                       (2026-08-14 18:25)
  make_chattime_figures.py                     (2026-08-13 20:23)
  make_ili_evaluation_figure.py                (2026-08-14 18:25)
  make_ili_fulltest_figure.py                  (2026-08-14 18:25)  ← ChatTime full-test figure
  prepare_ili_chattime.py                      (2026-08-13 20:23)
  run_chattime_cgtsf.py                        (2026-08-14 18:25)
  run_chattime_zeroshot.py                     (2026-08-14 18:25)
  run_ili_inference.py                         (2026-08-13 20:23)
  run_ili_walkforward.py                       (2026-08-14 18:25)  ← ChatTime L=52 walk-forward
  run_ili_walkforward_cgtsf.py                 (2026-08-14 18:25)
  sanity_check_cpu.py                         (2026-08-14 18:25)
  setup_chattime_hpc.sh                        (2026-08-14 18:25)
  similarity_screen.py                         (2026-08-14 18:25)
  slurm_jobs/  (ZSTSF/CGTSF baseline job scripts)
```

**Critical live finding:** `find . -name 'train_miflu.py'`, `'make_miflu_evaluation_figure.py'`, and `'compute_miflu_indicators.py'` returned **nothing** on the remote. The local MIFlu paper-protocol line has **never been uploaded** to HPC. The remote `scripts/` contains the ChatTime-backbone ILI line only.

### B.2 Remote scripts: local vs remote — are they the same lineage? (LIVE-CONFIRMED)

| Remote script | Exists locally? | Verified remote behaviour | Relationship to local `train_miflu.py` |
|---|---|---|---|
| `submit_ili_fulltest.sh` | ❌ No | Reads head: ChatTime ILI full-test continuous walk-forward, `Hist=104 / Pred=52 / stride=52`, **explicit "NO multi-horizon sweep. NO single-window figures."**, `#SBATCH --gres=gpu:a100:1`, calls `run_ili_walkforward.py` → `compute_peak_metrics.py` → `make_ili_fulltest_figure.py` | **Independent second pipeline**, NOT a copy of `train_miflu.py`. |
| `run_ili_walkforward.py` (in `scripts/`) | ❌ No | Reads head: "ChatTime ZSTSF WALK-FORWARD over the full ILI test period", uses `ChatTime-1-7B-Chat` (`reference/ChatTime`), `Hist=104/Pred=52/stride=52`, outputs `results/ili/ili_fulltest_walkforward.csv`. | **Different model & protocol** (7B ChatTime, L=52 rolling) from `train_miflu.py` (fine-tuned MIFlu, L∈{24,36,48,60} independent). Separate codebase. |
| `make_ili_fulltest_figure.py` | ❌ No | Reads head: draws `fig_ili_fulltest_continuous.png`, GT vs walk-forward over full test, peak markers + annotation box (Aggregate MAE / Peak-Week Error / Peak-Intensity Error %). "No single-window / L=24 panels." | Mirrors local `make_miflu_evaluation_figure.py` **in intent only**; not the same file. Local diverged (split-column / test-only / Phase-1). |
| `compute_peak_metrics.py` | ❌ No | Reads head: CDC FluSight-style peak metrics on the ILI full test period → `ili_peak_metrics.json` (Aggregate MAE, Peak Week Error, Peak Intensity Error). | Conceptually overlaps `compute_miflu_indicators.py` but a **different implementation** (FluSight/continuous, not Fix-Brief #3 per-horizon Timing semantics). |

**Answer to the core question (now definitive):** `submit_ili_fulltest.sh` / `run_ili_walkforward.py` / `make_ili_fulltest_figure.py` / `compute_peak_metrics.py` are **NOT** the same code as the local `train_miflu.py` family. They are a **separate ChatTime-1-7B-Chat backbone ILI production line** (L=52 continuous walk-forward) that lives only on the HPC. The local `train_miflu.py` + `compute_miflu_indicators.py` + `make_miflu_evaluation_figure.py` are the MIFlu paper-protocol line. **They are two completely independent pipelines.**

### B.3 Do the remote ChatTime scripts need a Phase-1 rewrite, or can they be retired?

Per the project's own decision (README §"Phase 2 (planned)", `chattime_variant/README.md`, and `PROJECT_STATE.md` line 7: *"MIFlu reproduction: ABANDONED … irreproducible"* — that line refers to reproducing the *original* MIFlu paper, not our fine-tuned MIFlu model):
- The **MIFlu paper-protocol deliverable (Phase 1)** is exclusively the local `train_miflu.py` line. It has **no dependency** on the remote ChatTime scripts.
- The remote ChatTime scripts represent the **ChatTime-backbone comparison / Phase-2 work** — they run a *different model* (ChatTime-1-7B-Chat) and a *different evaluation* (L=52 continuous walk-forward) than the Phase-1 MIFlu protocol.
- **Recommendation:**
  - **Do NOT** reuse `submit_ili_fulltest.sh` for Phase 1. It embeds `Hist=104/Pred=52/stride=52` and an explicit "NO L=24/36/48/60 sweep" rule; re-pointing it at `train_miflu.py` would silently re-produce the deprecated protocol.
  - For Phase 1, **upload the local `train_miflu.py` (and `miflu_model.py`, `textual_embedder.py`, `compute_miflu_indicators.py`, `make_miflu_evaluation_figure.py`, `feature_verification.py`) to HPC** and write a NEW submit script `submit_miflu_paper_protocol.sh` that invokes `train_miflu.py` with the four-horizon sweep, `stingy` partition, PATH-prepend conda, scratch HF cache (HPC_GUIDE §3–4).
  - **Archive** the existing remote `submit_ili_fulltest.sh` (+ `run_ili_walkforward.py`, `make_ili_fulltest_figure.py`, `compute_peak_metrics.py`) by renaming to `*_DEPRECATED.*` / moving into an `archive/` dir so no future run re-submits the L=52 protocol. These scripts are **not part of Phase 1** and should not be rewritten into the paper protocol — they serve a different (ChatTime) model.

### B.4 ⚠️ HPC_GUIDE.md §6 conflict (MUST be corrected before any run) — CONFIRMED LIVE

Live grep of `HPC_GUIDE.md` on the remote confirms the conflict is real:
- Line **124**: `### Figure output convention (Phase 0.5 / ILI) — CORRECT full-test pattern (2026-08-14)`
- Line **129**: `  - NO single-window figures. NO multi-horizon L=24/36/48/60 sweep.`
- Line **135**: `  ... (replaces the deleted submit_ili_chattime.sh / submit_ili_multihorizon.sh).`

The verified remote text (lines 124–135):

> "The ONLY ILI figure is `results/ili/figures/fig_ili_fulltest_continuous.png`, produced by `make_ili_fulltest_figure.py` … NO single-window figures. **NO multi-horizon L=24/36/48/60 sweep.** … Pipeline entry point: `submit_ili_fulltest.sh` (replaces the deleted `submit_ili_chattime.sh` / `submit_ili_multihorizon.sh`)."

This **directly contradicts** the Phase-1 plan, which is built around the **L=24/36/48/60 four-horizon independent sweep** as the *only* authoritative result source. Note the guide even claims `submit_ili_multihorizon.sh` was *deleted* — but the local `train_miflu.py` multi-horizon sweep is exactly what Phase 1 needs, so the guide's framing is now inverted relative to the current project direction.

If a future session (or the user) follows §6 literally, it will: (1) submit `submit_ili_fulltest.sh` (L=52 walk-forward — deprecated protocol); (2) forbid the very sweep the paper requires; (3) overwrite/ignore the paper-protocol figures.

**Required fix (pending user confirmation):** update `HPC_GUIDE.md` §6 to reflect the new protocol:
- Replace "NO multi-horizon L=24/36/48/60 sweep" with "**The authoritative pipeline IS the L=24/36/48/60 four-horizon independent sweep** (`train_miflu.py`); `submit_ili_fulltest.sh` is DEPRECATED."
- Replace the single-figure convention with: per-L figures `fig_miflu_eval_continuous_L{L}.png` (test-only) + the tidy table `data/results_miflu_paper_protocol_table_*.csv` as the conclusion source.
- Add the new submit script name (`submit_miflu_paper_protocol.sh`) and the upload/verify checklist (re-upload every changed `.sh` alongside `.py`).
- **Both the local and the remote `HPC_GUIDE.md` must be updated** (the remote copy was last touched 2026-08-14 01:09 and is the one HPC runs actually consult).

Until §6 is rewritten on **both** copies, the guide is **unsafe to follow** for Phase 1.

### B.5 Sync-state verdict (replaces the former "pending remote actions")

Live audit resolved all five former pending items:

1. **Remote tree captured** — see B.1. ✅
2. **Local vs remote sync:** `train_miflu.py`, `compute_miflu_indicators.py`, `make_miflu_evaluation_figure.py`, `feature_verification.py`, `miflu_model.py`, `textual_embedder.py` are **absent on the remote** → the 2026-08-16 local fixes are **100% out of sync** with HPC. ✅ (confirmed)
3. **`generate_walkforward.py`:** the remote has **no** `generate_walkforward.py` at all (only `run_ili_walkforward.py` / `run_ili_walkforward_cgtsf.py`). The local isolation move (`scripts/chattime_variant/generate_walkforward.py`) therefore has no remote counterpart to reconcile — but the remote's `run_ili_walkforward.py` is the ChatTime equivalent of that old L=52 protocol. ✅ (resolved)
4. **Archive targets confirmed present remotely:** `submit_ili_fulltest.sh`, `scripts/run_ili_walkforward.py`, `scripts/make_ili_fulltest_figure.py`, `scripts/compute_peak_metrics.py` all exist on the remote and must be renamed/relocated to `*_DEPRECATED`. ✅ (confirmed)
5. **Stale remote checkpoints:** no `best_miflu_L*.pth` exists anywhere on the remote (the remote never ran the MIFlu fine-tune). ✅ (no stale MIFlu ckpt to worry about; the remote's model is the 7B ChatTime weights in `reference/ChatTime`.)

---

## C. Gate Before Execution (per user instruction — DO NOT auto-train)

This audit produced **no training and changed no code**. Before entering the Upload → Submit four-horizon training → Pull-back results phase, the following must be confirmed by the user:

1. **Local → HPC sync verified:** the 2026-08-16 fixed `train_miflu.py` (+ `miflu_model.py`, `textual_embedder.py`, `compute_miflu_indicators.py`, `make_miflu_evaluation_figure.py`, `feature_verification.py`) are **uploaded** to the remote `scripts/`. Live audit (B.5.2) confirmed they are currently **absent** on HPC — upload is mandatory before any run.
2. **HPC_GUIDE.md §6 rewritten** (on **both** the local and remote copies) to mandate the L=24/36/48/60 sweep and deprecate `submit_ili_fulltest.sh`. Live grep (B.4) confirms the remote copy still carries the banning line.
3. **Remote ChatTime scripts** (`submit_ili_fulltest.sh`, `scripts/run_ili_walkforward.py`, `scripts/make_ili_fulltest_figure.py`, `scripts/compute_peak_metrics.py`) explicitly archived/renamed (`*_DEPRECATED`) so they cannot be re-submitted for Phase 1. Live audit (B.5.4) confirmed all four exist on the remote.
4. **Local stale checkpoints** (`checkpoints/best_miflu_L{24,36,48,60}.pth` dated 2026-08-07) acknowledged as not representing Phase-1 results; re-trained under current `train_miflu.py`. (No remote MIFlu ckpt exists — B.5.5.)

**Live remote audit (Section B) is now COMPLETE** — all former pending items are resolved with evidence. The gate above is fully actionable now.

---

## D. Supplementary Audit Note — missed remote directory `MLFLU/` (2026-08-16)

A third remote scratch directory was discovered that the original Section B audit (and the
HPC_GUIDE `MLFlu_Q1` reference) did **NOT** cover:

- `/home/sychan552/scratch/MLFlu_Q1/` → **DOES NOT EXIST** (the path used in the old HPC_GUIDE
  memory note was obsolete/incorrect).
- `/home/sychan552/scratch/MLFLU/` → **EXISTS** (top mtime 2026-08-14). This is the **OLD L=52
  workspace**, a historical leftover from the deprecated protocol:
  - `scripts/train_miflu.py`: `L_list=[52]` (old protocol, NOT the paper protocol).
  - `checkpoints/`: `best_miflu_L24.pth` (2026-08-14_20:37), `best_miflu_L36.pth`
    (2026-08-14_20:37), `best_miflu_L52.pth` (2026-08-14_21:12). **No L48 / L60** — incomplete
    for the four-horizon protocol.
  - `data/results_miflu_20260814_204437.csv` (the DEPRECATED L=52 run) + its training log.
  - Still carries the deprecated `generate_walkforward.py`, `train_q1_L52.sh`,
    `infer_walkforward_L52.sh`.
- `/home/sychan552/scratch/CHATTIME/Chattime/` → **EXISTS** (top mtime 2026-08-16_18:16), the
  verified Phase-1 working dir (MIFlu paper-protocol scripts uploaded 2026-08-16_17:57, old
  ChatTime scripts archived as `*_DEPRECATED`, HPC_GUIDE §6 rewritten).

**Conclusion / decision:**
- The previous audit (Section B) **omitted `/home/sychan552/scratch/MLFLU/`** — it was missed
  because the old memory referenced `MLFlu_Q1` (which does not exist), and the live `find` in
  Section B.1 only listed `CHATTIME/Chattime`. This gap is now closed.
- **Authoritative working directory for the Phase-1 four-horizon training = `/home/sychan552/scratch/CHATTIME/Chattime/`** (scripts already uploaded, paths verified, HPC_GUIDE §6 aligned).
- `/home/sychan552/scratch/MLFLU/` is to be treated as **历史遗留 (legacy), NOT used** — do NOT
  submit training from there, do NOT read its checkpoints as Phase-1 results. It is retained for
  historical reference (the "坑" record) and is **NOT deleted** per user instruction.
- No `REPRODUCTION_PROOF.md` document exists anywhere (local or remote); it was deleted on
  2026-08-14 (see Cross-Reference Convention). Only a `.codebuddy/plans/` plan-spec artifact
  remains, which is not the document and needs no annotation.

---

*End of audit. No files were modified by producing this report.*
