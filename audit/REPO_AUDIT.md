# Repository audit and refactor decision

Audit of the supplied ZIP, not of a live remote repository. It contains no .git history. The corrected ZIP includes tests_archive/ for inspection; it does not collect cleanly in the shipped layout. No git push, live HPC command or GPU training was performed. This cannot establish whether large files were committed to the actual remote. Source CSV hashes were recorded and are preserved.

## Structure and entry points

| Tree | Role | Current entry point / risk |
|---|---|---|
| 01_最终报告 | Six current reports, figures, builds, plus two older record_for_journal archives | _build2/build_revised.py is the audited report path. Historical source modules are retained, not authoritative current prose. |
| 02_数字表格 | Frozen summary tables, including many pre/post snapshots | Canonical unsuffixed files drive the audit. BENCH_PAIRED_TESTS.csv is retained with its defective source Holm column. |
| 03_预测数据_证据 | Per-cell predictions/logs/metrics | expanded_runs contains raw npz. One NLinear cell was inspected, not the whole tree. |
| 04_详细说明文档 | Method notes, historical state/ledger, agent/HPC notes | Use source/status dates. Some older notes falsely claim complete ablation. |
| 05_程序代码 | Training, analyses, experimental v3/innovation trees | train_miflu.py / train_backbone_966.py are GPU entry points. analysis_postprocess.py’s Holm line is fixed, but its complete output pipeline was not rerun. |
| 06_原始数据集 | Several vintages and train-fit scaler | Only the author-format 966-row data should enter this protocol; do not mix the 1025-row vintage. |
| hpc_experiments | Historical one-off fixes and queue diagnostics | Archive operational scripts after submission. They are not a public quickstart. |
| scripts | New read-only snapshot audit | verify_snapshot.py recomputes aggregate facts and writes separate audit outputs. |
| tests_archive | Supplied historical model/protocol suite | Static inspection; collection fails on missing dependencies and historical paths. No passing suite or reliable total claimed. |
| tests | New seven-test audit suite | The archived original suite is supplied but runtime execution is blocked. These seven tests do not certify training or model correctness. |

## Executed checks

1. `python -m pytest tests_archive --collect-only -q` was **executed and failed during collection** on stale imports and missing dependencies. The raw transcript is ARCHIVE_COLLECTION_LOG.txt. Its partial collected count is not a reliable suite total and no test-count claim is made.
2. The three no-text assertions were inspected statically. The archived model tests were **not executed** because torch/transformers and cached GPT-2 are unavailable in this environment.
3. New `python -m pytest tests/test_snapshot_audit.py -q`: **7 passed**. New collect-only count is 7. These validate Holm direction/ties/floor and audit invariants.
4. `python scripts/verify_snapshot.py --raw-smoke`: passed arithmetic/flag checks and rescored one (170,7,24) NLinear export on 160 windows. MSE = 1.76705057; test start row is at least 773.
5. Local 966×7 numerical file equality: max difference zero. This is not independently downloaded upstream identity.
6. Static Python syntax scan: 251 files inspected, 0 parse failures. Details below. This is not execution coverage.

## Findings and required action

| Issue | Severity | Timing | Effort estimate | Risk to published number |
|---|---|---|---|---|
| Incorrect reverse-min Holm routine | blocker | Fix now; line fixed and separate corrected export supplied | A few hours for correction/independent review | The corrected corpus already reports 0/136 and p about 0.1172; source CSV adjusted values remain quarantined. Original CSV preserved. |
| Archived regression suite has stale imports and missing runtime dependencies | blocker | Repair archive execution before publication; disclose collection errors now | Unknown until path/dependency repair is tested | High uncertainty; do not invent pass counts. |
| Historical reproduce_all.py paths and oracle seed assumptions | high | Bypass with audited snapshot quickstart now; repair general training flow after submission | One working day estimate, then environment-specific validation | Historical oracle expects 2021–2030 and can index incorrectly on benchmark seeds 42–44. Do not conflate protocols. |
| Full-window, regional and rolling-origin validation absent | high scientific limitation | After school submission or sooner if already available | Depends on measured runtime | Could change ranking. Preserve current snapshot. |
| Source effect labelled paired Cohen d but uses pooled SD | high | Relabel now; design season-level inference after submission | A few hours estimate | Point MSE unchanged; effect interpretation changes. |
| Probabilistic scoring uses an arbitrary ensemble variance floor and nonstandard WIS normalisation | high for uncertainty claims | Do not rely on those columns now; repair and rescore after independent formula review | One working day estimate | May change probabilistic scores. Main reports do not rely on them. |
| Hard-coded paths and Windows-only render tools | high | Add portable report rebuild and audit now | A few hours estimate | No training number changes. |
| Misstated 28-arm family sum and hardware coverage | high | Fix now | A few hours estimate | Interpretation/denominators change; source accuracy values unchanged. |
| One-off fix scripts, duplicate snapshots, .bak files | medium | Archive/deduplicate after submission with provenance retained | One to two working days estimate | Low if immutable inputs are preserved. |
| Loose requirements and missing torch/transformers/peft/scipy training dependencies | high for training reproducibility | Publish audit requirements now; lock the tested training environment after recovery | Unknown until a real clean rebuild | Potential runtime/number drift. No unsupported lockfile manufactured. |
| Licence and model revisions | medium | Inspect original code/weight licences before public redistribution | Depends on number of weight sources | MIT covers this project’s original code, not automatically all imported code, data and weights. |

All effort estimates are planning judgements, not measured task times.

## Code quality and silent failure points

