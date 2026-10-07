# CodeBuddy Stage 4: implement, verify, then execute within recorded authorization

This continuation incorporates the user's corrected Stage 3 summary. ChatGPT has not independently inspected the project's Stage 3 files. CodeBuddy must ground execution in the actual files and logs. Sending this prompt instructs CodeBuddy to perform the reversible implementation and verification work below; it does not itself grant an unspecified GPU budget or approve unresolved scientific decisions.

---

Continue my EE4080 MIFlu recovery at Stage 4. Read the current recovery plan/master prompt, `recovery/STATE.md`, `recovery/manifest.json`, the corrected Stage 1/2 audits, and all Stage 3 specifications, profiles, commands, patch, resource estimates, and run-matrix records. Preserve existing results and the correction history. Do not repeat completed audits unless a concrete inconsistency affects execution.

## 1. Use the corrected evidence

The current summary reports one real 19-week gap in the 1,025-row snapshot: 2002w21–39, between rows 19/20. Twenty training input windows cross it; targets and lead times do not. The author dataset is calendar-dense. Earlier apparent gaps at week-53 transitions were calendar-label artifacts. Use the canonical epiweek mapping and saved checks as the authority, not the superseded gap script.

Clarify indexing in documentation: for zero-based input-start indices 0–19 and T=104, the corresponding forecast-origin indices are 103–122. Do not label input-start rows as forecast origins. Describe the affected inputs as 104 observations spanning 123 calendar-week slots, rather than 104 consecutive weeks.

This finding removes the asserted target-gap and seasonal-lag defects; it does not prove that irregular early training inputs have zero modeling effect. Retain the existing study with that disclosed limitation. Do not impose wholesale retraining or an extra sensitivity experiment by default. Any optional sensitivity belongs to a separately specified retrospective analysis.

The project has already run author data through its corrected model, including job 514859 and a `control966` run. Remove any remaining unsupported claim that track A was never attempted. A0 released-code replay remains uncompleted. Existing author-data runs may still fail to cover the new controlled matrix; determine this from provenance, not labels alone.

## 2. Apply reversible changes and build the runners

Inspect repository status and use an isolated branch/worktree or equivalent versioned working area. Preserve dirty work. Review `recovery/stage3/author_data_adapter.patch`, run `git apply --check`, and apply it only when the check passes and the patch matches the specified behavior. If it does not apply, resolve the specific conflict in isolation; do not force-apply, reset, or overwrite unrelated work.

Verify that the adapter introduces explicit, hash-pinned dataset profiles rather than merely deleting the 1,025-row guard. Preserve column meanings/order, split boundaries, embedding alignment and cache separation, and versioned output paths. Parameterizing a date range must not cause prompt summaries to incorporate future target values or synthetic date labels to be treated as verified calendar dates.

Implement the two thin runners specified in Stage 3 for NLinear and deterministic references. Reuse the existing model definition and documented training behavior where appropriate. Do not silently introduce a different NLinear architecture while extracting it from `innovation/`. Keep model code, data preparation, checkpoint selection, and metrics consistent with the frozen A2 protocol.

Treat applying the reviewed patch and implementing these local reversible runners as engineering work requested by this prompt. Do not require a new supervisor decision solely because earlier notes named these steps `D-adapter` and `D-nlinear`. Preserve any genuinely applicable access restriction or scientific dependency. Do not assume GPU or Test-evaluation authorization follows from completing the code.

## 3. Verify concrete failure risks

Run focused CPU checks on synthetic or permitted development inputs, without full training or new Test scoring:

- Author and project profiles remain distinct and enforce their expected hashes, shapes, and feature order.
- All target windows stay inside their assigned split; training scalers use training rows only.
- All seven variables are evaluated by the corrected runner and all eligible samples are retained.
- Validation determines the saved checkpoint; the selected state is copied/saved correctly and restored for evaluation. No Test call occurs in A2 training or selection.
- LoRA modules and trainable/frozen parameter names/counts match the resolved configuration.
- Different text tensors actually reach the corrected model; deterministic output sensitivity is checked where locally available dependencies permit it. Distinguish tensor dependence from useful semantic information.
- Full and no-text variants differ only as specified. Record any token-count/position changes; a pathway-removal ablation alone does not isolate semantic content.
- Last Value and Seasonal Naive never read future observations, including leads 53–60. Use the canonical calendar checks already established rather than reopening resolved week-53 issues without cause.
- Extracted NLinear predictions match the original implementation for identical weights and inputs, allowing a stated numerical tolerance; no GPU retraining is required for this check.

Avoid large downloads or full GPT-2 training for a CPU preflight. If an actual-model check requires unavailable weights, mark that specific check blocked and prepare it for the authorized compute-node preflight. Do not substitute a toy test and report an end-to-end pass.

## 4. Resolve reuse and the split before launching

