# MLFlu — Influenza Forecasting Reproduction & Innovation (FYP)

**Author**: CHAN Sing Yeung Sunny (Final Year Project, 2026)

This repository is an independent **reproduction and innovation** study of the MIFlu method, based on *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme* (Moon, Shim, Kim & Hwang, IEEE JBHI 29(10):7790–7801, 2025, DOI [10.1109/JBHI.2025.3561214](https://doi.org/10.1109/JBHI.2025.3561214)).

We reproduced the paper's **Table V** on the official US CDC National-Illness 966-row dataset, then ran a **28-model benchmark** with four sub-benchmarks (accuracy, peak skill, efficiency, statistical significance). The reproduction is honest: we fixed two defects discovered in the original code (data leakage via test-set checkpoint selection, and a test-loader bug) and report them as deliberate deviations.

> **中文说明**：本仓库是 CHAN Sing Yeung 的毕业设计（FYP）成果，独立复现并创新扩展了 Moon et al. (IEEE JBHI 2025) 的 MIFlu 方法。在官方 966 行 US CDC National-Illness 数据集上复现 Table V，并跑了一个 28 模型基准（含四个子基准）。复现过程诚实标注了两处修复的缺陷（验证集选检查点修复数据泄漏、7 变量指标修复 test-loader bug）。最新的 1120 格共同协议结果与旧快照分开保存，见下文 **New common 1120-cell panel**。

## Headline Results

### Reproduction of Table V (MIFlu, 10-seed mean, 2021–2030, validation-selected checkpoints)

| Horizon L | Paper MSE | Our MSE | Δ | Paper MAE | Our MAE | Δ |
|----------:|----------:|--------:|--:|----------:|--------:|--:|
| 24 | 1.5420 | 1.3045 | **−15.4%** | 0.7260 | 0.7482 | +3.1% |
| 36 | 1.4220 | 1.3561 | **−4.6%** | 0.7790 | 0.7712 | −1.0% |
| 48 | 1.4140 | 1.6543 | +17.0% | 0.7570 | 0.8381 | +10.7% |
| 60 | 1.3640 | 1.6829 | +23.4% | 0.7190 | 0.8596 | +19.6% |
| **4L mean** | **1.4355** | **1.4995** | **+4.5%** | **0.7452** | **0.8043** | +7.9% |

**Sign crossover 2–2**: we *beat* the paper at L=24 and L=36 but *lose* at L=48 and L=60 (longer horizons are harder for our run). Net **+4.5%** on the 4-horizon mean — a close, credible reproduction. **Defensible claim only**: reproduced within 4.5% with a horizon-dependent sign — *not* a claim of superiority, and *not* "the paper is wrong". Every MIFlu cell is gated against the 40-run per-seed oracle at |Δ| ≤ 1e-5, so the numbers trace to individual runs, not a summary file.

### 28-Model Benchmark — Historical Snapshot (frozen `02_数字表格/`)

| Sub-benchmark | Champion | Key number |
|---------------|----------|-----------|
| **1. MSE/MAE** (accuracy) | **MIFlu** | 1.5574 (4-horizon mean) |
| **2. PTE/PIE** (peak skill, Kramer & Shaman) | **NLinear** | 4/16 passes; step-0 PTE 0.21 wk, PIE 3.2% |
| **3. Pareto** (accuracy vs params) | NLinear is Pareto-optimal | 2,520 params vs PatchTST 531,878 (211× fewer, only 11% worse MSE, non-significant) |
| **4. Statistical significance** | **0/136 rejections** after proper Holm | 128/136 raw p<0.05; min adjusted p ≈ 0.0664; NLinear–PatchTST 0.1172 |

> **Historical finding (old snapshot)**: the MSE leader (MIFlu) is not the peak-skill leader (NLinear). The MSE order is MIFlu < PatchTST < NLinear while the PIE order is NLinear < MIFlu < PatchTST — **inverted at both ends**. MIFlu and NLinear each pass 4/16 aggregated cells at *different* locations; PatchTST passes 0/16. This is a descriptive local change, not statistical independence, universal dominance or an exact reversal.

**Important correction.** The original exported `p_holm` column is defective. Recomputing from `p_raw` with a forward cumulative maximum after sorting gives **0/136 rejections**, not the "109 significant" figure quoted in older drafts. The exact-grid reconstruction is distinct from rounding the six-decimal export. Parameter exports cover 11 arms, not all 28; 211× parameters does **not** mean 211× latency.

### Frozen LLM encoders (negative result)

11 frozen LLM encoders (Qwen2.5, DeepSeek-R1-distill ×5 sizes, Tencent Hunyuan ×3, Tencent ContextPilot ×2) were merged into the benchmark as feature extractors + a shared linear head. **All are poor**: best Tencent-Hunyuan-1.8B (MSE 4.7374), worst Qwen2.5-1.5B (5.2049) — every one ~3× worse than MIFlu (1.5574); **none pass the Kramer & Shaman peak criterion**. This finding is specific to **frozen features plus a linear readout**; it does not cover generation, prompting, fine-tuning or numerical time-series pretraining.

### Notable findings (from the historical 28-model snapshot)

- **A linear model is #2.** NLinear reaches MSE 1.8716 with only **2,520 parameters**, versus PatchTST's 531,878. Architecture sophistication does *not* buy accuracy on a 966-row series.
- **Published LLM forecasters do badly.** Qwen-Time-LLM (5.2557) and CALF-LLM (5.5785) are both large, published models — and both are beaten by a nearest-neighbour baseline (KNN, 3.7854).
- **Model choice dominates.** The MSE spread is **3.4×** (1.6621 → 5.6155); which model you pick matters far more than any hyper-parameter tuning reported in the compared papers.
- **More parameters ≠ better.** Regressing 4-horizon MSE on log₁₀(parameters) across the 11 parametric arms gives slope **+0.1171** and **R² = 0.0223** — more parameters trend *worse*, and the relationship is ~pure noise.

### New common 1120-cell panel (verified 2026-11-07 00:28 HKT / 2026-11-06 16:28 UTC)

Measured directly on Burgundy (`cellok.py count`, `squeue`, `sacct`, `mmlsquota`, NPZ validation), not from an older handoff. Full details: `HANDOFF_20261105/final/FINAL_RESULTS.md`, `HANDOFF_20261105/final/SCIENTIFIC_AUDIT.md`, `HANDOFF_20261105/v8/SCIENTIFIC_AUDIT.md`.

| Item | Verified |
|---|---|
| Core artefacts | **160 / 160** |
| National 28 × 4 × 10 panel | **1120 / 1120** (`BY_REASON {}`) |
| Seven-channel MIFlu recovery | **40 / 40 NPZ** from existing checkpoints; all finite, shapes `(N, 7, L)`, windows 170/158/146/134 at L=24/36/48/60, `target_start_row` starts 773; **0 bad files** |
| Slurm queue | **empty** — no running or pending jobs at capture |
| Walk-forward (legacy N=3 panel) | `final/WF_RECOMPUTED.csv` **1020 / 1020 `ok`** |
| Regional Table VI | **53 / 53** valid `mse_z` rows (10-variable regional metric, not the 7-channel national metric) |
| Quota | home 23.9 GB / 50 GB soft; scratch 342 GB / 300 GB soft, **grace 8 days**, hard 1024 GB |

The O1 scoring repair is complete. `final/` holds harmonised scores on **two identical-target-population panels**: `all_valid` (all valid test windows) and `crop` (historical crop). Both give the same leading MSE order MIFlu < PatchTST < NLinear (all-valid **1.7944 / 1.9521 / 2.0782**; crop **1.4994 / 1.6352 / 1.9027**). The crop panel reproduces the historical MIFlu mean (1.4994 vs 1.4995), validating checkpoint recovery.

> **New results change an old conclusion.** On the harmonised panel, step-level peak passes are MIFlu **252/1680** (15.0%), PatchTST **215/1680** (12.8%), NLinear **57/1680** (3.4%) — so "NLinear is the peak champion" does **not** hold here. Event-level analysis (181,868 events) separates detection from timing/height: iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8% detection, PIE 30.4%. The 60-cell ablation ladder is **non-monotonic** (K4 best 1.4989, K12 worst 1.7604), contradicting the older "logarithmic-ladder champion / monotonic depth trend" claim. The historical 16-unit table, the new 1120 panel, the legacy 5-fold N=3 walk-forward panel, the CDC ILINet vintage reconstruction and the foundation roster are **separate populations** and must never be pooled.

**Still blocked / unverified** (not findings): foundation models (Chronos/TimesFM) are on a **separate roster**, use a **single-variable** adapter (7 channels predicted independently, so cross-channel dependence is lost and the information set is not equal to the multivariate arms), were run **zero-shot with no training**, and their 10 repetitions are **10 rolling origins (rows 773–782), not 10 training seeds** (`seed_semantics=NOT_APPLICABLE`); a literal 10-seed expansion remains `NOT_EXECUTED_BY_PROTOCOL`. Resource measurements are a **6-model subset** on one A100 (no full-1120 Pareto). CDC vintage uses a Delphi ingest **proxy**, not a CDC-issued revision number. JBHI guidance was verified on 2026-11-06 (14/16 pp incl. supplementary, ≤250-word abstract, APC US$2,800) but the official template-selector download is **UNVERIFIED** and `manuscript_submission_ready: NO`. The expansion protocol was unfrozen when submitted — a disclosed **retrospective** deviation. Ten seeds estimate training variation, not independent epidemics. A structural validator `PASS` is `scientific_readiness: NOT_ASSESSED`, not scientific certification.

### Final v8c evidence package (verified 2026-11-07 03:46 HKT / 2026-11-06 19:46 UTC)

Every figure below was re-checked against the files on disk and against Burgundy at that time.

| Item | Verified value |
|---|---|
| National panel | `cellok.py count` → **COMPLETE 1120 / 1120**, `BY_REASON {}` |
| Core | **COMPLETE 160 / 160** |
| Foundation matrix (separate roster) | `FOUNDATION_80_CELLS.csv` → **80 / 80 `ok`**, all finite, 80 real NPZ (40 Chronos + 40 TimesFM); sha256 `6278267…92cf` |
| Foundation pilot cost | peak VRAM **2608 MiB**; Chronos **10.229 ± 1.074 ms**, TimesFM **50.906 ± 4.459 ms** (warm-up + repeats) |
| Legacy `final_llm_import` tree | **388 / 388 NPZ readable** (two previously corrupt files restored by COPY, originals quarantined not deleted); `BENCH_MSE_BY_MODEL_L.csv` sha256 `a7d98ad…1e46`, 69 lines |
| Walk-forward (legacy N=3 panel) | `WF_RECOMPUTED.csv` **1020 / 1020 `ok`**; legacy means MIFlu **2.2203**, PatchTST **3.0396**, NLinear **3.2116** (seeds 42/43/44, separate population) |
| Regional Table VI | **53 / 53** valid `mse_z` rows |
| Six-model resource measurements | peak VRAM (MiB): MIFlu **4816**, NLinear **558**, PatchTST **720**, GPT-2 frozen encoder **1070**, Chronos **596**, TimesFM **2594**; latency 6.98 ± 0.097 / 9.854 ± 0.337 / 48.273 ± 3.531 ms; `RESOURCE_MEASUREMENTS.csv` sha256 `9574eef…1117` |
| v8c documents | manuscript 10 pp, internal report 10 pp, Q&A companion 16 pp; all six DOCX/PDF conversions rc=0; hashes match `v8/docs/V8C_REBUILD_LOG.md` |
| Return package | 1432 files hashed, 1434 members; validator `integrity_status: PASS`, `errors: []`, `scientific_readiness: NOT_ASSESSED` |
| HPC jobs | 16 job IDs (`743850`, `743920`, `744110`, `744134`, `744271`, `744334`, `744532`, `744533`, `744574`, `744576`, `744589`, `744607`, `744884`, `744886`, `744897`, `744899`) — **all COMPLETED 0:0**; `squeue` empty |
| Quota | home 23.9 GB / 50 GB soft; scratch 342 GB / 300 GB soft, **grace 8 days** |

| Return ZIP (`HANDOFF_20261105/v8/`) | bytes | SHA-256 |
|---|---:|---|
| `RETURN_TO_CHATGPT.zip` | 199,883,696 | `5433e8d8a799c418c4fd55db1e8884b1ec1f4b141f98790f0f51cdd39887ad03` |
| `RAW_EVIDENCE.zip` | 345,006,379 | `550977437230dafc257cb3a36b02837764afec411e90f286b41d3f3c3d083f75` |

Authoritative hashes live **outside** the package in `HANDOFF_20261105/v8/packaging/FINAL_HASHES.txt`, because the package mirrors its own documents and would otherwise be self-referential. Both ZIPs extract into the same root. To refresh after any document edit:

```bash
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"
```

**Not measured / not claimed:** isolated single-forward latency for MIFlu, NLinear and PatchTST (`NOT_MEASURED` — the old NPZ scoring-path numbers are not a forward pass), the official JBHI template class file (`UNVERIFIED`), an information-set-matched per-channel foundation adapter, dependence-aware confirmatory statistics, any full-1120 Pareto claim, and submission readiness.

---

## Deviations from the Paper (reported honestly)

| # | Deviation | Original code | Why necessary |
|---|-----------|--------------|---------------|
| 1 | **Checkpoint selection** | paper/test config uses **test set** to pick best checkpoint → data leakage | we select on the **validation** set only. Top-tier venues forbid test-set selection. |
| 2 | **Metric aggregation** | 7-variable normalized aggregation | we use **7-variable z-space MSE/MAE** to match Table V exactly; PTE/PIE use **ILITOTAL** (de-normalized to patient counts) because the 7 variables differ in scale by ~283,650× (OT mean 493,629 vs %ILI 1.74) and cannot be de-normalized. |
| 3 | **Inference windows** | `batch_size=16, drop_last=True` drops the tail | new inference exports use `drop_last=False` (170/158/146/134 windows); the historical crop (160/144/144/128) is reconstructed from the *same* predictions for comparability, never by mixing stored scores. |

Both original deviations are flagged `[DEVIATION]` in the reports.

---

## Why These Protocol Choices (for reviewers)

- **Reproduction uses 10 seeds (2021–2030); the historical benchmark snapshot used 3 seeds (42/43/44).** The new common panel uses **2021–2030 for all 28 models**, so every model shares the same seed list. 42/43/44 are **not** a subset of 2021–2030 — the two sets are never merged into one ten-seed estimate.
- **70/10/20 train/val/test split (676/97/193 weeks), chronological.** Standard split of the LTSF benchmark family (Informer → PatchTST → MIFlu); scaler fit on train only. The 966-row profile and T=104 lookback are pinned, not inferred from `configs.py` defaults.
- **`(W//16)*16` crop windows (160/144/144/128).** NOT a journal requirement — a side-effect of the original code's `drop_last=True`. It is kept only as the **sensitivity** panel; `all_valid` is the primary panel.
- **Pareto frontier**: models where no other model is both more accurate *and* more efficient. A standard ML-efficiency analysis; our measured subset does not support a full-1120 claim.

---

## Repository Structure

```
MLFlu/
├── README.md                      # This file
├── AGENTS.md                      # Operational rules for AI agents working on this repo
├── HPC_GUIDE.md                   # How to run experiments on the CityU HPC cluster
├── 00_START_HERE.md / README_START_HERE.md   # Revision 9.2 entry points
├── DELIVERY_INDEX.json / DELIVERY_MANIFEST.json  # Current document roles and hashes
├── reproduce_all.py               # One-click reproduction entry
├── requirements.txt
├── CITATION.cff  /  LICENSE
├── 01_最终报告/                   # Generated reports (DOCX + PDF) + build pipeline (_build2/)
│   ├── report_internal_zh.pdf     # Concise Chinese internal report
│   ├── report_internal_qa_zh.pdf  # Separate Q01–Q25 literature companion
│   ├── progress_report_en.pdf / progress_report_zh.pdf  # FYP school template
│   ├── ieee_manuscript_en.pdf     # Journal-style manuscript (LaTeX-compiled PDF)
│   ├── v7/  v8/                   # Dated revision builds
│   └── figures/                   # Charts (forecasts, K&S ranking, Pareto…)
├── 02_数字表格/                   # Frozen historical CSV tables + CDC vintage reconstruction
├── 03_预测数据_证据/              # Raw predictions + audit evidence
├── 04_详细说明文档/               # Glossary, methodology, LEDGER, HPC runbook, SOP
├── 05_程序代码/                   # Reproduction + benchmark pipeline
├── 06_原始数据集/                 # Official 966-row CDC dataset + scaler
├── HANDOFF_20261105/              # Dated handoffs, final/ scored tables, v7/v8 evidence
├── handoff_revision9/             # Current DeepSeek prompt + RETURN_CONTRACT.json
├── manuscript/  presentation/     # LaTeX source, 13-slide deck, English notes
├── audit/  journal/  scripts/     # Audits, journal record, rebuild scripts
└── tests_archive/                 # Archived tests (collection has known import errors)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full reproduction + benchmark + report pipeline
python reproduce_all.py

# 3. Rebuild the current rev9.2 documents
python scripts/build_delivery_v9.py
python 01_最终报告/_build2/to_pdf.py
python manuscript/build_pdf.py

# 4. Verify report integrity (content + CJK round-trip)
python 01_最终报告/_build2/verify_docs.py
python scripts/verify_snapshot.py --raw-smoke
```

English notes and report Word copies require LibreOffice; the canonical English manuscript PDF comes from `manuscript/build_pdf.py`, not a Word export. Exact executed/not-executed commands are in `audit/revision9/EXECUTION_RECORD.md`.

---

## Key Definitions (used throughout the reports)

- **Horizon L**: input is a fixed **T=104**-week history; output is **L weeks** of forecast (L=24/36/48/60). L is the *lead*, not the history length.
- **Step s** within an L-week forecast: step 0 = the **1st week ahead**, step 3 = the 4th week ahead.
- **PTE (Peak Timing Error)** = |predicted peak week − actual peak week| (weeks). **PIE (Peak Intensity Error)** = relative error of predicted peak intensity. **Kramer & Shaman (2019, PLoS Comput Biol 15(2):e1006742)** criterion: PTE ≤ 1 week **and** PIE ≤ 25% ⇒ peak captured. The new 1120 panel uses `find_peaks(prominence=0.15*range, distance=15)` with ±8-week one-to-one matching — a **different scoring population** from the historical 16 aggregated units.
- **The 16 aggregated units are not a seasonal probability**, and PIE is not probability calibration. Non-rejection is not equivalence.

---

## Deliverables — Reports (in `01_最终报告/`)

Reports are produced in Chinese and English variants, built from the same pipeline so numbers agree across languages. Revision 9.2 keeps the concise Chinese internal report and the separate `report_internal_qa_zh` Q01–Q25 companion; FYP Part A (BEng — Computer and Data Engineering, EE4080, 2026/27 A) is confirmed, while the required meetings and weekly-hours fields stay blank because actual values are unknown.

**Key content shared by all reports** (so the README, reports and tables never disagree): the frozen 28-arm historical snapshot in `02_数字表格/`; the separately named new 1120-cell panel in `HANDOFF_20261105/final/`; corrected Holm 0/136; "inverted at both ends"; 4/16 aggregate units for MIFlu and NLinear, 0/16 for PatchTST; and the explicit note that new verified results may change rankings or conclusions.

**Handoff packages**: `HANDOFF_20261105/v8/RETURN_TO_CHATGPT.zip` and `RAW_EVIDENCE.zip` extract into the same root and contain the per-cell ledger, both scored panels, event-level peaks, resource measurements, executed-command logs and protocol deviations. The full-project and focused DeepSeek ZIPs are delivered as local files (gitignored by `*.zip`).

**Presentation**: Progress presentation is in Week 12 (Nov 16–20, 2026); report submission deadline **20 Nov 2026 (11:59 pm)** via FYP InfoNet. The 13-slide owner-layout deck and 606-word English script are in `presentation/`. Formatting and a validator PASS do **not** establish JBHI submission readiness or acceptance.

---

## Status (as of 2026-11-07)

- ✅ Table V reproduction (10-seed, +4.5%, sign crossover 2–2)
- ✅ Historical 28-model snapshot, four sub-benchmarks; corrected Holm 0/136
- ✅ New common 1120-cell national panel complete — **1120/1120**
- ✅ O1 scoring repair: **40/40** seven-channel MIFlu tensors recovered from checkpoints; `all_valid` and `crop` panels built from identical target populations
- ✅ Walk-forward recomputation **1020/1020**; regional Table VI **53/53**; CDC ILINet vintage reconstruction complete (Delphi proxy)
- ✅ 60-cell ablation ladder measured — **non-monotonic** (K4 best, K12 worst); old monotonic claim superseded
- ✅ Revision 9.2 documents plus **v8c** rebuild: manuscript 10 pp, internal report 10 pp, Q&A companion 16 pp; superseded claims marked SUPERSEDED in the body
- ✅ `final_llm_import` legacy tree restored to **388/388** readable NPZ; table rebuilt (sha256 `a7d98ad…1e46`)
- ✅ Foundation models (Chronos/TimesFM) on a **separate roster**: **80/80** zero-shot cells, real NPZ, measured latency/VRAM
- ✅ Resource measurements for **six models** (MIFlu 4816, NLinear 558, PatchTST 720, GPT-2 encoder 1070, Chronos 596, TimesFM 2594 MiB peak VRAM)
- ✅ Dated JBHI guidance verification; `v8/PAPER_TO_CODE.md` created and applied by the packager
- ✅ HPC queue empty at capture; all 16 v8 job IDs COMPLETED 0:0; no duplicate lanes or controllers
- 🔄 Official JBHI template-selector download UNVERIFIED; `manuscript_submission_ready: NO`
- 🔄 Isolated single-forward latency NOT_MEASURED for MIFlu, NLinear, PatchTST
- 🔄 Scratch quota 342 GB / 300 GB soft, grace 8 days — cleanup proposed separately; nothing deleted
- ⛔ Not claimed: seasonal external validity, independent epidemics from repeated seeds, equivalence from non-rejection, information-set-matched foundation adapter, full-1120 Pareto, O2 calibration, or venue acceptance

---

## Citation

If you use this work, please cite:

```bibtex
@misc{chan2026mlflu,
  title        = {MLFlu: Influenza Forecasting Reproduction \& Innovation},
  author       = {CHAN, Sing Yeung Sunny},
  year         = {2026},
  howpublished = {\url{https://github.com/CHANSingYeungSunny/FLUTE-Flu}},
  note         = {Final Year Project}
}
```

The paper being reproduced:

```bibtex
@article{moon2025miflu,
  title   = {MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme},
  author  = {Moon, Jinha and Shim, Seongjun and Kim, Minha and Hwang, Jae-Hyun},
  journal = {IEEE Journal of Biomedical and Health Informatics},
  volume  = {29},
  number  = {10},
  pages   = {7790--7801},
  year    = {2025},
  doi     = {10.1109/JBHI.2025.3561214}
}
```

See [CITATION.cff](CITATION.cff) for machine-readable metadata.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Author

**CHAN Sing Yeung Sunny** — Final Year Project (2026). Sole author of this reproduction and innovation study.
