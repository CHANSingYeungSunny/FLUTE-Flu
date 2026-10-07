# CodeBuddy master execution prompt: EE4080 MIFlu research recovery

Copy everything below the separator into CodeBuddy. Give CodeBuddy access to the project workspace and these two companion files: `EE4080_MIFlu_Research_Recovery_Plan.md` and `CodeBuddy_MIFlu_Recovery_Prompt.md`. The recovery-plan PDF is an alternative rendering, not additional evidence. This prompt directs execution; it does not certify that the proposed experiments have supervisor approval.

---

You are the independent research engineer and critical reproducibility auditor for my EE4080 FYP. Execute the research recovery work described in the supplied recovery plan and earlier CodeBuddy prompt. Read both completely before changing code. Do not merely summarize them or write another high-level plan. Produce an evidence-backed audit, implement the necessary reversible corrections in an isolated working area, verify them, and execute the experiments that are unblocked and within the established compute authorization.

## 1. Objective and operating rules

My original goal was to reproduce and extend “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” using the author repository at `https://github.com/Jmoon3108/MIFlu`.

My completed study instead used a fixed July 2026 CMU Delphi FluView national ILINet snapshot with 1,025 weekly observations and seven variables. It used input length 104, forecast horizons 24/36/48/60, chronological train/validation/Test separation, train-only scaling, frozen seeds, validation selection, and an originally frozen three-model Test comparison. Models screened were NLinear, DLinear, PatchTST-inspired, iTransformer, GPT-2 MIFlu, Qwen Time-LLM, CALF, and TimeCMA, plus Last Value and Seasonal Naive references. Verify these statements against actual artifacts; do not assume the implementation fulfilled the stated protocol.

Preserve three distinct scientific tracks:

- **A — Author-data reproduction:** author data and evidence-supported paper configuration, with explicit reproduction limitations.
- **B — Refreshed-data benchmark:** the fixed July 2026 project snapshot, with its actual data vintage and retrospective evaluation status.
- **C — Extended generalization:** the original holdout result in its historical context, and any separately defined, genuinely untouched future evaluation.

Preserve every existing result, dataset, checkpoint, prediction, log, and configuration. Archive by reference, hashes, and manifests where practical; do not duplicate large immutable artifacts unnecessarily. Never delete results, overwrite the original snapshot, reset existing work, silently replace implementations, or relabel an exposed Test set as untouched.

The prior plan contains research findings and proposals, not infallible facts or blanket approval. Independently verify consequential findings. Distinguish `observed`, `inferred`, `runtime_verified`, and `unresolved`. The paper establishes reported methods and claims; repository code establishes released behavior; execution artifacts establish what my study actually ran. Record contradictions instead of silently selecting a convenient source.

Follow applicable workspace instructions and existing authorization. Proceed autonomously with read-only audits, isolated reversible fixes, CPU checks, and permitted small development checks. Do not interpret a proposed run matrix as approval for unlimited GPU work. If compute authorization, a scientific decision, or a required file is missing, complete independent work and identify only the blocked branch. Do not contact authors or supervisors, publish results, or access a sealed final evaluation without authorization.

## 2. Establish the workspace and evidence ledger

Locate the two companion files, paper, author checkout, project data, preprocessing code, model implementations, split manifests, run configurations, training logs, predictions, checkpoints, result tables, and available compute instructions. Search the workspace before asking for paths. If a companion file is absent, state that explicitly; use this prompt for unblocked work without pretending to have read it.

Create a dated recovery directory and, where supported, an isolated Git branch or worktree. Preserve dirty working files. Record repository remotes, commit IDs, environment versions, hardware, and SHA-256 hashes for datasets and configurations. Record actual extraction timestamps from evidence rather than inferring them from a filename.

Maintain a concise `STATE.md` with completed steps, evidence paths, unresolved decisions, running jobs, failures, and the next executable action. Maintain one machine-readable manifest connecting each result to its data, split, code, configuration, seed, checkpoint, metric definition, and evaluation exposure status. Use deterministic run identifiers so resuming does not duplicate completed or queued work.

## 3. Execute the data identity audit first

Freeze the existing project snapshot. Obtain and pin the author repository if access is available; otherwise report the access limitation. Do not refetch FluView and substitute its current values for the July snapshot. Any API request is a separately named extraction with parameters, response metadata, issue/lag information, and retrieval time preserved.

For `national_illness.csv`, `national_illness_orig.csv`, and the project snapshot:

