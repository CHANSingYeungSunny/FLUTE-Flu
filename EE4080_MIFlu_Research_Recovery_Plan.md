# EE4080: Independent MIFlu Research Recovery Plan

Prepared 23 September 2026 (UTC). Evidence: the three supplied PDFs, the public MIFlu repository inspected at commit `6ed210150b8819313947cf607eb1821c87b1bee3`, and the primary sources linked below.

**Recommendation:** preserve the completed experiments, audit the data and executable pipeline, and add a narrowly scoped reproduction study. Do not launch a wholesale eight-model rerun merely because the snapshots differ. There are concrete released-code issues to resolve before expensive training.

**Evidence boundary:** I read the supplied paper, Chinese results report and project planning document, and inspected the live author code and both CSVs through GitHub's code view. I did not receive the project's 1,025-row CSV, raw July API response, training code, checkpoints, predictions or execution ledgers. I have not run MIFlu training. Repository findings below are static observations and numerical checks of displayed CSV contents; they are not an executed reproduction or a completed identity audit of your snapshot.

## 1. Diagnosis and defensible current claims

### Three distinct studies

| Study | Data and protocol | Question and permissible claim |
| --- | --- | --- |
| A. Exact reproduction target | Fixed author dataset, original model, original experiment definitions, recoverable original settings | Can the published national MIFlu results be independently recovered? Exactness remains a target until ambiguities are resolved. |
| B. Refreshed-data benchmark | Your immutable July 2026 snapshot, explicit preprocessing and common evaluation contract | How do the audited implementations compare on this particular data vintage? A different vintage does not invalidate an internally fair comparison. |
| C. Extended Test/Holdout generalization | A declared historical or later calendar interval, with models frozen before its first use | How well do frozen candidates generalize to another period? Independence is determined by exposure and selection history, not by a folder name. |

Your previous three-model Test comparison belongs to B/C if its implementation and isolation checks pass. It does not establish exact reproduction of A. The author and project Test periods may overlap in calendar time, so they must not be counted as independent replications of one another.

### What the author data actually show

