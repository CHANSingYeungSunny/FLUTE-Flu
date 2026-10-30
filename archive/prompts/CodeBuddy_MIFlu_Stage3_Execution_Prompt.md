# CodeBuddy Stage 3 execution prompt

Purpose: convert the completed data and implementation audits into an executable, minimal rerun package. This continuation narrows the earlier master prompt to preparation only: no GPU jobs, training, or new Test evaluation.

The instructions below are based on the user's Stage 2 summary. The underlying audit files were not available in this ChatGPT workspace for independent inspection; CodeBuddy must use its actual project files as evidence.

---

Continue the EE4080 MIFlu recovery project at Stage 3. Read the current master execution prompt and recovery plan, then read the actual files below in your project workspace:

- `recovery/STATE.md` and `recovery/manifest.json`
- `recovery/data_identity_report.md`
- `recovery/implementation_audit.md`
- `recovery/window_manifest.json`
- `recovery/result_disposition.csv`
- `recovery/smoke_text_visibility.py` and `recovery/audit_windows.py`
- Relevant project model/configuration files, the pinned author code, and commands/logs establishing executed configurations.

Do not restart completed audits wholesale. Check provenance and resolve only contradictions or gaps that affect the next experiment. Produce concrete configuration files, command specifications, resource estimates, and a rerun decision package. Do not stop at a narrative recommendation.

## Scope and authorization

This stage authorizes inspection and creation of preparation artifacts under `recovery/stage3/`, plus appended Stage 3 status in the existing state and manifest files. Preserve earlier evidence and decisions.

Do not modify production model/data-loader code, existing datasets, results, checkpoints, or frozen configurations. If a code change is required, provide an unapplied patch and its proposed verification commands. Do not submit scheduler jobs, launch training on CPU or GPU, download large model weights, evaluate additional Test predictions, or unseal a future holdout. Small CPU-only configuration parsing and window-arithmetic checks are permitted if they do not train or expose held-out outcomes.

This is preparation with artifact writes, not literally a read-only filesystem session. Existing scientific approvals remain valid; proposed runs remain proposed. Map unresolved decisions to affected jobs rather than treating all 12 supervisor questions as prerequisites for every task.

## 1. Correct the evidence and claim labels

Use the audit evidence to distinguish:

1. Released source behavior under specific flags and defaults.
2. Behavior of the actual configurations run in this project.
3. Behavior described in the paper.
4. Behavior demonstrated by a synthetic mechanism test versus an end-to-end author-model test.

Do not call the project implementation “paper-faithful” merely because it repairs apparent defects. Use “project reconstruction with documented deviations” until a component-level comparison supports a stronger description. Specifically document text-first ordering, positional encoding, channel treatment, forecast head, normalization, prompt content, LoRA/freezing, and selection procedure. Joint seven-channel prediction versus a channel-independent implementation can change the architecture even when both predict seven variables.

If the smoke script reconstructs a causal-attention mechanism rather than importing the actual author model, state that explicitly. A bit-identical prefix supports the mechanism tested; it is not an end-to-end reproduction or evidence that the paper used that implementation. Under the audited causal graph, suffix text cannot influence retained prefix outputs if no other computational path exists; identify that condition.

Record default `multimodal`, `PEFT`, and epoch settings separately from flags in actual run commands. A default does not prove what the authors ran. Distinguish Test monitoring, Test-based checkpoint choice, checkpoint-copy defects, and last-epoch reporting; these have different consequences.

For the reported 72 revised weeks, retain “revision” only if provenance supports it; otherwise report “72 overlapping weeks with value differences.” Identify affected variables and the verified alignment rule. Do not infer historical vintages solely from numerical disagreement.

## 2. Resolve the 19-week gap's consequences before proposing reuse

Read the exact missing epidemiological weeks from the identity audit. Do not assume they form one contiguous hole. Determine whether the project pipeline preserves calendar gaps or compresses remaining rows into a falsely regular weekly sequence.

For each horizon and split, report:

- Number of origins whose 104-week input crosses a gap.
- Number whose target sequence crosses a gap.
- Number whose nominal lead does not equal elapsed calendar weeks.
- Consequences for a 52-row Seasonal Naive lag and any calendar features or prompt statistics.
- Counts and identities of unaffected origins.