1. Record hashes, rows, columns, dtypes, date ranges, nulls, duplicate dates, invalid values, and ordering. Compare both byte identity and parsed numeric identity.
2. Construct an evidence-backed data dictionary covering variable meaning, unit, numerator/denominator, aggregation, geographic scope, missing-value rules, column order, scaling, and transformations.
3. Investigate the proposed mapping: processed columns 1–6 may represent weighted ILI, unweighted ILI, age 0–4 ILI count, age 5–24 ILI count, total ILI count, and provider count; `OT` may be total patients. Verify against original headers, source definitions, and numerical identities. Do not assume `OT` is ILITOTAL or a single disease target.
4. Recover epidemiological-week semantics. Verify whether author date labels are synthetic and whether project dates use MMWR, ISO, or another convention. Do not choose a calendar shift by maximizing correlation. If week identity cannot be established, report overlap identity as unresolved.
5. Once alignment is justified, compare every overlapping week and variable: exact matches, differences within a declared rounding tolerance, nontrivial differences, maximum/median absolute differences, relative differences with a safe zero rule, first/last mismatches, and missing or additional weeks. Save row-level discrepancies.
6. Separate observations from causes: revisions/backfill, field mismatch, calendar mismatch, filtering, rounding, and transformations are different hypotheses. Claim historical revision only with supporting vintage evidence.

The earlier audit reported 966 author rows, identical parsed values in the two author CSVs, and regular stored labels from 2002-01-01 to 2020-06-30. Recheck rather than hardcode these findings. Explain whether the difference from 1,025 rows is only range extension, overlapping-value differences, missing weeks, or unresolved alignment.

Structural integrity checks may cover held-out dates and schema, but do not inspect model errors or outcome patterns on a genuinely sealed future Test set to make design choices. Keep sealed outcomes out of development reports.

## 4. Audit released MIFlu and the project implementation

Trace the actual execution path, not just classes that exist in the repository. Identify the selected CSV, loader, feature mode, normalization, prompt construction, embedding cache, backbone revision, parameter-freezing policy, LoRA settings, forecast head, optimizer, scheduler, stopping rule, and metric aggregation. Check whether dependencies, prompt text, caches, and scripts are sufficient for clean execution.

Specifically verify the earlier plan’s potential defects:

- Does the selected Test dataset enumerate all seven variables, or only feature zero because feature expansion differs between training and Test?
- Are validation or Test samples omitted through `drop_last`, and does validation shuffling change the evaluated subset?
- Does training inspect Test each epoch, select a checkpoint using Test, or report an epoch inconsistent with the saved checkpoint? Are best states safely copied and repetition-level state reset?
- Are all intended frozen GPT-2 parameters actually frozen? Is train/eval mode restored correctly?
- Are text embeddings appended after time-series tokens while the output retains only the time-series prefix? Under causal attention, can the forecast output depend on text at all?
- Do embedding-generation filenames and loaders match? Can the stated text embeddings be regenerated from documented prompts and available dependencies?

For text dependence, run a small deterministic development-only test: fixed weights, identical time-series inputs, identical token count and positions, evaluation mode, dropout disabled; substitute clearly different text embeddings and compare outputs. If feasible, inspect gradients or computational dependencies as additional evidence. First verify that the supplied text actually changes the tensor entering the model. Report tolerance and limitations. Equal outputs in one test are evidence, not universal proof. Do not attribute training differences caused by sequence length or random-number consumption to semantic text benefits.

Inspect the project’s window construction and all eight model adaptations. Preserve the “PatchTST-inspired” label unless canonical fidelity is established. Verify Time-LLM, CALF, and TimeCMA mechanisms and losses, rather than treating a model filename as proof of implementation fidelity.

Use small, meaningful checks for these concrete risks. Do not spend time constructing a broad test suite unrelated to the recovery decisions.

## 5. Define reproduction variants without conflating them

Maintain separately named configurations and result tables:

- **A0: Released-code replay.** Preserve author behavior to diagnose what the pinned repository actually produces. Any Test-driven selection is disclosed and does not support an independent generalization claim.
- **A1: Paper-method reconstruction.** Implement evidence-supported paper settings and document every missing detail, assumption, compatibility change, and discrepancy. Do not call a reconstruction an exact numerical reproduction.
- **A2: Corrected evaluation or architecture variant.** Repair demonstrated evaluation defects. Any change that makes text causally accessible, such as reordering tokens, changes the model and requires a named variant; it is not a silent reproduction fix.

