# R1_PAPER_FIGURE_TARGETS.md

**Paper:** MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme
(IEEE JBHI, vol. 29, no. 10, Oct. 2025). **PDF SHA-256:**
`7735a4388145dd2aced536417f7a4f50dafe21ed0d4fca64baa2b20f2e27885c`.

One row per figure: verbatim caption, the series it draws, and what is needed to regenerate it.
Captions are quoted exactly as they appear in the PDF text layer and were confirmed against the
rendered pages. "PDF page" is the page on which the caption/art appears.

> **Render-filename warning.** The supplied PNGs are mis-named for two pages:
> `page_06.png` actually contains **PDF page 9** (journal p7798) and `page_09.png` actually
> contains **PDF page 6** (journal p7795). All references below use the true PDF page number.

---

## Fig. 1 — Architecture of the proposed scheme
- **Page:** PDF 4 (journal p7793). Source render: `page_04.png`.
- **Caption (verbatim):** "Fig. 1. Architecture of the proposed scheme."
- **Series shown:** not a data plot. A block diagram of the three modules — *textual input
  embedder* (Tokenizer → Text-embedding LLM), *time-series input embedder* (Instance norm +
  Patching → Linear embedder), and the *forecasting LLM* (K transformer blocks). The inset marks
  which parameters are **Frozen** (snowflake: embedding LLM, feed-forward) and which are
  **Trainable** (flame: linear embedder, PE, LoRA on Wq/Wk/Wv/Wo, output projection). Legend keys:
  `h_text`, `h_time`, `h_forecast`.
- **Derived from a table:** no.
- **Digitizable:** no — it is a schematic.
- **To regenerate:** redraw from the Section IV prose plus Table IV (`K` = 6 national / 4 regional,
  LoRA on the multi-head attention layer, PE + layer-norm fine-tuned). No data required.

