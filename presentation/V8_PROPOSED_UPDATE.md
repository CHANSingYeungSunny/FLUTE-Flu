# Proposed V8 slide/notes update

This is a proposal only. The owner-edited `Week12_Progress_Presentation.pptx` was
not overwritten.

## Results slide

- National common panel: 1,120/1,120 valid cells; all-valid MSE MIFlu 1.7944,
  PatchTST 1.9521, NLinear 2.0782.
- Crop MSE: MIFlu 1.4994, PatchTST 1.6352, NLinear 1.9027.
- Peak step passes: MIFlu 252/1680, PatchTST 215/1680, NLinear 57/1680.

## Scope caveats

- The 1,020/1,020 walk-forward result is a separate legacy five-fold panel
  (seeds 42/43/44), not part of the national 1,120-cell panel.
- Chronos and TimesFM are a separate 80-cell zero-shot rolling-origin roster;
  their ten replicates are origins, not training seeds, and their adapter is
  univariate per channel.
- Ablation depth is non-monotonic: K4 is best (1.4989) and K12 is worst
  (1.7604).
- CDC vintage analysis is retrospective final-vintage reconstruction. Resource
  measurements are a six-model representative subset, not a full-panel Pareto.
- Validator PASS is structural only (`scientific_readiness: NOT_ASSESSED`); the
  exact JBHI template class remains unverified and the work is not
  submission-ready.