Read job 514859, `control966`, and the 1,025-row paper-window run's actual configurations, logs, checkpoints, and prediction metadata. Determine what “control” means and confirm metric scale, variables, seed, horizon, architecture, and checkpoint rule. Do not compare 1.379 and 2.238 as interchangeable estimates until these dimensions match.

Build a reuse map against the 45 proposed rows: A0 diagnostic (1), A2 learned fits (36), and baseline evaluations (8). These are 45 planned experiment/evaluation records, not 45 GPU training jobs.

For each row classify `REUSE_EXACT`, `REEVALUATE_EXISTING`, `NEW_FIT`, or `BLOCKED`, with a reason. Historical split 676/96/194 differs from proposed 676/97/193. Identical training rows alone do not make validation-selected checkpoints equivalent. A compatible complete checkpoint history may permit selection under the new validation rule; document that as a retrospective reanalysis, verify the selection inputs, and do not pretend the original selection used that rule. Reuse complete matching predictions only where the target mask and estimand permit it.

Use 676/97/193 as the recommended candidate A2 profile because of the documented author convention, not because of its observed scores. Retain 676/96/194 as the historical profile. If `D-split` remains unresolved, prepare/check the candidate profile but do not launch dependent A2 fits or mark the recommendation approved. Record any already-documented approval without asking for it again.

Keep A0 metrics separate from corrected seven-variable A2 metrics. Run A0 in an isolated pinned author checkout with a ledger of strictly necessary compatibility edits. If missing dependencies or caches prevent a literal replay, report a blocker; an invented replacement is a reconstruction, not verbatim replay.

## 5. Honor the execution boundary

After local implementation and preflight, check the recorded authorization for: dataset/split and protocol, the remaining matrix, compute ceiling, and permitted evaluation. Read existing session/project decisions; do not invent approvals. Finish all unblocked engineering work before reporting any remaining decision needed.

If execution authorization is absent, stop at `READY_FOR_AUTHORIZED_LAUNCH` with exact commands, checked prerequisites, the reduced matrix, resource estimates, and only the unresolved decisions. Do not submit jobs merely because commands exist or the budget seems small.

If authorization already exists, continue without asking again: use the allowed compute node and scheduler, confirm the required GPT-2 cache and pinned revision, and run a bounded development preflight before dispatching the approved matrix. Do not train on a login node or silently download/upgrade a model. Record preflight compute separately; do not add uncounted fits to the budget.

Treat the reported 8 s/epoch, 0.88 GB, and approximately 1.2 GPU-hours as evidence to verify for comparable configurations. Record whether memory is allocated, reserved, peak, or device-wide, and whether timings include validation and embeddings. A0 with full fine-tuning may have different resource needs from LoRA A2. Do not extrapolate one memory figure to all variants.

Use deterministic run IDs, unique outputs, queue/completion checks, and resumable status. Reuse a successful preflight fit only if its complete protocol matches a planned run. If hardware requirements or projected total exceed authorization, complete unaffected work and pause the affected launch; do not shrink scientific settings silently.

## 6. Preserve evaluation integrity

Freeze the resolved protocol and code/data/configuration hashes before the training batch. Select checkpoints using validation only. Store predictions by run, seed, origin, lead, and variable with enough metadata to reproduce every metric.

Keep Test scoring in a separate step after the prespecified selection is complete. Existing author/project Test periods have already influenced the research history; new evaluations there are retrospective. Freezing this rerun improves discipline but does not make those periods fresh. Any genuinely untouched future holdout requires its own approved sealed protocol.

The A0 diagnostic may intentionally reproduce the released Test-every-epoch behavior only within its specifically authorized retrospective replay. Do not transfer that behavior into A2 or use A0 Test results to tune A2.

Report full MIFlu versus NLinear as a system comparison and full versus no-text as the specified ablation. Preserve seed-level losses; averaging predictions across seeds creates an ensemble and is a different estimand. Do not infer universal LLM superiority/inferiority, semantic text benefit, or statistical equivalence from a three-seed table.

## 7. Deliver and record the actual state

Under `recovery/stage4/`, write the applied-code diff and configuration hashes, `preflight_report.md`, `reuse_map.csv`, and the executable reduced run matrix/commands. Update the existing state and manifest without erasing corrections or historical results.

If jobs are authorized and run, additionally maintain `execution_ledger.csv`, predictions/results, and a concise comparison report with evidence limits. Record actual transitions such as `PREPARED`, `PREFLIGHT_PASSED`, `READY_FOR_AUTHORIZED_LAUNCH`, `SUBMITTED`, `RUNNING`, `COMPLETED`, and `FAILED`; preparation is not execution and job completion is not scientific validation.

Finish with: code changed and why; checks actually run; existing results reused and why; new fit/evaluation counts; remaining approval/dependency blocks; and actual compute/jobs/evaluations performed. Do not claim this prompt itself supplies missing scientific or GPU approval. Do not reopen resolved decisions, repeat completed stages wholesale, or add models and experiments beyond the approved scope.