Both author CSVs contain **966 observations**, seven numeric fields and a date column. Every parsed date and all **6,762 numeric cells** match between the two files. Differences include headers and date-string formatting. The stored dates form a regular seven-day sequence from **2002-01-01 to 2020-06-30**. These are stored labels; their correspondence to CDC observation weeks still needs provenance verification. Do not silently replace them with epidemiological weeks. [Processed CSV](https://github.com/Jmoon3108/MIFlu/blob/main/dataset/illness/national_illness.csv?plain=1), [original CSV](https://github.com/Jmoon3108/MIFlu/blob/main/dataset/illness/national_illness_orig.csv?plain=1).

The paper describes national data as 2002-2021. Several Table II statistics closely agree with the released file: weighted ILI mean 1.851286, age 0-4 mean 3434.813665, and provider mean 1608.261905. This is strong evidence linking the released values to the paper, while leaving its date description unresolved. It is not proof that the complete published evaluation used this exact executable pipeline. Source: supplied MIFlu PDF, Table II and Section V.A.

The entry point defaults to `national_illness.csv`, and the embedding notebook reads that file too. This answers which file the released default path uses. Publication commands or author confirmation are still needed to establish which file and overrides generated the tables. Because the two CSVs have identical parsed values, renaming `_orig` alone cannot explain a performance difference. [Entry point](https://github.com/Jmoon3108/MIFlu/blob/main/main_ILI_lora.py), [notebook](https://github.com/Jmoon3108/MIFlu/blob/main/text_emb.ipynb?short_path=2e76a6b).

### Released-code findings that must precede training

| Finding | Evidence and consequence | Required verification |
| --- | --- | --- |
| Text may have no route to predictions | In `models/GPT4TS_lora.py`, line 139 appends text after time-series tokens; line 145 retains only the earlier patch tokens. Standard GPT-2 causal attention prevents those earlier outputs from using later text. | Fixed-weight, evaluation-mode text substitution and gradient tests. This is a strong static inference, not an executed test. |
| Test appears to cover only feature 0 | `Dataset_Custom.__getitem__` derives a feature index from the sample index. Training/validation lengths multiply by seven; Test length does not. With the default factory, every Test feature index is therefore zero. | Enumerate `(origin, feature)` coverage before batching; inspect the actual batch and prediction dimensions. |
| Test participates in epoch inspection and best-result tracking | The entry point evaluates Test every epoch, records a best result using Test MSE, and comments out validation early stopping. The reported mean and the saved best result also follow different paths. | Trace which outputs were used in the paper; distinguish legacy replay from a validation-selected benchmark. |
| Batch handling changes scored examples | The factory defaults to dropping incomplete Test/validation batches and shuffles validation. | Save exact scored keys. Clean evaluation must retain every eligible example and weight by observations. |
| Prompt reconstruction is incomplete | The notebook uses a placeholder prompt. Its saved filename differs from the forecasting model's expected cache name. Non-GPT embedding filenames in the loader use a different date suffix from the visible BERT/LLaMA files. | Recover exact prompts, tokenizer/model revisions, shapes and generation settings; never infer cache meaning from filenames. |
| Freeze and checkpoint semantics need checking | The non-PEFT GPT-2 branch does not explicitly freeze other parameters; the stored best state is not explicitly copied. | Print trainable parameter names; verify a saved state remains unchanged after later optimizer steps and survives reload. |

Sources: [model](https://github.com/Jmoon3108/MIFlu/blob/main/models/GPT4TS_lora.py), [loader](https://github.com/Jmoon3108/MIFlu/blob/main/data_provider/data_loader.py), [factory](https://github.com/Jmoon3108/MIFlu/blob/main/data_provider/data_factory.py), [scoring helper](https://github.com/Jmoon3108/MIFlu/blob/main/utils/tools.py), [entry point](https://github.com/Jmoon3108/MIFlu/blob/main/main_ILI_lora.py), [embedding assets](https://github.com/Jmoon3108/MIFlu/tree/main/dataset/illness/text_emb). GPT-2's causal behavior is documented by [Hugging Face](https://huggingface.co/docs/transformers/model_doc/gpt2); the checkpoint-reference issue is documented by [PyTorch](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html?highlight=state_dict).

A change in training loss after removing text would not resolve the causal-attention concern: different sequence lengths can change dropout random-number use. Test equal-length, different-content embeddings with fixed weights, disabled dropout and unchanged time-series inputs. Also inspect the gradient of forecasting loss with respect to text embeddings. Do not call a prefix-text repair an unchanged reproduction.

The visible repository is **not a self-contained package for all paper results**: the paper's regional experiment, complete comparison-model suite, exact table-producing commands and full prompt provenance are not all established by the supplied tree. The paper explicitly imports baseline results from prior publications (Section V.C). Reproducing its MIFlu column and rerunning every baseline are separate work packages. A clean-environment import check is also needed, including the top-level `embed` dependency referenced by the model.

### Issues in the existing project report

1. The report states 717/102/206 split rows, but elsewhere places validation through index 819 and the first Test target at 820. The author's integer rule applied to 1,025 gives **717/103/205**, with Test indices 820-1024. The reported Test window counts match the latter split. This may be a reporting error; trace the executable indices before concluding leakage.
2. Claimed training/validation window counts of 613/103 are independent of horizon. A complete-target, stride-one split should have horizon-dependent counts. Training targets extending into validation, or validation targets extending into Test, would be substantive contamination even if no function named `test()` was called.
3. A continuous MMWR Sunday grid from 2002w01 to 2021w52 has 1,044 weeks, not 1,025. If those endpoints are accurate, explain the 19-week difference through the raw extraction and filtering log. Do not assume missing weeks are harmless or compress them into adjacent observations.
4. The report's confidence intervals are across ten training seeds on one historical series. They do not establish uncertainty over new seasons. The deterministic baseline has no seed variance, but does have temporal forecasting uncertainty.
5. Non-significant component removals do not demonstrate zero contribution or equivalence. A small-sample negative control cannot establish absence of useful information.
6. Its representative peak curves use lead-one predictions from models trained for different output lengths. These curves do not demonstrate peak forecasting 24-60 weeks ahead.
7. An NLinear win over full MIFlu is an architecture-level comparison, not an estimate of the marginal effect of adding text to MIFlu. Calling that marginal text value negative is unsupported.
8. Seasonal Naive's failure in one window does not mean seasonal forecasting is not forecasting. Replace such wording with a result restricted to the evaluated interval.

These statements come from the supplied Chinese report, especially pages 2, 3-4, 7, 10-12. Its claimed audit passes are reported evidence, not independently verified logs.

### What can still be said

Subject to the audit, the archived comparison reports NLinear 2.739, GPT-2 MIFlu 3.051 and Seasonal Naive 4.279 for average standardized MSE over four horizons. NLinear's point estimate is about **10.2% lower than MIFlu** and **36.0% lower than Seasonal Naive** on that fixed evaluation. It does not establish superiority over all eight models or over LLMs in general. The interval includes pre-pandemic and pandemic years; calling the whole period COVID-era should not obscure that mixture.

Why the validation ranking could reverse remains a set of hypotheses: period-specific seasonality, changes in reporting and patient volumes, data revisions, model capacity, selection optimism after many experiments, different loss emphasis across variables, and implementation differences. Text can help a MIFlu variant relative to its own ablation while that full variant still loses to NLinear. Neither proposition contradicts the other.

## 2. Phased recovery plan

| Phase | Work | Exit evidence and next decision |
| --- | --- | --- |
| 0. Preserve, immediately | Archive raw snapshot, processed CSV, commits, environments, configurations, prompts, checkpoints, predictions, metrics and access ledgers. Hash originals. Add an append-only correction/status note. | Each existing result receives a dataset/protocol/model identity and exposure status. No deletion or replacement of old numbers. |
| 1. Data and index audit, first priority | Compare author CSVs with the frozen July raw and processed data; verify calendar and variable mapping; enumerate every input and target index. | A machine-readable identity report, difference tables and rerun decision. No GPU training needed. |
| 2. Executable audit | Pin author code; smoke-test imports, channels, text influence, parameter freezing, checkpoint restoration, metrics and batch coverage on synthetic or development data. | Every discrepancy classified as reporting-only, evaluation-only, training-affecting, or unresolved. |
| 3. Focused reproduction pilot | Recover paper settings. Separate legacy replay and documented repairs. Use MIFlu, its matched no-text control and NLinear, with both naive references. | Small, fixed run matrix and paper-versus-run results with explicit discrepancies. Stop accuracy hunting if provenance remains unresolved. |
| 4. Benchmark completion | Reuse audited valid artifacts. Repair and rerun only affected cells. If broad comparison is required, include canonical model implementations under the common protocol. | Frozen candidate/configuration list, outputs, seeds, budget and evaluator before final evaluation. |
| 5. Generalization and report | Preserve old Test findings; evaluate new frozen claims on an untouched interval where feasible. Reanalyze saved losses with temporal dependence acknowledged. | Separate reproduction, refreshed benchmark and generalization tables; claim/status matrix and limitations. |

Before the next meeting, aim to finish Phases 0-2 and a small validated pilot if compute permits. A concrete discrepancy report is more informative than a large rerun with unresolved data or code semantics. Treat the dates in the supplied planning chart as planning inputs; this review has not independently verified university deadlines.

## 3. Rerun decision tree

Start with each result's dependencies: data, split, transform, prompt, architecture, checkpoint selection and metric code. Follow the first applicable branch, then propagate the required action to every dependent experiment.

| Decision | If yes | If no |
| --- | --- | --- |
| Q1. Can the original data, configuration and prediction/checkpoint provenance be established? | Go to Q2. | Keep the result as provenance-incomplete exploratory evidence. Reconstruct only what is needed for a new reliable result; do not invent missing provenance. |
| Q2. Is there shared training contamination, wrong targets, invalid chronology, or a transform fitted with prohibited future information? | Retrain all affected models and descendants, including validation selection. If shared, this can require a full affected-benchmark rerun. | Go to Q3. |
| Q3. Is the defect confined to evaluation, aggregation, units, plotting or confidence intervals? | Recompute from saved predictions. If inputs/checkpoints are valid but predictions are missing, rerun inference. Preserve an amended-evaluation label. | Go to Q4. |
| Q4. Does only one model's implementation differ materially from its claimed architecture? | Relabel the old implementation; rerun the corrected model and its matched controls. Unaffected models can be reused when evaluation keys match. | Go to Q5. |
| Q5. Is the snapshot different but internally consistent and leakage checks pass? | Retain B/C. Add A on author data. Use a matched-overlap bridge to measure vintage effects; no automatic full rerun. | If only formatting or headers differ, harmonize audit views and retain valid runs. |

Changing the training row set, chronological cutoffs, scaler, prompt statistics or forecast targets usually requires retraining affected learned models. Cropping already-computed valid predictions to a new reporting subset normally does not. A pure label permutation can sometimes be corrected without retraining, but only if tensors, scalers and semantic text are demonstrably consistent.

Recomputing an already-open Test set is allowed for correction and transparent reanalysis. It cannot restore its status as unseen evidence. If a bug affected training or model selection, a corrected result on the old Test is an amended retrospective result; fresh confirmation needs a genuinely untouched interval.

## 4. Data identity audit specification

### Required inputs and immutable identities

Use both author CSVs at the pinned commit; the original July API JSON/CSV response; the exact 1,025-row processed file; preprocessing code; query parameters; retrieval timestamps; and relevant manifests. The planning PDF reports retrieval on 15 July and local update on 18 July 2026: verify both against files/logs. Do not overwrite them with a current API query.

Record byte SHA-256, byte size, encoding, row/column counts, order, null conventions and a canonical semantic hash after documented parsing. Byte inequality can reflect formatting; semantic equality needs an explicit week and variable mapping. Keep raw and canonical files separate.

### Seven-variable contract

| Author column | Original author header | Expected FluView field | Unit / interpretation |
| --- | --- | --- | --- |
| 1 | % WEIGHTED ILI | `wili` | Percentage of visits, population-weighted |
| 2 | %UNWEIGHTED ILI | `ili` | Percentage of visits, unweighted |
| 3 | AGE 0-4 | `num_age_0` | ILI visit/case count, ages 0-4 |
| 4 | AGE 5-24 | `num_age_1` | ILI visit/case count, ages 5-24 |
| 5 | ILITOTAL | `num_ili` | Total ILI count |
| 6 | NUM. OF PROVIDERS | `num_providers` | Reporting-provider count |
| OT | OT | `num_patients` | Total patient visits, the ILI-percentage denominator |

The project side of this mapping remains to be verified from the raw field names and processing code. `OT` is not `ILITOTAL`. In the author file, `100 * column_5 / OT` reproduces column 2 to a maximum absolute residual of approximately 0.000005 percentage points, supporting the denominator interpretation. ILI is a surveillance syndrome, not laboratory-confirmed influenza. Field definitions and vintage controls are documented in the [FluView API](https://cmu-delphi.github.io/delphi-epidata/api/fluview.html).

### Audit operations and outputs

1. **Calendar:** establish observation epiweek separately from issue/release date and retrieval date. Check MMWR versus ISO conventions, Sunday/Tuesday/Saturday labels, year boundaries and week 53. Identify synthetic timestamps or dropped weeks. Do not align by row index, truncate to the shorter file, or select a time shift because it maximizes correlation.
2. **Coverage:** report each source's unique observation weeks, duplicates, gaps, overlap, source-only weeks and contiguous segments. Investigate the reported 1,025 versus 1,044 discrepancy. A horizon of 60 rows is 60 weeks only if the calendar is valid.
3. **Semantics:** verify definitions, age bands, population/region aggregation, percent versus proportion, column order, count versus rate, and treatment of unknown/missing ages. Map national `nat`, not an accidental regional or imputed series.
4. **Values:** join by verified observation week, compare all seven variables, and emit exact-equality counts, numerical-equality counts, precision-equivalence counts, missingness disagreement, first/last mismatch, max/median absolute difference and relative differences with an explicit zero rule. Require exact equality for integer counts; distinguish decimal serialization noise from source rounding and actual revisions.
5. **Tolerance:** derive tolerance from documented storage/source precision, never from an accuracy result. A binary-parsing check and a source-rounding check are separate. Report the residual distribution even when a tolerance passes. High correlation does not establish identity.
6. **Preprocessing:** reconstruct every filter, sort, deduplication, interpolation, imputation, outlier operation, scaling and row drop. Missing targets must not become fabricated labels. Any new imputation must be causal and documented; record masks and score only eligible observed targets.
7. **Vintage:** retain available `issue`, `lag` and `release_date` fields. The legacy API uses current issues if neither issue nor lag is specified, and supports revisions. If historical provenance is absent, label it unknown. A new extraction is a new snapshot, not recovery of the July artifact. [FluView vintage behavior](https://cmu-delphi.github.io/delphi-epidata/api/fluview.html).
8. **Splits and windows:** write one row per `(split, origin, horizon, feature)` with all input/target bounds and calendar dates. Check label disjointness across train/validation/Test, full target containment, scaler fit rows and prompt-statistic fit rows. Historical input context crossing an earlier split boundary is permitted; future targets crossing a boundary are not.

Deliver `dataset_manifest.json`, `feature_mapping.csv`, `coverage_audit.csv`, `overlap_differences.csv`, `preprocessing_lineage.md`, `window_manifest.parquet`, and `data_identity_report.md`. Return one of: byte-identical; semantically identical; precision-equivalent; range-only extension; revised values; changed definitions; calendar inconsistency; or unresolved. Several statuses can coexist by variable or period.

### Separate vintage from added history

First compare the two snapshots on identical verified weeks and variables using fixed calendar cutoffs. Then compare the full July series as a separate extension. For a diagnostic vintage study, hold model/checkpoint/scaler fixed to examine changed inputs or targets; separately refit the same algorithm on each vintage to assess the complete training effect. Do not mix these estimands. Standardized MSE from differently fitted scalers is not automatically comparable across datasets; add common-unit metrics or a declared common reference scaler for this sensitivity analysis.

## 5. Exact MIFlu reproduction specification

### Published national target

The supplied paper's Table V gives:

| Output length L | MIFlu MSE | MIFlu MAE |
| --- | --- | --- |
| 24 | 1.542 | 0.726 |
| 36 | 1.422 | 0.779 |
| 48 | 1.414 | 0.757 |
| 60 | 1.364 | 0.719 |
| Arithmetic mean | 1.4355 | 0.74525 |

Table VIII rounds the average to 1.436/0.745. The paper is not reporting the project's 0.771 validation value. Comparing these numbers directly would mix datasets, splits and potentially target coverage.

### Configuration to recover and lock

| Item | Paper target / required resolution |
| --- | --- |
| Task | National multivariate forecasting, T=104, L=24/36/48/60; independently verify what channels the published scores include |
| Dataset | Author 966-row fixed artifact; verify hash and observation-week semantics |
| Split | Chronological 70:10:20; released integer rule gives 676/97/193 rows and target blocks 0-675 / 676-772 / 773-965 |
| Scaling | Per-variable StandardScaler; released loader fits on training rows; distinguish it from input-window instance normalization |
| Forecasting backbone | First six GPT-2 layers, hidden width 768 |
| Text embedder | Full GPT-2; exact prompt, tokenizer/model revision, token order, token length, embedding cache and generation state must be recovered |
| Patching | Length 24, stride 2, right replication padding; 42 patches at T=104 |
| Fine-tuning | LoRA rank 4 plus the stated position/layer-normalization updates; verify actual trainable parameters and target modules |
| Optimization | Paper: 20 epochs, batch size 16, learning rate 0.0005; recover scheduler, dropout, optimizer details, checkpoint rule and seeds |
| Repetitions | Paper averages ten repetitions; reproduce the original randomization rule if recoverable, otherwise declare the replacement seed list |
| Environment | Paper: Python 3.9.18, PyTorch 2.1.0, RTX 3090; lock compatible Transformers, PEFT, NumPy and pandas versions too |

Source: supplied paper, Table IV and Sections V.B-C; additional code settings must be tied to the pinned files. Defaults are not paper commands: the released entry point defaults to one epoch, learning rate 0.0001, multimodality off and PEFT off. Merely running it without overrides is not the full reported MIFlu model.

### Three clearly labelled implementation states

**A0: released-code replay.** Preserve the source unchanged and record its actual behavior, including defective or uncertain behavior. Run only in an isolated diagnostic namespace on the already-public author benchmark. Its Test-assisted output is not an independent holdout result.

**A1: reconstructed paper configuration.** Apply only documented setting choices and necessary execution fixes. Keep a deviation ledger: source location, reason, exact diff, expected effect and whether author confirmation exists. A missing prompt can be reconstructed from Table X with training-only statistics, but this is a reconstructed prompt, not recovered original text. Do not tune wording to recover the published scores.

**A2: corrected benchmark implementation.** Repair channel enumeration, text visibility, parameter freezing, validation selection, incomplete batches and checkpoint storage as needed. A possible text-visibility repair is prefixing text and reading the subsequent patch positions, but this is a declared algorithm change until confirmed by the authors. Validate it before using it to test textual mechanisms.

For standard complete-target windows before feature expansion or batch dropping, the author split gives:

| L | Training origins | Validation origins | Test origins |
| --- | --- | --- | --- |
| 24 | 549 | 74 | 170 |
| 36 | 537 | 62 | 158 |
| 48 | 525 | 50 | 146 |
| 60 | 513 | 38 | 134 |

Training/validation are channel-expanded in the released loader. A corrected channel-independent evaluator must cover all seven channels for every origin; it can reconstruct an `(origin, lead, variable)` tensor without changing the model into a joint multivariate architecture. Fixing only loader length does not cure the model's batch-times-channel embedding assumptions; test tensor shapes explicitly.

### Reproduction acceptance and minimal reconstruction

Verify the complete contract before looking for numerical agreement. Report all four MSE/MAE pairs, seed dispersion, absolute/relative gaps, evaluated keys and every deviation. Numerical closeness alone cannot prove a correct reproduction.

With exact artifacts and settings, request deterministic agreement where feasible. With different hardware or unrecoverable seeds, define a tolerance before evaluation, justified by repeated-run numerical variability. Because the paper does not provide full per-seed uncertainty, do not manufacture an author confidence interval. If a managerial threshold such as a fixed percentage is used, label it an engineering criterion, not a statistical proof.

Recover missing details in order: committed launch/configuration files and logs; supplementary materials; a concise author inquiry approved by the supervisor; then a documented minimum reconstruction based on the paper and cited parent implementation. Hold out the new generalization set throughout. Missing dependencies can justify a compatibility patch; missing experimental semantics cannot be silently guessed. A robust FYP outcome can be a partially reproduced result with precisely localized blockers.

## 6. What the MIFlu ablations establish, and the redesigned benchmark

### Actual paper evidence

Table VIII reports averages across four horizons:

| Variant | MSE | MAE | MSE change from full MIFlu |
| --- | --- | --- | --- |
| Full MIFlu | 1.436 | 0.745 | Reference |
| Without dataset information | 1.473 | 0.770 | +0.037 |
| Without task instruction | 1.465 | 0.759 | +0.029 |
| Without input-variable description | 1.538 | 0.779 | +0.102 |
| Without LoRA | 1.570 | 0.794 | +0.134 |
| Without multimodality | 1.647 | 0.816 | +0.211 |
| Without LoRA and multimodality | 1.925 | 0.904 | +0.489 |

These are reported improvements within that configuration. They do not provide a universal superiority claim, proof of necessity, or a statistical equivalence test. Table VIII supplies no confidence intervals or hypothesis tests. It removes the textual branch, not the forecasting GPT-2 itself; the last row is described as GPT4TS. Therefore it does not isolate the benefit of a pretrained forecasting LLM over an otherwise matched model with no LLM.

The text/LoRA variants form a useful 2-by-2 comparison, but the displayed numbers do not establish positive synergy: the MSE benefit of text is 0.211 with LoRA and 0.355 without it. This difference is descriptive, without uncertainty.

Table VII compares GPT-2, BERT and LLaMA2-7B text embedders while retaining the forecasting system. It supports an empirical embedder comparison, not a general rule that larger text models are better. GPT-2 has the best MSE in all four rows; it does not have the best MAE in every row. Differing representation widths/adapters, training and embedding provenance also matter. The released-code discrepancies prevent treating these tables as already executable evidence.

The supervisor's textual-summary question concerns an input prompt containing dataset/variable/task information, not the written FYP project summary. Much of that prompt is static or derived from the numerical data. It is not an additional independent observation of future influenza.

### Two complementary benchmark questions

**Practical comparison:** which of the declared implementations offers the best accuracy/cost trade-off under a common information set? Use seven outputs, T=104, the four horizons, identical eligible forecast keys, a common training-only scaler, the same loss definition, and explicit chronological cutoffs. Architecture-specific operations such as instance normalization remain part of the method and are disclosed.

**Mechanism comparison:** within the same MIFlu implementation, what changes when text, LoRA or pretraining is removed? Use identical data, origins, training budgets and documented parameter-freezing rules. Do not substitute NLinear for a no-text MIFlu control.

For mechanism work prioritize full MIFlu, no text with LoRA retained, no LoRA with text retained, and neither. Then add matched constant/neutral text or equal-length control embeddings to separate semantic content from additional tokens/positions. Randomly shuffling examples is ineffective when every example has the same static prompt. A text-influence test must pass before interpreting semantic ablations.

To investigate the forecasting LLM itself, compare pretrained and randomly initialized backbones under a carefully declared adaptation budget, and a dedicated time-series replacement where feasible. A frozen random backbone answers a different question from a trainable random backbone. No single replacement perfectly holds all architecture and pretraining factors constant.

### Common benchmark rules

Lock training information, input/output shapes, origin lists, scaler, metric weighting, run keys, seed list and validation access. Give each architecture a sensible published starting configuration and an equal declared tuning opportunity, such as an equal trial cap and a per-trial hardware/time cap. Identical learning rates or epoch counts are not inherently fair across different optimizers and architectures. Count all development trials in the budget.

Separate a method-faithful comparison from an explicitly resource-constrained comparison. Record total parameters, trainable parameters, adapter/head parameters, precision/quantization, peak VRAM, train time, inference time, embedding preparation and total search cost. A million trainable parameters is not a million-parameter total LLM; compare like quantities.

Use the loss over seeds, not the loss of a seed-averaged forecast, as the default repeated-training result. An ensemble is a separate method. Retain failure/OOM records and apply a predeclared retry/exclusion rule; never replace poor seeds selectively.

## 7. Model selection and Qwen/DeepSeek recommendation

| Model | Scientific role | Recommendation |
| --- | --- | --- |
| NLinear | Strong low-cost baseline using a last-value normalization idea | Retain; essential practical comparator, not selected merely because it won the old Test. |
| DLinear | Decomposition-based linear baseline | Retain; a useful complementary simple baseline. |
| PatchTST-inspired | Custom patch-based implementation | Archive and report under its actual name. Add canonical PatchTST before making claims about PatchTST itself. |
| iTransformer | Dedicated time-series transformer with a different tokenization design | Retain if the implementation passes a fidelity review. |
| GPT-2 MIFlu | Original research target and multimodal component study | Mandatory; distinguish author replay, local implementation and repaired variants. |
| Qwen Time-LLM | Reprogramming method with a specified Qwen backbone | Retain as an adaptation if verified; record exact Qwen ID/revision, size and deviations from Time-LLM. |
| CALF | Cross-modal fine-tuning/alignment approach | Retain if its principal alignment modules and losses are implemented; otherwise label an adaptation. |
| TimeCMA | A distinct cross-modality alignment approach | Retain subject to the same fidelity and input-information audit. |
| Last Value / Seasonal Naive | Low-cost forecasting references | Always report both in the new benchmark. |

Canonical references: [PatchTST](https://github.com/yuqinie98/PatchTST), [iTransformer](https://github.com/thuml/iTransformer), [Time-LLM](https://github.com/KimMeen/Time-LLM), [CALF](https://github.com/Hank0626/CALF), [TimeCMA](https://github.com/ChenxiLiu-HNU/TimeCMA). These references establish method identities; they do not certify the project's implementations.

Four models per family is a balanced presentation choice, not a scientific sampling design. The models are deliberately chosen and heterogeneous. Do not average their scores and treat the eight architectures as independent random samples from all possible LLM/non-LLM models. State conclusions about the selected methods and the selection procedure.

**Do not add DeepSeek to the core recovery run.** Fix provenance and the MIFlu comparison first. A modern model is valuable only when tied to a specific question and affordable implementation, not because its brand is newer.

If resources remain, add one separately labelled backbone sensitivity study. A verified small option is `Qwen/Qwen3-0.6B-Base`, whose official card describes a 0.6B causal pretrained model. Use it inside a fixed forecasting adapter, with no chain-of-thought generation, and disclose the parameter/architecture differences from GPT-2. This is an example, not a claim that it is the newest Qwen release or that it is size-matched to truncated GPT-2. [Qwen model card](https://huggingface.co/Qwen/Qwen3-0.6B-Base).

`DeepSeek-R1-Distill-Qwen-1.5B` is derived from Qwen2.5-Math-1.5B. It is not an independent DeepSeek backbone architecture. Comparing it with its parent would investigate checkpoint/post-training differences. Full DeepSeek-R1 is a much larger MoE model and is unsuitable as a routine architecture-matched addition here. [DeepSeek model card](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B).

Any optional comparison must lock numerical history, text information, tokenizer/prompt rules, effective token count, context use, forecast head, tuning trials and compute cap. Audit positional embeddings, attention masks, hidden widths, LoRA module names and frozen layers. Equal layer counts do not mean equal capacity. A black-box chat API lacks the same hidden-state/training interface and belongs in a separate forecasting task, if studied at all.

Record checkpoint release dates and known pretraining coverage. Modern checkpoints postdate much historical Test data; this creates a possible pretraining-contamination limitation, not proof of memorization. Historical retrospective results with such checkpoints are not simulations of models actually available in 2018.

## 8. Leakage-safe validation and Test protocol

### All eight models or selected representatives?

Both designs are valid, but answer different questions. For a broad benchmark, **freeze all included architectures before evaluation, choose each one's configuration using validation only, and evaluate all once in one final release**. Use validation to select hyperparameters/checkpoints, not to suppress inconvenient Test rows. Predeclare the main MIFlu-NLinear and component contrasts; treat other pairwise comparisons as secondary.

For the minimal-compute FYP, validation can select a pre-specified representative from each family. Then the Test comparison estimates the performance of those selection procedures and representatives, not an eight-model Test ranking. Your existing three-model experiment fits this narrower design if its prior freeze is verified.

The old holdout has already been seen. Scoring remaining frozen models on it now can be a useful retrospective extension, but must not be presented as the original pre-specified one-time eight-model comparison. New architecture choices motivated by that result need fresh confirmation.

### Forecast-window contract

Use zero-based inclusive indices. Let the last input index be `o`. Input is `[o-103, ..., o]`; target is `[o+1, ..., o+L]`. A target belongs to split `[a,b]` only if `o+1 >= a` and `o+L <= b`. Assert that training, validation and Test target sets are disjoint. The same observed historical point may be both an earlier target and a later forecast input; that is normal rolling-origin forecasting.

With 1,025 rows and the author's rounding rule, the expected split is 717/103/205 and the complete-target counts are:

| L | Training origins | Validation origins | Test origins |
| --- | --- | --- | --- |
| 24 | 590 | 80 | 182 |
| 36 | 578 | 68 | 170 |
| 48 | 566 | 56 | 158 |
| 60 | 554 | 44 | 146 |

These are audit expectations for that explicit rule, not a retroactive instruction to silently change the old project protocol. Explain any different result through the original window builder.

### Freeze and exposure rules

1. Keep the old results immutable and mark the old holdout as exposed. Audit logs must record actual consumed timestamps across all code paths, including preprocessing and prompt generation.
2. Use chronological development folds. Prefer multiple expanding-window validation periods when affordable, with all forecast targets contained in their assigned blocks. Purge crossing target windows. A 104-week blanket embargo is unnecessary merely because historical inputs overlap; availability and target containment are the relevant constraints.
3. Fit scalers, imputers, learned preprocessing and global prompt statistics only on the permitted training period. Window statistics may use the observed input window. Never compute global extrema, trends, seasonal descriptions, PCA over series data, or generated summaries using future labels.
4. Select on a fixed primary validation loss, with a deterministic tie rule such as lower measured development cost then a fixed model identifier. Lock seed aggregation, failed-run treatment and all configurations.
5. For the simplest auditable recovery, do not refit on train plus validation. If refitting is desired, specify the training duration and transform refit rule before Test, and apply it consistently. Recompute prompts/scalers from that permitted training pool.
6. Freeze data hashes, target masks, model revisions, checkpoints, prompts, evaluation code and the full run matrix in a signed-off manifest before any new Test scores are revealed. A two-stage evaluator can generate predictions and reveal metrics only after all run keys pass integrity checks.
7. A new holdout can be a genuinely unexamined later interval, potentially after 2021 if available. Choose its dates before inspecting outcomes. Audit all earlier exposure, including notebooks and plots. Historical periods already inspected cannot become fresh by renaming them or changing random seeds.
8. A July-revised retrospective series is not an as-of-real-time benchmark. For operational claims, reconstruct each input at the issue available at forecast time, including reporting lag, and define a fixed mature-target vintage. If that cannot be reconstructed, state the retrospective limitation.

Test inputs from earlier Test dates are allowed in a rolling-origin evaluation once those observations would have been available. Weights and hyperparameters remain fixed. That is distinct from a single 60-week forecast issued at the beginning of the entire holdout. Label both the issue date and lead for every prediction.

For Seasonal Naive beyond 52 weeks, use only the observed last seasonal cycle. With an origin at `o`, define the 52-week repeating forecast as `y[o-51+((k-1) mod 52)]` for lead `k`. Do not use actual `y[o+k-52]` when `k>52`, because it lies after the origin. Declare how a 53-week epidemiological year is handled; a row-based 52-week benchmark and an epiweek-aligned seasonal baseline are different definitions.

One-time Test use means no adaptive feedback into model design, not a prohibition on checking saved predictions or correcting documented arithmetic errors. Keep every post-release change in the amendment log.

## 9. Statistical analysis plan

### Primary quantity and retained evidence

Save predictions and targets with `(dataset_id, protocol_id, model_id, checkpoint_id, seed, origin_week, lead, target_week, variable, vintage, mask)`. Retain both standardized and original units, or enough information to reproduce both.

For model m, seed s and horizon L, define MSE as the mean squared standardized error across eligible origins, all leads 1..L and seven variables. Average that MSE across seeds; then average the four horizon values with weight 1/4 each. MAE is the analogous secondary metric. This preserves the project's declared estimand. A longer horizon must not gain extra aggregate weight simply because it contains more lead cells.

Report per-horizon MSE/MAE and a variable-by-horizon table. Add original-unit errors for weighted ILI, unweighted ILI and ILITOTAL individually; do not average unlike raw units. Baseline-relative skill can be `1 - MSE_model/MSE_reference`, with reference and aggregation declared. Do not pool raw standardized scores across different data vintages without addressing scaler differences.

### Separate two kinds of uncertainty

**Optimization variability:** mean, SD and an explicitly conditional interval across seeds on the fixed historical evaluation. The existing seed tests may be retained with this restricted interpretation. Numeric seed labels alone do not guarantee meaningful common-random-number pairing across architectures. They are not independent future seasons.

**Temporal variability:** compute paired model loss differences at common forecast origins. Resample blocks of consecutive origins, applying the same sampled blocks to every model, variable and seed. This preserves much more dependence than treating every origin-lead-variable cell as independent. Choose the block rule from development data; for the aggregate up-to-60-week trajectory loss, a primary block length of at least 60 origins is a reasonable proposed starting point, with a predeclared longer-block sensitivity such as 104. It is a proposal, not a universal optimal length. Dependent-data bootstrap foundations are described by [Politis and Romano](https://statistics.stanford.edu/technical-reports/stationary-bootstrap).

Average losses over seeds before the primary temporal resampling if the target is expected performance over training randomness. If also resampling seeds, keep an entire fitted seed trajectory together and disclose the two-level procedure. Never resample each prediction independently.

For the old unequal origin sets across horizons, preserve their original weights using a shared origin timeline and horizon-validity masks. Report a separately labelled common-origin sensitivity analysis. For a new protocol, a common set of origins eligible for L=60 makes cross-horizon aggregation and pairing simpler; also report all-eligible-origin scores for transparency. Changing origin sets changes the estimand.

The old Test has only 146 common origins at L=60 and spans roughly four seasons. Blocks of length 60 leave very few effective blocks. COVID-related nonstationarity also weakens stationary-bootstrap assumptions. Treat resulting intervals as conditional sensitivity analyses; do not manufacture precision by shortening blocks until significance appears. Show year/season-level differences and individual trajectories even if formal inference is inconclusive. A deterministic naive forecast still has temporal uncertainty under this analysis.

### Hypotheses and multiplicity

For a fresh frozen study, prioritize (i) full MIFlu versus NLinear and (ii) full versus matched no-text MIFlu. If improvement over Seasonal Naive is also confirmatory, add it explicitly before release. Predefine direction or use two-sided differences, report effect sizes and confidence intervals, and apply Holm correction across the declared primary family. Per-horizon, per-variable, peak and additional-model comparisons are secondary; mark exploratory analyses and control their multiplicity where inferential claims are made.

A Diebold-Mariano-style comparison of origin-level loss differences with dependence-robust variance can be a sensitivity analysis if assumptions and sample size support it. For a multi-lead aggregate, blindly setting the variance lag to L-1 is not sufficient; serial/seasonal dependence may persist longer. Do not use such a test to override weak temporal evidence.

Non-significance is not equivalence. An equivalence claim requires a predeclared practical margin and enough information to estimate the difference tightly. The current holdout's new analyses are post hoc even if their calculations are rigorous.

### Peaks and visual interpretation

Distinguish output length L from forecast lead k. Use fixed-origin forecast trajectories or clearly labelled fixed-lead curves. Lead-one curves from an L=60 model are one-week-ahead evaluations. For within-window peaks, predefine argmax/tie handling, peak-timing error, intensity units, boundary-censored peaks and near-zero denominators. For seasonal peak claims, use calendar-defined seasons and origins whose forecast spans the required period; incomplete seasons cannot demonstrate full-season peak accuracy. Treat these as secondary rather than retroactive selection criteria.

## 10. Minimal-compute and full-compute execution

### Minimal-compute plan

1. Finish the CPU data/index audit and recompute existing metrics and intervals from saved predictions. Reuse all passing artifacts.
2. Run synthetic/development smoke checks, then one short L=24 and one L=60 training smoke test of the chosen MIFlu variant. These are engineering checks, not accuracy evidence.
3. For a focused author-data pilot, freeze full MIFlu, matched no-text MIFlu and NLinear across four horizons and three seeds: **36 learned fits**, plus eight deterministic reference evaluations. If only 18 fits are affordable, use the same three configurations at L=24 and L=60 and label it a two-horizon pilot; do not report an average over four horizons.
4. If the existing July implementation and evaluation pass, retain those results. If the audit identifies a localized defect, add only its affected reruns. Do not automatically repeat all 580 validation rows or 84 Test runs.
5. Use the paper Test only for the labelled reproduction/reanalysis track. Any remaining genuinely untouched generalization interval stays sealed until the protocol is fixed.

Three seeds do not reproduce the paper's ten-repetition aggregate. They provide a feasibility and discrepancy pilot. The full/no-text pair takes priority over a new DeepSeek implementation because it addresses the supervisor's mechanism question directly.

### Full-compute plan

1. Complete the national MIFlu reproduction target at four horizons and ten repetitions: 40 fits per implementation state actually approved for numerical reporting. Do not multiply this across speculative patches.
2. Complete the 2-by-2 text/LoRA experiment under the corrected protocol: 4 configurations x 4 horizons x 10 seeds = 160 fits, including full MIFlu. Account for overlap with previous fits rather than counting twice.
3. Complete the eight-model benchmark on each required dataset track: 8 x 4 x 10 = 320 final-configuration fits per track, excluding tuning. Add two naive references. Include canonical PatchTST as a replacement in the core suite, preserving the inspired version in the archive or appendix.
4. Add the matched-week vintage bridge using a small prespecified subset of models; expand only if the differences warrant it. Add several chronological development folds if feasible and freeze the final comparison afterward.
5. Add one modern-backbone sensitivity only after the main study is complete. Regional reproduction, few-shot work and the full original baseline table are separate optional scope extensions.

Estimate wall time from measured pilot runs using `sum(number_of_fits * measured_time_per_fit)` plus tuning, embedding preparation, evaluation and queue overhead. Track peak VRAM and failed attempts. Do not extrapolate every model from NLinear's reported five-second runtime, or promise completion before checking hardware. Set a supervisor-approved GPU-hour cap and stop rules before launching the full matrix.

## 11. Next meeting and final FYP structure

Use a seven-page meeting brief or seven slides:

1. **Research question:** reproduce the national MIFlu claim and assess its generalization against credible time-series baselines.
2. **Verified data facts:** both author files have 966 matching rows; stored dates end in June 2020; the July project overlap remains to be audited. Show the seven-field mapping and coverage timeline.
3. **Existing result and scope:** Test point estimates for the three frozen models, with the exact calendar period and seven-output aggregation. Put validation selection details in an appendix.
4. **What the paper ablates:** Table VIII and the distinction between full-versus-no-text and full-MIFlu-versus-NLinear comparisons.
5. **Executable discrepancies:** text visibility, channel coverage, selection and prompt provenance. State which are statically observed and which have now passed executable tests.
6. **Recovery evidence:** data audit status, a paper-versus-reproduced table with pending cells left pending, and the minimal run budget. Never populate planned results with guessed numbers.
7. **Decisions requested:** scope, corrected-method naming, final Test design, inference strength and compute cap.

A suitable spoken explanation is: the previous comparison used a different fixed data vintage, so it evaluates generalization under the project protocol. It does not by itself contradict the paper's within-MIFlu text ablation. The recovery work will establish data identity, check the public implementation and reproduce the national experiment separately.

For the final FYP, use chapters for motivation/questions; paper and reproducibility evidence; data identity and provenance; experimental protocol; author-data reproduction; refreshed-data benchmark; holdout generalization; component/cost analysis; and limitations/conclusion. Include appendices for implementation deviations, window manifests, frozen plans, exposure history and amended results. The contribution can be a reproducibility diagnosis and carefully bounded generalization study even if MIFlu's table cannot be exactly recovered.

## 12. Questions requiring supervisor decisions

These decisions should be resolved before the affected scientific runs, while preservation, read-only auditing and smoke checks can proceed immediately.

1. Is national forecasting the required reproduction scope, or are regional, few-shot and the entire imported-baseline table also required?
2. Is a clearly documented partial reproduction acceptable if original prompts, evaluation semantics or author settings cannot be recovered?
3. Should the main corrected method use an explicitly repaired text path, and what name distinguishes it from the released MIFlu implementation?
4. Is the project's primary target all seven standardized outputs, weighted ILI alone, or ILITOTAL? Keep secondary targets separate and do not change the primary based on old Test rankings.
5. Is the final claim about all eight implementations, or about validation-selected representatives under a limited budget?
6. What genuinely unexamined period is available for new confirmation? If none is available, is a transparent retrospective extension acceptable without claiming a new untouched Test?
7. Is the intended claim retrospective accuracy on a fixed revised snapshot, or operational as-of forecasting with reporting delays and historical vintages?
8. Should new final models be refitted on train plus validation, or should the already-selected training-only checkpoints remain the standard?
9. What tuning budget, total GPU-hour cap, reproduction tolerance and practical improvement/equivalence margin should be fixed?
10. May an author inquiry be sent requesting commands, prompt provenance and clarification of code/table discrepancies? Prepare it first; do not send without authorization.
11. Is canonical PatchTST required in the core suite, with the inspired implementation retained as an adaptation?
12. Should the optional modern-Qwen or DeepSeek-distillation study be excluded until the core work is complete? Recommendation: yes.

## 13. CodeBuddy execution prompt

Use the accompanying `CodeBuddy_MIFlu_Recovery_Prompt.md`. It gives CodeBuddy a phased, audit-first execution contract with explicit preservation rules, acceptance evidence, computation gates and claim boundaries. The complete prompt follows in the PDF and can be copied from the separate file.

