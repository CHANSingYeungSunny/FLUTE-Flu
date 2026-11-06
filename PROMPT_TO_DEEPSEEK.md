# Execute the next MIFlu evidence handoff

You are continuing the MIFlu / FLUTE-Flu FYP on Burgundy. This revision supersedes older writing and handoff prompts. Read `00_START_HERE.md`, `README.md`, this prompt and `handoff_revision9/RETURN_CONTRACT.json` before changing files. Use the supplied revision 9.2 full project and focused handoff ZIP as context. If the full ZIP is too large for the chat attachment interface, read the existing local project folder and record its exact path and archive hash. Do not upload model weights, credentials or a whole Hugging Face cache to ChatGPT.

## 1. What changed in revision 9

The English manuscript is now a journal-style empirical paper with a publisher-class, locally compiled two-column LaTeX PDF and an editable Word copy. The manuscript is not a scheduler report: job numbers, DONE counts and CLI flags have been removed from the scientific narrative. The internal report and this handoff retain the operational evidence. Predictive ablation results have not been invented to fill the missing table. The 28-arm means, peak findings, parameter results and corrected historical Holm results are unchanged.

The English-only speaking notes contain the actual 606-word script with a 300-second plan, named-paper explanations and reading locators. Human rehearsal and native Microsoft Office inspection are not executed. The owner-corrected 13-slide deck and its two editable chart workbooks are retained. The Chinese internal report is now concise. All Q01–Q25, complete paper-based explanations, reading locators and references are preserved in the separate companion 01_最终报告/report_internal_qa_zh.docx / .pdf. Keep the companion separate; do not reinsert all Q&A into the main report or drop the companion from the delivery. The FYP report contains confirmed student/project details; programme BEng — Computer and Data Engineering, course EE4080 and term 2026/27 A are confirmed from the owner-supplied summary. Meetings and weekly hours remain blank because actual values are unknown; both fields explicitly appear on page 2 of the official progress-report template. The current title concerns influenza forecasting; the owner says the earlier H5N1 registration was only an initial, changeable idea. Do not relabel the national influenza/ILI experiments as H5N1 validation.

We directly retrieved the official JBHI author page on 5 November 2026: it states single-spaced double-column manuscripts with embedded figures/tables, an abstract no longer than 250 words, and a regular-paper limit of 14 pages including supplementary material. The live template selector returned HTTP 418. The included class came from the publisher template linked by the official IEEE EMBS BHI 2024 page. The exact current selector download and cloud Overleaf compilation are not verified. Keep that provenance distinction; do not call the manuscript submission-ready or promise acceptance.

## 2. Keep the historical science separate

The archived retained roster is 28 = 13 conventional + 4 LLM-based + 11 frozen language encoders. The historical paired family is the 17 non-encoder models INCLUDING MIFlu, excluding DLinear and the encoders: 136 pairs. Proper Holm gives 0/136 rejections, versus 128/136 raw p<0.05; the minimum adjusted p is about 0.0664 and NLinear–PatchTST is 0.1172. Do not trust the original exported p_holm column. Recompute from p_raw with a forward cumulative maximum after sorting. The exact-grid reconstruction is explicitly distinguished from rounding the six-decimal export.

The historical MSE order is MIFlu < PatchTST < NLinear, while PIE is NLinear < MIFlu < PatchTST. Say “inverted at both ends.” Both MIFlu and NLinear pass 4/16 aggregated cells at different locations; PatchTST passes 0/16. This is not a seasonal probability, universal dominance, statistical independence or exact reversal. Parameter exports cover 11 arms, not all 28; 211 times the parameters does not mean 211 times the latency. The frozen-encoder negative finding is specific to frozen features plus a linear readout.

These are baseline-snapshot results, not invariants to force on the new experiments. New verified results may change rankings, p-values or conclusions. Keep new panels and statistical families separately named until ChatGPT has checked them. Never overwrite the frozen historical CSVs with new results.

## 3. Establish actual execution status first

The last returned core artefacts were complete at 160/160 for MIFlu, NLinear, PatchTST and DLinear over four lengths and ten seeds (2021–2030). The national ledger snapshot recorded 117/1120 complete and 1003 queued at 4 November 23:35 HKT; a later supplied report recorded 139; the owner reported 141 at 5 November 00:15 HKT. These are historical capture times, not current live counts. Inspect the live filesystem and scheduler and write a fresh UTC/HKT capture time.

The owner reported 13 empty decision_tree partial directories and two pending gpu_a100 lanes at the last handoff. The ZIP separately contains complete decision-tree cells. Identify each actual configuration rather than treating the two observations as the same directories. Inspect sentinels, logs, finite metrics and valid prediction files; a directory or DONE label alone is insufficient. Reconcile the v2 Table VI 19 TODO and walk-forward 170 TODO with older legacy DONE rows and the separate nine-regional-TODO summary. Do not count legacy statuses as new v2 completion without a configuration match.