## Fig. 2 — Boxen plots of the two datasets
- **Page:** PDF 6 (journal p7795). Source render: `page_09.png` (mis-named).
- **Caption (verbatim):** "Fig. 2. Boxen plots for the variables and regions used in the national-Illness and US-region datasets, respectively."
- **Series shown:** (a) boxen plot of the **7 National-Illness variables** (Variable 1 … Variable 7)
  and (b) boxen plot of the **10 US-Region series** (Region 1 … Region 10, x-axis "ILI patient
  count", 0–30000).
- **Derived from a table:** yes — the same quantities summarised in Tables II and III.
- **Digitizable:** partially — the boxen geometry can be recomputed from the raw series.
- **To regenerate:** the public CDC data (ref [25]) for both datasets, split exactly as described
  in Section V-A; then run the authors' boxen-plot code. The two tables' literature values cannot
  be used as a cross-check because **Tables II/III could not be read** (see the blocker note below).

## Fig. 3 — Average forecasting performance
- **Page:** PDF 8 (journal p7797). Source render: `page_08.png`.
- **Caption (verbatim):** "Fig. 3. Comparison of average forecasting performance for L = 24, 36, 48, 60."
- **Series shown:** grouped bars of the **average MSE (a)** and **average MAE (b)** over the four
  national lead times, with one bar per model. Legend: MIFlu, GPT4TS, DLinear, PatchTST, TimesNet,
  FEDformer, Autoformer, Stationary, ETSformer, LightTS, Informer, Reformer (12 models).
- **Derived from a table:** yes — it is the arithmetic mean of the four lead-time rows of **Table V**.
- **Digitizable:** yes (fully) — every bar equals `mean(Table V row)`.
- **To regenerate:** take Table V, average the L = 24/36/48/60 columns per model and per metric.
  Only the **MIFlu** bar is an author-generated result; the other 11 bars re-plot cited values.

## Fig. 4 — Real vs predicted ILI (US-Region)
- **Page:** PDF 9 (journal p7798). Source render: `page_06.png` (mis-named).
- **Caption (verbatim):** "Fig. 4. Comparison of the real and predicted ILIs for MIFlu using the US-Region dataset."
- **Series shown:** two panels — (a) `L = 2` and (b) `L = 20` — each overlaying **Actual Data** and
  **Predicted Data** for the mean ILI across all regions over the test period (x = Time Step,
  y = ILI occurrences).
- **Derived from a table:** no.
- **Digitizable:** no (would need the model's test-set predictions).
- **To regenerate:** reimplement MIFlu and run regional forecasting at L = 2 and L = 20, then plot
  the region-averaged actual and predicted series. No baseline is plotted, so this figure isolates
  the proposed scheme.

## Fig. 5 — Accuracy vs window size T
- **Page:** PDF 9 (journal p7798). Source render: `page_06.png` (mis-named).
- **Caption (verbatim):** "Fig. 5. Changes in forecasting accuracy according to T."
- **Series shown:** (a) RMSE and (b) PCC of **MIFlu** on US-Region at `L = 20` as the window size
  `T` sweeps the marked points 10, 20, 30, 40, 50 (RMSE falls from ≈2800 to ≈1550; PCC rises from
  ≈0.1 to ≈0.8).
- **Derived from a table:** no — the values exist only as plotted points.
- **Digitizable:** partially — the plotted marker positions are readable but approximate.
- **To regenerate:** reimplement MIFlu and sweep `T ∈ {10,20,30,40,50}` at L = 20 on US-Region.
  Prose expectation to match: performance improves up to `T = 40`, then degrades at `T = 50`
  ("the excessive input data can lead to overfitting").

## Fig. 6 — Accuracy vs number of GPT2 layers K
- **Page:** PDF 10 (journal p7799) — although the figure is introduced at the end of PDF page 9.
  Source render: `page_10.png`.
- **Caption (verbatim):** "Fig. 6. Changes in forecasting accuracy according to K."
- **Series shown:** (a) RMSE and (b) PCC of **MIFlu** on US-Region at `L = 20` as the number of
  GPT2 backbone layers `K` sweeps 1 … 7 (RMSE ~2250 → ~1960; PCC ~0.57 → ~0.69).
- **Derived from a table:** no — visual only.
- **Digitizable:** partially.
- **To regenerate:** reimplement MIFlu and sweep `K ∈ {1..7}` at L = 20 on US-Region. The prose
  states the expected shape: performance rises to `K = 4` (this is why the regional default is
  `K = 4`), and "when there are more than six layers, text-specific information is more likely to
  be incorporated, which can reduce forecasting accuracy."

## Fig. 7 — Few-shot forecasting comparison
- **Page:** PDF 11 (journal p7800). Source render: `page_11.png`.
- **Caption (verbatim):** "Fig. 7. Few-shot forecasting comparison results using the National-Illness dataset."
- **Series shown:** (a) `L = 48, 50% training data` and (b) `L = 24, 10% training data`; each panel
  overlays **MIFlu**, **GPT4TS** and **Actual ILI**, for the normalized `ILITOTAL` variable over the
  last two seasons (x = Time Step, y = normalized ILI occurrences).
- **Derived from a table:** no.
- **Digitizable:** no.
- **To regenerate:** reimplement **both** MIFlu and GPT4TS, restrict training to the first 50%
  (L = 48) and first 10% (L = 24) of the training split, and plot the normalized forecasts against
  the actual `ILITOTAL` series. Expected qualitative result: MIFlu tracks peak intensity and peak
  timing better than GPT4TS.

---

## Summary table

| Fig. | PDF page | Kind | Rebuild source | Regenerable here? |
|---|---|---|---|---|
| 1 | 4 | schematic | Section IV prose + Table IV | Yes (redraw) |
| 2 | 6 | distribution plot | public CDC data [25] | Partial (recompute from data) |
| 3 | 8 | bar chart | arithmetic mean of Table V | Yes (from Table V) |
| 4 | 9 | line plot | MIFlu test predictions | No (needs reimplementation) |
| 5 | 9 | sweep line plot | MIFlu T sweep | Partial (re-sweep) |
| 6 | 10 | sweep line plot | MIFlu K sweep | Partial (re-sweep) |
| 7 | 11 | line plot | MIFlu + GPT4TS few-shot predictions | No (needs reimplementation) |

---

## Blocker carried over from the table pass

**PDF page 5 (journal p7794) was never rendered.** That page carries **Tables II and III**
(descriptive statistics of the National-Illness and US-Region datasets). Because every table cell
value in this PDF is an image and the numeric values have zero occurrences in the text layer, no
cell of Tables II or III could be transcribed — they are recorded as `UNREADABLE` in
`PAPER_TABLE_CELL_MASTER.csv`. Fig. 2 is the visual analogue of those two tables and is therefore
also the only recoverable view of that content.

**PDF page 12 (journal p7801) has no render either.** The PDF text layer for that page contains
**references only** ([7]–[37]) and no table or figure caption, so nothing is believed to be missing
there.