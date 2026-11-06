# Executed delivery checks

```bash
python scripts/verify_snapshot.py --raw-smoke
python 01_最终报告/_build2/verify_docs.py
python presentation/build_deck.py --out repeat.pptx
python presentation/verify_presentation.py --repeat repeat.pptx
python 01_最终报告/_build2/make_manifest.py
python scripts/package_review.py --out ../delivery
```

CSV/raw smoke, Word/PDF text/citation/table checks, deck/chart/workbook/notes consistency and deterministic PPTX repeat checks were executed and passed. LibreOffice conversion was executed for all eight report pairs and presentation/notes. The private skill-supplied finalizer also checked 13 slides, three native tables, two editable charts/workbooks, 13 imported slides, source fonts and package geometry; its receipt is DECK_FINALIZER_V8.json. Human rehearsal, native Microsoft Office, new training/inference and live HPC were not executed; commands/status boundaries are in EXECUTION_STATUS.md. Model assertions are supplied execution evidence rather than a new local run.