Extract a paper-to-code configuration matrix and ablation table with precise citations. The earlier plan identifies national paper targets at horizons 24/36/48/60 as MSE 1.542/1.422/1.414/1.364 and MAE 0.726/0.779/0.757/0.719; verify against the paper before using them. Verify input length, split, patching, GPT-2 depth, LoRA, learning rate, epochs, batch size, and repetitions. Do not fill missing settings from memory.

Report numerical deltas from paper targets, together with differences in evaluated variables, origins, scaling, and checkpoint selection. A similar number under a different estimand is not successful reproduction. Assess national reproduction first; report separately whether regional, few-shot, baseline, and embedding results are reproducible from available artifacts.

Explain what the paper’s ablations actually isolate. Removing text while retaining the forecasting LLM is not removing the LLM. MIFlu versus NLinear does not isolate the effect of text. Do not infer significance or beneficial interaction from point estimates alone.

## 6. Decide which existing results can be reused

Create a result-level dependency and disposition table: `retain`, `retain_with_relabeling`, `recompute_metrics`, `reevaluate_checkpoint`, `retrain`, or `blocked`, with evidence and affected scope.

Apply these rules:

- A different but correctly processed snapshot does not invalidate a benchmark on that snapshot; it changes the reproduction claim.
- A reporting, unit-conversion, aggregation, or origin-mask error may require only recalculation from complete saved predictions.
- An inference loader or feature-coverage error may require checkpoint reevaluation if training and selection were sound.
- Errors affecting training labels, training normalization, permitted information, checkpoint selection, or model computation can require retraining of dependent runs.
- A representation-preserving rename or proven consistent column permutation need not trigger retraining.
- An invalid baseline should be corrected without automatically discarding unrelated model results.
- Previously inspected Test results remain exposed after every repair. Retraining or changing a random seed does not restore independence.

Do not conclude that all eight models were beaten on Test when only three were evaluated. Keep the original holdout result and its selection history visible, while labeling new analyses on the same period retrospective.

## 7. Implement and freeze the evaluation protocol

Write a machine-readable protocol before consequential reruns. Include data hashes, canonical week mapping, explicit split dates/indices, eligible forecast origins, variables, horizons, seeds, model revisions, hyperparameter search budgets, selection objective, checkpoint rule, metrics, information availability, compute ceiling, and Test exposure status.

For origin `o`, use input `[o-103, o]` and targets `[o+1, o+L]`. All target weeks must lie inside the assigned split. Earlier observed inputs may cross a split boundary in a rolling evaluation; target labels may not. Assert counts before feature expansion and batching. Resolve reported 717/102/206 versus possible 717/103/205 boundaries from actual code and artifacts. Do not impose a split merely because it appeared in the earlier plan.

Fit transformations on training data only. Calculate prompts and statistics from information available at each origin. Audit externally generated summaries and cached embeddings for target-period information. Distinguish a fixed revised-data retrospective study from an as-of-vintage operational simulation; record checkpoint pretraining timing without asserting contamination without evidence.

Implement Seasonal Naive recursively for horizons above 52. For a declared 52-week cycle and one-based lead `k`, the repeat-last-observed-cycle reference is `y[o-51 + ((k-1) mod 52)]`; it must never read an actual observation after `o`. Declare treatment of 53-week epidemiological years. Verify Last Value similarly.

For a future benchmark, prefer all eight prespecified models plus the two references if budget supports a fair implementation and search. Validation-selected family representatives answer a narrower question and are acceptable if selection is fixed before Test access. For the already-exposed historical Test, further models can be reported only with the appropriate retrospective qualification. Do not imply that evaluating all models itself causes leakage; outcome-driven subsequent design and selection are the concern.

Use bounded, architecture-appropriate tuning with a common selection objective and documented information access. Identical learning rates or training epochs are not sufficient fairness. Report total/trainable parameters, pretrained revisions, precision, GPU time, memory, embedding cost, and search cost. Select no model or seed because it looks favorable on Test.

Do not add DeepSeek or a newer Qwen model to the core recovery benchmark by default. Treat a later backbone substitution as a separately scoped experiment with explicit size, tokenizer, context, objective, adaptation, and compute controls. A distilled DeepSeek model based on Qwen does not establish an independent architecture-family comparison.

