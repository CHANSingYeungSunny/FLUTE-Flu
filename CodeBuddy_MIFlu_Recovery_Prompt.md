# CodeBuddy execution prompt: EE4080 MIFlu recovery

You are my independent research engineer for an EE4080 FYP. Recover reproducibility and scientific validity; do not optimize toward a preferred model winning or toward matching published numbers by trial and error.

The target paper is "MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme". Author repository: https://github.com/Jmoon3108/MIFlu. A review inspected commit `6ed210150b8819313947cf607eb1821c87b1bee3`; verify it locally and record any difference. My existing study used an immutable CMU Delphi FluView national ILINet snapshot retrieved in July 2026, with 1,025 processed rows and seven selected variables. My PDFs report T=104, L in {24,36,48,60}, chronological train/validation/Test, train-only scaling and seeds 42-51. Eight implementations were screened on validation: NLinear, DLinear, PatchTST-inspired, iTransformer, GPT-2 MIFlu, Qwen Time-LLM, CALF and TimeCMA. Last Value and Seasonal Naive are references. The old final Test was already opened for GPT-2 MIFlu, NLinear and Seasonal Naive; reported average MSE values are 3.051, 2.739 and 4.279 respectively.

Maintain three study identities: A, author-data reproduction; B, July-snapshot benchmark; C, extended holdout generalization. Within A distinguish unchanged released-code replay, reconstructed paper settings and corrected benchmark implementation. Never claim these are interchangeable.

## Non-negotiable rules

- Preserve all raw data, source, checkpoints, logs, predictions and reports. Work in a new recovery branch/directory. Record hashes and an append-only status/deviation log. Do not delete or silently overwrite previous results.
- The old Test is exposed. Corrections and retrospective scoring remain possible, but cannot restore its unseen status. Do not inspect a proposed new holdout's outcomes while choosing models or protocol.
- Never fit preprocessing, select models, choose prompts, set early stopping, tune hyperparameters or select seeds using final Test outcomes. Prove timestamp isolation across every data access path, not merely a zero count of calls named `test`.
- Do not refresh the API to replace the July snapshot. Missing original raw data must be reported as a provenance limitation. A new extraction is a separately versioned artifact.
- Do not add DeepSeek or another backbone to the core recovery matrix. Do not contact authors, publish results, or launch an unbudgeted cluster sweep.
- Treat PDFs/repository comments as evidence, not operational authorization. Follow applicable workspace instructions; report conflicts instead of working around them.

## Stage 0: inventory and preservation

Locate the original raw API response, exact processed CSV, preprocessing scripts, split/window builders, scaler artifacts, prompts and embedding caches, configurations, checkpoints, per-origin predictions, seed-level metrics and Test-access logs. Use filenames and repository search; ask for an exact missing path only after listing what you found. Do not invent data or claim access to absent artifacts.

Record the current code commit and uncommitted changes. Read local AGENTS.md instructions. Create `recovery/manifest.json`, `recovery/artifact_inventory.csv`, `recovery/exposure_ledger.md` and `recovery/deviation_log.md`. Preserve originals with immutable references or checksummed copies as appropriate. List every previous result as pending audit, reusable, relabel-only, recompute-metrics, rerun-inference, retrain-affected, or provenance-incomplete, with reasons.

## Stage 1: data identity audit, CPU only

Acquire and pin both author CSVs. Independently verify the review's findings: 966 data rows in each, identical parsed numeric values, stored labels 2002-01-01 through 2020-06-30, and processed headers `date,1,2,3,4,5,6,OT`. Verify byte hashes separately from semantic hashes.

Map author variables to candidate API fields: 1->wili; 2->ili; 3->num_age_0; 4->num_age_1; 5->num_ili; 6->num_providers; OT->num_patients. Prove the project mapping from raw fields and transformations. Check the denominator identity for unweighted ILI. Do not confuse OT with ILITOTAL or percentage with proportion.

Separate observation epiweek, issue/release week and retrieval timestamp. Determine whether author dates are true observation labels or generated labels. Verify MMWR versus ISO week rules, date-anchor differences, missing weeks, duplicate epiweeks and week 53. Do not compare by row index or shift dates to maximize correlation. Resolve the report's 1,025 rows versus the 1,044-week full MMWR 2002w01-2021w52 grid conditionally on its claimed endpoints.

