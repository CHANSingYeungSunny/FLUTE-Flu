# R3 SENSITIVITY CONTRACTS (Figs 5, 6)

## The decisive fact: both are REGIONAL

| Figure | Factor varied | Range | Dataset and horizon | Paper's reported shape |
|---|---|---|---|---|
| **Fig. 5(a)** | input window **T** | 10–50 | **US-Region, L=20** | RMSE falls from ~2800 at T=10 to a minimum ~1430 at T=40, then rises at T=50 (described as overfitting) |
| **Fig. 5(b)** | same | same | same | PCC rises from ~0.1 at T=10 to ~0.82 at T=40 |
| **Fig. 6** | GPT-2 layers **K** | 1–7 | **US-Region, L=20** | improves to K=4, degrades beyond K=6; the text says MIFlu still beats ReILIF (RMSE 2431.7, PCC 0.596) at every K |

**Both use the US-Region dataset, which the released tree does not contain.** They are
`BLOCKED_BY_MISSING_DATA`.

## What must NOT happen

| Prohibited |
|---|
| silently re-scoping either sensitivity study onto the national data and calling it a reproduction |
| varying more than one factor at a time |
| using different repetitions across the points of one curve |
| reporting only the best point |
| digitising the published curve and presenting it as a reproduced result |

The published curves are recorded as `FIGURE_DIGITIZED_APPROXIMATION` — a description of the
printed shape, not a measurement.

## Contract, if the data ever becomes available

One factor varied; every other factor fixed (architecture, prompt, LoRA, seeds, metric);
matched repetitions; raw outputs saved per point; the figure regenerated from those outputs;
mean and dispersion reported; trained results kept separate from figure-digitised
approximations.
