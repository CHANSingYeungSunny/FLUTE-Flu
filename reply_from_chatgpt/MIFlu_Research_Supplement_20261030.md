# MIFlu research audit and exploratory benchmark supplement

Date: 30 October 2026 (Hong Kong). Status: **PARTIAL_REPRODUCTION**.

This is an evidence supplement to the single historical authoritative report, **not a replacement final report or a submission-ready manuscript**. The original DOCX and its MD mirror are unchanged. This supplement records newly verified facts, contradictions, and separately labelled exploratory experiments. It does not promote a new Track C champion. `UNIFIED_PAIR_KEY=966|L24|seed42` is retained as the supplied reference anchor; each other cell has its own real horizon/seed key. It is not a license to relabel every cell L24/seed42.

## Abstract

We audited the supplied MIFlu handoff, independently rescored all 12 packaged MIFlu test prediction files, and ran 132 new CPU model cells plus 12 exploratory hybrid evaluations on the unmodified author-966 dataset. The archived Track C mean seven-variable z-space MSE is 1.8652; the paper Table V mean is 1.4355. Their descriptive separation is 29.93%, **not an experimentally identified performance deficit under an identical protocol**. The data are US CDC National-Illness, not Hong Kong surveillance. A scalar ILITOTAL variance cannot denormalize the seven-variable aggregate. MIFlu's independently recomputed ILITOTAL-only mean MSE is 3.7020 z², equivalent to 300071219.8818 patient-count². Existing peak tables use actual lead k=1, not lead L. The packaged event evidence yields 15/36 MIFlu hits, while the user-specified 31/36 CONSENSUS cannot be authenticated because `peak_criteria.json` is missing. A prior scheduler sensitivity experiment changed 1.8561 to 1.8225 in separate Track R; a newly detected one-epoch schedule shift remains untested. The newly executed compact CPU suite includes classical, neural, TimesNet and Autoformer models with NLinear as its only learned linear baseline. All new results are exploratory because the test data were already exposed. New LLM feature/reasoning experiments and exact MIFlu retraining remain blocked by missing weights/code and inaccessible HPC.

## Introduction

The scientific question is whether language-derived context improves influenza forecasts beyond inexpensive numerical predictors, particularly at decision-relevant peaks. A lower aggregate MSE is not equivalent to better timing or intensity at epidemic peaks. Reproducing a reported table, comparing methods on a controlled test contract, establishing a text mechanism, and demonstrating operational utility are distinct research questions.