Use dates/epiweek keys and metadata, not held-out error patterns. Report existing dense-row counts separately from calendar-valid counts. The split lengths 676/97/193 are observations per split, not horizon-specific window counts.

Where applicable, verify the dense, contiguous 966-row reference counts before feature expansion and dropped batches:

| Horizon | Train origins | Validation origins | Test origins |
|---|---:|---:|---:|
| 24 | 549 | 74 | 170 |
| 36 | 537 | 62 | 158 |
| 48 | 525 | 50 | 146 |
| 60 | 513 | 38 | 134 |

These counts assume T=104, split lengths 676/97/193, earlier observed context allowed, and all target weeks inside the assigned split. Do not apply them where the actual protocol differs.

Recommend a calendar-safe policy with explicit consequences: for example, exclude every origin lacking a fully observed contiguous input and target sequence, or propose a separately justified regularization/imputation method. Do not silently fill gaps or replace the fixed snapshot with refreshed API values. Any later training imputation must respect origin-time information; do not impute missing Test targets and score them as observed truth.

Classify reuse according to dependency. If incorrect windows entered training or validation-based selection, repairing scoring alone does not repair that fitted experiment. Conversely, do not automatically discard models whose training and selection were unaffected. Preserve old compressed-row results as historical results with the corresponding limitation.

## 3. Define the smallest experiments that answer distinct questions

Do not expand `A0/A1/A2 × horizons × seeds` automatically. These are provenance categories, not necessarily three distinct model architectures.

Prepare this staged proposal, adjusting only when evidence requires it:

**A0: Released-code diagnostic.** Propose one horizon and one seed/configuration first. State whether the replay uses released defaults or an evidence-supported paper command. Preserve algorithmic behavior; list minimal environment compatibility changes. Identify missing imports, embeddings, prompts, or dependencies as blockers. Separate literal execution feasibility from reproduction of a paper-table number. Expand to four horizons/repetitions only if it answers a necessary scientific question. A0's feature-zero metric is not a seven-variable benchmark score.

**A1: Paper-method reconstruction.** Produce the paper-to-code discrepancy ledger and a configuration only to the extent supported by evidence. If critical methods remain ambiguous, mark the paper-reproduction claim blocked while completing other preparation. If the candidate configuration is identical to an A2 run, reference that run once rather than scheduling duplicate training; explain which claims it can support.

**A2: Controlled author-data comparison.** Propose project-reconstructed MIFlu, its precisely defined no-text ablation, and NLinear on the same author dataset, seven-output task, eligible origins, scaling, and validation-selection policy. Four horizons × three prespecified seeds × three learned configurations = 36 fits, plus Last Value and Seasonal Naive for each horizon. Verify seed choices against the frozen seed list; never choose favorable seeds. This is a minimum comparison, not ten-repetition paper reproduction.

Define “no text” precisely. Removing tokens changes positions and sequence length; the resulting contrast measures the whole text pathway. If the scientific claim concerns information in the text, specify an additional matched-length content control or explain the identification limitation. Keep this optional control separate from the minimum fit count. No-text MIFlu still contains a forecasting LLM.

**B: Fixed-project-snapshot repairs.** Include only reruns justified by the gap, revisions, training/selection integrity, or other demonstrated dependencies. Evaluate whether a same-calendar-period comparison is needed to separate snapshot-value differences from date-range and split differences. Running two differently sized datasets with percentage splits does not isolate the effect of revisions.

**C: Generalization status.** Preserve the original three-model holdout comparison and its original selection history. Mark subsequent evaluation on that period retrospective. Identify any genuinely untouched-period proposal without inspecting its outcomes. Do not treat a subset of already-exposed dates as fresh.

Do not add DeepSeek, newer Qwen models, or all-eight-model reruns by default. Put broader experiments in a separate full-compute option with incremental counts and scientific purpose. Preserve overlap and avoid double-counting fits.

## 4. Make the author-data adapter concrete without applying it

Locate every assumption behind the 1,025-row guard. Prepare an unapplied minimal patch that replaces dataset-specific assumptions with explicit dataset profiles and validated split/origin manifests. Do not simply delete the assertion or globally replace 1,025 with 966.

