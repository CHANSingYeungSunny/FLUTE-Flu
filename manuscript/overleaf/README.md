# Revision 9 journal manuscript LaTeX source

Select main.tex and compile with pdfLaTeX. All required class/style files, figures, table values and a compiled main.pdf preview are included. The publisher class and generic.sty are unmodified. review_layout.sty removes sample masthead material, fixes the author paragraph and restores the References heading. The body dimensions and columns are retained. TEMPLATE_PROVENANCE.json documents the retrieved JBHI guidance and the exact-current-selector limitation.

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Local compilation has been executed. Cloud Overleaf execution is NOT_EXECUTED. Formatting does not establish submission readiness. Scientific values remain the audited historical snapshot; no new national benchmark is reported. The editable Word companion has the same text/table source with different pagination.

article_source.json is the editorial/evidence source; citation_mapping.json relates the internal-report bibliography to this article's first-citation numbering. To regenerate both Word and LaTeX or the plotted data, use manuscript/build_manuscript.py in the full revision 9 project, whose frozen CSVs and generators are not duplicated into this small source ZIP. Do not update numbers without verifying raw evidence, scoring panels and statistical units first.
