# Revision 9 execution record

## Executed locally in this revision

The following work was actually executed using the installed Python runtime. Historical supplied model/HPC outputs are evidence reviewed here, not newly executed jobs.

```bash
python manuscript/build_manuscript.py
python manuscript/build_pdf.py
python scripts/add_revision9_internal.py
python presentation/build_english_notes.py
python scripts/verify_snapshot.py --raw-smoke
python 01_最终报告/_build2/verify_docs.py
python presentation/verify_presentation.py
```

The LaTeX builder executes the following twice inside `manuscript/overleaf`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The final LaTeX build has no overfull boxes or unresolved references. The expected class-name warning occurs because the unmodified publisher file `ieeecolor.cls` declares IEEEtran. The canonical English manuscript is six pages, 211 abstract words, five tables, two plots and 21 used references. Its Word source is six pages in the local rendering and has the same text/table source, with different pagination.

LibreOffice document conversion and page rendering were executed for the three edited Word artifacts using:

```bash
FONTCONFIG_FILE=/workspace/scratch/3ee30e2684d1/work/fyp_details_20261105/fonts.conf python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/ieee_manuscript_en.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9/render_manuscript_final --emit_pdf
FONTCONFIG_FILE=/workspace/scratch/3ee30e2684d1/work/fyp_details_20261105/fonts.conf python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/report_internal_zh.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9/render_internal_zh --emit_pdf
FONTCONFIG_FILE=/workspace/scratch/3ee30e2684d1/work/fyp_details_20261105/fonts.conf python /root/.codex/skills/builtins/documents/render_docx.py presentation/Presentation_Notes_EN.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9/render_notes_en --emit_pdf
```

The Word rendering of the English manuscript is QA only; it does not replace the canonical LaTeX PDF. FitZ page rendering was used for final page-image inspection after Poppler produced incomplete PNG output in an intermediate run. No defective PNG is a delivered artifact.

The private release check was executed as `python /workspace/scratch/3ee30e2684d1/work/r9/check_release.py`. It confirms the original Chinese paragraph prefix, table cells, six figure assets and Q01–Q25; exact FYP 8.1 and deck/script preservation; all 83 historical CSV hashes; 13 English script segments; citation mappings; and six synthetic integrity-validator cases. These are not forecasting model tests. Its receipts are CONTENT_PRESERVATION.json and HANDOFF_VALIDATOR_TESTS.json. Release check code is copied into this folder as check_release_source.py for inspection; its original input paths are recorded in that file and must be adapted to reproduce the archive comparisons.

Official JBHI author guidance was retrieved directly over HTTPS with HTTP 200. The live template selector returned HTTP 418. The included class/package source and hashes are in manuscript/TEMPLATE_PROVENANCE.json. Do not describe this as exact-current selector verification or cloud Overleaf execution.

## Not executed in this revision

- Full authoring-pipeline rerun after integrating the entry-point routing: NOT_EXECUTED as a single command. Individual edited builders and checks above were executed. Exact rebuild command: `python scripts/build_delivery_v9.py`, then `python 01_最终报告/_build2/to_pdf.py`. The legacy wrapper now routes to the revision-9 pipeline and conversion delegates the English manuscript to LaTeX.
- Full archived pytest collection and forecasting assertions: NOT_EXECUTED here. The three CPU passes/zero skips are supplied JUnit/runtime evidence, not a new model-test run. Exact commands at the project root:

```bash
python -m pytest tests_archive --collect-only -q
PYTHONPATH="$PWD/05_程序代码" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest -q -rs --junitxml=tests/no_text_runtime.xml tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
```

- Live Burgundy monitoring, training, prediction recovery and new aggregation: NOT_EXECUTED. Exact supplied monitor command:

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk 'squeue -u sychan552; python /gpfs1/scratch/sychan552/trackB_20261104/cellok.py count /gpfs1/scratch/sychan552/trackB_20261104/all/export /gpfs1/scratch/sychan552/trackB_20261104/all/cells_all.tsv'
```

After inspecting the active code/window contract, the supplied aggregation commands, run from `/gpfs1/scratch/sychan552/trackB_20261104`, are:

```bash
python cellok.py count all/export all/cells_all.tsv
python aggregate_core.py
python aggregate_peak.py
```

- Whole-benchmark rerun, Table VI, walk-forward, regional stages, full seven-channel MIFlu recovery, predictive ablation aggregation and O2 calibration: NOT_EXECUTED here. The handoff specifies the required configs/exports. There is no verified current inference-export CLI or additional-variant training command in this review; do not invent one. DeepSeek must inspect the working driver/checkpoint interface and return the exact observed command before claiming execution.
- Native Word/PowerPoint inspection, cloud Overleaf compilation and human 5:00 rehearsal: NOT_EXECUTED. These are interactive/manual tasks rather than verified shell commands. To perform them, open the delivered DOCX/PPTX in their native apps; upload the Overleaf ZIP, select main.tex and compile; rehearse only the 606-word spoken paragraphs against the 300-second slide plan.

Existing national counts (117 ledger / later 141 owner report), quota and pending-lane observations are dated historical captures. No new live count or training result is inferred. Integrity PASS means hashes, required structure and declarations only; scientific readiness remains NOT_ASSESSED.