Read the source monitoring/resume commands in `handoffs/20261105_return/REPRODUCE.md`. The documented working root is `/gpfs1/scratch/sychan552/trackB_20261104`. Do not submit duplicate lanes or a second controller while the existing one is alive. Do not cancel active jobs to make the status look tidy. If access is unavailable, mark the check NOT_EXECUTED and return the exact intended command, without guessed output.

Recheck actual quota before additional work. The previous owner report was about 306/300 GB soft, ten-day grace, 1024 GB hard; it is not a current reading. Do not delete datasets, checkpoints, raw predictions or encoder caches during this task. Report any proposed cleanup separately.

## 4. Highest scientific priority: recover common scoring

The new stored metrics mix cropped MIFlu windows with all valid windows for other models. The 40 returned MIFlu CSV exports contain ILITOTAL only, despite the name prediction_ili; they do not contain a complete seven-channel prediction tensor. Recalculation matched 237 seven-channel NPZ cells and 40 MIFlu ILITOTAL cells at their own recorded panels, but that does not create a harmonised leaderboard.

Recover full seven-channel MIFlu predictions from existing checkpoints first. Prefer export/rescore to retraining. If recovery is impossible, identify the exact missing configurations, explain why, and report the smallest justified rerun set. Do not restart all completed experiments solely because seeds are being aligned. If a rerun is necessary within the already authorised benchmark, preserve the previous artefacts, pin all actual settings and label the rerun distinctly.

For each cell return prediction and target arrays, actual axis order, channel order, original target row indices, forecast-origin indices, all four scored leads, scaler means/stds, normalised/physical-unit metadata, source profile hash, training config, checkpoint-selection rule, seed, code/environment identifiers and hardware. Absolute CSV week minus forecast step reconstructs target start for the inspected exports; verify that relation rather than applying it blindly. Check shapes, finite values, equality of target arrays and exact row/lead/channel correspondence before comparing scores.

Produce BOTH panels: (a) all valid test windows and (b) the common historical crop, using identical target populations for every compared model. Record any missing predictions explicitly. Choose and timestamp the new primary/sensitivity specification before inspecting the aggregated conclusions; disclose the existing retrospective deviation. Do not backdate the protocol or mutate the original `PROTOCOL_LOCK.json`, which had frozen:false at submission. Create a new versioned scoring specification and explain what was chosen after execution.

The two profiles author_966 and author_repo_966 have different byte hashes. A supplied comparison reports max absolute numerical difference 0.0 across seven aligned channels. Include the actual profile files or a reproducible aligned comparison with channel/date mapping, not a claim of byte identity. Verify original CDC calendar/vintage before assigning peaks to epidemiological seasons. Synthetic labels cannot establish season-wise external validity.

## 5. Aggregate without pooling incompatible runs

The national planned roster is 28 x 4 x 10 = 1120. DLinear core controls lie outside that roster. Core and national runs overlap for some named models/configurations; compare full config/profile/window hashes before deduplicating or combining them. Return a unique-cell map. Do not add 160 and 1120 and call that the independent sample size.

For compatible completed cells, aggregate seven-channel MSE/MAE and ILITOTAL peak metrics with transparent numerators and denominators. Report by model, length, seed, lead and panel, then report declared summaries and variability. Recompute peak detection/matching from raw predictions using the specified retrospective algorithm. Return event-level matches, failed matches/misses, observed and predicted peak weeks/heights, and denominator definitions. Separate mean-error cell screens from event-level or season-level success rates. Do not generate a calibrated probability from a pass fraction or an arbitrary variance floor.

The legacy execution-end aggregation commands were:

```bash
python cellok.py count all/export all/cells_all.tsv
python aggregate_core.py
python aggregate_peak.py
```

Inspect their current code and window contract before using their output scientifically. The packaged local cell checker is also at `handoffs/20261105_return/code/trackB_v2/cellok.py`. Do not invent a new CLI or claim a missing script ran. For every actual command, save its working directory, interpreter/environment, timestamp, exit code, stdout/stderr and generated-file hashes. Mark unrun commands NOT_EXECUTED. A post-all driver starting after `all/phase.done` does not prove its scores are comparable.

## 6. Predictive ablations and the text invariant

The returned queue reports 60/60 additional ablation cells DONE; the old job 722968 is a historical cancelled job. No aggregate depth/LoRA trend has yet been verified. The planned additional arms are no_lora and K=2/4/8/12, each four lengths by three seeds. The reference K=6 cells are separate. Establish a default reference with matching seed, data, scaler, checkpoint selection, scoring panel and training settings. Do not compare the three-seed ladder against an unmatched ten-seed mean or count the reference twice. Return per-run values, paired differences, variability and raw evidence. Only then propose an ablation results table; never replace missing measurements with DONE labels.