The original analysis discovers only directory names matching `[A-Za-z_]+_L...`, excluding identifiers with digits such as encoder names. That explains why some analysis exports have smaller model families. It catches parameter-read exceptions and silently leaves missing values; a global Pareto claim would be unsafe. model/seed/checkpoint metadata should be strict required fields rather than inferred from paths. The run pipeline must fail when required outputs are missing; the historical orchestrator prints MISSING but can still print PASS.

The WIS function divides by a sum of weights rather than the conventional K+0.5 normaliser for its weighted interval-score expression. It can preserve some fixed-design rankings while changing score scale. Its Gaussian three-seed spread with a 0.05 floor is not validated predictive uncertainty. No result derived from that file is presented as calibrated probability in the revised documents.

Determinism needs independent checks of data order, seed routing, adapter initialisation and validation-only snapshot restoration. The source’s causal mask permits a static no-text inference on the author_faithful branch. No absent GPU/model regression test is counted as passed. Legacy text-first and gated branches differ.

## Coverage by area

| Area | This revision | Still missing |
|---|---|---|
| Data | Matched-column equality, split/window metadata, one raw target-start guard | Independent upstream download and full calendar identity |
| Evaluation | Rank, pass flags, correlations, regression, Holm and raw one-cell MSE | Complete 336-cell raw rescore and season-sensitive peak detector audit |
| Model | Static attention/token-order inspection | Original model suite, torch/transformers execution, bit-identical/no-text check |
| Analysis | Seven new meaningful CPU checks and report-source derivations | Independent paired raw inputs, dependence-aware uncertainty, robust coverage scoring |
| Documents | Regeneration and PDF/text/CJK/layout checks recorded in manifest | Word/PowerPoint native application inspection |

## Static details

Syntax findings: []

Files with machine-specific path patterns (26):

- hpc_experiments/check_t6_seeds.py
- hpc_experiments/fix_table6.py
- hpc_experiments/check_dispatch.py
- hpc_experiments/find_table6.py
- hpc_experiments/check_queue.py
- hpc_experiments/diag_scheduler.py
- hpc_experiments/check_table6.py
- hpc_experiments/verify_driver.py
- hpc_experiments/fix_driver.py
- hpc_experiments/analyze_t6.py
- 05_程序代码/build_final_report_v2.py
- 05_程序代码/summarize_regional_table_vi.py
- 05_程序代码/stage5_package.py
- 05_程序代码/train_regional.py
- 05_程序代码/update_agents_next.py
- 05_程序代码/innovation/assets.py
- 05_程序代码/innovation/paths.py
- 05_程序代码/innovation/runtime_guard.py
- 05_程序代码/innovation/hpc_specs.py
- 05_程序代码/innovation/clean_gate.py
- 05_程序代码/v3/build_screening_freeze.py
- 05_程序代码/v3_clean/freeze_candidate_and_comparators.py
- 05_程序代码/v3_clean/build_final_freeze_documents.py
- 05_程序代码/v3_clean/resolve_deferred_and_freeze.py
- 01_最终报告/_build2/verify_docs.py
- 01_最终报告/_build2/to_pdf.py

Largest files in this snapshot (bytes):

- 20,250,027: 03_预测数据_证据/expanded_runs/miflu_L60_s43/predictions_miflu_L60_s43.csv
- 20,244,515: 03_预测数据_证据/expanded_runs/miflu_L60_s42/predictions_miflu_L60_s42.csv
- 20,228,259: 03_预测数据_证据/expanded_runs/miflu_L60_s44/predictions_miflu_L60_s44.csv
- 17,050,562: 03_预测数据_证据/expanded_runs/miflu_L48_s44/predictions_miflu_L48_s44.csv
- 17,039,333: 03_预测数据_证据/expanded_runs/miflu_L48_s43/predictions_miflu_L48_s43.csv
- 17,024,342: 03_预测数据_证据/expanded_runs/miflu_L48_s42/predictions_miflu_L48_s42.csv
- 13,430,270: 03_预测数据_证据/expanded_runs/miflu_L36_s42/predictions_miflu_L36_s42.csv
- 13,421,001: 03_预测数据_证据/expanded_runs/miflu_L36_s44/predictions_miflu_L36_s44.csv
- 13,413,370: 03_预测数据_证据/expanded_runs/miflu_L36_s43/predictions_miflu_L36_s43.csv
- 9,374,252: 03_预测数据_证据/expanded_runs/miflu_L24_s43/predictions_miflu_L24_s43.csv
- 9,368,333: 03_预测数据_证据/expanded_runs/miflu_L24_s42/predictions_miflu_L24_s42.csv
- 9,364,024: 03_预测数据_证据/expanded_runs/miflu_L24_s44/predictions_miflu_L24_s44.csv

A value-suppressing credential-pattern scan was performed for private-key headers, token formats and hard-coded password assignments. Its file/line-only output is recorded in HYGIENE_SCAN.json. It cannot prove no secrets exist. Personal Windows paths occur in the historical renderer scripts and notes. No weights were newly downloaded or redistributed by this revision.

## Refactor decision

**Fix reproducibility blockers now, defer broad refactoring.** Keep training, data and prediction arrays frozen. Supply the repaired statistic, honest README, portable document conversion and small CPU audit. After 20 November, consolidate configuration/paths, archive one-off operations, restore/organise the real tests, pin source/model revisions and add a clean CPU CI job. Do not “clean” code by changing the numerical experiment before its provenance is fixed.

The current handoff is **not yet strong enough for an unqualified JBHI reproducibility statement**. A reviewer can reproduce headline export arithmetic using the new commands. They cannot independently reproduce every training result from a clean checkout because execution of the archived suite, precise training environment, upstream revision, some validation outputs and weight licences remain incomplete. The three highest-impact repairs are: restore and run the real model/data suite; provide a pinned clean training recipe with artefact hashes; and independently rescore every declared run with strict source/seed/window checks.
