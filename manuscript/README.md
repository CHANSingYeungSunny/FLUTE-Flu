# English journal manuscript revision 9

The canonical PDF is 01_最终报告/ieee_manuscript_en.pdf, compiled locally from overleaf/main.tex using the included unmodified publisher class. The Word copy is editable and contains the same source text/tables; its pagination and fonts need not be pixel-identical to LaTeX. The original revision-8 manuscript is preserved under archive/manuscript_revision8.

The article reports historical audited values. It does not contain an operational DONE-status ablation table, job IDs or F0–F5 labels. Incomplete predictive ablation effects are not inferred from queue records. Material scoring/protocol limitations remain in scientific language.

```bash
python manuscript/build_manuscript.py
python manuscript/build_pdf.py
```

For direct LaTeX compilation:

```bash
cd manuscript/overleaf
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Upload the source ZIP to Overleaf and select main.tex to compile in that service. Cloud compilation was not executed here. Do not edit numerical text in isolation from the evidence: article_source.json is the editorial source, and table_data.json contains the inherited scientific table values. Future common-panel results must be verified and then integrated through a coordinated source rewrite.

TEMPLATE_PROVENANCE.json documents direct retrieval of the official JBHI guidance, the HTTP-418 template selector limitation, the publisher class source/hash and the header/author compatibility file. Body dimensions and columns remain those of the publisher class. The template source is not claimed to be the exact current selector download. Formatting alone does not make this incomplete study submission-ready.
