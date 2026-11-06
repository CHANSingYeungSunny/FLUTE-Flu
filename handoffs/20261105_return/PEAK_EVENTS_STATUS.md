# PEAK_EVENTS.csv is intentionally header-only

Protocol S requires pre-defined peak-detection parameters and a monotonic
one-to-one observed/predicted event matching rule, with unmatched events counted.
Neither was implemented in this execution round, so there are no honest
event-level rows to write. Fabricating event IDs would be worse than an empty table.

What DOES exist: `AGGREGATION/TRACKB_PEAK_PARTIAL.csv` contains real step-level
PTE/PIE aggregates (model, L, seed, step, pte, pie, passed, n_windows) from a
partial set of cells, using `find_peaks(prominence=0.15*range, distance=15)` and
a +/-8 week matching window. These are **step aggregates**, not event-level
success rates. The 16 aggregate passing units and any per-event success rate must
be reported separately; a low PIE is not probability calibration.

Next executable step: freeze detector parameters, implement monotonic 1:1
matching with unmatched-event accounting, then regenerate `PEAK_EVENTS.csv` from
`RAW_EVIDENCE/cells/`.
