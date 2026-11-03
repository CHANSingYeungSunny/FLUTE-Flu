"""
fidelity.py — the three architecture-fidelity levels (pre-HPC clarification 5).
==============================================================================

Every backbone must declare exactly one level, backed by component-level
file:line evidence and an explicit deviation list:

  REFERENCE_FAITHFUL
      Components match the published architecture; no material deviation.

  REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS
      The core mechanism matches the published architecture, but one or more
      components deviate and each deviation is listed (and disclosed in the
      architecture report). NOT to be called "faithful".

  INSPIRED_SIMPLIFICATION
      Materially simplified / re-scoped relative to the published model (e.g.
      no self-supervised pretraining, reduced capacity, or not a paper
      architecture at all). The display name must say "-inspired".

A model may NOT be labelled REFERENCE_FAITHFUL without component-level and
file:line evidence in `architecture_report()`.
"""

from __future__ import annotations

REFERENCE_FAITHFUL = "REFERENCE_FAITHFUL"
REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS = \
    "REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS"
INSPIRED_SIMPLIFICATION = "INSPIRED_SIMPLIFICATION"

LEVELS = (REFERENCE_FAITHFUL, REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS,
          INSPIRED_SIMPLIFICATION)