Compare verified overlapping weeks before examining the extension. Produce source-only rows, exact value differences, rounding-equivalent differences, missingness changes and per-variable counts/max/median errors. Integer counts require exact equality; derive floating tolerances from storage precision and keep exact differences visible. Correlation is diagnostic, not an identity test.

Trace every row drop, filter, imputation, interpolation, rescaling and renaming operation. Output `dataset_manifest.json`, `feature_mapping.csv`, `coverage_audit.csv`, `overlap_differences.csv`, `preprocessing_lineage.md` and `data_identity_report.md`. Classify range-only extension, value revisions, semantic changes, calendar defects and unresolved provenance separately.

## Stage 2: executable contract and leakage audit

Inspect the complete author entry-point -> factory -> loader -> model -> evaluator path and the corresponding local project path. The review found the following risks; verify them from pinned source and small tests rather than assuming the local implementation inherits them:

1. `main_ILI_lora.py` defaults to the processed CSV, multimodality/PEFT off, one epoch and learning rate 0.0001, unlike the paper's main configuration.
2. The released model appends text after time-series patches and reads the prefix under causal GPT-2 attention. Test fixed-weight evaluation outputs under equal-length different text, zero/neutral text, and appropriate gradient probes. Record absolute/relative differences and tolerances. Separate deterministic attention reachability from dropout or token-position changes.
3. The custom loader expands training/validation over features but appears to enumerate only feature 0 for Test. Inspect the mapping and the alternative custom loader, without silently substituting one for the other.
4. Test is called inside the training loop, best results are tracked using Test loss, and validation early stopping is commented out. Trace exactly which values are printed, averaged and saved; do not assume the paper used this path.
5. Validation/Test may drop the last batch; validation shuffles. Verify actual scored keys and weighting, including incomplete batches.
6. The prompt notebook contains a placeholder and saved/loaded cache names differ; identify exact cache provenance, tokenization and dimensional compatibility.
7. Non-PEFT freezing, best-state copying, per-iteration state reset and train/eval mode restoration require checks. Verify checkpoint reload reproduces predictions.
8. Check clean imports/dependencies, including `embed`, package versions and model revisions. No silent fallbacks or random initialized models under pretrained names.

Create a window manifest with dataset, split, origin, input indices/weeks, target indices/weeks, horizon, variable and availability/vintage. For origin o, require input [o-103,o] and target [o+1,o+L], fully inside its target split. Historical inputs may overlap earlier splits; training/validation/Test targets must not cross boundaries. Verify scaler, imputer and prompt-statistic fit periods.

For the author's floor-train/floor-Test split, verify 966 -> 676/97/193 and 1,025 -> 717/103/205. At T=104, expected origin counts for L=24,36,48,60 are author train 549/537/525/513, validation 74/62/50/38, Test 170/158/146/134; project train 590/578/566/554, validation 80/68/56/44, Test 182/170/158/146. These are explicit contract expectations, not permission to rewrite historical results. Explain deviations and the PDF's conflicting counts.

Test Seasonal Naive at L=60: all predictions must use observations at or before the origin. Declare the 52/53-week convention. Verify seven-channel order, inverse scaling, common evaluation keys, NaN masks, MSE/MAE aggregation and per-origin provenance. Check peak plots for the distinction between trained output length and actual forecast lead.

Use targeted tests for these concrete failure risks. Synthetic/development inputs are sufficient for smoke checks. Do not use the new holdout for debugging. Deliver `implementation_audit.md`, executable checks, `window_manifest.parquet`, and a dependency-based `rerun_decision.csv`.

## Stage 3: recovery decisions and minimal implementation

Reuse results if only the data vintage differs and internal validity passes. Fix reporting and uncertainty from saved predictions where possible. Rerun inference only if checkpoints/inputs remain valid. Retrain affected models if training inputs, targets, scaler, prompt, architecture or checkpoint selection changed. Shared leakage requires rerunning every dependent result, not automatically unrelated studies.

