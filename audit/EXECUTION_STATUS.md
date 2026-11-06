# Current execution and evidence scope revision 8

Scientific snapshot: audited 3 Nov results. Execution evidence: 5 Nov 00:15 HKT owner handoff, with packaged ledger at 4 Nov 23:35. Core 160/160 artefact complete; national ledger 117/1120, later owner report 141/1120. Matrix incomplete. Supplied fixed-weight CPU no-text JUnit: 3 passed, 0 skipped. Whole-archive collection remains failed. Ablation queue reports 60/60 DONE; per-variant aggregate trend is unverified.

Executed in this review: ZIP/hash/CRC checks, normalised-return integrity check after transient-file quarantine, cell completeness checks, independent raw scoring at the supplied scoring panels, source-preserving document and deck edits, PDF rendering and visual review, historical CSV arithmetic verification. No new training result is created. Full verification records are in return_review_20261105 and INTEGRATED_DOCUMENT_BUILD.json.

Not executed here: live Burgundy SSH/monitor/submission, GPU training or inference, independent model-test rerun, human five-minute rehearsal, native Microsoft Office inspection, event-level peak matching, full-matrix statistics, source-paper/code pinning and official JBHI guidance verification. The supplied execution logs are distinguished from checks rerun here.

Exact execution-end commands and follow-up needs are in handoffs/20261105_return/REPRODUCE.md and audit/return_review_20261105/SUPPLIED_MESSAGE_TO_CHATGPT.md. Native checks: Start-Process .\presentation\Week12_Progress_Presentation.pptx and Start-Process .\presentation\Presentation_Notes_EN_ZH.docx. New common scoring requires complete seven-channel MIFlu exports and matching windows; the submitted protocol remains frozen:false and is not backdated.

## Commands for work not executed here

```bash
# Three model assertions: supplied execution passed, local rerun not executed
PYTHONPATH="$PWD/05_程序代码" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest -q -rs --junitxml=tests/no_text_runtime.xml tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
# Execution-end working directory, after completed exports; not executed here
python cellok.py count all/export all/cells_all.tsv
python aggregate_core.py
python aggregate_peak.py
# Whole archive collection still fails in supplied evidence; not rerun here
python -m pytest tests_archive --collect-only -q
```

For Burgundy monitor/resume use the exact owner-supplied commands in `handoffs/20261105_return/REPRODUCE.md`; no new training CLI is guessed. Native Office, not executed: `Start-Process .\presentation\Week12_Progress_Presentation.pptx` and `Start-Process .\presentation\Presentation_Notes_EN_ZH.docx` in PowerShell. Human timing: deliver only the English `TALKING_SCRIPT.md` aloud with a stopwatch, using the printed slide intervals; not executed. Current official venue and upstream protocol verification also remain unexecuted; no unverified venue facts are inserted.