The proposed adapter must address dataset hash, column meaning/order, dates versus canonical week identity, split boundaries, expected shapes, embedding alignment, cache keys, and output paths. Both datasets need separate immutable profiles. Identify whether each embedding is static dataset-level text, variable-level text, or origin-specific text, and whether any cached statistics depend on a split or date range.

Keep the project's architectural identity stable for the initial same-model author-data comparison. A separately named architecture correction must not be hidden in a data adapter.

Provide focused future verification commands for profile isolation, complete target containment, gap handling, train-only scaling, seven-variable coverage, validation-only checkpoint selection, and seasonal-naive leads 53–60. List the code dependencies that prevent execution until the patch is applied.

## 5. Produce exact configs and commands without pretending to execute them

Each proposed run record must specify:

- Scientific question, track/variant, and claim limitations.
- Code commit plus any required patch hash; data and profile hashes.
- Horizon, T, seed, feature order, split and origin-mask identifiers.
- Backbone and embedding revision; text mode; parameter-freezing/LoRA configuration.
- Optimizer, learning rate, scheduler, batch size, maximum epochs, selection objective, and checkpoint rule, with evidence or explicit assumption labels.
- Metric definition, feature coverage, origin weighting, scaling/inverse scaling, and Test exposure status.
- Exact output directory, prerequisites, command, estimated resources, and execution status.

Use actual entry points and supported arguments found in the workspace. For a missing capability, provide the corresponding proposed patch and mark the command `BLOCKED_PENDING_PATCH`. Never invent an apparently runnable flag or hide unresolved choices in a command described as ready.

Keep templates separate from complete launchable commands. Prevent preparation scripts from submitting jobs by default; generate job files rather than executing them. Do not use shell tracing that could expose credentials. Give existing runs stable identifiers and avoid overwriting their outputs.

## 6. Resource estimates and decision gates

Estimate training time and memory from comparable logged runs on identified hardware. Separate measured quantities from extrapolations. Include training, validation, embeddings, search/retries where applicable, storage, total GPU-hours, and wall time under stated concurrency. Do not assert a memory or time number without a basis. If no suitable measurements exist, state `UNMEASURED` and provide a bounded future pilot proposal; do not run it now.

Map every pending supervisor decision to specific blocked run IDs. Recommend defaults for review, but do not record them as approved. Prioritize: target/metric, reconstruction naming, minimum scientific scope, gap policy, compute budget, and exposure/holdout policy. Defer unrelated optional-model questions so they do not block preparation of the core experiment.

Prepare a short answer to Ben: author-data consistency and the project snapshot differ; the released implementation and project reconstruction also differ; the next controlled author-data comparison separates these issues. NLinear versus MIFlu does not identify the causal effect of text. Full MIFlu versus its controlled ablation is the relevant within-model comparison. Do not claim the original paper is disproved.

## 7. Deliverables and stopping point

Create under `recovery/stage3/`:

1. `stage3_rerun_spec.md` — recommended minimum matrix, separate full-compute expansion, evidence limits, and dependency-based decision tree.
2. `run_matrix.csv` — one row per concrete proposed fit/evaluation, plus a clearly separated blocked/options inventory if needed; reconcile totals.
3. `configs/` and `commands.md` — resolved configurations and exact commands with prerequisites and execution status.
4. `author_data_adapter.patch` — only if required, explicitly unapplied, with proposed checks.
5. `resource_estimate.md` — evidence-based estimates and unknowns.
6. `supervisor_brief.md` — concise findings, recommended scope, old-result status, and decisions tied to affected runs.

Append Stage 3 output references and next actions to `STATE.md` and the manifest without erasing Stage 1/2 history. Update result dispositions only where new evidence requires it, preserving earlier entries or a change log. Exposure and validity are separate properties: `EXPOSED` does not itself mean scientifically invalid; `SUPERSEDED` must identify what supersedes the result and why.

Complete permitted static/configuration checks and report their actual results. Distinguish `PREPARED`, `CHECKED`, `BLOCKED`, and `NOT_EXECUTED`; do not mark proposed training or Test evaluation complete. End with the smallest recommended run matrix, justified reuse/retraining decisions, exact blocking approvals, and the ready-to-run commands or explicit reasons they are not ready. State that no GPU jobs, training, or new Test evaluation were launched. Stop at this preparation boundary.