The three supplied no-text CPU assertions passed with zero skips. They concern fixed-weight evaluation and matched initialisation. Keep the test file, actual model/imported modules, pinned environment, cache/revision identifiers and JUnit/stdout. A test path citation alone is insufficient. Whole-archive collection still has legacy-layout/dependency errors; do not claim a passing complete suite or a reliable test count.

If rerunning the three CPU checks in the working environment, use the documented command, adapting paths only to observed files:

```bash
PYTHONPATH="$PWD/05_程序代码" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest -q -rs --junitxml=tests/no_text_runtime.xml tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
```

The inspected default path puts text after time tokens under a causal mask, and the head reads time positions. Do not expand this into equality of independent training trajectories, lack of pretrained-weight contribution, or absence of all adaptation gradients. If performing a training diagnostic, record matching initial weights/RNG states and per-module forecast-loss gradient reachability; a zero text-path gradient and a nonzero time-path adaptation gradient answer different questions. Return the code and actual output. Keep such a diagnostic separate from predictive ablations.

## 7. Statistical and publication priorities

O1 remains the default: repair scoring and provenance, complete the existing comparison, then prioritise rolling origins, regions and faithful modern numerical-foundation/readout controls. Ten repeated seeds improve repeated-training precision but do not create independent epidemics. The four lengths reuse observations and overlapping targets. Do not treat all length–seed cells as independent datasets or obtain publishability by increasing the nominal sample count.

State the new comparison family, estimand, temporal sampling unit and dependence assumptions. Return paired raw errors, effect estimates and uncertainty inputs. If block resampling is used, justify block length and synchronise blocks across models; report sensitivity. Apply proper Holm to the chosen valid raw p-values. Do not force the historical 0/136 outcome or reuse the invalid exported p_holm column. Explain what cannot be inferred when few independent seasons/origins are available.

Numerical foundation models are not represented by the 11 frozen language encoders. If the existing controller already contains validated regional/WF stages, let it finish without duplicate submission, but inspect outputs before aggregation. For additional controls outside the existing chain, return a faithful source-pinned configuration and a measured pilot cost before making a broad resource claim. Do not invent wall times or venue acceptance predictions.

O2 remains OPTIONAL: validation-fitted peak-height calibration. Use only auditable validation predictions to fit/choose the adjustment, freeze it, and evaluate held-out predictions. Zero new GPU training is conditional on suitable validation/test exports already existing. CPU time and memory must be measured. O2 must not replace O1's scoring repair, and ordinary calibration is not automatically a novel method.

## 8. Return the evidence needed for the next scientific rewrite

Follow `RETURN_CONTRACT.json`. Return `RETURN_TO_CHATGPT.zip` and `RAW_EVIDENCE.zip`, both extracting into the same versioned root. Use a fresh capture time and an explicit complete/in-progress label. A readable package is required even when the full matrix is unfinished.

Include per-cell ledger/config/provenance, both scored panels, ablation/reference alignment, event-level peaks, paired-statistical inputs, hardware/resource measurements, executed-command logs, protocol deviations, tests and source patches. Include raw prediction tensors sufficient to independently rescore every newly claimed cell. Hash all listed files, validate the two ZIPs and report validator output. Structural/hash PASS must say `scientific_readiness: NOT_ASSESSED`; it is not scientific certification. Quarantine unlisted transient files in a review copy and retain a record. The previous return had one such temporary prediction file while all 896 manifest-listed hashes matched; do not silently rewrite that history.

Write `SCIENTIFIC_AUDIT.md` as a traceable argument: which claims are supported, partial, contradicted or blocked, each with exact source rows/files and scoring populations. Write `MESSAGE_TO_CHATGPT.md` using the companion return prompt. Identify every changed claim and every missing input. If the latest evidence changes a ranking or interpretation, say so; do not optimise for agreement with the old manuscript.

ChatGPT will verify the return and coordinate the scientific rewrite across the manuscript, Chinese internal report, English FYP report, journal record, README, PPT and English notes. Preserve Q01–Q25 and paper citations in the separate Chinese companion; do not turn scheduler status into journal findings; do not call completion, polished formatting or a validator PASS proof of JBHI publishability.

## Administrative update 9.1

Use the current FYP Part A source and retain its required blank meetings/hours fields. The supplied planning-summary PDF is an administrative source here; do not import its older dataset, Test/Holdout protocol or rankings into the retained 966-row/28-model scientific snapshot. Any future use of those older results requires separate provenance and protocol verification. Revision 9.1 adds no new HPC result.

## Document organisation update 9.2

The owner explicitly requested separation of all Chinese internal-report Q&A. This supersedes earlier instructions to keep the questions inline. Main science remains in report_internal_zh; all 25 full questions and their literature/evidence explanations are in report_internal_qa_zh. Both carry the original shared reference numbering. The full rebuild automatically applies scripts/split_internal_qa_zh.py. Future scientific updates must revise affected companion answers alongside the main report, preserving the questions and reasoning while replacing obsolete values when justified. The FYP 9.1 metadata and required blank fields remain unchanged. No new experimental result was added by this split.