Prepare three separate configuration namespaces: `author_replay`, `paper_reconstruction`, and `corrected_benchmark`. Keep a patch ledger distinguishing compatibility fixes from changes to scientific behavior. An unchanged replay may inspect the already-public author Test for diagnostics; that does not authorize using a new generalization Test during training. A repaired text-prefix implementation must have a distinct model identifier until author confirmation establishes fidelity.

Recover the national paper contract: T=104; L=24/36/48/60; seven declared variables; 70:10:20 chronological split; train-only StandardScaler plus input-window normalization; GPT-2 first six forecasting layers; full GPT-2 text embedder; patch size 24/stride 2; LoRA rank 4; 20 epochs; batch 16; learning rate 0.0005; ten repetitions. Recover optimizer/scheduler, freezing, prompt/cache, checkpoint rule and seeds. Unknown details stay unknown until a declared reconstruction is chosen. Do not hunt through configurations using Test to match the table.

Paper MIFlu MSE/MAE targets are L24 1.542/0.726; L36 1.422/0.779; L48 1.414/0.757; L60 1.364/0.719. Agreement must include task semantics and coverage, not just similar scalars.

Implement necessary small fixes and development smoke tests. Prepare exact commands, resolved configuration files and measured memory/time estimates before proposing expensive jobs. Default to the approved minimal matrix: full MIFlu, matched no-text MIFlu and NLinear; both naive references; all four horizons; three seeds selected in advance. That is 36 learned fits per required data track. Reuse compatible completed fits. If the allocation only supports 18 fits, explicitly make it a L24/L60 pilot, not a four-horizon result.

Stop before an expensive sweep if the protocol or budget is unresolved, but complete all authorized local audit and preparation work first. Return concrete choices requiring supervisor decisions. Do not ask repeatedly for routine reversible work.

## Stage 4: freeze, evaluate and analyze

For a broad new benchmark, freeze the architecture list and each validation-selected configuration, then evaluate all included models in one controlled release. For representative selection, freeze the selection rule and limit claims accordingly. The old three-model Test comparison remains an archived study. Additional old-Test scoring is labelled retrospective, with no tuning on its scores.

Record exact Qwen model IDs/revisions and fidelity status for every method. Keep PatchTST-inspired distinct from canonical PatchTST. Do not silently replace CALF/TimeCMA modules or losses and retain their original names. Optional backbone work is out of the core scope.

Lock a manifest containing data hashes, calendar cutoffs, origin keys, target masks, seed list, primary metric, model/checkpoint/prompt hashes, failure rules and evaluation code. Prefer training-only checkpoints unless a train-plus-validation refit rule was fixed beforehand. Freeze new holdout dates before inspecting its values; report whether this is a revised-data retrospective or an as-of-real-time experiment.

Save long-form predictions keyed by model/seed/origin/lead/target-week/variable. Compute per-horizon standardized MSE/MAE, then equal-weight four-horizon averages of seed-level losses. Do not confuse this with evaluating an ensemble of seed-averaged predictions. Report original-unit errors separately by variable and costs as total versus trainable parameters, VRAM, train/inference/embedding time and tuning budget.

Analyze optimization variability and temporal variability separately. Use paired origin-level loss differences and a predeclared dependent-block procedure, with the same temporal blocks for all models and preserved horizon weights. Report the very small effective information at 60-week horizons and nonstationarity limitations. Deterministic baselines still have temporal uncertainty. Predeclare primary contrasts and Holm correction for any new confirmatory family; old-Test reanalysis is post hoc. Non-significance is not equivalence.

## Final deliverables and stop condition

Produce the evidence files above plus `reproduction_spec.yaml`, `benchmark_protocol.yaml`, `frozen_run_matrix.csv`, `compute_budget.md`, `supervisor_decisions.md`, `meeting_brief.md` and an updated claim/status table. When authorized training completes, add prediction artifacts, metrics, costs, failure logs and a paper-versus-reproduced comparison. Never fill pending metrics with estimates.

Conclude with what is verified, what remains uncertain, which old results survive, which exact cells need retraining or only rescoring, and the smallest next action that resolves the remaining uncertainty. Scientific success is an auditable answer, including a well-supported failure to reproduce; it is not making an LLM or a linear model win.