The already-opened holdout cannot become a new final Test. Identify whether any eligible untouched period exists without selecting it based on favorable outcomes. If none exists, complete a transparent retrospective study and propose a prospective evaluation. Do not manufacture a fresh Test by renaming old data.

## 8. Compute and statistical analysis

Begin with CPU audits and reuse saved predictions. Run only permitted development smoke checks before a larger launch. Measure resource use; inspect existing scheduler rules and queued jobs rather than inventing partition names or launching training on login nodes.

The proposed minimum learned-model matrix is full MIFlu, its controlled no-text ablation, and NLinear × four horizons × three prespecified seeds: 36 fits per required track, plus deterministic references. This is a proposal, not existing approval. If only two horizons are affordable, label the 18-fit study a pilot and do not report it as the four-horizon aggregate. Choose seeds independently of performance. Do not launch both data tracks automatically.

A full eight-model matrix is 320 fits per data track at four horizons and ten seeds, excluding tuning. Paper-oriented MIFlu alone is 40 fits. A four-cell text × LoRA design is 160 fits inclusive of its full-model cell; reuse compatible runs. Obtain or use documented scope and budget before substantial submissions. If blocked, prepare exact configurations, commands, and resource estimates, then continue other work.

For the new protocol, define primary MSE as the mean standardized squared error over matched origins, leads, and seven variables for each horizon, then average seed losses and weight the four horizons equally. Preserve the original study’s metric definition in its historical table. Averaging predictions across seeds creates an ensemble and is a different estimand. Report MAE and original-unit per-variable errors as secondary; do not pool heterogeneous raw units into a scientifically uninterpretable average.

Compare paired errors on identical origins. Distinguish optimization variability across seeds from temporal uncertainty across origins. For uncertainty estimation, use paired temporal block resampling with shared blocks across models and preserved seed trajectories; state block-selection rationale and sensitivity. A 60- or 104-week block proposal is not an automatic guarantee of valid inference, especially on a short, nonstationary holdout. Explain low effective sample size and regime limitations. Report effects and uncertainty without forcing significance claims.

Prespecify primary contrasts for any new confirmatory evaluation, such as full MIFlu versus NLinear and full MIFlu versus no-text. Apply an explicit multiplicity rule where appropriate. Label old-Test analyses post hoc. Do not treat seeds, variables, overlapping horizons, or selected architectures as independent replications of the whole LLM-versus-non-LLM question. Failure to reject a difference is not equivalence or proof of no contribution.

## 9. Required outputs and completion criteria

Keep outputs concise and auditable, using the following files or an equivalent coherent structure:

1. `STATE.md` and a provenance/run manifest.
2. `data_audit.md`, a data dictionary, and machine-readable overlap discrepancies.
3. `implementation_audit.md`, including paper/code/project contrasts and runtime evidence.
4. `result_disposition.csv`, identifying exactly what is reusable and what must change.
5. A frozen protocol and runnable configuration files, with approved versus proposed runs distinguished.
6. Isolated code changes and verification results for demonstrated defects.
7. Result tables and statistical outputs for completed, valid runs; explicit placeholders for unexecuted work.
8. `supervisor_brief.md`: what changed in the project’s claims, established findings, Test results with exposure labels, reproduction gaps, partial/full rerun decision, compute estimate, and specific decisions requiring Ben’s input.

The supervisor brief must address why validation leadership and holdout leadership can differ without contradicting a within-MIFlu text ablation. Give plausible explanations as hypotheses, then connect each to evidence or a feasible check. Separate architecture effects, text effects, data vintage, selection noise, and temporal distribution shift.

Carry forward unresolved scientific decisions from the recovery plan, prioritizing those that actually block execution: reproduction scope, primary target and metric, corrected-variant naming, all-model versus representative evaluation, availability of an untouched period, refitting policy, compute budget, and optional model additions. Do not reopen decisions already documented as approved.

For each phase report `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, with evidence. A written script is not an executed check; a submitted job is not a completed experiment. Record commands, exit status, result locations, failures, and reasoned deviations. Retry only genuine failures under the same scientific configuration unless a new version is explicitly logged; never replace an unfavorable completed seed with another.

Start now by reading the companion documents and inspecting the workspace. Execute unblocked steps in order, maintain resumable state, and continue until the authorized scope is complete or a specific dependency prevents further progress. Finish with verified findings, changed files, completed checks/runs, preserved-result status, remaining blockers, and the next concrete action. Do not end by asking whether I want you to begin.
