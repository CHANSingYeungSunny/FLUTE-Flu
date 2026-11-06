# Changes from the corrected upload

Editing base: PROJECT_HANDOFF(4).zip, supplied 4 November 2026. Experimental status remains the supplied 3 November snapshot. Accepted corrected values are retained: 0/136 after proper Holm, 128/136 unadjusted, minimum adjusted p about 0.0664, NLinear–PatchTST 0.1172, and 13+4+11 model families. All source CSV byte hashes remain unchanged.

| Change | Evidence and exact location | Consequence |
|---|---|---|
| Correct actual paired membership | BENCH_PAIRED_TESTS.csv, unique model_a/model_b; MIFlu appears in 16 rows, DLinear in none | 17-model family includes MIFlu and excludes DLinear plus all 11 encoders. |
| Retain corrected statistics without trusting exported adjusted column | Same file p_raw, source data.py and audit/HOLM_RECOMPUTATION.csv | Rounded-export result 0.117180 and documented-grid recovery 0.1171875 both display 0.1172. No equivalence claim. |
| Use “inverted at both ends” with explicit orders | BENCH_MSE_BY_MODEL_L.csv and BENCH_PTE_PIE_BY_STEP.csv grouped by model | The end positions change, but no universal rank reversal or independence is claimed. |
| Correct MAE interpretation | ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–5 | MAE has one lower and three higher values, distinct from MSE’s two/two pattern. |
| Correct reproduction mean precision | Same table line 6 | Paper means shown as 1.4355 MSE and 0.7452 MAE, not truncated to three places. |
| Replace timing-champion and calibration wording | Peak CSV model-keyed aggregates; Kramer–Shaman full text and Bracher interval-scoring paper | MIFlu has better mean timing than NLinear; PIE measures magnitude error rather than probabilistic calibration. |
| Correct the peak chart’s colours | scripts/rebuild_peak_figure.py reads peak CSV step=0 means | Each bar is coloured against its own tolerance; all three timing means are below one week. |
| Restrict encoder conclusion | Benchmark CSV family=llm_encoder; literature [6–14] | Frozen-feature plus linear-readout finding only. |
| Distinguish archived assertions from execution | tests_archive/test_miflu_ablations.py and ARCHIVE_COLLECTION_LOG.txt | Assertions statically verified; archived model test outcomes not executed or counted as a passing suite. |
| Narrow data identity and hardware claims | Two supplied 966-row files’ matched numeric columns; BENCH_GPU_PROVENANCE.csv membership | Numeric local equality verified; upstream byte identity and complete per-cell hardware coverage not established. |
| Remove unsupported upstream and baseline-count allegations | No pinned upstream checkout; supplied paper notes conflict with the draft | Describe local behaviour and mark upstream details unverified. |
| Rewrite reports and public README | build_revised.py, DOC_REVIEW.md and full DOCUMENT_DIFFS.md | Six bilingual reports, continuous internal sections, exact school template, eight manuscript tables and verified source identities. |
| Correct source generating routine and add audit | analysis_postprocess.py Holm line; scripts/verify_snapshot.py; tests/test_snapshot_audit.py | Frozen CSVs preserved. Seven new CPU audit tests passed, separately from the archived suite. |
| Make report rebuild portable and keep metadata current | to_pdf.py, verify_docs.py and make_manifest.py | Installed/bundled LibreOffice supported; embedded CJK fonts required for Chinese QA; manifest regeneration measures current files and cannot restore stale statistics. |
| Generate deterministic deck and script | presentation/build_deck.py and deck_spec.json | Thirteen slides, source notes, fixed 300-second pacing budget, byte-identical repeat build; actual human timing not executed. |

The full diffs list every changed paragraph and table row. ORIGINAL_NUMERICAL_INVENTORY.csv records each original numeric token and its source sentence. Operational, model-runtime and venue details that could not be independently verified are explicitly listed in UNVERIFIED_ITEMS.md. No fabricated experiment or new method result was added. O1 is the default; O2 is presented separately with conditions and unmeasured costs clearly labelled.







## Revision 2: four-axis presentation and restored internal teaching material

- Restored the six explicit original explanations and added surrounding support as Q01–Q25, in both internal reports beside their evidence. Exact mapping is in QA_RESTORATION_MAP.md. The complete current paragraph/table differences are in DOCUMENT_DIFFS.md.
- Retained all corrected science: proper Holm 0/136, raw 128/136, frontier p 0.1172, 13+4+11 roster, MIFlu in the 17-model paired family, bounded frozen-feature result, and no-text runtime marked not executed.
- Rebuilt the entire thirteen-slide deck around four axes with different model coverage. The new cover uses the accepted title and avoids an unproved decoupling claim.
- Added editable reproduction/accuracy charts and an actual source-derived passing-cell grid. Enlarged Pareto labels on a separate presentation-specific figure while retaining all eleven measured points.
- Regenerated the planned five-minute script, embedded bilingual preparation notes, ten-question sheet, complete supervisor guide and bilingual notes DOCX/PDF. Actual human delivery remains not executed.
- Added Q01–Q25 retention checks and actual notes/chart-data checks, and normalised embedded chart workbook metadata for deterministic repeat builds.
- Corrected a malformed MIFlu DOI link in LITERATURE_REVIEW.md to 10.1109/JBHI.2025.3561214. The source ledger and manuscript citation already carried the correct DOI.
- Refreshed every report PDF/DOCX pair, counts, inventories, README instructions and both delivery archives. All frozen input CSV hashes remain unchanged.

## Revision 3: owner-corrected PowerPoint synchronisation

- Preserved the uploaded PowerPoint byte for byte, including user formatting and the resized cover author box. The cover now says CHAN Sing Yeung; the closing deadline line is removed. Slide footers remain exactly as uploaded.
- Updated formal authorship across all six DOCX/PDF report pairs, report metadata, README and bilingual notes. The scientific slide text, native chart values, 300-second script and all 25 internal-report questions are unchanged.
- Retained the verified school deadline in written planning sections; its removal from the slide is not treated as cancellation.
- Made build_deck.py restore the checksum-verified owner master. The original programmatic alternative is retained separately and does not overwrite manual changes.
- Updated the root CITATION.cff author, obsolete reproduction abstract and MIFlu given names against the existing verified ledger; repository URLs and licence handles are unchanged.
- Refreshed PDF exports, inventories, current verification records and both delivery archives. No source CSV or forecast data changed.

## Revision 4 paper-backed explanations

All Q01–Q25 now connect a direct local answer with a named-paper argument, a specific reading location and a short supervisor response. QA_CITATION_MAP.md/.json records every link. The complete supervisor guide mirrors both languages, and the external notes/live Q&A carry matching paper support. Seven methodological references extend the internal list to 25. School and manuscript report pairs, the owner-edited PPTX/PDF and the planned English speech remain unchanged.

The original split rationale is strengthened by Tan et al. §3.3 (Illness 70/10/20) and iTransformer Appendix A.1 (chronological separation). The original three-seed citation is corrected: PatchTST A.6.1 and iTransformer A.2/Table 5 report five-seed robustness. PatchTST A.6.2 also reports ILI sensitivity to model settings. These passages explain why a three-seed compute compromise and a cross-model parameter regression do not settle robustness or tuning importance.

The added methods explain leakage, measurement scale, Holm, equivalence, causal masking and forecast evaluation. Tashman is used only at publisher-indexed abstract depth; direct publisher access was blocked. No unseen upstream defect or unexecuted model outcome is promoted to fact. This is a literature/explanation revision, with no new training or HPC result.

