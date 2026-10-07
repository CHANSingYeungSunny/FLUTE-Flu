# v3 protocol simplification audit

The authoritative correction restores the verified GPT-2/MIFlu National-Illness workflow as the only active v3 data and evaluation protocol.

Removed from active v3: CDC/Delphi/NHSN acquisition, `ili`/`wili` target replacement, new external data, new-holdout blockers, reduced-feature redesign, rolling-origin redesign, and new split design. Their completed investigations remain on disk and are classified as `SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY`.

Retained: canonical `ILITOTAL`, the exact GPT-2/MIFlu train/validation/test split, train-only scaler and prompt statistics, horizons 24/36/48/60, formal seeds 42..51, checkpoint/validation-MSE workflow, fixed steps 0..3, and the approved `q1_step_sweep.py` plotting format.

Phase 1 remains unauthorized. No weights, models, Test values, result figures, or Slurm jobs were accessed or created in this correction turn.