The correct target-paper title is *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme*, by Moon, Shim, Kim and Hwang, IEEE JBHI 29(10), 7790–7801, DOI [10.1109/JBHI.2025.3561214](https://doi.org/10.1109/JBHI.2025.3561214). The alternative Hong Kong title in the prompt is not the title of that DOI. The supplied paper's Section V-A explicitly identifies US national and US regional data. Current publication metadata was checked against [the authors' institutional record](https://pure.korea.ac.kr/en/publications/miflu-large-language-model-based-multimodal-influenza-forecasting/).

Execution status:

| Part | Status | Evidence / limitation |
| --- | --- | --- |
| A1 | COMPLETED locally | Data, splits, scorer, source/audit contradictions checked |
| A2 | PARTLY BLOCKED | Existing 24-fit R1C recomputed; C2 schedule candidate prepared, not trained |
| A3 | COMPLETED assessment | No causal percent allocation or achievable optimum is identifiable |
| B1 | COMPLETED where identifiable | Target-only MIFlu rescored; other seven target metrics unavailable |
| B2 | COMPLETED | All archived models: per-L scores and normalized profiles; MIFlu actual k also computed |
| B3 | COMPLETED with evidence conflict | 32 archive model-by-L rows; consensus 31/36 cannot be verified |
| B4 | PARTLY COMPLETED | 132 new CPU cells for 11 models + 12 hybrid evaluations; LLM arms not run |
| B5 | PRELIMINARY | Academic analysis and confirmatory protocol; publication claims await validation |

## Related Work

MIFlu uses a frozen GPT-2 text embedder and a truncated forecasting GPT-2, with trainable patch/output projections, positional and layer-normalization parameters, and low-rank attention adapters. The released source implements token concatenation; it is not a cross-attention fusion implementation. The supplied paper compares national baselines largely using values cited from earlier studies, so Table V is not evidence of all methods being retrained under this project's Track C contract.

Kramer and Shaman (2019), [DOI 10.1371/journal.pcbi.1006742](https://doi.org/10.1371/journal.pcbi.1006742), evaluate peak timing within one week and peak intensity within 25% of the observed value. **The joint AND rule is this project's composite application of those two tolerances**; do not imply that the original article establishes this project's greedy peak picker or joint hit rate. The article analyzes forecasts by predicted lead to the epidemic peak, which differs from a model's output-window length.

Our new Autoformer and TimesNet implementations are unmodified model sources from the authors' [Time-Series-Library](https://github.com/thuml/Time-Series-Library), pinned to commit `4e938a1767106324dd753b2a44832bf870a0252e`. TimesNet is an FFT-driven 2D convolution model, not a transformer. Autoformer supplies the requested additional transformer family. Compact capacities, data protocol and training wrapper are disclosed below; these are not claims to replicate either method's original best published score.

## Methods

### Evidence hierarchy and frozen records

The archive contains 161 Python source files, all syntactically parsed in `results/source_inventory.json`. Source/audit checks focused on the author loader, model, trainer, embedder notebook, Track C master/scaler/peak contracts, R1-C trainer/results, canonical scorer and model-fidelity classes. Hashes for every input file appear in `results/input_sha256_manifest.csv`; no input was modified.

Conflicting statements are kept visible. For example, START_HERE says 36/36, the authoritative MD and event tables show 15/36, and the prompt asserts an unavailable 31/36 consensus. The authoritative MD also calls MIFlu a non-LLM model in several passages despite its own table and the model's GPT-2 backbone. These are documented report defects; they are not reasons to overwrite frozen evidence silently. New conclusions must be incorporated by a controlled future revision of the original authoritative DOCX/MD pair and its manifests.

### Dataset, scaling and split verification

Official SHA256: `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`. Independently verified shape: 966 rows by seven finite numerical features, excluding the synthetic date index. The project-schema 966-row copy is a separate byte representation; the 1025-row vintage is excluded from every calculation in this supplement.

Train is [0,676), validation [676,773), test [773,966), matching the released loader's integer 70:10:20 arithmetic. The paper supplies the ratio, not a dataset hash or exact integer boundaries, so exact identity to the unpublished training-time artifact cannot be proved from the paper alone. The packaged data and author CSV bytes match the declared hash. The author date column is a synthetic weekly index: do not equate its apparent 2016–2020 dates with verified CDC surveillance weeks or make calendar-specific COVID claims without an independent mapping.

For every origin o, input is [o−103,o] and target is [o+1,o+L]. All target rows must belong to the selected split. Counts, independently recomputed:

| L | train | validation | test |
| --- | --- | --- | --- |
| 24 | 549 | 74 | 170 |
| 36 | 537 | 62 | 158 |
| 48 | 525 | 50 | 146 |
| 60 | 513 | 38 | 134 |

The persisted scaler is train-only and agrees with a float64 refit to relative tolerance 2e−7. Small float32 rounding differences are documented, not silently refitted away. ILITOTAL mean is 9439.841796875, scale 9003.152343750. The prompt's 9003.15 is rounded. All valid physical calculations below use the packaged full-precision scale. No nonnegative clipping is introduced, because it would alter scores and break simple affine error conversion.

### Model fidelity and training audit (A1)

| Component | Verified evidence | Assessment |
| --- | --- | --- |
| T=104, K=6, patch=24, stride=2 | Author source + R1C configuration | Matched declarations; 42 patches per variable |
| LoRA r=4 | Author `GPT4TS_lora.py` + R1C config | Matched rank; released `c_attn` targets fused Q/K/V, not only Q/K as the paper diagram suggests |
| 20 epochs, batch=16, lr=0.0005 | Paper Table IV; R1C trainer | Matched settings; earlier audits claiming no paper provenance are stale |
| Optimizer / loss | Author main trainer; R1C trainer | Adam / MSE, no warmup found; optimizer is recovered from code, not unspecified everywhere |
| Scheduler | Author main + tools; R1C trainer | Author default end-of-epoch type1 decay; R1C start-of-epoch shift found; no exact corrected result available |
| Selection | Author main trainer selects on test each epoch | Track C deliberately repairs this with validation-only checkpoint selection; never reintroduce test selection to chase 1.4355 |
| Evaluation scope | Author Dataset_Custom length excludes feature multiplier on test | Test returns feature 0 only under released indexing; corrected Track C evaluates all seven. Major protocol mismatch, effect not quantified |
| Repetitions | Paper 10; Track C 3 | Seeds 42/43/44 versus unspecified paper repetition sequence; more runs cannot be assumed to shift the mean toward the target |
| Seed implementation | Author main initializes seed 2021 once before iteration loop | A seed exists; a per-repetition reseeding list does not. Audit language saying no seed call at all is inaccurate |
| Actual corrected Track C model | R1C imports `r1b_model.R1BCorrectedMIFlu` | **Module absent**. `miflu_model.py` is a different reconstruction; the supplied adapter is not evidence that it generated the Track C results |
| Frozen text assets | Four author text matrices included | 317×768 each; static across samples, but NOT identical vectors across tokens. Training-time original embedding hashes/weights not independently supplied |

The author model concatenates `[time_patches, text_tokens]` and retains the time-prefix outputs. Under ordinary deterministic causal attention, later suffix tokens cannot affect retained prefix positions. The paper's figure description instead uses the last patch positions, and its prose/slicing is internally ambiguous. **This is an architectural concern, not a resolution of the recorded GPU/CPU contradiction.** The missing corrected source and matched checkpoints prevent verification of what Track C actually executed.

The generic control in `mechanism_probe.py` numerically verifies suffix independence and a prefix positive control; it does not load pretrained GPT-2 or reproduce the contested GPU trace. Static text can still influence predictions when it is causally accessible, for example as a prefix, or through explicit cross-attention/FiLM; constancy over forecast origins alone does not establish uselessness.

Text asset fingerprints and token variation:

| L | rows | dims | sha256 | max_token_difference | scope |
| --- | --- | --- | --- | --- | --- |
| 24 | 317 | 768 | 837502311354c9ddf71e42fbdf5689b6bbbbd2f00c71055d0d226c3c1f44c0c8 | 300.9852 | static token matrix reused across origins; tokens NOT identical |
| 36 | 317 | 768 | f70d1a141928f1fd65ba78bad30a9a167fa9315a4c22effc291aac2bd593b464 | 300.9852 | static token matrix reused across origins; tokens NOT identical |
| 48 | 317 | 768 | 25bf529f66842df18b09b7dd3f0418347c098f07222e0017fc75e80f3205edd5 | 300.9852 | static token matrix reused across origins; tokens NOT identical |
| 60 | 317 | 768 | fe98826fef910fd3e0316b67b823274b7991084db67524125ac0c4eda29f4ac0 | 300.9852 | static token matrix reused across origins; tokens NOT identical |

### Scoring scope and physical units (B1)

For variable j, MSE_physical,j = MSE_z,j × scale_j² and MAE_physical,j = MAE_z,j × scale_j. MSE is measured in **patient-count²**, MAE and RMSE in patient counts. For seven heterogeneous variables, mean_j(MSE_z,j) × scale_ILITOTAL² is not the ILITOTAL MSE and has no defensible common physical unit. The true target-specific quantity must first be extracted from feature index 4. Means cancel from error conversion, but are essential when converting absolute values for PIE.

Seven non-MIFlu raw prediction sets are missing (`test_eval_download.tar.gz` and corresponding NPZs are not packaged). Thus their valid ILITOTAL errors are **NA**, not zero and not inferred from aggregate errors. The requested scalar multiplication is saved separately in `requested_arithmetic_NOT_patient_count_metrics.csv` only as explicitly invalid-unit arithmetic; it must not be cited as physical performance.

### Window length, actual lead and peak protocol (B2–B3)

L identifies an entire output window and its separately trained model. A per-L MSE averages all leads k=1…L, origins and variables. Changing L also changes the valid origin count, so an improving normalized per-L profile is not evidence of decreasing error as actual forecast lead grows. We additionally compute MIFlu errors for each actual k.

Legacy peak analysis takes feature 4, **k=1 only**, converts to counts, then picks peaks above each series' own mean and matches within ±2 weeks. The parameter called MIN_SEP_WEEKS=40 actually masks ±20 weeks, enforcing only 21-position spacing; it does not implement 40-week minimum separation. This frozen defect is reproduced for traceability, not endorsed. Means of PTE/PIE condition on matched peaks and censor larger timing failures, causing survivor bias. A PASS based on means is only a diagnostic; the valid event-level hit requires both tolerances, with missed true peaks in the denominator. False peaks are reported separately. The original three peaks repeated across L and seeds are not 36 independent epidemics.

B3 tables pool event errors rather than averaging rounded cell means. Archived event PIE is rounded to two decimals; frozen Hit statuses are preserved to avoid threshold reclassification errors. Newly recomputed MIFlu events use raw predictions. Additional shared-support analysis uses target rows 832–942 at k=1 and k=L for every L, avoiding unequal support. It contains only two underlying true peaks, repeated over three seeds.

### New expanded benchmark and exploratory hybrid (B4)

The expanded suite excludes DLinear: **NLinear is the only learned linear baseline**. Five classical models are DecisionTree, RandomForest, PCA-HistGB, PCA-SVR and KNN. PCA-HistGB and PCA-SVR explicitly compress training targets to eight PCA coordinates before fitting nonlinear regressors; they are not unrestricted independent-output implementations. They consume the same 104×7 standardized lag input. Training-only target PCA is fitted separately per L. Details and validation candidates are fixed in `protocol/config.json` before these new fits.

Neural baselines are NLinear, DNN, 1D CNN, GRU, TimesNet and Autoformer. All use Adam, MSE, 20 epochs, batch=16, lr=0.0005, validation-only checkpoint selection, seeds 42/43/44 and one frozen-winner test evaluation per cell. DNN has two width-64 hidden layers; CNN uses two width-16 convolutions and temporal pooling; GRU has width32; TimesNet uses width16, d_ff32, one block, top_k2, two convolution kernels; Autoformer uses width16/d_ff32, one encoder and decoder, two heads, moving-average25, label_len18. Autoformer uses its upstream normalization, while DNN/CNN/GRU use reversible window normalization. Calendar covariates are omitted because dates are synthetic. These are **compact, narrowly tuned exploratory implementations**, not fully optimized SOTA comparisons. Randomized tree ties/forests and neural initializations use seeds; deterministic KNN/SVR/HistGB repetitions are identical and do not create independent evidence.

We also execute **PeakBlend**, a feasibility experiment, not a novelty claim: w = sigmoid(b0 + b1 × (last observed ILITOTAL z − training q75) + b2 × last-four-week observed change). Forecast = w×NLinear + (1−w)×TimesNet. A fixed 18-combination gate grid is selected on validation all7 MSE plus ILITOTAL MSE above the **training q90** threshold. No test labels choose the gate; both experts remain frozen. Its inference requires both experts. The unchanged config is `protocol/hybrid_config.json`.

All these experiments are **EXPANDED_EXPLORATORY_966**, not Track C or paper reproduction runs. This historical test set was exposed before design. Validation-only selection within new scripts cannot turn an already exposed test into an untouched confirmatory test. Matching evaluation keys is necessary but does not prove historical baseline training fidelity or eliminate prior researcher adaptation.

## Results

### A2–A3: reproduction gap, existing experiment and realistic limits

The archived Track C figure 1.8652 and paper mean 1.4355 use different protocols and repetition counts. The 29.93% separation is descriptive only. The correct five-percent band is [1.363725, 1.507275]; an absolute ±0.10 band is not equivalent to 5%.

The supplied earlier R1-C experiment already ran 24 fits (two candidates × four L × three seeds 1000–1002). We recomputed its table from `R1C_RESULTS_PER_CANDIDATE.csv`; no new GPU experiment is implied:

| candidate_id | horizon | test_mse | test_mae |
| --- | --- | --- | --- |
| C0_r1b_constant_lr | 24 | 2.0460 | 0.9167 |
| C0_r1b_constant_lr | 36 | 1.9036 | 0.9178 |
| C0_r1b_constant_lr | 48 | 1.7339 | 0.8635 |
| C0_r1b_constant_lr | 60 | 1.7408 | 0.8804 |
| C1_released_type1_scheduler | 24 | 2.0588 | 0.9203 |
| C1_released_type1_scheduler | 36 | 1.8154 | 0.8693 |
| C1_released_type1_scheduler | 48 | 1.7166 | 0.8751 |
| C1_released_type1_scheduler | 60 | 1.6991 | 0.8704 |

Within Track R, C0 mean is 1.8561, C1 mean 1.8225, difference C1−C0 = -0.0336, a 1.81% lower MSE and 7.99% of that Track R baseline-to-paper descriptive gap. It improves L36/L48/L60 and worsens L24. This **does not quantify any fraction of the Track C gap**. The paired seed-level 95% t interval is [-0.2729, 0.2056], p=0.6069, n=3. It neither demonstrates superiority nor establishes non-inferiority. Treating all 12 correlated horizon cells as independent would overstate evidence.

Newly identified schedule alignment:

| training_epoch | author_end_update_matched | packaged_R1C_start_update |
| --- | --- | --- |
| 1 | 0.0005 | 0.0005 |
| 2 | 0.0005 | 0.0005 |
| 3 | 0.0005 | 0.0005 |
| 4 | 0.0005 | 0.0004 |
| 5 | 0.0004 | 0.0004 |
| 6 | 0.0004 | 0.0004 |

Candidate C2 matches the released end-of-previous-epoch update. `candidate_c2_train.py` is prepared in a separate path, with no change to evidence. **C2 is NOT RUN: per-L MSE, mean MSE, improvement and cost are unavailable.** A paper-method prefix-fusion reconstruction would be another explicit experimental arm, not a silent fix to Track C. The original corrected `r1b_model.py`, checkpoint/software fingerprints and matched GPU traces are required first.

An honest X%-seeds/Y%-architecture/Z%-unexplained causal decomposition is **not identifiable**: the factors are confounded, paper run-level outputs are absent and no controlled factorial experiment exists. The smallest supplied three-seed candidate mean is 1.8225 in **separate Track R**; it is an observed candidate, not the closest achievable optimum or a replacement for 1.8652. No available evidence establishes that a 5% tolerance is achievable, or proves it impossible. More seeds estimate randomness; they do not repair protocol differences. No percentage is assigned to hardware without a controlled rerun.

### B1: archived aggregate errors and valid ILITOTAL physical errors

| model | MSE_z_all7 | MAE_z_all7 | MSE_z_ILITOTAL | MSE_counts2_ILITOTAL | MAE_z_ILITOTAL | MAE_counts_ILITOTAL | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| miflu | 1.8652 | 0.8842 | 3.7020 | 300071219.8818 | 1.2621 | 11362.5245 | raw predictions independently rescored |
| nlinear | 2.0495 | 0.9566 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| dlinear | 2.3478 | 1.0884 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| timecma_llm | 2.6700 | 1.0927 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| patchtst | 3.9205 | 1.3826 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| itransformer | 3.9847 | 1.3545 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| qwen_time_llm | 5.2196 | 1.5784 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |
| calf_llm | 5.5153 | 1.6080 | NA | NA | NA | NA | aggregate CSV only; target-only errors unavailable |

Source: archived ranking CSV plus independent scoring of the 12 MIFlu prediction CSVs; `results/verified_miflu_cells.csv`. Four L receive equal weight, then three seeds receive equal weight; observations are not pooled across L with unequal counts.

### B2: archived scores by output-window length

| model | 24 | 36 | 48 | 60 | mean_4L | best_L | worst_L | L60_vs_L24_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| miflu | 1.9686 | 1.9332 | 1.7547 | 1.8042 | 1.8652 | 48 | 24 | -8.35 |
| nlinear | 2.1008 | 2.0277 | 2.0033 | 2.0664 | 2.0495 | 48 | 24 | -1.64 |
| dlinear | 2.2850 | 2.2780 | 2.3558 | 2.4726 | 2.3478 | 36 | 60 | 8.21 |
| timecma_llm | 2.4541 | 2.6432 | 2.7203 | 2.8625 | 2.6700 | 24 | 60 | 16.64 |
| patchtst | 3.8884 | 3.7766 | 3.9525 | 4.0643 | 3.9205 | 36 | 60 | 4.52 |
| itransformer | 3.7511 | 3.9813 | 4.0343 | 4.1721 | 3.9847 | 24 | 60 | 11.23 |
| qwen_time_llm | 4.6187 | 4.9957 | 5.6660 | 5.5978 | 5.2196 | 24 | 48 | 21.20 |
| calf_llm | 5.2711 | 5.3431 | 5.6149 | 5.8321 | 5.5153 | 24 | 60 | 10.64 |

Normalized profile (MSE_L / own four-window mean):

| model | 24 | 36 | 48 | 60 |
| --- | --- | --- | --- | --- |
| miflu | 1.0554 | 1.0365 | 0.9408 | 0.9673 |
| nlinear | 1.0250 | 0.9893 | 0.9774 | 1.0082 |
| dlinear | 0.9732 | 0.9703 | 1.0034 | 1.0531 |
| timecma_llm | 0.9191 | 0.9900 | 1.0188 | 1.0721 |
| patchtst | 0.9918 | 0.9633 | 1.0082 | 1.0367 |
| itransformer | 0.9414 | 0.9991 | 1.0125 | 1.0470 |
| qwen_time_llm | 0.8849 | 0.9571 | 1.0855 | 1.0725 |
| calf_llm | 0.9557 | 0.9688 | 1.0181 | 1.0574 |

MIFlu is lowest among the eight archived aggregates at every L. Its relative advantage over archived NLinear is not uniform. `results/B2_per_horizon_MSE_MAE.csv` retains both MSE and MAE per L. A falling profile for MIFlu must not be described as improved long-range forecast skill, because it mixes k and changes support. Actual-k data are in `miflu_actual_lead_means.csv` and Figure 4.

### B3: archived model × L peak results

The following means are conditional on matched k=1 peaks. PASS columns test **means only**, as requested; **event hit rate is the acceptance metric**, and a mean PASS is not evidence that all events pass. `n_true=9` means three underlying peaks repeated across three seeds. These are archive-derived numbers, not a verification of the unavailable CONSENSUS file.

| model | L | mean_PTE_wk | mean_PIE_pct | mean_PTE_le1 | mean_PIE_le25 | mean_combined | n_true | n_matched | n_missed | n_false | n_hit | hit_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| miflu | 24 | 0.2500 | 23.06 | PASS | PASS | PASS | 9 | 8 | 1 | 2 | 5 | 55.56 |
| miflu | 36 | 0.2857 | 24.36 | PASS | PASS | PASS | 9 | 7 | 2 | 3 | 4 | 44.44 |
| miflu | 48 | 0.3750 | 28.42 | PASS | FAIL | FAIL | 9 | 8 | 1 | 1 | 2 | 22.22 |
| miflu | 60 | 0.2857 | 24.69 | PASS | PASS | PASS | 9 | 7 | 2 | 2 | 4 | 44.44 |
| nlinear | 24 | 0.1111 | 3.95 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| nlinear | 36 | 0.3333 | 4.18 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| nlinear | 48 | 0.2222 | 2.42 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| nlinear | 60 | 0.4444 | 2.03 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| dlinear | 24 | 0.8889 | 16.32 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| dlinear | 36 | 1.1111 | 15.86 | FAIL | PASS | FAIL | 9 | 9 | 0 | 0 | 8 | 88.89 |
| dlinear | 48 | 0.7778 | 23.19 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 6 | 66.67 |
| dlinear | 60 | 0.8889 | 15.51 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 8 | 88.89 |
| timecma_llm | 24 | 1.1111 | 42.49 | FAIL | FAIL | FAIL | 9 | 9 | 0 | 2 | 0 | 0.00 |
| timecma_llm | 36 | 1.3750 | 55.55 | FAIL | FAIL | FAIL | 9 | 8 | 1 | 1 | 0 | 0.00 |
| timecma_llm | 48 | 1.3333 | 50.70 | FAIL | FAIL | FAIL | 9 | 9 | 0 | 0 | 0 | 0.00 |
| timecma_llm | 60 | 1.6250 | 52.69 | FAIL | FAIL | FAIL | 9 | 8 | 1 | 1 | 0 | 0.00 |
| patchtst | 24 | 0.5556 | 68.58 | PASS | FAIL | FAIL | 9 | 9 | 0 | 2 | 0 | 0.00 |
| patchtst | 36 | 0.5000 | 61.18 | PASS | FAIL | FAIL | 9 | 4 | 5 | 5 | 0 | 0.00 |
| patchtst | 48 | 1.0000 | 69.36 | PASS | FAIL | FAIL | 9 | 5 | 4 | 4 | 0 | 0.00 |
| patchtst | 60 | 0.7500 | 65.61 | PASS | FAIL | FAIL | 9 | 4 | 5 | 5 | 0 | 0.00 |
| itransformer | 24 | 0.2500 | 65.46 | PASS | FAIL | FAIL | 9 | 4 | 5 | 6 | 0 | 0.00 |
| itransformer | 36 | 0.8333 | 66.34 | PASS | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| itransformer | 48 | 1.0000 | 67.45 | PASS | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| itransformer | 60 | 1.0000 | 66.18 | PASS | FAIL | FAIL | 9 | 4 | 5 | 5 | 0 | 0.00 |
| qwen_time_llm | 24 | 1.1667 | 37.84 | FAIL | FAIL | FAIL | 9 | 6 | 3 | 6 | 0 | 0.00 |
| qwen_time_llm | 36 | 1.0000 | 37.34 | PASS | FAIL | FAIL | 9 | 6 | 3 | 4 | 1 | 11.11 |
| qwen_time_llm | 48 | 0.8333 | 37.80 | PASS | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| qwen_time_llm | 60 | 0.8333 | 32.34 | PASS | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| calf_llm | 24 | 2.0000 | 79.64 | FAIL | FAIL | FAIL | 9 | 1 | 8 | 11 | 0 | 0.00 |
| calf_llm | 36 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| calf_llm | 48 | 0.2000 | 82.72 | PASS | FAIL | FAIL | 9 | 5 | 4 | 5 | 0 | 0.00 |
| calf_llm | 60 | 1.3333 | 80.56 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |

MIFlu hits by L are 5/9, 4/9, 2/9 and 4/9, summing to 15/36. This pattern is nonmonotonic. The prompt's 31/36 is retained as an unresolved source assertion; in the supplied frozen tables **31/36 belongs to DLinear**. Do not silently substitute one for the other. The simplified 36/36 MIFlu count from START_HERE is not supported by these strict event tables.

Descriptive correlation across the eight archived models: Spearman rho between MSE and peak hit rate = -0.6722, p=0.0678. Lower MSE tends to align with higher hit rate overall, but champions differ and the relationship is not one-to-one; with eight selected models and tied zeros this is not robust inferential evidence. MIFlu versus NLinear paired **seed-level** MSE difference is -0.1844, exact two-sided sign-flip p=0.2500, n=3. Twelve correlated L×seed cells are not twelve independent datasets.

Shared-support actual-lead MIFlu diagnostic:

| model | L | mean_PTE_wk | mean_PIE_pct | mean_PTE_le1 | mean_PIE_le25 | mean_combined | n_true | n_matched | n_missed | n_false | n_hit | hit_rate_pct | metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| miflu | 24 | 0.0000 | 19.86 | PASS | PASS | PASS | 6 | 5 | 1 | 1 | 5 | 83.33 | common_k1 |
| miflu | 36 | 0.0000 | 21.47 | PASS | PASS | PASS | 6 | 4 | 2 | 2 | 3 | 50.00 | common_k1 |
| miflu | 48 | 0.2000 | 25.98 | PASS | FAIL | FAIL | 6 | 5 | 1 | 1 | 2 | 33.33 | common_k1 |
| miflu | 60 | 0.2500 | 19.71 | PASS | PASS | PASS | 6 | 4 | 2 | 2 | 4 | 66.67 | common_k1 |
| miflu | 24 | 0.8333 | 30.37 | PASS | FAIL | FAIL | 6 | 6 | 0 | 3 | 2 | 33.33 | common_terminal |
| miflu | 36 | 1.0000 | 30.32 | PASS | FAIL | FAIL | 6 | 6 | 0 | 1 | 2 | 33.33 | common_terminal |
| miflu | 48 | 0.6667 | 36.82 | PASS | FAIL | FAIL | 6 | 6 | 0 | 3 | 0 | 0.00 | common_terminal |
| miflu | 60 | 0.2000 | 46.37 | PASS | FAIL | FAIL | 6 | 5 | 1 | 6 | 0 | 0.00 | common_terminal |

All terminal-lead mean PIE values exceed 25%, and terminal-lead hit rates reach zero at 48 and 60 weeks in this tiny diagnostic. Timing means alone look small partly because unmatched peaks are censored. This challenges extrapolating one-week diagnostics into long-horizon peak claims; it does not adjudicate the paper's separate few-shot figure or prove general inferiority.

### B4: newly executed expanded suite

New runs only; three seeds, equal four-window means. MIFlu's historical Track C score is kept in its separate table above. The lowest new-suite all7 MSE is 2.0662 (NLinear); this is a descriptive exploratory ranking, not a new authoritative champion.

| model | mse_z_all7 | mae_z_all7 | mse_z_ili | mae_z_ili | mse_counts2_ili | mae_counts_ili | sd_seed_MSE_all7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NLinear | 2.0662 | 0.9595 | 4.0656 | 1.3079 | 329545887.9509 | 11775.5654 | 0.0228 |
| CNN | 2.1883 | 0.9235 | 4.5032 | 1.2869 | 365016351.7846 | 11585.8415 | 0.0728 |
| PeakBlend | 2.1955 | 0.9736 | 4.4687 | 1.3543 | 362214286.7826 | 12192.7265 | 0.2590 |
| GRU | 2.3069 | 0.9878 | 4.6759 | 1.3814 | 379014137.5308 | 12437.2701 | 0.0967 |
| TimesNet | 2.4529 | 1.0108 | 5.1579 | 1.4441 | 418086228.4400 | 13001.2182 | 0.4815 |
| DNN | 2.7019 | 1.0994 | 5.4722 | 1.6818 | 443555888.2359 | 15141.2686 | 0.0270 |
| Autoformer | 3.7881 | 1.4002 | 8.0346 | 2.0306 | 651261656.1576 | 18281.4329 | 0.0180 |
| KNN | 3.8844 | 1.3606 | 7.5257 | 1.8117 | 610008444.6273 | 16311.4026 | 0.0000 |
| PCA-HistGB | 4.5306 | 1.4250 | 9.1470 | 1.8600 | 741429457.2798 | 16745.7357 | 0.0000 |
| RandomForest | 4.6348 | 1.4547 | 9.0841 | 1.8253 | 736328346.6373 | 16433.6794 | 0.0236 |
| DecisionTree | 5.3184 | 1.5895 | 10.3076 | 2.0283 | 835497960.4033 | 18261.2223 | 0.0534 |
| PCA-SVR | 5.8616 | 1.6478 | 11.1008 | 2.1226 | 899798302.7210 | 19110.1753 | 0.0000 |

Per-L scores with both spaces. The two physical columns refer only to ILITOTAL; `mse_z_all7` is a different multivariate target:

| model | L | mse_z_all7 | mae_z_all7 | mse_z_ili | mae_z_ili | mse_counts2_ili | mae_counts_ili |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Autoformer | 24 | 3.6945 | 1.3920 | 7.8148 | 2.0500 | 633442378.9201 | 18456.2241 |
| Autoformer | 36 | 3.6592 | 1.3702 | 7.7567 | 2.0045 | 628730100.1348 | 18047.0463 |
| Autoformer | 48 | 3.8045 | 1.4015 | 8.0330 | 2.0085 | 651130883.2220 | 18082.4848 |
| Autoformer | 60 | 3.9944 | 1.4369 | 8.5341 | 2.0593 | 691743262.3534 | 18539.9762 |
| CNN | 24 | 2.3132 | 0.9549 | 4.7991 | 1.3990 | 389003066.2854 | 12595.0329 |
| CNN | 36 | 2.1830 | 0.9164 | 4.4843 | 1.2761 | 363481187.6908 | 11488.9079 |
| CNN | 48 | 2.1552 | 0.9175 | 4.3977 | 1.2418 | 356460378.4120 | 11179.6846 |
| CNN | 60 | 2.1020 | 0.9053 | 4.3318 | 1.2307 | 351120774.7502 | 11079.7408 |
| DNN | 24 | 2.8999 | 1.0712 | 5.8687 | 1.6383 | 475698432.2130 | 14749.8812 |
| DNN | 36 | 2.6293 | 1.0780 | 5.3857 | 1.6649 | 436549202.0532 | 14989.4014 |
| DNN | 48 | 2.6089 | 1.1134 | 5.2185 | 1.6886 | 422994407.5860 | 15202.4637 |
| DNN | 60 | 2.6696 | 1.1350 | 5.4157 | 1.7353 | 438981511.0915 | 15623.3279 |
| DecisionTree | 24 | 4.6968 | 1.4817 | 8.9657 | 1.8379 | 726726907.9027 | 16546.7389 |
| DecisionTree | 36 | 5.4421 | 1.5919 | 10.4024 | 2.0433 | 843182373.3586 | 18396.2688 |
| DecisionTree | 48 | 5.7069 | 1.6690 | 11.0804 | 2.1161 | 898140367.0046 | 19051.8750 |
| DecisionTree | 60 | 5.4278 | 1.6154 | 10.7819 | 2.1159 | 873942193.3472 | 19050.0065 |
| GRU | 24 | 2.3005 | 1.0030 | 4.5976 | 1.4305 | 372662856.6124 | 12879.1119 |
| GRU | 36 | 2.3769 | 0.9990 | 4.8510 | 1.3993 | 393204309.6469 | 12597.8817 |
| GRU | 48 | 2.2360 | 0.9738 | 4.5004 | 1.3397 | 364785039.7091 | 12061.4225 |
| GRU | 60 | 2.3145 | 0.9755 | 4.7547 | 1.3563 | 385404344.1547 | 12210.6642 |
| KNN | 24 | 3.8106 | 1.3452 | 7.1808 | 1.7621 | 582055648.5992 | 15864.8247 |
| KNN | 36 | 3.8004 | 1.3372 | 7.2891 | 1.7730 | 590830089.4564 | 15962.7123 |
| KNN | 48 | 3.9171 | 1.3699 | 7.6660 | 1.8360 | 621384300.3416 | 16529.5344 |
| KNN | 60 | 4.0096 | 1.3901 | 7.9668 | 1.8758 | 645763740.1122 | 16888.5390 |
| NLinear | 24 | 2.1115 | 0.9554 | 4.1638 | 1.3373 | 337508122.7060 | 12039.9183 |
| NLinear | 36 | 2.0096 | 0.9408 | 3.9364 | 1.2759 | 319070244.2010 | 11487.4675 |
| NLinear | 48 | 2.0682 | 0.9682 | 4.0648 | 1.3079 | 329482307.4615 | 11775.5074 |
| NLinear | 60 | 2.0754 | 0.9737 | 4.0974 | 1.3106 | 332122877.4350 | 11799.3681 |
| PCA-HistGB | 24 | 4.0101 | 1.3412 | 7.8954 | 1.6961 | 639972074.8478 | 15270.3307 |
| PCA-HistGB | 36 | 4.4695 | 1.3984 | 9.0316 | 1.8242 | 732071322.8693 | 16423.8332 |
| PCA-HistGB | 48 | 4.6324 | 1.4463 | 9.4196 | 1.9018 | 763524137.9327 | 17121.8692 |
| PCA-HistGB | 60 | 5.0105 | 1.5143 | 10.2416 | 2.0178 | 830150293.4695 | 18166.9095 |
| PCA-SVR | 24 | 5.6845 | 1.6136 | 10.4875 | 2.0601 | 850086703.3437 | 18547.6840 |
| PCA-SVR | 36 | 5.7753 | 1.6303 | 10.8244 | 2.0884 | 877386936.8938 | 18802.3383 |
| PCA-SVR | 48 | 5.9202 | 1.6573 | 11.3254 | 2.1421 | 918002999.9627 | 19285.8204 |
| PCA-SVR | 60 | 6.0664 | 1.6902 | 11.7660 | 2.1998 | 953716570.6836 | 19804.8585 |
| PeakBlend | 24 | 2.5589 | 1.0505 | 5.3718 | 1.5467 | 435418642.5945 | 13925.4282 |
| PeakBlend | 36 | 1.9932 | 0.9315 | 3.9456 | 1.2611 | 319818348.8502 | 11354.3154 |
| PeakBlend | 48 | 2.3318 | 0.9976 | 4.8081 | 1.3873 | 389731391.7675 | 12490.2360 |
| PeakBlend | 60 | 1.8983 | 0.9147 | 3.7491 | 1.2219 | 303888763.9182 | 11000.9264 |
| RandomForest | 24 | 3.8991 | 1.3716 | 7.2653 | 1.5974 | 588902318.4165 | 14381.8173 |
| RandomForest | 36 | 4.5019 | 1.4137 | 8.7845 | 1.7720 | 712043382.4410 | 15953.6885 |
| RandomForest | 48 | 4.8681 | 1.4756 | 9.7091 | 1.8882 | 786988680.7351 | 16999.6929 |
| RandomForest | 60 | 5.2700 | 1.5581 | 10.5775 | 2.0437 | 857379004.9565 | 18399.5189 |
| TimesNet | 24 | 2.7961 | 1.0693 | 5.9901 | 1.5986 | 485537033.5955 | 14392.2882 |
| TimesNet | 36 | 2.1290 | 0.9506 | 4.3576 | 1.3137 | 353215573.7112 | 11827.8494 |
| TimesNet | 48 | 2.8846 | 1.0936 | 6.2632 | 1.5988 | 507672550.3142 | 14394.2788 |
| TimesNet | 60 | 2.0020 | 0.9296 | 4.0209 | 1.2652 | 325919756.1391 | 11390.4564 |

Best/worst output-window lengths:

| model | 24 | 36 | 48 | 60 | mean_4L | best_L | worst_L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NLinear | 2.1115 | 2.0096 | 2.0682 | 2.0754 | 2.0662 | 36 | 24 |
| CNN | 2.3132 | 2.1830 | 2.1552 | 2.1020 | 2.1883 | 60 | 24 |
| PeakBlend | 2.5589 | 1.9932 | 2.3318 | 1.8983 | 2.1955 | 60 | 24 |
| GRU | 2.3005 | 2.3769 | 2.2360 | 2.3145 | 2.3069 | 48 | 36 |
| TimesNet | 2.7961 | 2.1290 | 2.8846 | 2.0020 | 2.4529 | 60 | 48 |
| DNN | 2.8999 | 2.6293 | 2.6089 | 2.6696 | 2.7019 | 48 | 24 |
| Autoformer | 3.6945 | 3.6592 | 3.8045 | 3.9944 | 3.7881 | 36 | 60 |
| KNN | 3.8106 | 3.8004 | 3.9171 | 4.0096 | 3.8844 | 36 | 60 |
| PCA-HistGB | 4.0101 | 4.4695 | 4.6324 | 5.0105 | 4.5306 | 24 | 60 |
| RandomForest | 3.8991 | 4.5019 | 4.8681 | 5.2700 | 4.6348 | 24 | 60 |
| DecisionTree | 4.6968 | 5.4421 | 5.7069 | 5.4278 | 5.3184 | 24 | 48 |
| PCA-SVR | 5.6845 | 5.7753 | 5.9202 | 6.0664 | 5.8616 | 24 | 60 |

Normalized per-L all7 profile (each model divided by its own mean):

| model | 24 | 36 | 48 | 60 |
| --- | --- | --- | --- | --- |
| NLinear | 1.0219 | 0.9726 | 1.0010 | 1.0045 |
| CNN | 1.0570 | 0.9976 | 0.9848 | 0.9606 |
| PeakBlend | 1.1655 | 0.9078 | 1.0620 | 0.8646 |
| GRU | 0.9972 | 1.0303 | 0.9692 | 1.0033 |
| TimesNet | 1.1399 | 0.8680 | 1.1760 | 0.8162 |
| DNN | 1.0733 | 0.9731 | 0.9656 | 0.9880 |
| Autoformer | 0.9753 | 0.9660 | 1.0043 | 1.0544 |
| KNN | 0.9810 | 0.9784 | 1.0084 | 1.0322 |
| PCA-HistGB | 0.8851 | 0.9865 | 1.0225 | 1.1059 |
| RandomForest | 0.8413 | 0.9713 | 1.0504 | 1.1371 |
| DecisionTree | 0.8831 | 1.0233 | 1.0730 | 1.0206 |
| PCA-SVR | 0.9698 | 0.9853 | 1.0100 | 1.0349 |

New-suite per-model × L peak diagnostics (k=1, legacy picker, matched-only means):

| model | L | mean_PTE_wk | mean_PIE_pct | mean_PTE_le1 | mean_PIE_le25 | mean_combined | n_true | n_matched | n_missed | n_false | n_hit | hit_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DecisionTree | 24 | 1.0000 | 72.96 | PASS | FAIL | FAIL | 9 | 1 | 8 | 14 | 0 | 0.00 |
| DecisionTree | 36 | 2.0000 | 57.63 | FAIL | FAIL | FAIL | 9 | 1 | 8 | 5 | 0 | 0.00 |
| DecisionTree | 48 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 3 | 0 | 0.00 |
| DecisionTree | 60 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 15 | 0 | 0.00 |
| RandomForest | 24 | 1.2000 | 67.19 | FAIL | FAIL | FAIL | 9 | 5 | 4 | 6 | 0 | 0.00 |
| RandomForest | 36 | 1.5000 | 84.62 | FAIL | FAIL | FAIL | 9 | 2 | 7 | 8 | 0 | 0.00 |
| RandomForest | 48 | 1.0000 | 82.59 | PASS | FAIL | FAIL | 9 | 4 | 5 | 5 | 0 | 0.00 |
| RandomForest | 60 | 0.6667 | 84.36 | PASS | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| PCA-HistGB | 24 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| PCA-HistGB | 36 | 1.0000 | 72.90 | PASS | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| PCA-HistGB | 48 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| PCA-HistGB | 60 | 2.0000 | 75.03 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| PCA-SVR | 24 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| PCA-SVR | 36 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| PCA-SVR | 48 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 9 | 0 | 0.00 |
| PCA-SVR | 60 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 6 | 0 | 0.00 |
| KNN | 24 | 2.0000 | 64.52 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| KNN | 36 | 2.0000 | 65.23 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| KNN | 48 | 2.0000 | 67.47 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| KNN | 60 | 2.0000 | 67.47 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 6 | 0 | 0.00 |
| NLinear | 24 | 0.6667 | 2.09 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| NLinear | 36 | 0.4444 | 4.18 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| NLinear | 48 | 0.5556 | 1.67 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| NLinear | 60 | 0.6667 | 3.68 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| DNN | 24 | 0.5000 | 21.87 | PASS | PASS | PASS | 9 | 8 | 1 | 5 | 5 | 55.56 |
| DNN | 36 | 0.6000 | 25.93 | PASS | FAIL | FAIL | 9 | 5 | 4 | 4 | 2 | 22.22 |
| DNN | 48 | 0.5556 | 27.41 | PASS | FAIL | FAIL | 9 | 9 | 0 | 4 | 3 | 33.33 |
| DNN | 60 | 0.8750 | 26.79 | PASS | FAIL | FAIL | 9 | 8 | 1 | 5 | 2 | 22.22 |
| CNN | 24 | 1.1667 | 49.04 | FAIL | FAIL | FAIL | 9 | 6 | 3 | 7 | 0 | 0.00 |
| CNN | 36 | 1.2857 | 50.80 | FAIL | FAIL | FAIL | 9 | 7 | 2 | 2 | 0 | 0.00 |
| CNN | 48 | 1.2857 | 51.85 | FAIL | FAIL | FAIL | 9 | 7 | 2 | 2 | 0 | 0.00 |
| CNN | 60 | 1.5714 | 52.07 | FAIL | FAIL | FAIL | 9 | 7 | 2 | 2 | 0 | 0.00 |
| GRU | 24 | 1.1429 | 30.97 | FAIL | FAIL | FAIL | 9 | 7 | 2 | 5 | 2 | 22.22 |
| GRU | 36 | 1.0000 | 37.45 | PASS | FAIL | FAIL | 9 | 7 | 2 | 4 | 1 | 11.11 |
| GRU | 48 | 1.1667 | 44.13 | FAIL | FAIL | FAIL | 9 | 6 | 3 | 3 | 0 | 0.00 |
| GRU | 60 | 1.0000 | 41.30 | PASS | FAIL | FAIL | 9 | 9 | 0 | 0 | 0 | 0.00 |
| TimesNet | 24 | 1.3333 | 27.17 | FAIL | FAIL | FAIL | 9 | 6 | 3 | 7 | 1 | 11.11 |
| TimesNet | 36 | 0.6000 | 39.89 | PASS | FAIL | FAIL | 9 | 5 | 4 | 6 | 1 | 11.11 |
| TimesNet | 48 | 1.2000 | 36.81 | FAIL | FAIL | FAIL | 9 | 5 | 4 | 8 | 1 | 11.11 |
| TimesNet | 60 | 1.0000 | 39.39 | PASS | FAIL | FAIL | 9 | 8 | 1 | 2 | 1 | 11.11 |
| Autoformer | 24 | 1.0000 | 66.88 | PASS | FAIL | FAIL | 9 | 3 | 6 | 12 | 0 | 0.00 |
| Autoformer | 36 | 1.3333 | 58.25 | FAIL | FAIL | FAIL | 9 | 3 | 6 | 13 | 0 | 0.00 |
| Autoformer | 48 | NA | NA | NA | NA | NA | 9 | 0 | 9 | 14 | 0 | 0.00 |
| Autoformer | 60 | 1.0000 | 73.95 | PASS | FAIL | FAIL | 9 | 3 | 6 | 10 | 0 | 0.00 |
| PeakBlend | 24 | 0.6667 | 2.10 | PASS | PASS | PASS | 9 | 9 | 0 | 6 | 9 | 100.00 |
| PeakBlend | 36 | 0.4444 | 4.24 | PASS | PASS | PASS | 9 | 9 | 0 | 0 | 9 | 100.00 |
| PeakBlend | 48 | 0.5556 | 1.72 | PASS | PASS | PASS | 9 | 9 | 0 | 1 | 9 | 100.00 |
| PeakBlend | 60 | 0.6667 | 9.77 | PASS | PASS | PASS | 9 | 9 | 0 | 1 | 9 | 100.00 |

New-suite **actual terminal-lead** peak diagnostics, on the same target rows 832–942 at every L (two underlying peaks, repeated across three seeds; matched-only means):

| model | L | mean_PTE_wk | mean_PIE_pct | mean_PTE_le1 | mean_PIE_le25 | mean_combined | n_true | n_matched | n_missed | n_false | n_hit | hit_rate_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DecisionTree | 24 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| DecisionTree | 36 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 14 | 0 | 0.00 |
| DecisionTree | 48 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 15 | 0 | 0.00 |
| DecisionTree | 60 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| RandomForest | 24 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 9 | 0 | 0.00 |
| RandomForest | 36 | 2.0000 | 80.75 | FAIL | FAIL | FAIL | 6 | 1 | 5 | 7 | 0 | 0.00 |
| RandomForest | 48 | 2.0000 | 80.01 | FAIL | FAIL | FAIL | 6 | 2 | 4 | 7 | 0 | 0.00 |
| RandomForest | 60 | 1.0000 | 84.31 | PASS | FAIL | FAIL | 6 | 3 | 3 | 3 | 0 | 0.00 |
| PCA-HistGB | 24 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| PCA-HistGB | 36 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| PCA-HistGB | 48 | 1.5000 | 76.21 | FAIL | FAIL | FAIL | 6 | 6 | 0 | 3 | 0 | 0.00 |
| PCA-HistGB | 60 | 1.0000 | 72.74 | PASS | FAIL | FAIL | 6 | 6 | 0 | 3 | 0 | 0.00 |
| PCA-SVR | 24 | 2.0000 | 88.63 | FAIL | FAIL | FAIL | 6 | 3 | 3 | 3 | 0 | 0.00 |
| PCA-SVR | 36 | 2.0000 | 80.66 | FAIL | FAIL | FAIL | 6 | 6 | 0 | 0 | 0 | 0.00 |
| PCA-SVR | 48 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 9 | 0 | 0.00 |
| PCA-SVR | 60 | 1.0000 | 74.54 | PASS | FAIL | FAIL | 6 | 6 | 0 | 0 | 0 | 0.00 |
| KNN | 24 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| KNN | 36 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| KNN | 48 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| KNN | 60 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 6 | 0 | 0.00 |
| NLinear | 24 | 1.2500 | 42.82 | FAIL | FAIL | FAIL | 6 | 4 | 2 | 5 | 0 | 0.00 |
| NLinear | 36 | 0.4000 | 43.76 | PASS | FAIL | FAIL | 6 | 5 | 1 | 4 | 0 | 0.00 |
| NLinear | 48 | 1.0000 | 40.84 | PASS | FAIL | FAIL | 6 | 6 | 0 | 3 | 0 | 0.00 |
| NLinear | 60 | 1.5000 | 55.40 | FAIL | FAIL | FAIL | 6 | 2 | 4 | 7 | 0 | 0.00 |
| DNN | 24 | 0.4000 | 31.76 | PASS | FAIL | FAIL | 6 | 5 | 1 | 6 | 2 | 33.33 |
| DNN | 36 | 1.0000 | 23.60 | PASS | PASS | PASS | 6 | 3 | 3 | 8 | 1 | 16.67 |
| DNN | 48 | 1.0000 | 27.67 | PASS | FAIL | FAIL | 6 | 3 | 3 | 7 | 1 | 16.67 |
| DNN | 60 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 10 | 0 | 0.00 |
| CNN | 24 | 1.5000 | 52.06 | FAIL | FAIL | FAIL | 6 | 4 | 2 | 5 | 0 | 0.00 |
| CNN | 36 | 1.0000 | 54.28 | PASS | FAIL | FAIL | 6 | 2 | 4 | 7 | 0 | 0.00 |
| CNN | 48 | 1.0000 | 58.54 | PASS | FAIL | FAIL | 6 | 2 | 4 | 7 | 0 | 0.00 |
| CNN | 60 | 0.0000 | 56.40 | PASS | FAIL | FAIL | 6 | 1 | 5 | 8 | 0 | 0.00 |
| GRU | 24 | 1.2500 | 61.04 | FAIL | FAIL | FAIL | 6 | 4 | 2 | 5 | 0 | 0.00 |
| GRU | 36 | 0.3333 | 54.69 | PASS | FAIL | FAIL | 6 | 3 | 3 | 6 | 0 | 0.00 |
| GRU | 48 | 0.7500 | 53.76 | PASS | FAIL | FAIL | 6 | 4 | 2 | 5 | 0 | 0.00 |
| GRU | 60 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 9 | 0 | 0.00 |
| TimesNet | 24 | 1.6000 | 30.83 | FAIL | FAIL | FAIL | 6 | 5 | 1 | 5 | 0 | 0.00 |
| TimesNet | 36 | 1.6667 | 46.92 | FAIL | FAIL | FAIL | 6 | 3 | 3 | 6 | 0 | 0.00 |
| TimesNet | 48 | 0.7500 | 47.83 | PASS | FAIL | FAIL | 6 | 4 | 2 | 6 | 0 | 0.00 |
| TimesNet | 60 | 1.0000 | 47.38 | PASS | FAIL | FAIL | 6 | 1 | 5 | 10 | 0 | 0.00 |
| Autoformer | 24 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 13 | 0 | 0.00 |
| Autoformer | 36 | 1.5000 | 57.16 | FAIL | FAIL | FAIL | 6 | 4 | 2 | 6 | 0 | 0.00 |
| Autoformer | 48 | NA | NA | NA | NA | NA | 6 | 0 | 6 | 11 | 0 | 0.00 |
| Autoformer | 60 | 1.0000 | 76.09 | PASS | FAIL | FAIL | 6 | 2 | 4 | 10 | 0 | 0.00 |
| PeakBlend | 24 | 1.6000 | 32.07 | FAIL | FAIL | FAIL | 6 | 5 | 1 | 5 | 0 | 0.00 |
| PeakBlend | 36 | 1.2500 | 45.95 | FAIL | FAIL | FAIL | 6 | 4 | 2 | 5 | 0 | 0.00 |
| PeakBlend | 48 | 1.3333 | 42.42 | FAIL | FAIL | FAIL | 6 | 6 | 0 | 3 | 0 | 0.00 |
| PeakBlend | 60 | 0.5000 | 53.50 | PASS | FAIL | FAIL | 6 | 2 | 4 | 7 | 0 | 0.00 |

The corresponding terminal-lead point errors are in `expanded_actual_terminal_scores.csv`; their k=L errors must not be confused with the mean over k=1…L in the main per-L table. Both peak tables use the frozen legacy picker for continuity and remain exploratory. New NLinear and PeakBlend each achieve zero terminal-lead hits at all four L on this common support, despite perfect k=1 hit rates. Their one-week success therefore provides no evidence of successful 24–60-week peak forecasting.

PeakBlend's full per-cell gate choices and validation objectives are retained, including unfavorable test outcomes. Its all7 mean MSE is 2.1955, **6.26% higher than new NLinear** (2.0662). Both achieve 36/36 hits in the k=1 legacy diagnostic, so this gate offers no gain over NLinear on that diagnostic and worsens aggregate MSE. This is a negative feasibility result, not a successful innovation claim. It is not evidence that gating improves MIFlu, because MIFlu is not one of its executable experts. A MIFlu+NLinear hybrid is a proposed future arm requiring matched validation predictions and the corrected original source.

Measured CPU costs (includes all candidates' training + validation; test prediction latency measured separately; checkpoint writing and environment setup excluded):

| model | fit_val_seconds_mean | fit_val_seconds_total | inference_ms_per_origin | gpu_hours_total | parameters_min | parameters_max | FLOPs | uses_text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Autoformer | 13.3873 | 160.6481 | 0.3267 | 0.0000 | 6631.0000 | 6631.0000 | unmeasured | False |
| CNN | 1.4230 | 17.0762 | 0.0346 | 0.0000 | 36984.0000 | 89652.0000 | unmeasured | False |
| DNN | 0.9299 | 11.1584 | 0.0163 | 0.0000 | 61736.0000 | 78116.0000 | unmeasured | False |
| DecisionTree | 1.6463 | 19.7550 | 0.0024 | 0.0000 | NA | NA | unmeasured | False |
| GRU | 11.7678 | 141.2139 | 0.1010 | 0.0000 | 9480.0000 | 17796.0000 | unmeasured | False |
| KNN | 0.0138 | 0.1651 | 0.0516 | 0.0000 | NA | NA | unmeasured | False |
| NLinear | 0.6556 | 7.8667 | 0.0040 | 0.0000 | 2520.0000 | 6300.0000 | unmeasured | False |
| PCA-HistGB | 6.3443 | 76.1312 | 0.0453 | 0.0000 | NA | NA | unmeasured | False |
| PCA-SVR | 0.7890 | 9.4683 | 1.2330 | 0.0000 | NA | NA | unmeasured | False |
| RandomForest | 11.0941 | 133.1293 | 0.1480 | 0.0000 | NA | NA | unmeasured | False |
| TimesNet | 9.9350 | 119.2202 | 0.3184 | 0.0000 | 24327.0000 | 28107.0000 | unmeasured | False |

All new training used CPU, so measured GPU-hours are zero. Classical estimator NN parameter counts are NA; FLOPs are unmeasured, not zero. PeakBlend additional gate timing is in `results/hybrid/hybrid_cost.csv` and must be added to the two experts' training/inference costs for deployment. Historical MIFlu total cost (1.5083 GPU-hours across 12 fits) and parameter counts are provided by the handoff's `TRACK_C_COST_SUMMARY.csv` and `TRACK_C_MIFLU_RUN_MATRIX.csv`, not measured anew. CPU and A100 wall times are not directly interchangeable, so historical MIFlu is excluded from the CPU Pareto frontier. Timings come from concurrently running jobs on a shared host, not dedicated hardware trials.

### LLM and API execution status

| model | status | encoding_arm | generation_arm | blocker |
| --- | --- | --- | --- | --- |
| Qwen/Qwen2.5-1.5B-Instruct | NOT_RUN | planned | planned | local snapshot not supplied; paired encoding/generation runner supplied |
| deepseek-ai/DeepSeek-V2-Lite-Chat | NOT_RUN | planned | planned | local snapshot not supplied; remote custom-code implementation requires separate reviewed adapter |
| deepseek-ai/DeepSeek-V3-0324 | NOT_RUN | planned | planned | local snapshot absent; multi-GPU memory and serving plan required; generic local runner not validated for this MoE |
| meta-llama/Llama-3.1-8B-Instruct | NOT_RUN | planned | planned | local snapshot not supplied; license/access must be satisfied |
| mistralai/Mistral-7B-Instruct-v0.3 | NOT_RUN | planned | planned | local snapshot not supplied |
| GPT-4o API | NOT_RUN | not available through API | planned | no API credential or versioned endpoint supplied; hidden states unavailable; generation-only separate arm |
| Claude API | NOT_RUN | not available through API | planned | no API credential or versioned endpoint supplied; hidden states unavailable; generation-only separate arm |

These checkpoint families are requested comparators, not a claim to be the October-2026 SOTA frontier. No newly measured Qwen, DeepSeek, Llama, Mistral, GPT-4o or Claude performance is reported. The archived Qwen/TimeCMA/CALF methods are explicitly inspired simplifications; their scores cannot substitute for these missing paired experiments.

`run_llm_features.py` provides local-snapshot encoding-only and generation-augmented arms for compatible Transformers checkpoints. It uses identical observed-window summaries, the same frozen instruct model per pair, 16 train-fitted PCA feature dimensions and the same random-forest downstream regressor. Generation is deterministic, bounded to 96 tokens of structured analysis, cached and hashed; it is an operational generation augmentation, **not proof of internal reasoning**. Its incremental information and token budget must be matched against numerical-summary and extra-token controls. The prompt and code are included, with no API keys. Local weights and immutable revision metadata are required; it never silently downloads weights or uses a remote API. The DeepSeek custom/MoE families require their own reviewed backend; the generic runner is not asserted to support them. Generation-only commercial APIs cannot supply the identical hidden-state encoder arm, so they must remain a separate comparison.

## Discussion

### What makes MIFlu special?

The archived result supports strong contract-specific aggregate point forecasting, but it does not isolate the effect of text. Frozen token matrices are static across origins, their tokens vary, released fusion has a causal-access concern, and actual corrected Track C source is absent. A useful next experiment is a matched replay with original GPU/software/source fingerprints: full, zero-text of identical shape, semantically shuffled/irrelevant text, equal-shape random features, text removed with controlled RNG, random-initialized forecasting GPT-2 and no-pretraining controls. Reset dropout/random streams, use deterministic eval probes, retain exact tensors, measure gradients and forward perturbations on CPU and GPU. Prefix and cross-attention repairs should be named separate paper-method hypotheses. Until then the mechanism contradiction remains **UNRESOLVED**.

### Linear versus nonlinear forecasting

Archived NLinear excels at the legacy peak diagnostic, and the new NLinear is a competitive inexpensive reference. This justifies retaining it and excluding a redundant second learned linear baseline in the expanded suite. It does not establish that nonlinear modeling or language models are unnecessary: tail distribution shift, limited data and narrow hyperparameter budgets may explain this dataset's behavior. Classical tree-based regressors cannot extrapolate beyond training targets in the way a linear temporal map can; the large later ILITOTAL peaks make this a relevant hypothesis, not a proven causal explanation of their observed error. PCA target compression also limits the SVR/boosting arms and must be ablated before drawing family-level conclusions.

### When might LLM context add value?

Potential benefits are testable when context contains information unavailable in numeric lags, is timestamped before forecast issuance and is causally accessible to the model. Static variable descriptions may act as priors; that is different from dynamic policy or pathogen information. The present dataset alone cannot determine a sample-size threshold or a cross-location benefit. Few-shot subsets must be chronological training prefixes with validation retained, all prompt statistics refit on allowed training data, and fixed forecast targets.

### Scale, architecture and generation

A newer or larger text encoder does not automatically improve a forecasting task. Run paired encoding/generation arms with the same numerical backbone, feature dimensionality, fusion and training budget. Then vary model scale within a family, and fusion within a fixed model. Separate pretraining, architecture and representation effects with random-weight and non-LLM text controls. Full DeepSeek-V3 has 671B main-model parameters (37B activated per token according to its model card) and is not a single-small-GPU experiment; V2-Lite is a distinct smaller comparator, not equivalent evidence. Weight access, memory, energy and serving latency need measurement. No frontier improvement is inferred here.

### Peak versus point forecasting and the proposed innovation

The scientifically useful contribution is a **causally valid, peak-aware decision study**, not simply a longer list of LLMs. PeakBlend is a small executable feasibility probe. A stronger future model would combine a well-calibrated numerical point forecaster, an explicit amplitude/timing residual expert, and a gate driven by available text and observed numerical state. Train with a preregistered combination of multivariate point loss, target-tail loss and differentiable peak-timing loss; use validation only to choose trade-offs. Compare a constant ensemble, a numerical gate, a text gate and a sham-text gate at equal capacity. Demonstrate improved external-season peak forecasting without materially degrading point scores or calibration. Gating/ensembling itself is established; novelty and publication suitability must be established by causal evidence, robust evaluation and clinical relevance.

### Public-health deployment

No model is deployment-validated by these retrospective data. A numerical baseline is the sensible operational reference because it is inexpensive and inspectable, while MIFlu remains a point-forecast research comparator. Selection should depend on forecast-issuance lead, missed-peak cost, false alarms, calibrated intervals, coverage, latency, revision handling and real prospective data availability. ILITOTAL is a surveillance count of ILI visits, not unique laboratory-confirmed influenza cases or population incidence. Do not transfer US benchmark findings to Hong Kong without a separate jurisdiction-specific dataset and validation.

### Confirmatory protocol required before journal claims

1. Recover the missing corrected MIFlu source, original manifests/checkpoints, complete seven-model prediction arrays, `peak_criteria.json` and HPC guide/access. Resolve the peak-version conflict using provenance, not preference.
2. Commit and hash a single protocol before new untouched evaluation: data vintage, real epidemiological week mapping, variable order, allowed context timestamps, precise training budgets and candidate counts. Lock 10 repetitions for paper-oriented reproduction; use matched initialization and report seed-level results.
3. Keep Track C immutable. Add C2 source-matched schedule and explicitly separated prefix-fusion hypotheses. Select configurations on training/validation only; do not use proximity to 1.4355 as a tuning objective.
4. Add chronological rolling-origin folds and external seasons/jurisdictions, plus persistence and seasonal-naive references as non-fitted sanity controls. Do not duplicate NLinear with a second learned linear baseline. Report model-specific hyperparameter search budgets; a fixed 20 epochs alone does not equalize optimization quality.
5. Define fixed season or event windows using information available at issuance. Score the actual peak of each complete forecast trajectory, report lead to observed/predicted peak, timing/intensity errors, missed/false peaks and probabilistic calibration. Correct the minimum-distance implementation in a separately versioned protocol; retain the legacy picker only for historical reconciliation.
6. Use paired, block/season-aware resampling or forecast-loss tests that respect overlapping targets. Seeds measure optimization noise, not epidemiological diversity. Preregister multiplicity correction and primary endpoints; avoid treating repeated predictions of the same three peaks as independent epidemics.
7. Evaluate text/no-text, random/shuffled text, numeric summaries, token-budget controls and random-pretraining controls under identical feature/adapter budgets. Audit possible pretraining contamination: modern LLMs were trained after this historical test period, so absence of future values in the prompt alone does not establish prospective validity.
8. Measure dedicated-device end-to-end latency, feature-generation tokens, total/amortized training cost, parameters, FLOPs/energy where measurable, memory and prospective surveillance revision effects. Report failed and incomplete runs explicitly.

## Conclusion

The valid outcome remains **PARTIAL_REPRODUCTION**. The local audit reproduces the archived MIFlu aggregate, identifies invalid physical-unit conversion and misleading lead-time interpretation, exposes unresolved peak provenance and a scheduler shift, and executes an expanded numerical suite plus a transparent hybrid feasibility test. It does not establish that the text pathway helps or is useless, close the paper-level gap, or deliver an executed SOTA-LLM frontier. Those questions remain empirically open. The supplied code, prediction arrays, configuration hashes, tables, logs and figures make the completed work reviewable without claiming experiments that could not run.

## Figures

![Per-window MSE comparison](figures/per_window_MSE.png)

Figure 1. Newly executed model-window MSE; each bar averages actual leads 1…L and three seeds. This is not a terminal-lead chart.

![Peak timing and intensity diagnostic](figures/peak_scatter.png)

Figure 2. k=1 matched-peak PTE/PIE means; marker area reflects event hit rate. Censored timing failures and repeated seasons limit interpretation.

![CPU cost and error frontier](figures/cost_accuracy_pareto.png)

Figure 3. Mean CPU training/validation wall cost versus aggregate error. Historical GPU results and incomplete hybrid cost are excluded. Shared-host concurrency limits precise cost comparisons.

![Actual MIFlu lead profiles](figures/miflu_actual_leads.png)

Figure 4. Archived MIFlu actual forecast lead k within each L model. Complete values and valid origin counts are retained in CSV.

## Reproducibility and evidence map

| Claim / output | Original evidence or computation |
| --- | --- |
| Official data identity / split / scaler | `02_author_repo/code/dataset/illness/national_illness.csv`; `03_data/scaler_miflu_author966.json`; `results/scaler_verification.csv`, `window_counts.csv` |
| Archived eight-model aggregate and per-L scores | `08_paper_tables/TRACK_C_TEST_MSE_RANKING.csv`, `TRACK_C_PER_HORIZON_CHAMPIONS.csv`, `TRACK_C_PER_SEED_RANKINGS.csv` |
| Independent MIFlu MSE/MAE and physical target errors | 12 `04_benchmark/miflu/.../test_predictions_*.csv`; `code/audit.py`; `results/verified_miflu_cells.csv` |
| Archived peak per model/L | `04_benchmark/PTE_PIE_per_peak.csv`; `code/common.py:peak_summary`; `results/B3_legacy_k1_per_model_L.csv` |
| MIFlu true-lead shared-support peaks | Raw MIFlu predictions; `results/common_support_peak_events.csv`, `common_support_peak_summary.csv` |
| Prior scheduler experiment | `05_reproduction_audit/R1C_RESULTS_PER_CANDIDATE.csv`; `results/R1C_existing_24_fits.csv`, `R1C_per_L_means.csv` |
| New schedule shift | Author `main_ILI_lora.py` + `utils/tools.py`; R1C trainer; `code/scheduler_contract.py`, `results/scheduler_timeline.csv` |
| New classical/neural metrics | `results/expanded`, `timesnet`, `autoformer`: cell prediction NPZs, selected neural state, metric/selection/cost JSONs and logs |
| New hybrid | `protocol/hybrid_config.json`; `code/run_hybrid.py`; `results/hybrid`: gate candidates, predictions, costs |
| New all-model tables | `results/expanded_all_cells.csv`, `expanded_all_per_L.csv`, `expanded_all_peak_events.csv`, `expanded_all_peak_by_L.csv` |
| Figure inputs | CSVs named in `code/build_supplement.py`; figures also supplied as vector PDFs |
| Mechanism boundary controls | `code/mechanism_probe.py`; `results/mechanism_probe.json`; not a pretrained MIFlu replay |
| Preserved authoritative report | DOCX SHA256 `73f97cc2439f56950b37fa9a8726cac1f84e375b54553700f93b2f196b2ea5f6`; MD mirror retained unchanged in the input archive |
| Missing / blocked evidence | `results/llm_execution_status.csv`; README continuation instructions |

All numerical table values derive from CSV/JSON files or the supplied paper's Table V. Display rounding is four decimals for MSE/MAE and two for percentages. NA means unavailable, not a zero-valued metric. `TABLES.md` repeats the numerical tables for convenient copying. The frozen input zip is included unchanged in the delivery bundle.
